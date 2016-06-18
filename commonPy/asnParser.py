#!/usr/bin/env python3
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
'''
ASN.1 Parser

This module parses ASN.1 grammars and creates an abstract syntax tree (AST)
inside configMT.inputCodeAST, for use with the code generators.
'''
import os
import sys
import copy
import tempfile
import re
import distutils.spawn as spawn

import xml.sax  # type: ignore
from typing import Union, List, Dict, Tuple, Any  # pylint: disable=W0611

from . import configMT
from . import utility

from .asnAST import (
    AsnBasicNode, AsnEnumerated, AsnSequence, AsnChoice, AsnSequenceOf,
    AsnSet, AsnSetOf, AsnMetaMember, AsnMetaType, AsnInt, AsnReal, AsnNode,
    AsnComplexNode, AsnBool, AsnOctetString, AsnAsciiString
)

g_asnFilename = ""

g_filename = ''
g_metatypes = {}

# MyPy type aliases
Typename = str
Filename = str
AST_Lookup = Dict[Typename, AsnNode]
AST_TypenamesOfFile = Dict[Filename, List[str]]  # pylint: disable=invalid-sequence-index
AST_TypesOfFile = Dict[Filename, List[AsnNode]]  # pylint: disable=invalid-sequence-index
AST_Leaftypes = Dict[Typename, str]

g_names = {}         # type: AST_Lookup
g_typesOfFile = {}   # type: AST_TypenamesOfFile
g_leafTypeDict = {}  # type: AST_Leaftypes
g_astOfFile = {}     # type: AST_TypesOfFile

g_checkedSoFarForKeywords = {}  # type: Dict[str, int]

g_invalidKeywords = [
    "active", "adding", "all", "alternative", "and", "any", "as", "atleast", "axioms", "block", "call", "channel", "comment", "connect", "connection", "constant", "constants", "create", "dcl", "decision", "default", "else", "endalternative", "endblock", "endchannel", "endconnection", "enddecision", "endgenerator", "endmacro", "endnewtype", "endoperator", "endpackage", "endprocedure", "endprocess", "endrefinement", "endselect", "endservice", "endstate", "endsubstructure", "endsyntype", "endsystem", "env", "error", "export", "exported", "external", "fi", "finalized", "for", "fpar", "from", "gate", "generator", "if", "import", "imported", "in", "inherits", "input", "interface", "join", "literal", "literals", "macro", "macrodefinition", "macroid", "map", "mod", "nameclass", "newtype", "nextstate", "nodelay", "noequality", "none", "not", "now", "offspring", "operator", "operators", "or", "ordering", "out", "output", "package", "parent", "priority", "procedure", "process", "provided", "redefined", "referenced", "refinement", "rem", "remote", "reset", "return", "returns", "revealed", "reverse", "save", "select", "self", "sender", "service", "set", "signal", "signallist", "signalroute", "signalset", "spelling", "start", "state", "stop", "struct", "substructure", "synonym", "syntype", "system", "task", "then", "this", "timer", "to", "type", "use", "via", "view", "viewed", "virtual", "with", "xor", "end", "i", "j", "auto", "const",
    # From Nicolas Gillet/Astrium for SCADE
    "abstract", "activate", "and", "assume", "automaton", "bool", "case", "char", "clock", "const", "default", "div", "do", "else", "elsif", "emit", "end", "enum", "every", "false", "fby", "final", "flatten", "fold", "foldi", "foldw", "foldwi", "function", "guarantee", "group", "if", "imported", "initial", "int", "is", "last", "let", "make", "map", "mapfold", "mapi", "mapw", "mapwi", "match", "merge", "mod", "node", "not", "numeric", "of", "onreset", "open", "or", "package", "parameter", "pre", "private", "probe", "public", "real", "restart", "resume", "returns", "reverse", "sensor", "sig", "specialize", "state", "synchro", "tel", "then", "times", "transpose", "true", "type", "unless", "until", "var", "when", "where", "with", "xor",
    # From Maxime - ESA GNC Team
    "open", "close", "flag"
]

tokens = (
    'DEFINITIONS',
    'APPLICATION',
    'AUTOMATIC',
    'IMPLICIT',
    'EXPLICIT',
    'TAGS',
    'BEGIN',
    'IMPORTS',
    'EXPORTS',
    'FROM',
    'ALL',
    'CHOICE',
    'SEQUENCE',
    'SET',
    'OF',
    'END',
    'OPTIONAL',
    'INTEGER',
    'REAL',
    'OCTET',
    #    'BIT',
    'STRING',
    'BOOLEAN',
    'TRUE',
    'FALSE',
    'ASCIISTRING',
    'NUMBERSTRING',
    'VISIBLESTRING',
    'PRINTABLESTRING',
    'UTF8STRING',
    'ENUMERATED',
    'SEMI',
    'LPAREN',
    'RPAREN',
    'LBRACKET',
    'RBRACKET',
    'BLOCK_END',
    'BLOCK_BEGIN',
    'DEF',
    'NAME',
    'COMMA',
    'INTVALUE',
    'REALVALUE',
    'DEFAULT',
    'SIZE',
    'DOTDOT',
    'DOTDOTDOT',
    'WITH',
    'COMPONENTS',
    'MANTISSA',
    'BASE',
    'EXPONENT'
)

