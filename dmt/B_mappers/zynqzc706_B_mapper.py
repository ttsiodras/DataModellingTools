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

This code generator supports both UPER and Native encodings.

Matlab/Simulink is a member of the synchronous "club" (SCADE, etc) ;
The subsystem developer (or rather, the APLC developer) is
building a model in Simulink, and the generated code is offered
in the form of a "function" that does all the work.
To that end, we create "glue" functions for input and output
parameters, which have C callable interfaces. The necessary
stubs (to allow calling from the VM side) are also generated.
'''

'''
Status: Device driver side (PS, ARM) calls to AXI are still to be implemented. Hence such AXI writes/reads are temporarily commented out.
TODO This and other possibly needed libraries will soon be linked and included with the exported device driver.
'''

import os
import re
import math

from typing import cast, Union, List, Tuple, IO, Any, Dict  # NOQA pylint: disable=unused-import

from ..commonPy.utility import panic, panicWithCallStack
from ..commonPy.asnAST import (
    AsnBasicNode, AsnInt, AsnSequence, AsnSet, AsnChoice, AsnSequenceOf,
    AsnSetOf, AsnEnumerated, AsnMetaMember, isSequenceVariable,
    sourceSequenceLimit, AsnNode, AsnString, AsnReal, AsnOctetString,
    AsnSequenceOrSetOf, AsnSequenceOrSet, AsnBool)
from ..commonPy.asnParser import AST_Lookup, AST_Leaftypes
from ..commonPy.aadlAST import (
    InParam, OutParam, AadlPort, AadlParameter,
)
from ..commonPy.aadlAST import Param, ApLevelContainer  # NOQA pylint: disable=unused-import
from ..commonPy import asnParser

from ..commonPy.recursiveMapper import RecursiveMapperGeneric
from .synchronousTool import SynchronousToolGlueGeneratorGeneric


isAsynchronous = False
vhdlBackend = None


def Version() -> None:
    print("Code generator: " + "$Id: zynqzc706_B_mapper.py 2019-2020 tmsj@gmv $")  # pragma: no cover


def CleanName(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def RegistersAllocated(node_or_str: Union[str, AsnNode]) -> int:
    names = asnParser.g_names
    if isinstance(node_or_str, str):
        node = names[node_or_str]  # type: AsnNode
    else:
        node = node_or_str
    retValue = None
    if isinstance(node, AsnBasicNode):
        retValue = 0
        realLeafType = asnParser.g_leafTypeDict[node._leafType]
        if realLeafType == "INTEGER":
            retValue = 8
        elif realLeafType == "REAL":
            panic("The VHDL mapper can't work with REALs (non-synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover
        elif realLeafType == "BOOLEAN":
            retValue = 1
        elif realLeafType == "OCTET STRING":
            nodeOct = cast(AsnString, node)
            if not nodeOct._range:
                panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
            if len(nodeOct._range) > 1 and nodeOct._range[0] != nodeOct._range[1]:
                panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
            retValue = nodeOct._range[-1]
        else:  # pragma: no cover
            panicWithCallStack("Basic type %s can't be mapped..." % realLeafType)  # pragma: no cover
    elif isinstance(node, (AsnSequence, AsnSet)):
        retValue = sum(RegistersAllocated(x[1]) for x in node._members)
    elif isinstance(node, AsnChoice):
        retValue = 1 + sum(RegistersAllocated(x[1]) for x in node._members)
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
        retValue = 1
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

    def __init__(self, sp: ApLevelContainer) -> None:
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

    def __str__(self) -> str:
        msg = "PI:%s\n" % self._sp._id  # pragma: no cover
        msg += ''.join([p[0]._id + ':' + p[0]._signal._asnNodename + ("(in)" if isinstance(p[0], InParam) else "(out)") + '\n' for p in self._params])  # pragma: no cover
        return msg  # pragma: no cover

    def AddParam(self, nodeTypename: str, node: AsnNode, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        VHDL_Circuit.names = names
        VHDL_Circuit.leafTypeDict = leafTypeDict
        self._params.append((param, nodeTypename, node))


# pylint: disable=no-self-use
class FromVHDLToASN1SCC(RecursiveMapperGeneric[List[int], str]):  # pylint: disable=invalid-sequence-index
    def MapInteger(self, srcVHDL: List[int], destVar: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = srcVHDL[0] + srcVHDL[1]
        lines = []  # type: List[str]
        lines.append("{\n")
        lines.append("    unsigned long long tmp;\n")
        lines.append("    unsigned int i;\n")
        lines.append("    asn1SccSint val = 0;\n")
        lines.append("    for(i=0; i<sizeof(asn1SccSint)/4; i++) {\n")
        lines.append("        //axi_read(R_AXI_BASEADR + %s + (i*4), &tmp, 4, R_AXI_DSTADR);\n" % hex(register))
        lines.append("        tmp = rtems_axi_read32(R_AXI_BASEADR + %s + (i*4));\n" % hex(register))
        lines.append("        tmp >>= 32; // ?\n")
        lines.append("        val |= (tmp << (32*i));\n")
        lines.append("    }\n")
        lines.append("    %s = val;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 8
        return lines

    def MapReal(self, dummy: List[int], _: str, node: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panicWithCallStack("REALs (%s) cannot be used for synthesizeable VHDL" % node.Location())  # pragma: no cover
        # return ["%s = (double) %s;\n" % (destVar, srcVHDL)]

    def MapBoolean(self, srcVHDL: List[int], destVar: str, node: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = srcVHDL[0] + srcVHDL[1]
        lines = []  # type: List[str]        
        lines.append("{\n")
        lines.append("    unsigned int tmp = 0;\n")
        lines.append("    //axi_read(R_AXI_BASEADR + %s, &tmp, 4, R_AXI_DSTADR);\n" % hex(register))
        lines.append("    tmp = rtems_axi_read32(R_AXI_BASEADR + %s + (i*4));\n" % hex(register))
        lines.append("    %s = (asn1SccUint) tmp;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 4
        return lines

    def MapOctetString(self, srcVHDL: List[int], destVar: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        if isSequenceVariable(node):
            panicWithCallStack("OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        if node._range[-1] % 4 != 0: # TODO
            panicWithCallStack("OCTET STRING (in %s) is not a multiple of 4 bytes (this is not yet supported)." % node.Location())            

        register = srcVHDL[0] + srcVHDL[1]
        lines = []  # type: List[str]
        
        lines.append("{\n")
        lines.append("    unsigned int tmp, i;\n")
        lines.append("    for(i=0; i<%d; i++) {\n" % int(node._range[-1] / 4))
        lines.append("        tmp = 0;\n")
        lines.append("        //axi_read(R_AXI_BASEADR + %s + (i*4), &tmp, 4, R_AXI_DSTADR);\n" % hex(register))
        lines.append("        tmp = rtems_axi_read32(R_AXI_BASEADR + %s + (i*4));\n" % hex(register))
        lines.append("        memcpy(%s.arr + (i*4), (unsigned char*)&tmp, sizeof(unsigned int));\n" % destVar)
        lines.append("    }\n")
        lines.append("}\n")
        
        srcVHDL[0] += node._range[-1]
        return lines

    def MapEnumerated(self, srcVHDL: List[int], destVar: str, node: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = srcVHDL[0] + srcVHDL[1]
        lines = []  # type: List[str]        
        lines.append("{\n")
        lines.append("    unsigned int tmp;\n")
        lines.append("    //axi_read(R_AXI_BASEADR + %s, &tmp, 4, R_AXI_DSTADR);\n" % hex(register))  
        lines.append("    tmp = rtems_axi_read32(R_AXI_BASEADR + %s);\n" % hex(register))
        lines.append("    %s = tmp;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 4
        return lines

    def MapSequence(self, srcVHDL: List[int], destVar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
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

    def MapSet(self, srcVHDL: List[int], destVar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcVHDL, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVHDL: List[int], destVar: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panicWithCallStack("CHOICEs (%s) not yet supported." % node.Location())  # pragma: no cover
        register = srcVHDL[0] + srcVHDL[1]
        lines = []  # type: List[str]
        childNo = 0
        lines.append("{\n")
        lines.append("    unsigned char choiceIdx = 0;\n")
        #lines.append("    ZynQZC706ReadRegister(g_Handle, BASE_ADDR + %s, &choiceIdx);\n" % hex(register))
        if len(node._members) > 255:
            panic("Up to 255 different CHOICEs can be supported (%s)" % node.Location())  # pragma: no cover
        for child in node._members:
            childNo += 1
            lines.append("    %sif (choiceIdx == %d) {\n" % (self.maybeElse(childNo), childNo))
            lines.extend(
                ['        ' + x
                 for x in self.Map(
                     srcVHDL,
                     destVar + ".u." + self.CleanName(child[0]),
                     child[1],
                     leafTypeDict,
                     names)])
            lines.append("        %s.kind = %s;\n" % (destVar, self.CleanName(child[2])))
            lines.append("    }\n")
        lines.append("}\n")
        srcVHDL[0] += 1
        return lines

    def MapSequenceOf(self, srcVHDL: List[int], destVar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.extend(
                self.Map(
                    srcVHDL,
                    destVar + ".arr[%d]" % i,
                    node._containedType,
                    leafTypeDict,
                    names))
        if isSequenceVariable(node):
            lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapSetOf(self, srcVHDL: List[int], destVar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcVHDL, destVar, node, leafTypeDict, names)  # pragma: nocover


# pylint: disable=no-self-use
class FromASN1SCCtoVHDL(RecursiveMapperGeneric[str, List[int]]):  # pylint: disable=invalid-sequence-index
    def MapInteger(self, srcVar: str, dstVHDL: List[int], _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = dstVHDL[0] + dstVHDL[1]
        lines = []  # type: List[str]
        lines.append("{\n")
        lines.append("    unsigned int tmp, i;\n")
        lines.append("    asn1SccSint val = %s;\n" % srcVar)
        lines.append("    for(i=0; i<sizeof(asn1SccSint)/4; i++) {\n")
        lines.append("        tmp = val & 0xFFFFFFFF;\n")
        lines.append("        //axi_write(R_AXI_BASEADR + %s + (i*4), &tmp, 4, R_AXI_DSTADR);\n" % hex(register))
        lines.append("        rtems_axi_write32(AXI_BANK_IP  + %s + (i*4), tmp);\n" % hex(register))
        lines.append("        val >>= 32;\n")
        lines.append("    }\n")
        lines.append("}\n")
        dstVHDL[0] += 8
        return lines

    def MapReal(self, dummy: str, _: List[int], node: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panicWithCallStack("REALs (%s) cannot be used for synthesizeable VHDL" % node.Location())  # pragma: no cover

    def MapBoolean(self, srcVar: str, dstVHDL: List[int], _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = dstVHDL[0] + dstVHDL[1]
        lines = []  # type: List[str]
        lines.append("{\n")
        lines.append("    unsigned int tmp = (unsigned int)%s;\n" % srcVar)
        lines.append("    //axi_write(R_AXI_BASEADR + %s, &tmp, 4, R_AXI_DSTADR);\n" % hex(register))
        lines.append("    rtems_axi_write32(AXI_BANK_IP  + %s, tmp);\n" % hex(register))
        lines.append("}\n")
        dstVHDL[0] += 4
        return lines

    def MapOctetString(self, srcVar: str, dstVHDL: List[int], node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if isSequenceVariable(node):
            panicWithCallStack("OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        if node._range[-1] % 4 != 0:  # TODO
            panicWithCallStack("OCTET STRING (in %s) is not a multiple of 4 bytes (this is not yet supported)." % node.Location())

        register = dstVHDL[0] + dstVHDL[1]
        lines = []  # type: List[str]

        lines.append("{\n")
        lines.append("    unsigned int tmp, i;\n")
        lines.append("    for(i=0; i<%d; i++) {\n" % int(node._range[-1] / 4))
        lines.append("        tmp = 0;\n")
        lines.append("        tmp = *(unsigned int*)(%s.arr + (i*4));\n" % srcVar)
        lines.append("        //axi_write(R_AXI_BASEADR + %s + (i*4), &tmp, 4, R_AXI_DSTADR);\n" % hex(register)) 
        lines.append("        rtems_axi_write32(AXI_BANK_IP  + %s + (i*4), tmp);\n" % hex(register))
        lines.append("    }\n")
        lines.append("}\n")

        dstVHDL[0] += node._range[-1]
        return lines

    def MapEnumerated(self, srcVar: str, dstVHDL: List[int], node: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if None in [x[1] for x in node._members]:
            panicWithCallStack("an ENUMERATED must have integer values! (%s)" % node.Location())  # pragma: no cover
        register = dstVHDL[0] + dstVHDL[1]
        lines = []  # type: List[str]
        lines.append("{\n")
        lines.append("    unsigned int tmp = (unsigned int)%s;\n" % srcVar)
        lines.append("    //axi_write(R_AXI_BASEADR + %s, &tmp, 4, R_AXI_DSTADR);\n" % hex(register))
        lines.append("    rtems_axi_write32(AXI_BANK_IP  + %s, tmp);\n" % hex(register))
        lines.append("}\n")
        dstVHDL[0] += 4
        return lines

    def MapSequence(self, srcVar: str, dstVHDL: List[int], node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
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

    def MapSet(self, srcVar: str, dstVHDL: List[int], node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcVar, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar: str, dstVHDL: List[int], node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = dstVHDL[0] + dstVHDL[1]
        lines = []  # type: List[str]
        childNo = 0
        if len(node._members) > 255:
            panic("Up to 255 different CHOICEs can be supported (%s)" % node.Location())  # pragma: no cover
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.kind == %s) {\n" % (self.maybeElse(childNo), srcVar, self.CleanName(child[2])))
            lines.append("    unsigned char tmp = %d;\n" % childNo)
            #lines.append("    ZynQZC706WriteRegister(g_Handle, BASE_ADDR + %s, tmp);\n" % hex(register))
            lines.extend(
                ['    ' + x
                 for x in self.Map(
                     srcVar + ".u." + self.CleanName(child[0]),
                     dstVHDL,
                     child[1],
                     leafTypeDict,
                     names)])
            lines.append("}\n")
        dstVHDL[0] += 1
        return lines

    def MapSequenceOf(self, srcVar: str, dstVHDL: List[int], node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
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
                node._containedType,
                leafTypeDict,
                names))
        return lines

    def MapSetOf(self, srcVar: str, dstVHDL: List[int], node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcVar, dstVHDL, node, leafTypeDict, names)


class VHDLGlueGenerator(SynchronousToolGlueGeneratorGeneric[List[int], List[int]]):  # pylint: disable=invalid-sequence-index
    def Version(self) -> None:
        print("Code generator: " + "$Id: vhdl_B_mapper.py 1754 2009-12-26 13:02:45Z ttsiodras $")  # pragma: no cover

    def FromToolToASN1SCC(self) -> RecursiveMapperGeneric[List[int], str]:  # pylint: disable=invalid-sequence-index
        return FromVHDLToASN1SCC()

    def FromASN1SCCtoTool(self) -> RecursiveMapperGeneric[str, List[int]]:  # pylint: disable=invalid-sequence-index
        return FromASN1SCCtoVHDL()

    # def HeadersOnStartup(self, modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname):
    def HeadersOnStartup(self, unused_modelingLanguage: str, unused_asnFile: str, unused_subProgram: ApLevelContainer, unused_subProgramImplementation: str, unused_outputDir: str, unused_maybeFVname: str) -> None:
        self.C_SourceFile.write("#include \"%s.h\" // Space certified compiler generated\n" % self.asn_name)
        self.C_SourceFile.write('''

