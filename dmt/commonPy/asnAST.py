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

#
# ASCIIO-created UML Class diagram of the AST stuff that matter in the A and B mappers.
# These are the only classes that matter after the fixup that takes place in
# VerifyAndFixAST()
#
#                  +----------------+
#                  |  AsnBasicNode  |
#         +------->|----------------|<-------------------------+
#         |        |                |                          |
#   +-----------+  +----------------+               +--------------------+
#   |  AsnBool  |     ^          ^                  |     AsnString      |
#   |-----------|     |          |                  |--------------------|
#   |           |     |      +--------------------+ | _range: [min, max] |
#   +-----------+     |      |      AsnReal       | +--------------------+
#     +--------------------+ |--------------------|
#     |       AsnInt       | | _range: [min, max] |
#     |--------------------| +--------------------+
#     | _range: [min, max] |
#     +--------------------+          +----------------+
#                                     | AsnComplexNode |
#                   +---------------->|----------------|<----------+
#                   |                 |                |           |
#                   |                 +----------------+           |
#    +-----------------------------+           ^                   |
#    |        AsnEnumerated        |           |             +------------------------+
#    |-----------------------------|           |             | AsnSequenceOf/AsnSetOf |
#    | _members list:(name, value) |           |             |------------------------|
#    +-----------------------------+           |             | _containedType         |
#                     +------------------------------------+ | value: string,         |
#                     |     AsnSequence/AsnSet/AsnChoice   | |        AsnBasicNode,   |
#                     |------------------------------------| |        AsnEnumerated   |
#                     | _members list:(name, value, ...    | +------------------------+
#                     | value: AsnBasicNode,               |
#                     |        AsnEnumerated,              |
#                     |        AsnMetaMember               |
#                     | en: the EnumID from ASN1SCC        |
#                     | op: the OPTIONAL-ity status        |
#                     | alwaysPresent: bool [1]            |
#                     | alwaysAbsent: bool  [1]            |
#                     +------------------------------------+
#
# [1] The alwaysAbsent/Present are additions made in Oct/2018 to accomodate
#     the complex interactions between OPTIONAL and WITH COMPONENTS.
#     Maxime described it to me as follows:
#
#     "The use case is two-fold - for SEQUENCE :
#
#     MySeq ::= MyOtherSeq (WITH COMPONENTS {..., b ABSENT })
#
#     ...and for CHOICE:
#
#     AllPossibleTC ::= CHOICE {
#        tc-6-1 ..,
#        tc-5-4 , .....}
#     TC-Subset ::= AllPossibleTC (WITH COMPONENTS {tc-6-1 ABSENT})
#
#     So alwaysPresent is NOT the negative of alwaysPresent:
#     a field can be optional, OR always present, OR always absent

from typing import List, Union, Dict, Any  # NOQA pylint: disable=unused-import

from . import utility

Lookup = Dict[str, 'AsnNode']
AsnSequenceOrSet = Union['AsnSequence', 'AsnSet']
AsnSequenceOrSetOf = Union['AsnSequenceOf', 'AsnSetOf']


class AsnNode:

    def __init__(self, asnFilename: str) -> None:
        self._leafType = "unknown"
        self._asnFilename = asnFilename
        self._lineno = -1
        self._isArtificial = False
        self.hasAcnEncDec = True

    def Location(self) -> str:
        return "file %s, line %d" % (self._asnFilename, int(self._lineno))  # pragma: no cover

    def IdenticalPerSMP2(self, unused_other: 'AsnNode', unused_mynames: Lookup, unused_othernames: Lookup) -> bool:  # pylint: disable=no-self-use
        utility.panic("internal error: Must be defined in derived class...")

    def AsASN1(self, _: Lookup) -> str:  # pylint: disable=no-self-use
        utility.panic("internal error: Must be defined in derived class...")


class AsnBasicNode(AsnNode):
    def __init__(self, asnFilename: str) -> None:
        AsnNode.__init__(self, asnFilename)


class AsnComplexNode(AsnNode):
    def __init__(self, asnFilename: str) -> None:
        AsnNode.__init__(self, asnFilename)

