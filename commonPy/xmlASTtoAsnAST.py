#!/usr/bin/env python
#
# (C) Semantix Information Technologies.
#
# Semantix Information Technologies is licensing the code of the
# Data Modelling Tools (DMT) in the following dual-license mode:
#
# Commercial Developer License:
#       The DMT Commercial Developer License is the appropriate version
# to use for the development of proprietary and/or commercial software.
# This version is for developers/companies who do not want to share
# the source code they develop with others or otherwise comply with the
# terms of the GNU Lesser General Public License version 3.
#
# GNU LGPL v. 2.1:
#       This version of DMT is the one to use for the development of
# non-commercial applications, when you are willing to comply
# with the terms of the GNU Lesser General Public License version 3.
#
# The features of the two licenses are summarized below:
#
#                       Commercial
#                       Developer               LGPL
#                       License
#
# License cost          License fee charged     No license fee
#
# Must provide source
# code changes to DMT   No, modifications can   Yes, all source code
#                       be closed               must be provided back
#
# Can create            Yes, that is,           No, applications are subject
# proprietary           no source code needs    to the LGPL and all source code
# applications          to be disclosed         must be made available
#
# Support               Yes, 12 months of       No, but available separately
#                       premium technical       for purchase
#                       support
#
# Charge for Runtimes   None                    None
#
import sys
import re
import os
from xml.sax.handler import ContentHandler
import xml.sax

from .asnAST import AsnBool, AsnInt, AsnReal, AsnEnumerated, AsnOctetString, AsnAsciiString, \
    AsnMetaType, AsnSet, AsnSequence, AsnSetOf, AsnSequenceOf, AsnChoice, AsnMetaMember
from .utility import panic, warn
from . import asnParser

g_xmlASTrootNode = None

g_lineno = -1


class Element:
    def __init__(self, name, attrs):
        self._name = name
        self._attrs = attrs
        self._children = []


class InputFormatXMLHandler(ContentHandler):
    def __init__(self, debug=False):
        ContentHandler.__init__(self)
        self._debug = False
        if debug:
            self._debug = True  # pragma: no cover
            self._indent = ""  # pragma: no cover
        self._root = Element('root', {})
        self._roots = [self._root]

    def startElement(self, name, attrs):
        if self._debug:
            print(self._indent + "(", name, ")", ", ".join(list(attrs.keys())))  # pragma: no cover
            self._indent += "    "  # pragma: no cover
        newElement = Element(name, attrs)
        self._roots[-1]._children.append(newElement)
        self._roots.append(newElement)

    #def endElement(self, name):
    def endElement(self, _):
        if self._debug:
            if len(self._indent)>4:  # pragma: no cover
                self._indent = self._indent[:len(self._indent)-4]  # pragma: no cover
            #print self._indent + "(", name, ") ends" # pragma: no cover
        self._roots.pop()

#def Travel(indent, node):
#    print indent + node._name, ",".join(node._attrs.keys())
#    for c in node._children:
#       Travel(indent+"    ", c)


def VisitAll(node, expectedType, Action):
    results = []
    if node is not None:
        if node._name == expectedType:
            results = [Action(node)]
        for child in node._children:
            results += VisitAll(child, expectedType, Action)
    return results


def GetAttr(node, attrName):
    if attrName not in list(node._attrs.keys()):
        return None
    else:
        return node._attrs[attrName]


def GetChild(node, childName):
    for x in node._children:
        if x._name == childName:
            return x
    return None  # pragma: no cover


class Pretty:
    def __repr__(self):
        result = ""  # pragma: no cover
        for i in dir(self):  # pragma: no cover
            if i != "__repr__":  # pragma: no cover
                result += chr(27)+"[32m"+i+chr(27) + "[0m:"  # pragma: no cover
                result += repr(getattr(self, i))  # pragma: no cover
                result += "\n"  # pragma: no cover
        return result  # pragma: no cover