#include <stdio.h>
#include <string.h>

#ifndef STATIC
#define STATIC
#endif

#define LOGERRORS
#define LOGWARNINGS
#define LOGINFOS
//#define LOGDEBUGS

#ifdef LOGERRORS
#define LOGERROR(x...) printf(x)
#else
#define LOGERROR(x...)
#endif
#ifdef LOGWARNINGS
#define LOGWARNING(x...) printf(x)
#else
#define LOGWARNING(x...)
#endif
#ifdef LOGINFOS
#define LOGINFO(x...) printf(x)
#else
#define LOGINFO(x...)
#endif
#ifdef LOGDEBUGS
#define LOGDEBUG(x...) printf(x)
#else
#define LOGDEBUG(x...)
#endif

// ZYNQZC706 device driver considers different possible FPGA status
// See for instance device drivers' function <Function Block name>_<PI name>_ZynQZC706_Fpga (invoked by dispatcher when delegation is to HW)
// and that first checks if FPGA is "ready" before converting parameters and initiating AXI exchanges with HW
// This status is to be maintained by a dedicated component acting as the FPGA reconfiguration manager and that "watchdogs" the HW component
#define FPGA_READY              "ready"
#define FPGA_RECONFIGURING      "reconfiguring"
#define FPGA_ERROR              "error"
#define FPGA_DISABLED           "disabled"

