# (C) Semantix Information Technologies.
#
# Semantix Information Technologies is licensing the code of the
# Data Modelling Tools (DMT) in the following dual-license mode:
#
# Commercial Developer License:
#	The DMT Commercial Developer License is the appropriate version 
# to use for the development of proprietary and/or commercial software. 
# This version is for developers/companies who do not want to share 
# the source code they develop with others or otherwise comply with the 
# terms of the GNU General Public License version 2.1.
#
# GNU GPL v. 2.1:
#	This version of DMT is the one to use for the development of 
# non-commercial applications, when you are willing to comply 
# with the terms of the GNU General Public License version 2.1.
#
# The features of the two licenses are summarized below:
#
#			Commercial 		
#			Developer		GPL
#			License
#
# License cost		License fee charged	No license fee
#
# Must provide source 
# code changes to DMT	No, modifications can	Yes, all source code 
#			be closed		must be provided back
#
# Can create		Yes, that is,		No, applications are subject 
# proprietary		no source code needs	to the GPL and all source code 
# applications      	to be disclosed		must be made available 
#
# Support		Yes, 12 months of	No, but available separately 
#			premium technical	for purchase
#			support	
#
# Charge for Runtimes	None			None
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

import re
import os
import math

from typing import cast, Union, List, Tuple, IO, Any  # NOQA pylint: disable=unused-import

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
from ..commonPy.aadlAST import Param, ApLevelContainer  # NOQA pylint: disable=unused-import
from ..commonPy import asnParser

from ..commonPy.recursiveMapper import RecursiveMapperGeneric, RecursiveMapper
from .synchronousTool import SynchronousToolGlueGeneratorGeneric, SynchronousToolGlueGenerator

isAsynchronous = False
vhdlBackend = None

def Version():
    print("Code generator: " + "$Id: vhdl_B_mapper.py 1754 2009-12-26 13:02:45Z ttsiodras $") # NOSTMTCOVERAGE

def CleanName(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)

def RegistersAllocated(node):
    names = asnParser.g_names
    while isinstance(node, str):
        node = names[node]
    if isinstance(node, AsnBasicNode):
        retValue = 0
        realLeafType = asnParser.g_leafTypeDict[node._leafType]
        if realLeafType == "INTEGER":
            retValue = 8
        elif realLeafType == "REAL":
            panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location()) # NOSTMTCOVERAGE
        elif realLeafType == "BOOLEAN":
            retValue = 1
        elif realLeafType == "OCTET STRING":
            if node._range == []:
                panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location()) # NOSTMTCOVERAGE
            if len(node._range)>1 and node._range[0]!=node._range[1]:
                panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location()) # NOSTMTCOVERAGE
            retValue = node._range[-1]
        else: # NOSTMTCOVERAGE
            panicWithCallStack("Basic type %s can't be mapped..." % realLeafType) # NOSTMTCOVERAGE
        return retValue
    elif isinstance(node, AsnSequence): 
        return sum(map(RegistersAllocated, [x[1] for x in node._members]))
    elif isinstance(node, AsnSet):
        return sum(map(RegistersAllocated, [x[1] for x in node._members]))
    elif isinstance(node, AsnChoice):
        return 1 + sum(map(RegistersAllocated, [x[1] for x in node._members]))
    elif isinstance(node, AsnSequenceOf):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location()) # NOSTMTCOVERAGE
        return node._range[-1] * RegistersAllocated(node._containedType)
    elif isinstance(node, AsnSetOf):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location()) # NOSTMTCOVERAGE
        return node._range[-1] * RegistersAllocated(node._containedType)
    elif isinstance(node, AsnEnumerated):
        return 1
    elif isinstance(node, AsnMetaMember):
        return RegistersAllocated(names[node._containedType])
    else: # NOSTMTCOVERAGE
        panicWithCallStack("unsupported %s (%s)" % (str(node.__class__), node.Location())) # NOSTMTCOVERAGE

class VHDL_Circuit:
    allCircuits = []
    lookupSP = {}
    completedSP = {}
    currentCircuit = names = leafTypeDict = None
    currentOffset = 0x0
    def __init__(self, sp):
        VHDL_Circuit.allCircuits.append(self)
        VHDL_Circuit.lookupSP[sp._id] = self
        VHDL_Circuit.currentCircuit = self
        self._sp = sp
        self._params = []
        self._spCleanName = CleanName(sp._id)
        self._offset = VHDL_Circuit.currentOffset
        VHDL_Circuit.currentOffset += 1 # reserve one register for "start" signal
        self._paramOffset = {}
        for p in sp._params:
            self._paramOffset[p._id] = VHDL_Circuit.currentOffset
            VHDL_Circuit.currentOffset += RegistersAllocated(p._signal._asnNodename)
    def __str__(self):
        msg = "PI:%s\n" % self._sp._id # NOSTMTCOVERAGE
        msg += ''.join([p[0]._id+':'+p[0]._signal._asnNodename+("(in)" if isinstance(p[0], InParam) else "(out)")+'\n' for p in self._params]) # NOSTMTCOVERAGE
        return msg # NOSTMTCOVERAGE
    def AddParam(self, nodeTypename, node, param, leafTypeDict, names):
        VHDL_Circuit.names = names
        VHDL_Circuit.leafTypeDict = leafTypeDict
        self._params.append([param, nodeTypename, node])

#def IsElementMappedToPrimitive(node, names):
#    contained = node._containedType
#    while isinstance(contained, str):
#        contained = names[contained]
#    return isinstance(contained, AsnInt) or isinstance(contained, AsnReal) or isinstance(contained, AsnBool) or isinstance(contained, AsnEnumerated)

