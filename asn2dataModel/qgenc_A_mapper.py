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
import re
import commonPy
from commonPy.utility import panic, inform
from commonPy.asnAST import AsnBool, AsnInt, AsnReal, AsnString, AsnEnumerated, AsnSequence, AsnSet, AsnChoice, AsnMetaMember, AsnSequenceOf, AsnSetOf
from .createInternalTypes import ScanChildren

# The file written to
g_outputFile = None

# A map of the ASN.1 types defined so far
g_definedTypes = {}

g_octetStrings = 0

g_bHasStartupRunOnce = False


def Version():
    print("Code generator: " + "$Id: qgenc_A_mapper.py $")  # pragma: no cover


def CleanNameAsSimulinkWants(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def OnStartup(unused_modelingLanguage, unused_asnFile, outputDir):
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
    inform("QGenC_A_mapper: Creating file '%s'...", outputFilename)
    global g_outputFile
    g_outputFile = open(outputDir + outputFilename, 'w')
    global g_definedTypes
    g_definedTypes = {}
    global g_octetStrings
    g_octetStrings = 0
    CreateDeclarationsForAllTypes(commonPy.asnParser.g_names, commonPy.asnParser.g_leafTypeDict)


def OnBasic(nodeTypename, node, leafTypeDict):
    pass


def OnSequence(nodeTypename, node, leafTypeDict):
    pass


def OnSet(nodeTypename, node, leafTypeDict):
    pass  # pragma: nocover


def OnEnumerated(nodeTypename, node, leafTypeDict):
    pass


def OnSequenceOf(nodeTypename, node, leafTypeDict):
    pass


def OnSetOf(nodeTypename, node, leafTypeDict):
    pass  # pragma: nocover


def OnChoice(nodeTypename, node, leafTypeDict):
    pass


def OnShutdown():
    pass


def MapInteger(node):
    if node._range[0]>=0 and node._range[1]<=255:
        return "uint8"
    elif node._range[0]>=-128 and node._range[1]<=127:
        return "int8"
    elif node._range[0]>=0 and node._range[1]<=65535:
        return "uint16"
    elif node._range[0]>=-32768 and node._range[1]<=32767:
        return "int16"
    elif node._range[0]>=0:
        return "uint32"
    else:
        return "int32"


def CreateAlias(nodeTypename, mappedType, description):
    # Requirements have changed: Simulink has an issue with AliasType...
    g_outputFile.write("%s = Simulink.AliasType;\n" % CleanNameAsSimulinkWants(nodeTypename))
    g_outputFile.write("%s.BaseType = '%s';\n" % (CleanNameAsSimulinkWants(nodeTypename), mappedType))
    g_outputFile.write("%s.Description = '%s';\n\n" % (CleanNameAsSimulinkWants(nodeTypename), description))
    return


def DeclareCollection(node, name, internal):
    for i in range(0, node._range[-1]):
        g_outputFile.write('%s_member_%02d=Simulink.BusElement;\n' % (name, i))
        # Andreas(ESA) wants them to be called 'element_%02d'
        g_outputFile.write("%s_member_%02d.name='element_%02d';\n" % (name, i, i))
        g_outputFile.write("%s_member_%02d.DataType='%s';\n" % (name, i, internal))
        g_outputFile.write("%s_member_%02d.dimensions=1;\n\n" % (name, i))
    g_outputFile.write('%s_member_length=Simulink.BusElement;\n' % name)
    g_outputFile.write("%s_member_length.name='length';\n" % (name))
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


def DeclareSimpleCollection(node, name, internal):
    g_outputFile.write('%s_member_data=Simulink.BusElement;\n' % name)
    g_outputFile.write("%s_member_data.name='element_data';\n" % name)
    g_outputFile.write("%s_member_data.DataType='%s';\n" % (name, internal))
    g_outputFile.write("%s_member_data.dimensions=%d;\n\n" % (name, node._range[-1]))

    bNeedLength = False
    if len(node._range)>1 and node._range[0]!=node._range[1]:
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


def CreateDeclarationForType(nodeTypename, names, leafTypeDict):
    if nodeTypename in g_definedTypes:
        return
    g_definedTypes[nodeTypename]=1
    results = []
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
        if node._range == []:
            panic("QGenC_A_mapper: string (in %s) must have a SIZE constraint!\n" % node.Location())  # pragma: no cover
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
                panic("QGenC_A_mapper: must have values for enumerants (%s)" % node.Location())  # pragma: no cover
        CreateAlias(nodeTypename, "int32", "values of ENUMERATED %s" % nodeTypename)
        g_outputFile.write("\n")
    elif isinstance(node, AsnSequence) or isinstance(node, AsnSet) or isinstance(node, AsnChoice):
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

                #mappedType = CleanNameAsSimulinkWants(child[1]._containedType + "_t") XYZ
                mappedType = CleanNameAsSimulinkWants(child[1]._containedType)
            else:  # pragma: no cover
                panic("QGenC_A_mapper: Unexpected category of child (%s)" % str(child[1]))  # pragma: no cover
            g_outputFile.write(name + ".DataType='%s';\n" % mappedType)
            # Used to be -1 for strings and metaMembers, but requirements have changed (again :-)
            g_outputFile.write(name + ".dimensions=1;\n\n")

        g_outputFile.write("%s = Simulink.Bus;\n" % CleanNameAsSimulinkWants(nodeTypename))
        g_outputFile.write("%s.Elements = " % CleanNameAsSimulinkWants(nodeTypename))
        if elemNo>1:
            g_outputFile.write('[')
        for i in range(0, elemNo):
            g_outputFile.write("%s_elem%02d " % (CleanNameAsSimulinkWants(nodeTypename), i+1))
        if elemNo>1:
            g_outputFile.write(']')
        g_outputFile.write(";\n\n")
    elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
        name = CleanNameAsSimulinkWants(nodeTypename)
        contained = node._containedType
        assert isinstance(contained, str)
        containedNode = contained
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
            panic("QGenC_A_mapper: Unexpected category of contained type (%s,%s)" % (node.Location(), str(contained)))  # pragma: no cover

    else:  # pragma: no cover
        panic("Unexpected ASN.1 type... Send this grammar to Semantix")  # pragma: no cover


def CreateDeclarationsForAllTypes(names, leafTypeDict):
    for nodeTypename in list(names.keys()):
        CreateDeclarationForType(nodeTypename, names, leafTypeDict)
