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

from typing import Union, Dict

from . import configMT
from . import utility

from .asnAST import *
from . import xmlASTtoAsnAST


g_asnFilename = ""

g_filename = ''
g_leafTypeDict = {}
g_names = {}  # type: Dict[str, AsnNode]
g_metatypes = {}

g_typesOfFile = {}  # type: Dict[str, List[str]]
g_astOfFile = {}  # type: Dict[str, List[AsnNode]]

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
    if isinstance(node, str):
        utility.panic("Referenced type (%s) does not exist!\n" % node)
    if isinstance(node, AsnBasicNode):
        return True
    elif isinstance(node, AsnEnumerated):
        return True
    elif isinstance(node, AsnSequence) or isinstance(node, AsnChoice) or isinstance(node, AsnSet):
        for x in node._members:
            if not KnownType(x[1], names):
                return False
        return True
    elif isinstance(node, AsnMetaMember):
        return KnownType(names.get(node._containedType, node._containedType), names)
    elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
        if isinstance(node._containedType, str):
            return KnownType(names.get(node._containedType, node._containedType), names)
        else:
            return KnownType(node._containedType, names)
    elif isinstance(node, AsnMetaType):
        return KnownType(names.get(node._containedType, node._containedType), names)
    else:
        return utility.panic("Unknown node type (%s)!\n" % str(node))