class FromVHDLToASN1SCC(RecursiveMapper):
    def MapInteger(self, srcVHDL, destVar, _, __, ___):
        register = srcVHDL[0] + srcVHDL[1]
        lines=[]
        lines.append("{\n")
        lines.append("    unsigned char tmp, i;\n")
        lines.append("    asn1SccSint val = 0;\n")
        lines.append("    for(i=0; i<sizeof(asn1SccSint); i++) {\n")
        lines.append("        ZestSC1ReadRegister(g_Handle, BASE_ADDR + %s + i, &tmp);\n" % hex(register))
        lines.append("        val <<= 8; val |= tmp;\n")
        lines.append("    }\n")
        lines.append("#if WORD_SIZE == 8\n")
        lines.append("    val = __builtin_bswap64(val);\n")
        lines.append("#else\n")
        lines.append("    val = __builtin_bswap32(val);\n")
        lines.append("#endif\n")
        lines.append("    %s = val;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 8
        return lines
    def MapReal(self, dummy, _, node, __, ___):
        panicWithCallStack("REALs (%s) cannot be used for synthesizeable VHDL" % node.Location()) # NOSTMTCOVERAGE
        # return ["%s = (double) %s;\n" % (destVar, srcVHDL)]
    def MapBoolean(self, srcVHDL, destVar, _, __, ___):
        register = srcVHDL[0] + srcVHDL[1]
        lines=[]
        lines.append("{\n")
        lines.append("    unsigned char tmp;\n")
        lines.append("    ZestSC1ReadRegister(g_Handle, BASE_ADDR + %s, &tmp);\n" % hex(register))
        lines.append("    %s = (asn1SccUint) tmp;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 1
        return lines
    def MapOctetString(self, srcVHDL, destVar, node, _, __):
        register = srcVHDL[0] + srcVHDL[1]
        lines = []
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location()) # NOSTMTCOVERAGE
        for i in range(0, node._range[-1]):
            lines.append("{\n")
            lines.append("    unsigned char tmp;\n")
            lines.append("    ZestSC1ReadRegister(g_Handle, BASE_ADDR + %s, &tmp);\n" % hex(register+i))
            lines.append("    %s.arr[%d] = tmp;\n" % (destVar, i))
            lines.append("}\n")
        lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        srcVHDL[0] += node._range[-1]
        return lines
    def MapEnumerated(self, srcVHDL, destVar, _, __, ___):
        register = srcVHDL[0] + srcVHDL[1]
        lines=[]
        lines.append("{\n")
        lines.append("    unsigned char tmp;\n")
        lines.append("    ZestSC1ReadRegister(g_Handle, BASE_ADDR + %s, &tmp);\n" % hex(register))
        lines.append("    %s = tmp;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 1
        return lines
    def MapSequence(self, srcVHDL, destVar, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVHDL,
                    destVar + "." + self.CleanName(child[0]), 
                    child[1],
                    leafTypeDict,
                    names))
        return lines
    def MapSet(self, srcVHDL, destVar, node, leafTypeDict, names):
        return self.MapSequence(srcVHDL, destVar, node, leafTypeDict, names)
    def MapChoice(self, srcVHDL, destVar, node, leafTypeDict, names):
        register = srcVHDL[0] + srcVHDL[1]
        lines = []
        childNo = 0
        lines.append("{\n")
        lines.append("    unsigned char choiceIdx = 0;\n")
        lines.append("    ZestSC1ReadRegister(g_Handle, BASE_ADDR + %s, &choiceIdx);\n" % hex(register))
        if len(node._members)>255:
            panic("Up to 255 different CHOICEs can be supported (%s)" % node.Location()) # NOSTMTCOVERAGE
        for child in node._members:
            childNo += 1
            lines.append("    %sif (choiceIdx == %d) {\n" % (self.maybeElse(childNo), childNo))
            lines.extend(['        '+x for x in self.Map(
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
    def MapSequenceOf(self, srcVHDL, destVar, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location()) # NOSTMTCOVERAGE
        #isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                    #isMappedToPrimitive and ("%s.element_data[%d]" % (srcVHDL, i)) or ("%s.element_%02d" % (srcVHDL, i)),
                    srcVHDL,
                    destVar + ".arr[%d]" % i,
                    node._containedType,
                    leafTypeDict,
                    names))
        lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        return lines
    def MapSetOf(self, srcVHDL, destVar, node, leafTypeDict, names):
        return self.MapSequenceOf(srcVHDL, destVar, node, leafTypeDict, names)

class FromASN1SCCtoVHDL(RecursiveMapper):
    def MapInteger(self, srcVar, dstVHDL, _, __, ___):
        register = dstVHDL[0] + dstVHDL[1]
        lines=[]
        lines.append("{\n")
        lines.append("    unsigned char tmp, i;\n")
        lines.append("    asn1SccSint val = %s;\n" % srcVar)
        lines.append("    for(i=0; i<sizeof(asn1SccSint); i++) {\n")
        lines.append("        tmp = val & 0xFF;\n")
        lines.append("        ZestSC1WriteRegister(g_Handle, BASE_ADDR + %s + i, tmp);\n" % hex(register))
        lines.append("        val >>= 8;\n")
        lines.append("    }\n")
        lines.append("}\n")
        dstVHDL[0] += 8
        return lines
    def MapReal(self, dummy, _, node, __, ___):
        panicWithCallStack("REALs (%s) cannot be used for synthesizeable VHDL" % node.Location()) # NOSTMTCOVERAGE
        #return ["%s = %s;\n" % (dstVHDL, srcVar)]
    def MapBoolean(self, srcVar, dstVHDL, _, __, ___):
        register = dstVHDL[0] + dstVHDL[1]
        lines=[]
        lines.append("{\n")
        lines.append("    unsigned char tmp = %s;\n" % srcVar)
        lines.append("    ZestSC1WriteRegister(g_Handle, BASE_ADDR + %s, tmp);\n" % hex(register))
        lines.append("}\n")
        dstVHDL[0] += 1
        return lines
    def MapOctetString(self, srcVar, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location()) # NOSTMTCOVERAGE
        register = dstVHDL[0] + dstVHDL[1]
        lines = []
        for i in range(0, node._range[-1]):
            lines.append("{\n")
            lines.append("    unsigned char tmp;\n")
            lines.append("    if (%s.nCount >= %d)\n" % (srcVar, i+1))
            lines.append("        tmp = %s.arr[%d];\n" % (srcVar, i))
            lines.append("    else\n")
            lines.append("        tmp = 0;\n")
            lines.append("    ZestSC1WriteRegister(g_Handle, BASE_ADDR + %s + %d, tmp);\n" % (hex(register), i))
            lines.append("}\n")
        dstVHDL[0] += node._range[-1]
        return lines
    def MapEnumerated(self, srcVar, dstVHDL, node, __, ___):
        if None in [x[1] for x in node._members]:
            panicWithCallStack("an ENUMERATED must have integer values! (%s)" % node.Location()) # NOSTMTCOVERAGE
        register = dstVHDL[0] + dstVHDL[1]
        lines=[]
        lines.append("{\n")
        lines.append("    unsigned char tmp = %s;\n" % srcVar)
        lines.append("    ZestSC1WriteRegister(g_Handle, BASE_ADDR + %s, tmp);\n" % hex(register))
        lines.append("}\n")
        dstVHDL[0] += 1
        return lines
    def MapSequence(self, srcVar, dstVHDL, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]), 
                    dstVHDL,
                    child[1],
                    leafTypeDict,
                    names))
        return lines
    def MapSet(self, srcVar, dstVHDL, node, leafTypeDict, names):
        return self.MapSequence(srcVar, dstVHDL, node, leafTypeDict, names)
    def MapChoice(self, srcVar, dstVHDL, node, leafTypeDict, names):
        register = dstVHDL[0] + dstVHDL[1]
        lines = []
        childNo = 0
        if len(node._members)>255:
            panic("Up to 255 different CHOICEs can be supported (%s)" % node.Location()) # NOSTMTCOVERAGE
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.kind == %s) {\n" % (self.maybeElse(childNo), srcVar, self.CleanName(child[2])))
            lines.append("    unsigned char tmp = %d;\n" % childNo)
            lines.append("    ZestSC1WriteRegister(g_Handle, BASE_ADDR + %s, tmp);\n" % hex(register))
            lines.extend(['    '+x for x in self.Map(
                    srcVar + ".u." + self.CleanName(child[0]), 
                    dstVHDL,
                    child[1],
                    leafTypeDict,
                    names)])
            lines.append("}\n")
        dstVHDL[0] += 1
        return lines
    def MapSequenceOf(self, srcVar, dstVHDL, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location()) # NOSTMTCOVERAGE
        # isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                srcVar + ".arr[%d]" % i,
                dstVHDL,
                #isMappedToPrimitive and ("%s.element_data[%d]" % (dstVHDL, i)) or ("%s.element_%02d" % (dstVHDL, i)),
                node._containedType,
                leafTypeDict,
                names))
        return lines
    def MapSetOf(self, srcVar, dstVHDL, node, leafTypeDict, names):
        return self.MapSequenceOf(srcVar, dstVHDL, node, leafTypeDict, names)

