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
This is the code generator for the Simulink code mappers.
This backend is called by aadl2glueC, when a Simulink subprogram
is identified in the input concurrency view.

This code generator supports both UPER/ACN and Native encodings,
and also supports UPER/ACN using both ASN1SCC and Nokalva.

Matlab/Simulink is a member of the synchronous "club" (SCADE, etc) ;
The subsystem developer (or rather, the APLC developer) is
building a model in Simulink, and the generated code is offered
in the form of a "function" that does all the work.
To that end, we create "glue" functions for input and output
parameters, which have C callable interfaces. The necessary
stubs (to allow calling from the VM side) are also generated.
'''

from typing import List

from ..commonPy.utility import panicWithCallStack
from ..commonPy.asnAST import (
    AsnInt, AsnReal, AsnBool, AsnEnumerated, isSequenceVariable, sourceSequenceLimit,
    AsnOctetString, AsnSequenceOrSet, AsnSequenceOrSetOf, AsnChoice, AsnNode)
from ..commonPy.aadlAST import AadlPort, AadlParameter, ApLevelContainer, Param
from ..commonPy.asnParser import AST_Lookup, AST_Leaftypes

from ..commonPy.recursiveMapper import RecursiveMapper
from .synchronousTool import SynchronousToolGlueGenerator

isAsynchronous = False


def IsElementMappedToPrimitive(node: AsnSequenceOrSetOf, names: AST_Lookup) -> bool:
    contained = node._containedType
    while isinstance(contained, str):
        contained = names[contained]
    return isinstance(contained, (AsnInt, AsnReal, AsnBool, AsnEnumerated))


# pylint: disable=no-self-use
class FromSimulinkToASN1SCC(RecursiveMapper):
    def MapInteger(self, srcSimulink: str, destVar: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = (asn1SccSint) %s;\n" % (destVar, srcSimulink)]

    def MapReal(self, srcSimulink: str, destVar: str, _: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = (double) %s;\n" % (destVar, srcSimulink)]

    def MapBoolean(self, srcSimulink: str, destVar: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = (asn1SccUint) %s;\n" % (destVar, srcSimulink)]

    def MapOctetString(self, srcSimulink: str, destVar: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        for i in range(0, node._range[-1]):
            lines.append("%s.arr[%d] = %s.element_data[%d];\n" % (destVar, i, srcSimulink, i))
        if isSequenceVariable(node):
            lines.append("%s.nCount = %s.length;\n" % (destVar, srcSimulink))
        # No nCount anymore
        # else:
        #     lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapEnumerated(self, srcSimulink: str, destVar: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (destVar, srcSimulink)]

    def MapSequence(self, srcSimulink: str, destVar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s.%s" % (srcSimulink, self.CleanName(child[0])),
                    destVar + "." + self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcSimulink: str, destVar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcSimulink, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcSimulink: str, destVar: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choiceIdx == %d) {\n" % (self.maybeElse(childNo), srcSimulink, childNo))
            lines.extend(
                ['    ' + x
                 for x in self.Map(
                     "%s.%s" % (srcSimulink, self.CleanName(child[0])),
                     destVar + ".u." + self.CleanName(child[0]),
                     child[1],
                     leafTypeDict,
                     names)])
            lines.append("    %s.kind = %s;\n" % (destVar, self.CleanName(child[2])))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcSimulink: str, destVar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.extend(
                self.Map(("%s.element_data[%d]" % (srcSimulink, i)) if isMappedToPrimitive else ("%s.element_%02d" % (srcSimulink, i)),
                         destVar + ".arr[%d]" % i,
                         node._containedType,
                         leafTypeDict,
                         names))
        if isSequenceVariable(node):
            lines.append("%s.nCount = %s.length;\n" % (destVar, srcSimulink))
        # No nCount anymore
        # else:
        #     lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapSetOf(self, srcSimulink: str, destVar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcSimulink, destVar, node, leafTypeDict, names)  # pragma: nocover


# pylint: disable=no-self-use
class FromASN1SCCtoSimulink(RecursiveMapper):
    def MapInteger(self, srcVar: str, dstSimulink: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (dstSimulink, srcVar)]

    def MapReal(self, srcVar: str, dstSimulink: str, _: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (dstSimulink, srcVar)]

    def MapBoolean(self, srcVar: str, dstSimulink: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (dstSimulink, srcVar)]

    def MapOctetString(self, srcVar: str, dstSimulink: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover

        lines = []  # type: List[str]
        limit = sourceSequenceLimit(node, srcVar)
        lines.append("unsigned int i=0;\n")
        lines.append("for(i=0; i<%s; i++)\n        %s.element_data[i] = %s.arr[i];\n" % (limit, dstSimulink, srcVar))

        if len(node._range) > 1 and node._range[0] != node._range[1]:
            lines.append("%s.length = %s;\n" % (dstSimulink, limit))
        return lines

    def MapEnumerated(self, srcVar: str, dstSimulink: str, node: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if None in [x[1] for x in node._members]:
            panicWithCallStack("an ENUMERATED must have integer values! (%s)" % node.Location())  # pragma: no cover
        return ["%s = %s;\n" % (dstSimulink, srcVar)]

    def MapSequence(self, srcVar: str, dstSimulink: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]),
                    "%s.%s" % (dstSimulink, self.CleanName(child[0])),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVar: str, dstSimulink: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcVar, dstSimulink, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar: str, dstSimulink: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.kind == %s) {\n" % (self.maybeElse(childNo), srcVar, self.CleanName(child[2])))
            lines.extend(
                ['    ' + x
                 for x in self.Map(
                     srcVar + ".u." + self.CleanName(child[0]),
                     "%s.%s" % (dstSimulink, self.CleanName(child[0])),
                     child[1],
                     leafTypeDict,
                     names)])
            lines.append("    %s.choiceIdx = %d;\n" % (dstSimulink, childNo))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcVar: str, dstSimulink: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                srcVar + ".arr[%d]" % i,
                ("%s.element_data[%d]" % (dstSimulink, i)) if isMappedToPrimitive else ("%s.element_%02d" % (dstSimulink, i)),
                node._containedType,
                leafTypeDict,
                names))
        if isSequenceVariable(node):
            lines.append("%s.length = %s.nCount;\n" % (dstSimulink, srcVar))
        return lines

    def MapSetOf(self, srcVar: str, dstSimulink: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcVar, dstSimulink, node, leafTypeDict, names)  # pragma: nocover


# pylint: disable=no-self-use
class FromSimulinkToOSS(RecursiveMapper):
    def MapInteger(self, srcSimulink: str, destVar: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (destVar, srcSimulink)]

    def MapReal(self, srcSimulink: str, destVar: str, _: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (destVar, srcSimulink)]

    def MapBoolean(self, srcSimulink: str, destVar: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = (char) %s;\n" % (destVar, srcSimulink)]

    def MapOctetString(self, srcSimulink: str, destVar: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        for i in range(0, node._range[-1]):
            lines.append("%s.value[%d] = %s.element_data[%d];\n" % (destVar, i, srcSimulink, i))
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            lines.append("%s.length = %s.length;\n" % (destVar, srcSimulink))
        else:
            lines.append("%s.length = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapEnumerated(self, srcSimulink: str, destVar: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (destVar, srcSimulink)]

    def MapSequence(self, srcSimulink: str, destVar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s.%s" % (srcSimulink, self.CleanName(child[0])),
                    destVar + "." + self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcSimulink: str, destVar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcSimulink, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcSimulink: str, destVar: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choiceIdx == %d) {\n" % (self.maybeElse(childNo), srcSimulink, childNo))
            lines.extend(
                ['    ' + x
                 for x in self.Map(
                     "%s.%s" % (srcSimulink, self.CleanName(child[0])),
                     destVar + ".u." + self.CleanName(child[0]),
                     child[1],
                     leafTypeDict,
                     names)])
            lines.append("    %s.choice = OSS_%s_chosen;\n" % (destVar, self.CleanName(child[0])))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcSimulink: str, destVar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("(%s) needs a SIZE constraint or else we can't generate C code!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.extend(
                self.Map(("%s.element_data[%d]" % (srcSimulink, i)) if isMappedToPrimitive else ("%s.element_%02d" % (srcSimulink, i)),
                         destVar + ".value[%d]" % i,
                         node._containedType,
                         leafTypeDict,
                         names))
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            lines.append("%s.count = %s.length;\n" % (destVar, srcSimulink))
        else:
            lines.append("%s.count = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapSetOf(self, srcSimulink: str, destVar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcSimulink, destVar, node, leafTypeDict, names)  # pragma: nocover


# pylint: disable=no-self-use
class FromOSStoSimulink(RecursiveMapper):
    def MapInteger(self, srcVar: str, dstSimulink: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (dstSimulink, srcVar)]

    def MapReal(self, srcVar: str, dstSimulink: str, _: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (dstSimulink, srcVar)]

    def MapBoolean(self, srcVar: str, dstSimulink: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (dstSimulink, srcVar)]

    def MapOctetString(self, srcVar: str, dstSimulink: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.append("if (%s.length >= %d) %s.element_data[%d] = %s.value[%d]; else %s.element_data[%d] = 0;\n" %
                         (srcVar, i + 1, dstSimulink, i, srcVar, i, dstSimulink, i))
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            lines.append("%s.length = %s.length;" % (dstSimulink, srcVar))
        return lines

    def MapEnumerated(self, srcVar: str, dstSimulink: str, node: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if None in [x[1] for x in node._members]:
            panicWithCallStack("an ENUMERATED must have integer values! (%s)" % node.Location())  # pragma: no cover
        return ["%s = %s;\n" % (dstSimulink, srcVar)]

    def MapSequence(self, srcVar: str, dstSimulink: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]),
                    "%s.%s" % (dstSimulink, self.CleanName(child[0])),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVar: str, dstSimulink: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcVar, dstSimulink, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar: str, dstSimulink: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choice == OSS_%s_chosen) {\n" % (self.maybeElse(childNo), srcVar, self.CleanName(child[0])))
            lines.extend(
                ['    ' + x
                 for x in self.Map(
                     srcVar + ".u." + self.CleanName(child[0]),
                     "%s.%s" % (dstSimulink, self.CleanName(child[0])),
                     child[1],
                     leafTypeDict,
                     names)])
            lines.append("    %s.choiceIdx = %d;\n" % (dstSimulink, childNo))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcVar: str, dstSimulink: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("(%s) needs a SIZE constraint or else we can't generate C code!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                srcVar + ".value[%d]" % i,
                ("%s.element_data[%d]" % (dstSimulink, i)) if isMappedToPrimitive else ("%s.element_%02d" % (dstSimulink, i)),
                node._containedType,
                leafTypeDict,
                names))
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            lines.append("%s.length = %s.count;\n" % (dstSimulink, srcVar))
        return lines

    def MapSetOf(self, srcVar: str, dstSimulink: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcVar, dstSimulink, node, leafTypeDict, names)  # pragma: nocover


class SimulinkGlueGenerator(SynchronousToolGlueGenerator):
    g_FVname = None  # type: str

    def Version(self) -> None:
        print("Code generator: " + "$Id: simulink_B_mapper.py 2390 2012-07-19 12:39:17Z ttsiodras $")  # pragma: no cover

    def FromToolToASN1SCC(self) -> RecursiveMapper:
        return FromSimulinkToASN1SCC()

    def FromToolToOSS(self) -> RecursiveMapper:
        return FromSimulinkToOSS()

    def FromASN1SCCtoTool(self) -> RecursiveMapper:
        return FromASN1SCCtoSimulink()

    def FromOSStoTool(self) -> RecursiveMapper:
        return FromOSStoSimulink()

    def HeadersOnStartup(self, unused_modelingLanguage: str, unused_asnFile: str, subProgram: ApLevelContainer, unused_subProgramImplementation: str, unused_outputDir: str, unused_maybeFVname: str) -> None:
        if self.useOSS:
            self.C_SourceFile.write(
                "#include \"%s.oss.h\" // OSS generated\n" % self.asn_name)
            self.C_SourceFile.write("extern OssGlobal *g_world;\n\n")
        self.C_SourceFile.write("#include \"%s.h\" // Space certified compiler generated\n" % self.asn_name)
        self.C_SourceFile.write("#include \"%s.h\"\n\n" % self.CleanNameAsToolWants(subProgram._id))
        self.C_SourceFile.write("#include \"%s_types.h\"\n\n" % self.CleanNameAsToolWants(subProgram._id))
        self.g_FVname = subProgram._id

    def SourceVar(self,
                  unused_nodeTypename: str,
                  unused_encoding: str,
                  unused_node: AsnNode,
                  unused_subProgram: ApLevelContainer,
                  unused_subProgramImplementation: str,
                  param: Param,
                  unused_leafTypeDict: AST_Leaftypes,
                  unused_names: AST_Lookup) -> str:
        if isinstance(param._sourceElement, AadlPort):
            srcSimulink = "%s_Y.%s" % (self.g_FVname, param._id)  # pragma: no cover
        elif isinstance(param._sourceElement, AadlParameter):
            srcSimulink = "%s_Y.%s" % (self.g_FVname, param._id)
        else:  # pragma: no cover
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return srcSimulink

    def TargetVar(self,
                  unused_nodeTypename: str,
                  unused_encoding: str,
                  unused_node: AsnNode,
                  unused_subProgram: ApLevelContainer,
                  unused_subProgramImplementation: str,
                  param: Param,
                  unused_leafTypeDict: AST_Leaftypes,
                  unused_names: AST_Lookup) -> str:
        if isinstance(param._sourceElement, AadlPort):
            dstSimulink = "%s_U.%s" % (self.g_FVname, param._id)  # pragma: no cover
        elif isinstance(param._sourceElement, AadlParameter):
            dstSimulink = "%s_U.%s" % (self.g_FVname, param._id)
        else:  # pragma: no cover
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return dstSimulink

    def InitializeBlock(self, unused_modelingLanguage: str, unused_asnFile: str, sp: ApLevelContainer, unused_subProgramImplementation: str, maybeFVname: str) -> None:
        self.C_SourceFile.write("    static int initialized = 0;\n")
        self.C_SourceFile.write("    if (!initialized) {\n")
        self.C_SourceFile.write("        initialized = 1;\n")
        self.C_SourceFile.write("        %s_initialize();\n" % self.g_FVname)
        # If there are HW(FPGA) configurations defined, initialize also the HW side (the device driver: <self.g_FVname>_Simulink.vhdl.c).
        if sp._fpgaConfigurations != '':
            self.C_SourceFile.write("        init_%s_Fpga();\n" % maybeFVname)  # pragma: no cover
        self.C_SourceFile.write("    }\n")

    def ExecuteBlock(self, unused_modelingLanguage: str, unused_asnFile: str, unused_sp: ApLevelContainer, unused_subProgramImplementation: str, unused_maybeFVname: str) -> None:
        self.C_SourceFile.write("#ifndef rtmGetStopRequested\n")
        self.C_SourceFile.write("    %s_step();\n" % self.g_FVname)
        self.C_SourceFile.write("#else\n")
        self.C_SourceFile.write("    if (!rtmGetStopRequested(%s_M)) {\n" % self.g_FVname)
        self.C_SourceFile.write("        %s_step();\n" % self.g_FVname)
        self.C_SourceFile.write("        if (rtmGetStopRequested(%s_M)) { %s_terminate(); }\n" %
                                (self.g_FVname, self.g_FVname))
        self.C_SourceFile.write("    }\n")
        self.C_SourceFile.write("#endif\n")


simulinkBackend: SimulinkGlueGenerator


def OnStartup(modelingLanguage: str, asnFile: str, subProgram: ApLevelContainer, subProgramImplementation: str, outputDir: str, maybeFVname: str, useOSS: bool) -> None:
    global simulinkBackend
    simulinkBackend = SimulinkGlueGenerator()
    simulinkBackend.OnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS)


def OnBasic(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    simulinkBackend.OnBasic(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequence(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    simulinkBackend.OnSequence(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSet(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    simulinkBackend.OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    simulinkBackend.OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequenceOf(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    simulinkBackend.OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSetOf(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    simulinkBackend.OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    simulinkBackend.OnChoice(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnShutdown(modelingLanguage: str, asnFile: str, sp: ApLevelContainer, subProgramImplementation: str, maybeFVname: str) -> None:
    simulinkBackend.OnShutdown(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname)
