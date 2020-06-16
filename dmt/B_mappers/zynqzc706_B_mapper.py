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
            retValue = 8
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
            if isinstance(p, InParam):
                self._paramOffset[p._id] = VHDL_Circuit.currentOffset
                VHDL_Circuit.currentOffset += RegistersAllocated(p._signal._asnNodename)
        
        for p in sp._params:
            if not isinstance(p, InParam):
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
        lines.append("        tmp = rtems_axi_read32(AXI_BANK_IP + %s + (i*4));\n" % hex(register))
        lines.append("        //tmp >>= 32; // ?\n")
        lines.append("        val |= (tmp << (32*i));\n")
        lines.append("    }\n")
        lines.append("    %s = val;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 8
        return lines

    def MapReal(self, srcVHDL: List[int], destVar: str, node: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = srcVHDL[0] + srcVHDL[1]
        lines = []  # type: List[str]
        lines.append("{\n")
        lines.append("    double tmp;\n")
        lines.append("    unsigned int i;\n")
        lines.append("    asn1SccSint val = 0;\n")
        lines.append("    for(i=0; i<sizeof(asn1Real)/4; i++) {\n")
        lines.append("        tmp = rtems_axi_read32(AXI_BANK_IP + %s + (i*4));\n" % hex(register))
        lines.append("        val |= (tmp << (32*i));\n")
        lines.append("    }\n")
        lines.append("    %s = val;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 8
        return lines

    def MapBoolean(self, srcVHDL: List[int], destVar: str, node: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = srcVHDL[0] + srcVHDL[1]
        lines = []  # type: List[str]        
        lines.append("{\n")
        lines.append("    unsigned int tmp = 0;\n")
        lines.append("    //axi_read(R_AXI_BASEADR + %s, &tmp, 4, R_AXI_DSTADR);\n" % hex(register))
        lines.append("    tmp = rtems_axi_read32(AXI_BANK_IP + %s);\n" % hex(register))
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
        lines.append("        tmp = rtems_axi_read32(AXI_BANK_IP + %s + (i*4));\n" % hex(register))
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
        lines.append("    tmp = rtems_axi_read32(AXI_BANK_IP + %s);\n" % hex(register))
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

    def MapReal(self, srcVar: str, dstVHDL: List[int], node: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        register = dstVHDL[0] + dstVHDL[1]
        lines = []  # type: List[str]
        lines.append("{\n")
        lines.append("    double tmp;\n")
        lines.append("    unsigned int i;\n")
        lines.append("    asn1Real val = %s;\n" % srcVar)
        lines.append("    for(i=0; i<sizeof(asn1Real)/4; i++) {\n")
        lines.append("        tmp = val & 0xFFFFFFFF;\n")
        lines.append("        rtems_axi_write32(AXI_BANK_IP  + %s + (i*4), tmp);\n" % hex(register))
        lines.append("        val >>= 32;\n")
        lines.append("    }\n")
        lines.append("}\n")
        dstVHDL[0] += 8
        return lines
    
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
//#define LOGWARNINGS
//#define LOGINFOS
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
#include "axi_support.h"
#include <rtems.h>

#define XPAR_TASTE_0_BASEADDR 0x40000000

#define BUS_ALIGNEMENT                4
#define AXI_BANK_IP                 XPAR_TASTE_0_BASEADDR + START_ADD
#define START_ADD                    0x00000300

static inline uint32_t rtems_axi_read32(uintptr_t Addr)
{
    return *(volatile uint32_t *) Addr;
}

static inline void rtems_axi_write32(uintptr_t Addr, uint32_t Value)
{
    volatile uint32_t *LocalAddr = (volatile uint32_t *)Addr;
    *LocalAddr = Value;
    rtems_task_wake_after(10);
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
        self.C_SourceFile.write('    rtems_axi_write32(AXI_BANK_IP + %s, okstart);\n' %
                                hex(int(VHDL_Circuit.lookupSP[sp._id]._offset)))
        self.C_SourceFile.write('    //if (rtems_axi_write32(R_AXI_BASEADR + %s, okstart)) {\n' %
                                hex(int(VHDL_Circuit.lookupSP[sp._id]._offset)))
        self.C_SourceFile.write('    //   LOGERROR("Failed writing Target\\n");\n')
        self.C_SourceFile.write('    //   return -1;\n')
        self.C_SourceFile.write('    //}\n')
        self.C_SourceFile.write('    LOGDEBUG(" - Write OK\\n");\n')

        self.C_SourceFile.write('    count = 0;\n')
        self.C_SourceFile.write('    while (flag==0 && count < RETRIES){\n')
        self.C_SourceFile.write("      // Wait for processing logic to complete\n")
        self.C_SourceFile.write('      count++;\n')
        self.C_SourceFile.write("      // axi_read32 returns successful??\n")
        self.C_SourceFile.write('      flag = rtems_axi_read32(AXI_BANK_IP + %s);\n' %
                                hex(int(VHDL_Circuit.lookupSP[sp._id]._offset)))
        self.C_SourceFile.write('      // if (rtems_axi_read32(AXI_BANK_IP + %s)==0) {\n' %
                                hex(int(VHDL_Circuit.lookupSP[sp._id]._offset)))
        self.C_SourceFile.write('      //  LOGERROR("Failed reading Target\\n");\n')
        self.C_SourceFile.write('      //  return -1;\n')
        self.C_SourceFile.write('      //}\n')
        self.C_SourceFile.write('      LOGDEBUG(" - Read OK\\n");\n')
        self.C_SourceFile.write('    }\n')
        self.C_SourceFile.write('    if(flag==0 && count == RETRIES){\n')
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

    def MapReal(self, direction: str, dstVHDL: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [dstVHDL + ' : ' + direction + ('std_logic_vector(63 downto 0);')]
    
    def MapBoolean(self, direction: str, dstVHDL: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [dstVHDL + ' : ' + direction + 'std_logic_vector(7 downto 0);']

    def MapOctetString(self, direction: str, dstVHDL: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        if direction == "in ":
            lines.append(dstVHDL + ('_q0: ') + direction + 'std_logic_vector(31 downto 0);')
        else:
            lines.append(dstVHDL + ('_d0: ') + direction + 'std_logic_vector(31 downto 0);')
            lines.append(dstVHDL + ('_we0: ') + direction + 'std_logic;')
            
        lines.append(dstVHDL + ('_address0: out std_logic_vector(2 downto 0);'))
        lines.append(dstVHDL + ('_ce0: out std_logic;'))
        #for i in range(node._range[-1]):
        #    lines.append(dstVHDL + ('_elem_%0*d: ' % (maxlen, i)) + direction + 'std_logic_vector(7 downto 0);')
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

    def MapReal(self, _: str, dstVHDL: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['signal ' + dstVHDL + ' : ' + ('std_logic_vector(63 downto 0);')]

    def MapBoolean(self, _: str, dstVHDL: str, __: AsnBool, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['signal ' + dstVHDL + ' : ' + 'std_logic_vector(7 downto 0);']

    def MapOctetString(self, direction: str, dstVHDL: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        lines.append('signal ' + dstVHDL + ('_q0: std_logic_vector(31 downto 0);'))
        lines.append('signal ' + dstVHDL + ('_address0: std_logic_vector(2 downto 0);'))
        lines.append('signal ' + dstVHDL + ('_we0 : std_logic;'))
        lines.append('signal ' + dstVHDL + ('_ce0 : std_logic;'))

        if(direction == 'out '):
            lines.append('signal ' + dstVHDL + ('_d0: std_logic_vector(31 downto 0);'))

#        for i in range(node._range[-1]):
#            lines.append('' + dstVHDL + ('_elem_%0*d: ' % (maxlen, i)) + 'std_logic_vector(7 downto 0);')
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
class MapASN1ToVHDLinput(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, _: str, dstVHDL: str, node: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        bits = math.log(max(abs(x) for x in node._range) + 1, 2)
        bits += (bits if node._range[0] < 0 else 0)
        return ['' + dstVHDL + ' : ' + ('std_logic_vector(63 downto 0); -- ASSERT uses 64 bit INTEGERs (optimal would be %d bits)' % bits)]

    def MapReal(self, _: str, dstVHDL: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['' + dstVHDL + ' : ' + ('std_logic_vector(63 downto 0);')]

    def MapBoolean(self, _: str, dstVHDL: str, __: AsnBool, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['' + dstVHDL + ' : ' + 'std_logic_vector(7 downto 0);']

    def MapOctetString(self, _: str, dstVHDL: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
#        if not node._range:
#            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
#        if len(node._range) > 1 and node._range[0] != node._range[1]:
#            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
#        maxlen = len(str(node._range[-1]))
#        lines = []  # type: List[str]
#        for i in range(node._range[-1]):
#            lines.append('' + dstVHDL + ('_elem_%0*d: ' % (maxlen, i)) + 'std_logic_vector(7 downto 0);')
        return []

    def MapEnumerated(self, _: str, dstVHDL: str, __: AsnEnumerated, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['' + dstVHDL + ' : ' + 'std_logic_vector(7 downto 0);']

    def MapSequence(self, _: str, dstVHDL: str, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(_, dstVHDL + "_" + CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, _: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(_, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, _: str, dstVHDL: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        lines.append('' + dstVHDL + '_choiceIdx : ' + 'std_logic_vector(7 downto 0);')
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
class MapASN1ToVHDLinputassign(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, _: str, dstVHDL: str, node: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        bits = math.log(max(abs(x) for x in node._range) + 1, 2)
        bits += (bits if node._range[0] < 0 else 0)
        return ['' + dstVHDL + ' => (others => \'0\'),']

    def MapReal(self, _: str, dstVHDL: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['' + dstVHDL + ' => (others => \'0\'),']

    def MapBoolean(self, _: str, dstVHDL: str, __: AsnBool, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['' + dstVHDL + ' => (others => \'0\'),']

    def MapOctetString(self, _: str, dstVHDL: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
#        if not node._range:
#            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
#        if len(node._range) > 1 and node._range[0] != node._range[1]:
#            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
#        maxlen = len(str(node._range[-1]))
#        lines = []  # type: List[str]
#        for i in range(node._range[-1]):
#            lines.append('' + dstVHDL + ('_elem_%0*d' % (maxlen, i)) + ' => (others => \'0\'),')
        return []

    def MapEnumerated(self, _: str, dstVHDL: str, __: AsnEnumerated, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['' + dstVHDL + ' => (others => \'0\'),']

    def MapSequence(self, _: str, dstVHDL: str, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(_, dstVHDL + "_" + CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, _: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(_, dstVHDL, node, leafTypeDict, name2s)  # pragma: nocover

    def MapChoice(self, _: str, dstVHDL: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        lines.append('' + dstVHDL + '_choiceIdx' + ' => (others => \'0\'),')
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
class MapASN1ToVHDLinternalsignals(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, _: str, dstVHDL: str, node: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        bits = math.log(max(abs(x) for x in node._range) + 1, 2)
        bits += (bits if node._range[0] < 0 else 0)
        return ['' + dstVHDL + ' <= S00_AXI_r.' + dstVHDL + ';\n']

    def MapReal(self, _: str, dstVHDL: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['' + dstVHDL + ' <= S00_AXI_r.' + dstVHDL + ';\n']

    def MapBoolean(self, _: str, dstVHDL: str, __: AsnBool, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['' + dstVHDL + ' <= S00_AXI_r.' + dstVHDL + ';\n']

    def MapOctetString(self, _: str, dstVHDL: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        for i in range(node._range[-1]):
            lines.append('' + dstVHDL + ('_elem_%0*d' % (maxlen, i)) + ' <= S00_AXI_r.' + dstVHDL + ('_elem_%0*d' % (maxlen, i)) + ';\n')
        return lines

    def MapEnumerated(self, _: str, dstVHDL: str, __: AsnEnumerated, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ['' + dstVHDL + ' <= S00_AXI_r.' + dstVHDL + ';\n']

    def MapSequence(self, _: str, dstVHDL: str, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(_, dstVHDL + "_" + CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, _: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(_, dstVHDL, node, leafTypeDict, name2s)  # pragma: nocover

    def MapChoice(self, _: str, dstVHDL: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        lines.append('' + dstVHDL + '_choiceIdx' + ' <= S00_AXI_r.' + dstVHDL + '_choiceIdx' + ';\n')
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
class MapASN1ToVHDLs00_signals_writing(RecursiveMapperGeneric[List[int], str]):  # pylint: disable=invalid-sequence-index
    def MapInteger(self, reginfo: List[int], dstVHDL: str, node: AsnInt, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        # bits = math.log(max(map(abs, node._range)+1),2)+(1 if node._range[0] < 0 else 0)
        lines = []  # type: List[str]
        lines.append('when (%s) => v.%s(31 downto  0) := S00_AXI_WDATA;' % (reginfo[0], dstVHDL))
        lines.append('when (%s) => v.%s(63 downto  32) := S00_AXI_WDATA;' % (reginfo[0] + 4, dstVHDL))
        reginfo[0] += 8
        return lines

    def MapReal(self, reginfo: List[int], dstVHDL: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        lines.append('when (%s) => v.%s(31 downto  0) := S00_AXI_WDATA;' % (reginfo[0], dstVHDL))
        lines.append('when (%s) => v.%s(63 downto  32) := S00_AXI_WDATA;' % (reginfo[0] + 4, dstVHDL))
        reginfo[0] += 8
        return lines
    
    def MapBoolean(self, reginfo: List[int], dstVHDL: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['when X"%s" => %s(7 downto 0) <= axii.pwdata(7 downto 0);' % (hex(reginfo[0])[2:] if len(hex(reginfo[0])[2:]) > 3 else ('0' + hex(reginfo[0])[2:]), dstVHDL)]
        reginfo[0] += 4
        return lines

    def MapOctetString(self, reginfo: List[int], dstVHDL: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

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

class MapASN1ToVHDLs00_signals_internal(RecursiveMapperGeneric[str, str]):  # pylint: disable=invalid-sequence-index
    def MapInteger(self, direction: str, dstVHDL: str, node: AsnInt, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        # bits = math.log(max(map(abs, node._range)+1),2)+(1 if node._range[0] < 0 else 0)
        lines = []  # type: List[str]
        lines.append('%s <= S00_AXI_r.%s;' % (dstVHDL, dstVHDL))
        return lines

    def MapReal(self, direction: str, dstVHDL: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        lines.append('%s <= S00_AXI_r.%s;' % (dstVHDL, dstVHDL))
        return lines
    
    def MapBoolean(self, direction: str, dstVHDL: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['%s <= S00_AXI_r.%s;' % (dstVHDL, dstVHDL)]
        return lines

    def MapOctetString(self, direction: str, dstVHDL: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapEnumerated(self, direction: str, dstVHDL: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['%s <= S00_AXI_r.%s;' % (dstVHDL, dstVHDL)]
        return lines

    def MapSequence(self, direction: str, dstVHDL: str, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for x in node._members:
            lines.extend(self.Map(direction, dstVHDL + "_" + CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, direction: str, dstVHDL: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(direction, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, direction: str, dstVHDL: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['%s <= S00_AXI_r.%s;' % (dstVHDL, dstVHDL)]
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
        return self.MapSequenceOf(direction, dstVHDL, node, leafTypeDict, names)


# pylint: disable=no-self-use
class MapASN1ToVHDLs00_signals_rcomp(RecursiveMapperGeneric[List[int], str]):  # pylint: disable=invalid-sequence-index
    def MapInteger(self, reginfo: List[int], dstVHDL: str, node: AsnInt, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        # bits = math.log(max(map(abs, node._range)+1),2)+(1 if node._range[0] < 0 else 0)
        lines = []  # type: List[str]
        lines.append('when (%s) => v_comb_out.rdata(31 downto 0) := %s(31 downto  0);' % (reginfo[0] + 0, dstVHDL))
        lines.append('when (%s) => v_comb_out.rdata(31 downto 0) := %s(63 downto  32);' % (reginfo[0] + 4, dstVHDL))
        reginfo[0] += 8
        return lines

    def MapReal(self, reginfo: List[int], dstVHDL: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        lines.append('when (%s) => v_comb_out.rdata(31 downto 0) := %s(31 downto  0);' % (reginfo[0] + 0, dstVHDL))
        lines.append('when (%s) => v_comb_out.rdata(31 downto 0) := %s(63 downto  32);' % (reginfo[0] + 4, dstVHDL))
        reginfo[0] += 8
        return lines
    
    def MapBoolean(self, reginfo: List[int], dstVHDL: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['when (%s) => v_comb_out.rdata(7 downto 0) := %s(7 downto 0);' % (reginfo[0], dstVHDL)]
        reginfo[0] += 4
        return lines

    def MapOctetString(self, reginfo: List[int], dstVHDL: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        if node._range[-1] % 4 != 0:  # TODO
            panicWithCallStack("OCTET STRING (in %s) is not a multiple of 4 bytes (this is not yet supported)." % node.Location())            
        return []

    def MapEnumerated(self, reginfo: List[int], dstVHDL: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = ['when (%s) => v_comb_out.rdata(7 downto 0) := %s(7 downto 0);' % (reginfo[0], dstVHDL)]
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
        lines = ['when (%s) => v_comb_out.rdata(7 downto 0) := %s_choiceIdx(7 downto 0);' % (reginfo[0], dstVHDL)]
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

    def MapReal(self, srcRegister: str, dstCircuitPort: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [dstCircuitPort + ' => ' + srcRegister]

    def MapBoolean(self, srcRegister: str, dstCircuitPort: str, __: AsnBool, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [dstCircuitPort + ' => ' + srcRegister]

    def MapOctetString(self, srcRegister: str, dstCircuitPort: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        lines.append(dstCircuitPort + ('_q0') + ' => ' + srcRegister + ('_q0'))
        lines.append(dstCircuitPort + ('_ce0') + ' => ' + srcRegister + ('_ce0'))
        lines.append(dstCircuitPort + ('_address0') + ' => ' + srcRegister + ('_address0'))
        #for i in range(node._range[-1]):
        #    lines.append(dstCircuitPort + ('_elem_%0*d' % (maxlen, i)) + ' => ' + srcRegister + ('_elem_%0*d' % (maxlen, i)))
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


# pylint: disable=no-self-use
class MapASN1ToSystemCBRAMoutputconnections(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, srcRegister: str, dstCircuitPort: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapReal(self, srcRegister: str, dstCircuitPort: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapBoolean(self, srcRegister: str, dstCircuitPort: str, __: AsnBool, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapOctetString(self, srcRegister: str, dstCircuitPort: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        lines.append(dstCircuitPort + ('_we0') + ' => ' + srcRegister + ('_we0'))
        lines.append(dstCircuitPort + ('_ce0') + ' => open')

        #for i in range(node._range[-1]):
        #    lines.append(dstCircuitPort + ('_elem_%0*d' % (maxlen, i)) + ' => ' + srcRegister + ('_elem_%0*d' % (maxlen, i)))
        return lines

    def MapEnumerated(self, srcRegister: str, dstCircuitPort: str, __: AsnEnumerated, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

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


# pylint: disable=no-self-use
class MapASN1ToBRAMsconnections(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, direction : str, srcRegister: str, node: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []
    
    def MapReal(self, direction : str, srcRegister: str, node: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []
    
    def MapBoolean(self, direction : str, srcRegister: str, node: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []
    
    def MapOctetString(self, direction : str, srcRegister: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []  # type: List[str]
        lines.append(srcRegister + ('_BRAM:  block_ram_2p_inf\n'))
        lines.append('\tgeneric map(\n')
        lines.append(('\t\tabits =>  ') + srcRegister + ('_address0\'length,\n'))
        lines.append(('\t\tdbits => ') + srcRegister + ('_q0\'length\n\t)\n'))
        
        lines.append('\tport map(\n')
        lines.append(('\t\tclkr =>  S01_AXI_ACLK,\n'))
        lines.append(('\t\trena => ') + srcRegister + ('_ce0,\n'))
        if (direction == 'in '):
            lines.append(('\t\tradd => ') + srcRegister + ('_address0,\n'))
        else:
            lines.append(('\t\tradd => S01_AXI_ARADDR(') + srcRegister + ('_address0\'length-1+2 downto 2),\n'))
        lines.append(('\t\tdout => ') + srcRegister + ('_q0,\n'))
        lines.append(('\t\tclkw => S01_AXI_ACLK,\n'))
        lines.append(('\t\twena => ') + srcRegister + ('_we0,\n'))
        if (direction == 'in '):
            lines.append(('\t\twaddr => S01_AXI_AWADDR(') + srcRegister + ('_address0\'length-1+2 downto 2),\n'))
            lines.append(('\t\tdin => S01_AXI_WDATA(') + srcRegister + ('_q0\'range)\n\t);'))
        else:
            lines.append(('\t\twaddr => ') + srcRegister + ('_address0,\n'))
            lines.append(('\t\tdin => ') + srcRegister + ('_d0\n\t);'))

        #for i in range(node._range[-1]):
        #    lines.append(dstCircuitPort + ('_elem_%0*d' % (maxlen, i)) + ' => ' + srcRegister + ('_elem_%0*d' % (maxlen, i)))
        return lines

    def MapEnumerated(self, direction : str, srcRegister: str, node: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequence(self, direction : str, srcRegister: str, node: AsnSequenceOrSet, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []
    
    def MapSet(self, direction : str, srcRegister: str, node: AsnSequenceOrSet, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []
    
    def MapChoice(self, direction : str, srcRegister: str, node: AsnChoice, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []
    
    def MapSequenceOf(self, direction : str, srcRegister: str, node: AsnSequenceOrSetOf, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []
    
    def MapSetOf(self, direction : str, srcRegister: str, node: AsnSequenceOrSetOf, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []
    
class MapASN1ToOutputs(RecursiveMapperGeneric[str, int]):
    def MapInteger(self, paramName: str, _: int, dummy: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [paramName]

    def MapReal(self, paramName: str, __: int, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return [paramName]

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

class MapASN1ToVHDLs01_signals(RecursiveMapperGeneric[str, int]):
    def MapInteger(self, paramName: str, _: int, dummy: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapReal(self, paramName: str, __: int, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapBoolean(self, paramName: str, _: int, dummy: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapOctetString(self, paramName: str, _: int, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        lines.append('%s_q0' % (paramName))
        return lines

    def MapEnumerated(self, paramName: str, dummy: int, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequence(self, paramName: str, dummy: int, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSet(self, paramName: str, dummy: int, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(paramName, dummy, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, paramName: str, dummy: int, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequenceOf(self, paramName: str, dummy: int, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSetOf(self, reginfo: str, dstVHDL: int, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []  # pragma: nocover
    
class MapASN1ToVHDLs01_signals_write(RecursiveMapperGeneric[str, List[int]]):
    def MapInteger(self, paramName: str, reginfo: List[int], dummy: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapReal(self, paramName: str, reginfo: List[int], node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapBoolean(self, paramName: str, reginfo: List[int], dummy: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapOctetString(self, paramName: str, reginfo: List[int], node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        lines.append('when (%s) => v_comb_out.%s_we0 := \'1\';' % (reginfo[0], paramName))
        reginfo[0] += 8
        return lines

    def MapEnumerated(self, paramName: str, reginfo: List[int], _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequence(self, paramName: str, reginfo: List[int], node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSet(self, paramName: str, reginfo: List[int], node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(paramName, dummy, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, paramName: str, reginfo: List[int], node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequenceOf(self, paramName: str, reginfo: List[int], node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSetOf(self, paramName: str, reginfo: List[int], node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []  # pragma: nocover
    
class MapASN1ToVHDLs01_signals_declaration(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, paramName: str, direction : str, dummy: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapReal(self, paramName: str, direction : str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapBoolean(self, paramName: str, direction : str, dummy: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapOctetString(self, paramName: str, direction : str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        if(direction == 'in '):
            lines.append('%s_we0 : std_logic;' % (paramName))
        else:
            lines.append('%s_ce0 : std_logic;' % (paramName))
        return lines

    def MapEnumerated(self, paramName: str, direction : str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequence(self, paramName: str, direction : str, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSet(self, paramName: str, direction : str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(paramName, dummy, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, paramName: str, direction : str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequenceOf(self, paramName: str, direction : str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSetOf(self, paramName: str, direction : str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []  # pragma: nocover
    
class MapASN1ToVHDLs01_signals_assign(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, paramName: str, direction : str, dummy: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapReal(self, paramName: str, direction : str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapBoolean(self, paramName: str, direction : str, dummy: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapOctetString(self, paramName: str, direction : str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        if(direction == 'in '):
            lines.append('%s_we0 => \'0\'' % (paramName))
        else:
            lines.append('%s_we0 => \'0\'' % (paramName))
        return lines

    def MapEnumerated(self, paramName: str, direction : str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequence(self, paramName: str, direction : str, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSet(self, paramName: str, direction : str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(paramName, dummy, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, paramName: str, direction : str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequenceOf(self, paramName: str, direction : str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSetOf(self, paramName: str, direction : str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []  # pragma: nocover

class MapASN1ToVHDLs01_signals_read(RecursiveMapperGeneric[str, List[int]]):
    def MapInteger(self, paramName: str, reginfo: List[int], dummy: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapReal(self, paramName: str, reginfo: List[int], node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapBoolean(self, paramName: str, reginfo: List[int], dummy: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapOctetString(self, paramName: str, reginfo: List[int], node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        lines.append('when (%s) => v_comb_out.%s_ce0 := \'1\';' % (reginfo[0], paramName))
        reginfo[0] += 8
        return lines

    def MapEnumerated(self, paramName: str, reginfo: List[int], _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequence(self, paramName: str, reginfo: List[int], node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSet(self, paramName: str, reginfo: List[int], node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(paramName, dummy, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, paramName: str, reginfo: List[int], node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequenceOf(self, paramName: str, reginfo: List[int], node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSetOf(self, paramName: str, reginfo: List[int], node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []  # pragma: nocover
    
class MapASN1ToVHDLs01_signals_rcomp_res(RecursiveMapperGeneric[str, List[int]]):
    def MapInteger(self, paramName: str, reginfo: List[int], dummy: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapReal(self, paramName: str, reginfo: List[int], node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapBoolean(self, paramName: str, reginfo: List[int], dummy: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapOctetString(self, paramName: str, reginfo: List[int], node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        lines.append('when (%s) => v_comb_out.rdata(31 downto 0) := %s_q0 := \'1\';' % (reginfo[0], paramName))
        reginfo[0] += 8
        return lines

    def MapEnumerated(self, paramName: str, reginfo: List[int], _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequence(self, paramName: str, reginfo: List[int], node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSet(self, paramName: str, reginfo: List[int], node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(paramName, dummy, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, paramName: str, reginfo: List[int], node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequenceOf(self, paramName: str, reginfo: List[int], node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSetOf(self, paramName: str, reginfo: List[int], node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []  # pragma: nocover
    
class MapASN1ToVHDLs01_signals_internal(RecursiveMapperGeneric[str, str]):
    def MapInteger(self, paramName: str, direction: str, dummy: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapReal(self, paramName: str, direction: str, node: AsnReal, ___: AST_Leaftypes, dummy: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapBoolean(self, paramName: str, direction: str, dummy: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapOctetString(self, paramName: str, direction: str, node: AsnOctetString, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        if direction == "in ":
            lines.append('%s_we0 <= S01_AXI_rin_comb_out.%s_we0;' % (paramName, paramName))
        else:
            lines.append('%s_ce0 <= S01_AXI_rin_comb_out.%s_ce0;' % (paramName, paramName))
        return lines

    def MapEnumerated(self, paramName: str, direction: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequence(self, paramName: str, direction: str, node: Union[AsnSequenceOrSet, AsnChoice], leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSet(self, paramName: str, direction: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(paramName, dummy, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, paramName: str, direction: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSequenceOf(self, paramName: str, direction: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []

    def MapSetOf(self, paramName: str, direction: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return []  # pragma: nocover

g_placeholders = {
    "circuits": '',
    "ioregisters": '',
    "startStopSignals": '',
    "reset": '',
    "updateStartCompleteLedRegs": '',
    "updateStartStopPulses": '',
    "setStartSignalsLow": '',
    "connectionsToSystemC": '',
    "updateCalculationsCompleteReset": '',
    "updateCalculationsComplete": '',
    "pi": '',
    "s00_signals_declaration": '',
    "s00_signals_assign": '',
    "s01_signals_declaration": '',
    "s01_signals_assign": '',
    "m00_signals_declaration": '',
    "m00_signals_assign": '',
    "m00_signals": '',
    "m00_signals_internalassign": '',
    "m00_signals_internal": '',
    "s00s_signals_declaration": '',
    "s00s_signals_assign": '',
    "m00s_signals_declaration": '',
    "m00s_signals_assign": '',
    "done_start_assign": '',
    "starstoppulses": '',
    "internalsignals": '',
    "memfilesrelocation": '',
    "connectionsToBRAMs": '',
    "connectionsToFIFOs": '',
    "s00_signals": '',
    "s00_signals_writing": '',
    "s00_signals_rcomp": '',
    "s00_signals_internal": '',
    "s01_signals": '',
    "s01_signals_write": '',
    "s01_signals_read": '',
    "s01_signals_rcomp": '',
    "s01_signals_rcomp_res": '',
    "s01_signals_internal": '',
    "s00s_signals": '',
    "s00s_signals_running": '',
    "s00s_signals_internal": '',
    "m00s_signals": '',
    "m00s_signals_variables": '',
    "m00s_signals_running": '',
    "m00s_signals_internal": '',
    "starts": '',
    "completions": ''
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
    inputDeclarationMapper = MapASN1ToVHDLinput()
    inputAssignMapper = MapASN1ToVHDLinputassign()
    internalSignalsMapper = MapASN1ToVHDLinternalsignals()
    s00_signals_writingMapper = MapASN1ToVHDLs00_signals_writing()
    s00_signals_rcompMapper = MapASN1ToVHDLs00_signals_rcomp()
    s00_signals_internalMapper = MapASN1ToVHDLs00_signals_internal()
    
    s01_signals_declarationMapper = MapASN1ToVHDLs01_signals_declaration()
    s01_signals_assignMapper = MapASN1ToVHDLs01_signals_assign()
    s01_signalsMapper = MapASN1ToVHDLs01_signals()
    s01_signals_writeMapper = MapASN1ToVHDLs01_signals_write()
    s01_signals_readMapper = MapASN1ToVHDLs01_signals_read()
    s01_signals_rcomp_resMapper = MapASN1ToVHDLs01_signals_rcomp_res()
    s01_signals_internalMapper = MapASN1ToVHDLs01_signals_internal()


    connectionsToSystemCMapper = MapASN1ToSystemCconnections()
    connectionsToSystemCBRAMoutputMapper = MapASN1ToSystemCBRAMoutputconnections()

    connectionsToBRAMsMapper = MapASN1ToBRAMsconnections()

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
        
        inputdeclarationLines = []
        inputassignLines = []
        internalsignalsLines = []

        s00_signals_writingLines = []
        s00_signals_internalLines = []
        
        s01_signals_declarationLines = []
        s01_signals_assignLines = []
        s01_signalsLines = []
        s01_signals_writeLines = []
        s01_signals_readLines = []
        s01_signals_rcomp_resLines = []
        s01_signals_internalLines = []

        connectionsToSystemCLines = []

        connectionsToBRAMsLines = []

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
                           
            connectionsToBRAMsLines.extend(
                connectionsToBRAMsMapper.Map(
                    direction, c._spCleanName + '_' + p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
            
            s01_signals_internalLines.extend(
                s01_signals_internalMapper.Map(
                    c._spCleanName + '_' + p._id, direction, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
                
            s01_signals_declarationLines.extend(
                    s01_signals_declarationMapper.Map(
                        c._spCleanName + '_' + p._id, direction, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
                    
            s01_signals_assignLines.extend(
                    s01_signals_assignMapper.Map(
                        c._spCleanName + '_' + p._id, direction, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
                    
            if isinstance(p, InParam):
                s00_signals_writingLines.extend(
                    s00_signals_writingMapper.Map(
                        counter, c._spCleanName + '_' + p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
                
                s00_signals_internalLines.extend(
                    s00_signals_internalMapper.Map(
                        direction, c._spCleanName + '_' + p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
                    
                inputdeclarationLines.extend(
                    inputDeclarationMapper.Map(
                        direction, c._spCleanName + '_' + p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
                    
                inputassignLines.extend(
                    inputAssignMapper.Map(
                        direction, c._spCleanName + '_' + p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
                    
                internalsignalsLines.extend(
                    internalSignalsMapper.Map(
                        direction, c._spCleanName + '_' + p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
                
                s01_signals_writeLines.extend(
                    s01_signals_writeMapper.Map(
                        c._spCleanName + '_' + p._id, counter, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))

            else:
                outputs.extend([c._spCleanName + '_' + x for x in outputsMapper.Map(p._id, 1, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names)])
                
                s01_signalsLines.extend(
                    s01_signalsMapper.Map(
                        c._spCleanName + '_' + p._id, 1, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
                    
                s01_signals_readLines.extend(
                    s01_signals_readMapper.Map(
                        c._spCleanName + '_' + p._id, counter, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))

                s01_signals_rcomp_resLines.extend(
                    s01_signals_rcomp_resMapper.Map(
                        c._spCleanName + '_' + p._id, counter, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))
                
                connectionsToSystemCLines.extend(
                    connectionsToSystemCBRAMoutputMapper.Map(
                        c._spCleanName + '_' + p._id, p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))

        s00_signals_rcompLines = []

        for p in c._sp._params:
            node = VHDL_Circuit.names[p._signal._asnNodename]
            if not isinstance(p, InParam):
                s00_signals_rcompLines.extend(
                    s00_signals_rcompMapper.Map(
                        counter, c._spCleanName + '_' + p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))

        completions.append(c._spCleanName + '_done')
        starts.append(c._spCleanName + '_start')

        AddToStr('circuits', '    component %s_bambu is\n' % c._spCleanName)
        AddToStr('circuits', '    port (\n')
        AddToStr('circuits', '\n'.join(['        ' + x for x in circuitLines]) + '\n')
        AddToStr('circuits', '        start_%s  : in  std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '        finish_%s : out std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '        clock_%s : in std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '        reset_%s  : in  std_logic\n' % c._spCleanName)
        if(checkAsnOctetStringUsed(VHDL_Circuit.leafTypeDict, VHDL_Circuit.names)):
            AddToStr('circuits', ';\n')
            AddToStr('circuits', '        ddr_ext_pointer_A : in  std_logic_vector(31 downto 0);\n')
            AddToStr('circuits', '        M_Rdata_ram : in  std_logic_vector(63 downto 0);\n')
            AddToStr('circuits', '        M_DataRdy : in  std_logic;\n')
            AddToStr('circuits', '        Mout_oe_ram : out  std_logic;\n')
            AddToStr('circuits', '        Mout_we_ram : out  std_logic;\n')
            AddToStr('circuits', '        Mout_addr_ram : out std_logic_vector(31 downto 0);\n')
            AddToStr('circuits', '        Mout_Wdata_ram : out std_logic_vector(63 downto 0);\n')
            AddToStr('circuits', '        Mout_data_ram_size : out std_logic_vector(6 downto 0)\n')
        AddToStr('circuits', '    );\n')
        AddToStr('circuits', '    end component;\n\n')
        
        skeleton = []
        skeleton.append('    entity %s_bambu is\n' % c._spCleanName)
        skeleton.append('    port (\n')
        skeleton.append('\n'.join(['        ' + x for x in circuitLines]) + '\n')
        skeleton.append('        start_%s  : in  std_logic;\n' % c._spCleanName)
        skeleton.append('        finish_%s : out std_logic;\n' % c._spCleanName)
        skeleton.append('        clock_%s : in std_logic;\n' % c._spCleanName)
        skeleton.append('        reset_%s  : in  std_logic\n' % c._spCleanName)
        skeleton.append('    );\n')
        skeleton.append('    end %s_bambu;\n\n' % c._spCleanName)
        vhdlSkeleton = open(vhdlBackend.dir + "/TASTE-VHDL-DESIGN/ip/src/" + c._spCleanName + '_bambu.vhd', 'w')
        vhdlSkeleton.write(
            vhdlTemplateZynQZC706.per_circuit_vhd % {
                'pi': c._spCleanName,
                'declaration': ''.join(skeleton)
            })
        vhdlSkeleton.close()

        AddToStr('ioregisters', '\n'.join(['    ' + x for x in ioregisterLines]) + '\n\n')
        AddToStr('ioregisters', "   signal %(pi)s_start  : std_logic;\n" % {'pi': c._spCleanName})
        AddToStr('ioregisters', "   signal %(pi)s_done   : std_logic;\n" % {'pi': c._spCleanName})
        if(checkAsnOctetStringUsed(VHDL_Circuit.leafTypeDict, VHDL_Circuit.names)):
            AddToStr('ioregisters', "   signal M_Rdata_ram : std_logic_vector(63 downto 0);\n")
            AddToStr('ioregisters', "   signal M_DataRdy : std_logic;\n")
            AddToStr('ioregisters', "   signal Mout_oe_ram : std_logic;\n")
            AddToStr('ioregisters', "   signal Mout_we_ram : std_logic;\n")
            AddToStr('ioregisters', "   signal Mout_addr_ram : std_logic_vector(31 downto 0);\n")
            AddToStr('ioregisters', "   signal Mout_Wdata_ram : std_logic_vector(63 downto 0);\n")
            AddToStr('ioregisters', "   signal Mout_data_ram_size : std_logic_vector(6 downto 0);\n")
            AddToStr('ioregisters', "   signal ddr_ext_pointer_A : std_logic_vector(31 downto 0);\n")
        
        AddToStr('m00_signals_declaration', "   M_Rdata_ram : std_logic_vector(63 downto 0);\n")
        AddToStr('m00_signals_declaration', "   M_DataRdy : std_logic;\n")
        
        AddToStr('m00_signals_assign', "M_Rdata_ram			=> (others => '0'),\n")
        AddToStr('m00_signals_assign', "M_DataRdy			=> '0',\n")
        
        AddToStr('s00_signals_declaration', '\n'.join(['    ' + x for x in inputdeclarationLines]) + '\n\n')
        AddToStr('s00_signals_declaration', "%(pi)s_StartCalculationsInternal   : std_logic;\n" % {'pi': c._spCleanName})
        AddToStr('s00_signals_declaration', "%(pi)s_StartCalculationsInternalOld   : std_logic;\n" % {'pi': c._spCleanName})
        
        AddToStr('s00_signals_assign', '\n'.join(['    ' + x for x in inputassignLines]) + '\n\n')
        AddToStr('s00_signals_assign', "%(pi)s_StartCalculationsInternal   => '0',\n" % {'pi': c._spCleanName})
        AddToStr('s00_signals_assign', "%(pi)s_StartCalculationsInternalOld   => '0',\n" % {'pi': c._spCleanName})
        
        AddToStr('internalsignals', '\n'.join(['    ' + x for x in internalsignalsLines]) + '\n\n')
        AddToStr('internalsignals', "%(pi)s_start   <= S00_AXI_r.%(pi)s_StartCalculationsInternal xor S00_AXI_r.%(pi)s_StartCalculationsInternalOld;\n" % {'pi': c._spCleanName})
        
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


        AddToStr('s00_signals_writing', 'when (%s) => v.%s_StartCalculationsInternal	:= S00_AXI_r.%s_StartCalculationsInternal xor \'1\';\n' % (0x0300 + c._offset, c._spCleanName, c._spCleanName))
        AddToStr('s00_signals_writing', '\n'.join([' ' * 22 + x for x in s00_signals_writingLines]) + '\n')
        
        AddToStr('s00_signals_internal', ''.join(['\n\t' + x for x in s00_signals_internalLines]))
        
        AddToStr('setStartSignalsLow', ' ' * 12 + "if(%s_CalculationsCompletePulse = '1') then\n" % c._spCleanName)
        AddToStr('setStartSignalsLow', ' ' * 12 + "     %s_StartCalculationsInternal    <= '0';\n" % c._spCleanName)
        AddToStr('setStartSignalsLow', ' ' * 12 + "     %s_StartCalculationsPulse       <= '0';\n" % c._spCleanName)
        AddToStr('setStartSignalsLow', ' ' * 12 + "     %s_StartCalculationsInternalOld <= '0';\n" % c._spCleanName)
        AddToStr('setStartSignalsLow', ' ' * 12 + "end if;\n")
        
        AddToStr('s00_signals_rcomp', 'when (%s) => v_comb_out.rdata(31 downto 0)	:= X"000000" & "0000000" & S00_AXI_r.doneInternal;\n' % (0x0300 + c._offset))
        AddToStr('s00_signals_rcomp', '\n'.join(['\t' * 5 + x for x in s00_signals_rcompLines]) + '\n')
        
        AddToStr('s01_signals', ''.join([x + ', ' for x in s01_signalsLines]))
        AddToStr('s01_signals_write', ''.join(s01_signals_writeLines))
        AddToStr('s01_signals_read', ''.join(s01_signals_readLines))
        AddToStr('s01_signals_rcomp_res', ''.join(s01_signals_rcomp_resLines))
        AddToStr('s01_signals_internal', ''.join(s01_signals_internalLines))
        AddToStr('s01_signals_declaration', ''.join(s01_signals_declarationLines))
        AddToStr('s01_signals_assign', ''.join([x + ', ' for x in s01_signals_assignLines]))


        AddToStr('connectionsToSystemC', '\n    Interface_%s : %s_bambu\n' % (c._spCleanName, c._spCleanName))
        AddToStr('connectionsToSystemC', '        port map (\n')
        AddToStr('connectionsToSystemC', ',\n'.join(['            ' + x for x in connectionsToSystemCLines]) + ',\n')
        AddToStr('connectionsToSystemC', '            start_%s => %s_start,\n' % (c._spCleanName, c._spCleanName))
        AddToStr('connectionsToSystemC', '            finish_%s => %s_done,\n' % (c._spCleanName, c._spCleanName))
        AddToStr('connectionsToSystemC', '            clock_%s => S00_AXI_ACLK,\n' % c._spCleanName)
        AddToStr('connectionsToSystemC', '            reset_%s => S00_AXI_ARESETN\n' % c._spCleanName)
        
        if(checkAsnOctetStringUsed(VHDL_Circuit.leafTypeDict, VHDL_Circuit.names)):
            AddToStr('connectionsToSystemC', ',\n')
            AddToStr('connectionsToSystemC', '            ddr_ext_pointer_A => ddr_ext_pointer_A,\n')
            AddToStr('connectionsToSystemC', '            M_Rdata_ram => M_Rdata_ram,\n')
            AddToStr('connectionsToSystemC', '            M_DataRdy => M_DataRdy,\n')
            AddToStr('connectionsToSystemC', '            Mout_oe_ram => Mout_oe_ram,\n')
            AddToStr('connectionsToSystemC', '            Mout_we_ram => Mout_we_ram,\n')
            AddToStr('connectionsToSystemC', '            Mout_addr_ram => Mout_addr_ram,\n')
            AddToStr('connectionsToSystemC', '            Mout_Wdata_ram => Mout_Wdata_ram,\n')
            AddToStr('connectionsToSystemC', '            Mout_data_ram_size => Mout_data_ram_size\n')
        AddToStr('connectionsToSystemC', '        );\n')
        
        if(checkAsnOctetStringUsed(VHDL_Circuit.leafTypeDict, VHDL_Circuit.names)):
            AddToStr('m00_signals', 'Mout_oe_ram, Mout_we_ram, Mout_addr_ram, Mout_Wdata_ram, Mout_data_ram_size,\n')
            AddToStr('m00_signals_internalassign', 'v_comb_out.awaddr := Mout_addr_ram;\n')
            AddToStr('m00_signals_internalassign', 'v_comb_out.araddr := Mout_addr_ram;\n')
            AddToStr('m00_signals_internalassign', 'v_comb_out.wdata := Mout_Wdata_ram;\n')
            AddToStr('m00_signals_internalassign', 'comb_Mout_we_ram_Mout_oe_ram := Mout_we_ram&Mout_oe_ram;\n')
            AddToStr('m00_signals_internal', 'M_Rdata_ram <= M00_AXI_rin_comb_out.M_Rdata_ram;\n')
            AddToStr('m00_signals_internal', 'M_DataRdy <= M00_AXI_rin_comb_out.M_DataRdy;\n')

        
        AddToStr('connectionsToBRAMs', ''.join(connectionsToBRAMsLines))

        AddToStr('updateCalculationsCompleteReset', ' ' * 12 + "%s_CalculationsComplete    <= '0';\n" % c._spCleanName)
        AddToStr('updateCalculationsComplete', ' ' * 12 + "if(%s_CalculationsCompletePulse = '1') then\n" % c._spCleanName)
        AddToStr('updateCalculationsComplete', ' ' * 12 + "    %s_CalculationsComplete <= '1';\n" % c._spCleanName)
        AddToStr('updateCalculationsComplete', ' ' * 12 + "elsif (%s_StartCalculationsPulse='1') then\n" % c._spCleanName)
        AddToStr('updateCalculationsComplete', ' ' * 12 + "    %s_CalculationsComplete <= '0';\n" % c._spCleanName)
        AddToStr('updateCalculationsComplete', ' ' * 12 + "end if;\n")
        
        AddToStr('done_start_assign', 'if %s_start = \'1\' then\nv.done	:= \'0\';\nend if;\n' % c._spCleanName)
        AddToStr('done_start_assign', 'if %s_done = \'1\' then\nv.done	:= \'1\';\nend if;\n' % c._spCleanName)

        AddToStr('starstoppulses', 'v.%s_StartCalculationsInternalOld 	:= S00_AXI_r.%s_StartCalculationsInternal;\n' % (c._spCleanName, c._spCleanName))

        AddToStr('s00_signals', ''.join([x + ', ' for x in outputs]))
        AddToStr('s00_signals', ''.join([x + ', ' for x in completions]))
        AddToStr('s00_signals', ''.join([x + ', ' for x in starts]))
        AddToStr('completions', ''.join(completions))
        AddToStr('starts', ''.join(starts))

    AddToStr('pi', "%s" % c._spCleanName)
    vhdlFile = open(vhdlBackend.dir + '/TASTE-VHDL-DESIGN/ip/src/TASTE_AXI.vhd', 'w')
    vhdlFile.write(vhdlTemplateZynQZC706.vhd % g_placeholders)
    vhdlFile.close()

    msg = ""
    for c in VHDL_Circuit.allCircuits:
        msg += '%s_bambu.vhd' % c._spCleanName
    makefile = open(vhdlBackend.dir + '/TASTE-VHDL-DESIGN/project/Makefile', 'w')
    makefile.write(vhdlTemplateZynQZC706.makefile % {'pi': msg, 'tab': '\t'})
    makefile.close()

    load_exec = open(vhdlBackend.dir + '/TASTE-VHDL-DESIGN/project/load_exec.sh', 'w')
    load_exec.write(vhdlTemplateZynQZC706.load_exec)
    load_exec.close()

    programming_tcl = open(vhdlBackend.dir + '/TASTE-VHDL-DESIGN/project/programming.tcl', 'w')
    programming_tcl.write(vhdlTemplateZynQZC706.programming_tcl)
    programming_tcl.close()

    axi_support = open(vhdlBackend.dir + '/axi_support.h', 'w')
    axi_support.write(vhdlTemplateZynQZC706.axi_support)
    axi_support.close()
    
    catalog = open(vhdlBackend.dir + '/TASTE-VHDL-DESIGN/ip/component.xml', 'w')
    catalog.write(vhdlTemplateZynQZC706.component_xml % {'pi': msg} )
    catalog.close()


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
    if isinstance(node, AsnReal):
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
      #  lines.extend(["asn1Scc" + clean(asnTypename) + " " + prefix + "[" + str(node._range[-1]) + "]"])
        lines.extend(["asn1Scc" + clean(asnTypename) + " " + prefix ])
        #for i in range(0, node._range[-1]):
        #    lines.extend(["unsigned char" + " " + prefix + "_elem_%0*d" %  (maxlen, i)])
        return lines    
    else:
        panicWithCallStack("[computeBambuDeclarations] Unsupported type: " + str(node.__class__))

def readInputsAsBambuWantsForSimulink(sp: ApLevelContainer, param: Param, names: AST_Lookup, leafTypeDict: AST_Leaftypes):
    prefixVHDL = param._id
    prefixSimulink = param._id
    asnTypename = param._signal._asnNodename
    node = names[asnTypename]
    return computeBambuInputAssignmentsForSimulink(sp, node, asnTypename, prefixSimulink, prefixVHDL, names, leafTypeDict)

def checkAsnOctetStringUsed(names: AST_Lookup, leafTypeDict: AST_Leaftypes):
    for c in VHDL_Circuit.allCircuits:
        for p in c._sp._params:
            if (isinstance(p, AsnOctetString)):
                return True
    return False

def computeBambuInputAssignmentsForSimulink(sp: ApLevelContainer, node: AsnNode, asnTypename: str, prefixSimulink: str, prefixVHDL: str, names: AST_Lookup, leafTypeDict: AST_Leaftypes) -> List[str]:
    clean = vhdlBackend.CleanNameAsToolWants
    while isinstance(node, AsnMetaMember):
        node = names[node._containedType]
    while isinstance(node, str):
        node = names[node]
    if isinstance(node, AsnInt):
        return ["%s_U.%s = %s" % (clean(sp._id), prefixSimulink, prefixVHDL)]
    if isinstance(node, AsnReal):
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
        lines.extend(["for (int i = 0; i< %d ; i++)" % (node._range[-1]) + "\n\t\t" + clean(sp._id) + "_U." + prefixSimulink + ".element_data[i] = " + prefixVHDL + ".arr[i]"])
       # lines.extend(["\t" + clean(sp._id) + "_U." + prefixSimulink + "[i] = " + prefixVHDL + "[i]"])
        #for i in range(0, node._range[-1]):
        #    lines.extend([clean(sp._id) + "_U." + prefixSimulink + ".element_data[%d] = " % i + prefixVHDL + "_elem_%0*d" % (maxlen, i)])
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
    if isinstance(node, AsnReal):
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
        lines.extend([prefixC + " = " + prefixVHDL])
        #for i in range(0, node._range[-1]):
        #    lines.extend([prefixC + ".arr[%d] = " % i + prefixVHDL + "_elem_%0*d" % (maxlen, i)])
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
    if isinstance(node, AsnReal):
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
        lines.extend([prefixVHDL + " = " + clean(sp._id) + "_Y." + prefixSimulink])
        #for i in range(0, node._range[-1]):
        #    lines.extend([prefixVHDL + "_elem_%0*d = " % (maxlen, i) + clean(sp._id) + "_Y." + prefixSimulink + ".element_data[%d]" % i])
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
    if isinstance(node, AsnReal):
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
        lines.extend([prefixVHDL + " = " + prefixC])
        #for i in range(0, node._range[-1]):
        #    lines.extend([prefixVHDL + "_elem_%0*d = " % (maxlen, i) + prefixC + ".arr[%d]" % i])
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
    bambuFile.write("#include \"%s.c\"\n" % vhdlBackend.CleanNameAsToolWants(sp._id))
    #TODO can be added later for optimization (and these 2 files can then be removed from Bambu call
    #bambuFile.write("#include \"%s.c\"\n\n" % vhdlBackend.CleanNameAsToolWants(sp._id))
    #bambuFile.write("#include \"%s_data.c\"\n\n" % vhdlBackend.CleanNameAsToolWants(sp._id))

    bambuFile.write('void %s_bambu(\n    ' %  sp._id)
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
    
    functionBlocksName = os.path.dirname(vhdlBackend.C_SourceFile.name).lstrip(os.sep)
    functionBlocksName = functionBlocksName[:functionBlocksName.index(os.sep)] if os.sep in functionBlocksName else functionBlocksName # a bit more elegant way of retrieving function block's name

    bambuFile.write("#include \"%s.h\" // Space certified compiler generated\n" % vhdlBackend.asn_name)
    bambuFile.write("#include \"%s.h\"\n" % functionBlocksName) 
    bambuFile.write("#include \"%s.c\"\n" % functionBlocksName) 


    bambuFile.write('\nvoid %s_bambu(\n    ' %  sp._id)
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