#def CreateBoolean(newModule, lineNo, xmlBooleanNode):
def CreateBoolean(newModule, lineNo, _):
    return AsnBool(
        asnFilename=newModule._asnFilename,
        lineno=lineNo)


def GetRange(newModule, lineNo, nodeWithMinAndMax, valueType):
    try:
        mmin = GetAttr(nodeWithMinAndMax, "Min")
        #rangel = ( mmin == "MIN" ) and -2147483648L or valueType(mmin)
        if mmin == "MIN":
            panic("You missed a range specification, or used MIN/MAX (line %s)" % lineNo)  # pragma: no cover
        rangel = valueType(mmin)
        mmax = GetAttr(nodeWithMinAndMax, "Max")
        #rangeh = ( mmax == "MAX" ) and 2147483647L or valueType(mmax)
        if mmax == "MAX":
            panic("You missed a range specification, or used MIN/MAX (line %s)" % lineNo)  # pragma: no cover
        rangeh = valueType(mmax)
    except:  # pragma: no cover
        descr = {int: "integer", float: "floating point"}  # pragma: no cover
        panic("Expecting %s value ranges (%s, %s)" %  # pragma: no cover
              (descr[valueType], newModule._asnFilename, lineNo))  # pragma: no cover
    return [rangel, rangeh]


def CreateInteger(newModule, lineNo, xmlIntegerNode):
    return AsnInt(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        range=GetRange(newModule, lineNo, xmlIntegerNode, int))


def CreateReal(newModule, lineNo, xmlRealNode):
    return AsnReal(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        range=GetRange(newModule, lineNo, xmlRealNode, float))


def CreateEnumerated(newModule, lineNo, xmlEnumeratedNode):
    #bSetIntValue = True
    #if GetAttr(xmlEnumeratedNode, "ValuesAutoCalculated") == "True":
    #   bSetIntValue = False
    return AsnEnumerated(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        members=VisitAll(
            xmlEnumeratedNode,
            "EnumValue",
            lambda x: [GetAttr(x, "StringValue"), GetAttr(x, "IntValue")]))
            #lambda x: [GetAttr(x, "StringValue"), GetAttr(x, "IntValue"), GetAttr(x, "EnumID")]))
            # old code: used to check the ValuesAutoCalculated and use None for the integer values
            #lambda x: [GetAttr(x, "StringValue"), bSetIntValue and GetAttr(x, "IntValue") or None]))


#def CreateBitString(newModule, lineNo, xmlBitString):
def CreateBitString(_, __, ___):
    panic("BitString type is not supported by the toolchain."+  # pragma: no cover
          "Please use SEQUENCE OF BOOLEAN")  # pragma: no cover


def CreateOctetString(newModule, lineNo, xmlOctetString):
    return AsnOctetString(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        range=GetRange(newModule, lineNo, xmlOctetString, int))


def CreateIA5String(newModule, lineNo, xmlIA5StringNode):
    #panic("IA5Strings are supported by ASN1SCC, but are not supported yet " # pragma: no cover
    #        "by the toolchain. Please use OCTET STRING") # pragma: no cover
    #return CreateOctetString(newModule, lineNo, xmlIA5StringNode)
    return AsnAsciiString(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        range=GetRange(newModule, lineNo, xmlIA5StringNode, int))


def CreateNumericString(newModule, lineNo, xmlNumericStringNode):
    return CreateOctetString(newModule, lineNo, xmlNumericStringNode)  # pragma: no cover


def CreateReference(newModule, lineNo, xmlReferenceNode):
    try:
        mi=int(GetAttr(xmlReferenceNode, "Min"))
    except:
        try:
            mi=float(GetAttr(xmlReferenceNode, "Min"))
        except:
            mi = None
    try:
        ma=int(GetAttr(xmlReferenceNode, "Max"))
    except:
        try:
            ma=float(GetAttr(xmlReferenceNode, "Max"))
        except:
            ma=None
    return AsnMetaType(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        containedType=GetAttr(xmlReferenceNode, "ReferencedTypeName"),
        Min=mi, Max=ma)


