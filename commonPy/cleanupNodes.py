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
__doc__ = '''
Rules to gather the list of types that must be skipped
'''

from typing import Dict, Union

import commonPy.asnParser
from commonPy.asnAST import (
    AsnAsciiString, AsnChoice, AsnSet, AsnSequenceOf, AsnSequence,
    AsnMetaMember, AsnSetOf, AsnNode
)

def DiscoverBadTypes() -> Dict[str, bool]:
    '''
    This returns a dictionary that tells us which types to skip
    pver during type mappings. For now, it includes IA5Strings
    and types whose descendants end up having such a field.
    '''
    badTypes = {}  # type: Dict[str, bool]
    cache = {}  # type: Dict[AsnNode, bool]

    def CheckNodeForIA5(node_or_str: Union[AsnNode, str]) -> bool:
        names = commonPy.asnParser.g_names
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
                return True
            cache[node] = \
                isinstance(node._containedType, str) \
                and \
                CheckNodeForIA5(names[node._containedType])
            return cache[node]
        cache[node] = False
        return cache[node]

    # Hack for IA5Strings (IA5s are used in TASTE's runtime configuration spec)
    names = commonPy.asnParser.g_names
    while True:
        foundOne = False
        for nodeTypename in names.keys():
            node = names[nodeTypename]
            if nodeTypename not in badTypes and CheckNodeForIA5(node):
                badTypes[nodeTypename] = True
                foundOne = True
        if not foundOne:
            break
    return badTypes
