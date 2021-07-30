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
'''This contains the implementation of model level mapping
of ASN.1 constructs to SMP2 ones. It is used as a backend of Semantix's
code generator A.'''

import os
import re
import random

from typing import Dict, List, Set, IO, Any  # NOQA pylint: disable=unused-import

from ..commonPy.asnAST import AsnMetaMember, AsnChoice, AsnSet, AsnSequence, AsnSequenceOf, AsnSetOf, AsnBool, AsnInt, AsnReal, AsnOctetString
from ..commonPy.asnParser import g_names, g_leafTypeDict, CleanNameForAST
from ..commonPy.utility import panic, warn
from ..commonPy.cleanupNodes import SetOfBadTypenames
from ..commonPy.asnAST import AsnBasicNode, AsnSequenceOrSet, AsnSequenceOrSetOf, AsnEnumerated
from ..commonPy.asnParser import AST_Leaftypes

g_catalogueXML: IO[Any]
g_innerTypes = set()  # type: Set[str]
g_uniqueStringOfASN1files = ""
g_outputDir = "."
g_asnFiles: List[str]


def Version() -> None:
    print("Code generator: " + "$Id: smp2_A_mapper.py 1932 2010-06-15 13:41:15Z ttsiodras $")  # pragma: no cover


# noinspection PyDefaultArgument
def getUID(strIdentifier: str, idStore: Dict[str, str] = {}) -> str:  # pylint: disable=dangerous-default-value
    def h(digits: int) -> str:
        ret = ""
        for _ in range(0, digits):
            ret += random.choice('0123456789abcdef')
        return ret
    if strIdentifier not in idStore:
        idStore[strIdentifier] = h(8) + '-' + h(4) + '-' + h(4) + '-' + h(4) + '-' + h(12)
    return idStore[strIdentifier]


g_dependencyGraph = {}  # type: Dict[str, Dict[str, int]]


def FixupAstForSMP2() -> None:
    '''
    Find all the SEQUENCE, CHOICE and SEQUENCE OFs
    and make sure the contained types are not "naked" (i.e. unnamed)
    '''
    internalNo = 1

    def neededToAddPseudoType() -> bool:
        nonlocal internalNo
        addedNewPseudoType = False
        listOfTypenames = sorted(list(g_names.keys()) + list(g_innerTypes))
        for nodeTypename in listOfTypenames:
            node = g_names[nodeTypename]
            if isinstance(node, (AsnChoice, AsnSequence, AsnSet)):
                for child in node._members:
                    if not isinstance(child[1], AsnMetaMember):
                        internalName = newname = "TaStE_" + CleanNameForAST(child[0].capitalize() + "_type")
                        while internalName in g_names:
                            internalName = (newname + "_%d") % internalNo  # pragma: no cover
                            internalNo += 1                                # pragma: no cover
                        g_names[internalName] = child[1]
                        child[1]._isArtificial = True
                        g_leafTypeDict[internalName] = child[1]._leafType
                        child[1] = AsnMetaMember(asnFilename=child[1]._asnFilename, containedType=internalName)
                        addedNewPseudoType = True
                        g_innerTypes.add(internalName)
                        g_dependencyGraph.setdefault(nodeTypename, {})
                        g_dependencyGraph[nodeTypename][internalName] = 1
                    else:
                        g_dependencyGraph.setdefault(nodeTypename, {})
                        g_dependencyGraph[nodeTypename][child[1]._containedType] = 1
            elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
                if not isinstance(node._containedType, str):
                    internalName = newname = "TaStE_" + "internalSeqOf_type"
                    while internalName in g_names:
                        internalName = (newname + "_%d") % internalNo  # pragma: no cover
                        internalNo += 1                                # pragma: no cover
                    g_names[internalName] = node._containedType
                    node._containedType._isArtificial = True
                    g_leafTypeDict[internalName] = node._containedType._leafType
                    node._containedType = internalName
                    addedNewPseudoType = True
                    g_innerTypes.add(internalName)
                    g_dependencyGraph.setdefault(nodeTypename, {})
                    g_dependencyGraph[nodeTypename][internalName] = 1
                else:
                    g_dependencyGraph.setdefault(nodeTypename, {})
                    g_dependencyGraph[nodeTypename][node._containedType] = 1
        return addedNewPseudoType

    while True:
        if not neededToAddPseudoType():
            break