def CommonSetSeqOf(newModule, lineNo, xmlSequenceOfNode, classToCreate):
    xmlType = GetChild(xmlSequenceOfNode, "Type")
    if xmlType is None:
        panic("CommonSetSeqOf: No child under SequenceOfType (%s, %s)" %  # pragma: no cover
              (newModule._asnFilename, lineNo))  # pragma: no cover
    if len(xmlType._children) == 0:
        panic("CommonSetSeqOf: No children for Type (%s, %s)" %  # pragma: no cover
              (newModule._asnFilename, lineNo))  # pragma: no cover
    if xmlType._children[0]._name == "ReferenceType":
        contained = GetAttr(xmlType._children[0], "ReferencedTypeName")
    else:
        contained = GenericFactory(newModule, xmlType)
    return classToCreate(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        range=GetRange(newModule, lineNo, xmlSequenceOfNode, int),
        containedType=contained)


def CreateSequenceOf(newModule, lineNo, xmlSequenceOfNode):
    return CommonSetSeqOf(newModule, lineNo, xmlSequenceOfNode, AsnSequenceOf)


def CreateSetOf(newModule, lineNo, xmlSetOfNode):
    return CommonSetSeqOf(newModule, lineNo, xmlSetOfNode, AsnSetOf)


def CommonSeqSetChoice(newModule, lineNo, xmlSequenceNode, classToCreate, childTypeName):
    # Bug fixed in ASN1SCC, this check is no longer needed
#   if len(xmlSequenceNode._children) == 0:
#       panic("CommonSeqSetChoice: No children under Sequence/Choice/SetType (%s, %s)" %  # pragma: no cover
#             (newModule._asnFilename, lineNo))  # pragma: no cover

    myMembers = []
    for x in xmlSequenceNode._children:
        if x._name == childTypeName:
            opti = GetAttr(x, "Optional")
            if opti and opti == "True":
                warn("OPTIONAL attribute ignored (for field contained in %s,%s)" % (newModule._asnFilename, lineNo))
            enumID = GetAttr(x, "EnumID")
            myMembers.append([GetAttr(x, "VarName"), GenericFactory(newModule, GetChild(x, "Type"))])
            myMembers[-1].append(enumID)
    for tup in myMembers:
        if isinstance(tup[1], AsnMetaType):
            asnMetaMember = AsnMetaMember(
                asnFilename=tup[1]._asnFilename,
                containedType=tup[1]._containedType,
                lineno=tup[1]._lineno,
                Min=tup[1]._Min,
                Max=tup[1]._Max)
            tup[1] = asnMetaMember

    return classToCreate(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        members=myMembers)


def CreateSequence(newModule, lineNo, xmlSequenceNode):
    return CommonSeqSetChoice(
        newModule, lineNo, xmlSequenceNode,
        AsnSequence, "SequenceOrSetChild")


def CreateSet(newModule, lineNo, xmlSetNode):
    return CommonSeqSetChoice(
        newModule, lineNo, xmlSetNode,
        AsnSet, "SequenceOrSetChild")


def CreateChoice(newModule, lineNo, xmlChoiceNode):
    return CommonSeqSetChoice(
        newModule, lineNo, xmlChoiceNode,
        AsnChoice, "ChoiceChild")