lotokens = [tkn.lower() for tkn in tokens]


# Parsing rules

#    'BIT': 'BIT',
reserved = {
    'DEFINITIONS': 'DEFINITIONS',
    'APPLICATION': 'APPLICATION',
    'TAGS': 'TAGS',
    'BEGIN': 'BEGIN',
    'CHOICE': 'CHOICE',
    'SEQUENCE': 'SEQUENCE',
    'SET': 'SET',
    'OF': 'OF',
    'END': 'END',
    'OPTIONAL': 'OPTIONAL',
    'BOOLEAN': 'BOOLEAN',
    'INTEGER': 'INTEGER',
    'REAL': 'REAL',
    'OCTET': 'OCTET',
    'STRING': 'STRING',
    'UTF8String': 'UTF8STRING',
    'AsciiString': 'ASCIISTRING',
    'NumberString': 'NUMBERSTRING',
    'VisibleString': 'VISIBLESTRING',
    'PrintableString': 'PRINTABLESTRING',
    'ENUMERATED': 'ENUMERATED',
    'AUTOMATIC': 'AUTOMATIC',
    'IMPLICIT': 'IMPLICIT',
    'EXPLICIT': 'EXPLICIT',
    'SIZE': 'SIZE',
    'TRUE': 'TRUE',
    'FALSE': 'FALSE',
    'DEFAULT': 'DEFAULT',
    'mantissa': 'MANTISSA',
    'base': 'BASE',
    'exponent': 'EXPONENT',
    'WITH': 'WITH',
    'FROM': 'FROM',
    'IMPORTS': 'IMPORTS',
    'EXPORTS': 'EXPORTS',
    'ALL': 'ALL',
    'COMPONENTS': 'COMPONENTS'
}


def KnownType(node, names):
    retVal = True
    if isinstance(node, str):
        utility.panic("Referenced type (%s) does not exist!\n" % node)
    if isinstance(node, (AsnBasicNode, AsnEnumerated)):
        pass
    elif isinstance(node, (AsnSequence, AsnChoice, AsnSet)):
        for x in node._members:
            if not KnownType(x[1], names):
                return False
    elif isinstance(node, AsnMetaMember):
        retVal = KnownType(names.get(node._containedType, node._containedType), names)
    elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
        if isinstance(node._containedType, str):
            containedType = names.get(node._containedType, node._containedType)
        else:
            containedType = node._containedType
        retVal = KnownType(containedType, names)
    elif isinstance(node, AsnMetaType):
        retVal = KnownType(names.get(node._containedType, node._containedType), names)
    else:
        utility.panic("Unknown node type (%s)!\n" % str(node))
    return retVal


