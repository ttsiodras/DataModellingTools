# (C)  Semantix Information Technologies,
#      Neuropublic,
#      European Space Agency
#
# The license of the Data Modelling Tools (DMT) is GPL with Runtime Exception

'''
Rules to gather the list of types that must be skipped
'''

from typing import Set, Union, Dict  # NOQA

from . import asnParser
from .asnAST import (
    AsnAsciiString, AsnChoice, AsnSet, AsnSequenceOf, AsnSequence,
    AsnMetaMember, AsnSetOf, AsnNode
)

SetOfBadTypenames = Set[str]


def DiscoverBadTypes() -> SetOfBadTypenames:
    '''
    This returns a dictionary that tells us which types to skip
    pver during type mappings. For now, it includes IA5Strings
    and types whose descendants end up having such a field.
    '''
    badTypes = set()  # type: SetOfBadTypenames
    cache = {}  # type: Dict[AsnNode, bool]

    names = asnParser.g_names

    def CheckNodeForIA5(node_or_str: Union[AsnNode, str]) -> bool:
        if isinstance(node_or_str, str):
            node = names[node_or_str]  # type: AsnNode
        else:
            node = node_or_str
        if node in cache:
            return cache[node]
        if isinstance(node, AsnAsciiString):
            cache[node] = True
            return True
        elif isinstance(node, (AsnChoice, AsnSequence, AsnSet)):
            for child in node._members:
                if isinstance(child[1], AsnAsciiString):
                    cache[node] = True
                    return cache[node]
            cache[node] = any(
                CheckNodeForIA5(names[child[1]._containedType])
                for child in node._members
                if isinstance(child[1], AsnMetaMember))
            return cache[node]
        elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
            if isinstance(node._containedType, AsnAsciiString):
                cache[node] = True
            else:
                cache[node] = \
                    isinstance(node._containedType, str) and \
                    CheckNodeForIA5(names[node._containedType])
            return cache[node]
        cache[node] = False
        return cache[node]

    # Hack for IA5Strings (IA5s are used in TASTE's runtime configuration spec)
    while True:
        foundOne = False
        for nodeTypename in names.keys():
            nodeAST = names[nodeTypename]
            if nodeTypename not in badTypes and CheckNodeForIA5(nodeAST):
                badTypes.add(nodeTypename)
                foundOne = True
        if not foundOne:
            break
    return badTypes

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
