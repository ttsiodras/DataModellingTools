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
This is the code generator for the QgenAda code mappers.
This backend is called by aadl2glueC, when a QgenAda subprogram
is identified in the input concurrency view.

This code generator supports both UPER/ACN and Native encodings,
and also supports UPER/ACN using both ASN1SCC and Nokalva.

QgenAda is a member of the synchronous "club" (SCADE, etc) ;
The subsystem developer (or rather, the APLC developer) is
building a model in QGenAda, generating code with QGenc
and the generated code is offered
in the form of a "function" that does all the work.
To that end, we create "glue" functions for input and output
parameters, which have Ada callable interfaces. The necessary
stubs (to allow calling from the VM side) are also generated.
'''

from commonPy.utility import panicWithCallStack
from commonPy.asnAST import AsnInt, AsnReal, AsnBool, AsnEnumerated, isSequenceVariable, sourceSequenceLimit
from commonPy.aadlAST import AadlPort, AadlParameter

from recursiveMapper import RecursiveMapper
from synchronousTool import SynchronousToolGlueGenerator

import c_B_mapper

isAsynchronous = False
qgenadaBackend = None
cBackend = None


def Version():
    print "Code generator: " + "$Id: qgenada_B_mapper.py 2390 2012-07-19 12:39:17Z ttsiodras $"


def IsElementMappedToPrimitive(node, names):
    contained = node._containedType
    while isinstance(contained, str):
        contained = names[contained]
    return isinstance(contained, AsnInt) or isinstance(contained, AsnReal) or isinstance(contained, AsnBool) or isinstance(contained, AsnEnumerated)


class FromQGenAdaToASN1SCC(RecursiveMapper):
    def MapInteger(self, srcQGenAda, destVar, _, __, ___):
        return ["%s := %s;\n" % (destVar, srcQGenAda)]

    def MapReal(self, srcQGenAda, destVar, _, __, ___):
        return ["%s := %s;\n" % (destVar, srcQGenAda)]

    def MapBoolean(self, srcQGenAda, destVar, _, __, ___):
        return ["%s := %s;\n" % (destVar, srcQGenAda)]

    def MapOctetString(self, srcQGenAda, destVar, node, _, __):
        lines = []
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        for i in xrange(0, node._range[-1]):
            lines.append("%s.Data (%d) := %s.Data (%d);\n" % (destVar, i+1, srcQGenAda, i))
        if isSequenceVariable(node):
            lines.append("%s.nCount := %s'Length;\n" % (destVar, srcQGenAda))
        # No nCount anymore
        #else:
        #    lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapEnumerated(self, srcQGenAda, destVar, _, __, ___):
        return ["%s := %s;\n" % (destVar, srcQGenAda)]

    def MapSequence(self, srcQGenAda, destVar, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s.%s" % (srcQGenAda, self.CleanName(child[0])),
                    destVar + "." + self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcQGenAda, destVar, node, leafTypeDict, names):
        return self.MapSequence(srcQGenAda, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcQGenAda, destVar, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choiceIdx == %d) then\n" % (self.maybeElse(childNo), srcQGenAda, childNo))
            lines.extend(['    ' + x for x in self.Map(
                         "%s.%s" % (srcQGenAda, self.CleanName(child[0])),
                         destVar + ".u." + self.CleanName(child[0]),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.kind = %s;\n" % (destVar, self.CleanName(child[2])))
            lines.append("end if;\n")
        return lines

    def MapSequenceOf(self, srcQGenAda, destVar, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []
        for i in xrange(0, node._range[-1]):
            lines.extend(self.Map(
                         isMappedToPrimitive and ("%s.Data (%d)" % (srcQGenAda, i)) or ("%s.element_%02d" % (srcQGenAda, i)),
                         destVar + ".Data (%d)" % (i+1),
                         node._containedType,
                         leafTypeDict,
                         names))
        if isSequenceVariable(node):
            lines.append("%s.nCount := %s'Length;\n" % (destVar, srcQGenAda))
        # No nCount anymore
        #else:
        #    lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapSetOf(self, srcQGenAda, destVar, node, leafTypeDict, names):
        return self.MapSequenceOf(srcQGenAda, destVar, node, leafTypeDict, names)  # pragma: nocover


class FromASN1SCCtoQGenAda(RecursiveMapper):
    def MapInteger(self, srcVar, dstQGenAda, _, __, ___):
        return ["%s := %s;\n" % (dstQGenAda, srcVar)]

    def MapReal(self, srcVar, dstQGenAda, _, __, ___):
        return ["%s := %s;\n" % (dstQGenAda, srcVar)]

    def MapBoolean(self, srcVar, dstQGenAda, _, __, ___):
        return ["%s := %s;\n" % (dstQGenAda, srcVar)]

    def MapOctetString(self, srcVar, dstQGenAda, node, _, __):
        if node._range == []:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover

        lines = []
        limit = sourceSequenceLimit(node, srcVar)
        for i in xrange(0, node._range[-1]):
            lines.append("if (%s>=%d) %s.Data (%d) := %s.Data (%d); else %s.Data (%d) := 0;\n" %
                         (limit, i, dstQGenAda, i, srcVar, i+1, dstQGenAda, i))
        if len(node._range)>1 and node._range[0]!=node._range[1]:
            lines.append("%s.length := %s;\n" % (dstQGenAda, limit))
        return lines

    def MapEnumerated(self, srcVar, dstQGenAda, node, __, ___):
        if None in [x[1] for x in node._members]:
            panicWithCallStack("an ENUMERATED must have integer values! (%s)" % node.Location())  # pragma: no cover
        return ["%s := %s;\n" % (dstQGenAda, srcVar)]

    def MapSequence(self, srcVar, dstQGenAda, node, leafTypeDict, names):
        lines = []
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]),
                    "%s.%s" % (dstQGenAda, self.CleanName(child[0])),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVar, dstQGenAda, node, leafTypeDict, names):
        return self.MapSequence(srcVar, dstQGenAda, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar, dstQGenAda, node, leafTypeDict, names):
        lines = []
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.kind == %s) then\n" % (self.maybeElse(childNo), srcVar, self.CleanName(child[2])))
            lines.extend(['    '+x for x in self.Map(
                         srcVar + ".u." + self.CleanName(child[0]),
                         "%s.%s" % (dstQGenAda, self.CleanName(child[0])),
                         child[1],
                         leafTypeDict,
                         names)])
            lines.append("    %s.choiceIdx := %d;\n" % (dstQGenAda, childNo))
            lines.append("end if;\n")
        return lines

    def MapSequenceOf(self, srcVar, dstQGenAda, node, leafTypeDict, names):
        if node._range == []:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []
        for i in xrange(0, node._range[-1]):
            lines.extend(self.Map(
                srcVar + ".Data (%d)" % (i+1),
                isMappedToPrimitive and ("%s.Data (%d)" % (dstQGenAda, i)) or ("%s.element_%02d" % (dstQGenAda, i)),
                node._containedType,
                leafTypeDict,
                names))
        if isSequenceVariable(node):
            lines.append("%s.length := %s.nCount;\n" % (dstQGenAda, srcVar))
        return lines

    def MapSetOf(self, srcVar, dstQGenAda, node, leafTypeDict, names):
        return self.MapSequenceOf(srcVar, dstQGenAda, node, leafTypeDict, names)  # pragma: nocover


class FromQGenAdaToOSS(RecursiveMapper):
    def MapInteger(self, srcQGenAda, destVar, _, __, ___):
        pass

    def MapReal(self, srcQGenAda, destVar, _, __, ___):
        pass

    def MapBoolean(self, srcQGenAda, destVar, _, __, ___):
        pass

    def MapOctetString(self, srcQGenAda, destVar, node, _, __):
        pass

    def MapEnumerated(self, srcQGenAda, destVar, _, __, ___):
        pass

    def MapSequence(self, srcQGenAda, destVar, node, leafTypeDict, names):
        pass

    def MapSet(self, srcQGenAda, destVar, node, leafTypeDict, names):
        pass

    def MapChoice(self, srcQGenAda, destVar, node, leafTypeDict, names):
        pass

    def MapSequenceOf(self, srcQGenAda, destVar, node, leafTypeDict, names):
        pass

    def MapSetOf(self, srcQGenAda, destVar, node, leafTypeDict, names):
        pass


class FromOSStoQGenAda(RecursiveMapper):
    def MapInteger(self, srcVar, dstQGenAda, _, __, ___):
        pass

    def MapReal(self, srcVar, dstQGenAda, _, __, ___):
        pass

    def MapBoolean(self, srcVar, dstQGenAda, _, __, ___):
        pass

    def MapOctetString(self, srcVar, dstQGenAda, node, _, __):
        pass

    def MapEnumerated(self, srcVar, dstQGenAda, node, __, ___):
        pass

    def MapSequence(self, srcVar, dstQGenAda, node, leafTypeDict, names):
        pass

    def MapSet(self, srcVar, dstQGenAda, node, leafTypeDict, names):
        pass

    def MapChoice(self, srcVar, dstQGenAda, node, leafTypeDict, names):
        pass

    def MapSequenceOf(self, srcVar, dstQGenAda, node, leafTypeDict, names):
        pass

    def MapSetOf(self, srcVar, dstQGenAda, node, leafTypeDict, names):
        pass


class QGenAdaGlueGenerator(SynchronousToolGlueGenerator):
    def Version(self):
        print "Code generator: " + "$Id: qgenada_B_mapper.py 2390 2012-07-19 12:39:17Z ttsiodras $"  # pragma: no cover

    def FromToolToASN1SCC(self):
        return FromQGenAdaToASN1SCC()

    def FromToolToOSS(self):
        return FromQGenAdaToOSS()

    def FromASN1SCCtoTool(self):
        return FromASN1SCCtoQGenAda()

    def FromOSStoTool(self):
        return FromOSStoQGenAda()

    def HeadersOnStartup(self, unused_modelingLanguage, unused_asnFile, subProgram, unused_subProgramImplementation, unused_outputDir, unused_maybeFVname):
        pass

    def SourceVar(self, unused_nodeTypename, unused_encoding, unused_node, unused_subProgram, unused_subProgramImplementation, param, unused_leafTypeDict, unused_names):
        if isinstance(param._sourceElement, AadlPort):
            srcQGenAda = "IN_QGen_%s" % (param._id)  # pragma: no cover
        elif isinstance(param._sourceElement, AadlParameter):
            srcQGenAda = "IN_QGen_%s" % (param._id)
        else:  # pragma: no cover
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return srcQGenAda

    def TargetVar(self, unused_nodeTypename, unused_encoding, unused_node, unused_subProgram, unused_subProgramImplementation, param, unused_leafTypeDict, unused_names):
        if isinstance(param._sourceElement, AadlPort):
            dstQGenAda = "OUT_QGen_%s" % (param._id)  # pragma: no cover
        elif isinstance(param._sourceElement, AadlParameter):
            dstQGenAda = "OUT_QGen_%s" % (param._id)
        else:  # pragma: no cover
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return dstQGenAda

    def InitializeBlock(self, unused_modelingLanguage, unused_asnFile, unused_sp, unused_subProgramImplementation, unused_maybeFVname):
        self.C_SourceFile.write("    static int initialized = 0;\n")
        self.C_SourceFile.write("    if (!initialized) {\n")
        self.C_SourceFile.write("        initialized = 1;\n")
        self.C_SourceFile.write("        %s_initialize(1);\n" % self.g_FVname)
        self.C_SourceFile.write("    }\n")

    def ExecuteBlock(self, unused_modelingLanguage, unused_asnFile, unused_sp, unused_subProgramImplementation, unused_maybeFVname):
        pass


def OnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS):
    global qgenadaBackend
    qgenadaBackend = QGenAdaGlueGenerator()
    qgenadaBackend.OnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS)
    global cBackend
    cBackend = c_B_mapper.C_GlueGenerator()
    cBackend.OnStartup("C", asnFile, outputDir, maybeFVname, useOSS)


def OnBasic(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgenadaBackend.OnBasic(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    cBackend.OnBasic(nodeTypename, node, leafTypeDict, names)


def OnSequence(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgenadaBackend.OnSequence(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    cBackend.OnSequence(nodeTypename, node, leafTypeDict, names)


def OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgenadaBackend.OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover
    cBackend.OnSet(nodeTypename, node, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgenadaBackend.OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    cBackend.OnEnumerated(nodeTypename, node, leafTypeDict, names)


def OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgenadaBackend.OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    cBackend.OnSequenceOf(nodeTypename, node, leafTypeDict, names)


def OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgenadaBackend.OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover
    cBackend.OnSetOf(nodeTypename, node, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names):
    qgenadaBackend.OnChoice(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)
    cBackend.OnChoice(nodeTypename, node, leafTypeDict, names)


def OnShutdown(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname):
    qgenadaBackend.OnShutdown(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname)
    cBackend.OnShutdown("C", asnFile, maybeFVname)