def CleanNameForAST(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def VerifyAndFixAST() -> Dict[str, str]:
    '''Check that all types are defined and are not missing.
    It returns a map providing the leafType of each type.
    '''
    unknownTypes = {}  # type: Dict[str, int]
    knownTypes = {}    # type: Dict[str, str]
    equivalents = {}   # type: Dict[str, List[str]]
    while True:  # pylint: disable=too-many-nested-blocks
        lastUnknownTypes = copy.copy(unknownTypes)
        lastKnownTypes = copy.copy(knownTypes)
        lastEquivalents = copy.copy(equivalents)
        for nodeTypename in list(g_names.keys()):

            node = g_names[nodeTypename]  # type: AsnNode

            # AsnMetaMembers can only appear inside SEQUENCEs and CHOICEs,
            # not at the top level!
            assert not isinstance(node, AsnMetaMember)

            # Type level typedefs are stored in the equivalents dictionary
            if isinstance(node, AsnMetaType):
                # A ::= B
                # A and B are nodeTypename  and  node._containedType
                equivalents.setdefault(node._containedType, [])
                # Add A to the list of types that are equivalent to B
                equivalents[node._containedType].append(nodeTypename)
                # and if we know B's leafType, then we also know A's
                if node._containedType in knownTypes:
                    knownTypes[nodeTypename] = node._containedType
                else:
                    unknownTypes[nodeTypename] = 1
            # AsnBasicNode type assignments are also equivalents
            elif isinstance(node, AsnBasicNode):
                # node._leafType is one of BOOLEAN, OCTET STRING, INTEGER, etc
                equivalents.setdefault(node._leafType, [])
                equivalents[node._leafType].append(nodeTypename)
                knownTypes[nodeTypename] = node._leafType
            # AsnEnumerated types are known types - they don't have external refs
            elif isinstance(node, AsnEnumerated):
                # node._leafType is ENUMERATED
                knownTypes[nodeTypename] = node._leafType
            # SEQUENCEs and CHOICEs: check their children for unknown AsnMetaMembers
            elif isinstance(node, (AsnSequence, AsnChoice, AsnSet)):
                bFoundUnknown = False
                for x in node._members:
                    if isinstance(x[1], AsnMetaMember) and x[1]._containedType not in knownTypes:
                        bFoundUnknown = True
                        break
                if bFoundUnknown:
                    unknownTypes[nodeTypename] = 1
                else:
                    # node._leafType is SEQUENCE or CHOICE
                    knownTypes[nodeTypename] = node._leafType
            # SEQUENCE OFs: check their contained type
            elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
                if node._containedType in knownTypes or isinstance(node._containedType, AsnBasicNode):
                    knownTypes[nodeTypename] = node._leafType
                elif isinstance(node._containedType, AsnComplexNode):
                    knownTypes[nodeTypename] = node._leafType
                else:
                    unknownTypes[nodeTypename] = 1

        # We have completed a sweep over all AST entries.
        # now check the knownTypes and unknownTypes information
        # to see if we have figured out (leafType wise) all nodes
        for known in list(knownTypes.keys()):
            # for each of the nodes we know (leafType wise)

            # remove it from the unknownTypes dictionary
            if known in unknownTypes:
                del unknownTypes[known]

            # remove all it's equivalents, too (from the unknownTypes)
            if known in equivalents:
                for alsoKnown in equivalents[known]:
                    if alsoKnown in unknownTypes:
                        del unknownTypes[alsoKnown]

                    # Additionally, follow the chain to the last knownType
                    seed = known
                    while seed in knownTypes:
                        if seed != knownTypes[seed]:
                            seed = knownTypes[seed]
                        else:
                            break
                    # and update knownTypes dictionary to contain leafType
                    knownTypes[alsoKnown] = seed

        # If this pass has not changed the knownTypes and the unknownTypes and the equivalents, we are done
        if lastEquivalents == equivalents and lastKnownTypes == knownTypes and lastUnknownTypes == unknownTypes:
            break

    if len(unknownTypes) != 0:
        utility.panic('AsnParser: Types remain unknown after symbol fixup:\n%s\n' % list(unknownTypes.keys()))

    # Remove all AsnMetaTypes from the ast
    # by using the g_names lookup on their _containedType
    for nodeTypename in list(g_names.keys()):
        # Min, Max: to cope with ReferenceTypes that redefine their
        # constraints (for now, ASN1SCC provides only INTEGERs)
        Min = Max = None
        node = g_names[nodeTypename]
        if hasattr(node, "_Min") and Min is None:
            Min = node._Min  # type: ignore
        if hasattr(node, "_Max") and Max is None:
            Max = node._Max  # type: ignore
        originalNode = node
        while isinstance(node, AsnMetaType):
            g_metatypes[nodeTypename] = node._containedType
            node = g_names[node._containedType]
            if hasattr(node, "_Min") and Min is None:
                Min = node._Min  # type: ignore
            if hasattr(node, "_Max") and Max is None:
                Max = node._Max  # type: ignore
        # To cope with ReferenceTypes that redefine their
        # constraints (for now, ASN1SCC provides only INTEGERs)
        if isinstance(originalNode, AsnMetaType):
            target = copy.copy(node)  # we need to keep the _asnFilename
            target._asnFilename = originalNode._asnFilename
        elif isinstance(node, AsnInt) and Min is not None and Max is not None:
            target = copy.copy(node)  # we need to keep the Min/Max
            target._range = [Min, Max]
        else:
            target = node
        g_names[nodeTypename] = target

    for name, node in list(g_names.items()):
        if not KnownType(node, g_names):
            utility.panic("Node %s not resolvable (%s)!\n" % (name, node.Location()))
        for i in ["_Min", "_Max"]:
            cast = float if isinstance(node, AsnReal) else int
            if hasattr(node, i) and getattr(node, i) is not None:
                setattr(node, i, cast(getattr(node, i)))

    knownTypes['INTEGER'] = 'INTEGER'
    knownTypes['REAL'] = 'REAL'
    knownTypes['BOOLEAN'] = 'BOOLEAN'
    knownTypes['OCTET STRING'] = 'OCTET STRING'
    knownTypes['AsciiString'] = 'OCTET STRING'
    knownTypes['NumberString'] = 'OCTET STRING'
    knownTypes['VisibleString'] = 'OCTET STRING'
    knownTypes['PrintableString'] = 'OCTET STRING'
    knownTypes['UTF8String'] = 'OCTET STRING'

    # Find all the SEQUENCE, CHOICE and SEQUENCE OFs
    # and if the contained type is not one of AsnBasicNode, AsnEnumerated, AsnMetaMember,
    # define a name and use it... (for SEQUENCEOFs/SETOFs, allow also 'str')
    internalNo = 1
    addedNewPseudoType = True
    while addedNewPseudoType:  # pylint: disable=too-many-nested-blocks
        addedNewPseudoType = False
        listOfTypenames = sorted(g_names.keys())
        for nodeTypename in listOfTypenames:
            node = g_names[nodeTypename]
            if isinstance(node, (AsnChoice, AsnSequence, AsnSet)):
                for child in node._members:
                    if not isinstance(child[1], AsnBasicNode) and \
                            not isinstance(child[1], AsnEnumerated) and \
                            not isinstance(child[1], AsnMetaMember):
                        # It will be an internal sequence, choice or sequenceof
                        assert \
                            isinstance(child[1], AsnChoice) or \
                            isinstance(child[1], AsnSequence) or \
                            isinstance(child[1], AsnSet) or \
                            isinstance(child[1], AsnSetOf) or \
                            isinstance(child[1], AsnSequenceOf)
                        internalName = newname = nodeTypename + '_' + CleanNameForAST(child[0])
                        while internalName in g_names:
                            internalName = (newname + "_%d") % internalNo
                            internalNo += 1
                        g_names[internalName] = child[1]
                        child[1]._isArtificial = True
                        g_leafTypeDict[internalName] = child[1]._leafType
                        child[1] = AsnMetaMember(asnFilename=child[1]._asnFilename, containedType=internalName)
                        addedNewPseudoType = True
            elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
                if not isinstance(node._containedType, str) and \
                        not isinstance(node._containedType, AsnBasicNode) and \
                        not isinstance(node._containedType, AsnEnumerated):
                    internalName = newname = nodeTypename + "_elm"
                    while internalName in g_names:
                        internalName = (newname + "_%d") % internalNo
                        internalNo += 1
                    g_names[internalName] = node._containedType
                    node._containedType._isArtificial = True
                    g_leafTypeDict[internalName] = node._containedType._leafType
                    node._containedType = internalName
                    addedNewPseudoType = True

    # return the leafType dictionary
    return knownTypes


def IsInvalidType(name: str) -> bool:
    return \
        (name.lower() in g_invalidKeywords) or \
        (name.lower() in lotokens) or \
        any([name.lower().endswith(x) for x in ["-buffer", "-buffer-max"]])


def CheckForInvalidKeywords(node_or_str: Union[str, AsnNode]) -> None:
    if isinstance(node_or_str, str):
        if IsInvalidType(node_or_str):
            utility.panic(
                "TASTE disallows certain type names for various reasons.\n'%s' is not allowed" % node_or_str)
        node = g_names[node_or_str]  # type: AsnNode
    else:
        node = node_or_str

    if isinstance(node, (AsnBasicNode, AsnEnumerated)):
        pass
    elif isinstance(node, (AsnSequence, AsnChoice, AsnSet)):
        for child in node._members:
            if child[0].lower() in g_invalidKeywords or child[0].lower() in lotokens:
                utility.panic(
                    "TASTE disallows certain field names because they are used in various modelling tools.\n" +
                    "Invalid field name '%s' used in type defined in %s" % (child[0], node.Location()))
            if isinstance(child[1], AsnMetaMember) and child[1]._containedType not in g_checkedSoFarForKeywords:
                if IsInvalidType(child[1]._containedType.lower()):
                    utility.panic(
                        "TASTE disallows certain type names for various reasons.\n" +
                        "Invalid type name '%s' used in type defined in %s" % (child[1]._containedType, node.Location()))
                if child[1]._containedType not in g_checkedSoFarForKeywords:
                    g_checkedSoFarForKeywords[child[1]._containedType] = 1
                    CheckForInvalidKeywords(g_names[child[1]._containedType])
            if isinstance(child[1], AsnMetaMember) and child[1]._containedType.lower() == child[0].lower():
                utility.panic(
                    "Ada mappers won't allow SEQUENCE/CHOICE fields with same names as their types.\n" +
                    "Fix declaration at %s" % node.Location())
    elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
        if isinstance(node._containedType, str):
            if IsInvalidType(node._containedType):
                utility.panic(
                    "TASTE disallows certain type names for various reasons.\n" +
                    "Invalid type name '%s' used in type defined in %s" % (node._containedType, node.Location()))
            if node._containedType not in g_checkedSoFarForKeywords:
                g_checkedSoFarForKeywords[node._containedType] = 1
                CheckForInvalidKeywords(g_names[node._containedType])


def ParseAsnFileList(listOfFilenames):
    asn1SccPath = spawn.find_executable('asn1.exe')
    if asn1SccPath is None:
        utility.panic("ASN1SCC seems not installed on your system (asn1.exe not found in PATH).\n")
    else:
        (dummy, xmlAST) = tempfile.mkstemp()
        os.fdopen(dummy).close()
        # spawnResult = os.system("mono \""+asn1SccPath+"\" -ast \""+xmlAST+"\" \"" + "\" \"".join(listOfFilenames) + "\"")
        asn1SccDir = os.path.dirname(os.path.abspath(asn1SccPath))
        mono = "mono " if sys.argv[0].endswith('.py') and sys.platform.startswith('linux') else ""
        spawnResult = os.system(mono + "\"" + asn1SccPath + "\" -customStg \"" + asn1SccDir + "/xml.stg:" + xmlAST + "\" -customStgAstVerion 4 \"" + "\" \"".join(listOfFilenames) + "\"")
        if spawnResult != 0:
            errCode = spawnResult/256
            if errCode == 1:
                utility.panic("ASN1SCC reported syntax errors. Aborting...")
            elif errCode == 2:
                utility.panic("ASN1SCC reported semantic errors (or mono failed). Aborting...")
            elif errCode == 3:
                utility.panic("ASN1SCC reported internal error. Contact Semantix with this input. Aborting...")
            elif errCode == 4:
                utility.panic("ASN1SCC reported usage error. Aborting...")
            else:
                utility.panic("ASN1SCC generic error. Contact Semantix with this input. Aborting...")
        ParseASN1SCC_AST(xmlAST)
        os.unlink(xmlAST)
        g_names.update(g_names)
        g_leafTypeDict.update(g_leafTypeDict)
        g_checkedSoFarForKeywords.update(g_checkedSoFarForKeywords)
        g_typesOfFile.update(g_typesOfFile)

        # We also need to mark the artificial types -
        # So spawn the custom type output at level 1 (unfiltered)
        # and mark any types not inside it as artificial.
        os.system(mono + "\"" + asn1SccPath + "\" -customStg \"" + asn1SccDir + "/xml.stg:" + xmlAST + "2\" -customStgAstVerion 1 \"" + "\" \"".join(listOfFilenames) + "\"")
        realTypes = {}
        for line in os.popen("grep  'ExportedType\>' \"" + xmlAST + "2\"").readlines():
            line = re.sub(r'^.*Name="', '', line.strip())
            line = re.sub(r'" />$', '', line)
            realTypes[line] = 1
        os.unlink(xmlAST + "2")
        for nodeTypename in list(g_names.keys()):
            if nodeTypename not in realTypes:
                g_names[nodeTypename]._isArtificial = True


def Dump():
    for nodeTypename in sorted(g_names.keys()):
        if g_names[nodeTypename]._isArtificial:
            continue
        print("\n===== From", g_names[nodeTypename]._asnFilename)
        print(nodeTypename)
        print("::", g_names[nodeTypename], g_leafTypeDict[nodeTypename])


def test_asn1():
    if "-debug" in sys.argv:
        configMT.debugParser = True
        sys.argv.remove("-debug")
    if len(sys.argv) < 2:
        sys.stderr.write('Usage: %s input.asn [input2.asn] ...\n' % sys.argv[0])
        sys.exit(1)
    for f in sys.argv[1:]:
        if not os.path.isfile(f):
            sys.stderr.write("'%s' is not a file!\n" % f)
            sys.exit(1)

    ParseAsnFileList(sys.argv[1:])
    Dump()


g_xmlASTrootNode = None

g_lineno = -1


class Element:
    def __init__(self, name, attrs):
        self._name = name
        self._attrs = attrs
        self._children = []  # type: List[Element]


class InputFormatXMLHandler(xml.sax.ContentHandler):
    def __init__(self, debug=False):
        xml.sax.ContentHandler.__init__(self)
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

    # def endElement(self, name):
    def endElement(self, _):
        if self._debug:
            if len(self._indent) > 4:  # pragma: no cover
                self._indent = self._indent[:len(self._indent) - 4]  # pragma: no cover
            # print self._indent + "(", name, ") ends" # pragma: no cover
        self._roots.pop()

# def Travel(indent, node):
#     print indent + node._name, ",".join(node._attrs.keys())
#     for c in node._children:
#        Travel(indent+"    ", c)


def VisitAll(node, expectedType, Action):
    results = []  # type: List[Any]
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
                result += chr(27) + "[32m" + i + chr(27) + "[0m:"  # pragma: no cover
                result += repr(getattr(self, i))  # pragma: no cover
                result += "\n"  # pragma: no cover
        return result  # pragma: no cover


# def CreateBoolean(newModule, lineNo, xmlBooleanNode):
def CreateBoolean(newModule, lineNo, _):
    return AsnBool(
        asnFilename=newModule._asnFilename,
        lineno=lineNo)


def GetRange(newModule, lineNo, nodeWithMinAndMax, valueType):
    try:
        mmin = GetAttr(nodeWithMinAndMax, "Min")
        # rangel = ( mmin == "MIN" ) and -2147483648L or valueType(mmin)
        if mmin == "MIN":
            utility.panic("You missed a range specification, or used MIN/MAX (line %s)" % lineNo)  # pragma: no cover
        rangel = valueType(mmin)
        mmax = GetAttr(nodeWithMinAndMax, "Max")
        # rangeh = ( mmax == "MAX" ) and 2147483647L or valueType(mmax)
        if mmax == "MAX":
            utility.panic("You missed a range specification, or used MIN/MAX (line %s)" % lineNo)  # pragma: no cover
        rangeh = valueType(mmax)
    except:  # pragma: no cover
        descr = {int: "integer", float: "floating point"}  # pragma: no cover
        utility.panic("Expecting %s value ranges (%s, %s)" %  # pragma: no cover
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
    # bSetIntValue = True
    # if GetAttr(xmlEnumeratedNode, "ValuesAutoCalculated") == "True":
    #    bSetIntValue = False
    return AsnEnumerated(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        members=VisitAll(
            xmlEnumeratedNode,
            "EnumValue",
            # lambda x: [GetAttr(x, "StringValue"), GetAttr(x, "IntValue"), GetAttr(x, "EnumID")]))
            #  old code: used to check the ValuesAutoCalculated and use None for the integer values
            # lambda x: [GetAttr(x, "StringValue"), bSetIntValue and GetAttr(x, "IntValue") or None]))
            lambda x: [GetAttr(x, "StringValue"), GetAttr(x, "IntValue")]))


# def CreateBitString(newModule, lineNo, xmlBitString):
def CreateBitString(_, __, ___):
    utility.panic("BitString type is not supported by the toolchain. "  # pragma: no cover
                  "Please use SEQUENCE OF BOOLEAN")  # pragma: no cover


def CreateOctetString(newModule, lineNo, xmlOctetString):
    return AsnOctetString(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        range=GetRange(newModule, lineNo, xmlOctetString, int))


def CreateIA5String(newModule, lineNo, xmlIA5StringNode):
    # utility.panic("IA5Strings are supported by ASN1SCC, but are not supported yet " # pragma: no cover
    #               "by the toolchain. Please use OCTET STRING") # pragma: no cover
    # return CreateOctetString(newModule, lineNo, xmlIA5StringNode)
    return AsnAsciiString(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        range=GetRange(newModule, lineNo, xmlIA5StringNode, int))


def CreateNumericString(newModule, lineNo, xmlNumericStringNode):
    return CreateOctetString(newModule, lineNo, xmlNumericStringNode)  # pragma: no cover


def CreateReference(newModule, lineNo, xmlReferenceNode):
    try:
        mi = int(GetAttr(xmlReferenceNode, "Min"))  # type: Union[int, float]
    except:
        try:
            mi = float(GetAttr(xmlReferenceNode, "Min"))
        except:
            mi = None
    try:
        ma = int(GetAttr(xmlReferenceNode, "Max"))  # type: Union[int, float]
    except:
        try:
            ma = float(GetAttr(xmlReferenceNode, "Max"))
        except:
            ma = None
    return AsnMetaType(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        containedType=GetAttr(xmlReferenceNode, "ReferencedTypeName"),
        Min=mi, Max=ma)


def CommonSetSeqOf(newModule, lineNo, xmlSequenceOfNode, classToCreate):
    xmlType = GetChild(xmlSequenceOfNode, "Type")
    if xmlType is None:
        utility.panic("CommonSetSeqOf: No child under SequenceOfType (%s, %s)" %  # pragma: no cover
                      (newModule._asnFilename, lineNo))  # pragma: no cover
    if len(xmlType._children) == 0:
        utility.panic("CommonSetSeqOf: No children for Type (%s, %s)" %  # pragma: no cover
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
    # if len(xmlSequenceNode._children) == 0:
    #     utility.panic("CommonSeqSetChoice: No children under Sequence/Choice/SetType (%s, %s)" %  # pragma: no cover
    #           (newModule._asnFilename, lineNo))  # pragma: no cover

    myMembers = []
    for x in xmlSequenceNode._children:
        if x._name == childTypeName:
            opti = GetAttr(x, "Optional")
            if opti and opti == "True":
                utility.warn("OPTIONAL attribute ignored (for field contained in %s,%s)" % (newModule._asnFilename, lineNo))
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
        utility.panic("GenericFactory: No children for Type (%s, %s)" %  # pragma: no cover
                      (newModule._asnFilename, lineNo))  # pragma: no cover
    xmlContainedType = xmlType._children[0]
    if xmlContainedType._name not in list(Factories.keys()):
        utility.panic("Unsupported XML type node: '%s' (%s, %s)" %  # pragma: no cover
                      (xmlContainedType._name, newModule._asnFilename, lineNo))  # pragma: no cover
    return Factories[xmlContainedType._name](
        newModule, lineNo, xmlContainedType)


def VisitTypeAssignment(newModule, xmlTypeAssignment):
    xmlType = GetChild(xmlTypeAssignment, "Type")
    if xmlType is None:
        utility.panic("VisitTypeAssignment: No child under TypeAssignment")  # pragma: no cover
    return (
        GetAttr(xmlTypeAssignment, "Name"),
        GenericFactory(newModule, xmlType))


class Module(Pretty):
    _id = None                 # type: str
    _asnFilename = None        # type: str
    _exportedTypes = None      # type: List[str]
    _exportedVariables = None  # type: List[str]
    _importedModules = None    # type: List[ Tuple[ str, List[str], List[str] ] ]
                               # (tuples of ModuleName, imported types, imported vars)
    _typeAssignments = None    # type: List[ Tuple[str, AsnNode] ]
    pass


def VisitAsn1Module(xmlAsn1File, xmlModule, modules):
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

    g_typesOfFile.setdefault(newModule._asnFilename, [])
    g_typesOfFile[newModule._asnFilename].extend(
        [x for x, _ in newModule._typeAssignments])

    g_astOfFile.setdefault(newModule._asnFilename, [])
    g_astOfFile[newModule._asnFilename].extend(
        [y for _, y in newModule._typeAssignments])

    modules.append(newModule)


def ParseASN1SCC_AST(filename):
    parser = xml.sax.make_parser()
    handler = InputFormatXMLHandler()
    parser.setContentHandler(handler)
    # parser.setFeature("http://xml.org/sax/features/validation", True)
    parser.parse(filename)

    if len(handler._root._children) != 1 or handler._root._children[0]._name != "ASN1AST":
        utility.panic("You must use an XML file that contains one ASN1AST node")  # pragma: no cover

    # Travel("", handler._roots[0])
    modules = []  # type: List[Module]
    VisitAll(
        handler._root._children[0],
        "Asn1File",
        lambda x: VisitAll(
            x,
            "Asn1Module",
            lambda y: VisitAsn1Module(x, y, modules)))

    global g_xmlASTrootNode
    g_xmlASTrootNode = handler._root

    global g_names
    g_names = {}
    global g_checkedSoFarForKeywords
    g_checkedSoFarForKeywords = {}
    global g_leafTypeDict
    g_leafTypeDict = {}

    for m in modules:
        # print "Module", m._id
        for typeName, typeData in m._typeAssignments:
            # print "Type:", typeName
            g_names[typeName] = typeData
    g_leafTypeDict.update(VerifyAndFixAST())

    for nodeTypename in list(g_names.keys()):
        if nodeTypename not in g_checkedSoFarForKeywords:
            g_checkedSoFarForKeywords[nodeTypename] = 1
            CheckForInvalidKeywords(nodeTypename)


def SimpleCleaner(x):
    return re.sub(r'[^a-zA-Z0-9_]', '_', x)


def PrintType(f, xmlType, indent, nameCleaner):
    if len(xmlType._children) == 0:
        utility.panic("AST inconsistency: xmlType._children == 0\nContact ESA")  # pragma: no cover
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
        utility.panic("BIT STRINGs are not supported, use SEQUENCE OF BOOLEAN")  # pragma: no cover
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
        if len(options) > 0:
            f.write(indent + '    ' + nameCleaner(GetAttr(options[0], "StringValue")) + "(" + GetAttr(options[0], "IntValue") + ")")
            for otherOptions in options[1:]:
                f.write(',\n' + indent + '    ' + nameCleaner(GetAttr(otherOptions, "StringValue")) + "(" + GetAttr(otherOptions, "IntValue") + ")")
        f.write('\n' + indent + '}')
    elif realType._name == "SequenceType" or realType._name == "SetType":
        if realType._name == "SequenceType":
            f.write('SEQUENCE {\n')
        else:
            f.write('SET {\n')
        if len(realType._children) > 0:
            f.write(indent + '    ' + nameCleaner(GetAttr(realType._children[0], "VarName")) + "\t")
            firstChildOptional = GetAttr(realType._children[0], "Optional") == "True"
            if len(realType._children[0]._children) == 0:
                utility.panic("AST inconsistency: len(realType._children[0]._children) = 0\nContact ESA")  # pragma: no cover
            PrintType(f, realType._children[0]._children[0], indent + "    ", nameCleaner)  # the contained type of the first child
            if firstChildOptional:
                f.write(' OPTIONAL')
            for sequenceOrSetChild in realType._children[1:]:
                f.write(",\n" + indent + '    ' + nameCleaner(GetAttr(sequenceOrSetChild, "VarName")) + "\t")
                childOptional = GetAttr(sequenceOrSetChild, "Optional") == "True"
                if len(sequenceOrSetChild._children) == 0:
                    utility.panic("AST inconsistency: len(sequenceOrSetChild._children) = 0\nContact ESA")  # pragma: no cover
                PrintType(f, sequenceOrSetChild._children[0], indent + "    ", nameCleaner)  # the contained type
                if childOptional:
                    f.write(' OPTIONAL')
#       else:
#           utility.panic("AST inconsistency: len(realType._children)=0\nContact ESA")  # pragma: no cover
        f.write('\n' + indent + '}')
    elif realType._name == "ChoiceType":
        f.write('CHOICE {\n')
        if len(realType._children) > 0:
            f.write(indent + '    ' + nameCleaner(GetAttr(realType._children[0], "VarName")) + "\t")
            if len(realType._children[0]._children) == 0:
                utility.panic("AST inconsistency: len(realType._children[0]._children) = 0\nContact ESA")  # pragma: no cover
            PrintType(f, realType._children[0]._children[0], indent + "    ", nameCleaner)  # the contained type of the first child
            for choiceChild in realType._children[1:]:
                f.write(",\n" + indent + '    ' + nameCleaner(GetAttr(choiceChild, "VarName")) + "\t")
                if len(choiceChild._children) == 0:
                    utility.panic("AST inconsistency: len(choiceChild._children) = 0\nContact ESA")  # pragma: no cover
                PrintType(f, choiceChild._children[0], indent + "    ", nameCleaner)  # the contained type
        else:
            utility.panic("AST inconsistency: len(realType._children)=0\nContact ESA")  # pragma: no cover
        f.write('\n' + indent + '}')
    elif realType._name == "SequenceOfType":
        f.write('SEQUENCE')
        mmin = GetAttr(realType, "Min")
        mmax = GetAttr(realType, "Max")
        f.write(' (SIZE (%s .. %s)) OF ' % (mmin, mmax))
        if len(realType._children) > 0:
            PrintType(f, realType._children[0], indent + "    ", nameCleaner)  # the contained type
        else:
            utility.panic("AST inconsistency: len(realType._children)=0\nContact ESA")  # pragma: no cover
    elif realType._name == "SetOfType":
        f.write('SET')
        mmin = GetAttr(realType, "Min")
        mmax = GetAttr(realType, "Max")
        f.write(' (SIZE (%s .. %s)) OF ' % (mmin, mmax))
        if len(realType._children) > 0:
            PrintType(f, realType._children[0], indent + "    ", nameCleaner)  # the contained type
        else:
            utility.panic("AST inconsistency: len(realType._children)=0\nContact ESA")  # pragma: no cover
    else:
        utility.panic("AST inconsistency: Unknown type (%s)\nContact ESA" % realType._name)  # pragma: no cover


def PrintGrammarFromAST(f, nameCleaner=SimpleCleaner):
    ourtypeAssignments = []
    VisitAll(
        g_xmlASTrootNode._children[0],
        "Asn1File",
        lambda x: VisitAll(
            x,
            "TypeAssignment",
            lambda y: ourtypeAssignments.append((x, y))))

    for a, t in ourtypeAssignments:
        f.write("-- " + GetAttr(a, "FileName") + "\n%s ::= " % nameCleaner(GetAttr(t, "Name")))
        typeChild = GetChild(t, "Type")
        if typeChild:
            PrintType(f, typeChild, '', nameCleaner)
            f.write('\n\n')
        else:
            utility.panic("AST inconsistency: typeChild is None\nContact ESA")  # pragma: no cover


def PrintGrammarFromASTtoStdOut():
    # Starting from the xmlASTrootNode, recurse and print the ASN.1 grammar
    PrintGrammarFromAST(sys.stdout)


def test_xml():
    if len(sys.argv) != 2 or not os.path.isfile(sys.argv[1]):
        sys.stderr.write("Missing or invalid path provided!\n")
        sys.exit(1)

    ParseASN1SCC_AST(sys.argv[1])
    Dump()
    print("\nRe-created grammar:\n\n")
    PrintGrammarFromASTtoStdOut()

if __name__ == "__main__":
    if "-testXML" in sys.argv:
        sys.argv.remove("-testXML")
        test_xml()
    elif "-testASN1" in sys.argv:
        sys.argv.remove("-testASN1")
        test_asn1()
