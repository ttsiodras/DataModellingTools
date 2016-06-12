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
__doc__ = '''Implementation of mapping ASN.1 constructs
to SCADE's modeling language, using .xscade files. It is used by the
backend of Semantix's code generator A.'''

import re
import os
import random
from xml.dom.minidom import Document

from commonPy.utility import inform, panic
from commonPy.asnAST import AsnBasicNode, AsnString, AsnEnumerated, AsnMetaMember, AsnSet, AsnSetOf, AsnSequence, AsnSequenceOf, AsnChoice
import commonPy.asnParser

g_lookup = {
    "INTEGER": "int",
    "REAL": "real",
    "BOOLEAN": "bool"
}

# The file written to
g_outputFile = None

# The assigned OIDs
g_oid = {}

# The main OID for this module
g_mainOid = ""

# The counter for OIDs in this module
g_currOid = 0x1f00

# The types declared so far
g_declaredTypes = {}

# The DOM elements
g_doc = None
g_Declarations = None


def Version():
    print("Code generator: " + "$Id: scade612_A_mapper.py 1842 2010-03-10 14:16:42Z ttsiodras $")  # pragma: no cover


def CleanNameAsScadeWants(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def RandomHex(digits):
    result = ""
    for i in range(0, digits):
        result += random.choice('0123456789abcdef')
    return result


def FixupNestedStringsAndEnumerated():
    names = commonPy.asnParser.g_names
    leafTypeDict = commonPy.asnParser.g_leafTypeDict
    for nodeTypename in list(names.keys()):
        node = names[nodeTypename]
        if isinstance(node, AsnSequence) or isinstance(node, AsnChoice) or isinstance(node, AsnSet):
            for child in node._members:
                if isinstance(child[1], AsnString) or isinstance(child[1], AsnEnumerated):
                    newName = nodeTypename + "_" + child[0]                                                    # pragma: no cover
                    while newName in names:                                                                    # pragma: no cover
                        newName += "_t"                                                                        # pragma: no cover
                    names[newName] = child[1]                                                                  # pragma: no cover
                    leafTypeDict[newName] = isinstance(child[1], AsnString) and 'OCTET STRING' or 'ENUMERATED' # pragma: no cover
                    child[1] = AsnMetaMember(asnFilename=child[1]._asnFilename, containedType=newName)         # pragma: no cover
        elif isinstance(node, AsnSequenceOf) or isinstance(node, AsnSetOf):
            if isinstance(node._containedType, AsnString) or isinstance(node._containedType, AsnEnumerated):
                newName = nodeTypename + "_contained"                                                                 # pragma: no cover
                while newName in names:                                                                               # pragma: no cover
                    newName += "_t"                                                                                   # pragma: no cover
                names[newName] = node._containedType                                                                  # pragma: no cover
                leafTypeDict[newName] = isinstance(node._containedType, AsnString) and 'OCTET STRING' or 'ENUMERATED' # pragma: no cover
                node._containedType = newName                                                                         # pragma: no cover


def OnStartup(unused_modelingLanguage, asnFile, outputDir, unused_badTypes):
    outputFilename = CleanNameAsScadeWants(os.path.basename(os.path.splitext(asnFile)[0])) + ".xscade"

    FixupNestedStringsAndEnumerated()

    inform("Scade612_A_mapper: Creating file '%s'...", outputFilename)
    global g_outputFile
    g_outputFile = open(outputDir + outputFilename, 'wb')

    global g_mainOid
    g_mainOid = "/" + RandomHex(4) + "/" + RandomHex(3) + "/"

    global g_currOid
    g_currOid = 0x1f00

    global g_doc
    g_doc = Document()

    File = g_doc.createElement("File")
    File.setAttribute("xmlns", "http://www.esterel-technologies.com/ns/scade/3")
    File.setAttribute("xmlns:ed", "http://www.esterel-technologies.com/ns/scade/pragmas/editor/2")
    File.setAttribute("xmlns:kcg", "http://www.esterel-technologies.com/ns/scade/pragmas/codegen/1")
    g_doc.appendChild(File)

    global g_Declarations
    g_Declarations = g_doc.createElement("declarations")
    File.appendChild(g_Declarations)


def RenderElements(controlString):
    if controlString.endswith(","):
        controlString=controlString[:-1]
    createdElements = {}
    parent = g_Declarations
    for elem in controlString.split(","):
        if '`' in elem:
            element = elem.split("`")[0]
            under = elem.split("`")[1]
        else:
            element = elem
            under = None
        if '$' in element:
            data = element.split("$")
            finalElementName = data[0]
            attributes = data[1:]
        else:
            finalElementName = element
            attributes = []
        if finalElementName.startswith("TEXT"):
            newElement = g_doc.createTextNode(finalElementName[4:])
        else:
            newElement = g_doc.createElement(finalElementName)
        if attributes != []:
            for atr in attributes:
                newElement.setAttribute(atr.split('=')[0], atr.split('=')[1])
        if under is not None:
            parent = createdElements[under]
        parent.appendChild(newElement)
        createdElements[finalElementName] = newElement
        parent = newElement


def GetOID(nodeTypename):
    global g_currOid
    if nodeTypename not in g_oid:
        oid = hex(g_currOid)[2:] + g_mainOid + RandomHex(12)
        g_oid[nodeTypename] = oid
        g_currOid += 1
    else:                          # pragma: no cover
        oid = g_oid[nodeTypename]  # pragma: no cover
    return oid


def CheckPrerequisites(nodeTypename):
    names = commonPy.asnParser.g_names
    leafTypeDict = commonPy.asnParser.g_leafTypeDict
    if nodeTypename not in g_declaredTypes:
        node = names[nodeTypename]
        leafType = leafTypeDict[nodeTypename]
        # If it is a base type,
        if leafType in ['BOOLEAN', 'INTEGER', 'REAL', 'OCTET STRING']:
            OnBasic(nodeTypename, node, leafTypeDict)
        # if it is a complex type
        elif leafType in ['SEQUENCE', 'SET', 'CHOICE', 'SEQUENCEOF', 'SETOF', 'ENUMERATED']:
            # make sure we have mapping instructions for the element
            mappedName = {
                'SEQUENCE': 'OnSequence',
                'SET': 'OnSet',
                'CHOICE': 'OnChoice',
                'SEQUENCEOF': 'OnSequenceOf',
                'SETOF': 'OnSetOf',
                'ENUMERATED': 'OnEnumerated'
            }
            if mappedName[leafType] not in list(globals().keys()):
                panic("ASN.1 grammar contains %s but no %s section found in the backend! Contact Semantix." %  # pragma: no cover
                      (nodeTypename, mappedName[leafType]))  # pragma: no cover
            processor = globals()[mappedName[leafType]]
            processor(nodeTypename, node, leafTypeDict)
        # what type is this?
        else:  # pragma: no cover
            panic("Unexpected type of element: %s" % leafTypeDict[nodeTypename])  # pragma: no cover
        g_declaredTypes[nodeTypename] = True


def HandleTypedef(nodeTypename):
    if nodeTypename not in commonPy.asnParser.g_metatypes:
        return False
    controlString = 'Type$name=%s,definition,NamedType,type,TypeRef$name=%s' % \
        (CleanNameAsScadeWants(nodeTypename), CleanNameAsScadeWants(commonPy.asnParser.g_metatypes[nodeTypename]))
    RenderElements(controlString)
    return True


def OnBasic(nodeTypename, node, unused_leafTypeDict):
    assert(isinstance(node, AsnBasicNode))
    if nodeTypename in g_declaredTypes:
        return
    g_declaredTypes[nodeTypename] = 1
    if HandleTypedef(nodeTypename):
        return
    oid = GetOID(nodeTypename)

    # Make the type name SCADE-compliant
    nodeTypename = CleanNameAsScadeWants(nodeTypename)

    controlString = 'Type$name=%(nodeTypename)s,definition,' % {"nodeTypename": nodeTypename}

    # Check to see the real leaf type of this node
    if isinstance(node, AsnString):
        # An OCTET STRING must always include a range definition,
        # otherwise SCADE will not be able to create C code!
        if node._range == []:
            panic(("Scade612_A_mapper: string (in %s) must have a SIZE constraint inside ASN.1,\n" +  # pragma: no cover
                  "or else SCADE can't generate C code!") % node.Location())  # pragma: no cover
        controlString += 'Table,type,NamedType,type,TypeRef$name=char,size`Table,ConstValue$value=%d,' % node._range[-1]
    else:
        # For the rest of the simple types, use the lookup table defined in g_lookup
        realLeafType = node._leafType
        try:
            controlString += 'NamedType,type,TypeRef$name=%s,' % g_lookup[realLeafType]
        except KeyError:  # pragma: no cover
            panic("Scade612_A_mapper: Unsupported literal: %s (%s)\n" % (realLeafType, node.Location()))  # pragma: no cover

    controlString += 'pragmas`Type,ed:Type$oid=!ed/%(oid)s' % {"nodeTypename": nodeTypename, "oid": oid}
    RenderElements(controlString)


def OnSequence(nodeTypename, node, unused_leafTypeDict, isChoice=False):
    if nodeTypename in g_declaredTypes:
        return
    g_declaredTypes[nodeTypename] = 1
    if HandleTypedef(nodeTypename):
        return
    oid = GetOID(nodeTypename)
    controlString = 'Type$name=%s,definition,Struct,fields,' % CleanNameAsScadeWants(nodeTypename)
    if isChoice:
        controlString += 'Field$name=choiceIdx`fields,type,NamedType,type,TypeRef$name=int,'
    for child in node._members:
        realLeafType = child[1]._leafType
        controlString += 'Field$name=%s`fields,' % CleanNameAsScadeWants(child[0])
        if isinstance(node, AsnString):
            controlString += 'Table,type,NamedType,type,TypeRef$name=char,size`Table,ConstValue$value=%d,' % node._range[-1]  # pragma: no cover because of FixupNestedStringsAndEnumerated
        elif isinstance(child[1], AsnBasicNode):
            controlString += 'type,NamedType,type,TypeRef$name=%s,' % g_lookup[realLeafType]
        elif isinstance(child[1], AsnEnumerated):
            panic("Scade612_A_mapper: Don't use naked ENUMERATED in CHOICE/SEQUENCE, SCADE doesn't support them (%s)!\n" % node.Location())  # pragma: no cover because of FixupNestedStringsAndEnumerated
        elif isinstance(child[1], AsnMetaMember):
            CheckPrerequisites(child[1]._containedType)
            controlString += 'type,NamedType,type,TypeRef$name=%s,' % CleanNameAsScadeWants(child[1]._containedType)
        else:  # pragma: no cover
            panic("Scade612_A_mapper: Unexpected member %s (%s)!\n" % (child[0], node.Location()))  # pragma: no cover
        controlString += 'pragmas`Field,ed:Field$oid=!ed/%s,' % GetOID(nodeTypename + "_" + child[0])
    controlString += 'pragmas`Type,ed:Type$oid=!ed/%s,' % oid
    RenderElements(controlString)


def OnSet(nodeTypename, node, leafTypeDict):
    OnSequence(nodeTypename, node, leafTypeDict)  # pragma: nocover


def OnEnumerated(nodeTypename, node, unused_leafTypeDict):
    if nodeTypename in g_declaredTypes:
        return
    g_declaredTypes[nodeTypename] = 1
    if HandleTypedef(nodeTypename):
        return
    oid = GetOID(nodeTypename)
    controlString = 'Type$name=%(nodeTypename)s,definition,Enum,values,' % {"nodeTypename": CleanNameAsScadeWants(nodeTypename)}
    for member in node._members:
        # member[0] is the enumerant name
        # member[1] is the integer value used (or None)
        if member[1] is not None:
            # Alain, what do I need to do with pragmas here?
            # g_outputFile.write("\t    %s[%s]" % (CleanNameAsScadeWants(member[0]), member[1]))
            controlString += 'Value$name=%(enumerant)s`values,pragmas,ed:Value$oid=%(oid)s,kcg:Pragma`pragmas,TEXTenum_val %(value)s,' % {
                "enumerant": CleanNameAsScadeWants(member[0]),
                "oid": GetOID(nodeTypename+"_"+member[0]),
                "value": member[1]
            }
        else:  # pragma: no cover
            controlString += 'Value$name=%(enumerant)s`values,pragmas,ed:Value$oid=%(oid)s,' % \
                {  # pragma: no cover
                    "enumerant": CleanNameAsScadeWants(member[0]),  # pragma: no cover
                    "oid": GetOID(nodeTypename+"_"+member[0])  # pragma: no cover
                }  # pragma: no cover
    controlString += 'pragmas`Type,ed:Type$oid=!ed/%(oid)s' % {"oid": oid}
    RenderElements(controlString)


def OnSequenceOf(nodeTypename, node, unused_leafTypeDict):
    if nodeTypename in g_declaredTypes:
        return
    g_declaredTypes[nodeTypename] = 1
    if HandleTypedef(nodeTypename):
        return
    if node._range == []:
        panic("Scade612_A_mapper: must have a SIZE constraint or else SCADE can't generate C code (in %s)!\n" %  # pragma: no cover
              node.Location())  # pragma: no cover
    oid = GetOID(nodeTypename)
    controlString = 'Type$name=%s,definition,Table,type,NamedType,type,' % CleanNameAsScadeWants(nodeTypename)
    if isinstance(node._containedType, AsnBasicNode):
        controlString += 'TypeRef$name=%s,' % g_lookup[node._containedType._leafType]
    elif isinstance(node._containedType, AsnEnumerated):
        panic("Scade612_A_mapper: Don't use naked ENUMERATED in SEQUENCEOF, SCADE doesn't support them (%s)!\n" % node.Location())  # pragma: no cover because of FixupNestedStringsAndEnumerated
    elif isinstance(node._containedType, str):
        CheckPrerequisites(node._containedType)
        controlString += 'TypeRef$name=%s,' % CleanNameAsScadeWants(node._containedType)
    else:  # pragma: no cover
        panic("Scade612_A_mapper: Unexpected contained %s (%s)!\n" % (str(node._containedType), node.Location()))  # pragma: no cover
    controlString += 'size`Table,ConstValue$value=%s,' % node._range[-1]
    controlString += 'pragmas`Type,ed:Type$oid=!ed/%s' % oid
    RenderElements(controlString)


def OnSetOf(nodeTypename, node, leafTypeDict):
    OnSequenceOf(nodeTypename, node, leafTypeDict)  # pragma: nocover


def OnChoice(nodeTypename, node, leafTypeDict):
    OnSequence(nodeTypename, node, leafTypeDict, isChoice=True)


def OnShutdown(unused_badTypes):
    g_outputFile.write(g_doc.toprettyxml(indent="    ", encoding="UTF-8"))
