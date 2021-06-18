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
'''This contains the implementation of model level mapping
of ASN.1 constructs to C. It is used as a backend of Semantix's
code generator A.'''

import os
import sys
import re

from distutils import spawn
from typing import List, Union, Set, IO, Any  # NOQA

from ..commonPy import asnParser
from ..commonPy.utility import panic, inform
from ..commonPy.createInternalTypes import ScanChildren
from ..commonPy.cleanupNodes import SetOfBadTypenames
from ..commonPy.asnAST import (
    AsnBasicNode, AsnSequenceOrSet, AsnSequenceOrSetOf, AsnBool, AsnInt,
    AsnReal, AsnString, AsnEnumerated, AsnSequence, AsnSet, AsnChoice,
    AsnMetaMember, AsnSequenceOf, AsnSetOf)
from ..commonPy.asnAST import AsnNode  # NOQA pylint: disable=unused-import
from ..commonPy.asnParser import AST_Leaftypes, AST_Lookup

# The file written to
g_outputFile: IO[Any]

# A map of the ASN.1 types defined so far
g_definedTypes = set()  # type: Set[asnParser.Typename]

g_octetStrings = 0

g_bHasStartupRunOnce = False


def Version() -> None:
    print("Code generator: " + "$Id: qgenada_A_mapper.py $")  # pragma: no cover


