#
# (C) Semantix Information Technologies.
#
# Semantix Information Technologies is licensing the code of the
# Data Modelling Tools (DMT) in the following dual-license mode:
#
# Commercial Developer License:
#       The DMT Commercial Developer License is the suggested version
# to use for the development of proprietary and/or commercial software.
# This version is for developers/companies who do not want to comply
# with the terms of the GNU Lesser General Public License version 2.1.
#
# GNU LGPL v. 2.1:
#       This version of DMT is the one to use for the development of
# applications, when you are willing to comply with the terms of the
# GNU Lesser General Public License version 2.1.
#
# Note that in both cases, there are no charges (royalties) for the
# generated code.
#
'''
This is the code generator for the VHDL code mapper.
This backend is called by aadl2glueC, when a VHDL subprogram
is identified in the input concurrency view.

This code generator supports both UPER/ACN and Native encodings,
and is designed to target the ESA Virtex4 XC4VLX100.

Currently, this is developed in the form of a sync mapper,
that  is a member of the synchronous "club" (SCADE, etc) ;
The subsystem developer (or rather, the APLC developer) is
building a model in Simulink, and the generated code is offered
in the form of a "function" that does all the work.
To that end, we create "glue" functions for input and output
parameters, which have C callable interfaces. The necessary
stubs (to allow calling from the VM side) are also generated.
'''
# pylint: disable=too-many-lines

import re
import os
import math

from typing import cast, List, Tuple, IO, Any  # NOQA pylint: disable=unused-import

from ..commonPy.utility import panic, panicWithCallStack
from ..commonPy.asnAST import (
    AsnBasicNode, AsnInt, AsnSequence, AsnSet, AsnChoice, AsnSequenceOf,
    AsnSetOf, AsnEnumerated, AsnMetaMember, isSequenceVariable,
    sourceSequenceLimit, AsnNode, AsnString, AsnReal, AsnOctetString,
    AsnSequenceOrSetOf, AsnSequenceOrSet, AsnBool)
from ..commonPy.asnParser import AST_Lookup, AST_Leaftypes
from ..commonPy.aadlAST import (
    InParam, OutParam, InOutParam, AadlPort, AadlParameter,
)
from ..commonPy.aadlAST import Param  # NOQA pylint: disable=unused-import
from ..commonPy import asnParser

from ..commonPy.recursiveMapper import RecursiveMapperGeneric
from .synchronousTool import SynchronousToolGlueGenerator

isAsynchronous = False
vhdlBackend = None

# List of octet string sizes (used in VHDL type declarations)
g_octStr = []  # type: List[int]


def Version():
    print("Code generator: " + "$Id: vhdl_B_mapper.py 2390 2012-07-19 12:39:17Z ttsiodras $")  # pragma: no cover


