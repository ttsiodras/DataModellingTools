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
of ASN.1 constructs to SQL Alchemy ones. It is used as a backend of
Semantix's code generator A.'''

import os
import re

from commonPy.asnAST import (
    AsnMetaMember, AsnChoice, AsnSet, AsnSequence, AsnSequenceOf,
    AsnSetOf, isSequenceVariable)
from commonPy.asnParser import g_names, g_leafTypeDict, CleanNameForAST
from commonPy.utility import panic, warn
from commonPy.cleanupNodes import SetOfBadTypenames

g_sqlalchemyOutput = None
g_innerTypes = {}  # type: Dict[str, int]
g_uniqueStringOfASN1files = ""
g_outputDir = "."
g_asnFiles = None


# ====== Dummy stubs =====
# The output can't contain forward declarations,
# so this follows the FixupAst/OnShutdown pattern.

def OnBasic(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass


def OnSequence(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass


def OnSet(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass  # pragma: no cover


def OnEnumerated(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass


def OnSequenceOf(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass


def OnSetOf(unused_nodeTypename, unused_node, unused_leafTypeDict):
    pass  # pragma: no cover


def OnChoice(unused_nodeTypename, unused_unused_node,
             unused_unused_leafTypeDict):
    pass
# ====== End of dummy stubs =====


def Version():
    print("$Id$")  # pragma: no cover


g_dependencyGraph = {}  # type: Dict[str, Dict[str, int]]


def FixupAstForSQLAlchemy():
    '''
    Find all the SEQUENCE, CHOICE and SEQUENCE OFs
    and make sure the contained types are not "naked" (i.e. unnamed)
    '''
    internalNo = 1

    def neededToAddPseudoType():
        nonlocal internalNo
        addedNewPseudoType = False
        listOfTypenames = sorted(list(g_names.keys()) + list(g_innerTypes.keys()))
        for nodeTypename in listOfTypenames:
            node = g_names[nodeTypename]
            if isinstance(node, (AsnChoice, AsnSequence, AsnSet)):
                for child in node._members:
                    if not isinstance(child[1], AsnMetaMember):
                        internalName = newname = \
                            "TaStE_" + \
                            CleanNameForAST(child[0].capitalize() + "_type")
                        while internalName in g_names:
                            internalName = (newname + "_%d") % internalNo  # pragma: no cover
                            internalNo += 1                                # pragma: no cover
                        g_names[internalName] = child[1]
                        child[1]._isArtificial = True
                        g_leafTypeDict[internalName] = child[1]._leafType
                        child[1] = AsnMetaMember(
                            asnFilename=child[1]._asnFilename,
                            containedType=internalName)
                        addedNewPseudoType = True
                        g_innerTypes[internalName] = 1
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
                        internalName = (newname + "_%d") % internalNo  # pragma: no cover
                        internalNo += 1                                # pragma: no cover
                    g_names[internalName] = node._containedType
                    node._containedType._isArtificial = True
                    g_leafTypeDict[internalName] = \
                        node._containedType._leafType
                    node._containedType = internalName
                    addedNewPseudoType = True
                    g_innerTypes[internalName] = 1
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


def OnStartup(unused_modelingLanguage, asnFiles, outputDir, unused_badTypes):
    '''
    SQL cannot represent unnamed inner types
    e.g. this...
        SEQUENCE (SIZE(20)) OF INTEGER (0 .. 12)
    ...would need the declaration of an "inner" type
    that would carry the constraint (0..12).

    We do this AST "fixup" via a call to FixupAstForSQLAlchemy
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
    FixupAstForSQLAlchemy()


def CleanName(fieldName):
    return re.sub(r'[^a-zA-Z0-9_]', '_', fieldName)


def CreateBasic(nodeTypename, node, leafTypeDict):
    cleanTypename = CleanName(nodeTypename)
    baseType = leafTypeDict[node._leafType]
    baseSqlType = {
        'INTEGER': 'Integer',
        'REAL': 'Float',
        'BOOLEAN': 'Boolean',
        'OCTET STRING': 'String'
    }[baseType]
    constraint = ""
    if baseType == 'OCTET STRING':
        constraint += "(" + str(node._range[-1]) + ")"
        # defValue = '""'
    elif baseType in ['INTEGER', 'REAL'] and node._range:
        constraint += ", CheckConstraint('data>=%s and data<=%s')" % (
            node._range[0], node._range[-1])
        # defValue = node._range[-1]
    # else:
        # defValue = 'False'
    constraint += ", nullable=False"
    g_sqlalchemyOutput.write(
        '''
class {cleanTypename}_SQL(Base):
    __tablename__ = '{cleanTypename}'
    __table_args__ = (UniqueConstraint('iid'),)
    iid = Column(Integer, primary_key=True)
    data = Column({baseSqlType}{constraint})
'''.format(cleanTypename=cleanTypename,
           baseSqlType=baseSqlType,
           constraint=constraint))

    getter = "Get"
    setter = "Set"
    if baseType not in ['INTEGER', 'REAL', 'BOOLEAN']:
        getter = "GetPyString"
        setter = "SetFromPyString"

    g_sqlalchemyOutput.write('''
    @staticmethod
    def loadFromDB(session, iid):
        return session.query(
            {cleanTypename}_SQL).filter({cleanTypename}_SQL.iid == iid).first()

    @property
    def asn1(self):
        if hasattr(self, "_cache"):
            return self._cache
        pyObj = {cleanTypename}()
        self.assignToASN1object(pyObj)
        self._cache = pyObj
        return pyObj

    def assignToASN1object(self, pyObj):
        pyObj.{setter}(self.data)

    def __init__(self, pyObj):
        self.data = pyObj.{getter}()

    def save(self, session):
        session.add(self)
        session.commit()
        return self.iid

'''.format(setter=setter, getter=getter,
           cleanTypename=cleanTypename))


def CreateSequence(nodeTypename, node, unused_leafTypeDict, isChoice=False):
    cleanTypename = CleanName(nodeTypename)
    choiceField = ''
    if isChoice:
        choiceField = \
            '    kind = Column(Integer, nullable=False)\n'

    memberAssignments = []
    if isChoice:
        memberAssignments.append('pyObj.kind.Set(self.kind)')
        for c in node._members:
            cleanFieldname = CleanName(c[0])
            memberAssignments.append(
                'if self.kind == DV.' + c[-1] + ':')
            memberAssignments.append('    pyObj.Reset(state)')
            assert isinstance(c[1], AsnMetaMember)
            containedTypename = CleanName(c[1]._containedType)
            memberAssignments.append(
                '    self.' + cleanFieldname + '.assignToASN1object(' +
                'pyObj.' + cleanFieldname + ')')
    else:
        for c in node._members:
            memberAssignments.append('pyObj.Reset(state)')
            cleanFieldname = CleanName(c[0])
            assert isinstance(c[1], AsnMetaMember)
            containedTypename = CleanName(c[1]._containedType)
            memberAssignments.append(
                'self.' + cleanFieldname + '.assignToASN1object(' +
                'pyObj.' + cleanFieldname + ')')

    g_sqlalchemyOutput.write(
        '''
class {cleanTypename}_SQL(Base):
    __tablename__ = '{cleanTypename}'
    __table_args__ = (UniqueConstraint('iid'),)
    iid = Column(Integer, primary_key=True)
{choiceField}
    @staticmethod
    def loadFromDB(session, iid):
        return session.query(
            {cleanTypename}_SQL).filter({cleanTypename}_SQL.iid == iid).first()

    @property
    def asn1(self):
        if hasattr(self, "_cache"):
            return self._cache
        pyObj = {cleanTypename}()
        self.assignToASN1object(pyObj)
        self._cache = pyObj
        return pyObj

    def assignToASN1object(self, pyObj):
        state = pyObj.GetState()
        {assignMembers}
        pyObj.Reset(state)

    def save(self, session):
        session.add(self)
        session.commit()
        return self.iid
'''.format(cleanTypename=cleanTypename, choiceField=choiceField,
           assignMembers="\n        ".join(memberAssignments)))

    nullable = "True" if isChoice else "False"
    for c in node._members:
        cleanFieldname = CleanName(c[0])
        childNode = c[1]
        assert isinstance(childNode, AsnMetaMember)
        containedTypename = CleanName(c[1]._containedType)
        g_sqlalchemyOutput.write(
            '\n    fk_%s_iid = Column(Integer, ' % cleanFieldname)
        g_sqlalchemyOutput.write(
            "ForeignKey('{containedTypename}.iid'), nullable={nl})".format(
                nl=nullable,
                containedTypename=containedTypename))
        g_sqlalchemyOutput.write(
            '''
    {relation} = relationship(
        "{containedTypename}_SQL",
        foreign_keys=[fk_{relation}_iid])'''.format(relation=cleanFieldname,
                                                    containedTypename=containedTypename))
    g_sqlalchemyOutput.write('\n\n    def __init__(self, pyObj):\n')
    g_sqlalchemyOutput.write('        state = pyObj.GetState()\n')
    if isChoice:
        g_sqlalchemyOutput.write('        self.kind = pyObj.kind.Get()\n')
        g_sqlalchemyOutput.write('        pyObj.Reset(state)\n')
    for c in node._members:
        cleanFieldname = CleanName(c[0])
        childNode = c[1]
        assert isinstance(childNode, AsnMetaMember)
        containedTypename = CleanName(c[1]._containedType)
        if isChoice:
            g_sqlalchemyOutput.write(
                '        '
                'if self.kind == DV.' + c[-1] + ':\n')
            g_sqlalchemyOutput.write(
                '            '
                'self.{cleanFieldname} = '
                '{containedTypename}_SQL(pyObj.{cleanFieldname})\n'.format(
                    cleanFieldname=cleanFieldname,
                    containedTypename=containedTypename))
            g_sqlalchemyOutput.write(
                '            pyObj.Reset(state)\n')
        else:
            g_sqlalchemyOutput.write(
                '        '
                'self.{cleanFieldname} = '
                '{containedTypename}_SQL(pyObj.{cleanFieldname})\n'.format(
                    cleanFieldname=cleanFieldname,
                    containedTypename=containedTypename))
            g_sqlalchemyOutput.write(
                '        pyObj.Reset(state)\n')
    g_sqlalchemyOutput.write('\n')


def CreateEnumerated(nodeTypename, node, unused_leafTypeDict):
    checkConstraint = ' OR '.join('data='+x[1] for x in node._members)
    constants = '\n    '.join(CleanName(x[0])+' = '+x[1]
                              for x in node._members)
    # defValue = CleanName(nodeTypename) + "_SQL." + CleanName(node._members[0][0])
    g_sqlalchemyOutput.write('''
class {cleanTypename}_SQL(Base):
    __tablename__ = '{cleanTypename}'
    __table_args__ = (UniqueConstraint('iid'),)
    {constants}
    iid = Column(Integer, primary_key=True)
    data = Column(Integer, CheckConstraint('{constraint}'), nullable=False)

    @staticmethod
    def loadFromDB(session, iid):
        return session.query(
            {cleanTypename}_SQL).filter({cleanTypename}_SQL.iid == iid).first()

    @property
    def asn1(self):
        if hasattr(self, "_cache"):
            return self._cache
        pyObj = {cleanTypename}()
        self.assignToASN1object(pyObj)
        self._cache = pyObj
        return pyObj

    def assignToASN1object(self, pyObj):
        pyObj.Set(self.data)

    def __init__(self, pyObj):
        self.data = pyObj.Get()

    def save(self, session):
        session.add(self)
        session.commit()
        return self.iid

'''.format(cleanTypename=CleanName(nodeTypename),
           constraint=checkConstraint,
           constants=constants))


def CreateSequenceOf(nodeTypename, node, unused_leafTypeDict):
    cleanTypename = CleanName(nodeTypename)
    reftype = node._containedType
    reftype = CleanName(reftype)
    constraint = ""
    if node._range != []:
        constraint = \
            ", CheckConstraint('idx>=0 AND idx<%s')" % (node._range[-1])

    # The detail table, containing the index of the cell
    # and the foreign key to the actual data
    g_sqlalchemyOutput.write('''
class {cleanTypename}_indexes_SQL(Base):
    __tablename__ = '{cleanTypename}_indexes'
    __table_args__ = (UniqueConstraint('idx', 'fk_{cleanTypename}_iid'),)
    iid = Column(Integer, primary_key=True)
    idx = Column(Integer{constraint}, nullable=False)
    fk_{cleanTypename}_iid = Column(
        Integer,
        ForeignKey('{cleanTypename}.iid'),
        nullable=False)
    fk_{reftype}_iid = Column(
        Integer,
        ForeignKey('{reftype}.iid'),
        nullable=False)
    array = relationship(
        "{cleanTypename}_SQL",
        foreign_keys=[fk_{cleanTypename}_iid],
        backref='arrIndexes_{cleanTypename}')
    data = relationship(
        "{reftype}_SQL",
        foreign_keys=[fk_{reftype}_iid])

    def save(self, session):
        session.add(self)
        session.commit()
        return self.iid
'''.format(reftype=reftype,
           cleanTypename=cleanTypename,
           constraint=constraint))

    # The master table
    if isSequenceVariable(node):
        setLength = \
            '        ' + \
            'pyObj.SetLength(len(self.arrIndexes_%s))' % cleanTypename
    else:
        setLength = ''
    g_sqlalchemyOutput.write('''
class {cleanTypename}_SQL(Base):
    __tablename__ = '{cleanTypename}'
    iid = Column(Integer, primary_key=True)

    @staticmethod
    def loadFromDB(session, iid):
        return session.query(
            {cleanTypename}_SQL).filter({cleanTypename}_SQL.iid == iid).first()

    @property
    def asn1(self):
        if hasattr(self, "_cache"):
            return self._cache
        pyObj = {cleanTypename}()
        self.assignToASN1object(pyObj)
        self._cache = pyObj
        return pyObj

    def assignToASN1object(self, pyObj):
        state = pyObj.GetState()
{setLength}
        for idx, idxObj in enumerate(self.arrIndexes_{cleanTypename}):
            pyObj.Reset(state)
            idxObj.data.assignToASN1object(pyObj[idxObj.idx])
        pyObj.Reset(state)

    def save(self, session):
        session.add(self)
        for c in self._children:
            session.add(c[0])
            session.add(c[1])
        session.commit()
        return self.iid

    def __init__(self, pyObj):
        self._children = []
        state = pyObj.GetState()
        for i in xrange(pyObj.GetLength()):
            pyObj.Reset(state)
            newIndex = {cleanTypename}_indexes_SQL()
            newIndex.idx = i
            newIndex.array = self
            newData = {reftype}_SQL(pyObj[i])
            newIndex.data = newData
            self._children.append((newIndex, newData))

        pyObj.Reset(state)

'''.format(cleanTypename=cleanTypename, setLength=setLength,
           reftype=reftype))

    if not isinstance(reftype, str):
        panic("FixupAstForSQLAlchemy failed to create a pseudoType for %s" %
              nodeTypename)  # pragma: no cover


def CreateChoice(nodeTypename, node, _):
    CreateSequence(nodeTypename, node, _, isChoice=True)

g_bShutdownRun = False


def OnShutdown(badTypes: SetOfBadTypenames):
    global g_bShutdownRun
    if g_bShutdownRun:
        return   # pragma: no cover
    g_bShutdownRun = True

    global g_sqlalchemyOutput
    g_sqlalchemyOutput = open(
        g_outputDir + os.sep + g_uniqueStringOfASN1files + "_model.py", 'w')
    d = g_asnFiles if isinstance(g_asnFiles, str) else '","'.join(g_asnFiles)
    typenameList = []
    for nodeTypename in sorted(list(g_innerTypes.keys()) + list(g_names.keys())):
        if nodeTypename in badTypes:
            continue
        if nodeTypename not in typenameList:
            typenameList.append(nodeTypename)

    g_sqlalchemyOutput.write('''
#  SQLAlchemy models for types used in "{d}"

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import (Column, Integer, String, Boolean, Float,
                        ForeignKey, CheckConstraint, UniqueConstraint)
from sqlalchemy.orm import relationship

from {d_cleaned} import (
    {types}
)

import DV

'''.format(d=d, d_cleaned=CleanName(d),
           types=", ".join(
               CleanName(x)
               for x in typenameList
               if not g_names[x]._isArtificial)))
    typesDoneSoFar = {}

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
            typesDoneSoFar[nodeTypename] = 1

            # if we process even one type, deps may be removed,
            # so scan again next time
            workRemains = True

            # make sure we know what leaf type this node is
            node = g_names[nodeTypename]
            assert nodeTypename in g_leafTypeDict
            leafType = g_leafTypeDict[nodeTypename]
            if leafType in ['BOOLEAN', 'INTEGER', 'REAL', 'OCTET STRING']:
                CreateBasic(nodeTypename, node, g_leafTypeDict)
            elif leafType in ['SEQUENCE', 'SET']:
                CreateSequence(nodeTypename, node, g_leafTypeDict)
            elif leafType == 'CHOICE':
                CreateChoice(nodeTypename, node, g_leafTypeDict)
            elif leafType in ['SEQUENCEOF', 'SETOF']:
                CreateSequenceOf(nodeTypename, node, g_leafTypeDict)
            elif leafType == 'ENUMERATED':
                CreateEnumerated(nodeTypename, node, g_leafTypeDict)
            else:  # pragma: no cover
                warn("Ignoring unsupported node type: %s (%s)" % (
                    leafType, nodeTypename))  # pragma: no cover

            # eliminate nodeTypename from dependency lists
            for t in typenameList:
                if t in g_dependencyGraph and \
                        nodeTypename in g_dependencyGraph[t]:
                    del g_dependencyGraph[t][nodeTypename]
    # g_sqlalchemyOutput.write('if __name__ == "__main__":\n')
    # g_sqlalchemyOutput.write('    Base.metadata.create_all(engine)\n')
    g_sqlalchemyOutput.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
