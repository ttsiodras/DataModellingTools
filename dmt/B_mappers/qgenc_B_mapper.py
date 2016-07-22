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

from typing import List
from ..commonPy.utility import panicWithCallStack
from ..commonPy.asnAST import (
    sourceSequenceLimit, isSequenceVariable, AsnInt, AsnReal, AsnEnumerated,
    AsnBool, AsnSequenceOrSet, AsnSequenceOrSetOf, AsnChoice, AsnOctetString,
    AsnNode)
from ..commonPy.asnParser import AST_Lookup, AST_Leaftypes
from ..commonPy.aadlAST import AadlPort, AadlParameter, ApLevelContainer, Param
from ..commonPy.recursiveMapper import RecursiveMapper
from .synchronousTool import SynchronousToolGlueGenerator

isAsynchronous = False
qgencBackend = None


def IsElementMappedToPrimitive(node: AsnSequenceOrSetOf, names: AST_Lookup) -> bool:
    contained = node._containedType
    while isinstance(contained, str):
        contained = names[contained]
    return isinstance(contained, AsnInt) or isinstance(contained, AsnReal) or isinstance(contained, AsnBool) or isinstance(contained, AsnEnumerated)


# pylint: disable=no-self-use
class FromQGenCToASN1SCC(RecursiveMapper):
    def MapInteger(self, srcQGenC: str, destVar: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = (asn1SccSint) %s;\n" % (destVar, srcQGenC)]

    def MapReal(self, srcQGenC: str, destVar: str, _: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = (double) %s;\n" % (destVar, srcQGenC)]

    def MapBoolean(self, srcQGenC: str, destVar: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = (asn1SccUint) %s;\n" % (destVar, srcQGenC)]

    def MapOctetString(self, srcQGenC: str, destVar: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        for i in range(0, node._range[-1]):
            lines.append("%s.arr[%d] = %s.element_data[%d];\n" % (destVar, i, srcQGenC, i))
        if isSequenceVariable(node):
            lines.append("%s.nCount = %s.length;\n" % (destVar, srcQGenC))
        # No nCount anymore
        # else:
        #     lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapEnumerated(self, srcQGenC: str, destVar: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (destVar, srcQGenC)]

    def MapSequence(self, unused_srcQGenC: str, unused_destVar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s" % (self.CleanName(child[0])),
                    self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcQGenC: str, destVar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcQGenC, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcQGenC: str, destVar: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choiceIdx == %d) {\n" % (self.maybeElse(childNo), srcQGenC, childNo))
            lines.extend(
                ['    ' + x
                 for x in self.Map(
                     "%s.%s" % (srcQGenC, self.CleanName(child[0])),
                     destVar + ".u." + self.CleanName(child[0]),
                     child[1],
                     leafTypeDict,
                     names)])
            lines.append("    %s.kind = %s;\n" % (destVar, self.CleanName(child[2])))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcQGenC: str, destVar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.extend(
                self.Map(("%s.element_data[%d]" % (srcQGenC, i)) if isMappedToPrimitive else ("%s.element_%02d" % (srcQGenC, i)),
                         destVar + ".arr[%d]" % i,
                         node._containedType,
                         leafTypeDict,
                         names))
        if isSequenceVariable(node):
            lines.append("%s.nCount = %s.length;\n" % (destVar, srcQGenC))
        # No nCount anymore
        # else:
        #     lines.append("%s.nCount = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapSetOf(self, srcQGenC: str, destVar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcQGenC, destVar, node, leafTypeDict, names)  # pragma: nocover


# pylint: disable=no-self-use
class FromASN1SCCtoQGenC(RecursiveMapper):
    def MapInteger(self, srcVar: str, dstQGenC: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapReal(self, srcVar: str, dstQGenC: str, _: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapBoolean(self, srcVar: str, dstQGenC: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapOctetString(self, srcVar: str, dstQGenC: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover

        lines = []  # type: List[str]
        limit = sourceSequenceLimit(node, srcVar)
        for i in range(0, node._range[-1]):
            lines.append("if (%s>=%d) %s.element_data[%d] = %s.arr[%d]; else %s.element_data[%d] = 0;\n" %
                         (limit, i + 1, dstQGenC, i, srcVar, i, dstQGenC, i))
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            lines.append("%s.length = %s;\n" % (dstQGenC, limit))
        return lines

    def MapEnumerated(self, srcVar: str, dstQGenC: str, node: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if None in [x[1] for x in node._members]:
            panicWithCallStack("an ENUMERATED must have integer values! (%s)" % node.Location())  # pragma: no cover
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapSequence(self, srcVar: str, dstQGenC: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]),
                    "%s.%s" % (dstQGenC, self.CleanName(child[0])),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVar: str, dstQGenC: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcVar, dstQGenC, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar: str, dstQGenC: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.kind == %s) {\n" % (self.maybeElse(childNo), srcVar, self.CleanName(child[2])))
            lines.extend(
                ['    ' + x
                 for x in self.Map(
                     srcVar + ".u." + self.CleanName(child[0]),
                     "%s.%s" % (dstQGenC, self.CleanName(child[0])),
                     child[1],
                     leafTypeDict,
                     names)])
            lines.append("    %s.choiceIdx = %d;\n" % (dstQGenC, childNo))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcVar: str, dstQGenC: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("need a SIZE constraint or else we can't generate C code (%s)!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                srcVar + ".arr[%d]" % i,
                ("%s.element_data[%d]" % (dstQGenC, i)) if isMappedToPrimitive else ("%s.element_%02d" % (dstQGenC, i)),
                node._containedType,
                leafTypeDict,
                names))
        if isSequenceVariable(node):
            lines.append("%s.length = %s.nCount;\n" % (dstQGenC, srcVar))
        return lines

    def MapSetOf(self, srcVar: str, dstQGenC: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcVar, dstQGenC, node, leafTypeDict, names)  # pragma: nocover


# pylint: disable=no-self-use
class FromQGenCToOSS(RecursiveMapper):
    def MapInteger(self, srcQGenC: str, destVar: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (destVar, srcQGenC)]

    def MapReal(self, srcQGenC: str, destVar: str, _: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (destVar, srcQGenC)]

    def MapBoolean(self, srcQGenC: str, destVar: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = (char) %s;\n" % (destVar, srcQGenC)]

    def MapOctetString(self, srcQGenC: str, destVar: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        for i in range(0, node._range[-1]):
            lines.append("%s.value[%d] = %s.element_data[%d];\n" % (destVar, i, srcQGenC, i))
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            lines.append("%s.length = %s.length;\n" % (destVar, srcQGenC))
        else:
            lines.append("%s.length = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapEnumerated(self, srcQGenC: str, destVar: str, _: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (destVar, srcQGenC)]

    def MapSequence(self, srcQGenC: str, destVar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                self.Map(
                    "%s.%s" % (srcQGenC, self.CleanName(child[0])),
                    destVar + "." + self.CleanName(child[0]),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcQGenC: str, destVar: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcQGenC, destVar, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcQGenC: str, destVar: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choiceIdx == %d) {\n" % (self.maybeElse(childNo), srcQGenC, childNo))
            lines.extend(
                ['    ' + x
                 for x in self.Map(
                     "%s.%s" % (srcQGenC, self.CleanName(child[0])),
                     destVar + ".u." + self.CleanName(child[0]),
                     child[1],
                     leafTypeDict,
                     names)])
            lines.append("    %s.choice = OSS_%s_chosen;\n" % (destVar, self.CleanName(child[0])))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcQGenC: str, destVar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("(%s) needs a SIZE constraint or else we can't generate C code!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.extend(
                self.Map(("%s.element_data[%d]" % (srcQGenC, i)) if isMappedToPrimitive else ("%s.element_%02d" % (srcQGenC, i)),
                         destVar + ".value[%d]" % i,
                         node._containedType,
                         leafTypeDict,
                         names))
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            lines.append("%s.count = %s.length;\n" % (destVar, srcQGenC))
        else:
            lines.append("%s.count = %s;\n" % (destVar, node._range[-1]))
        return lines

    def MapSetOf(self, srcQGenC: str, destVar: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcQGenC, destVar, node, leafTypeDict, names)  # pragma: nocover


# pylint: disable=no-self-use
class FromOSStoQGenC(RecursiveMapper):
    def MapInteger(self, srcVar: str, dstQGenC: str, _: AsnInt, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapReal(self, srcVar: str, dstQGenC: str, _: AsnReal, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapBoolean(self, srcVar: str, dstQGenC: str, _: AsnBool, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapOctetString(self, srcVar: str, dstQGenC: str, node: AsnOctetString, _: AST_Leaftypes, __: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("OCTET STRING (in %s) must have a SIZE constraint inside ASN.1,\nor else we can't generate C code!" % node.Location())  # pragma: no cover
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.append("if (%s.length >= %d) %s.element_data[%d] = %s.value[%d]; else %s.element_data[%d] = 0;\n" %
                         (srcVar, i + 1, dstQGenC, i, srcVar, i, dstQGenC, i))
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            lines.append("%s.length = %s.length;" % (dstQGenC, srcVar))
        return lines

    def MapEnumerated(self, srcVar: str, dstQGenC: str, node: AsnEnumerated, __: AST_Leaftypes, ___: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if None in [x[1] for x in node._members]:
            panicWithCallStack("an ENUMERATED must have integer values! (%s)" % node.Location())  # pragma: no cover
        return ["%s = %s;\n" % (dstQGenC, srcVar)]

    def MapSequence(self, srcVar: str, dstQGenC: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        for child in node._members:
            lines.extend(
                self.Map(
                    srcVar + "." + self.CleanName(child[0]),
                    "%s.%s" % (dstQGenC, self.CleanName(child[0])),
                    child[1],
                    leafTypeDict,
                    names))
        return lines

    def MapSet(self, srcVar: str, dstQGenC: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequence(srcVar, dstQGenC, node, leafTypeDict, names)  # pragma: nocover

    def MapChoice(self, srcVar: str, dstQGenC: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        lines = []  # type: List[str]
        childNo = 0
        for child in node._members:
            childNo += 1
            lines.append("%sif (%s.choice == OSS_%s_chosen) {\n" % (self.maybeElse(childNo), srcVar, self.CleanName(child[0])))
            lines.extend(
                ['    ' + x
                 for x in self.Map(
                     srcVar + ".u." + self.CleanName(child[0]),
                     "%s.%s" % (dstQGenC, self.CleanName(child[0])),
                     child[1],
                     leafTypeDict,
                     names)])
            lines.append("    %s.choiceIdx = %d;\n" % (dstQGenC, childNo))
            lines.append("}\n")
        return lines

    def MapSequenceOf(self, srcVar: str, dstQGenC: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        if not node._range:
            panicWithCallStack("(%s) needs a SIZE constraint or else we can't generate C code!\n" % node.Location())  # pragma: no cover
        isMappedToPrimitive = IsElementMappedToPrimitive(node, names)
        lines = []  # type: List[str]
        for i in range(0, node._range[-1]):
            lines.extend(self.Map(
                srcVar + ".value[%d]" % i,
                ("%s.element_data[%d]" % (dstQGenC, i)) if isMappedToPrimitive else ("%s.element_%02d" % (dstQGenC, i)),
                node._containedType,
                leafTypeDict,
                names))
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            lines.append("%s.length = %s.count;\n" % (dstQGenC, srcVar))
        return lines

    def MapSetOf(self, srcVar: str, dstQGenC: str, node: AsnSequenceOrSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> List[str]:  # pylint: disable=invalid-sequence-index
        return self.MapSequenceOf(srcVar, dstQGenC, node, leafTypeDict, names)  # pragma: nocover


class QGenCGlueGenerator(SynchronousToolGlueGenerator):
    g_FVname = None  # type: str

    def Version(self) -> None:
        print("Code generator: " + "$Id: qgenc_B_mapper.py 2390 2014-11-27 12:39:17Z dtuulik $")  # pragma: no cover

    def FromToolToASN1SCC(self) -> RecursiveMapper:
        return FromQGenCToASN1SCC()

    def FromToolToOSS(self) -> RecursiveMapper:
        return FromQGenCToOSS()

    def FromASN1SCCtoTool(self) -> RecursiveMapper:
        return FromASN1SCCtoQGenC()

    def FromOSStoTool(self) -> RecursiveMapper:
        return FromOSStoQGenC()

    def HeadersOnStartup(self, unused_modelingLanguage: str, unused_asnFile: str, subProgram: ApLevelContainer, unused_subProgramImplementation: str, unused_outputDir: str, unused_maybeFVname: str) -> None:
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
            srcQGenC = "cOutput.%s" % param._id  # pragma: no cover
        elif isinstance(param._sourceElement, AadlParameter):
            srcQGenC = "cOutput.%s" % param._id
        else:  # pragma: no cover
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return srcQGenC

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
            dstQGenC = "cInput.%s" % param._id  # pragma: no cover
        elif isinstance(param._sourceElement, AadlParameter):
            dstQGenC = "cInput.%s" % param._id
        else:  # pragma: no cover
            panicWithCallStack("%s not supported (yet?)\n" % str(param._sourceElement))  # pragma: no cover
        return dstQGenC

    def InitializeBlock(self, unused_modelingLanguage: str, unused_asnFile: str, unused_sp: ApLevelContainer, unused_subProgramImplementation: str, unused_maybeFVname: str) -> None:
        self.C_SourceFile.write("    static int initialized = 0;\n")
        self.C_SourceFile.write("    if (!initialized) {\n")
        self.C_SourceFile.write("        initialized = 1;\n")
        self.C_SourceFile.write("        %s_init();\n" % self.g_FVname)
        self.C_SourceFile.write("    }\n")

    def ExecuteBlock(self, unused_modelingLanguage: str, unused_asnFile: str, unused_sp: ApLevelContainer, unused_subProgramImplementation: str, unused_maybeFVname: str) -> None:
        self.C_SourceFile.write("#ifndef rtmGetStopRequested\n")
        self.C_SourceFile.write("    %s_comp(&cInput, &cOutput);\n" % self.g_FVname)
        self.C_SourceFile.write("#else\n")
        self.C_SourceFile.write("    if (!rtmGetStopRequested(%s_M)) {\n" % self.g_FVname)
        self.C_SourceFile.write("        %s_step(&cInput, &cOutput);\n" % self.g_FVname)
        self.C_SourceFile.write("        if (rtmGetStopRequested(%s_M)) { %s_terminate(); }\n" %
                                (self.g_FVname, self.g_FVname))
        self.C_SourceFile.write("    }\n")
        self.C_SourceFile.write("#endif\n")


def OnStartup(modelingLanguage: str, asnFile: str, subProgram: ApLevelContainer, subProgramImplementation: str, outputDir: str, maybeFVname: str, useOSS: bool) -> None:
    global qgencBackend
    qgencBackend = QGenCGlueGenerator()
    qgencBackend.OnStartup(modelingLanguage, asnFile, subProgram, subProgramImplementation, outputDir, maybeFVname, useOSS)


def OnBasic(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    qgencBackend.OnBasic(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequence(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    qgencBackend.OnSequence(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSet(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    qgencBackend.OnSet(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    qgencBackend.OnEnumerated(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSequenceOf(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    qgencBackend.OnSequenceOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnSetOf(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    qgencBackend.OnSetOf(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename: str, node: AsnNode, subProgram: ApLevelContainer, subProgramImplementation: str, param: Param, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    qgencBackend.OnChoice(nodeTypename, node, subProgram, subProgramImplementation, param, leafTypeDict, names)


def OnShutdown(modelingLanguage: str, asnFile: str, sp: ApLevelContainer, subProgramImplementation: str, maybeFVname: str) -> None:
    qgencBackend.OnShutdown(modelingLanguage, asnFile, sp, subProgramImplementation, maybeFVname)