class VHDLGlueGenerator(SynchronousToolGlueGenerator):
    def Version(self):
        print("Code generator: " + "$Id: vhdl_B_mapper.py 1754 2009-12-26 13:02:45Z ttsiodras $") # NOSTMTCOVERAGE
    def FromToolToASN1SCC(self):
        return FromVHDLToASN1SCC()
    def FromASN1SCCtoTool(self):
        return FromASN1SCCtoVHDL()
    def FromOSStoTool(self):
        pass # NOSTMTCOVERAGE
    def FromToolToOSS(self):
        pass # NOSTMTCOVERAGE
    #def HeadersOnStartup(self, modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname):
    def HeadersOnStartup(self, _, __, subProgram, unused, ___, ____):
        self.C_SourceFile.write("#include \"%s.h\" // Space certified compiler generated\n" % self.asn_name)
        self.C_SourceFile.write('''
#include "ZestSC1.h"

#ifndef STATIC
#define STATIC
#endif

#define BASE_ADDR  0x2000

static ZESTSC1_HANDLE g_Handle = NULL;

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

static void ErrorHandler(
    const char *Function,
    ZESTSC1_HANDLE Handle,
    ZESTSC1_STATUS Status,
    const char *Msg)
{
    printf("**** TASTE - Function %s returned an error\\n        \\"%%s\\"\\n\\n", Function, Msg);
    exit(1);
}

''')
        self.g_FVname = subProgram._id
    #def SourceVar(self, nodeTypename, encoding, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    def SourceVar(self, _, __, ___, subProgram, dummy, param, ____, _____):
        if isinstance(param._sourceElement, AadlPort):
            srcVHDL = [0, VHDL_Circuit.lookupSP[subProgram._id]._paramOffset[param._id]] # NOSTMTCOVERAGE
        elif isinstance(param._sourceElement, AadlParameter):
            srcVHDL = [0, VHDL_Circuit.lookupSP[subProgram._id]._paramOffset[param._id]]
        else: # NOSTMTCOVERAGE
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement)) # NOSTMTCOVERAGE
        return srcVHDL
    #def TargetVar(self, nodeTypename, encoding, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    def TargetVar(self, _, __, ___, subProgram, dummy, param, ____, _____):
        if isinstance(param._sourceElement, AadlPort):
            dstVHDL = [0, VHDL_Circuit.lookupSP[subProgram._id]._paramOffset[param._id]] # NOSTMTCOVERAGE
        elif isinstance(param._sourceElement, AadlParameter):
            dstVHDL = [0, VHDL_Circuit.lookupSP[subProgram._id]._paramOffset[param._id]]
        else: # NOSTMTCOVERAGE
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement)) # NOSTMTCOVERAGE
        return dstVHDL
    #def InitializeBlock(self, modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname):
    def InitializeBlock(self, _, __, ___, ____, _____):
        self.C_SourceFile.write('''    ZESTSC1_HANDLE Handle = (ZESTSC1_HANDLE) NULL;

    ZestSC1RegisterErrorHandler(ErrorHandler);

    if (g_Handle == (ZESTSC1_HANDLE) NULL) {
        static unsigned int Count;
        static unsigned int NumCards;
        static unsigned long CardIDs[256];
        static unsigned long SerialNumbers[256];
        static ZESTSC1_FPGA_TYPE FPGATypes[256];
        ZestSC1CountCards((unsigned long*)&NumCards, CardIDs, SerialNumbers, FPGATypes);
        if (NumCards==0) {
            printf("No cards in the system\\n");
            exit(1);
        }
        ZestSC1OpenCard(CardIDs[0], &Handle);
        g_Handle = Handle;
        if (FPGATypes[0]==ZESTSC1_XC3S1000) {
            ZestSC1ConfigureFromFile(g_Handle, "taste.bit");
        } else {
            puts("Only for XC3S1000");
            exit(1);
        }
        ZestSC1SetSignalDirection(g_Handle, 0xf);
''')
        self.C_SourceFile.write("    }\n")
    #def ExecuteBlock(self, modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname):
    def ExecuteBlock(self, _, __, sp, ____, _____):
        self.C_SourceFile.write("    unsigned char flag = 0;\n\n")
        self.C_SourceFile.write("    // Now that the parameters are passed inside the FPGA, run the processing logic\n")
        self.C_SourceFile.write("    ZestSC1WriteRegister(g_Handle, BASE_ADDR + %s, (unsigned char)1);\n" % 
            hex(int(VHDL_Circuit.lookupSP[sp._id]._offset)))
        self.C_SourceFile.write("    while (!flag) {\n")
        self.C_SourceFile.write("        // Wait for processing logic to complete\n")
        self.C_SourceFile.write("        ZestSC1ReadRegister(g_Handle, BASE_ADDR + %s, &flag);\n" % 
            hex(int(VHDL_Circuit.lookupSP[sp._id]._offset)))
        self.C_SourceFile.write("    }\n\n")

