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
of ASN.1 constructs to SQL ones. It is used as a backend of Semantix's
code generator A.'''

import os
import re

from typing import List, Union, Set, IO, Any, Dict  # NOQA pylint: disable=unused-import

from ..commonPy.asnAST import (
    AsnMetaMember, AsnChoice, AsnSet, AsnSequence, AsnSequenceOf, AsnSetOf,
    AsnBasicNode, AsnSequenceOrSet, AsnSequenceOrSetOf, AsnEnumerated,
    AsnOctetString, AsnInt, AsnReal)
from ..commonPy.asnParser import g_names, g_leafTypeDict, CleanNameForAST
from ..commonPy.utility import panic, warn
from ..commonPy.cleanupNodes import SetOfBadTypenames
from ..commonPy.asnParser import AST_Leaftypes

g_sqlOutput: IO[Any]
g_innerTypes = set()  # type: Set[str]
g_uniqueStringOfASN1files = ""
g_outputDir = "."
g_asnFiles: List[str]


# ====== Dummy stubs =====
# The output can't contain forward declarations,
# so this follows the FixupAst/OnShutdown pattern.

def OnBasic(unused_nodeTypename: str, unused_node: AsnBasicNode, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass


def OnSequence(unused_nodeTypename: str, unused_node: AsnSequenceOrSet, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass


def OnSet(unused_nodeTypename: str, unused_node: AsnSequenceOrSet, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnEnumerated(unused_nodeTypename: str, unused_node: AsnEnumerated, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass


def OnSequenceOf(unused_nodeTypename: str, unused_node: AsnSequenceOrSetOf, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass


def OnSetOf(unused_nodeTypename: str, unused_node: AsnSequenceOrSetOf, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnChoice(unused_nodeTypename: str, unused_node: AsnChoice, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass
# ====== End of dummy stubs =====


def Version() -> None:
    print("$Id: sql_A_mapper.py 1932 2010-06-15 13:41:15Z ttsiodras $")  # pragma: no cover


g_dependencyGraph = {}  # type: Dict[str, Dict[str, int]]


def FixupAstForSQL() -> None:
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
                        internalName = newname = \
                            "TaStE_" + \
                            CleanNameForAST(child[0].capitalize() + "_type")
                        while internalName in g_names:
                            internalName = (newname + "_%d") % internalNo
                            internalNo += 1
                        g_names[internalName] = child[1]
                        child[1]._isArtificial = True
                        g_leafTypeDict[internalName] = child[1]._leafType
                        child[1] = AsnMetaMember(
                            asnFilename=child[1]._asnFilename,
                            containedType=internalName)
                        addedNewPseudoType = True
                        g_innerTypes.add(internalName)
                        g_dependencyGraph.setdefault(nodeTypename, {})
                        g_dependencyGraph[nodeTypename][internalName] = 1
                    else:
                        g_dependencyGraph.setdefault(nodeTypename, {})
                        g_dependencyGraph[nodeTypename][
                            child[1]._containedType] = 1
            elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
                if not isinstance(node._containedType, str):
                    internalName = newname = "TaStE_" + "internalSeqOf_type"
                    while internalName in g_names:
                        internalName = (newname + "_%d") % internalNo
                        internalNo += 1
                    g_names[internalName] = node._containedType
                    node._containedType._isArtificial = True
                    g_leafTypeDict[internalName] = \
                        node._containedType._leafType
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
    SQL cannot represent unnamed inner types
    e.g. this...
        SEQUENCE (SIZE(20)) OF INTEGER (0 .. 12)
    ...would need the declaration of an "inner" type
    that would carry the constraint (0..12).

    We do this AST "fixup" via a call to FixupAstForSQL
    '''
    global g_uniqueStringOfASN1files
    if isinstance(asnFiles, str):
        g_uniqueStringOfASN1files = \
            CleanName(
                asnFiles.lower().replace(".asn1", "").replace(".asn", ""))
    else:
        g_uniqueStringOfASN1files = \
            "_".join(
                CleanName(
                    x.lower().replace(".asn1", "").replace(".asn", ""))
                for x in asnFiles)  # pragma: no cover
    global g_bStartupRun  # pragma: no cover
    if g_bStartupRun:
        # Must run only once, no more.
        return  # pragma: no cover
    g_bStartupRun = True
    global g_outputDir
    g_outputDir = outputDir
    global g_asnFiles
    g_asnFiles = asnFiles
    FixupAstForSQL()