#########################################################
# Basic nodes: Bool, Int, Real, UTF8String, OctetString #
#########################################################


def CommonIdenticalRangePerSMP2(range1: List[int], range2: List[int]) -> bool:  # pylint: disable=invalid-sequence-index
    '''Helper for SMP2 comparisons of types with ranges.'''
    def collapseSpan(r: List[int]) -> List[int]:  # pylint: disable=invalid-sequence-index
        if len(r) == 2 and r[0] == r[1]:
            return [r[0]]
        return r
    mySpan = collapseSpan(range1)
    otherSpan = collapseSpan(range2)
    return (
        (mySpan == [] and otherSpan == []) or
        (len(mySpan) == 1 and len(otherSpan) == 1 and mySpan[0] == otherSpan[0]) or
        (len(mySpan) == 2 and len(otherSpan) == 2 and mySpan[-1] == otherSpan[-1]))


class AsnBool(AsnBasicNode):
    '''
This class stores the semantic content of an ASN.1 BOOLEAN.
Members:
    _name : the name of the type (or var)
    _bDefaultValue : one of True,False,None.
'''
    validOptions = ['bDefaultValue', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnBasicNode.__init__(self, args.get('asnFilename', ''))
        self._name = "BOOLEAN"  # default in case of SEQUENCE_OF BOOLEAN
        self._leafType = "BOOLEAN"
        self._lineno = args.get('lineno', None)
        self._bDefaultValue = args.get('bDefaultValue', None)
        for i in args:
            assert i in AsnBool.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        if self._bDefaultValue is not None:
            result += ", default value " + self._bDefaultValue  # pragma: no cover
        return result

    def IdenticalPerSMP2(self, other: AsnNode, unused_mynames: Lookup, unused_othernames: Lookup) -> bool:  # pylint: disable=no-self-use
        return isinstance(other, AsnBool)

    def AsASN1(self, _: Lookup) -> str:
        return 'BOOLEAN'


class AsnInt(AsnBasicNode):
    '''
This class stores the semantic content of an ASN.1 INTEGER.
Members:
    _name : the name of the type (or var)
    _range : a tuple containing the valid range for the integer or []
    _iDefaultValue : either None, or the default value for this integer
'''
    validOptions = ['range', 'iDefaultValue', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnBasicNode.__init__(self, args.get('asnFilename', ''))
        self._name = "INTEGER"  # default in case of SEQUENCE_OF INTEGER
        self._leafType = "INTEGER"
        self._lineno = args.get('lineno', None)
        self._range = args.get('range', [])
        self._iDefaultValue = args.get('iDefaultValue', None)
        for i in args:
            assert i in AsnInt.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        if self._range:
            result += " within [%s,%s]" % (self._range[0], self._range[1])
        if self._iDefaultValue is not None:
            result += " with default value of %s" % self._iDefaultValue  # pragma: no cover
        return result

    def IdenticalPerSMP2(self, other: AsnNode, unused_mynames: Lookup, unused_othernames: Lookup) -> bool:  # pylint: disable=no-self-use
        return isinstance(other, AsnInt) and CommonIdenticalRangePerSMP2(self._range, other._range)

    def AsASN1(self, _: Lookup) -> str:
        ret = 'INTEGER'
        if self._range:
            ret += ' (' + str(self._range[0]) + ' .. ' + str(self._range[1]) + ')'
        return ret


class AsnReal(AsnBasicNode):
    '''
This class stores the semantic content of an ASN.1 REAL.
Members:
    _name : the name of the type (or var)
    _range : a tuple containing the valid range for the integer or []
    _baseRange,
    _mantissaRange,
    _exponentRange  : single or double element tuples containing
                      the allowed ranges for respective values.
                      Or [].
    _dbDefaultValue : either None, or the default value for this real
'''
    validOptions = ['range', 'mantissa', 'base', 'exponent', 'defaultValue', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnBasicNode.__init__(self, args.get('asnFilename', ''))
        self._name = "REAL"  # default in case of SEQUENCE_OF REAL
        self._leafType = "REAL"
        self._lineno = args.get('lineno', None)
        self._range = args.get('range', [])
        self._mantissaRange = args.get('mantissa', None)
        self._baseRange = args.get('base', None)
        self._exponentRange = args.get('exponent', None)
        self._dbDefaultValue = args.get('defaultValue', None)
        for i in args:
            assert i in AsnReal.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        if self._mantissaRange is not None:
            result += ", mantissa range is"  # pragma: no cover
            result += str(self._mantissaRange)  # pragma: no cover
        if self._baseRange is not None:
            result += ", base range is"  # pragma: no cover
            result += str(self._baseRange)  # pragma: no cover
        if self._exponentRange is not None:
            result += ", exponent range is"  # pragma: no cover
            result += str(self._exponentRange)  # pragma: no cover
        if self._dbDefaultValue is not None:
            result += ", default value of "  # pragma: no cover
            result += self._dbDefaultValue  # pragma: no cover
        if self._range:
            result += ", default range"
            result += " within [%s,%s]" % (self._range[0], self._range[1])
        return result

    def IdenticalPerSMP2(self, other: AsnNode, unused_mynames: Lookup, unused_othernames: Lookup) -> bool:  # pylint: disable=no-self-use
        return isinstance(other, AsnReal) and CommonIdenticalRangePerSMP2(self._range, other._range)

    def AsASN1(self, _: Lookup) -> str:
        ret = 'REAL'
        if self._range:
            ret += ' (' + ("%f" % self._range[0]) + ' .. ' + ("%f" % self._range[1]) + ')'
        return ret


class AsnString(AsnBasicNode):
    '''
This class stores the semantic content of an ASN.1 String.
Members:
    _name : the name of the type (or var)
    _range : a tuple containing the allowed string size or []
'''
    validOptions = ['range', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnBasicNode.__init__(self, args.get('asnFilename', ''))
        self._leafType = "unknown"
        self._lineno = args.get('lineno', None)
        self._range = args.get('range', [])
        # Used by the Simulink and QGen mappers:
        # nameless string types can't be used, so a unique pseudo-type name
        # is created from the fieldname + "_type"
        self._pseudoname = None  # type: Union[None, str]
        for i in args:
            assert i in AsnString.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        if self._range:
            result += ", length within "
            result += str(self._range)
        return result

    def IdenticalPerSMP2(self, other: AsnNode, unused_mynames: Lookup, unused_othernames: Lookup) -> bool:  # pylint: disable=no-self-use
        return isinstance(other, AsnString) and CommonIdenticalRangePerSMP2(self._range, other._range)

    def AsASN1(self, _: Lookup) -> str:
        ret = 'OCTET STRING'
        if self._range:
            if len(self._range) > 1 and self._range[0] != self._range[1]:
                ret += ' (SIZE (' + str(self._range[0]) + ' .. ' + str(self._range[1]) + '))'
            else:
                ret += ' (SIZE (' + str(self._range[0]) + '))'
        return ret


class AsnOctetString(AsnString):
    '''This class stores the semantic content of an ASN.1 OCTET STRING.'''

    def __init__(self, **args: Any) -> None:
        AsnString.__init__(self, **args)
        self._name = "OCTET STRING"  # default in case of SEQUENCE_OF OCTET STRING
        self._leafType = "OCTET STRING"

# class AsnBitString(AsnString):
#     '''This class stores the semantic content of an ASN.1 BIT STRING.'''
#     def __init__(self, **args):
#        apply(AsnString.__init__, (self,), args)
#        self._name = "BIT STRING" # default in case of SEQUENCE_OF BIT STRING
#        self._leafType = "BIT STRING"


class AsnUTF8String(AsnString):
    '''This class stores the semantic content of an ASN.1 UTF8String.'''

    def __init__(self, **args: Any) -> None:
        AsnString.__init__(self, **args)  # pragma: no cover
        self._name = "UTF8String"  # default in case of SEQUENCE_OF UTF8String  # pragma: no cover
        self._leafType = "UTF8String"  # pragma: no cover


class AsnAsciiString(AsnString):
    '''This class stores the semantic content of an ASN.1 AsciiString.'''

    def __init__(self, **args: Any) -> None:
        AsnString.__init__(self, **args)  # pragma: no cover
        self._name = "AsciiString"  # default in case of SEQUENCE_OF AsciiString  # pragma: no cover
        self._leafType = "AsciiString"  # pragma: no cover


class AsnNumberString(AsnString):
    '''This class stores the semantic content of an ASN.1 NumberString.'''

    def __init__(self, **args: Any) -> None:
        AsnString.__init__(self, **args)  # pragma: no cover
        self._name = "NumberString"  # default in case of SEQUENCE_OF NumberString  # pragma: no cover
        self._leafType = "NumberString"  # pragma: no cover


class AsnVisibleString(AsnString):
    '''This class stores the semantic content of an ASN.1 VisibleString.'''

    def __init__(self, **args: Any) -> None:
        AsnString.__init__(self, **args)  # pragma: no cover
        self._name = "VisibleString"  # default in case of SEQUENCE_OF VisibleString  # pragma: no cover
        self._leafType = "VisibleString"  # pragma: no cover


class AsnPrintableString(AsnString):
    '''This class stores the semantic content of an ASN.1 PrintableString.'''

    def __init__(self, **args: Any) -> None:
        AsnString.__init__(self, **args)  # pragma: no cover
        self._name = "PrintableString"  # default in case of SEQUENCE_OF PrintableString  # pragma: no cover
        self._leafType = "PrintableString"  # pragma: no cover

###########################################################
# Complex nodes: Enumerated, Sequence, Choice, SequenceOf #
###########################################################


class AsnEnumerated(AsnComplexNode):
    '''
This class stores the semantic content of an ASN.1 enumeration.
Members:
    _name : the name of the type
    _members : a tuple of all the allowed values for the enumeration.
               Each value is itself a tuple, containing the name
               and the integer value associated with it (or None,
               if it is ommited)
    _default : if one of the values of the enumeration is the default,
               it is contained in this member
'''
    validOptions = ['members', 'default', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnComplexNode.__init__(self, args.get('asnFilename', ''))
        self._name = "ENUMERATED"  # default in case of SEQUENCE_OF ENUMERATED
        self._leafType = "ENUMERATED"
        self._members = args.get('members', [])
        self._default = args.get('default', None)
        self._lineno = args.get('lineno', None)
        # Used by the Simulink and QGen mappers:
        # nameless string types can't be used, so a unique pseudo-type name
        # is created from the fieldname + "_type"
        self._pseudoname = None  # type: Union[None, str]
        for i in args:
            assert i in AsnEnumerated.validOptions
        existing = {}  # type: Dict[str, int]
        for elem in self._members:
            if elem[0] in existing:
                utility.panic(
                    "member '%s' appears more than once in ENUMERATED %s" % (  # pragma: no cover
                        elem[0],
                        ("defined in line %s" % self._lineno) if self._lineno is not None else ""))  # pragma: no cover
            else:
                existing[elem[0]] = 1

    def __repr__(self) -> str:
        result = self._leafType
        assert self._members != []
        for member in self._members:
            result += ", option "
            result += str(member)
        return result

    def IdenticalPerSMP2(self, other: AsnNode, unused_mynames: Lookup, unused_othernames: Lookup) -> bool:  # pylint: disable=no-self-use
        return isinstance(other, AsnEnumerated) and sorted(self._members) == sorted(other._members)

    def AsASN1(self, _: Lookup) -> str:
        ret = []
        for m in self._members:
            ret.append(m[0] + '(' + m[1] + ')')
        return 'ENUMERATED {' + ", ".join(ret) + "}"


TypeWithMembers = Union['AsnSequence', 'AsnSet', 'AsnChoice']


def CommonIdenticalCheck(me: TypeWithMembers, other: TypeWithMembers, mynames: Lookup, othernames: Lookup) -> bool:
    # sort members on variable name
    myMembers = [y[1] for y in sorted((x[0], x[1]) for x in me._members)]
    otherMembers = [y[1] for y in sorted((x[0], x[1]) for x in other._members)]

    def resolve(node: AsnNode, d: Dict[str, AsnNode]) -> AsnNode:
        while isinstance(node, AsnMetaMember):
            cont = node._containedType
            while isinstance(cont, str):
                if cont not in d:
                    utility.panic("There's no such type in typename dictionary: '%s'" % cont)
                cont = d[cont]
            node = cont
        return node

    for listOfNodes, dd in [(myMembers, mynames), (otherMembers, othernames)]:
        for i in range(len(listOfNodes)):  # pylint: disable=consider-using-enumerate
            listOfNodes[i] = resolve(listOfNodes[i], dd)
    return all(x.IdenticalPerSMP2(y, mynames, othernames) for x, y in zip(myMembers, otherMembers))


def CommonAsASN1(kind: str, node: TypeWithMembers, typeDict: Lookup) -> str:
    ret = []
    for m in node._members:
        child = m[1]
        if isinstance(child, AsnMetaMember):
            child = child._containedType
            while isinstance(child, str):
                if child not in typeDict:
                    utility.panic("There's no such type in typename dictionary: '%s'" % child)
                child = typeDict[child]
        ret.append(m[0] + ' ' + child.AsASN1(typeDict))
    return kind + ' {' + ", ".join(ret) + "}"


class AsnSequence(AsnComplexNode):
    '''
This class stores the semantic content of an ASN.1 SEQUENCE.
Members:
    _name : the name of the type
    _members    : a tuple of all child elements. Each tuple contains
                  many elements: the name of the variable, the type itself
                  (as an AsnInt, AsnReal, ... or an AsnMetaMember),
                  an optionality boolean (true mean OPTIONAL),
                  and two more booleans to indicate alwaysAbsent
                  and alwaysPresent semantics. See comment at the
                  top diagram for more info.
'''
    validOptions = ['members', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnComplexNode.__init__(self, args.get('asnFilename', ''))
        self._name = "SEQUENCE"
        self._leafType = "SEQUENCE"
        self._members = args.get('members', [])
        self._lineno = args.get('lineno', None)
        for i in args:
            assert i in AsnSequence.validOptions
        existing = {}  # type: Dict[str, int]
        for elem in self._members:
            if elem[0] in existing:
                utility.panic(
                    "member '%s' appears more than once in %s" % (  # pragma: no cover
                        elem[0],
                        ("defined in line %s" % self._lineno) if self._lineno is not None else ""))  # pragma: no cover
            else:
                existing[elem[0]] = 1

    def __repr__(self) -> str:
        result = self._leafType
        assert self._members != []
        for member in self._members:
            result += ", member "
            result += str(member)
        return result

    def IdenticalPerSMP2(self, other: AsnNode, mynames: Lookup, othernames: Lookup) -> bool:
        # to allow for SMP2 mappings, where there's no AsnSet
        # return isinstance(other, AsnSequence) and CommonIdenticalCheck(self, other, mynames, othernames)
        return \
            isinstance(other, (AsnSet, AsnSequence, AsnChoice)) and \
            CommonIdenticalCheck(self, other, mynames, othernames)

    def AsASN1(self, typeDict: Lookup = None) -> str:
        if typeDict is None:
            typeDict = {}
        return CommonAsASN1('SEQUENCE', self, typeDict)


class AsnSet(AsnComplexNode):

    def __init__(self, **args: Any) -> None:
        AsnComplexNode.__init__(self, args.get('asnFilename', ''))
        self._name = "SET"
        self._leafType = "SET"
        self._members = args.get('members', [])
        self._lineno = args.get('lineno', None)
        for i in args:
            assert i in AsnSequence.validOptions
        existing = {}  # type: Dict[str, int]
        for elem in self._members:
            if elem[0] in existing:
                utility.panic(
                    "member '%s' appears more than once in %s" % (  # pragma: no cover
                        elem[0],
                        ("defined in line %s" % self._lineno) if self._lineno is not None else ""))  # pragma: no cover
            else:
                existing[elem[0]] = 1

    def __repr__(self) -> str:
        result = self._leafType
        assert self._members != []
        for member in self._members:
            result += ", member "
            result += str(member)
        return result

    def IdenticalPerSMP2(self, other: AsnNode, mynames: Lookup, othernames: Lookup) -> bool:
        # to allow for SMP2 mappings, where there's no AsnSet
        # return isinstance(other, AsnSet) and CommonIdenticalCheck(self, other, mynames, othernames)
        return \
            isinstance(other, (AsnSet, AsnSequence, AsnChoice)) and \
            CommonIdenticalCheck(self, other, mynames, othernames)

    def AsASN1(self, typeDict: Lookup = None) -> str:
        if typeDict is None:
            typeDict = {}
        return CommonAsASN1('SET', self, typeDict)


class AsnChoice(AsnComplexNode):
    '''
This class stores the semantic content of an ASN.1 CHOICE.
Members:
    _name : the name of the type
    _members    : a tuple of all child elements. Each tuple contains
                  two elements: the name of the variable and the
                  type itself (as an AsnInt, AsnReal, ... or an AsnMetaMember).
'''
    validOptions = ['members', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnComplexNode.__init__(self, args.get('asnFilename', ''))
        self._name = "CHOICE"  # default in case of SEQUENCE_OF CHOICE
        self._leafType = "CHOICE"
        self._members = args.get('members', [])
        self._lineno = args.get('lineno', None)
        for i in args:
            assert i in AsnChoice.validOptions
        existing = {}  # type: Dict[str, int]
        for elem in self._members:
            if elem[0] in existing:
                utility.panic(
                    "member '%s' appears more than once in CHOICE %s" % (  # pragma: no cover
                        elem[0],
                        ("defined in line %s" % self._lineno) if self._lineno is not None else ""))  # pragma: no cover
            else:
                existing[elem[0]] = 1

    def __repr__(self) -> str:
        result = self._leafType
        assert self._members != []
        for member in self._members:
            result += ", member "
            result += str(member)
        return result

    def IdenticalPerSMP2(self, other: AsnNode, mynames: Lookup, othernames: Lookup) -> bool:
        return isinstance(other, AsnChoice) and CommonIdenticalCheck(self, other, mynames, othernames)

    def AsASN1(self, typeDict: Lookup = None) -> str:
        if typeDict is None:
            typeDict = {}
        return CommonAsASN1('CHOICE', self, typeDict)


TypeWithRange = Union['AsnSequenceOf', 'AsnSetOf']


def CommonIdenticalArrayCheck(me: TypeWithRange, other: TypeWithRange, mynames: Lookup, othernames: Lookup) -> bool:
    if not CommonIdenticalRangePerSMP2(me._range, other._range):
        return False
    cont = [[me._containedType, mynames], [other._containedType, othernames]]
    for e in range(0, 2):
        node, typeDict = cont[e]
        while isinstance(node, str):
            if node not in typeDict:
                utility.panic("There's no such type in typename dictionary: '%s'" % node)
            node = typeDict[node]
        cont[e][0] = node
    return cont[0][0].IdenticalPerSMP2(cont[1][0], mynames, othernames)


def CommonAsASN1array(kind: str, node: TypeWithRange, typeDict: Lookup) -> str:
    contained = node._containedType
    while isinstance(contained, str):
        if contained not in typeDict:
            utility.panic("There's no such type in typename dictionary: '%s'" % contained)
        contained = typeDict[contained]
    if node._range:
        if len(node._range) > 1 and node._range[0] != node._range[1]:
            span = ' (SIZE(' + str(node._range[0]) + ' .. ' + str(node._range[1]) + ')) OF '
        else:
            span = ' (SIZE(' + str(node._range[0]) + ')) OF '
    else:
        span = ' OF '
    return kind + span + contained.AsASN1(typeDict)


class AsnSequenceOf(AsnComplexNode):
    '''
This class stores the semantic content of an ASN.1 SEQUENCEOF.
Members:
    _name : the name of the type
    _containedType : the contained element (either a string or AsnNode)
    _range : [] or a tuple with the allowed size range.
'''
    validOptions = ['range', 'containedType', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnComplexNode.__init__(self, args.get('asnFilename', ''))
        self._range = args.get('range', [])
        self._containedType = args.get('containedType', None)
        self._lineno = args.get('lineno', None)
        self._name = "unnamed"  # default in case of SEQUENCE_OF SEQUENCE_OF
        self._leafType = "SEQUENCEOF"
        for i in args:
            assert i in AsnSequenceOf.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        if self._range:
            result += ", valid sizes in "
            result += str(self._range)
        assert self._containedType is not None
        result += ", contained type is "
        result += str(self._containedType)
        return result

    def IdenticalPerSMP2(self, other: AsnNode, mynames: Lookup, othernames: Lookup) -> bool:
        return \
            isinstance(other, (AsnSequenceOf, AsnSetOf)) and \
            CommonIdenticalArrayCheck(self, other, mynames, othernames)

    def AsASN1(self, typeDict: Lookup = None) -> str:
        if typeDict is None:
            typeDict = {}
        return CommonAsASN1array('SEQUENCE', self, typeDict)


class AsnSetOf(AsnComplexNode):

    def __init__(self, **args: Any) -> None:
        AsnComplexNode.__init__(self, args.get('asnFilename', ''))
        self._range = args.get('range', [])
        self._containedType = args.get('containedType', None)
        self._lineno = args.get('lineno', None)
        self._name = "unnamed"  # default in case of SEQUENCE_OF SEQUENCE_OF
        self._leafType = "SETOF"
        for i in args:
            assert i in AsnSequenceOf.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        if self._range:
            result += ", valid sizes in "
            result += str(self._range)
        assert self._containedType is not None
        result += ", contained type is "
        result += str(self._containedType)
        return result

    def IdenticalPerSMP2(self, other: AsnNode, mynames: Lookup, othernames: Lookup) -> bool:
        return \
            isinstance(other, (AsnSequenceOf, AsnSetOf)) and \
            CommonIdenticalArrayCheck(self, other, mynames, othernames)

    def AsASN1(self, typeDict: Lookup = None) -> str:
        if typeDict is None:
            typeDict = {}
        return CommonAsASN1array('SET', self, typeDict)


class AsnMetaMember(AsnNode):
    '''
This class stores the semantic content of a member type of a
CHOICE or SEQUENCE.
Members:
    _containedType : the contained element as a string (type name)
'''
    validOptions = ['containedType', 'Min', 'Max', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnNode.__init__(self, args.get('asnFilename', ''))
        self._leafType = args.get('containedType', None)
        self._containedType = args.get('containedType', None)
        self._lineno = args.get('lineno', None)
        self._Min = args.get('Min', None)
        self._Max = args.get('Max', None)
        for i in args:
            assert i in AsnMetaMember.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        assert self._leafType is not None
        result += ", contained member is "
        result += " of type "
        result += self._containedType
        return result


class AsnMetaType(AsnNode):
    '''
This class stores the semantic content of a type which is typedefed
to another type.
Members:
    _containedType : the contained type name
e.g.:
    MyNewType ::= MyOldType
    _name contains 'MyNewType'
    _containedType contains 'MyOldType'
'''
    validOptions = ['containedType', 'Min', 'Max', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnNode.__init__(self, args.get('asnFilename', ''))
        self._leafType = args.get('containedType', None)
        self._containedType = args.get('containedType', None)
        self._lineno = args.get('lineno', None)
        self._Min = args.get('Min', None)
        self._Max = args.get('Max', None)
        for i in args:
            assert i in AsnMetaType.validOptions

    def __repr__(self) -> str:
        result = "typedefed to " + self._leafType  # pragma: no cover
        if self._Min is not None:
            result += ", min=" + str(self._Min)  # pragma: no cover
        if self._Max is not None:
            result += ", max=" + str(self._Max)  # pragma: no cover
        assert self._leafType is not None   # pragma: no cover
        return result  # pragma: no cover

# Helper functions


def isSequenceVariable(node: Union[AsnString, AsnSequenceOf, AsnSetOf]) -> bool:
    return len(node._range) == 2 and node._range[0] != node._range[1]


def sourceSequenceLimit(node: Union[AsnString, AsnSequenceOf, AsnSetOf], srcCVariable: str) -> str:
    return str(node._range[-1]) if not isSequenceVariable(node) else "%s.nCount" % srcCVariable


def targetSequenceLimit(node: Union[AsnString, AsnSequenceOf, AsnSetOf], dstCVariable: str) -> str:
    return str(node._range[-1]) if not isSequenceVariable(node) else "%s.nCount" % dstCVariable

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