class MapASN1ToVHDLCircuit(RecursiveMapper):
    def MapInteger(self, direction, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location()) # NOSTMTCOVERAGE
        bits = math.log(max(list(map(abs, node._range)))+1, 2)
        bits += bits if node._range[0]<0 else 0
        #return [dstVHDL + ' : ' + direction + ('std_logic_vector(63 downto 0); -- normally, %d instead of 63' % bits)]
        return [dstVHDL + ' : ' + direction + ('std_logic_vector(63 downto 0); -- ASSERT uses 64 bit INTEGERs (optimal would be %d bits)' % bits)]
    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location()) # NOSTMTCOVERAGE
    def MapBoolean(self, direction, dstVHDL, _, __, ___):
        return [dstVHDL + ' : ' + direction + 'std_logic;']
    def MapOctetString(self, direction, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location()) # NOSTMTCOVERAGE
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.append(dstVHDL + ('_elem_%0*d: ' % (maxlen, i)) + direction + 'std_logic_vector(7 downto 0);')
        return lines
    def MapEnumerated(self, direction, dstVHDL, _, __, ___):
        return [dstVHDL + ' : ' + direction + 'std_logic(7 downto 0);']
    def MapSequence(self, direction, dstVHDL, node, leafTypeDict, names):
        lines = []
        for x in node._members:
            lines.extend( self.Map(direction, dstVHDL+"_"+CleanName(x[0]), x[1], leafTypeDict, names) )
        return lines
    def MapSet(self, direction, dstVHDL, node, leafTypeDict, names):
        return self.MapSequence(direction, dstVHDL, node, leafTypeDict, names)
    def MapChoice(self, direction, dstVHDL, node, leafTypeDict, names):
        lines = []
        lines.append(dstVHDL + '_choiceIdx : ' + direction + 'std_logic_vector(7 downto 0);')
        lines.extend(self.MapSequence(direction, dstVHDL, node, leafTypeDict, names))
        return lines
    def MapSequenceOf(self, direction, dstVHDL, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location()) # NOSTMTCOVERAGE
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.extend( self.Map(
                direction, dstVHDL + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines
    def MapSetOf(self, direction, dstVHDL, node, leafTypeDict, names):
        return self.MapSequenceOf(direction, dstVHDL, node, leafTypeDict, names)

class MapASN1ToVHDLregisters(RecursiveMapper):
    def MapInteger(self, _, dstVHDL, node, __, ___):
        if node._range == []:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location()) # NOSTMTCOVERAGE
        bits = math.log(max(list(map(abs, node._range)))+1, 2)
        bits += (bits if node._range[0]<0 else 0)
        #return ['signal ' + dstVHDL + ' : ' + ('std_logic_vector(63 downto 0); -- normally, %d bits instead of 63' % bits)]
        return ['signal ' + dstVHDL + ' : ' + ('std_logic_vector(63 downto 0); -- ASSERT uses 64 bit INTEGERs (optimal would be %d bits)' % bits)]
    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location()) # NOSTMTCOVERAGE
    def MapBoolean(self, _, dstVHDL, __, ___, dummy):
        return ['signal ' + dstVHDL + ' : ' + 'std_logic;']
    def MapOctetString(self, _, dstVHDL, node, __, ___):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location()) # NOSTMTCOVERAGE
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.append('signal ' + dstVHDL + ('_elem_%0*d: ' % (maxlen, i)) + 'std_logic_vector(7 downto 0);')
        return lines
    def MapEnumerated(self, _, dstVHDL, __, ___, dummy):
        return ['signal ' + dstVHDL + ' : ' + 'std_logic(7 downto 0);']
    def MapSequence(self, _, dstVHDL, node, leafTypeDict, names):
        lines = []
        for x in node._members:
            lines.extend( self.Map(_, dstVHDL+"_"+CleanName(x[0]), x[1], leafTypeDict, names) )
        return lines
    def MapSet(self, _, dstVHDL, node, leafTypeDict, names):
        return self.MapSequence(_, dstVHDL, node, leafTypeDict, names)
    def MapChoice(self, _, dstVHDL, node, leafTypeDict, names):
        lines = []
        lines.append('signal ' + dstVHDL + '_choiceIdx : ' + 'std_logic_vector(7 downto 0);')
        lines.extend(self.MapSequence(_, dstVHDL, node, leafTypeDict, names))
        return lines
    def MapSequenceOf(self, _, dstVHDL, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location()) # NOSTMTCOVERAGE
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.extend( self.Map(
                _, dstVHDL + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines
    def MapSetOf(self, _, dstVHDL, node, leafTypeDict, names):
        return self.MapSequenceOf(_, dstVHDL, node, leafTypeDict, names)

class MapASN1ToVHDLreadinputdata(RecursiveMapper):
    def MapInteger(self, reginfo, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location()) # NOSTMTCOVERAGE
        #bits = math.log(max(map(abs, node._range)+1),2)+(1 if node._range[0]<0 else 0)
        lines = []
        lines.append('when X"%s" => %s( 7 downto  0) <= DataIn;' % (hex(reginfo[0] + 0)[2:], dstVHDL))
        lines.append('when X"%s" => %s(15 downto  8) <= DataIn;' % (hex(reginfo[0] + 1)[2:], dstVHDL))
        lines.append('when X"%s" => %s(23 downto 16) <= DataIn;' % (hex(reginfo[0] + 2)[2:], dstVHDL))
        lines.append('when X"%s" => %s(31 downto 24) <= DataIn;' % (hex(reginfo[0] + 3)[2:], dstVHDL))
        lines.append('when X"%s" => %s(39 downto 32) <= DataIn;' % (hex(reginfo[0] + 4)[2:], dstVHDL))
        lines.append('when X"%s" => %s(47 downto 40) <= DataIn;' % (hex(reginfo[0] + 5)[2:], dstVHDL))
        lines.append('when X"%s" => %s(55 downto 48) <= DataIn;' % (hex(reginfo[0] + 6)[2:], dstVHDL))
        lines.append('when X"%s" => %s(63 downto 56) <= DataIn;' % (hex(reginfo[0] + 7)[2:], dstVHDL))
        reginfo[0] += 8
        return lines
    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location()) # NOSTMTCOVERAGE
    def MapBoolean(self, reginfo, dstVHDL, _, __, ___):
        lines = ['when X"%s" => %s <= DataIn(0);' % (hex(reginfo[0])[2:], dstVHDL)]
        reginfo[0] += 1
        return lines
    def MapOctetString(self, reginfo, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location()) # NOSTMTCOVERAGE
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.append('when X"%s" => %s_elem_%0*d(7 downto 0) <= DataIn;' % 
                (hex(reginfo[0])[2:], dstVHDL, maxlen, i))
            reginfo[0] += 1
        return lines
    def MapEnumerated(self, reginfo, dstVHDL, _, __, ___):
        lines = ['when X"%s" => %s(7 downto 0) <= DataIn;' % (hex(reginfo[0])[2:], dstVHDL)]
        reginfo[0] += 1
        return lines
    def MapSequence(self, reginfo, dstVHDL, node, leafTypeDict, names):
        lines = []
        for x in node._members:
            lines.extend( self.Map(reginfo, dstVHDL+"_"+CleanName(x[0]), x[1], leafTypeDict, names) )
        return lines
    def MapSet(self, reginfo, dstVHDL, node, leafTypeDict, names):
        return self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names)
    def MapChoice(self, reginfo, dstVHDL, node, leafTypeDict, names):
        lines = ['when X"%s" => %s_choiceIdx(7 downto 0) <= DataIn;' % (hex(reginfo[0])[2:], dstVHDL)]
        reginfo[0] += 1
        lines.extend(self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names))
        return lines
    def MapSequenceOf(self, reginfo, dstVHDL, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location()) # NOSTMTCOVERAGE
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.extend( self.Map(
                reginfo, dstVHDL + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines
    def MapSetOf(self, reginfo, dstVHDL, node, leafTypeDict, names):
        return self.MapSequenceOf(reginfo, dstVHDL, node, leafTypeDict, names)

class MapASN1ToVHDLwriteoutputdata(RecursiveMapper):
    def MapInteger(self, reginfo, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location()) # NOSTMTCOVERAGE
        #bits = math.log(max(map(abs, node._range)+1),2)+(1 if node._range[0]<0 else 0)
        lines = []
        lines.append('when X"%s" => DataOut <= %s( 7 downto  0);' % (hex(reginfo[0] + 0)[2:], dstVHDL))
        lines.append('when X"%s" => DataOut <= %s(15 downto  8);' % (hex(reginfo[0] + 1)[2:], dstVHDL))
        lines.append('when X"%s" => DataOut <= %s(23 downto 16);' % (hex(reginfo[0] + 2)[2:], dstVHDL))
        lines.append('when X"%s" => DataOut <= %s(31 downto 24);' % (hex(reginfo[0] + 3)[2:], dstVHDL))
        lines.append('when X"%s" => DataOut <= %s(39 downto 32);' % (hex(reginfo[0] + 4)[2:], dstVHDL))
        lines.append('when X"%s" => DataOut <= %s(47 downto 40);' % (hex(reginfo[0] + 5)[2:], dstVHDL))
        lines.append('when X"%s" => DataOut <= %s(55 downto 48);' % (hex(reginfo[0] + 6)[2:], dstVHDL))
        lines.append('when X"%s" => DataOut <= %s(63 downto 56);' % (hex(reginfo[0] + 7)[2:], dstVHDL))
        reginfo[0] += 8
        return lines
    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location()) # NOSTMTCOVERAGE
    def MapBoolean(self, reginfo, dstVHDL, _, __, ___):
        lines = ['when X"%s" => DataOut(0) <= %s;' % (hex(reginfo[0])[2:], dstVHDL)]
        reginfo[0] += 1
        return lines
    def MapOctetString(self, reginfo, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location()) # NOSTMTCOVERAGE
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.append('when X"%s" => DataOut <= %s_elem_%0*d(7 downto 0);' % 
                (hex(reginfo[0])[2:], dstVHDL, maxlen, i))
            reginfo[0] += 1
        return lines
    def MapEnumerated(self, reginfo, dstVHDL, _, __, ___):
        lines = ['when X"%s" => DataOut <= %s(7 downto 0);' % (hex(reginfo[0])[2:], dstVHDL)]
        reginfo[0] += 1
        return lines
    def MapSequence(self, reginfo, dstVHDL, node, leafTypeDict, names):
        lines = []
        for x in node._members:
            lines.extend( self.Map(reginfo, dstVHDL+"_"+CleanName(x[0]), x[1], leafTypeDict, names) )
        return lines
    def MapSet(self, reginfo, dstVHDL, node, leafTypeDict, names):
        return self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names)
    def MapChoice(self, reginfo, dstVHDL, node, leafTypeDict, names):
        lines = ['when X"%s" => DataOut <= %s_choiceIdx(7 downto 0);' % (hex(reginfo[0])[2:], dstVHDL)]
        reginfo[0] += 1
        lines.extend(self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names))
        return lines
    def MapSequenceOf(self, reginfo, dstVHDL, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location()) # NOSTMTCOVERAGE
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.extend( self.Map(
                reginfo, dstVHDL + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines
    def MapSetOf(self, reginfo, dstVHDL, node, leafTypeDict, names):
        return self.MapSequenceOf(reginfo, dstVHDL, node, leafTypeDict, names)

class MapASN1ToSystemCconnections(RecursiveMapper):
    def MapInteger(self, srcRegister, dstCircuitPort, _, __, ___):
        return [dstCircuitPort + ' => ' + srcRegister]
    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location()) # NOSTMTCOVERAGE
    def MapBoolean(self, srcRegister, dstCircuitPort, __, ___, dummy):
        return [dstCircuitPort + ' => ' + srcRegister]
    def MapOctetString(self, srcRegister, dstCircuitPort, node, __, ___):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location()) # NOSTMTCOVERAGE
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.append(dstCircuitPort + ('_elem_%0*d' % (maxlen, i)) + ' => ' + srcRegister + ('_elem_%0*d' % (maxlen, i)))
        return lines
    def MapEnumerated(self, srcRegister, dstCircuitPort, __, ___, dummy):
        return [dstCircuitPort + ' => ' + srcRegister]
    def MapSequence(self, srcRegister, dstCircuitPort, node, leafTypeDict, names):
        lines = []
        for x in node._members:
            lines.extend( self.Map(srcRegister+"_"+CleanName(x[0]), dstCircuitPort+"_"+CleanName(x[0]), x[1], leafTypeDict, names) )
        return lines
    def MapSet(self, srcRegister, dstCircuitPort, node, leafTypeDict, names):
        return self.MapSequence(srcRegister, dstCircuitPort, node, leafTypeDict, names)
    def MapChoice(self, srcRegister, dstCircuitPort, node, leafTypeDict, names):
        lines = []
        lines.append(dstCircuitPort + '_choiceIdx => ' + srcRegister + '_choiceIdx')
        lines.extend(self.MapSequence(srcRegister, dstCircuitPort, node, leafTypeDict, names))
        return lines
    def MapSequenceOf(self, srcRegister, dstCircuitPort, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location()) # NOSTMTCOVERAGE
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.extend( self.Map(
                srcRegister+('_elem_%0*d'%(maxlen,i)), dstCircuitPort+('_elem_%0*d'%(maxlen,i)), node._containedType, leafTypeDict, names))
        return lines
    def MapSetOf(self, srcRegister, dstCircuitPort, node, leafTypeDict, names):
        return self.MapSequenceOf(srcRegister, dstCircuitPort, node, leafTypeDict, names)