def CleanName(fieldName: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', fieldName)


def CreateBasic(nodeTypename: str, node: AsnBasicNode, leafTypeDict: AST_Leaftypes) -> None:
    baseType = leafTypeDict[node._leafType]
    baseSqlType = {
        'INTEGER': 'int',
        'REAL': 'float',
        'BOOLEAN': 'boolean',
        'OCTET STRING': 'VARCHAR'
    }[baseType]
    constraint = ""
    if isinstance(node, AsnOctetString):
        constraint += "(" + str(node._range[-1]) + ") "
    constraint += "NOT NULL"
    if isinstance(node, (AsnInt, AsnReal)) and node._range:
        constraint += ', CHECK(data>=%s and data<=%s)' % (
            node._range[0], node._range[-1])
    g_sqlOutput.write('''
CREATE TABLE {cleanTypename} (
    id int PRIMARY KEY,
    data {baseSqlType} {constraint}
);
'''.format(cleanTypename=CleanName(nodeTypename),
           baseSqlType=baseSqlType,
           constraint=constraint))


def CommonSeqSetChoice(nodeTypename: str,
                       node: Union[AsnChoice, AsnSet, AsnSequence],
                       unused_leafTypeDict: AST_Leaftypes,
                       isChoice: bool = False) -> None:
    cleanTypename = CleanName(nodeTypename)
    g_sqlOutput.write(
        '\nCREATE TABLE {cleanTypename} (\n    id int NOT NULL,\n'.format(
            cleanTypename=cleanTypename))
    if isChoice:
        g_sqlOutput.write('    indexOfActualFieldUsed int NOT NULL,\n')
    nullable = "" if isChoice else " NOT NULL"
    for c in node._members:
        cleanFieldname = CleanName(c[0])
        g_sqlOutput.write('    {cleanFieldname}_id int{nullable},\n'.format(
            cleanFieldname=cleanFieldname,
            nullable=nullable))
    g_sqlOutput.write(
        '    CONSTRAINT {cleanTypename}_pk PRIMARY KEY (id)'.format(
            cleanTypename=cleanTypename))
    for c in node._members:
        cleanFieldname = CleanName(c[0])
        childNode = c[1]
        containedTypename = CleanName(c[1]._containedType)
        assert isinstance(childNode, AsnMetaMember)
        g_sqlOutput.write(
            ',\n    CONSTRAINT {cleanFieldname}_fk '
            'FOREIGN KEY ({cleanFieldname}_id)\n'
            '\tREFERENCES {cleanTypename}(id)'.format(
                cleanFieldname=cleanFieldname,
                cleanTypename=containedTypename))
    g_sqlOutput.write(');\n\n')


def CreateSequence(nodeTypename: str, node: AsnSequenceOrSet, leafTypeDict: AST_Leaftypes) -> None:
    CommonSeqSetChoice(nodeTypename, node, leafTypeDict)


def CreateEnumerated(nodeTypename: str, node: AsnEnumerated, unused_leafTypeDict: AST_Leaftypes) -> None:
    optionsCheck = [
        '        -- {optionName}\n        enumerant = {optionValue}'.format(
            optionName=opt[0], optionValue=opt[1])
        for opt in node._members]

    g_sqlOutput.write('''
CREATE TABLE {cleanTypename} (
    id int PRIMARY KEY,
    enumerant int NOT NULL, CHECK(
{options}
    )
);
'''.format(cleanTypename=CleanName(nodeTypename),
           options='\n        OR\n'.join(optionsCheck)))


def CreateSequenceOf(nodeTypename: str, node: AsnSequenceOrSetOf, unused_leafTypeDict: AST_Leaftypes) -> None:
    cleanTypename = CleanName(nodeTypename)
    g_sqlOutput.write('\nCREATE TABLE %s (\n' % cleanTypename)
    g_sqlOutput.write('    id int PRIMARY KEY,\n')
    g_sqlOutput.write('    idx int NOT NULL,\n')
    reftype = node._containedType
    if not isinstance(reftype, str):
        panic("FixupAstForSQL failed to create a pseudoType for %s" %
              nodeTypename)  # pragma: no cover

    reftype = CleanName(reftype)
    g_sqlOutput.write('    {reftype}_id int NOT NULL,\n'.format(
        reftype=reftype))
    if node._range:
        constraint = 'CHECK(idx>=1 AND idx<=%s)' % (node._range[-1])
    g_sqlOutput.write("    " + constraint + ",\n")
    g_sqlOutput.write(
        '    CONSTRAINT {reftype}_fk FOREIGN KEY ({reftype}_id)\n'.format(
            reftype=reftype))
    g_sqlOutput.write(
        '    REFERENCES {reftype}(id)'.format(
            reftype=reftype))
    g_sqlOutput.write(');\n\n')


def CreateChoice(nodeTypename: str, node: AsnChoice, leafTypeDict: AST_Leaftypes) -> None:
    CommonSeqSetChoice(nodeTypename, node, leafTypeDict, True)


g_bShutdownRun = False


def OnShutdown(badTypes: SetOfBadTypenames) -> None:
    global g_bShutdownRun
    if g_bShutdownRun:
        return   # pragma: no cover
    g_bShutdownRun = True

    global g_sqlOutput
    g_sqlOutput = open(
        g_outputDir + os.sep + g_uniqueStringOfASN1files + ".sql", 'w')
    d = g_asnFiles if isinstance(g_asnFiles, str) else '","'.join(g_asnFiles)
    g_sqlOutput.write('--  SQL statements for types used in "%s"\n' % d)
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

            # only emit for types with no more dependencies
            if nodeTypename in g_dependencyGraph and \
                    g_dependencyGraph[nodeTypename]:
                continue

            # only emit each type once
            if nodeTypename in typesDoneSoFar:
                continue
            typesDoneSoFar.add(nodeTypename)

            # if we process even one type, deps may be removed,
            # so scan again next time
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
                warn("Ignoring unsupported node type: %s (%s)" % (
                    leafType, nodeTypename))  # pragma: no cover

            # eliminate nodeTypename from dependency lists
            for t in typenameList:
                if t in g_dependencyGraph and \
                        nodeTypename in g_dependencyGraph[t]:
                    del g_dependencyGraph[t][nodeTypename]

    g_sqlOutput.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