#define RETRIES                 200

#ifdef _WIN32

// For testing under the Redmond OS

static unsigned int bswap32(unsigned int x)
{
    return  ((x << 24) & 0xff000000 ) |
        ((x <<  8) & 0x00ff0000 ) |
        ((x >>  8) & 0x0000ff00 ) |
        ((x >> 24) & 0x000000ff );
}

static long long bswap64(long long x)
{
    unsigned  *p = (unsigned*)(void *)&x;
    unsigned t;
    t = bswap32(p[0]);
    p[0] = bswap32(p[1]);
    p[1] = t;
    return x;
}

#define __builtin_bswap64 bswap64

#endif

unsigned int count;

// include any needed lib headers
// #include "axi123.h"
#include <rtems.h>

#define R_AXI_DSTADR 0xfe
#define R_AXI_BASEADR 0x80000300
//unsigned int axi_base_address = R_AXI_BASEADR; /* Base address on Remote. This is the address to which the data is copied. */
//unsigned int axi_dst_address = R_AXI_DSTADR; /* AXI Destination address. */

/* NOTICE: the clock driver is explicitly disabled */
#define XPAR_TASTE_0_BASEADDR 0x43C00000 //this is cheating, from Xilinx generated h file

#define BUS_ALIGNEMENT                4
#define AXI_BANK_IP                 XPAR_TASTE_0_BASEADDR
#define START_ADD                    0x00000300

static inline uint32_t rtems_axi_read32(uintptr_t Addr)
{
    return *(volatile uint32_t *) Addr;
}

static inline void rtems_axi_write32(uintptr_t Addr, uint32_t Value)
{
    volatile uint32_t *LocalAddr = (volatile uint32_t *)Addr;
    *LocalAddr = Value;
    rtems_task_wake_after(1);
}

''')
        # self.g_FVname = subProgram._id

    # def SourceVar(self, nodeTypename, encoding, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    def SourceVar(self, unused_nodeTypename: str, unused_encoding: str, unused_node: AsnNode, subProgram: ApLevelContainer, unused_subProgramImplementation: str, param: Param, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> List[int]:  # pylint: disable=invalid-sequence-index
        if isinstance(param._sourceElement, AadlPort):
            srcVHDL = [0, VHDL_Circuit.lookupSP[subProgram._id]._paramOffset[param._id]]  # pragma: no cover
        elif isinstance(param._sourceElement, AadlParameter):
            srcVHDL = [0, VHDL_Circuit.lookupSP[subProgram._id]._paramOffset[param._id]]
        else:  # pragma: no cover
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return srcVHDL

    # def TargetVar(self, nodeTypename, encoding, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    def TargetVar(self, unused_nodeTypename: str, unused_encoding: str, unused_node: AsnNode, subProgram: ApLevelContainer, unused_subProgramImplementation: str, param: Param, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> List[int]:  # pylint: disable=invalid-sequence-index
        if isinstance(param._sourceElement, AadlPort):
            dstVHDL = [0, VHDL_Circuit.lookupSP[subProgram._id]._paramOffset[param._id]]  # pragma: no cover
        elif isinstance(param._sourceElement, AadlParameter):
            dstVHDL = [0, VHDL_Circuit.lookupSP[subProgram._id]._paramOffset[param._id]]
        else:  # pragma: no cover
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return dstVHDL

    # def InitializeBlock(self, modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname):
    def InitializeBlock(self, unused_modelingLanguage: str, unused_asnFile: str, unused_sp: ApLevelContainer, unused_subProgramImplementation: str, unused_maybeFVname: str) -> None:
        self.C_SourceFile.write('''    LOGINFO("[ ********* %s Init ********* ] Device driver init ... \\n");
    //axi123_init();\n