def CleanNameAsSimulinkWants(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


# Especially for the C mapper, since we need to pass the complete ASN.1 files list to ASN1SCC,
# the second param is not asnFile, it is asnFiles

def OnStartup(unused_modelingLanguage: str, asnFiles: List[str], outputDir: str, unused_badTypes: SetOfBadTypenames) -> None:  # pylint: disable=invalid-sequence-index
    # print "Use ASN1SCC to generate the structures for '%s'" % asnFile
    asn1SccPath = spawn.find_executable('asn1scc')
    if not asn1SccPath:
        panic("ASN1SCC seems to be missing from your system (asn1scc not found in PATH).\n")  # pragma: no cover
    os.system(
        "\"{}\"  -typePrefix asn1Scc -c -uPER -o \"".format(asn1SccPath) +
        outputDir + "\" \"" + "\" \"".join(asnFiles) + "\"")
    os.system("rm -f \"" + outputDir + "\"/*.adb")

    global g_bHasStartupRunOnce
    if g_bHasStartupRunOnce:
        # Don't rerun, it has already done all the work
        # for all the ASN.1 files used
        return  # pragma: no cover
    else:
        g_bHasStartupRunOnce = True
    # outputFilename = modelingLanguage + "_" + os.path.basename(asnFile).replace(".","_") + ".m"
    # Changed at Maxime's request, 27/1/2011
    outputFilename = "Simulink_DataView_asn.m"
    inform("QGenAda_A_mapper: Creating file '%s'...", outputFilename)
    global g_outputFile
    outputDir += "../"
    g_outputFile = open(outputDir + outputFilename, 'w')
    g_definedTypes.clear()
    global g_octetStrings
    g_octetStrings = 0
    CreateDeclarationsForAllTypes(asnParser.g_names, asnParser.g_leafTypeDict)


def OnBasic(unused_nodeTypename: str, unused_node: AsnBasicNode, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: nocover


def OnSequence(unused_nodeTypename: str, unused_node: AsnSequenceOrSet, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: nocover


def OnSet(unused_nodeTypename: str, unused_node: AsnSequenceOrSet, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: nocover


def OnEnumerated(unused_nodeTypename: str, unused_node: AsnEnumerated, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: nocover


def OnSequenceOf(unused_nodeTypename: str, unused_node: AsnSequenceOrSetOf, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: nocover


def OnSetOf(unused_nodeTypename: str, unused_node: AsnSequenceOrSetOf, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: nocover


def OnChoice(unused_nodeTypename: str, unused_node: AsnChoice, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: nocover


def OnShutdown(unused_badTypes: SetOfBadTypenames) -> None:
    pass


def MapInteger(node: AsnInt) -> str:
    if node._range[0] >= 0 and node._range[1] <= 255:
        return "uint8"
    elif node._range[0] >= -128 and node._range[1] <= 127:
        return "int8"
    elif node._range[0] >= 0 and node._range[1] <= 65535:
        return "uint16"
    elif node._range[0] >= -32768 and node._range[1] <= 32767:
        return "int16"
    elif node._range[0] >= 0:
        return "uint32"
    else:
        return "int32"


def CreateAlias(nodeTypename: str, mappedType: str, description: str) -> None:
    # Requirements have changed: Simulink has an issue with AliasType...
    g_outputFile.write("%s = Simulink.AliasType;\n" % CleanNameAsSimulinkWants(nodeTypename))
    g_outputFile.write("%s.BaseType = '%s';\n" % (CleanNameAsSimulinkWants(nodeTypename), mappedType))
    g_outputFile.write("%s.Description = '%s';\n\n" % (CleanNameAsSimulinkWants(nodeTypename), description))


def DeclareCollection(node: AsnSequenceOrSetOf, name: str, internal: str) -> None:
    for i in range(0, node._range[-1]):
        g_outputFile.write('%s_member_%02d=Simulink.BusElement;\n' % (name, i))
        # Andreas(ESA) wants them to be called 'element_%02d'
        g_outputFile.write("%s_member_%02d.name='element_%02d';\n" % (name, i, i))
        g_outputFile.write("%s_member_%02d.DataType='%s';\n" % (name, i, internal))
        g_outputFile.write("%s_member_%02d.dimensions=1;\n\n" % (name, i))
    g_outputFile.write('%s_member_length=Simulink.BusElement;\n' % name)
    g_outputFile.write("%s_member_length.name='length';\n" % name)
    g_outputFile.write("%s_member_length.DataType='int32';\n" % name)
    g_outputFile.write("%s_member_length.dimensions=1;\n\n" % name)
    g_outputFile.write('%s=Simulink.Bus;\n' % name)
    g_outputFile.write("%s.Elements = " % name)
    g_outputFile.write('[')
    for i in range(0, node._range[-1]):
        g_outputFile.write("%s_member_%02d " % (name, i))
    g_outputFile.write('%s_member_length' % name)
    g_outputFile.write(']')
    g_outputFile.write(";\n\n")


def DeclareSimpleCollection(node: Union[AsnString, AsnSequenceOf, AsnSetOf], name: str, internal: str) -> None:
    g_outputFile.write('%s_member_data=Simulink.BusElement;\n' % name)
    g_outputFile.write("%s_member_data.name='element_data';\n" % name)
    g_outputFile.write("%s_member_data.DataType='%s';\n" % (name, internal))
    g_outputFile.write("%s_member_data.dimensions=%d;\n\n" % (name, node._range[-1]))

    bNeedLength = False
    if len(node._range) > 1 and node._range[0] != node._range[1]:
        bNeedLength = True

    if bNeedLength:
        g_outputFile.write('%s_member_length=Simulink.BusElement;\n' % name)
        g_outputFile.write("%s_member_length.name='length';\n" % name)
        g_outputFile.write("%s_member_length.DataType='int32';\n" % name)
        g_outputFile.write("%s_member_length.dimensions=1;\n\n" % name)

    g_outputFile.write('%s=Simulink.Bus;\n' % name)
    g_outputFile.write("%s.Elements = " % name)
    g_outputFile.write('[')
    g_outputFile.write("%s_member_data " % name)
    if bNeedLength:
        g_outputFile.write('%s_member_length' % name)
    g_outputFile.write(']')
    g_outputFile.write(";\n\n")


def CreateDeclarationForType(nodeTypename: str, names: AST_Lookup, leafTypeDict: AST_Leaftypes) -> None:
    if nodeTypename in g_definedTypes:
        return
    g_definedTypes.add(nodeTypename)
    results = []  # type: List[str]
    ScanChildren(nodeTypename, names[nodeTypename], names, results, isRoot=True, createInnerNodesInNames=True)
    inform("Prerequisites of %s", nodeTypename)
    for prereqNodeTypename in results:
        if prereqNodeTypename != '':
            inform("\t%s", prereqNodeTypename)
            CreateDeclarationForType(prereqNodeTypename, names, leafTypeDict)
    node = names[nodeTypename]
    if isinstance(node, AsnBool):
        CreateAlias(nodeTypename, "boolean", 'A simple BOOLEAN')
    elif isinstance(node, AsnInt):
        CreateAlias(nodeTypename, MapInteger(node), "range is %s" % str(node._range))
    elif isinstance(node, AsnReal):
        CreateAlias(nodeTypename, "double", "range is %s" % str(node._range))
    elif isinstance(node, AsnString):
        if not node._range:
            panic("QGenAda_A_mapper: string (in %s) must have a SIZE constraint!\n" % node.Location())  # pragma: no cover
        name = CleanNameAsSimulinkWants(nodeTypename)
        DeclareSimpleCollection(node, name, "uint8")
    elif isinstance(node, AsnEnumerated):
        g_outputFile.write("%% Values for %s:\n" % nodeTypename)
        for member in node._members:
            # member[0] is the enumerant name
            # member[1] is the integer value used (or None)
            if member[1] is not None:
                g_outputFile.write("%s_value_%s = %s;\n" % (CleanNameAsSimulinkWants(nodeTypename), CleanNameAsSimulinkWants(member[0]), member[1]))
            else:  # pragma: no cover
                panic("QGenAda_A_mapper: must have values for enumerants (%s)" % node.Location())  # pragma: no cover
        CreateAlias(nodeTypename, "int32", "values of ENUMERATED %s" % nodeTypename)
        g_outputFile.write("\n")
    elif isinstance(node, (AsnSequence, AsnSet, AsnChoice)):
        if not node._members:
            return
            # Ignore empty sequences in the A mapper, but do not raise an error, as empty sequences
            # may be used in other parts of the system.
            # panic("Simulink_A_mapper: Simulink can't support empty Seq/Set/Choice! (%s)" % node.Location())  # pragma: no cover
        elemNo = 0
        if isinstance(node, AsnChoice):
            elemNo += 1
            name = "%s_elem%02d" % (CleanNameAsSimulinkWants(nodeTypename), elemNo)
            g_outputFile.write(name + "=Simulink.BusElement;\n")
            g_outputFile.write(name + ".name='choiceIdx';\n")
            g_outputFile.write(name + ".DataType='uint8';\n")
            g_outputFile.write(name + ".dimensions=1;\n\n")
        for child in node._members:
            elemNo += 1
            name = "%s_elem%02d" % (CleanNameAsSimulinkWants(nodeTypename), elemNo)
            g_outputFile.write(name + "=Simulink.BusElement;\n")
            g_outputFile.write(name + ".name='%s';\n" % CleanNameAsSimulinkWants(child[0]))

            # Since AliasType doesn't work well in the Matlab/Simulink typesystem,
            # we have to change the simple fields to their native types.
            # Trace all the AsnMetaMember chain to find out the leaf type...
            childNode = child[1]
            while isinstance(childNode, AsnMetaMember):
                childNode = names[childNode._containedType]

            # Now that you have the leaf type, use the native types wherever possible.
            # BUT! For octet strings, we have pre-declared (see Dependencies definitions)
            # octet_string_%d types, but ONLY for native AsnString, not for typedef'd ones...
            if isinstance(childNode, AsnBool):
                mappedType = 'boolean'
            elif isinstance(childNode, AsnInt):
                mappedType = MapInteger(childNode)
            elif isinstance(childNode, AsnReal):
                mappedType = 'double'
            elif isinstance(childNode, AsnString):
                if isinstance(child[1], AsnMetaMember):
                    mappedType = CleanNameAsSimulinkWants(child[1]._containedType)
                else:                                  # pragma: no cover
                    mappedType = child[1]._pseudoname  # pragma: no cover
            elif isinstance(childNode, AsnEnumerated):
                mappedType = 'int32'
            # These would not be possible: AsnSequence, AsnChoice, AsnSequenceOf,
            # since the parsing stage ends with automated pseudonames (through
            # AsnMetaMembers) for them. However, we resolve AsnMetaMembers in the
            # "while" above, so if we do meet one of them (now that the resolving
            # has been done), we must have started from an AsnMetaMember...
            # so we will use the containedType_t for reference.
            elif isinstance(childNode, (AsnSequence, AsnSequenceOf, AsnSet, AsnSetOf, AsnChoice)):

                # mappedType = CleanNameAsSimulinkWants(child[1]._containedType + "_t") XYZ
                mappedType = CleanNameAsSimulinkWants(child[1]._containedType)
            else:  # pragma: no cover
                panic("QGenAda_A_mapper: Unexpected category of child (%s)" % str(child[1]))  # pragma: no cover
            g_outputFile.write(name + ".DataType='%s';\n" % mappedType)
            # Used to be -1 for strings and metaMembers, but requirements have changed (again :-)
            g_outputFile.write(name + ".dimensions=1;\n\n")

        g_outputFile.write("%s = Simulink.Bus;\n" % CleanNameAsSimulinkWants(nodeTypename))
        g_outputFile.write("%s.Elements = " % CleanNameAsSimulinkWants(nodeTypename))
        if elemNo > 1:
            g_outputFile.write('[')
        for i in range(0, elemNo):
            g_outputFile.write("%s_elem%02d " % (CleanNameAsSimulinkWants(nodeTypename), i + 1))
        if elemNo > 1:
            g_outputFile.write(']')
        g_outputFile.write(";\n\n")
    elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
        name = CleanNameAsSimulinkWants(nodeTypename)
        contained = node._containedType
        assert isinstance(contained, str)
        containedNode = contained  # type: Union[AsnNode, str]
        while isinstance(containedNode, str):
            containedNode = names[containedNode]
        if isinstance(containedNode, AsnBool):
            DeclareSimpleCollection(node, name, 'boolean')
        elif isinstance(containedNode, AsnInt):
            DeclareSimpleCollection(node, name, MapInteger(containedNode))
        elif isinstance(containedNode, AsnReal):
            DeclareSimpleCollection(node, name, 'double')
        elif isinstance(containedNode, AsnString):
            DeclareCollection(node, name, CleanNameAsSimulinkWants(contained))
        elif isinstance(containedNode, AsnEnumerated):
            DeclareSimpleCollection(node, name, 'int32')
        # These are not possible: AsnSequence, AsnChoice, AsnSequenceOf, because we introduce
        # AsnMetaMember for them at the end of the parser. If we meet them here, it is
        # because resolving has been done (see while above), so we started from a string...
        elif isinstance(containedNode, (AsnSequence, AsnSequenceOf, AsnSet, AsnSetOf, AsnChoice)):

            DeclareCollection(node, name, CleanNameAsSimulinkWants(contained))
        else:  # pragma: no cover
            panic("QGenAda_A_mapper: Unexpected category of contained type (%s,%s)" % (node.Location(), str(contained)))  # pragma: no cover

    else:  # pragma: no cover
        panic("Unexpected ASN.1 type... Send this grammar to Semantix")  # pragma: no cover


def CreateDeclarationsForAllTypes(names: AST_Lookup, leafTypeDict: AST_Leaftypes) -> None:
    for nodeTypename in list(names.keys()):
        CreateDeclarationForType(nodeTypename, names, leafTypeDict)