#class MapASN1ToSystemCheader(RecursiveMapper):
#    def MapInteger(self, state, systemCvar, _, __, ___):
#        state.systemcHeader.write('    ' + state.directionPrefix + 'sc_uint<64> > ' + systemCvar + ';\n')   
#        return []
#    def MapReal(self, _, __, node, ___, dummy):
#        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location()) # NOSTMTCOVERAGE
#    def MapBoolean(self, state, systemCvar, _, __, ___):
#        state.systemcHeader.write('    ' + state.directionPrefix + 'bool> ' + systemCvar + ';\n')
#        return []
#    def MapOctetString(self, state, systemCvar, node, __, ___):
#        if node._range == []:
#            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location()) # NOSTMTCOVERAGE
#        if len(node._range)>1 and node._range[0]!=node._range[1]:
#            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location()) # NOSTMTCOVERAGE
#        maxlen = len(str(node._range[-1]))
#        for i in range(node._range[-1]):
#            state.systemcHeader.write('    ' + state.directionPrefix + 'sc_uint<8> > ' + ('%s_elem_%0*d'%(systemCvar, maxlen, i)) + ';\n' )
#        return []
#    def MapEnumerated(self, state, systemCvar, __, ___, dummy):
#        state.systemcHeader.write('    ' + state.directionPrefix + 'sc_uint<8> > ' + systemCvar + ';\n')
#        return []
#    def MapSequence(self, state, systemCvar, node, leafTypeDict, names):
#        for x in node._members:
#            self.Map(state, systemCvar+"_"+CleanName(x[0]), x[1], leafTypeDict, names)
#        return []
#    def MapSet(self, state, systemCvar, node, leafTypeDict, names):
#        return self.MapSequence(state, systemCvar, node, leafTypeDict, names)
#    def MapChoice(self, state, systemCvar, node, leafTypeDict, names):
#        state.systemcHeader.write('    ' + state.directionPrefix + 'sc_uint<8> >' + systemCvar + '_choiceIdx;\n')
#        self.MapSequence(state, systemCvar, node, leafTypeDict, names)
#        return []
#    def MapSequenceOf(self, state, systemCvar, node, leafTypeDict, names):
#        if node._range == []:
#            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location()) # NOSTMTCOVERAGE
#        if len(node._range)>1 and node._range[0]!=node._range[1]:
#            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location()) # NOSTMTCOVERAGE
#        maxlen = len(str(node._range[-1]))
#        for i in range(node._range[-1]):
#            self.Map(state, systemCvar+('_elem_%0*d'%(maxlen, i)), node._containedType, leafTypeDict, names)
#        return []
#    def MapSetOf(self, state, systemCvar, node, leafTypeDict, names):
#        return self.MapSequenceOf(state, systemCvar, node, leafTypeDict, names)

