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
import re
from typing import Union, List, Dict, TypeVar, Generic

from .utility import panicWithCallStack
from .asnAST import (
    AsnBasicNode, AsnSequence, AsnSet, AsnChoice, AsnSequenceOf,
    AsnSetOf, AsnEnumerated, AsnMetaMember, AsnNode, AsnInt, AsnReal, AsnBool,
    AsnOctetString
)
from .asnParser import AST_Leaftypes, AST_Lookup


TSrc = TypeVar('TSrc')
TDest = TypeVar('TDest')


# noinspection PyMethodMayBeStatic
class RecursiveMapperGeneric(Generic[TSrc, TDest]):

    def maybeElse(self, childNo: int) -> str:  # pylint: disable=no-self-use
        if childNo == 1:
            return ""
        else:
            return "else "

    def CleanName(self, fieldName: str) -> str:  # pylint: disable=no-self-use
        return re.sub(r'[^a-zA-Z0-9_]', '_', fieldName)

    def Version(self) -> None:  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapInteger(self, unused_srcVar: TSrc, unused_destVar: TDest, unused_node: AsnInt, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> List[str]:  # pylint: disable=no-self-use,invalid-sequence-index
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapReal(self, unused_srcVar: TSrc, unused_destVar: TDest, unused_node: AsnReal, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> List[str]:  # pylint: disable=no-self-use,invalid-sequence-index
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapBoolean(self, unused_srcVar: TSrc, unused_destVar: TDest, unused_node: AsnBool, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> List[str]:  # pylint: disable=no-self-use,invalid-sequence-index
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapOctetString(self, unused_srcVar: TSrc, unused_destVar: TDest, unused_node: AsnOctetString, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> List[str]:  # pylint: disable=no-self-use,invalid-sequence-index
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapEnumerated(self, unused_srcVar: TSrc, unused_destVar: TDest, unused_node: AsnEnumerated, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> List[str]:  # pylint: disable=no-self-use,invalid-sequence-index
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapSequence(self, unused_srcVar: TSrc, unused_destVar: TDest, unused_node: AsnSequence, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> List[str]:  # pylint: disable=no-self-use,invalid-sequence-index
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapSet(self, unused_srcVar: TSrc, unused_destVar: TDest, unused_node: AsnSet, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> List[str]:  # pylint: disable=no-self-use,invalid-sequence-index
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapChoice(self, unused_srcVar: TSrc, unused_destVar: TDest, unused_node: AsnChoice, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> List[str]:  # pylint: disable=no-self-use,invalid-sequence-index
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapSequenceOf(self, unused_srcVar: TSrc, unused_destVar: TDest, unused_node: AsnSequenceOf, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> List[str]:  # pylint: disable=no-self-use,invalid-sequence-index
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapSetOf(self, unused_srcVar: TSrc, unused_destVar: TDest, unused_node: AsnSetOf, unused_leafTypeDict: AST_Leaftypes, unused_names: AST_Lookup) -> List[str]:  # pylint: disable=no-self-use,invalid-sequence-index
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def Map(self,
            srcVar: TSrc,
            destVar: TDest,
            node_or_str: Union[str, AsnNode],
            leafTypeDict: Dict[str, str],
            names: Dict[str, AsnNode]) -> List[str]:  # pylint: disable=invalid-sequence-index
        if isinstance(node_or_str, str):
            node = names[node_or_str]  # type: AsnNode
        else:
            node = node_or_str
        lines = []  # type: List[str]
        if isinstance(node, AsnInt):
            lines.extend(self.MapInteger(srcVar, destVar, node, leafTypeDict, names))
        elif isinstance(node, AsnReal):
            lines.extend(self.MapReal(srcVar, destVar, node, leafTypeDict, names))
        elif isinstance(node, AsnBool):
            lines.extend(self.MapBoolean(srcVar, destVar, node, leafTypeDict, names))
        elif isinstance(node, AsnOctetString):
            lines.extend(self.MapOctetString(srcVar, destVar, node, leafTypeDict, names))
        elif isinstance(node, AsnSequence):
            lines.extend(self.MapSequence(srcVar, destVar, node, leafTypeDict, names))
        elif isinstance(node, AsnSet):
            lines.extend(self.MapSet(srcVar, destVar, node, leafTypeDict, names))
        elif isinstance(node, AsnChoice):
            lines.extend(self.MapChoice(srcVar, destVar, node, leafTypeDict, names))
        elif isinstance(node, AsnSequenceOf):
            lines.extend(self.MapSequenceOf(srcVar, destVar, node, leafTypeDict, names))
        elif isinstance(node, AsnSetOf):
            lines.extend(self.MapSetOf(srcVar, destVar, node, leafTypeDict, names))
        elif isinstance(node, AsnEnumerated):
            lines.extend(self.MapEnumerated(srcVar, destVar, node, leafTypeDict, names))
        elif isinstance(node, AsnMetaMember):
            lines.extend(self.Map(srcVar, destVar, names[node._containedType], leafTypeDict, names))
        else:
            panicWithCallStack("unsupported %s (%s)" % (str(node.__class__), node.Location()))
        return lines


# pylint: disable=no-self-use
RecursiveMapper = RecursiveMapperGeneric[str, str]


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
