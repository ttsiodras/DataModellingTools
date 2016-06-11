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
This is the code generator for the SCADE6 code mappers.
This backend is called by aadl2glueC, when a SCADE5 or SCADE6
subprogram is identified in the input concurrency view.

This code generator supports both UPER/ACN and Native encodings,
and also supports UPER/ACN using both ASN1SCC and Nokalva.

SCADE is a member of the synchronous "club" (Simulink, etc) ;
The subsystem developer (or rather, the APLC developer) is
building a model in SCADE, and the generated code is offered
in the form of a "function" that does all the work.
To that end, we create "glue" functions for input and output
parameters, which have C callable interfaces. The necessary
stubs (to allow calling from the VM side) are also generated.
'''

from commonPy.utility import panic, panicWithCallStack
from commonPy.asnAST import isSequenceVariable, sourceSequenceLimit
from commonPy.aadlAST import AadlPort, AadlParameter

from .recursiveMapper import RecursiveMapper
from .synchronousTool import SynchronousToolGlueGenerator

isAsynchronous = False
scadeBackend = None


def Version():
    print("Code generator: " + \
        "$Id: scade6_B_mapper.py 2390 2012-07-19 12:39:17Z ttsiodras $")


class FromSCADEtoASN1SCC(RecursiveMapper):
    def MapInteger(self, srcScadeMacro, destVar, _, __, ___):
        return ["%s = (asn1SccSint) %s;\n" % (destVar, srcScadeMacro)]

    def MapReal(self, srcScadeMacro, destVar, _, __, ___):
        return ["%s = (double) %s;\n" % (destVar, srcScadeMacro)]

    def MapBoolean(self, srcScadeMacro, destVar, _, __, ___):
        return ["%s = (int)%s;\n" % (destVar, srcScadeMacro)]

    def MapOctetString(self, srcScadeMacro, destVar, node, _, __):
        lines = []
        lines.append("{\n")
        if node._range == []:
            panicWithCallStack(
                "OCTET STRING (in %s) must have a SIZE constraint "  # pragma: no cover
                "inside ASN.1,\nor else SCADE can't generate C code!" % node.Location())  # pragma: no cover
        for i in range(0, node._range[-1]):
            lines.append("    %s.arr[%d] = %s[%d];\n" % (destVar, i, srcScadeMacro, i))
        if isSequenceVariable(node):
            lines.append("    %s.nCount = %d;\n" % (destVar, node._range[-1]))
        lines.append("}\n")
        return lines

    def MapEnumerated(self, srcScadeMacro, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcScadeMacro)]

    def MapSequence(self, srcScadeMacro, destVar, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s.%s" % (srcScadeMacro, self.CleanName(child[0])),
                    destVar + "." + self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcScadeMacro, destVar, node, leafTypeDict, names):
        return self.MapSequence(srcScadeMacro, destVar, node, leafTypeDict, names)  # pragma: nocover  # pragma: nocover

    def MapChoice(self, srcScadeMacro, destVar, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choiceIdx == %d) {\n" %
                         (self.maybeElse(childNo), srcScadeMacro, childNo))
            lines.extend(['    '+x for x in self.Map(
                         "%s.%s" % (srcScadeMacro, self.CleanName(child[0])),
                         destVar + ".u." + self.CleanName(child[0]),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.kind = %s;\n" % (destVar, self.CleanName(child[2])))
            lines.append("}")
        return lines

    def MapSequenceOf(self, srcScadeMacro, destVar, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack(
                "A SIZE constraint is required, or else SCADE can't generate C code (%s)!\n" %   # pragma: no cover
                node.Location())  # pragma: no cover
        lines = []
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                         "%s[%d]" % (srcScadeMacro, i),
                         "%s.arr[%d]" % (destVar, i),
                         node._containedType,
                         leafTypeDict,
                         names))
        if isSequenceVariable(node):
            lines.append("%s.nCount = %d;\n" % (destVar, node._range[-1]))
        return lines

    def MapSetOf(self, srcScadeMacro, destVar, node, leafTypeDict, names):
        return self.MapSequenceOf(srcScadeMacro, destVar, node, leafTypeDict, names)  # pragma: nocover


class FromASN1SCCtoSCADE(RecursiveMapper):
    def __init__(self):
        self._seqIndex = 1

    def MapInteger(self, srcVar, dstScadeMacro, _, __, ___):
        return ["%s = %s;\n" % (dstScadeMacro, srcVar)]

    def MapReal(self, srcVar, dstScadeMacro, _, __, ___):
        return ["%s = %s;\n" % (dstScadeMacro, srcVar)]

    def MapBoolean(self, srcVar, dstScadeMacro, _, __, ___):
        return ["%s = (%s)?1:0;\n" % (dstScadeMacro, srcVar)]

    def MapOctetString(self, srcVar, dstScadeMacro, node, _, __):
        if node._range == []:
            panicWithCallStack(
                "OCTET STRING (in %s) must have a SIZE constraint "  # pragma: no cover
                "inside ASN.1,\nor else SCADE can't generate C code!" % node.Location())  # pragma: no cover
        lines = []
        limit = sourceSequenceLimit(node, srcVar)
        #for i in xrange(0, node._range[-1]):
        #       lines.append("%s[%d] = %s->buf[%d];\n" % (dstScadeMacro, i, srcVar, i))
        lines.append("{\n")
        lines.append("    int i;\n")
        lines.append("    for(i=0; i<%s; i++) %s[i] = %s.arr[i];\n" % (limit, dstScadeMacro, srcVar))
        lines.append("    while(i<%d) { %s[i]=0; i++; }\n" % (node._range[-1], dstScadeMacro))
        lines.append("}\n")
        return lines

    def MapEnumerated(self, srcVar, dstScadeMacro, _, __, ___):
        return ["%s = %s;\n" % (dstScadeMacro, srcVar)]

    def MapSequence(self, srcVar, dstScadeMacro, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]),
                    "%s.%s" % (dstScadeMacro, self.CleanName(child[0])),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVar, dstScadeMacro, node, leafTypeDict, names):
        return self.MapSequence(srcVar, dstScadeMacro, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar, dstScadeMacro, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.kind == %s) {\n" %
                         (self.maybeElse(childNo), srcVar, self.CleanName(child[2])))
            lines.extend(['    '+x for x in self.Map(
                         srcVar + ".u." + self.CleanName(child[0]),
                         "%s.%s" % (dstScadeMacro, self.CleanName(child[0])),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.choiceIdx = %d;\n" % (dstScadeMacro, childNo))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcVar, dstScadeMacro, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack(
                "A SIZE constraint is required or else SCADE can't generate C code (%s)!\n" %   # pragma: no cover
                node.Location())  # pragma: no cover
        lines = []
        seqIndex = self._seqIndex
        self._seqIndex += 1
        lines.append("{\n")
        lines.append("    int i%d;\n" % seqIndex)
        # Bugfix for Astrium/Nicolas Gillet: always use the array max conf
        # lines.append("    for(i%d=0; i%d<%s.nCount; i%d++) {\n" % (seqIndex, seqIndex, srcVar, seqIndex))
        lines.append("    for(i%d=0; i%d<%d; i%d++) {\n" % (seqIndex, seqIndex, node._range[-1], seqIndex))
        lines.extend(["        "+x for x in self.Map(
                     srcVar + ".arr[i%d]" % seqIndex,
                     "%s[i%d]" % (dstScadeMacro, seqIndex),
                     node._containedType,
                     leafTypeDict,
                     names)])
        lines.append("    }\n")
        # How to reset the remaining elements in SCADE? No idea...
        lines.append("}\n")
        return lines

    def MapSetOf(self, srcVar, dstScadeMacro, node, leafTypeDict, names):
        return self.MapSequenceOf(srcVar, dstScadeMacro, node, leafTypeDict, names)  # pragma: nocover


class FromSCADEtoOSS(RecursiveMapper):
    def MapInteger(self, srcScadeMacro, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcScadeMacro)]

    def MapReal(self, srcScadeMacro, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcScadeMacro)]

    def MapBoolean(self, srcScadeMacro, destVar, _, __, ___):
        return ["%s = (char)%s;\n" % (destVar, srcScadeMacro)]

    def MapOctetString(self, srcScadeMacro, destVar, node, _, __):
        lines = []
        lines.append("{\n")
        if node._range == []:
            panicWithCallStack(
                "OCTET STRING (in %s) must have a SIZE constraint "  # pragma: no cover
                "inside ASN.1,\nor else SCADE can't generate C code!" % node.Location())  # pragma: no cover
        for i in range(0, node._range[-1]):
            lines.append("    %s.value[%d] = %s[%d];\n" % (destVar, i, srcScadeMacro, i))
        lines.append("    %s.length = %d;\n" % (destVar, node._range[-1]))
        lines.append("}\n")
        return lines

    def MapEnumerated(self, srcScadeMacro, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcScadeMacro)]

    def MapSequence(self, srcScadeMacro, destVar, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s.%s" % (srcScadeMacro, self.CleanName(child[0])),
                    destVar + "." + self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcScadeMacro, destVar, node, leafTypeDict, names):
        return self.MapSequence(srcScadeMacro, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcScadeMacro, destVar, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choiceIdx == %d) {\n" %
                         (self.maybeElse(childNo), srcScadeMacro, childNo))
            lines.extend(['    '+x for x in self.Map(
                         "%s.%s" % (srcScadeMacro, self.CleanName(child[0])),
                         destVar + ".u." + self.CleanName(child[0]),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.choice = OSS_%s_chosen;\n" % (destVar, self.CleanName(child[0])))
            lines.append("}")
        return lines

    def MapSequenceOf(self, srcScadeMacro, destVar, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack(
                "A SIZE constraint is required, or else SCADE can't generate C code (%s)!\n" %   # pragma: no cover
                node.Location())  # pragma: no cover
        lines = []
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                         "%s[%d]" % (srcScadeMacro, i),
                         "%s.value[%d]" % (destVar, i),
                         node._containedType,
                         leafTypeDict,
                         names))
        lines.append("%s.count = %d;\n" % (destVar, node._range[-1]))
        return lines

    def MapSetOf(self, srcScadeMacro, destVar, node, leafTypeDict, names):
        return self.MapSequenceOf(srcScadeMacro, destVar, node, leafTypeDict, names)  # pragma: nocover


class FromOSStoSCADE(RecursiveMapper):
    def __init__(self):
        self._seqIndex = 1

    def MapInteger(self, srcVar, dstScadeMacro, _, __, ___):
        return ["%s = %s;\n" % (dstScadeMacro, srcVar)]

    def MapReal(self, srcVar, dstScadeMacro, _, __, ___):
        return ["%s = %s;\n" % (dstScadeMacro, srcVar)]

    def MapBoolean(self, srcVar, dstScadeMacro, _, __, ___):
        return ["%s = (%s)?1:0;\n" % (dstScadeMacro, srcVar)]

    def MapOctetString(self, srcVar, dstScadeMacro, node, _, __):
        if node._range == []:
            panicWithCallStack(
                "OCTET STRING (in %s) must have a SIZE constraint "  # pragma: no cover
                "inside ASN.1,\nor else SCADE can't generate C code!" % node.Location())  # pragma: no cover
        lines = []
        lines.append("{\n")
        lines.append("    int i;\n")
        lines.append("    for(i=0; i<%s.length; i++) %s[i] = %s.value[i];\n" % (srcVar, dstScadeMacro, srcVar))
        lines.append("    while(i<%d) { %s[i]=0; i++; }\n" % (node._range[-1], dstScadeMacro))
        lines.append("}\n")
        return lines

    def MapEnumerated(self, srcVar, dstScadeMacro, _, __, ___):
        return ["%s = %s;\n" % (dstScadeMacro, srcVar)]

    def MapSequence(self, srcVar, dstScadeMacro, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]),
                    "%s.%s" % (dstScadeMacro, self.CleanName(child[0])),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVar, dstScadeMacro, node, leafTypeDict, names):
        return self.MapSequence(srcVar, dstScadeMacro, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar, dstScadeMacro, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choice == OSS_%s_chosen) {\n" %
                         (self.maybeElse(childNo), srcVar, self.CleanName(child[0])))
            lines.extend(['    '+x for x in self.Map(
                         srcVar + ".u." + self.CleanName(child[0]),
                         "%s.%s" % (dstScadeMacro, self.CleanName(child[0])),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.choiceIdx = %d;\n" % (dstScadeMacro, childNo))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcVar, dstScadeMacro, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack(
                "A SIZE constraint is required or else SCADE can't generate C code (%s)!\n" %   # pragma: no cover
                node.Location())  # pragma: no cover
        lines = []
        seqIndex = self._seqIndex
        self._seqIndex += 1
        lines.append("{\n")
        lines.append("    int i%d;\n" % seqIndex)
        lines.append("    for(i%d=0; i%d<%s.count; i%d++) {\n" % (seqIndex, seqIndex, srcVar, seqIndex))
        #for i in xrange(0, node._range[-1]):
        lines.extend(["        "+x for x in self.Map(
                     srcVar + ".value[i%d]" % seqIndex,
                     "%s[i%d]" % (dstScadeMacro, seqIndex),
                     node._containedType,
                     leafTypeDict,
                     names)])
        lines.append("    }\n")
        # How to reset the remaining elements in SCADE? No idea...
        lines.append("}\n")
        return lines

    def MapSetOf(self, srcVar, dstScadeMacro, node, leafTypeDict, names):
        return self.MapSequenceOf(srcVar, dstScadeMacro, node, leafTypeDict, names)  # pragma: nocover


class ScadeGlueGenerator(SynchronousToolGlueGenerator):
    def Version(self):
        print("Code generator: " + "$Id: scade6_B_mapper.py 2390 2012-07-19 12:39:17Z ttsiodras $")  # pragma: no cover

    def FromToolToASN1SCC(self):
        return FromSCADEtoASN1SCC()

    def FromToolToOSS(self):
        return FromSCADEtoOSS()

    def FromASN1SCCtoTool(self):
        return FromASN1SCCtoSCADE()

    def FromOSStoTool(self):
        return FromOSStoSCADE()

    def HeadersOnStartup(self, unused_modelingLanguage, unused_asnFile, subProgram, unused_subProgramImplementation, unused_outputDir, maybeFVname):
        if self.useOSS:
            self.C_SourceFile.write(
                "#include \"%s.oss.h\" // OSS generated\n" % self.asn_name)
            self.C_SourceFile.write("extern OssGlobal *g_world;\n\n")
        else:
            self.C_SourceFile.write(
                "#include \"%s.h\" // Space certified compiler generated\n\n" % self.asn_name)
        self.C_SourceFile.write("#include \"%s\"\n\n" % (self.CleanNameAsToolWants(maybeFVname) + ".h"))
        # Declare and define staging inputs and outputs
        #self.C_SourceFile.write("AADL2SCADE_%s_%s_DECLARE(var_%s_%s);\n\n" % \
        #    (subProgram._id, subProgramImplementation, subProgram._id, subProgramImplementation))
        #self.C_SourceFile.write("AADL2SCADE_%s_%s_DEFINE(var_%s_%s);\n\n" % \
        #    (subProgram._id, subProgramImplementation, subProgram._id, subProgramImplementation))
        for param in subProgram._params:
            self.C_SourceFile.write("%s %s;\n" % (self.CleanNameAsToolWants(param._signal._asnNodename), param._id))
        self.C_SourceFile.write("\n")

    def SourceVar(self, unused_nodeTypename, unused_encoding, unused_node, subProgram, subProgramImplementation, param, unused_leafTypeDict, unused_names):
        if isinstance(param._sourceElement, AadlPort):  # Both AadlPort and AadlEventDataPort
            panic("Unsupported old construct")  # pragma: no cover
            #srcScadeMacro = "AADL2SCADE_OUTPUT_DATA_PORT(var_%s, %s, %s)" % \
            #   (self.CleanNameAsToolWants(subProgram._id + "_" + subProgramImplementation),
            #    self.CleanNameAsToolWants(subProgram._id + "_" + subProgramImplementation),
            #    self.CleanNameAsToolWants(param._id).upper())
        elif isinstance(param._sourceElement, AadlParameter):
            #srcScadeMacro = "AADL2SCADE_OUTPUT_PARAMETER(var_%s, %s, %s)" % \
            #   (self.CleanNameAsToolWants(subProgram._id + "_" + subProgramImplementation),
            #    self.CleanNameAsToolWants(subProgram._id + "_" + subProgramImplementation),
            #    self.CleanNameAsToolWants(param._id).upper())
            srcScadeMacro = self.CleanNameAsToolWants(param._id)
        else:  # pragma: no cover
            panic(str(self.__class__) + ": %s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return srcScadeMacro

    def TargetVar(self, unused_nodeTypename, unused_encoding, unused_node, subProgram, subProgramImplementation, param, unused_leafTypeDict, unused_names):
        if isinstance(param._sourceElement, AadlPort):  # Both AadlPort and AadlEventDataPort
            panic("Unsupported old construct")  # pragma: no cover
            #dstScadeMacro = "AADL2SCADE_INPUT_DATA_PORT(var_%s, %s, %s)" % \
            #   (self.CleanNameAsToolWants(subProgram._id + "_" + subProgramImplementation),
            #    self.CleanNameAsToolWants(subProgram._id + "_" + subProgramImplementation),
            #    self.CleanNameAsToolWants(param._id).upper())
        elif isinstance(param._sourceElement, AadlParameter):
            #dstScadeMacro = "AADL2SCADE_INPUT_PARAMETER(var_%s, %s, %s)" % \
            #   (self.CleanNameAsToolWants(subProgram._id + "_" + subProgramImplementation),
            #    self.CleanNameAsToolWants(subProgram._id + "_" + subProgramImplementation),
            #    self.CleanNameAsToolWants(param._id).upper())
            dstScadeMacro = self.CleanNameAsToolWants(param._id)
        else:  # pragma: no cover
            panic(str(self.__class__) + ": %s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return dstScadeMacro

    def InitializeBlock(self, unused_modelingLanguage, unused_asnFile, sp, unused_subProgramImplementation, unused_maybeFVname):
        self.C_SourceFile.write("    %s_reset();\n" % (self.CleanNameAsToolWants(sp._id)))

    def ExecuteBlock(self, unused_modelingLanguage, unused_asnFile, sp, unused_subProgramImplementation, unused_maybeFVname):
        self.C_SourceFile.write("    %s();\n" % (self.CleanNameAsToolWants(sp._id)))


def OnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS):
    global scadeBackend
    scadeBackend = ScadeGlueGenerator()
    scadeBackend.OnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS)


def OnBasic(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    scadeBackend.OnBasic(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequence(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    scadeBackend.OnSequence(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    scadeBackend.OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    scadeBackend.OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    scadeBackend.OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    scadeBackend.OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    scadeBackend.OnChoice(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnShutdown(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname):
    scadeBackend.OnShutdown(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname)