def GenericFactory(newModule, xmlType):
    Factories = {
        "BooleanType": CreateBoolean,
        "IntegerType": CreateInteger,
        "RealType": CreateReal,
        "EnumeratedType": CreateEnumerated,
        "BitStringType": CreateBitString,
        "OctetStringType": CreateOctetString,
        "IA5StringType": CreateIA5String,
        "NumericStringType": CreateNumericString,
        "ReferenceType": CreateReference,
        "SequenceOfType": CreateSequenceOf,
        "SetOfType": CreateSetOf,
        "SequenceType": CreateSequence,
        "SetType": CreateSet,
        "ChoiceType": CreateChoice
    }
    lineNo = GetAttr(xmlType, "Line")
    global g_lineno
    g_lineno = lineNo
    if len(xmlType._children) == 0:
        panic("GenericFactory: No children for Type (%s, %s)" %  # pragma: no cover
              (newModule._asnFilename, lineNo))  # pragma: no cover
    xmlContainedType = xmlType._children[0]
    if xmlContainedType._name not in list(Factories.keys()):
        panic("Unsupported XML type node: '%s' (%s, %s)" %  # pragma: no cover
              (xmlContainedType._name, newModule._asnFilename, lineNo))  # pragma: no cover
    return Factories[xmlContainedType._name](
        newModule, lineNo, xmlContainedType)


def VisitTypeAssignment(newModule, xmlTypeAssignment):
    xmlType = GetChild(xmlTypeAssignment, "Type")
    if xmlType is None:
        panic("VisitTypeAssignment: No child under TypeAssignment")  # pragma: no cover
    return (
        GetAttr(xmlTypeAssignment, "Name"),
        GenericFactory(newModule, xmlType))


def VisitAsn1Module(xmlAsn1File, xmlModule, modules):
    class Module(Pretty):
        pass
    newModule = Module()
    newModule._id = GetAttr(xmlModule, "ID")
    newModule._asnFilename = GetAttr(xmlAsn1File, "FileName")
    newModule._exportedTypes = VisitAll(
        GetChild(xmlModule, "ExportedTypes"),
        "ExportedType",
        lambda x: GetAttr(x, "Name"))

    newModule._exportedVariables = VisitAll(
        GetChild(xmlModule, "ExportedVariables"),
        "ExportedVariable",
        lambda x: GetAttr(x, "Name"))

    newModule._importedModules = VisitAll(
        GetChild(xmlModule, "ImportedModules"),
        "ImportedModule",
        lambda x:
        (
            GetAttr(x, "ID"),
            VisitAll(
                GetChild(x, "ImportedTypes"),
                "ImportedType",
                lambda y: GetAttr(y, "Name")),
            VisitAll(
                GetChild(x, "ImportedVariables"),
                "ImportedVariable",
                lambda y: GetAttr(y, "Name")),
        )
    )

    newModule._typeAssignments = VisitAll(
        GetChild(xmlModule, "TypeAssignments"),
        "TypeAssignment",
        lambda x: VisitTypeAssignment(newModule, x))

    asnParser.g_typesOfFile.setdefault(newModule._asnFilename, [])
    asnParser.g_typesOfFile[newModule._asnFilename].extend(
        [x for x, y in newModule._typeAssignments])

    asnParser.g_astOfFile.setdefault(newModule._asnFilename, [])
    asnParser.g_astOfFile[newModule._asnFilename].extend(
        [x for x, y in newModule._typeAssignments])

    modules.append(newModule)


def ParseASN1SCC_AST(filename):
    parser = xml.sax.make_parser()
    handler = InputFormatXMLHandler()
    parser.setContentHandler(handler)
    #parser.setFeature("http://xml.org/sax/features/validation", True)
    parser.parse(filename)

    if len(handler._root._children) != 1 or handler._root._children[0]._name != "ASN1AST":
        panic("You must use an XML file that contains one ASN1AST node")  # pragma: no cover

    #Travel("", handler._roots[0])
    modules = []
    VisitAll(
        handler._root._children[0],
        "Asn1File",
        lambda x: VisitAll(
            x,
            "Asn1Module",
            lambda y: VisitAsn1Module(x, y, modules)))

    global g_xmlASTrootNode
    g_xmlASTrootNode = handler._root

    asnParser.g_names = {}
    asnParser.g_checkedSoFarForKeywords = {}
    asnParser.g_leafTypeDict = {}

    for m in modules:
        #print "Module", m._id
        for typeName, typeData in m._typeAssignments:
            #print "Type:", typeName
            asnParser.g_names[typeName] = typeData
    asnParser.g_leafTypeDict.update(asnParser.VerifyAndFixAST())

    for nodeTypename in list(asnParser.g_names.keys()):
        if nodeTypename not in asnParser.g_checkedSoFarForKeywords:
            asnParser.g_checkedSoFarForKeywords[nodeTypename] = 1
            asnParser.CheckForInvalidKeywords(nodeTypename)