g_bStartupRun = False


def OnStartup(unused_modelingLanguage: str, asnFiles: List[str], outputDir: str, unused_badTypes: SetOfBadTypenames) -> None:  # pylint: disable=invalid-sequence-index
    '''
    Smp2 cannot represent constraint changes in unnamed inner types
    e.g. this...
        SEQUENCE (SIZE(20)) OF INTEGER (0 .. 12)
    ...would need the declaration of an "inner" type that would carry the constraint (0..12).

    We do this AST "fixup" with this function.
    '''
    global g_uniqueStringOfASN1files
    if isinstance(asnFiles, str):
        g_uniqueStringOfASN1files = CleanName(asnFiles.lower().replace(".asn1", "").replace(".asn", ""))  # pragma: nocover
    else:
        g_uniqueStringOfASN1files = "_".join(CleanName(x.lower().replace(".asn1", "").replace(".asn", "")) for x in asnFiles)
    global g_bStartupRun
    if g_bStartupRun:
        # Must run only once, no more.
        return  # pragma: no cover
    g_bStartupRun = True
    global g_outputDir
    g_outputDir = outputDir
    global g_asnFiles
    g_asnFiles = asnFiles
    FixupAstForSMP2()


def CleanName(fieldName: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', fieldName)


def OnBasic(unused_nodeTypename: str, unused_node: AsnBasicNode, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def CreateBasic(nodeTypename: str, node: AsnBasicNode, leafTypeDict: AST_Leaftypes) -> None:
    baseType = leafTypeDict[node._leafType]
    xsitype = {
        'INTEGER': 'Types:Integer',
        'REAL': 'Types:Float',
        'BOOLEAN': 'Types:Integer',
        'OCTET STRING': 'Types:Array'
    }[baseType]
    span = ""
    if isinstance(node, AsnBool):
        span = 'Minimum="0" Maximum="1"'
    elif isinstance(node, (AsnInt, AsnReal)) and node._range:
        span = 'Minimum="%s" Maximum="%s"' % (node._range[0], node._range[-1])
    elif isinstance(node, AsnOctetString):
        span = 'Size="%s"' % node._range[-1]
    uid = getUID(nodeTypename)
    d = {"uid": uid, "xsitype": xsitype, "name": CleanName(nodeTypename), "range": span}
    g_catalogueXML.write('    <Type xsi:type="%(xsitype)s" Id="ID_%(uid)s" Name="%(name)s" %(range)s>\n' % d)
    g_catalogueXML.write('      <Description>in file "%s", line: %s%s</Description>\n' %
                         (node._asnFilename, node._lineno, ", artificial" if node._isArtificial else ""))
    g_catalogueXML.write('      <Uuid>%s</Uuid>\n' % uid)
    nativeSMP2type = {
        'INTEGER': "Int64",
        'REAL': "Float64",
        'BOOLEAN': "UInt8",
        'OCTET STRING': 'UInt8'
    }[baseType]
    element = "ItemType" if baseType == "OCTET STRING" else "PrimitiveType"
    g_catalogueXML.write('      <%s xlink:title="PrimitiveType %s" xlink:href="http://www.esa.int/2005/10/Smp#%s" />\n' %
                         (element, nativeSMP2type, nativeSMP2type))
    g_catalogueXML.write('    </Type>\n')


def OnSequence(unused_nodeTypename: str, unused_node: AsnSequenceOrSet, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def CreateSequence(nodeTypename: str, node: AsnSequenceOrSet, unused_leafTypeDict: AST_Leaftypes) -> None:
    uid = getUID(nodeTypename)
    d = {"uid": uid, "name": CleanName(nodeTypename)}
    g_catalogueXML.write('    <Type xsi:type="Types:Structure" Id="ID_%(uid)s" Name="%(name)s">\n' % d)
    g_catalogueXML.write('      <Description>in file "%s", line: %s%s</Description>\n' %
                         (node._asnFilename, node._lineno, ", artificial" if node._isArtificial else ""))
    g_catalogueXML.write('      <Uuid>%s</Uuid>\n' % uid)
    for c in node._members:
        uidc = getUID(nodeTypename + c[0] + "_" + c[1]._containedType)
        g_catalogueXML.write('      <Field Id="ID_%s" Name="%s"  Visibility="public">\n' %
                             (uidc, CleanName(c[0]),))
        g_catalogueXML.write('        <Description></Description>\n')
        childNode = c[1]
        if isinstance(childNode, AsnMetaMember):
            g_catalogueXML.write('        <Type xlink:title="%s" xlink:href="#ID_%s"></Type>\n' %
                                 (CleanName(c[1]._containedType), getUID(c[1]._containedType)))
        else:  # pragma: no cover
            panic("Unexpected child node in SEQUENCE")  # pragma: no cover

        g_catalogueXML.write('      </Field>\n')
    g_catalogueXML.write('    </Type>\n')


def OnSet(unused_nodeTypename: str, unused_node: AsnSequenceOrSet, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnEnumerated(unused_nodeTypename: str, unused_node: AsnEnumerated, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def CreateEnumerated(nodeTypename: str, node: AsnEnumerated, unused_leafTypeDict: AST_Leaftypes) -> None:
    uid = getUID(nodeTypename)
    d = {"uid": uid, "name": CleanName(nodeTypename)}
    g_catalogueXML.write('    <Type xsi:type="Types:Enumeration" Id="ID_%(uid)s" Name="%(name)s">\n' % d)
    g_catalogueXML.write('      <Description>in file "%s", line: %s%s</Description>\n' %
                         (node._asnFilename, node._lineno, ", artificial" if node._isArtificial else ""))
    g_catalogueXML.write('      <Uuid>%s</Uuid>\n' % uid)
    for opt in node._members:
        uido = getUID(nodeTypename + "_option_" + opt[0])
        g_catalogueXML.write('      <Literal Name="%s" Value="%s" Id="ID_%s" />\n' %
                             (opt[0], opt[1], uido))
    # g_catalogueXML.write('      <NativeType xlink:href="http://www.esa.int/2005/10/Smp#%s" />\n' % nativeSMP2type)
    g_catalogueXML.write('    </Type>\n')


def OnSequenceOf(unused_nodeTypename: str, unused_node: AsnSequenceOrSetOf, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def CreateSequenceOf(nodeTypename: str, node: AsnSequenceOrSetOf, unused_leafTypeDict: AST_Leaftypes) -> None:
    uid = getUID(nodeTypename)
    d = {"uid": uid, "name": CleanName(nodeTypename), "sz": node._range[-1]}
    g_catalogueXML.write('    <Type xsi:type="Types:Array" Id="ID_%(uid)s" Name="%(name)s" Size="%(sz)s">\n' % d)
    g_catalogueXML.write('      <Description>in file "%s", line: %s%s</Description>\n' %
                         (node._asnFilename, node._lineno, ", artificial" if node._isArtificial else ""))
    g_catalogueXML.write('      <Uuid>%s</Uuid>\n' % uid)
    reftype = node._containedType
    if isinstance(reftype, str):
        g_catalogueXML.write('      <ItemType xlink:href="#ID_%s" />\n' % getUID(reftype))
    else:  # pragma: no cover
        panic("FixupAstForSMP2 failed to create a pseudoType for %s" % nodeTypename)  # pragma: no cover
#    elif isinstance(reftype, AsnBasicNode):
#        baseType = reftype._leafType
#        smpType = {
#            'INTEGER': 'Int64',
#            'REAL': 'Float64',
#            'BOOLEAN': 'Bool',
#            'OCTET STRING': 'String8'
#        }[baseType]
#        g_catalogueXML.write('      <ItemType xlink:title="PrimitiveType %s" xlink:href="http://www.esa.int/2005/10/Smp#%s" />\n' %
#            (smpType, smpType))
    g_catalogueXML.write('    </Type>\n')


def OnSetOf(unused_nodeTypename: str, unused_node: AsnSequenceOrSetOf, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnChoice(unused_nodeTypename: str, unused_node: AsnChoice, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def CreateChoice(nodeTypename: str, node: AsnChoice, _: AST_Leaftypes) -> None:
    uid = getUID(nodeTypename)
    d = {"uid": uid, "name": CleanName(nodeTypename)}
    g_catalogueXML.write('    <Type xsi:type="Types:Structure" Id="ID_%(uid)s" Name="%(name)s">\n' % d)
    g_catalogueXML.write('      <Description>in file "%s", line: %s%s</Description>\n' %
                         (node._asnFilename, node._lineno, ", artificial" if node._isArtificial else ""))
    g_catalogueXML.write('      <Uuid>%s</Uuid>\n' % uid)
    uidIdx = getUID(nodeTypename + "_choiceIndex")
    g_catalogueXML.write('      <Field Id="ID_%s" Name="choiceIdx" Visibility="public">\n' % uidIdx)
    g_catalogueXML.write('        <Description>CHOICE selector field</Description>\n')
    g_catalogueXML.write('        <Type xlink:title="PrimitiveType UInt8" xlink:href="http://www.esa.int/2005/10/Smp#UInt8"></Type>\n')
    g_catalogueXML.write('      </Field>\n')
    for c in node._members:
        uidc = getUID(nodeTypename + c[0] + "_" + c[1]._containedType)
        g_catalogueXML.write('      <Field Id="ID_%s" Name="%s"  Visibility="public">\n' %
                             (uidc, CleanName(c[0]),))
        g_catalogueXML.write('        <Description></Description>\n')
        childNode = c[1]
        if isinstance(childNode, AsnMetaMember):
            g_catalogueXML.write('        <Type xlink:title="%s" xlink:href="#ID_%s"></Type>\n' %
                                 (CleanName(c[1]._containedType), getUID(c[1]._containedType)))
        else:  # pragma: no cover
            panic("Unexpected child node in SEQUENCE")   # pragma: no cover
        g_catalogueXML.write('      </Field>\n')
    g_catalogueXML.write('    </Type>\n')


g_bShutdownRun = False


def OnShutdown(badTypes: SetOfBadTypenames) -> None:
    global g_bShutdownRun
    if g_bShutdownRun:
        return   # pragma: no cover
    g_bShutdownRun = True

    global g_catalogueXML
    g_catalogueXML = open(g_outputDir + os.sep + g_uniqueStringOfASN1files + ".cat", 'w')
    g_catalogueXML.write('''\
<?xml version="1.0" encoding="UTF-8"?>
<Catalogue:Catalogue xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:Catalogue="http://www.esa.int/2005/10/Smdl/Catalogue" xmlns:Types="http://www.esa.int/2005/10/Core/Types" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xsi:schemaLocation="http://www.esa.int/2005/10/Smdl/Catalogue Catalogue.xsd" Id="%(uniqid)s" Name="%(uniqid)s" Creator="taste" Date="2012-02-02T09:26:40.909Z" Version="1.0">
''' % {'uniqid': g_uniqueStringOfASN1files})
    g_catalogueXML.write('  <Description>Catalogue with types used in "%s"</Description>\n' %
                         (g_asnFiles if isinstance(g_asnFiles, str) else '","'.join(g_asnFiles)))
    g_catalogueXML.write('  <Namespace Id="ID_%s" Name="DataTypes">\n' % getUID("DataTypes"))
    g_catalogueXML.write('    <Description>Types used in "%s"</Description>\n' %
                         (g_asnFiles if isinstance(g_asnFiles, str) else '","'.join(g_asnFiles)))
    typenameList = []  # type: List[str]
    for nodeTypename in sorted(list(g_innerTypes) + list(g_names.keys())):
        if nodeTypename in badTypes:
            continue
        if nodeTypename not in typenameList:
            typenameList.append(nodeTypename)
    typesDoneSoFar = set()  # type: Set[str]

    workRemains = True
    while workRemains:
        workRemains = False
        for nodeTypename in typenameList:

            # only emit XML chunks for types with no more dependencies
            if nodeTypename in g_dependencyGraph and g_dependencyGraph[nodeTypename]:
                continue

            # only emit each type once
            if nodeTypename in typesDoneSoFar:
                continue
            typesDoneSoFar.add(nodeTypename)

            # if we process even one type, deps may be removed, so scan again next time
            workRemains = True

            # make sure we know what leaf type this node is
            node = g_names[nodeTypename]
            assert nodeTypename in g_leafTypeDict
            leafType = g_leafTypeDict[nodeTypename]
            if isinstance(node, AsnBasicNode):
                CreateBasic(nodeTypename, node, g_leafTypeDict)
            elif isinstance(node, (AsnSequence, AsnSet)):
                CreateSequence(nodeTypename, node, g_leafTypeDict)
            elif isinstance(node, AsnChoice):
                CreateChoice(nodeTypename, node, g_leafTypeDict)
            elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
                CreateSequenceOf(nodeTypename, node, g_leafTypeDict)
            elif isinstance(node, AsnEnumerated):
                CreateEnumerated(nodeTypename, node, g_leafTypeDict)
            else:  # pragma: no cover
                warn("Ignoring unsupported node type: %s (%s)" % (leafType, nodeTypename))  # pragma: no cover

            # eliminate nodeTypename from dependency lists
            for t in typenameList:
                if t in g_dependencyGraph and nodeTypename in g_dependencyGraph[t]:
                    del g_dependencyGraph[t][nodeTypename]

    g_catalogueXML.write("  </Namespace>\n")
    g_catalogueXML.write("</Catalogue:Catalogue>\n")
    g_catalogueXML.close()

    pkgFile = open(g_uniqueStringOfASN1files + '.pkg', 'w')
    pkgFile.write('''<?xml version="1.0" encoding="UTF-8"?>
<Package:Package xmlns:Package="http://www.esa.int/2005/10/Smdl/Package" xmlns:xlink="http://www.w3.org/1999/xlink" Id="%(uniqid)s" Name="%(uniqid)s" Creator="TASTE" Date="2012-06-27T00:00:00.000Z" Version="1.0">\n''' % {'uniqid': g_uniqueStringOfASN1files})

    for nodeTypename in typenameList:
        node = g_names[nodeTypename]
        uid = getUID(nodeTypename)
        leafType = g_leafTypeDict[nodeTypename]
        if leafType in ['BOOLEAN', 'INTEGER', 'REAL', 'OCTET STRING']:
            baseType = g_leafTypeDict[node._leafType]
            xsitype = {
                'INTEGER': 'Integer',
                'REAL': 'Float',
                'BOOLEAN': 'Integer',
                'OCTET STRING': 'Array'
            }[baseType]
        elif leafType in ['SEQUENCE', 'SET', 'CHOICE']:
            xsitype = 'Structure'
        elif leafType in ['SEQUENCEOF', 'SETOF']:
            xsitype = 'Array'
        elif leafType == 'ENUMERATED':
            xsitype = 'Enumeration'
        else:  # pragma: no cover
            warn("Ignoring unsupported node type: %s (%s)" % (leafType, nodeTypename))  # pragma: no cover
            continue
        d = {"uid": uid, "xsitype": xsitype, "name": CleanName(nodeTypename), 'uniqid': g_uniqueStringOfASN1files}
        pkgFile.write('    <Implementation Uuid="%(uid)s">\n' % d)
        pkgFile.write('       <Type xlink:title="%(xsitype)s %(name)s" xlink:href="%(uniqid)s.cat#ID_%(uid)s" />\n' % d)
        pkgFile.write('    </Implementation>\n')
    pkgFile.write('</Package:Package>')
    pkgFile.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