''' % (self.CleanNameAsADAWants(unused_maybeFVname)))

    # def ExecuteBlock(self, modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname):
    def ExecuteBlock(self, unused_modelingLanguage: str, unused_asnFile: str, sp: ApLevelContainer, unused_subProgramImplementation: str, maybeFVname: str) -> None:
        self.C_SourceFile.write("    unsigned int flag = 0;\n\n")
        self.C_SourceFile.write("    // Now that the parameters are passed inside the FPGA, run the processing logic\n")
        
        self.C_SourceFile.write('    unsigned int okstart = 1;\n')
        self.C_SourceFile.write('    //if (//axi_write(R_AXI_BASEADR + %s, &okstart, 4, R_AXI_DSTADR)) {\n' %
                                hex(int(VHDL_Circuit.lookupSP[sp._id]._offset)))
        self.C_SourceFile.write('       //LOGERROR("Failed writing Target\\n");\n')
        self.C_SourceFile.write('       //return -1;\n')
        self.C_SourceFile.write('    //}\n')
        self.C_SourceFile.write('    //LOGDEBUG(" - Write OK\\n");\n')

        self.C_SourceFile.write('    count = 0;\n')
        self.C_SourceFile.write('    while (!flag && count < RETRIES){\n')
        self.C_SourceFile.write("      // Wait for processing logic to complete\n")
        self.C_SourceFile.write('      count++;\n')
        self.C_SourceFile.write('      //if (//axi_read(R_AXI_BASEADR + %s, &flag, 4, R_AXI_DSTADR)) {\n' %
                                hex(int(VHDL_Circuit.lookupSP[sp._id]._offset)))
        self.C_SourceFile.write('        //LOGERROR("Failed reading Target\\n");\n')
        self.C_SourceFile.write('        //return -1;\n')
        self.C_SourceFile.write('      //}\n')
        self.C_SourceFile.write('      //LOGDEBUG(" - Read OK\\n");\n')
        self.C_SourceFile.write('    }\n')
        self.C_SourceFile.write('    if(!flag && count == RETRIES){\n')
        self.C_SourceFile.write('      LOGERROR("Max Target read attempts reached.\\n");\n')
        self.C_SourceFile.write('      return -1;\n')
        self.C_SourceFile.write('    }\n')
        self.C_SourceFile.write('    return 0;\n')

# pylint: disable=no-self-use
class MapASN1ToVHDLCircuit(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, direction: str, dstVHDL: str, node: AsnInt, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        bits = math.log(max(abs(x) for x in node._range) + 1, 2)
        bits += bits if node._range[0] < 0 else 0
        return [dstVHDL + ' : ' + direction + ('std_logic_vector(63 downto 0); -- ASSERT uses 64 bit INTEGERs (optimal would be %d bits)' % bits)]

    def MapReal(self, _: str, __: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, direction: str, dstVHDL: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [dstVHDL + ' : ' + direction + 'std_logic_vector(7 downto 0);']

    def MapOctetString(self, direction: str, dstVHDL: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.append(dstVHDL + ('_elem_%0*d: ' % (maxlen, i)) + direction + 'std_logic_vector(7 downto 0);')
        return lines

    def MapEnumerated(self, direction: str, dstVHDL: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [dstVHDL + ' : ' + direction + 'std_logic_vector(7 downto 0);']

    def MapSequence(self, direction: str, dstVHDL: str, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
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


# pylint: disable=no-self-use
class MapASN1ToVHDLregisters(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, _: str, dstVHDL: str, node: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        bits = math.log(max(abs(x) for x in node._range) + 1, 2)
        bits += (bits if node._range[0] < 0 else 0)
        return ['signal ' + dstVHDL + ' : ' + ('std_logic_vector(63 downto 0); -- ASSERT uses 64 bit INTEGERs (optimal would be %d bits)' % bits)]

    def MapReal(self, _: str, __: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, _: str, dstVHDL: str, __: AsnBool, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['signal ' + dstVHDL + ' : ' + 'std_logic_vector(7 downto 0);']

    def MapOctetString(self, _: str, dstVHDL: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.append('signal ' + dstVHDL + ('_elem_%0*d: ' % (maxlen, i)) + 'std_logic_vector(7 downto 0);')
        return lines

    def MapEnumerated(self, _: str, dstVHDL: str, __: AsnEnumerated, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['signal ' + dstVHDL + ' : ' + 'std_logic_vector(7 downto 0);']

    def MapSequence(self, _: str, dstVHDL: str, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
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


# pylint: disable=no-self-use
class MapASN1ToVHDLreadinputdata(RecursiveMapperGeneric[List[int], str]):  # pylint: disable=invalid-sequence-index
    def MapInteger(self, reginfo: List[int], dstVHDL: str, node: AsnInt, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        # bits = math.log(max(map(abs, node._range)+1),2)+(1 if node._range[0] < 0 else 0)
        lines = []  # type: List[str]
        lines.append('when (%s) => %s(31 downto  0) <= S_AXI_WDATA;' % (reginfo[0], dstVHDL))
        lines.append('when (%s) => %s(63 downto  32) <= S_AXI_WDATA;' % (reginfo[0] + 4, dstVHDL))
        reginfo[0] += 8
        return lines

    def MapReal(self, _: List[int], __: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, reginfo: List[int], dstVHDL: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['when X"%s" => %s(7 downto 0) <= axii.pwdata(7 downto 0);' % (hex(reginfo[0])[2:] if len(hex(reginfo[0])[2:]) > 3 else ('0' + hex(reginfo[0])[2:]), dstVHDL)]
        reginfo[0] += 4
        return lines

    def MapOctetString(self, reginfo: List[int], dstVHDL: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        if node._range[-1] % 4 != 0:  # TODO
            panicWithCallStack("OCTET STRING (in %s) is not a multiple of 4 bytes (this is not yet supported)." % node.Location())            
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            if (i) % 4 == 0:
                lines.append('when X"%s" => %s_elem_%0*d(7 downto 0) <= axii.pwdata(7 downto 0);' % (hex(reginfo[0])[2:] if len(hex(reginfo[0])[2:]) > 3 else ('0' + hex(reginfo[0])[2:]), dstVHDL, maxlen, i+0))
                lines.append('                %s_elem_%0*d(7 downto 0) <= axii.pwdata(15 downto 8);' % (dstVHDL, maxlen, i+1))
                lines.append('                %s_elem_%0*d(7 downto 0) <= axii.pwdata(23 downto 16);' % (dstVHDL, maxlen, i+2))
                lines.append('                %s_elem_%0*d(7 downto 0) <= axii.pwdata(31 downto 24);' % (dstVHDL, maxlen, i+3))
            reginfo[0] += 1
        return lines

    def MapEnumerated(self, reginfo: List[int], dstVHDL: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['when X"%s" => %s(7 downto 0) <= axii.pwdata(7 downto 0);' % (hex(reginfo[0])[2:] if len(hex(reginfo[0])[2:]) > 3 else ('0' + hex(reginfo[0])[2:]), dstVHDL)]
        reginfo[0] += 4
        return lines

    def MapSequence(self, reginfo: List[int], dstVHDL: str, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(reginfo, dstVHDL + "_" + CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, reginfo: List[int], dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, reginfo: List[int], dstVHDL: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['when X"%s" => %s_choiceIdx(7 downto 0) <= axii.pwdata(7 downto 0);' % (hex(reginfo[0])[2:], dstVHDL)]
        reginfo[0] += 1
        lines.extend(self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, reginfo: List[int], dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
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

    def MapSetOf(self, reginfo: List[int], dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(reginfo, dstVHDL, node, leafTypeDict, names)


# pylint: disable=no-self-use
class MapASN1ToVHDLwriteoutputdata(RecursiveMapperGeneric[List[int], str]):  # pylint: disable=invalid-sequence-index
    def MapInteger(self, reginfo: List[int], dstVHDL: str, node: AsnInt, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        # bits = math.log(max(map(abs, node._range)+1),2)+(1 if node._range[0] < 0 else 0)
        lines = []  # type: List[str]
        lines.append('when (%s) => v_comb_out.rdata(31 downto 0) := %s(31 downto  0);' % (reginfo[0] + 0, dstVHDL))
        lines.append('when (%s) => v_comb_out.rdata(31 downto 0) := %s(63 downto  32);' % (reginfo[0] + 4, dstVHDL))
        reginfo[0] += 8
        return lines

    def MapReal(self, _: List[int], __: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, reginfo: List[int], dstVHDL: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['when X"%s" => axio.prdata(7 downto 0) <= %s(7 downto 0);' % (hex(reginfo[0])[2:] if len(hex(reginfo[0])[2:]) > 3 else ('0' + hex(reginfo[0])[2:]), dstVHDL)]
        reginfo[0] += 4
        return lines

    def MapOctetString(self, reginfo: List[int], dstVHDL: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        if node._range[-1] % 4 != 0:  # TODO
            panicWithCallStack("OCTET STRING (in %s) is not a multiple of 4 bytes (this is not yet supported)." % node.Location())            
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            if (i) % 4 == 0:
                lines.append('when X"%s" => axio.prdata(7 downto 0) <= %s_elem_%0*d(7 downto 0);' % (hex(reginfo[0])[2:] if len(hex(reginfo[0])[2:]) > 3 else ('0' + hex(reginfo[0])[2:]), dstVHDL, maxlen, i+0))
                lines.append('                axio.prdata(15 downto 8) <= %s_elem_%0*d(7 downto 0);' % (dstVHDL, maxlen, i+1))
                lines.append('                axio.prdata(23 downto 16) <= %s_elem_%0*d(7 downto 0);' % (dstVHDL, maxlen, i+2))
                lines.append('                axio.prdata(31 downto 24) <= %s_elem_%0*d(7 downto 0);' % (dstVHDL, maxlen, i+3))
            reginfo[0] += 1
        return lines

    def MapEnumerated(self, reginfo: List[int], dstVHDL: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['when X"%s" => axio.prdata(7 downto 0) <= %s(7 downto 0);' % (hex(reginfo[0])[2:] if len(hex(reginfo[0])[2:]) > 3 else ('0' + hex(reginfo[0])[2:]), dstVHDL)]
        reginfo[0] += 4
        return lines

    def MapSequence(self, reginfo: List[int], dstVHDL: str, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(reginfo, dstVHDL + "_" + CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, reginfo: List[int], dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names)

    def MapChoice(self, reginfo: List[int], dstVHDL: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['when X"%s" => axio.prdata(7 downto 0) <= %s_choiceIdx(7 downto 0);' % (hex(reginfo[0])[2:], dstVHDL)]
        reginfo[0] += 1
        lines.extend(self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, reginfo: List[int], dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
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

    def MapSetOf(self, reginfo: List[int], dstVHDL: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(reginfo, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


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
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.append(dstCircuitPort + ('_elem_%0*d' % (maxlen, i)) + ' => ' + srcRegister + ('_elem_%0*d' % (maxlen, i)))
        return lines

    def MapEnumerated(self, srcRegister: str, dstCircuitPort: str, __: AsnEnumerated, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [dstCircuitPort + ' => ' + srcRegister]

    def MapSequence(self, srcRegister: str, dstCircuitPort: str, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
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
        return self.MapSequenceOf(srcRegister, dstCircuitPort, node, leafTypeDict, names)


class MapASN1ToOutputs(RecursiveMapperGeneric[str, int]):
    def MapInteger(self, paramName: str, _: int, dummy: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [paramName]

    def MapReal(self, _: str, __: int, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, paramName: str, _: int, dummy: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [paramName]

    def MapOctetString(self, paramName: str, _: int, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.append('%s_elem_%0*d' % (paramName, maxlen, i))
        return lines

    def MapEnumerated(self, paramName: str, dummy: int, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = [paramName]
        return lines

    def MapSequence(self, paramName: str, dummy: int, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(paramName + "_" + CleanName(x[0]), dummy, x[1], leafTypeDict, names))
        return lines

    def MapSet(self, paramName: str, dummy: int, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(paramName, dummy, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, paramName: str, dummy: int, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['%s_choiceIdx' % paramName]
        lines.extend(self.MapSequence(paramName, dummy, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, paramName: str, dummy: int, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.extend(self.Map(paramName + ('_elem_%0*d' % (maxlen, i)), dummy, node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, reginfo: str, dstVHDL: int, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(reginfo, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


g_placeholders = {
    "circuits": '',
    "ioregisters": '',
    "startStopSignals": '',
    "reset": '',
    "updateStartCompleteLedRegs": '',
    "updateStartStopPulses": '',
    "readinputdata": '',
    "setStartSignalsLow": '',
    "outputs": '',
    "completions": '',
    "starts": '',
    "writeoutputdata": '',
    "connectionsToSystemC": '',
    "updateCalculationsCompleteReset": '',
    "updateCalculationsComplete": '',
    "pi": ''
}


# def Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
def Common(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, unused_subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    if subProgram._id not in VHDL_Circuit.lookupSP:
        VHDL_Circuit.currentCircuit = VHDL_Circuit(subProgram)
    VHDL_Circuit.currentCircuit.AddParam(nodeTypename, node, param, leafTypeDict, names)


def OnStartup(modelingLanguage: str, asnFile: str, subProgram: ApLevelContainer, subProgramImplementation: str, outputDir: str, maybeFVname: str, useOSS: bool) -> None:
    global vhdlBackend
    vhdlBackend = VHDLGlueGenerator()
    vhdlBackend.OnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS)


def OnBasic(nodeTypename: str, node: AsnBasicNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnBasic(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequence(nodeTypename: str, node: AsnSequence, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnSequence(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSet(nodeTypename: str, node: AsnSet, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover
    vhdlBackend.OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename: str, node: AsnEnumerated, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequenceOf(nodeTypename: str, node: AsnSequenceOf, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSetOf(nodeTypename: str, node: AsnSetOf, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover
    vhdlBackend.OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename: str, node: AsnChoice, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnChoice(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnShutdown(modelingLanguage: str, asnFile: str, sp: ApLevelContainer, subProgramImplementation: str, maybeFVname: str) -> None:
    vhdlBackend.OnShutdown(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname)
    if subProgramImplementation.lower() == "simulink":
        EmitBambuSimulinkBridge(sp, subProgramImplementation)
    elif subProgramImplementation.lower() == "c":
        EmitBambuCBridge(sp, subProgramImplementation)


def AddToStr(s: str, d: str) -> None:
    g_placeholders[s] += d


def OnFinal() -> None:
    circuitMapper = MapASN1ToVHDLCircuit()
    ioRegisterMapper = MapASN1ToVHDLregisters()
    readinputdataMapper = MapASN1ToVHDLreadinputdata()
    writeoutputdataMapper = MapASN1ToVHDLwriteoutputdata()
    connectionsToSystemCMapper = MapASN1ToSystemCconnections()
    outputsMapper = MapASN1ToOutputs()

    outputs = []
    completions = []
    starts = []

    from . import vhdlTemplateZynQZC706
    ZynQZC706_tarball = os.getenv("ZYNQZC706")
    assert ZynQZC706_tarball is not None
    if os.system("tar -C \"" + vhdlBackend.dir + "/\" -jxf '" + ZynQZC706_tarball + "'") != 0:
        panic("Failed to un-tar ZYNQZC706 tarball...")

    for c in VHDL_Circuit.allCircuits:
        circuitLines = []

        ioregisterLines = []

        readinputdataLines = []

        connectionsToSystemCLines = []

        counter = cast(List[int], [0x0300 + c._offset + 4])  # type: List[int]  # pylint: disable=invalid-sequence-index
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
        starts.append(c._spCleanName + '_StartCalculationsPulse')

        AddToStr('circuits', '    component bambu_%s is\n' % c._spCleanName)
        AddToStr('circuits', '    port (\n')
        AddToStr('circuits', '\n'.join(['        ' + x for x in circuitLines]) + '\n')
        AddToStr('circuits', '        clock_%s : in std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '        reset_%s  : in  std_logic\n' % c._spCleanName)
        AddToStr('circuits', '    );\n')
        AddToStr('circuits', '    end component;\n\n')
        
        skeleton = []
        skeleton.append('    entity bambu_%s is\n' % c._spCleanName)
        skeleton.append('    port (\n')
        skeleton.append('\n'.join(['        ' + x for x in circuitLines]) + '\n')
        skeleton.append('        start_%s  : in  std_logic;\n' % c._spCleanName)
        skeleton.append('        finish_%s : out std_logic;\n' % c._spCleanName)
        skeleton.append('        clock_%s : in std_logic;\n' % c._spCleanName)
        skeleton.append('        reset_%s  : in  std_logic\n' % c._spCleanName)
        skeleton.append('    );\n')
        skeleton.append('    end bambu_%s;\n\n' % c._spCleanName)
        vhdlSkeleton = open(vhdlBackend.dir + "/TASTE-VHDL-DESIGN/ip/src/bambu_" + c._spCleanName + '.vhd', 'w')
        vhdlSkeleton.write(
            vhdlTemplateZynQZC706.per_circuit_vhd % {
                'pi': c._spCleanName,
                'declaration': ''.join(skeleton)
            })
        vhdlSkeleton.close()

        AddToStr('ioregisters', '\n'.join(['    ' + x for x in ioregisterLines]) + '\n\n')

        AddToStr('startStopSignals', '''\
    signal %(pi)s_StartCalculationsPulse : std_logic;
    signal %(pi)s_CalculationsComplete : std_logic;          -- the finish signal for %(pi)s