def SimpleCleaner(x):
    return re.sub(r'[^a-zA-Z0-9_]', '_', x)


def PrintType(f, xmlType, indent, nameCleaner):
    if len(xmlType._children) == 0:
        panic("AST inconsistency: xmlType._children == 0\nContact ESA")  # pragma: no cover
    realType = xmlType._children[0]
    if realType._name == "BooleanType":
        f.write('BOOLEAN')
    elif realType._name == "IntegerType":
        f.write('INTEGER')
        mmin = GetAttr(realType, "Min")
        mmax = GetAttr(realType, "Max")
        f.write(' (%s .. %s)' % (mmin, mmax))
    elif realType._name == "RealType":
        f.write('REAL')
        mmin = GetAttr(realType, "Min")
        mmax = GetAttr(realType, "Max")
        f.write(' (%s .. %s)' % (mmin, mmax))
    elif realType._name == "BitStringType":
        panic("BIT STRINGs are not supported, use SEQUENCE OF BOOLEAN")  # pragma: no cover
    elif realType._name == "OctetStringType" or realType._name == "IA5StringType" or realType._name == "NumericStringType":
        f.write('OCTET STRING')
        mmin = GetAttr(realType, "Min")
        mmax = GetAttr(realType, "Max")
        f.write(' (SIZE (%s .. %s))' % (mmin, mmax))
    elif realType._name == "ReferenceType":
        f.write(nameCleaner(GetAttr(realType, "ReferencedTypeName")))
    elif realType._name == "EnumeratedType":
        f.write('ENUMERATED {\n')
        options = []
        VisitAll(realType, "EnumValue", lambda x: options.append(x))
        if len(options)>0:
            f.write(indent + '    ' + nameCleaner(GetAttr(options[0], "StringValue")) + "(" + GetAttr(options[0], "IntValue") + ")")
            for otherOptions in options[1:]:
                f.write(',\n' + indent + '    ' + nameCleaner(GetAttr(otherOptions, "StringValue")) + "(" + GetAttr(otherOptions, "IntValue") + ")")
        f.write('\n' + indent + '}')
    elif realType._name == "SequenceType" or realType._name == "SetType":
        if realType._name == "SequenceType":
            f.write('SEQUENCE {\n')
        else:
            f.write('SET {\n')
        if len(realType._children)>0:
            f.write(indent + '    ' + nameCleaner(GetAttr(realType._children[0], "VarName")) + "\t")
            firstChildOptional = GetAttr(realType._children[0], "Optional") == "True"
            if len(realType._children[0]._children) == 0:
                panic("AST inconsistency: len(realType._children[0]._children) = 0\nContact ESA")  # pragma: no cover
            PrintType(f, realType._children[0]._children[0], indent+"    ", nameCleaner)  # the contained type of the first child
            if firstChildOptional:
                f.write(' OPTIONAL')
            for sequenceOrSetChild in realType._children[1:]:
                f.write(",\n" + indent + '    ' + nameCleaner(GetAttr(sequenceOrSetChild, "VarName")) + "\t")
                childOptional = GetAttr(sequenceOrSetChild, "Optional") == "True"
                if len(sequenceOrSetChild._children) == 0:
                    panic("AST inconsistency: len(sequenceOrSetChild._children) = 0\nContact ESA")  # pragma: no cover
                PrintType(f, sequenceOrSetChild._children[0], indent+"    ", nameCleaner)  # the contained type
                if childOptional:
                    f.write(' OPTIONAL')