class MapASN1ToOutputs(RecursiveMapper):
    def MapInteger(self, paramName, _, dummy, __, ___):
        return [paramName]
    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location()) # NOSTMTCOVERAGE
    def MapBoolean(self, paramName, _, dummy, __, ___):
        return [paramName]
    def MapOctetString(self, paramName, _, node, __, ___):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location()) # NOSTMTCOVERAGE
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.append('%s_elem_%0*d' % (paramName, maxlen, i))
        return lines
    def MapEnumerated(self, paramName, dummy, _, __, ___):
        lines = [paramName]
        return lines
    def MapSequence(self, paramName, dummy, node, leafTypeDict, names):
        lines = []
        for x in node._members:
            lines.extend( self.Map(paramName+"_"+CleanName(x[0]), dummy, x[1], leafTypeDict, names) )
        return lines
    def MapSet(self, paramName, dummy, node, leafTypeDict, names):
        return self.MapSequence(paramName, dummy, node, leafTypeDict, names)
    def MapChoice(self, paramName, dummy, node, leafTypeDict, names):
        lines = ['%s_choiceIdx' % paramName]
        lines.extend(self.MapSequence(paramName, dummy, node, leafTypeDict, names))
        return lines
    def MapSequenceOf(self, paramName, dummy, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location()) # NOSTMTCOVERAGE
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location()) # NOSTMTCOVERAGE
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.extend( self.Map(paramName + ('_elem_%0*d' % (maxlen, i)), dummy, node._containedType, leafTypeDict, names))
        return lines
    def MapSetOf(self, reginfo, dstVHDL, node, leafTypeDict, names):
        return self.MapSequenceOf(reginfo, dstVHDL, node, leafTypeDict, names)

