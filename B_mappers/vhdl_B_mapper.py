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

import re
import os
import math

from commonPy.utility import panic, panicWithCallStack
from commonPy.asnAST import AsnBasicNode, AsnSequence, AsnSet, AsnChoice, AsnSequenceOf, AsnSetOf, AsnEnumerated, AsnMetaMember, isSequenceVariable, sourceSequenceLimit
from commonPy.aadlAST import InParam, OutParam, InOutParam, AadlPort, AadlParameter
import commonPy.asnParser

from .recursiveMapper import RecursiveMapper
from .synchronousTool import SynchronousToolGlueGenerator

isAsynchronous = False
vhdlBackend = None

# Dictionary for octet string VHDL type declarations
g_octStr = []


def Version():
    print("Code generator: " + "$Id: vhdl_B_mapper.py 2390 2012-07-19 12:39:17Z ttsiodras $")  # pragma: no cover


def CleanName(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def RegistersAllocated(node):
    # The ESA FPGA needs alignment to 4 byte offsets
    names = commonPy.asnParser.g_names
    while isinstance(node, str):
        node = names[node]
    if isinstance(node, AsnBasicNode):
        retValue = 0
        realLeafType = commonPy.asnParser.g_leafTypeDict[node._leafType]
        if realLeafType == "INTEGER":
            retValue = 8
        elif realLeafType == "REAL":
            panic("The VHDL mapper can't work with REALs (non-synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover
        elif realLeafType == "BOOLEAN":
            retValue = 4
        elif realLeafType == "OCTET STRING":
            if node._range == []:
                panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
            if len(node._range)>1 and node._range[0]!=node._range[1]:
                panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
            if node._range[-1] not in g_octStr:
                g_octStr.append(node._range[-1])
            retValue = 4*(int((node._range[-1]+3)/4))
        else:  # pragma: no cover
            panicWithCallStack("Basic type %s can't be mapped..." % realLeafType)  # pragma: no cover
        return retValue
    elif isinstance(node, AsnSequence):
        return sum(map(RegistersAllocated, [x[1] for x in node._members]))
    elif isinstance(node, AsnSet):
        return sum(map(RegistersAllocated, [x[1] for x in node._members]))
    elif isinstance(node, AsnChoice):
        return 4 + sum(map(RegistersAllocated, [x[1] for x in node._members]))
    elif isinstance(node, AsnSequenceOf):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        return node._range[-1] * RegistersAllocated(node._containedType)
    elif isinstance(node, AsnSetOf):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        return node._range[-1] * RegistersAllocated(node._containedType)
    elif isinstance(node, AsnEnumerated):
        return 4
    elif isinstance(node, AsnMetaMember):
        return RegistersAllocated(names[node._containedType])
    else:  # pragma: no cover
        panicWithCallStack("unsupported %s (%s)" % (str(node.__class__), node.Location()))  # pragma: no cover


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
        VHDL_Circuit.currentOffset += 4  # reserve one register for "start" signal
        self._paramOffset = {}
        for p in sp._params:
            self._paramOffset[p._id] = VHDL_Circuit.currentOffset
            VHDL_Circuit.currentOffset += RegistersAllocated(p._signal._asnNodename)
        if VHDL_Circuit.currentOffset > 256:
            panicWithCallStack("For the ESA FPGA, there is a limit of 63 registers (252/4) - your design required %d." % (VHDL_Circuit.currentOffset/4))

    def __str__(self):
        msg = "PI:%s\n" % self._sp._id  # pragma: no cover
        msg += ''.join([p[0]._id+':'+p[0]._signal._asnNodename+("(in)" if isinstance(p[0], InParam) else "(out)")+'\n' for p in self._params])  # pragma: no cover
        return msg  # pragma: no cover

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

    def MapReal(self, dummy, _, node, __, ___):
        panicWithCallStack("REALs (%s) cannot be used for synthesizeable VHDL" % node.Location())  # pragma: no cover
        # return ["%s = (double) %s;\n" % (destVar, srcVHDL)]

    def MapBoolean(self, srcVHDL, destVar, _, __, ___):
        register = srcVHDL[0] + srcVHDL[1]
        lines=[]
        lines.append("{\n")
        lines.append("    unsigned tmp;\n")
        lines.append("    tmp = ESAReadRegister(BASE_ADDR + %s);\n" % hex(register))
        lines.append("    %s = (asn1SccUint) tmp;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 4
        return lines

    def MapOctetString(self, srcVHDL, destVar, node, _, __):
        register = srcVHDL[0] + srcVHDL[1]
        lines = []
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        for i in range(0, int((node._range[-1]+3)/4)):
            lines.append("{\n")
            lines.append("    unsigned tmp;\n")
            lines.append("    tmp = ESAReadRegister(BASE_ADDR + %s);\n" % hex(register+i*4))
            if (i*4<node._range[-1]):
                lines.append("    %s.arr[%d] = tmp & 0xFF;\n" % (destVar, i*4))
            if (i*4+1<node._range[-1]):
                lines.append("    %s.arr[%d] = (tmp & 0xFF00) >> 8;\n" % (destVar, i*4+1))
            if (i*4+2<node._range[-1]):
                lines.append("    %s.arr[%d] = (tmp & 0xFF0000) >> 16;\n" % (destVar, i*4+2))
            if (i*4+3<node._range[-1]):
                lines.append("    %s.arr[%d] = (tmp & 0xFF000000) >> 24;\n" % (destVar, i*4+3))
            lines.append("}\n")
        if isSequenceVariable(node):
            lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        srcVHDL[0] += 4*int((node._range[-1]+3)/4)
        return lines

    def MapEnumerated(self, srcVHDL, destVar, _, __, ___):
        register = srcVHDL[0] + srcVHDL[1]
        lines=[]
        lines.append("{\n")
        lines.append("    unsigned char tmp;\n")
        lines.append("    tmp = ESAReadRegister(BASE_ADDR + %s);\n" % hex(register))
        lines.append("    %s = tmp;\n" % destVar)
        lines.append("}\n")
        srcVHDL[0] += 4
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
        return self.MapSequence(srcVHDL, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVHDL, destVar, node, leafTypeDict, names):
        register = srcVHDL[0] + srcVHDL[1]
        lines = []
        childNo = 0
        lines.append("{\n")
        lines.append("    unsigned choiceIdx = 0;\n")
        lines.append("    choiceIdx = ESAReadRegister(BASE_ADDR + %s);\n" % hex(register))
        for child in node._members:
            childNo += 1
            lines.append("    %sif (choiceIdx == %d) {\n" % (self.maybeElse(childNo), childNo))
            srcVHDL[0] += 4
            lines.extend(['        '+x for x in self.Map(
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

    def MapSequenceOf(self, srcVHDL, destVar, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        #isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []
        for i in range(0, node._range[-1]):
            lines.extend(
                self.Map(
                    #isMappedToPrimitive and ("%s.element_data[%d]" % (srcVHDL, i)) or ("%s.element_%02d" % (srcVHDL, i)),
                    srcVHDL,
                    destVar + ".arr[%d]" % i,
                    node._containedType,
                    leafTypeDict,
                    names))
        if isSequenceVariable(node):
            lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapSetOf(self, srcVHDL, destVar, node, leafTypeDict, names):
        return self.MapSequenceOf(srcVHDL, destVar, node, leafTypeDict, names)  # pragma: nocover


class FromASN1SCCtoVHDL(RecursiveMapper):
    def MapInteger(self, srcVar, dstVHDL, _, __, ___):
        register = dstVHDL[0] + dstVHDL[1]
        lines=[]
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

    def MapReal(self, dummy, _, node, __, ___):
        panicWithCallStack("REALs (%s) cannot be used for synthesizeable VHDL" % node.Location())  # pragma: no cover
        #return ["%s = %s;\n" % (dstVHDL, srcVar)]

    def MapBoolean(self, srcVar, dstVHDL, _, __, ___):
        register = dstVHDL[0] + dstVHDL[1]
        lines=[]
        lines.append("{\n")
        lines.append("    unsigned tmp = %s;\n" % srcVar)
        lines.append("    ESAWriteRegister(BASE_ADDR + %s, tmp);\n" % hex(register))
        lines.append("}\n")
        dstVHDL[0] += 4
        return lines

    def MapOctetString(self, srcVar, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if isSequenceVariable(node):
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        register = dstVHDL[0] + dstVHDL[1]
        limit = sourceSequenceLimit(node, srcVar)
        lines = []
        for i in range(0, int((node._range[-1]+3)/4)):
            lines.append("{\n")
            lines.append("    unsigned tmp = 0;\n")
            for shift in range(0, 4):
                if i*4+shift<node._range[-1]:
                    if isSequenceVariable(node):
                        lines.append("    if (%s >= %d)\n" % (limit, i*4+shift+1))
                        lines.append("        tmp |= ((unsigned)%s.arr[%d]) << %d;\n" % (srcVar, i*4+shift, shift*8))
                    else:
                        lines.append("    tmp |= ((unsigned)%s.arr[%d]) << %d;\n" % (srcVar, i*4+shift, shift*8))
            lines.append("    ESAWriteRegister(BASE_ADDR + %s + %d, tmp);\n" % (hex(register), i*4))
            lines.append("}\n")
        dstVHDL[0] += 4*int((node._range[-1]+3)/4)
        return lines

    def MapEnumerated(self, srcVar, dstVHDL, node, __, ___):
        if None in [x[1] for x in node._members]:
            panicWithCallStack("an ENUMERATED must have integer values! (%s)" % node.Location())  # pragma: no cover
        register = dstVHDL[0] + dstVHDL[1]
        lines=[]
        lines.append("{\n")
        lines.append("    unsigned tmp = %s;\n" % srcVar)
        lines.append("    ESAWriteRegister(BASE_ADDR + %s, tmp);\n" % hex(register))
        lines.append("}\n")
        dstVHDL[0] += 4
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
        return self.MapSequence(srcVar, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar, dstVHDL, node, leafTypeDict, names):
        register = dstVHDL[0] + dstVHDL[1]
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.kind == %s) {\n" % (self.maybeElse(childNo), srcVar, self.CleanName(child[2])))
            lines.append("    unsigned tmp = %d;\n" % childNo)
            lines.append("    ESAWriteRegister(BASE_ADDR + %s, tmp);\n" % hex(register))
            dstVHDL[0] += 4
            lines.extend(['    '+x for x in self.Map(
                         srcVar + ".u." + self.CleanName(child[0]),
                         dstVHDL,
                         child[1],
                         leafTypeDict,
                         names)])
            dstVHDL[0] -= 4
            lines.append("}\n")
        dstVHDL[0] += 4
        return lines

    def MapSequenceOf(self, srcVar, dstVHDL, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
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
        return self.MapSequenceOf(srcVar, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


class VHDLGlueGenerator(SynchronousToolGlueGenerator):
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


class MapASN1ToVHDLCircuit(RecursiveMapper):
    def MapInteger(self, direction, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        bits = math.log(max(list(map(abs, node._range)))+1, 2)
        bits += bits if node._range[0]<0 else 0
        #return [dstVHDL + ' : ' + direction + ('std_logic_vector(63 downto 0); -- normally, %d instead of 63' % bits)]
        return [dstVHDL + ' : ' + direction + ('std_logic_vector(63 downto 0); -- ASSERT uses 64 bit INTEGERs (optimal would be %d bits)' % bits)]

    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, direction, dstVHDL, _, __, ___):
        return [dstVHDL + ' : ' + direction + 'std_logic;']

    def MapOctetString(self, direction, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []
        lines.append(dstVHDL + ': ' + direction + 'octStr_%d;' % node._range[-1])
        return lines

    def MapEnumerated(self, direction, dstVHDL, _, __, ___):
        return [dstVHDL + ' : ' + direction + 'std_logic_vector(7 downto 0);']

    def MapSequence(self, direction, dstVHDL, node, leafTypeDict, names):
        lines = []
        for x in node._members:
            lines.extend(self.Map(direction, dstVHDL+"_"+CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, direction, dstVHDL, node, leafTypeDict, names):
        return self.MapSequence(direction, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, direction, dstVHDL, node, leafTypeDict, names):
        lines = []
        lines.append(dstVHDL + '_choiceIdx : ' + direction + 'std_logic_vector(7 downto 0);')
        lines.extend(self.MapSequence(direction, dstVHDL, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, direction, dstVHDL, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.extend(self.Map(
                direction, dstVHDL + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, direction, dstVHDL, node, leafTypeDict, names):
        return self.MapSequenceOf(direction, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


class MapASN1ToVHDLregisters(RecursiveMapper):
    def MapInteger(self, _, dstVHDL, node, __, ___):
        if node._range == []:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        bits = math.log(max(list(map(abs, node._range)))+1, 2)
        bits += (bits if node._range[0]<0 else 0)
        #return ['signal ' + dstVHDL + ' : ' + ('std_logic_vector(63 downto 0); -- normally, %d bits instead of 63' % bits)]
        return ['signal ' + dstVHDL + ' : ' + ('std_logic_vector(63 downto 0); -- ASSERT uses 64 bit INTEGERs (optimal would be %d bits)' % bits)]

    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, _, dstVHDL, __, ___, dummy):
        return ['signal ' + dstVHDL + ' : ' + 'std_logic;']

    def MapOctetString(self, _, dstVHDL, node, __, ___):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []
        lines.append('signal ' + dstVHDL + ': ' + 'octStr_%d;' % node._range[-1])
        return lines

    def MapEnumerated(self, _, dstVHDL, __, ___, dummy):
        return ['signal ' + dstVHDL + ' : ' + 'std_logic_vector(7 downto 0);']

    def MapSequence(self, _, dstVHDL, node, leafTypeDict, names):
        lines = []
        for x in node._members:
            lines.extend(self.Map(_, dstVHDL+"_"+CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, _, dstVHDL, node, leafTypeDict, names):
        return self.MapSequence(_, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, _, dstVHDL, node, leafTypeDict, names):
        lines = []
        lines.append('signal ' + dstVHDL + '_choiceIdx : ' + 'std_logic_vector(7 downto 0);')
        lines.extend(self.MapSequence(_, dstVHDL, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, _, dstVHDL, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.extend(self.Map(
                _, dstVHDL + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, _, dstVHDL, node, leafTypeDict, names):
        return self.MapSequenceOf(_, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


class MapASN1ToVHDLreadinputdata(RecursiveMapper):
    def MapInteger(self, reginfo, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        #bits = math.log(max(map(abs, node._range)+1),2)+(1 if node._range[0]<0 else 0)
        lines = []
        lines.append('%s(31 downto  0) <= regs(%d);' % (dstVHDL, reginfo[0]))
        lines.append('%s(63 downto  32) <= regs(%d);' % (dstVHDL, reginfo[0]+1))
        reginfo[0] += 2
        return lines

    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, reginfo, dstVHDL, _, __, ___):
        lines = ['%s <= regs(%d)(0);' % (dstVHDL, reginfo[0])]
        reginfo[0] += 1
        return lines

    def MapOctetString(self, reginfo, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []
        for i in range(node._range[-1]):
            realOffset = 4*reginfo[0] + i
            bitStart = 31 - 8*(realOffset % 4)
            bitEnd = bitStart - 7
            lines.append('%s(%d)(7 downto 0) <= regs(%d)(%d downto %d);' %
                         (dstVHDL, i, realOffset/4, bitStart, bitEnd))
        reginfo[0] += (node._range[-1]+3)/4
        return lines

    def MapEnumerated(self, reginfo, dstVHDL, _, __, ___):
        lines = ['%s(7 downto 0) <= regs(%d)(7 downto 0);' % (dstVHDL, reginfo[0])]
        reginfo[0] += 1
        return lines

    def MapSequence(self, reginfo, dstVHDL, node, leafTypeDict, names):
        lines = []
        for x in node._members:
            lines.extend(self.Map(reginfo, dstVHDL+"_"+CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, reginfo, dstVHDL, node, leafTypeDict, names):
        return self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, reginfo, dstVHDL, node, leafTypeDict, names):
        lines = ['%s_choiceIdx(7 downto 0) <= regs(%d)(7 downto 0);' % (dstVHDL, reginfo[0])]
        reginfo[0] += 1
        lines.extend(self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, reginfo, dstVHDL, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.extend(self.Map(
                reginfo, dstVHDL + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, reginfo, dstVHDL, node, leafTypeDict, names):
        return self.MapSequenceOf(reginfo, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


class MapASN1ToVHDLwriteoutputdata(RecursiveMapper):
    def MapInteger(self, reginfo, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("INTEGERs need explicit ranges when generating VHDL code... (%s)" % node.Location())  # pragma: no cover
        #bits = math.log(max(map(abs, node._range)+1),2)+(1 if node._range[0]<0 else 0)
        lines = []
        lines.append('regs(%d) := %s(31 downto  0);' % (reginfo[0], dstVHDL))
        lines.append('regs(%d) := %s(63 downto  32);' % (reginfo[0]+1, dstVHDL))
        reginfo[0] += 2
        return lines

    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, reginfo, dstVHDL, _, __, ___):
        lines = ['regs(%d)(0) := %s;' % (reginfo[0], dstVHDL)]
        reginfo[0] += 1
        return lines

    def MapOctetString(self, reginfo, dstVHDL, node, _, __):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []
        for i in range(node._range[-1]):
            realOffset = 4*reginfo[0] + i
            bitStart = 31 - 8*(realOffset % 4)
            bitEnd = bitStart - 7
            lines.append('regs(%d)(%d downto %d) := %s(%d)(7 downto 0);' %
                         (realOffset/4, bitStart, bitEnd, dstVHDL, i))
        reginfo[0] += (node._range[-1]+3)/4
        return lines

    def MapEnumerated(self, reginfo, dstVHDL, _, __, ___):
        lines = ['regs(%d)(7 downto 0) := %s(7 downto 0);' % (reginfo[0], dstVHDL)]
        reginfo[0] += 1
        return lines

    def MapSequence(self, reginfo, dstVHDL, node, leafTypeDict, names):
        lines = []
        for x in node._members:
            lines.extend(self.Map(reginfo, dstVHDL+"_"+CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, reginfo, dstVHDL, node, leafTypeDict, names):
        return self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, reginfo, dstVHDL, node, leafTypeDict, names):
        lines = ['regs(%d)(7 downto 0) := %s_choiceIdx(7 downto 0);' % (reginfo[0], dstVHDL)]
        reginfo[0] += 1
        lines.extend(self.MapSequence(reginfo, dstVHDL, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, reginfo, dstVHDL, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.extend(self.Map(
                reginfo, dstVHDL + ('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, reginfo, dstVHDL, node, leafTypeDict, names):
        return self.MapSequenceOf(reginfo, dstVHDL, node, leafTypeDict, names)  # pragma: nocover


class MapASN1ToSystemCconnections(RecursiveMapper):
    def MapInteger(self, srcRegister, dstCircuitPort, _, __, ___):
        return [dstCircuitPort + ' => ' + srcRegister]

    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, srcRegister, dstCircuitPort, __, ___, dummy):
        return [dstCircuitPort + ' => ' + srcRegister]

    def MapOctetString(self, srcRegister, dstCircuitPort, node, __, ___):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        lines = []
        #for i in xrange(node._range[-1]):
        #    lines.append(dstCircuitPort + ('(%d)' % (i)) + ' => ' + srcRegister + ('(%d)' % (i)))
        lines.append(dstCircuitPort + ' => ' + srcRegister)
        return lines

    def MapEnumerated(self, srcRegister, dstCircuitPort, __, ___, dummy):
        return [dstCircuitPort + ' => ' + srcRegister]

    def MapSequence(self, srcRegister, dstCircuitPort, node, leafTypeDict, names):
        lines = []
        for x in node._members:
            lines.extend(self.Map(srcRegister+"_"+CleanName(x[0]), dstCircuitPort+"_"+CleanName(x[0]), x[1], leafTypeDict, names))
        return lines

    def MapSet(self, srcRegister, dstCircuitPort, node, leafTypeDict, names):
        return self.MapSequence(srcRegister, dstCircuitPort, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcRegister, dstCircuitPort, node, leafTypeDict, names):
        lines = []
        lines.append(dstCircuitPort + '_choiceIdx => ' + srcRegister + '_choiceIdx')
        lines.extend(self.MapSequence(srcRegister, dstCircuitPort, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, srcRegister, dstCircuitPort, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.extend(self.Map(
                srcRegister+('_elem_%0*d' % (maxlen, i)), dstCircuitPort+('_elem_%0*d' % (maxlen, i)), node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, srcRegister, dstCircuitPort, node, leafTypeDict, names):
        return self.MapSequenceOf(srcRegister, dstCircuitPort, node, leafTypeDict, names)  # pragma: nocover


class MapASN1ToSystemCheader(RecursiveMapper):
    def MapInteger(self, state, systemCvar, _, __, ___):
        state.systemcHeader.write('    ' + state.directionPrefix + 'sc_uint<64> > ' + systemCvar + ';\n')
        return []

    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, state, systemCvar, _, __, ___):
        state.systemcHeader.write('    ' + state.directionPrefix + 'bool> ' + systemCvar + ';\n')
        return []

    def MapOctetString(self, state, systemCvar, node, __, ___):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        for i in range(node._range[-1]):
            state.systemcHeader.write('    ' + state.directionPrefix + 'sc_uint<8> > ' + ('%s_elem_%0*d'%(systemCvar, maxlen, i)) + ';\n')
        return []

    def MapEnumerated(self, state, systemCvar, __, ___, dummy):
        state.systemcHeader.write('    ' + state.directionPrefix + 'sc_uint<8> > ' + systemCvar + ';\n')
        return []

    def MapSequence(self, state, systemCvar, node, leafTypeDict, names):
        for x in node._members:
            self.Map(state, systemCvar+"_"+CleanName(x[0]), x[1], leafTypeDict, names)
        return []

    def MapSet(self, state, systemCvar, node, leafTypeDict, names):
        return self.MapSequence(state, systemCvar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, state, systemCvar, node, leafTypeDict, names):
        state.systemcHeader.write('    ' + state.directionPrefix + 'sc_uint<8> >' + systemCvar + '_choiceIdx;\n')
        self.MapSequence(state, systemCvar, node, leafTypeDict, names)
        return []

    def MapSequenceOf(self, state, systemCvar, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        for i in range(node._range[-1]):
            self.Map(state, systemCvar+('_elem_%0*d'%(maxlen, i)), node._containedType, leafTypeDict, names)
        return []

    def MapSetOf(self, state, systemCvar, node, leafTypeDict, names):
        return self.MapSequenceOf(state, systemCvar, node, leafTypeDict, names)  # pragma: nocover


class MapASN1ToOutputs(RecursiveMapper):
    def MapInteger(self, paramName, _, dummy, __, ___):
        return [paramName]

    def MapReal(self, _, __, node, ___, dummy):
        panic("The VHDL mapper can't work with REALs (synthesizeable circuits!) (%s)" % node.Location())  # pragma: no cover

    def MapBoolean(self, paramName, _, dummy, __, ___):
        return [paramName]

    def MapOctetString(self, paramName, _, node, __, ___):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("VHDL OCTET STRING (in %s) must have a fixed SIZE constraint !" % node.Location())  # pragma: no cover
        # maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.append('%s(%d)' % (paramName, i))
        return lines

    def MapEnumerated(self, paramName, dummy, _, __, ___):
        lines = [paramName]
        return lines

    def MapSequence(self, paramName, dummy, node, leafTypeDict, names):
        lines = []
        for x in node._members:
            lines.extend(self.Map(paramName+"_"+CleanName(x[0]), dummy, x[1], leafTypeDict, names))
        return lines

    def MapSet(self, paramName, dummy, node, leafTypeDict, names):
        return self.MapSequence(paramName, dummy, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, paramName, dummy, node, leafTypeDict, names):
        lines = ['%s_choiceIdx' % paramName]
        lines.extend(self.MapSequence(paramName, dummy, node, leafTypeDict, names))
        return lines

    def MapSequenceOf(self, paramName, dummy, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("For VHDL, a SIZE constraint is mandatory (%s)!\n" % node.Location())  # pragma: no cover
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            panicWithCallStack("Must have a fixed SIZE constraint (in %s) for VHDL code!" % node.Location())  # pragma: no cover
        maxlen = len(str(node._range[-1]))
        lines = []
        for i in range(node._range[-1]):
            lines.extend(self.Map(paramName + ('_elem_%0*d' % (maxlen, i)), dummy, node._containedType, leafTypeDict, names))
        return lines

    def MapSetOf(self, reginfo, dstVHDL, node, leafTypeDict, names):
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

    if len(VHDL_Circuit.allCircuits)>1:
        panic("The ESA VHDL mapper can currently handle only one circuit.")  # pragma: no cover

    totalIn = 0
    for p in VHDL_Circuit.allCircuits[0]._sp._params:
        if isinstance(p, InParam) or isinstance(p, InOutParam):
            totalIn += RegistersAllocated(p._signal._asnNodename)
    AddToStr('numberOfInputRegisters', str(totalIn/4))

    for v in sorted(g_octStr):
        AddToStr('octStr', '  type octStr_%d is array (0 to %d) of std_logic_vector(7 downto 0);\n' %
                 (v, v-1))

    for c in VHDL_Circuit.allCircuits:
        circuitLines = []

        ioregisterLines = []

        readinputdataLines = []

        connectionsToSystemCLines = []

        counter = [int(c._offset+4)/4]
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
        AddToStr('circuits', '\n'.join(['            '+x for x in circuitLines]) + '\n')
        AddToStr('circuits', '            start_%s  : in  std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '            finish_%s : out std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '            rst_%s    : in std_logic;\n' % c._spCleanName)
        AddToStr('circuits', '            clk_%s    : in  std_logic\n' % c._spCleanName)
        AddToStr('circuits', '        );\n')
        AddToStr('circuits', '        end component;\n\n')

        AddToStr('entities', '        entity %s is\n' % c._spCleanName)
        AddToStr('entities', '        port (\n')
        AddToStr('entities', '\n'.join(['            '+x for x in circuitLines]) + '\n')
        AddToStr('entities', '            start_%s  : in  std_logic;\n' % c._spCleanName)
        AddToStr('entities', '            finish_%s : out std_logic;\n' % c._spCleanName)
        AddToStr('entities', '            rst_%s    : in std_logic;\n' % c._spCleanName)
        AddToStr('entities', '            clk_%s    : in  std_logic\n' % c._spCleanName)
        AddToStr('entities', '        );\n')
        AddToStr('entities', '        end %s;\n\n' % c._spCleanName)

        AddToStr('ioregisters', '\n'.join(['        '+x for x in ioregisterLines]) + '\n\n')

        AddToStr('startStopSignals', '''        signal %(pi)s_start : std_logic;
        signal %(pi)s_finish : std_logic;
''' % {'pi': c._spCleanName})

        AddToStr('reset', "                        %(pi)s_start <= '0';\n" % {'pi': c._spCleanName})

        AddToStr('readinputdata', '\n'.join([' '*24 +x for x in readinputdataLines])+'\n')
        AddToStr('writeoutputdata', '\n'.join([' '*24 +x for x in writeoutputdataLines])+'\n')

        AddToStr('connectionsToSystemC', '\n        Interface_%s : %s\n' % (c._spCleanName, c._spCleanName))
        AddToStr('connectionsToSystemC', '            port map (\n')
        AddToStr('connectionsToSystemC', ',\n'.join(['                '+x for x in connectionsToSystemCLines]) + ',\n')
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

            class State:
                pass
            state = State()
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

    #msg = ""
    #for c in VHDL_Circuit.allCircuits:
    #    msg += '    circuit_%s.vhd         \\\n' % c._spCleanName
    #    msg += '    circuit_%s_do_%s.vhd   \\\n' % (c._spCleanName, c._spCleanName)
    #makefile = open(vhdlBackend.dir + 'Makefile', 'w')
    #makefile.write(vhdlTemplate.makefile % {'circuit_autofiles':msg})
    #makefile.close()

    #systemcHeader.write('\n#endif\n')
    #systemcHeader.close()

    #msg = ""
    #for c in VHDL_Circuit.allCircuits:
    #    msg += 'vhdl work "circuit_%s.vhd"\n' % c._spCleanName
    #    msg += 'vhdl work "circuit_%s_do_%s.vhd"\n' % (c._spCleanName, c._spCleanName)
    #prj = open(vhdlBackend.dir + 'TASTE.prj', 'w')
    #prj.write(vhdlTemplate.prj % {'circuits':msg})
    #prj.close()