#       else:
#           panic("AST inconsistency: len(realType._children)=0\nContact ESA")  # pragma: no cover
        f.write('\n' + indent + '}')
    elif realType._name == "ChoiceType":
        f.write('CHOICE {\n')
        if len(realType._children)>0:
            f.write(indent + '    ' + nameCleaner(GetAttr(realType._children[0], "VarName")) + "\t")
            if len(realType._children[0]._children) == 0:
                panic("AST inconsistency: len(realType._children[0]._children) = 0\nContact ESA")  # pragma: no cover
            PrintType(f, realType._children[0]._children[0], indent+"    ", nameCleaner)  # the contained type of the first child
            for choiceChild in realType._children[1:]:
                f.write(",\n" + indent + '    ' + nameCleaner(GetAttr(choiceChild, "VarName")) + "\t")
                if len(choiceChild._children) == 0:
                    panic("AST inconsistency: len(choiceChild._children) = 0\nContact ESA")  # pragma: no cover
                PrintType(f, choiceChild._children[0], indent+"    ", nameCleaner)  # the contained type
        else:
            panic("AST inconsistency: len(realType._children)=0\nContact ESA")  # pragma: no cover
        f.write('\n' + indent + '}')
    elif realType._name == "SequenceOfType":
        f.write('SEQUENCE')
        mmin = GetAttr(realType, "Min")
        mmax = GetAttr(realType, "Max")
        f.write(' (SIZE (%s .. %s)) OF ' % (mmin, mmax))
        if len(realType._children)>0:
            PrintType(f, realType._children[0], indent+"    ", nameCleaner)  # the contained type
        else:
            panic("AST inconsistency: len(realType._children)=0\nContact ESA")  # pragma: no cover
    elif realType._name == "SetOfType":
        f.write('SET')
        mmin = GetAttr(realType, "Min")
        mmax = GetAttr(realType, "Max")
        f.write(' (SIZE (%s .. %s)) OF ' % (mmin, mmax))
        if len(realType._children)>0:
            PrintType(f, realType._children[0], indent+"    ", nameCleaner)  # the contained type
        else:
            panic("AST inconsistency: len(realType._children)=0\nContact ESA")  # pragma: no cover
    else:
        panic("AST inconsistency: Unknown type (%s)\nContact ESA" % realType._name)  # pragma: no cover


def PrintGrammarFromAST(f, nameCleaner=SimpleCleaner):
    ourtypeAssignments = []
    VisitAll(
        g_xmlASTrootNode._children[0],
        "Asn1File",
        lambda x: VisitAll(
            x,
            "TypeAssignment",
            lambda y: ourtypeAssignments.append((x,y))))

    for a,t in ourtypeAssignments:
        f.write("-- " + GetAttr(a, "FileName") + "\n%s ::= " % nameCleaner(GetAttr(t, "Name")))
        typeChild = GetChild(t, "Type")
        if typeChild:
            PrintType(f, typeChild, '', nameCleaner)
            f.write('\n\n')
        else:
            panic("AST inconsistency: typeChild is None\nContact ESA")  # pragma: no cover


def PrintGrammarFromASTtoStdOut():
    # Starting from the xmlASTrootNode, recurse and print the ASN.1 grammar
    PrintGrammarFromAST(sys.stdout)


def main():
    if len(sys.argv) != 2 or not os.path.isfile(sys.argv[1]):
        sys.stderr.write("Missing or invalid path provided!\n")
        sys.exit(1)

    ParseASN1SCC_AST(sys.argv[1])
    asnParser.Dump()
    print("\nRe-created grammar:\n\n")
    PrintGrammarFromASTtoStdOut()

if __name__ == "__main__":
    main()