def CleanNameForAST(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def VerifyAndFixAST():
    '''\
Check that all types are defined and not missing.
It returns a map providing the leafType of each type.
'''
    unknownTypes = {}
    knownTypes = {}
    equivalents = {}
    while True:
        lastUnknownTypes = copy.copy(unknownTypes)
        lastKnownTypes = copy.copy(knownTypes)
        lastEquivalents = copy.copy(equivalents)
        for nodeTypename in list(g_names.keys()):

            node = g_names[nodeTypename]

            # AsnMetaMembers can only appear inside SEQUENCEs and CHOICEs,
            # not at the top level!
            assert (not isinstance(node, AsnMetaMember))

            #print node
            #print "Knowntypes:"
            #print knownTypes
            #print

            # Type level typedefs are stored in the equivalents dictionary
            if isinstance(node, AsnMetaType):
                # A ::= B
                # A and B are nodeTypename  and  node._containedType
                equivalents.setdefault(node._containedType, [])
                # Add A to the list of types that are equivalent to B
                equivalents[node._containedType].append(nodeTypename)
                # and if we know B's leafType, then we also know A's
                if node._containedType in knownTypes:
                    knownTypes[nodeTypename]=node._containedType
                else:
                    unknownTypes[nodeTypename]=1
            # AsnBasicNode type assignments are also equivalents
            elif isinstance(node, AsnBasicNode):
                # node._leafType is one of BOOLEAN, OCTET STRING, INTEGER, etc
                equivalents.setdefault(node._leafType, [])
                equivalents[node._leafType].append(nodeTypename)
                knownTypes[nodeTypename]=node._leafType
            # AsnEnumerated types are known types - they don't have external refs
            elif isinstance(node, AsnEnumerated):
                # node._leafType is ENUMERATED
                knownTypes[nodeTypename]=node._leafType
            # SEQUENCEs and CHOICEs: check their children for unknown AsnMetaMembers
            elif isinstance(node, AsnSequence) or isinstance(node, AsnChoice) or isinstance(node, AsnSet):
                bFoundUnknown = False
                for x in node._members:
                    if isinstance(x[1], AsnMetaMember) and x[1]._containedType not in knownTypes:
                        bFoundUnknown = True
                        break
                if bFoundUnknown:
                    unknownTypes[nodeTypename]=1
                else:
                    # node._leafType is SEQUENCE or CHOICE
                    knownTypes[nodeTypename]=node._leafType
            # SEQUENCE OFs: check their contained type
            elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
                if node._containedType in knownTypes or isinstance(node._containedType, AsnBasicNode):
                    knownTypes[nodeTypename]=node._leafType
                elif isinstance(node._containedType, AsnComplexNode):
                    knownTypes[nodeTypename]=node._leafType
                else:
                    unknownTypes[nodeTypename]=1

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
                        if seed!=knownTypes[seed]:
                            seed=knownTypes[seed]
                        else:
                            break
                    # and update knownTypes dictionary to contain leafType
                    knownTypes[alsoKnown]=seed

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
            Min = node._Min
        if hasattr(node, "_Max") and Max is None:
            Max = node._Max
        originalNode = node
        while isinstance(node, AsnMetaType):
            g_metatypes[nodeTypename] = node._containedType
            node = g_names[node._containedType]
            if hasattr(node, "_Min") and Min is None:
                Min = node._Min
            if hasattr(node, "_Max") and Max is None:
                Max = node._Max
        # To cope with ReferenceTypes that redefine their
        # constraints (for now, ASN1SCC provides only INTEGERs)
        if isinstance(originalNode, AsnMetaType):
            target = copy.copy(node)  # we need to keep the _asnFilename
            target._asnFilename = originalNode._asnFilename
        elif isinstance(node, AsnInt) and Min is not None and Max is not None:
            target = copy.copy(node)  # we need to keep the Min/Max
        else:
            target = node

        g_names[nodeTypename] = target
        if isinstance(node, AsnInt) and Min is not None and Max is not None:
            target._range = [Min, Max]

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
    while addedNewPseudoType:
        addedNewPseudoType = False
        listOfTypenames = sorted(g_names.keys())
        for nodeTypename in listOfTypenames:
            node = g_names[nodeTypename]
            if isinstance(node, AsnChoice) or isinstance(node, AsnSequence) or isinstance(node, AsnSet):
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
            elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
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
                    g_checkedSoFarForKeywords[child[1]._containedType]=1
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
                g_checkedSoFarForKeywords[node._containedType]=1
                CheckForInvalidKeywords(g_names[node._containedType])


def ParseAsnFileList(listOfFilenames):
    asn1SccPath = spawn.find_executable('asn1.exe')
    if asn1SccPath is None:
        utility.panic("ASN1SCC seems not installed on your system (asn1.exe not found in PATH).\n")
    else:
        (dummy, xmlAST) = tempfile.mkstemp()
        os.fdopen(dummy).close()
        #spawnResult = os.system("mono \""+asn1SccPath+"\" -ast \""+xmlAST+"\" \"" + "\" \"".join(listOfFilenames) + "\"")
        asn1SccDir = os.path.dirname(os.path.abspath(asn1SccPath))
        mono = "mono " if sys.argv[0].endswith('.py') and sys.platform.startswith('linux') else ""
        spawnResult = os.system(mono + "\""+asn1SccPath+"\" -customStg \""+asn1SccDir+"/xml.stg:"+xmlAST+"\" -customStgAstVerion 4 \"" + "\" \"".join(listOfFilenames) + "\"")
        if spawnResult != 0:
            if 1 == spawnResult/256:
                utility.panic("ASN1SCC reported syntax errors. Aborting...")
            elif 2 == spawnResult/256:
                utility.panic("ASN1SCC reported semantic errors (or mono failed). Aborting...")
            elif 3 == spawnResult/256:
                utility.panic("ASN1SCC reported internal error. Contact Semantix with this input. Aborting...")
            elif 4 == spawnResult/256:
                utility.panic("ASN1SCC reported usage error. Aborting...")
            else:
                utility.panic("ASN1SCC generic error. Contact Semantix with this input. Aborting...")
        xmlASTtoAsnAST.ParseASN1SCC_AST(xmlAST)
        os.unlink(xmlAST)
        g_names.update(xmlASTtoAsnAST.asnParser.g_names)
        g_leafTypeDict.update(xmlASTtoAsnAST.asnParser.g_leafTypeDict)
        g_checkedSoFarForKeywords.update(xmlASTtoAsnAST.asnParser.g_checkedSoFarForKeywords)
        g_typesOfFile.update(xmlASTtoAsnAST.asnParser.g_typesOfFile)

        # We also need to mark the artificial types - 
        # So spawn the custom type output at level 1 (unfiltered)
        # and mark any types not inside it as artificial.
        os.system(mono + "\""+asn1SccPath+"\" -customStg \""+asn1SccDir+"/xml.stg:"+xmlAST+"2\" -customStgAstVerion 1 \"" + "\" \"".join(listOfFilenames) + "\"")
        realTypes = {}
        for line in os.popen("grep  'ExportedType\>' \""+xmlAST+"2\"").readlines():
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


def main():
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

if __name__ == "__main__":
    if "-pdb" in sys.argv:
        sys.argv.remove("-pdb")
        import pdb
        pdb.run('main()')
    else:
        main()
