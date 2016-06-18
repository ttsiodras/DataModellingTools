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
# with the terms of the GNU Lesser General Public License version 3.
#
# GNU LLGPL v. 2.1:
#       This version of DMT is the one to use for the development of
# applications, when you are willing to comply with the terms of the
# GNU Lesser General Public License version 3.
#
# Note that in both cases, there are no charges (royalties) for the
# generated code.
#
'''
This module checks that all ASN.1 types are using the appropriate
constraint (ASSERT-wise).
'''

from typing import Dict, Union  # NOQA

from commonPy.utility import panic

import commonPy.asnAST
from commonPy.asnAST import AsnNode

import commonPy.configMT
from functools import reduce


def VerifyNodeRange(node):
    '''This function checks that
- INTEGERs
- REALs
- STRINGs
- and SEQUENCE/SET OFs

...are equipped with the necessary range constructs.
If they are not, a runtime error is generated, with a report
on the exact location of the offending type in the ASN.1 grammar.'''
    if isinstance(node, commonPy.asnAST.AsnInt):
        if node._range == []:
            panic("INTEGER (in %s) must have a range constraint inside ASN.1,\n"
                  "or else we might lose accuracy during runtime!" % node.Location())

    elif isinstance(node, commonPy.asnAST.AsnReal):
        if node._range == []:
            panic("REAL (in %s) must have a range constraint inside ASN.1,\n"
                  "or else we might lose accuracy during runtime!" % node.Location())
        else:
            # ASN1SCC uses C double for ASN.1 REAL.
            # this allows values from -1.7976931348623157E308 to 1.7976931348623157E308
            if node._range[0] < -1.7976931348623157E308:
                panic("REAL (in %s) must have a low limit >= -1.7976931348623157E308\n" %
                      node.Location())
            if node._range[1] > 1.7976931348623157E308:
                panic("REAL (in %s) must have a high limit <= 1.7976931348623157E308\n" %
                      node.Location())

    elif isinstance(node, commonPy.asnAST.AsnString):
        if node._range == []:
            panic("string (in %s) must have SIZE range set!\n" % node.Location())

    elif isinstance(node, commonPy.asnAST.AsnSequenceOf) or isinstance(node, commonPy.asnAST.AsnSetOf):
        if node._range == []:
            panic("SequenceOf (in %s) must have SIZE range set!\n" % node.Location())

    elif isinstance(node, commonPy.asnAST.AsnEnumerated):
        if reduce(lambda x, y: x or y, [x[1] is None for x in node._members]):
            panic("ENUMERATED must have integer value for each enum! (%s)" % node.Location())


def VerifyRanges(node_or_str: Union[str, AsnNode], names: Dict[str, AsnNode]) -> None:
    '''This function recursively traverses the AST,
calling VerifyNodeRange for each Node.'''
    if isinstance(node_or_str, str):
        node = names[node_or_str]  # type: AsnNode
    else:
        node = node_or_str
    if isinstance(node, commonPy.asnAST.AsnMetaMember):
        node = names[node._containedType]

    if isinstance(node, commonPy.asnAST.AsnBasicNode):
        VerifyNodeRange(node)
    elif isinstance(node, (commonPy.asnAST.AsnSequence, commonPy.asnAST.AsnChoice, commonPy.asnAST.AsnSet)):
        # Bug fixed in ASN1SCC - this check is no longer needed
        # if 0 == len(node._members):
        #     panic(
        #         "Empty SEQUENCE/SETs are not allowed. Please add at least one field in (%s)\n"
        #         % node.Location())
        for child in node._members:
            VerifyRanges(child[1], names)
    elif isinstance(node, (commonPy.asnAST.AsnSequenceOf, commonPy.asnAST.AsnSetOf)):
        VerifyNodeRange(node)
        VerifyRanges(node._containedType, names)
    elif isinstance(node, commonPy.asnAST.AsnEnumerated):
        VerifyNodeRange(node)
    else:
        panic("VerifyRanges: Unexpected %s\n" % str(node))