''' % {'pi': c._spCleanName})

        AddToStr('reset', "            %(pi)s_StartCalculationsInternal    <= '0';\n" % {'pi': c._spCleanName})
        AddToStr('reset', "            --%(pi)s_inp                          <= (others => '0');\n" % {'pi': c._spCleanName})
        AddToStr('reset', "            %(pi)s_StartCalculationsPulse       <= '0';\n" % {'pi': c._spCleanName})
        AddToStr('reset', "            %(pi)s_StartCalculationsInternalOld <= '0';\n" % {'pi': c._spCleanName})

        AddToStr('updateStartCompleteLedRegs', "            led_complete_reg        <= %(pi)s_CalculationsComplete;\n" % {'pi': c._spCleanName})
        AddToStr('updateStartCompleteLedRegs', "            if %(pi)s_StartCalculationsPulse = '1' then\n" % {'pi': c._spCleanName})
        AddToStr('updateStartCompleteLedRegs', "                led_start_reg       <= '1';\n")
        AddToStr('updateStartCompleteLedRegs', "            end if;\n")
        AddToStr('updateStartCompleteLedRegs', "            if %(pi)s_CalculationsComplete = '1' then\n" % {'pi': c._spCleanName})
        AddToStr('updateStartCompleteLedRegs', "                led_start_reg       <= '0';\n")
        AddToStr('updateStartCompleteLedRegs', "            end if;\n")

        AddToStr('updateStartStopPulses',
                 '            %(pi)s_StartCalculationsPulse <= %(pi)s_StartCalculationsInternal xor %(pi)s_StartCalculationsInternalOld;\n' % {'pi': c._spCleanName})
        AddToStr('updateStartStopPulses',
                 '            %(pi)s_StartCalculationsInternalOld <= %(pi)s_StartCalculationsInternal;\n' % {'pi': c._spCleanName})

        AddToStr('readinputdata', '\n'.join([' ' * 22 + x for x in readinputdataLines]) + '\n')
        
        AddToStr('setStartSignalsLow', ' ' * 12 + "if(%s_CalculationsCompletePulse = '1') then\n" % c._spCleanName)
        AddToStr('setStartSignalsLow', ' ' * 12 + "     %s_StartCalculationsInternal    <= '0';\n" % c._spCleanName)
        AddToStr('setStartSignalsLow', ' ' * 12 + "     %s_StartCalculationsPulse       <= '0';\n" % c._spCleanName)
        AddToStr('setStartSignalsLow', ' ' * 12 + "     %s_StartCalculationsInternalOld <= '0';\n" % c._spCleanName)
        AddToStr('setStartSignalsLow', ' ' * 12 + "end if;\n")
        
        AddToStr('writeoutputdata', '\n'.join(['\t' * 5 + x for x in writeoutputdataLines]) + '\n')

        AddToStr('connectionsToSystemC', '\n    Interface_%s : bambu_%s\n' % (c._spCleanName, c._spCleanName))
        AddToStr('connectionsToSystemC', '        port map (\n')
        AddToStr('connectionsToSystemC', ',\n'.join(['            ' + x for x in connectionsToSystemCLines]) + ',\n')
        AddToStr('connectionsToSystemC', '            clock_%s => S_AXI_ACLK,\n' % c._spCleanName)
        AddToStr('connectionsToSystemC', '            reset_%s => S_AXI_ARESETN\n' % c._spCleanName)
        AddToStr('connectionsToSystemC', '        );\n')

        AddToStr('updateCalculationsCompleteReset', ' ' * 12 + "%s_CalculationsComplete    <= '0';\n" % c._spCleanName)
        AddToStr('updateCalculationsComplete', ' ' * 12 + "if(%s_CalculationsCompletePulse = '1') then\n" % c._spCleanName)
        AddToStr('updateCalculationsComplete', ' ' * 12 + "    %s_CalculationsComplete <= '1';\n" % c._spCleanName)
        AddToStr('updateCalculationsComplete', ' ' * 12 + "elsif (%s_StartCalculationsPulse='1') then\n" % c._spCleanName)
        AddToStr('updateCalculationsComplete', ' ' * 12 + "    %s_CalculationsComplete <= '0';\n" % c._spCleanName)
        AddToStr('updateCalculationsComplete', ' ' * 12 + "end if;\n")

    AddToStr('outputs', ', '.join(outputs) + (', ' if len(outputs) else ''))
    AddToStr('completions', ', '.join(completions))
    AddToStr('starts', ', '.join(starts))

    AddToStr('pi', "%s" % c._spCleanName)
    vhdlFile = open(vhdlBackend.dir + '/TASTE-VHDL-DESIGN/ip/src/TASTE2.vhd', 'w')
    vhdlFile.write(vhdlTemplateZynQZC706.vhd % g_placeholders)
    vhdlFile.close()

    msg = ""
    for c in VHDL_Circuit.allCircuits:
        msg += ' ../ip/src/bambu_%s.vhd' % c._spCleanName
    makefile = open(vhdlBackend.dir + '/TASTE-VHDL-DESIGN/design/Makefile', 'w')
    makefile.write(vhdlTemplateZynQZC706.makefile % {'pi': msg, 'tab': '\t'})
    makefile.close()


def getTypeAndVarsAsBambuWantsThem(param: Param, names: AST_Lookup, leafTypeDict: AST_Leaftypes):
    prefix = "*" if isinstance(param, OutParam) else ""
    prefix += param._id
    asnTypename = param._signal._asnNodename
    node = names[asnTypename]
    return computeBambuDeclarations(node, asnTypename, prefix, names, leafTypeDict)

def computeBambuDeclarations(node: AsnNode, asnTypename: str, prefix: str, names: AST_Lookup, leafTypeDict: AST_Leaftypes) -> List[str]:
    clean = vhdlBackend.CleanNameAsToolWants
    while isinstance(node, AsnMetaMember):
        node = names[node._containedType]
    while isinstance(node, str):
        node = names[node]
    if isinstance(node, AsnInt):
        return ["asn1Scc" + clean(asnTypename) + " " + prefix]
    if isinstance(node, AsnBool):
        return ["asn1Scc" + clean(asnTypename) + " " + prefix]
    if isinstance(node, AsnEnumerated):
        return ["asn1Scc" + clean(asnTypename) + " " + prefix]
    elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
        if not node._range:
            panicWithCallStack("[computeBambuDeclarations] need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        maxlen = len(str(node._range[-1]))
        for i in range(0, node._range[-1]):
            lines.extend(
                computeBambuDeclarations(
                    node._containedType,
                    node._containedType,
                    prefix + "_elem_%0*d" % (maxlen, i),
                    names,
                    leafTypeDict))
        return lines
    elif isinstance(node, (AsnSequence, AsnSet)):
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                computeBambuDeclarations(
                    child[1],
                    (child[1]._containedType if not isinstance(child[1], AsnBool) else child[1]),
                    prefix + "_%s" % clean(child[0]),
                    names,
                    leafTypeDict))
        return lines
    elif isinstance(node, AsnOctetString):
        if not node._range:
            panicWithCallStack("[computeBambuDeclarations] need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover        
        lines = []  # type: List[str]
        maxlen = len(str(node._range[-1]))
        for i in range(0, node._range[-1]):
            lines.extend(["unsigned char" + " " + prefix + "_elem_%0*d" %  (maxlen, i)])
        return lines    
    else:
        panicWithCallStack("[computeBambuDeclarations] Unsupported type: " + str(node.__class__))

def readInputsAsBambuWantsForSimulink(sp: ApLevelContainer, param: Param, names: AST_Lookup, leafTypeDict: AST_Leaftypes):
    prefixVHDL = param._id
    prefixSimulink = param._id
    asnTypename = param._signal._asnNodename
    node = names[asnTypename]
    return computeBambuInputAssignmentsForSimulink(sp, node, asnTypename, prefixSimulink, prefixVHDL, names, leafTypeDict)

def computeBambuInputAssignmentsForSimulink(sp: ApLevelContainer, node: AsnNode, asnTypename: str, prefixSimulink: str, prefixVHDL: str, names: AST_Lookup, leafTypeDict: AST_Leaftypes) -> List[str]:
    clean = vhdlBackend.CleanNameAsToolWants
    while isinstance(node, AsnMetaMember):
        node = names[node._containedType]
    while isinstance(node, str):
        node = names[node]
    if isinstance(node, AsnInt):
        return ["%s_U.%s = %s" % (clean(sp._id), prefixSimulink, prefixVHDL)]
    if isinstance(node, AsnBool):
        return ["%s_U.%s = %s" % (clean(sp._id), prefixSimulink, prefixVHDL)]
    if isinstance(node, AsnEnumerated):
        return ["%s_U.%s = %s" % (clean(sp._id), prefixSimulink, prefixVHDL)]
    elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
        if not node._range:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        maxlen = len(str(node._range[-1]))
        for i in range(0, node._range[-1]):
            lines.extend(
                computeBambuInputAssignmentsForSimulink(
                    sp,
                    node._containedType,
                    node._containedType,
                    (prefixSimulink + ".element_%0*d" % (maxlen, i)) if node._containedType == 'TypeNested-octStrArray-elem' else (prefixSimulink + ".element_data[%d]" % i),
                    prefixVHDL + "_elem_%0*d" % (maxlen, i),
                    names,
                    leafTypeDict))
        return lines
    elif isinstance(node, (AsnSequence, AsnSet)):
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                computeBambuInputAssignmentsForSimulink(
                    sp,
                    child[1],
                    child[1],
                    prefixSimulink + ".%s" % clean(child[0]),
                    prefixVHDL + "_%s" % clean(child[0]),
                    names,
                    leafTypeDict))
        return lines
    elif isinstance(node, AsnOctetString):
        if not node._range:
            panicWithCallStack("[computeBambuInputAssignmentsForSimulink] need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        maxlen = len(str(node._range[-1]))
        for i in range(0, node._range[-1]):
            lines.extend([clean(sp._id) + "_U." + prefixSimulink + ".element_data[%d] = " % i + prefixVHDL + "_elem_%0*d" % (maxlen, i)])
        return lines
    else:
        panicWithCallStack("[computeBambuInputAssignmentsForSimulink] Unsupported type: " + str(node.__class__))
        
def readInputsAsBambuWantsForC(param: Param, names: AST_Lookup, leafTypeDict: AST_Leaftypes):
    prefixVHDL = param._id
    prefixC = "IN_" + param._id
    asnTypename = param._signal._asnNodename
    node = names[asnTypename]
    return computeBambuInputAssignmentsForC(node, asnTypename, prefixC, prefixVHDL, names, leafTypeDict)

def computeBambuInputAssignmentsForC(node: AsnNode, asnTypename: str, prefixC: str, prefixVHDL: str, names: AST_Lookup, leafTypeDict: AST_Leaftypes) -> List[str]:
    clean = vhdlBackend.CleanNameAsToolWants
    while isinstance(node, AsnMetaMember):
        node = names[node._containedType]
    while isinstance(node, str):
        node = names[node]
    if isinstance(node, AsnInt):
        return ["%s = %s" % (prefixC, prefixVHDL)]
    if isinstance(node, AsnBool):
        return ["%s = %s" % (prefixC, prefixVHDL)]
    if isinstance(node, AsnEnumerated):
        return ["%s = %s" % (prefixC, prefixVHDL)]
    elif isinstance(node, (AsnSequence, AsnSet)):
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                computeBambuInputAssignmentsForC(
                    child[1],
                    child[1],
                    prefixC + ".%s" % clean(child[0]),
                    prefixVHDL + "_%s" % clean(child[0]),
                    names,
                    leafTypeDict))
        return lines
    elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
        if not node._range:
            panicWithCallStack("[computeBambuInputAssignmentsForC] need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        maxlen = len(str(node._range[-1]))
        for i in range(0, node._range[-1]):
            lines.extend(
                computeBambuInputAssignmentsForC(
                    node._containedType,
                    node._containedType,
                    prefixC + ".arr[%d]" % i,
                    prefixVHDL + "_elem_%0*d" % (maxlen, i),
                    names,
                    leafTypeDict))
        return lines
    elif isinstance(node, AsnOctetString):
        if not node._range:
            panicWithCallStack("[computeBambuInputAssignmentsForC] need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        maxlen = len(str(node._range[-1]))
        for i in range(0, node._range[-1]):
            lines.extend([prefixC + ".arr[%d] = " % i + prefixVHDL + "_elem_%0*d" % (maxlen, i)])
        return lines    
    else:
        panicWithCallStack("[computeBambuInputAssignmentsForC] Unsupported type: " + str(node.__class__))
        

def writeOutputsAsBambuWantsForSimulink(sp: ApLevelContainer, param: Param, names: AST_Lookup, leafTypeDict: AST_Leaftypes):
    prefixVHDL = "*" + param._id
    prefixSimulink = param._id
    asnTypename = param._signal._asnNodename
    node = names[asnTypename]
    return computeBambuOutputAssignmentsForSimulink(sp, node, asnTypename, prefixSimulink, prefixVHDL, names, leafTypeDict)

def computeBambuOutputAssignmentsForSimulink(sp: ApLevelContainer, node: AsnNode, asnTypename: str, prefixSimulink: str, prefixVHDL: str, names: AST_Lookup, leafTypeDict: AST_Leaftypes) -> List[str]:
    clean = vhdlBackend.CleanNameAsToolWants
    while isinstance(node, AsnMetaMember):
        node = names[node._containedType]
    while isinstance(node, str):
        node = names[node]
    if isinstance(node, AsnInt):
        return ["%s = %s_Y.%s" % (prefixVHDL, clean(sp._id), prefixSimulink)]
    if isinstance(node, AsnBool):
        return ["%s = %s_Y.%s" % (prefixVHDL, clean(sp._id), prefixSimulink)]
    if isinstance(node, AsnEnumerated):
        return ["%s = %s_Y.%s" % (prefixVHDL, clean(sp._id), prefixSimulink)]
    elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
        if not node._range:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        maxlen = len(str(node._range[-1]))
        for i in range(0, node._range[-1]):
            lines.extend(
                computeBambuOutputAssignmentsForSimulink(
                    sp,
                    node._containedType,
                    node._containedType,
                    (prefixSimulink + ".element_%0*d" % (maxlen, i)) if node._containedType == 'TypeNested-octStrArray-elem' else (prefixSimulink + ".element_data[%d]" % i),
                    prefixVHDL + "_elem_%0*d" % (maxlen, i),
                    names,
                    leafTypeDict))
        return lines
    elif isinstance(node, (AsnSequence, AsnSet)):
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                computeBambuOutputAssignmentsForSimulink(
                    sp,
                    child[1],
                    child[1],
                    prefixSimulink + ".%s" % clean(child[0]),
                    prefixVHDL + "_%s" % clean(child[0]),
                    names,
                    leafTypeDict))
        return lines
    elif isinstance(node, AsnOctetString):
        if not node._range:
            panicWithCallStack("[computeBambuOutputAssignmentsForSimulink] need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        maxlen = len(str(node._range[-1]))
        for i in range(0, node._range[-1]):
            lines.extend([prefixVHDL + "_elem_%0*d = " % (maxlen, i) + clean(sp._id) + "_Y." + prefixSimulink + ".element_data[%d]" % i])
        return lines
    else:
        panicWithCallStack("[computeBambuOutputAssignmentsForSimulink] Unsupported type: " + str(node.__class__))

def writeOutputsAsBambuWantsForC(param: Param, names: AST_Lookup, leafTypeDict: AST_Leaftypes):
    prefixVHDL = "*" + param._id
    prefixC = "OUT_" + param._id
    asnTypename = param._signal._asnNodename
    node = names[asnTypename]
    return computeBambuOutputAssignmentsForC(node, asnTypename, prefixC, prefixVHDL, names, leafTypeDict)

def computeBambuOutputAssignmentsForC(node: AsnNode, asnTypename: str, prefixC: str, prefixVHDL: str, names: AST_Lookup, leafTypeDict: AST_Leaftypes) -> List[str]:
    clean = vhdlBackend.CleanNameAsToolWants
    while isinstance(node, AsnMetaMember):
        node = names[node._containedType]
    while isinstance(node, str):
        node = names[node]
    if isinstance(node, AsnInt):
        return ["%s = %s" % (prefixVHDL, prefixC)]
    if isinstance(node, AsnBool):
        return ["%s = %s" % (prefixVHDL, prefixC)]
    if isinstance(node, AsnEnumerated):
        return ["%s = %s" % (prefixVHDL, prefixC)]
    elif isinstance(node, (AsnSequence, AsnSet)):
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                computeBambuOutputAssignmentsForC(
                    child[1],
                    child[1],
                    prefixC + ".%s" % clean(child[0]),
                    prefixVHDL + "_%s" % clean(child[0]),
                    names,
                    leafTypeDict))
        return lines
    elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
        if not node._range:
            panicWithCallStack("[computeBambuOutputAssignmentsForC] need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        maxlen = len(str(node._range[-1]))
        for i in range(0, node._range[-1]):
            lines.extend(
                computeBambuOutputAssignmentsForC(
                    node._containedType,
                    node._containedType,
                    prefixC + ".arr[%d]" % i,
                    prefixVHDL + "_elem_%0*d" % (maxlen, i),
                    names,
                    leafTypeDict))
        return lines
    elif isinstance(node, AsnOctetString):
        if not node._range:
            panicWithCallStack("[computeBambuOutputAssignmentsForC] need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        maxlen = len(str(node._range[-1]))
        for i in range(0, node._range[-1]):
            lines.extend([prefixVHDL + "_elem_%0*d = " % (maxlen, i) + prefixC + ".arr[%d]" % i])
        return lines    
    else:
        panicWithCallStack("[computeBambuOutputAssignmentsForC] Unsupported type: " + str(node.__class__))

def EmitBambuSimulinkBridge(sp: ApLevelContainer, subProgramImplementation: str):
    # Parameter access is much faster in Python - cache these two globals
    names = asnParser.g_names
    leafTypeDict = asnParser.g_leafTypeDict

    outputCsourceFilename = vhdlBackend.CleanNameAsToolWants(sp._id) + "_bambu.c"
    
    bambuFile = open(os.path.dirname(vhdlBackend.C_SourceFile.name) + '/' +  outputCsourceFilename, 'w')
    
    bambuFile.write("#include \"%s.h\" // Space certified compiler generated\n" % vhdlBackend.asn_name)
    bambuFile.write("#include \"%s.h\"\n" % vhdlBackend.CleanNameAsToolWants(sp._id))
    bambuFile.write("#include \"%s_types.h\"\n\n" % vhdlBackend.CleanNameAsToolWants(sp._id))
    #TODO can be added later for optimization (and these 2 files can then be removed from Bambu call
    #bambuFile.write("#include \"%s.c\"\n\n" % vhdlBackend.CleanNameAsToolWants(sp._id))
    #bambuFile.write("#include \"%s_data.c\"\n\n" % vhdlBackend.CleanNameAsToolWants(sp._id))

    bambuFile.write('void bambu_%s(\n    ' %  sp._id)
    lines = []
    for param in sp._params:
        lines.extend(
            getTypeAndVarsAsBambuWantsThem(param, names, leafTypeDict))
    for idx, line in enumerate(lines):
        bambuFile.write(
            '%s%s' % (",\n    " if idx != 0 else "", line))
    bambuFile.write(') {\n')
    
    initStr = """

    static int initialized = 0;
    if (!initialized) {
        initialized = 1;
        %s_initialize();
    }
""" % (sp._id)
    bambuFile.write(initStr)

    lines = []
    for param in sp._params:
        if isinstance(param, InParam):
            lines.extend(
                readInputsAsBambuWantsForSimulink(sp, param, names, leafTypeDict))
    for idx, line in enumerate(lines):
        bambuFile.write(
            '%s%s;' % ("\n    ", line))
        
    stepStr = """

#ifndef rtmGetStopRequested
    %s_step();
#else
    if (!rtmGetStopRequested(%s_M)) {
        %s_step();
        if (rtmGetStopRequested(%s_M)) { %s_terminate(); }
    }
#endif
""" % (sp._id, sp._id, sp._id, sp._id, sp._id)
    bambuFile.write(stepStr)
    
    lines = []
    for param in sp._params:
        if isinstance(param, OutParam):
            lines.extend(
                writeOutputsAsBambuWantsForSimulink(sp, param, names, leafTypeDict))
    for idx, line in enumerate(lines):
        bambuFile.write(
            '%s%s;' % ("\n    ", line)) 
    
    bambuFile.write('\n}\n\n')


def EmitBambuCBridge(sp: ApLevelContainer, subProgramImplementation: str):
    # Parameter access is much faster in Python - cache these two globals
    names = asnParser.g_names
    leafTypeDict = asnParser.g_leafTypeDict

    outputCsourceFilename = vhdlBackend.CleanNameAsToolWants(sp._id) + "_bambu.c"
    
    bambuFile = open(os.path.dirname(vhdlBackend.C_SourceFile.name) + '/' +  outputCsourceFilename, 'w')
    
    functionBlocksName = os.path.dirname(vhdlBackend.C_SourceFile.name)[4:] # not elegant but not sure how to get the Function Block's name from here
    bambuFile.write("#include \"%s.h\" // Space certified compiler generated\n" % vhdlBackend.asn_name)
    bambuFile.write("#include \"%s.h\"\n" % functionBlocksName) 
    
    bambuFile.write('\nvoid bambu_%s(\n    ' %  sp._id)
    # List flattened PI parameters
    lines = []
    for param in sp._params:
        lines.extend(
            getTypeAndVarsAsBambuWantsThem(param, names, leafTypeDict))
    for idx, line in enumerate(lines):
        bambuFile.write(
            '%s%s' % (",\n    " if idx != 0 else "", line))
    bambuFile.write(') {\n')
    
    # Declare PI params
    lines = []
    for param in sp._params:
        if isinstance(param, InParam):
            lines.extend(["asn1Scc" + vhdlBackend.CleanNameAsToolWants(param._signal._asnNodename) + " IN_" + param._id])
        else:
            lines.extend(["asn1Scc" + vhdlBackend.CleanNameAsToolWants(param._signal._asnNodename) + " OUT_" + param._id])
    for idx, line in enumerate(lines):
        bambuFile.write(
            '%s%s;' % ("\n    ", line))

    # Write in PI input params
    bambuFile.write("\n")
    lines = []
    for param in sp._params:
        if isinstance(param, InParam):
            lines.extend(
                readInputsAsBambuWantsForC(param, names, leafTypeDict))
    for idx, line in enumerate(lines):
        bambuFile.write(
            '%s%s;' % ("\n    ", line))

    # Call PI
    bambuFile.write(
        '%s%s_PI_%s(\n        ' % ("\n\n    ", functionBlocksName, sp._id))
    lines = []
    for param in sp._params:
        if isinstance(param, InParam):
            lines.extend(["&IN_" + param._id])
        else:
            lines.extend(["&OUT_" + param._id])
    for idx, line in enumerate(lines):
        bambuFile.write(
            '%s%s' % (",\n        " if idx != 0 else "", line))
    bambuFile.write(');\n')

    # Read out PI output params
    lines = []
    for param in sp._params:
        if isinstance(param, OutParam):
            lines.extend(
                writeOutputsAsBambuWantsForC(param, names, leafTypeDict))
    for idx, line in enumerate(lines):
        bambuFile.write(
            '%s%s;' % ("\n    ", line)) 
    
    bambuFile.write('\n}\n\n')