g_placeholders = {
    "circuits":'',
    "ioregisters":'',
    "startStopSignals":'',
    "reset":'',
    "updateStartStopPulses":'',
    "readinputdata":'',
    "outputs":'',
    "completions":'',
    "writeoutputdata":'',
    "clearoutputs":'',
    "connectionsToSystemC":'',
    "updatePulseHistories":''
}

def AddToStr(s, d):
    g_placeholders[s] += d

#def Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
def Common(nodeTypename, node, subProgram, _, param, leafTypeDict, names):
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
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)

def OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)

def OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)

def OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    Common(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    vhdlBackend.OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)

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
    # systemCheaderMapper = MapASN1ToSystemCheader()
    outputsMapper = MapASN1ToOutputs()

    outputs = []
    completions = []
    
    # systemcHeader = open(vhdlBackend.dir + 'circuit.h', 'w')
    # systemcHeader.write('#ifndef CIRCUIT_H\n')
    # systemcHeader.write('#define CIRCUIT_H\n\n')
    # systemcHeader.write('#ifndef SC_SYNTHESIS\n')
    # systemcHeader.write('#include "systemc.h"\n')
    # systemcHeader.write('#endif\n\n')

    # systemcBody = open(vhdlBackend.dir + 'circuit.cpp', 'w')
    # systemcBody.write('#include "circuit.h"\n\n')

    for c in VHDL_Circuit.allCircuits:
        circuitLines = []

        ioregisterLines = []

        readinputdataLines = []
        readinputdataLines.append("\n" + ' '*22 + '-- kickoff ' + c._spCleanName)
        kickoffWriteAccess = "when X\"%(off)s\" => %(pi)s_StartCalculationsInternal <= %(pi)s_StartCalculationsInternal xor '1';\n" % {'pi':c._spCleanName, 'off':hex(0x2000 + c._offset)[2:]}
        readinputdataLines.append(kickoffWriteAccess)

        connectionsToSystemCLines = []

        counter = [0x2000 + c._offset+1]
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
                outputs.extend([c._spCleanName+'_'+x for x in outputsMapper.Map(p._id, 1, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names)])
                                
        writeoutputdataLines = []
        writeoutputdataLines.append("\n" + ' '*16 + '-- result calculated flag ' + c._spCleanName)
        accessCompletionFlag = "when X\"%(off)s\" => DataOut <= \"0000000\" & %(pi)s_CalculationsComplete;\n" % \
            {'pi':c._spCleanName, 'off':hex(0x2000 + c._offset)[2:]}
        writeoutputdataLines.append(accessCompletionFlag)

        for p in c._sp._params:
            node = VHDL_Circuit.names[p._signal._asnNodename]
            if not isinstance(p, InParam):
                writeoutputdataLines.extend(
                    writeoutputdataMapper.Map(
                        counter, c._spCleanName + '_' + p._id, node, VHDL_Circuit.leafTypeDict, VHDL_Circuit.names))

        completions.append(c._spCleanName + '_CalculationsComplete')

        AddToStr('circuits', '    component %s is\n' % c._spCleanName)
        AddToStr('circuits', '    port (\n')
        AddToStr('circuits', '\n'.join(['        '+x for x in circuitLines]) + '\n')
        AddToStr('circuits', '        start_%s  : in  std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '        finish_%s : out std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '        clock_%s : in std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '        reset_%s  : in  std_logic\n' % c._spCleanName)
        AddToStr('circuits', '    );\n')
        AddToStr('circuits', '    end component;\n\n')

        AddToStr('ioregisters', '\n'.join(['    '+x for x in ioregisterLines]) + '\n\n')

        AddToStr('startStopSignals', 
'''    signal %(pi)s_StartCalculationsInternalOld : std_logic;
    signal %(pi)s_StartCalculationsInternal : std_logic;
    signal %(pi)s_StartCalculationsPulse : std_logic;
    signal %(pi)s_CalculationsComplete : std_logic;          -- the finish signal for %(pi)s

''' % {'pi':c._spCleanName})

        AddToStr('reset', "            %(pi)s_StartCalculationsInternal <= '0';\n" % {'pi':c._spCleanName})
        AddToStr('updateStartStopPulses',
            '            %(pi)s_StartCalculationsPulse <= %(pi)s_StartCalculationsInternal xor %(pi)s_StartCalculationsInternalOld;\n' % {'pi':c._spCleanName})
        AddToStr('updateStartStopPulses',
            '            %(pi)s_StartCalculationsInternalOld <= %(pi)s_StartCalculationsInternal;\n' % {'pi':c._spCleanName})

        AddToStr('readinputdata', '\n'.join([' '*22 +x for x in readinputdataLines])+'\n')
        AddToStr('writeoutputdata', '\n'.join([' '*16 +x for x in writeoutputdataLines])+'\n')

        AddToStr('connectionsToSystemC', '\n    Interface_%s : %s\n' % (c._spCleanName, c._spCleanName))
        AddToStr('connectionsToSystemC', '        port map (\n')
        AddToStr('connectionsToSystemC', ',\n'.join(['            '+x for x in connectionsToSystemCLines]) + ',\n')
        AddToStr('connectionsToSystemC', '            start_%s => %s_StartCalculationsPulse,\n' % (c._spCleanName, c._spCleanName))
        AddToStr('connectionsToSystemC', '            finish_%s => %s_CalculationsComplete,\n' % (c._spCleanName, c._spCleanName))
        AddToStr('connectionsToSystemC', '            clock_%s => CLK,\n' % c._spCleanName)
        AddToStr('connectionsToSystemC', '            reset_%s => RST\n' % c._spCleanName)
        AddToStr('connectionsToSystemC', '        );\n')

#         systemcHeader.write('class ' + c._spCleanName + ' : public sc_module\n')
#         systemcHeader.write('{\n')
#         systemcHeader.write('public:\n')
#         for p in c._sp._params:
#             node = VHDL_Circuit.names[p._signal._asnNodename]
#             prefix = 'sc_in<' if isinstance(p, InParam) else 'sc_out<'
#             class State: 
#                 pass
#             state = State()
#             state.systemcHeader = systemcHeader
#             state.directionPrefix = prefix
#             systemCheaderMapper.Map(
#                 state,
#                 p._id,
#                 node,
#                 VHDL_Circuit.leafTypeDict,
#                 VHDL_Circuit.names)
#         systemcHeader.write('''
#     sc_in<bool>          start_%(PI)s;
#     sc_out<bool>         finish_%(PI)s;
#     sc_in<bool>          clock_%(PI)s;
# 
#     void do_%(PI)s ();
# 
#     SC_CTOR (%(PI)s)
#     {
#         SC_THREAD(do_%(PI)s);
#         sensitive_pos << clock_%(PI)s;
#     }
# ''' % {'PI':c._spCleanName})
#         systemcHeader.write('};\n\n')
# 
#         systemcBody.write('void %s::do_%s()\n' % (c._spCleanName, c._spCleanName))
#         systemcBody.write('{\n')
#         systemcBody.write('    // Declare your variables here\n')
#         systemcBody.write('    finish_%s = 0;\n' % c._spCleanName)
#         systemcBody.write('    while (1) {\n')
#         systemcBody.write('        do {\n')
#         systemcBody.write('            wait();\n')
#         systemcBody.write('        } while (!start_%s.read());\n' % c._spCleanName)
#         systemcBody.write('        finish_%s = 0;\n\n' % c._spCleanName)
#         systemcBody.write('        // Write your processing logic here\n')
#         for p in c._sp._params:
#             if not isinstance(p, OutParam):
#                 systemcBody.write('        // Read data from %s\n' % CleanName(p._id))
#         systemcBody.write('        // ...\n\n')
#         for p in c._sp._params:
#             if isinstance(p, OutParam):
#                 systemcBody.write('        // Write result for %s\n' % CleanName(p._id))
#         systemcBody.write('        finish_%s = 1;\n' % c._spCleanName)
#         systemcBody.write('        wait();\n')
#         systemcBody.write('    }\n')
#         systemcBody.write('}\n\n')

    AddToStr('outputs', ', '.join(outputs) + (', ' if len(outputs) else ''))
    AddToStr('completions', ', '.join(completions))

    # Handle invalid write accesses in the passinput space by kicking off the last circuit (i.e. an FDIR circuit)
    if len(VHDL_Circuit.allCircuits)>0:
        alternate_kickoffWriteAccess = "when others => %(pi)s_StartCalculationsInternal <= %(pi)s_StartCalculationsInternal xor '1';\n" % {'pi':VHDL_Circuit.allCircuits[-1]._spCleanName}
    AddToStr('readinputdata', ' '*22 + alternate_kickoffWriteAccess)

    from . import vhdlTemplate
    vhdlFile = open(vhdlBackend.dir + 'TASTE.vhd', 'w')
    vhdlFile.write( vhdlTemplate.vhd % g_placeholders )
    vhdlFile.close()

    msg = ""
    for c in VHDL_Circuit.allCircuits:
        msg += '    circuit_%s.vhd         \\\n' % c._spCleanName
        msg += '    circuit_%s_do_%s.vhd   \\\n' % (c._spCleanName, c._spCleanName)
    makefile = open(vhdlBackend.dir + 'Makefile', 'w')
    makefile.write(vhdlTemplate.makefile % {'circuit_autofiles':msg})
    makefile.close()

    # systemcHeader.write('\n#endif\n')
    # systemcHeader.close()

    msg = ""
    for c in VHDL_Circuit.allCircuits:
        msg += 'vhdl work "circuit_%s.vhd"\n' % c._spCleanName
        msg += 'vhdl work "circuit_%s_do_%s.vhd"\n' % (c._spCleanName, c._spCleanName)
    prj = open(vhdlBackend.dir + 'TASTE.prj', 'w')
    prj.write(vhdlTemplate.prj % {'circuits':msg})
    prj.close()