def CleanName(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def RegistersAllocated(node: AsnNode) -> int:
    # The ESA FPGA needs alignment to 4 byte offsets
    names = asnParser.g_names
    while isinstance(node, str):
        node = names[node]
    retValue = None
    if isinstance(node, AsnBasicNode):
        retValue = 0
        realLeafType = asnParser.g_leafTypeDict[node._leafType]
        if realLeafType == "INTEGER":
            retValue = 8
        elif realLeafType == "REAL":
            panic("The VHDL mapper can't work with REALs (non-synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover
        elif realLeafType == "BOOLEAN":
            retValue = 4
        elif realLeafType == "OCTET STRING":
            nodeOct = cast(AsnString, node)
            if not nodeOct._range:
                panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
            if len(nodeOct._range) > 1 and nodeOct._range[0] != nodeOct._range[1]:
                panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % nodeOct.Location())  # pragma: no cover
            if nodeOct._range[-1] not in g_octStr:
                g_octStr.append(nodeOct._range[-1])
            retValue = 4 * (int((nodeOct._range[-1] + 3) / 4))
        else:  # pragma: no cover
            panicWithCallStack("Basic type %s can't be mapped..." % realLeafType)  # pragma: no cover
    elif isinstance(node, (AsnSequence, AsnSet)):
        retValue = sum(RegistersAllocated(x[1]) for x in node._members)
    elif isinstance(node, AsnChoice):
        retValue = 4 + sum(RegistersAllocated(x[1]) for x in node._members)
    elif isinstance(node, AsnSequenceOf):
        if not node._range:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        retValue = node._range[-1] * RegistersAllocated(node._containedType)
    elif isinstance(node, AsnSetOf):
        if not node._range:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        retValue = node._range[-1] * RegistersAllocated(node._containedType)
    elif isinstance(node, AsnEnumerated):
        retValue = 4
    elif isinstance(node, AsnMetaMember):
        retValue = RegistersAllocated(names[node._containedType])
    else:  # pragma: no cover
        panicWithCallStack("unsupported %s (%s)" % (str(node.__class__), node.Location()))  # pragma: no cover
    return retValue


class VHDL_Circuit:
    allCircuits = []  # type: List[VHDL_Circuit]
    lookupSP = {}  # type: Dict[str, VHDL_Circuit]
    currentCircuit = None  # type: VHDL_Circuit
    names = None  # type: asnParser.AST_Lookup
    leafTypeDict = None  # type: asnParser.AST_Leaftypes
    currentOffset = 0x0  # type: int

    def __init__(self, sp):
        VHDL_Circuit.allCircuits.append(self)
        VHDL_Circuit.lookupSP[sp._id] = self
        VHDL_Circuit.currentCircuit = self
        self._sp = sp
        self._params = []  # type: List[Tuple[Param, asnParser.Typename, AsnNode]]
        self._spCleanName = CleanName(sp._id)
        self._offset = VHDL_Circuit.currentOffset
        VHDL_Circuit.currentOffset += 4  # reserve one register for "start" signal
        self._paramOffset = {}  # type: Dict[str, int]
        for p in sp._params:
            self._paramOffset[p._id] = VHDL_Circuit.currentOffset
            VHDL_Circuit.currentOffset += RegistersAllocated(p._signal._asnNodename)
        if VHDL_Circuit.currentOffset > 256:
            panicWithCallStack("For the ESA FPGA, there is a limit of 63 registers (252/4) - your design required %d." % (VHDL_Circuit.currentOffset / 4))

    def __str__(self):
        msg = "PI:%s\n" % self._sp._id  # pragma: no cover
        msg += ''.join([p[0]._id + ':' + p[0]._signal._asnNodename + ("(in)" if isinstance(p[0], InParam) else "(out)") + '\n' for p in self._params])  # pragma: no cover
        return msg  # pragma: no cover

    def AddParam(self, nodeTypename, node, param, leafTypeDict, names):
        VHDL_Circuit.names = names
        VHDL_Circuit.leafTypeDict = leafTypeDict
        self._params.append([param, nodeTypename, node])

# def IsElementMappedToPrimitive(node, names):
#     contained = node._containedType
#     while isinstance(contained, str):
#         contained = names[contained]
#     return isinstance(contained, AsnInt) or isinstance(contained, AsnReal) or isinstance(contained, AsnBool) or isinstance(contained, AsnEnumerated)


# noinspection PyListCreation
# pylint: disable=no-self-use
class FromVHDLToASN1SCC(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, srcVHDL: str, destVar: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = srcVHDL[0] + srcVHDL[1]
        lines = []  # type: List[str]
        lines.append("{\n")
        lines.append("    unsigned tmp, i;\n")
        lines.append("    asn1SccSint val = 0;\n")
        lines.append("    for(i=0; i<sizeof(asn1SccSint)/4; i++) {\n")
        lines.append("        tmp = ESAReadRegister(BASE_ADDR + %s + ((sizeof(asn1SccSint)/4)-1-i)*4);\n" % hex(register))
        lines.append("        val <<= 32; val |= tmp;\n")
        lines.append("    }\n")
        lines.append("    %s = val;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 8
        return lines

    def MapReal(self, dummy: str, _: str, node: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panicWithCallStack("REALs (%s) cannot be used for synthesizeable VHDL" % node.Location())  # pragma: no cover
        # return ["%s = (double) %s;\n" % (destVar, srcVHDL)]

    def MapBoolean(self, srcVHDL: str, destVar: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = srcVHDL[0] + srcVHDL[1]
        lines = []  # type: List[str]
        lines.append("{\n")
        lines.append("    unsigned tmp;\n")
        lines.append("    tmp = ESAReadRegister(BASE_ADDR + %s);\n" % hex(register))
        lines.append("    %s = (asn1SccUint) tmp;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 4
        return lines

    def MapOctetString(self, srcVHDL: str, destVar: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = srcVHDL[0] + srcVHDL[1]
        lines = []  # type: List[str]
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        for i in range(0, int((node._range[-1] + 3) / 4)):
            lines.append("{\n")
            lines.append("    unsigned tmp;\n")
            lines.append("    tmp = ESAReadRegister(BASE_ADDR + %s);\n" % hex(register + i * 4))
            if i * 4 < node._range[-1]:
                lines.append("    %s.arr[%d] = tmp & 0xFF;\n" % (destVar, i * 4))
            if i * 4 + 1 < node._range[-1]:
                lines.append("    %s.arr[%d] = (tmp & 0xFF00) >> 8;\n" % (destVar, i * 4 + 1))
            if i * 4 + 2 < node._range[-1]:
                lines.append("    %s.arr[%d] = (tmp & 0xFF0000) >> 16;\n" % (destVar, i * 4 + 2))
            if i * 4 + 3 < node._range[-1]:
                lines.append("    %s.arr[%d] = (tmp & 0xFF000000) >> 24;\n" % (destVar, i * 4 + 3))
            lines.append("}\n")
        if isSequenceVariable(node):
            lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        srcVHDL[0] += 4 * int((node._range[-1] + 3) / 4)
        return lines

    def MapEnumerated(self, srcVHDL: str, destVar: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = srcVHDL[0] + srcVHDL[1]
        lines = []  # type: List[str]
        lines.append("{\n")
        lines.append("    unsigned char tmp;\n")
        lines.append("    tmp = ESAReadRegister(BASE_ADDR + %s);\n" % hex(register))
        lines.append("    %s = tmp;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 4
        return lines

    def MapSequence(self, srcVHDL: str, destVar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVHDL,
                    destVar + "." + self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVHDL: str, destVar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcVHDL, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVHDL: str, destVar: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = srcVHDL[0] + srcVHDL[1]
        lines = []  # type: List[str]
        childNo = 0
        lines.append("{\n")
        lines.append("    unsigned choiceIdx = 0;\n")
        lines.append("    choiceIdx = ESAReadRegister(BASE_ADDR + %s);\n" % hex(register))
        for child in node._members:
            childNo += 1
            lines.append("    %sif (choiceIdx == %d) {\n" % (self.maybeElse(childNo), childNo))
            srcVHDL[0] += 4
            lines.extend(
                ['        ' + x
                 for x in self.Map(
                     srcVHDL,
                     destVar + ".u." + self.CleanName(child[0]),
                     child[1],
                     leafTypeDict,
                     names)])
            srcVHDL[0] -= 4
            lines.append("        %s.kind = %s;\n" % (destVar, self.CleanName(child[2])))
            lines.append("    }\n")
        lines.append("}\n")
        srcVHDL[0] += 4
        return lines

    def MapSequenceOf(self, srcVHDL: str, destVar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        # isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.extend(
                self.Map(
                    # isMappedToPrimitive and ("%s.element_data[%d]" % (srcVHDL, i)) or ("%s.element_%02d" % (srcVHDL, i)),
                    srcVHDL,
                    destVar + ".arr[%d]" % i,
                    node._containedType,
                    leafTypeDict,
                    names))
        if isSequenceVariable(node):
            lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapSetOf(self, srcVHDL: str, destVar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcVHDL, destVar, node, leafTypeDict, names)  # pragma: nocover


# noinspection PyListCreation
# pylint: disable=no-self-use
class FromASN1SCCtoVHDL(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, srcVar: str, dstVHDL: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = dstVHDL[0] + dstVHDL[1]
        lines = []  # type: List[str]
        lines.append("{\n")
        lines.append("    unsigned tmp, i;\n")
        lines.append("    asn1SccSint val = %s;\n" % srcVar)
        lines.append("    for(i=0; i<sizeof(asn1SccSint)/4; i++) {\n")
        lines.append("        tmp = val & 0xFFFFFFFF;\n")
        lines.append("        ESAWriteRegister(BASE_ADDR + %s + i*4, tmp);\n" % hex(register))
        lines.append("        val >>= 32;\n")
        lines.append("    }\n")
        lines.append("}\n")
        dstVHDL[0] += 8
        return lines

    def MapReal(self, dummy: str, _: str, node: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panicWithCallStack("REALs (%s) cannot be used for synthesizeable VHDL" % node.Location())  # pragma: no cover
        # return ["%s = %s;\n" % (dstVHDL, srcVar)]

    def MapBoolean(self, srcVar: str, dstVHDL: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = dstVHDL[0] + dstVHDL[1]
        lines = []  # type: List[str]
        lines.append("{\n")
        lines.append("    unsigned tmp = %s;\n" % srcVar)
        lines.append("    ESAWriteRegister(BASE_ADDR + %s, tmp);\n" % hex(register))
        lines.append("}\n")
        dstVHDL[0] += 4
        return lines

    def MapOctetString(self, srcVar: str, dstVHDL: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if isSequenceVariable(node):
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        register = dstVHDL[0] + dstVHDL[1]
        limit = sourceSequenceLimit(node, srcVar)
        lines = []  # type: List[str]
        for i in range(0, int((node._range[-1] + 3) / 4)):
            lines.append("{\n")
            lines.append("    unsigned tmp = 0;\n")
            for shift in range(0, 4):
                if i * 4 + shift < node._range[-1]:
                    if isSequenceVariable(node):
                        lines.append("    if (%s >= %d)\n" % (limit, i * 4 + shift + 1))
                        lines.append("        tmp |= ((unsigned)%s.arr[%d]) << %d;\n" % (srcVar, i * 4 + shift, shift * 8))
                    else:
                        lines.append("    tmp |= ((unsigned)%s.arr[%d]) << %d;\n" % (srcVar, i * 4 + shift, shift * 8))
            lines.append("    ESAWriteRegister(BASE_ADDR + %s + %d, tmp);\n" % (hex(register), i * 4))
            lines.append("}\n")
        dstVHDL[0] += 4 * int((node._range[-1] + 3) / 4)
        return lines

    def MapEnumerated(self, srcVar: str, dstVHDL: str, node: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if None in [x[1] for x in node._members]:
            panicWithCallStack("an ENUMERATED must have integer values! (%s)" % node.Location())  # pragma: no cover
        register = dstVHDL[0] + dstVHDL[1]
        lines = []  # type: List[str]
        lines.append("{\n")
        lines.append("    unsigned tmp = %s;\n" % srcVar)
        lines.append("    ESAWriteRegister(BASE_ADDR + %s, tmp);\n" % hex(register))
        lines.append("}\n")
        dstVHDL[0] += 4
        return lines

    def MapSequence(self, srcVar: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]),
                    dstVHDL,
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVar: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcVar, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar: str, dstVHDL: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = dstVHDL[0] + dstVHDL[1]
        lines = []  # type: List[str]
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.kind == %s) {\n" % (self.maybeElse(childNo), srcVar, self.CleanName(child[2])))
            lines.append("    unsigned tmp = %d;\n" % childNo)
            lines.append("    ESAWriteRegister(BASE_ADDR + %s, tmp);\n" % hex(register))
            dstVHDL[0] += 4
            lines.extend(
                ['    ' + x
                 for x in self.Map(
                     srcVar + ".u." + self.CleanName(child[0]),
                     dstVHDL,
                     child[1],
                     leafTypeDict,
                     names)])
            dstVHDL[0] -= 4
            lines.append("}\n")
        dstVHDL[0] += 4
        return lines

    def MapSequenceOf(self, srcVar: str, dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        # isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                srcVar + ".arr[%d]" % i,
                dstVHDL,
                # isMappedToPrimitive and ("%s.element_data[%d]" % (dstVHDL, i)) or ("%s.element_%02d" % (dstVHDL, i)),
                node._containedType,
                leafTypeDict,
                names))
        return lines

    def MapSetOf(self, srcVar: str, dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcVar, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


class VHDLGlueGenerator(SynchronousToolGlueGenerator):
    g_FVname = None  # type: str

    def Version(self):
        print("Code generator: " + "$Id: vhdl_B_mapper.py 2390 2012-07-19 12:39:17Z ttsiodras $")  # pragma: no cover

    def FromToolToASN1SCC(self):
        return FromVHDLToASN1SCC()

    def FromASN1SCCtoTool(self):
        return FromASN1SCCtoVHDL()

    def FromOSStoTool(self):
        pass  # pragma: no cover

    def FromToolToOSS(self):
        pass  # pragma: no cover

    def HeadersOnStartup(self, unused_modelingLanguage, unused_asnFile, subProgram, unused_subProgramImplementation, unused_outputDir, unused_maybeFVname):
        self.C_SourceFile.write("#include \"%s.h\" // Space certified compiler generated\n" % self.asn_name)
        self.C_SourceFile.write('''
#include "ESA_FPGA.h"

#ifndef STATIC
#define STATIC
#endif

#define BASE_ADDR  0x200

static int g_bFPGAexists = 0;
static int g_bInitialized = 0;

''')
        self.g_FVname = subProgram._id

    def SourceVar(self, unused_nodeTypename, unused_encoding, unused_node, subProgram, unused_subProgramImplementation, param, unused_leafTypeDict, unused_names):
        if isinstance(param._sourceElement, AadlPort):
            srcVHDL = [0, VHDL_Circuit.lookupSP[subProgram._id]._paramOffset[param._id]]  # pragma: no cover
        elif isinstance(param._sourceElement, AadlParameter):
            srcVHDL = [0, VHDL_Circuit.lookupSP[subProgram._id]._paramOffset[param._id]]
        else:  # pragma: no cover
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return srcVHDL

    def TargetVar(self, unused_nodeTypename, unused_encoding, unused_node, subProgram, unused_subProgramImplementation, param, unused_leafTypeDict, unused_names):
        if isinstance(param._sourceElement, AadlPort):
            dstVHDL = [0, VHDL_Circuit.lookupSP[subProgram._id]._paramOffset[param._id]]  # pragma: no cover
        elif isinstance(param._sourceElement, AadlParameter):
            dstVHDL = [0, VHDL_Circuit.lookupSP[subProgram._id]._paramOffset[param._id]]
        else:  # pragma: no cover
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return dstVHDL

    def InitializeBlock(self, unused_modelingLanguage, unused_asnFile, unused_sp, unused_subProgramImplementation, unused_maybeFVname):
        self.C_SourceFile.write('''
    if (g_bInitialized == 0) {
        if (Initialize_ESA_FPGA() != 1) {
            puts("Failure to initialize FPGA...");
            g_bFPGAexists = 0;
        } else
            g_bFPGAexists = 1;
        g_bInitialized = 1;
    }
''')

    def ExecuteBlock(self, unused_modelingLanguage, unused_asnFile, sp, unused_subProgramImplementation, unused_maybeFVname):
        self.C_SourceFile.write("    unsigned flag = 0;\n\n")
        self.C_SourceFile.write("    // Now that the parameters are passed inside the FPGA, run the processing logic\n")
        self.C_SourceFile.write("    ESAWriteRegister(BASE_ADDR + %s, (unsigned char)1);\n" %
                                hex(int(VHDL_Circuit.lookupSP[sp._id]._offset)))
        self.C_SourceFile.write("    // Poll FC bit\n")
        self.C_SourceFile.write("    while (!(flag & 4)) {\n")
        self.C_SourceFile.write("        // Wait for processing logic to complete\n")
        self.C_SourceFile.write("        flag = ESAReadRegister(BASE_ADDR + %s);\n" %
                                hex(int(VHDL_Circuit.lookupSP[sp._id]._offset)))
        self.C_SourceFile.write("    }\n\n")
        self.C_SourceFile.write("    ESAWriteRegister(BASE_ADDR + %s, (unsigned char)0);\n" %
                                hex(int(VHDL_Circuit.lookupSP[sp._id]._offset)))


# noinspection PyListCreation
# pylint: disable=no-self-use
class MapASN1ToVHDLCircuit(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, direction: str, dstVHDL: str, node: AsnInt, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        bits = math.log(max(abs(x) for x in node._range) + 1, 2)
        bits += bits if node._range[0] < 0 else 0
        # return [dstVHDL + ' : ' + direction + ('std_logic_vector(63 downto 0); -- normally, %d instead of 63' % bits)]
        return [dstVHDL + ' : ' + direction + ('std_logic_vector(63 downto 0); -- ASSERT uses 64 bit INTEGERs (optimal would be %d bits)' % bits)]

    def MapReal(self, _: str, __: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, direction: str, dstVHDL: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [dstVHDL + ' : ' + direction + 'std_logic;']

    def MapOctetString(self, direction: str, dstVHDL: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        lines.append(dstVHDL + ': ' + direction + 'octStr_%d;' % node._range[-1])
        return lines

    def MapEnumerated(self, direction: str, dstVHDL: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [dstVHDL + ' : ' + direction + 'std_logic_vector(7 downto 0);']

    def MapSequence(self, direction: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(direction, dstVHDL + "_" + CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, direction: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(direction, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, direction: str, dstVHDL: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        lines.append(dstVHDL + '_choiceIdx : ' + direction + 'std_logic_vector(7 downto 0);')
        lines.extend(self.MapSequence(direction, dstVHDL, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, direction: str, dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.extend(self.Map(
                direction, dstVHDL + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, direction: str, dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(direction, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


# noinspection PyListCreation
# pylint: disable=no-self-use
class MapASN1ToVHDLregisters(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, _: str, dstVHDL: str, node: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        bits = math.log(max(abs(x) for x in node._range) + 1, 2)
        bits += (bits if node._range[0] < 0 else 0)
        # return ['signal ' + dstVHDL + ' : ' + ('std_logic_vector(63 downto 0); -- normally, %d bits instead of 63' % bits)]
        return ['signal ' + dstVHDL + ' : ' + ('std_logic_vector(63 downto 0); -- ASSERT uses 64 bit INTEGERs (optimal would be %d bits)' % bits)]

    def MapReal(self, _: str, __: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, _: str, dstVHDL: str, __: AsnBool, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['signal ' + dstVHDL + ' : ' + 'std_logic;']

    def MapOctetString(self, _: str, dstVHDL: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        lines.append('signal ' + dstVHDL + ': ' + 'octStr_%d;' % node._range[-1])
        return lines

    def MapEnumerated(self, _: str, dstVHDL: str, __: AsnEnumerated, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['signal ' + dstVHDL + ' : ' + 'std_logic_vector(7 downto 0);']

    def MapSequence(self, _: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(_, dstVHDL + "_" + CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, _: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(_, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, _: str, dstVHDL: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        lines.append('signal ' + dstVHDL + '_choiceIdx : ' + 'std_logic_vector(7 downto 0);')
        lines.extend(self.MapSequence(_, dstVHDL, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, _: str, dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.extend(self.Map(
                _, dstVHDL + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, _: str, dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(_, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


# noinspection PyListCreation
# pylint: disable=no-self-use
class MapASN1ToVHDLreadinputdata(RecursiveMapperGeneric[List[int], str]):  # pylint: disable=invalid-sequence-index
    def MapInteger(self, reginfo: str, dstVHDL: str, node: AsnInt, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        # bits = math.log(max(map(abs, node._range)+1),2)+(1 if node._range[0]<0 else 0)
        lines = []  # type: List[str]
        lines.append('%s(31 downto  0) <= regs(%d);' % (dstVHDL, reginfo[0]))
        lines.append('%s(63 downto  32) <= regs(%d);' % (dstVHDL, reginfo[0] + 1))
        reginfo[0] += 2
        return lines

    def MapReal(self, _: str, __: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, reginfo: str, dstVHDL: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['%s <= regs(%d)(0);' % (dstVHDL, reginfo[0])]
        reginfo[0] += 1
        return lines

    def MapOctetString(self, reginfo: str, dstVHDL: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            realOffset = 4 * reginfo[0] + i
            bitStart = 31 - 8 * (realOffset % 4)
            bitEnd = bitStart - 7
            lines.append('%s(%d)(7 downto 0) <= regs(%d)(%d downto %d);' %
                         (dstVHDL, i, realOffset / 4, bitStart, bitEnd))
        reginfo[0] += (node._range[-1] + 3) / 4
        return lines

    def MapEnumerated(self, reginfo: str, dstVHDL: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['%s(7 downto 0) <= regs(%d)(7 downto 0);' % (dstVHDL, reginfo[0])]
        reginfo[0] += 1
        return lines

    def MapSequence(self, reginfo: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(reginfo, dstVHDL + "_" + CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, reginfo: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, reginfo: str, dstVHDL: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['%s_choiceIdx(7 downto 0) <= regs(%d)(7 downto 0);' % (dstVHDL, reginfo[0])]
        reginfo[0] += 1
        lines.extend(self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, reginfo: str, dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.extend(self.Map(
                reginfo, dstVHDL + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, reginfo: str, dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(reginfo, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


# noinspection PyListCreation
# pylint: disable=no-self-use
class MapASN1ToVHDLwriteoutputdata(RecursiveMapperGeneric[List[int], str]):  # pylint: disable=invalid-sequence-index
    def MapInteger(self, reginfo: str, dstVHDL: str, node: AsnInt, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        # bits = math.log(max(map(abs, node._range)+1),2)+(1 if node._range[0]<0 else 0)
        lines = []  # type: List[str]
        lines.append('regs(%d) := %s(31 downto  0);' % (reginfo[0], dstVHDL))
        lines.append('regs(%d) := %s(63 downto  32);' % (reginfo[0] + 1, dstVHDL))
        reginfo[0] += 2
        return lines

    def MapReal(self, _: str, __: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, reginfo: str, dstVHDL: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['regs(%d)(0) := %s;' % (reginfo[0], dstVHDL)]
        reginfo[0] += 1
        return lines

    def MapOctetString(self, reginfo: str, dstVHDL: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            realOffset = 4 * reginfo[0] + i
            bitStart = 31 - 8 * (realOffset % 4)
            bitEnd = bitStart - 7
            lines.append('regs(%d)(%d downto %d) := %s(%d)(7 downto 0);' %
                         (realOffset / 4, bitStart, bitEnd, dstVHDL, i))
        reginfo[0] += (node._range[-1] + 3) / 4
        return lines

    def MapEnumerated(self, reginfo: str, dstVHDL: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['regs(%d)(7 downto 0) := %s(7 downto 0);' % (reginfo[0], dstVHDL)]
        reginfo[0] += 1
        return lines

    def MapSequence(self, reginfo: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(reginfo, dstVHDL + "_" + CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, reginfo: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, reginfo: str, dstVHDL: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['regs(%d)(7 downto 0) := %s_choiceIdx(7 downto 0);' % (reginfo[0], dstVHDL)]
        reginfo[0] += 1
        lines.extend(self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, reginfo: str, dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.extend(self.Map(
                reginfo, dstVHDL + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, reginfo: str, dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(reginfo, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


# noinspection PyListCreation
# pylint: disable=no-self-use
class MapASN1ToSystemCconnections(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, srcRegister: str, dstCircuitPort: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [dstCircuitPort + ' => ' + srcRegister]

    def MapReal(self, _: str, __: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, srcRegister: str, dstCircuitPort: str, __: AsnBool, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [dstCircuitPort + ' => ' + srcRegister]

    def MapOctetString(self, srcRegister: str, dstCircuitPort: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        # for i in xrange(node._range[-1]):
        #     lines.append(dstCircuitPort + ('(%d)' % (i)) + ' => ' + srcRegister + ('(%d)' % (i)))
        lines.append(dstCircuitPort + ' => ' + srcRegister)
        return lines

    def MapEnumerated(self, srcRegister: str, dstCircuitPort: str, __: AsnEnumerated, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [dstCircuitPort + ' => ' + srcRegister]

    def MapSequence(self, srcRegister: str, dstCircuitPort: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(srcRegister + "_" + CleanName(x[0]), dstCircuitPort + "_" + CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, srcRegister: str, dstCircuitPort: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcRegister, dstCircuitPort, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcRegister: str, dstCircuitPort: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        lines.append(dstCircuitPort + '_choiceIdx => ' + srcRegister + '_choiceIdx')
        lines.extend(self.MapSequence(srcRegister, dstCircuitPort, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, srcRegister: str, dstCircuitPort: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.extend(self.Map(
                srcRegister + ('_elem_%0*d' % (maxlen, i)), dstCircuitPort + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, srcRegister: str, dstCircuitPort: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcRegister, dstCircuitPort, node, leafTypeDict, names)  # pragma: nocover


class SystemCheaderState:
    systemcHeader = None  # type: IO[Any]
    directionPrefix = None  # type: str


# pylint: disable=no-self-use
class MapASN1ToSystemCheader(RecursiveMapperGeneric[SystemCheaderState, str]):
    def MapInteger(self, state: str, systemCvar: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        state.systemcHeader.write('    ' + state.directionPrefix + 'sc_uint<64> > ' + systemCvar + ';\n')
        return []

    def MapReal(self, _: str, __: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, state: str, systemCvar: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        state.systemcHeader.write('    ' + state.directionPrefix + 'bool> ' + systemCvar + ';\n')
        return []

    def MapOctetString(self, state: str, systemCvar: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        for i in range(node._range[-1]):
            state.systemcHeader.write('    ' + state.directionPrefix + 'sc_uint<8> > ' + ('%s_elem_%0*d' % (systemCvar, maxlen, i)) + ';\n')
        return []

    def MapEnumerated(self, state: str, systemCvar: str, __: AsnEnumerated, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        state.systemcHeader.write('    ' + state.directionPrefix + 'sc_uint<8> > ' + systemCvar + ';\n')
        return []

    def MapSequence(self, state: str, systemCvar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        for x in node._members:
            self.Map(state, systemCvar + "_" + CleanName(x[0]), x[1], leafTypeDict, names)
        return []

    def MapSet(self, state: str, systemCvar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(state, systemCvar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, state: str, systemCvar: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        state.systemcHeader.write('    ' + state.directionPrefix + 'sc_uint<8> >' + systemCvar + '_choiceIdx;\n')
        self.MapSequence(state, systemCvar, node, leafTypeDict, names)
        return []

    def MapSequenceOf(self, state: str, systemCvar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        for i in range(node._range[-1]):
            self.Map(state, systemCvar + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names)
        return []

    def MapSetOf(self, state: str, systemCvar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(state, systemCvar, node, leafTypeDict, names)  # pragma: nocover


# pylint: disable=no-self-use
class MapASN1ToOutputs(RecursiveMapperGeneric[str, int]):
    def MapInteger(self, paramName: str, _: str, dummy: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [paramName]

    def MapReal(self, _: str, __: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, paramName: str, _: str, dummy: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [paramName]

    def MapOctetString(self, paramName: str, _: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        # maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.append('%s(%d)' % (paramName, i))
        return lines

    def MapEnumerated(self, paramName: str, dummy: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = [paramName]
        return lines

    def MapSequence(self, paramName: str, dummy: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(paramName + "_" + CleanName(x[0]), dummy, x[1], leafTypeDict, names))
        return lines

    def MapSet(self, paramName: str, dummy: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(paramName, dummy, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, paramName: str, dummy: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['%s_choiceIdx' % paramName]
        lines.extend(self.MapSequence(paramName, dummy, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, paramName: str, dummy: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.extend(self.Map(paramName + ('_elem_%0*d' % (maxlen, i)), dummy, node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, reginfo: str, dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(reginfo, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


g_placeholders = {
    "pi": '',
    "circuits": '',
    "entities": '',
    "ioregisters": '',
    "startStopSignals": '',
    "reset": '',
    "octStr": '',
    "updateStartStopPulses": '',
    "readinputdata": '',
    "outputs": '',
    "completions": '',
    "writeoutputdata": '',
    "clearoutputs": '',
    "connectionsToSystemC": '',
    "updateClockedPulses": '',
    "updatePulseHistories": '',
    "numberOfInputRegisters": ''
}


def AddToStr(s, d):
    g_placeholders[s] += d


def Common(nodeTypename, node, subProgram, unused_subProgramImplementation, param, leafTypeDict, names):
    if subProgram._id not in VHDL_Circuit.lookupSP:
        VHDL_Circuit.currentCircuit = VHDL_Circuit(subProgram)
    VHDL_Circuit.currentCircuit.AddParam(nodeTypename, node, param, leafTypeDict, names)


def OnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS):
    global vhdlBackend
    vhdlBackend = VHDLGlueGenerator()
    vhdlBackend.OnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS)


def OnBasic(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnBasic(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequence(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnSequence(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover
    vhdlBackend.OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover
    vhdlBackend.OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnChoice(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnShutdown(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname):
    vhdlBackend.OnShutdown(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname)


def OnFinal():
    circuitMapper = MapASN1ToVHDLCircuit()
    ioRegisterMapper = MapASN1ToVHDLregisters()
    readinputdataMapper = MapASN1ToVHDLreadinputdata()
    writeoutputdataMapper = MapASN1ToVHDLwriteoutputdata()
    connectionsToSystemCMapper = MapASN1ToSystemCconnections()
    systemCheaderMapper = MapASN1ToSystemCheader()
    outputsMapper = MapASN1ToOutputs()

    outputs = []
    completions = []

    systemcHeader = open(vhdlBackend.dir + 'circuit.h', 'w')
    systemcHeader.write('#ifndef CIRCUIT_H\n')
    systemcHeader.write('#define CIRCUIT_H\n\n')
    systemcHeader.write('#ifndef SC_SYNTHESIS\n')
    systemcHeader.write('#include "systemc.h"\n')
    systemcHeader.write('#endif\n\n')

    systemcBody = open(vhdlBackend.dir + 'circuit.cpp', 'w')
    systemcBody.write('#include "circuit.h"\n\n')

    if len(VHDL_Circuit.allCircuits) > 1:
        panic("The ESA VHDL mapper can currently handle only one circuit.")  # pragma: no cover

    totalIn = 0
    for p in VHDL_Circuit.allCircuits[0]._sp._params:
        if isinstance(p, InParam) or isinstance(p, InOutParam):
            totalIn += RegistersAllocated(p._signal._asnNodename)
    AddToStr('numberOfInputRegisters', str(totalIn / 4))

    for v in sorted(g_octStr):
        AddToStr('octStr', '  type octStr_%d is array (0 to %d) of std_logic_vector(7 downto 0);\n' %
                 (v, v - 1))

    for c in VHDL_Circuit.allCircuits:
        circuitLines = []

        ioregisterLines = []

        readinputdataLines = []

        connectionsToSystemCLines = []

        counter = cast(List[int], [int(c._offset + 4) / 4])  # type: List[int]  # pylint: disable=invalid-sequence-index
        for p in c._sp._params:
            node = VHDL_Circuit.names[p._signal._asnNodename]
            direction = "in " if isinstance(p, InParam) else "out "
            circuitLines.extend(
                circuitMapper.Map(
                    direction, p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
            ioregisterLines.extend(
                ioRegisterMapper.Map(
                    direction, c._spCleanName + '_' + p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))

            connectionsToSystemCLines.extend(
                connectionsToSystemCMapper.Map(
                    c._spCleanName + '_' + p._id, p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))

            if isinstance(p, InParam):
                readinputdataLines.extend(
                    readinputdataMapper.Map(
                        counter, c._spCleanName + '_' + p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
            else:
                outputs.extend([c._spCleanName + '_' + x for x in outputsMapper.Map(p._id, 1, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names)])

        writeoutputdataLines = []

        for p in c._sp._params:
            node = VHDL_Circuit.names[p._signal._asnNodename]
            if not isinstance(p, InParam):
                writeoutputdataLines.extend(
                    writeoutputdataMapper.Map(
                        counter, c._spCleanName + '_' + p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))

        completions.append(c._spCleanName + '_CalculationsComplete')

        AddToStr('pi', c._spCleanName)

        AddToStr('circuits', '        component %s is\n' % c._spCleanName)
        AddToStr('circuits', '        port (\n')
        AddToStr('circuits', '\n'.join(['            ' + x for x in circuitLines]) + '\n')
        AddToStr('circuits', '            start_%s  : in  std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '            finish_%s : out std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '            rst_%s    : in std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '            clk_%s    : in  std_logic\n' % c._spCleanName)
        AddToStr('circuits', '        );\n')
        AddToStr('circuits', '        end component;\n\n')

        AddToStr('entities', '        entity %s is\n' % c._spCleanName)
        AddToStr('entities', '        port (\n')
        AddToStr('entities', '\n'.join(['            ' + x for x in circuitLines]) + '\n')
        AddToStr('entities', '            start_%s  : in  std_logic;\n' % c._spCleanName)
        AddToStr('entities', '            finish_%s : out std_logic;\n' % c._spCleanName)
        AddToStr('entities', '            rst_%s    : in std_logic;\n' % c._spCleanName)
        AddToStr('entities', '            clk_%s    : in  std_logic\n' % c._spCleanName)
        AddToStr('entities', '        );\n')
        AddToStr('entities', '        end %s;\n\n' % c._spCleanName)

        AddToStr('ioregisters', '\n'.join(['        ' + x for x in ioregisterLines]) + '\n\n')

        AddToStr('startStopSignals', '''        signal %(pi)s_start : std_logic;
        signal %(pi)s_finish : std_logic;
''' % {'pi': c._spCleanName})

        AddToStr('reset', "                        %(pi)s_start <= '0';\n" % {'pi': c._spCleanName})

        AddToStr('readinputdata', '\n'.join([' ' * 24 + x for x in readinputdataLines]) + '\n')
        AddToStr('writeoutputdata', '\n'.join([' ' * 24 + x for x in writeoutputdataLines]) + '\n')

        AddToStr('connectionsToSystemC', '\n        Interface_%s : %s\n' % (c._spCleanName, c._spCleanName))
        AddToStr('connectionsToSystemC', '            port map (\n')
        AddToStr('connectionsToSystemC', ',\n'.join(['                ' + x for x in connectionsToSystemCLines]) + ',\n')
        AddToStr('connectionsToSystemC', '                start_%s => %s_start,\n' % (c._spCleanName, c._spCleanName))
        AddToStr('connectionsToSystemC', '                finish_%s => %s_finish,\n' % (c._spCleanName, c._spCleanName))
        AddToStr('connectionsToSystemC', '                rst_%s => rst,\n' % c._spCleanName)
        AddToStr('connectionsToSystemC', '                clk_%s => clk\n' % c._spCleanName)
        AddToStr('connectionsToSystemC', '            );\n')

        systemcHeader.write('class ' + c._spCleanName + ' : public sc_module\n')
        systemcHeader.write('{\n')
        systemcHeader.write('public:\n')
        for p in c._sp._params:
            node = VHDL_Circuit.names[p._signal._asnNodename]
            prefix = 'sc_in<' if isinstance(p, InParam) else 'sc_out<'

            state = SystemCheaderState()
            state.systemcHeader = systemcHeader
            state.directionPrefix = prefix
            systemCheaderMapper.Map(
                state,
                p._id,
                node,
                VHDL_Circuit.leafTypeDict,
                VHDL_Circuit.names)
        systemcHeader.write('''
    sc_in<bool>          start_%(PI)s;
    sc_out<bool>         finish_%(PI)s;
    sc_in<bool>          clock_%(PI)s;

    void do_%(PI)s ();

    SC_CTOR (%(PI)s)
    {
        SC_THREAD(do_%(PI)s);
        sensitive_pos << clock_%(PI)s;
    }
''' % {'PI': c._spCleanName})
        systemcHeader.write('};\n\n')

        systemcBody.write('void %s::do_%s()\n' % (c._spCleanName, c._spCleanName))
        systemcBody.write('{\n')
        systemcBody.write('    // Declare your variables here\n')
        systemcBody.write('    finish_%s = 0;\n' % c._spCleanName)
        systemcBody.write('    while (1) {\n')
        systemcBody.write('        do {\n')
        systemcBody.write('            wait();\n')
        systemcBody.write('        } while (!start_%s.read());\n' % c._spCleanName)
        systemcBody.write('        finish_%s = 0;\n\n' % c._spCleanName)
        systemcBody.write('        // Write your processing logic here\n')
        for p in c._sp._params:
            if not isinstance(p, OutParam):
                systemcBody.write('        // Read data from %s\n' % CleanName(p._id))
        systemcBody.write('        // ...\n\n')
        for p in c._sp._params:
            if isinstance(p, OutParam):
                systemcBody.write('        // Write result for %s\n' % CleanName(p._id))
        systemcBody.write('        finish_%s = 1;\n' % c._spCleanName)
        systemcBody.write('        wait();\n')
        systemcBody.write('    }\n')
        systemcBody.write('}\n\n')

    AddToStr('outputs', ', '.join(outputs) + (', ' if len(outputs) else ''))
    AddToStr('completions', ', '.join(completions))

    from . import vhdlTemplate

    os.mkdir(vhdlBackend.dir + "/VHDL")
    os.system("tar -C \"" + vhdlBackend.dir + "/\" -jxf $DMT/aadl2glueC/VHDL-templates.tar.bz2")

    # vhdlFile = open(vhdlBackend.dir + 'TASTE.vhd', 'w')
    # vhdlFile.write( vhdlTemplate.vhd % g_placeholders )
    # vhdlFile.close()

    apbWrapper = open(vhdlBackend.dir + 'VHDL/APB wrapper/apbwrapper.vhd', 'a')
    apbWrapper.write(vhdlTemplate.apbwrapper % g_placeholders)
    apbWrapper.close()

    apbwrapper_declaration = open(vhdlBackend.dir + 'VHDL/APB wrapper/apbwrapper_declaration.vhd', 'w')
    apbwrapper_declaration.write(vhdlTemplate.apbwrapper_declaration % g_placeholders)
    apbwrapper_declaration.close()

    architecture_top = open(vhdlBackend.dir + 'VHDL/Top architecture/architecture_top.vhd', 'w')
    architecture_top.write(vhdlTemplate.architecture_top % g_placeholders)
    architecture_top.close()

    architecture_config = open(vhdlBackend.dir + 'VHDL/Top architecture/architecture_config.vhd', 'w')
    architecture_config.write(vhdlTemplate.architecture_config % g_placeholders)
    architecture_config.close()

    customip2 = open(vhdlBackend.dir + 'VHDL/Custom IP/customip2.vhd', 'w')
    customip2.write(vhdlTemplate.customip2 % g_placeholders)
    customip2.close()

    esaHeader = open(vhdlBackend.dir + 'ESA_FPGA.h', 'w')
    esaHeader.write('''#ifndef __ESA_FPGA_H__
#define __ESA_FPGA_H__

// Returns 1 for OK, 0 for error (i.e. PCI id not found)
int Initialize_ESA_FPGA();

// Reads 32bits of data from the offset (which must be a multiple of 4)
unsigned ESAReadRegister(unsigned offset);

// Writes 32bits of data to the offset (which must be a multiple of 4)
void ESAWriteRegister(unsigned offset, unsigned value);

#endif
''')
    esaHeader.close()

    # msg = ""
    # for c in VHDL_Circuit.allCircuits:
    #     msg += '    circuit_%s.vhd         \\\n' % c._spCleanName
    #     msg += '    circuit_%s_do_%s.vhd   \\\n' % (c._spCleanName, c._spCleanName)
    # makefile = open(vhdlBackend.dir + 'Makefile', 'w')
    # makefile.write(vhdlTemplate.makefile % {'circuit_autofiles':msg})
    # makefile.close()

    # systemcHeader.write('\n#endif\n')
    # systemcHeader.close()

    # msg = ""
    # for c in VHDL_Circuit.allCircuits:
    #     msg += 'vhdl work "circuit_%s.vhd"\n' % c._spCleanName
    #     msg += 'vhdl work "circuit_%s_do_%s.vhd"\n' % (c._spCleanName, c._spCleanName)
    # prj = open(vhdlBackend.dir + 'TASTE.prj', 'w')
    # prj.write(vhdlTemplate.prj % {'circuits':msg})
    # prj.close()
