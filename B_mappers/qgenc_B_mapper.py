#
# (C) Semantix Information Technologies.
#
# Copyright 2014-2015 IB Krates <info@krates.ee>
#       QGenc code generator integration
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
This is the code generator for the QGenC code mappers.
This backend is called by aadl2glueC, when a QGenC subprogram
is identified in the input concurrency view.

This code generator supports both UPER/ACN and Native encodings,
and also supports UPER/ACN using both ASN1SCC and Nokalva.

Matlab/QGenC is a member of the synchronous "club" (SCADE, etc) ;
The subsystem developer (or rather, the APLC developer) is
building a model in QGenC, and the generated code is offered
in the form of a "function" that does all the work.
To that end, we create "glue" functions for input and output
parameters, which have C callable interfaces. The necessary
stubs (to allow calling from the VM side) are also generated.
'''

from commonPy.utility import panicWithCallStack
from commonPy.asnAST import AsnInt, AsnReal, AsnBool, AsnEnumerated, isSequenceVariable, sourceSequenceLimit
from commonPy.aadlAST import AadlPort, AadlParameter

from .recursiveMapper import RecursiveMapper
from .synchronousTool import SynchronousToolGlueGenerator

isAsynchronous = False
qgencBackend = None


def Version():
    print("Code generator: " + "$Id: qgenc_B_mapper.py $")


def IsElementMappedToPrimitive(node, names):
    contained = node._containedType
    while isinstance(contained, str):
        contained = names[contained]
    return isinstance(contained, AsnInt) or isinstance(contained, AsnReal) or isinstance(contained, AsnBool) or isinstance(contained, AsnEnumerated)


class FromQGenCToASN1SCC(RecursiveMapper):
    def MapInteger(self, srcQGenC, destVar, _, __, ___):
        return ["%s = (asn1SccSint) %s;\n" % (destVar, srcQGenC)]

    def MapReal(self, srcQGenC, destVar, _, __, ___):
        return ["%s = (double) %s;\n" % (destVar, srcQGenC)]

    def MapBoolean(self, srcQGenC, destVar, _, __, ___):
        return ["%s = (asn1SccUint) %s;\n" % (destVar, srcQGenC)]

    def MapOctetString(self, srcQGenC, destVar, node, _, __):
        lines = []
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        for i in range(0, node._range[-1]):
            lines.append("%s.arr[%d] = %s.element_data[%d];\n" % (destVar, i, srcQGenC, i))
        if isSequenceVariable(node):
            lines.append("%s.nCount = %s.length;\n" % (destVar, srcQGenC))
        # No nCount anymore
        #else:
        #    lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapEnumerated(self, srcQGenC, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcQGenC)]

    def MapSequence(self, srcQGenC, destVar, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s" % (self.CleanName(child[0])),
                    self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcQGenC, destVar, node, leafTypeDict, names):
        return self.MapSequence(srcQGenC, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcQGenC, destVar, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choiceIdx == %d) {\n" % (self.maybeElse(childNo), srcQGenC, childNo))
            lines.extend(['    ' + x for x in self.Map(
                         "%s.%s" % (srcQGenC, self.CleanName(child[0])),
                         destVar + ".u." + self.CleanName(child[0]),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.kind = %s;\n" % (destVar, self.CleanName(child[2])))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcQGenC, destVar, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                         isMappedToPrimitive and ("%s.element_data[%d]" % (srcQGenC, i)) or ("%s.element_%02d" % (srcQGenC, i)),
                         destVar + ".arr[%d]" % i,
                         node._containedType,
                         leafTypeDict,
                         names))
        if isSequenceVariable(node):
            lines.append("%s.nCount = %s.length;\n" % (destVar, srcQGenC))
        # No nCount anymore
        #else:
        #    lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapSetOf(self, srcQGenC, destVar, node, leafTypeDict, names):
        return self.MapSequenceOf(srcQGenC, destVar, node, leafTypeDict, names)  # pragma: nocover


class FromASN1SCCtoQGenC(RecursiveMapper):
    def MapInteger(self, srcVar, dstQGenC, _, __, ___):
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapReal(self, srcVar, dstQGenC, _, __, ___):
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapBoolean(self, srcVar, dstQGenC, _, __, ___):
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapOctetString(self, srcVar, dstQGenC, node, _, __):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover

        lines = []
        limit = sourceSequenceLimit(node, srcVar)
        for i in range(0, node._range[-1]):
            lines.append("if (%s>=%d) %s.element_data[%d] = %s.arr[%d]; else %s.element_data[%d] = 0;\n" %
                         (limit, i+1, dstQGenC, i, srcVar, i, dstQGenC, i))
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            lines.append("%s.length = %s;\n" % (dstQGenC, limit))
        return lines

    def MapEnumerated(self, srcVar, dstQGenC, node, __, ___):
        if None in [x[1] for x in node._members]:
            panicWithCallStack("an ENUMERATED must have integer values! (%s)" % node.Location())  # pragma: no cover
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapSequence(self, srcVar, dstQGenC, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]),
                    "%s.%s" % (dstQGenC, self.CleanName(child[0])),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVar, dstQGenC, node, leafTypeDict, names):
        return self.MapSequence(srcVar, dstQGenC, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar, dstQGenC, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.kind == %s) {\n" % (self.maybeElse(childNo), srcVar, self.CleanName(child[2])))
            lines.extend(['    '+x for x in self.Map(
                         srcVar + ".u." + self.CleanName(child[0]),
                         "%s.%s" % (dstQGenC, self.CleanName(child[0])),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.choiceIdx = %d;\n" % (dstQGenC, childNo))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcVar, dstQGenC, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                srcVar + ".arr[%d]" % i,
                isMappedToPrimitive and ("%s.element_data[%d]" % (dstQGenC, i)) or ("%s.element_%02d" % (dstQGenC, i)),
                node._containedType,
                leafTypeDict,
                names))
        if isSequenceVariable(node):
            lines.append("%s.length = %s.nCount;\n" % (dstQGenC, srcVar))
        return lines

    def MapSetOf(self, srcVar, dstQGenC, node, leafTypeDict, names):
        return self.MapSequenceOf(srcVar, dstQGenC, node, leafTypeDict, names)  # pragma: nocover


class FromQGenCToOSS(RecursiveMapper):
    def MapInteger(self, srcQGenC, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcQGenC)]

    def MapReal(self, srcQGenC, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcQGenC)]

    def MapBoolean(self, srcQGenC, destVar, _, __, ___):
        return ["%s = (char) %s;\n" % (destVar, srcQGenC)]

    def MapOctetString(self, srcQGenC, destVar, node, _, __):
        lines = []
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        for i in range(0, node._range[-1]):
            lines.append("%s.value[%d] = %s.element_data[%d];\n" % (destVar, i, srcQGenC, i))
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            lines.append("%s.length = %s.length;\n" % (destVar, srcQGenC))
        else:
            lines.append("%s.length = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapEnumerated(self, srcQGenC, destVar, _, __, ___):
        return ["%s = %s;\n" % (destVar, srcQGenC)]

    def MapSequence(self, srcQGenC, destVar, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s.%s" % (srcQGenC, self.CleanName(child[0])),
                    destVar + "." + self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcQGenC, destVar, node, leafTypeDict, names):
        return self.MapSequence(srcQGenC, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcQGenC, destVar, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choiceIdx == %d) {\n" % (self.maybeElse(childNo), srcQGenC, childNo))
            lines.extend(['    '+x for x in self.Map(
                         "%s.%s" % (srcQGenC, self.CleanName(child[0])),
                         destVar + ".u." + self.CleanName(child[0]),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.choice = OSS_%s_chosen;\n" % (destVar, self.CleanName(child[0])))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcQGenC, destVar, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("(%s) needs a SIZE constraint or else we can't generate C code!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                         isMappedToPrimitive and ("%s.element_data[%d]" % (srcQGenC, i)) or ("%s.element_%02d" % (srcQGenC, i)),
                         destVar + ".value[%d]" % i,
                         node._containedType,
                         leafTypeDict,
                         names))
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            lines.append("%s.count = %s.length;\n" % (destVar, srcQGenC))
        else:
            lines.append("%s.count = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapSetOf(self, srcQGenC, destVar, node, leafTypeDict, names):
        return self.MapSequenceOf(srcQGenC, destVar, node, leafTypeDict, names)  # pragma: nocover


class FromOSStoQGenC(RecursiveMapper):
    def MapInteger(self, srcVar, dstQGenC, _, __, ___):
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapReal(self, srcVar, dstQGenC, _, __, ___):
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapBoolean(self, srcVar, dstQGenC, _, __, ___):
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapOctetString(self, srcVar, dstQGenC, node, _, __):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        lines = []
        for i in range(0, node._range[-1]):
            lines.append("if (%s.length >= %d) %s.element_data[%d] = %s.value[%d]; else %s.element_data[%d] = 0;\n" %
                         (srcVar, i+1, dstQGenC, i, srcVar, i, dstQGenC, i))
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            lines.append("%s.length = %s.length;" % (dstQGenC, srcVar))
        return lines

    def MapEnumerated(self, srcVar, dstQGenC, node, __, ___):
        if None in [x[1] for x in node._members]:
            panicWithCallStack("an ENUMERATED must have integer values! (%s)" % node.Location())  # pragma: no cover
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapSequence(self, srcVar, dstQGenC, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]),
                    "%s.%s" % (dstQGenC, self.CleanName(child[0])),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVar, dstQGenC, node, leafTypeDict, names):
        return self.MapSequence(srcVar, dstQGenC, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar, dstQGenC, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choice == OSS_%s_chosen) {\n" % (self.maybeElse(childNo), srcVar, self.CleanName(child[0])))
            lines.extend(['    '+x for x in self.Map(
                         srcVar + ".u." + self.CleanName(child[0]),
                         "%s.%s" % (dstQGenC, self.CleanName(child[0])),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.choiceIdx = %d;\n" % (dstQGenC, childNo))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcVar, dstQGenC, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("(%s) needs a SIZE constraint or else we can't generate C code!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                srcVar + ".value[%d]" % i,
                isMappedToPrimitive and ("%s.element_data[%d]" % (dstQGenC, i)) or ("%s.element_%02d" % (dstQGenC, i)),
                node._containedType,
                leafTypeDict,
                names))
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            lines.append("%s.length = %s.count;\n" % (dstQGenC, srcVar))
        return lines

    def MapSetOf(self, srcVar, dstQGenC, node, leafTypeDict, names):
        return self.MapSequenceOf(srcVar, dstQGenC, node, leafTypeDict, names)  # pragma: nocover


class QGenCGlueGenerator(SynchronousToolGlueGenerator):
    def Version(self):
        print("Code generator: " + "$Id: qgenc_B_mapper.py 2390 2014-11-27 12:39:17Z dtuulik $")  # pragma: no cover

    def FromToolToASN1SCC(self):
        return FromQGenCToASN1SCC()

    def FromToolToOSS(self):
        return FromQGenCToOSS()

    def FromASN1SCCtoTool(self):
        return FromASN1SCCtoQGenC()

    def FromOSStoTool(self):
        return FromOSStoQGenC()

    def HeadersOnStartup(self, unused_modelingLanguage, unused_asnFile, subProgram, unused_subProgramImplementation, unused_outputDir, unused_maybeFVname):
        if self.useOSS:
            self.C_SourceFile.write(
                "#include \"%s.oss.h\" // OSS generated\n" % self.asn_name)
            self.C_SourceFile.write("extern OssGlobal *g_world;\n\n")
        self.C_SourceFile.write("#include \"%s.h\" // Space certified compiler generated\n" % self.asn_name)
        self.C_SourceFile.write("#include \"%s.h\"\n\n" % self.CleanNameAsToolWants(subProgram._id).lower())
        self.C_SourceFile.write("#include \"%s_types.h\"\n\n" % self.CleanNameAsToolWants(subProgram._id).lower())
        self.C_SourceFile.write("static comp_Input cInput;\n\n")
        self.C_SourceFile.write("static comp_Output cOutput;\n\n")
        self.g_FVname = subProgram._id

    def SourceVar(self, unused_nodeTypename, unused_encoding, unused_node, unused_subProgram, unused_subProgramImplementation, param, unused_leafTypeDict, unused_names):
        if isinstance(param._sourceElement, AadlPort):
            srcQGenC = "cOutput.%s" % (param._id)  # pragma: no cover
        elif isinstance(param._sourceElement, AadlParameter):
            srcQGenC = "cOutput.%s" % (param._id)
        else:  # pragma: no cover
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return srcQGenC

    def TargetVar(self, unused_nodeTypename, unused_encoding, unused_node, unused_subProgram, unused_subProgramImplementation, param, unused_leafTypeDict, unused_names):
        if isinstance(param._sourceElement, AadlPort):
            dstQGenC = "cInput.%s" % (param._id)  # pragma: no cover
        elif isinstance(param._sourceElement, AadlParameter):
            dstQGenC = "cInput.%s" % (param._id)
        else:  # pragma: no cover
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return dstQGenC

    def InitializeBlock(self, unused_modelingLanguage, unused_asnFile, unused_sp, unused_subProgramImplementation, unused_maybeFVname):
        self.C_SourceFile.write("    static int initialized = 0;\n")
        self.C_SourceFile.write("    if (!initialized) {\n")
        self.C_SourceFile.write("        initialized = 1;\n")
        self.C_SourceFile.write("        %s_init();\n" % self.g_FVname)
        self.C_SourceFile.write("    }\n")

    def ExecuteBlock(self, unused_modelingLanguage, unused_asnFile, unused_sp, unused_subProgramImplementation, unused_maybeFVname):
        self.C_SourceFile.write("#ifndef rtmGetStopRequested\n")
        self.C_SourceFile.write("    %s_comp(&cInput, &cOutput);\n" % self.g_FVname)
        self.C_SourceFile.write("#else\n")
        self.C_SourceFile.write("    if (!rtmGetStopRequested(%s_M)) {\n" % self.g_FVname)
        self.C_SourceFile.write("        %s_step(&cInput, &cOutput);\n" % self.g_FVname)
        self.C_SourceFile.write("        if (rtmGetStopRequested(%s_M)) { %s_terminate(); }\n" %
                                (self.g_FVname, self.g_FVname))
        self.C_SourceFile.write("    }\n")
        self.C_SourceFile.write("#endif\n")


def OnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS):
    global qgencBackend
    qgencBackend = QGenCGlueGenerator()
    qgencBackend.OnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS)


def OnBasic(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgencBackend.OnBasic(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequence(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgencBackend.OnSequence(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgencBackend.OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgencBackend.OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgencBackend.OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgencBackend.OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgencBackend.OnChoice(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnShutdown(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname):
    qgencBackend.OnShutdown(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname)
