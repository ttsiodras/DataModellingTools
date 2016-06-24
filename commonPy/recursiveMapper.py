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
from typing import Union, List, Dict

from commonPy.utility import panicWithCallStack
from commonPy.asnAST import (
    AsnBasicNode, AsnSequence, AsnSet, AsnChoice, AsnSequenceOf,
    AsnSetOf, AsnEnumerated, AsnMetaMember, AsnNode
)


class RecursiveMapper:

    # noinspection PyMethodMayBeStatic
    def maybeElse(self, childNo: int) -> str:  # pylint: disable=no-self-use
        if childNo == 1:
            return ""
        else:
            return "else "

    # noinspection PyMethodMayBeStatic
    def CleanName(self, fieldName: str) -> str:  # pylint: disable=no-self-use
        return re.sub(r'[^a-zA-Z0-9_]', '_', fieldName)

    # noinspection PyMethodMayBeStatic
    def Version(self):  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapInteger(self, unused_srcVar, unused_destVar, unused_node, unused_leafTypeDict, unused_names):  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapReal(self, unused_srcVar, unused_destVar, unused_node, unused_leafTypeDict, unused_names):  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapBoolean(self, unused_srcVar, unused_destVar, unused_node, unused_leafTypeDict, unused_names):  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapOctetString(self, unused_srcVar, unused_destVar, unused_node, unused_leafTypeDict, unused_names):  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapEnumerated(self, unused_srcVar, unused_destVar, unused_node, unused_leafTypeDict, unused_names):  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapSequence(self, unused_srcVar, unused_destVar, unused_node, unused_leafTypeDict, unused_names):  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapSet(self, unused_srcVar, unused_destVar, unused_node, unused_leafTypeDict, unused_names):  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapChoice(self, unused_srcVar, unused_destVar, unused_node, unused_leafTypeDict, unused_names):  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapSequenceOf(self, unused_srcVar, unused_destVar, unused_node, unused_leafTypeDict, unused_names):  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def MapSetOf(self, unused_srcVar, unused_destVar, unused_node, unused_leafTypeDict, unused_names):  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a RecursiveMapper...")

    def Map(self,
            srcVar: str,
            destVar: str,
            node_or_str: Union[str, AsnNode],
            leafTypeDict: Dict[str, str],
            names: Dict[str, AsnNode]) -> List[str]:  # pylint: disable=invalid-sequence-index
        if isinstance(node_or_str, str):
            node = names[node_or_str]  # type: AsnNode
        else:
            node = node_or_str
        lines = []  # type: List[str]
        if isinstance(node, AsnBasicNode):
            realLeafType = leafTypeDict[node._leafType]
            if realLeafType == "INTEGER":
                lines.extend(self.MapInteger(srcVar, destVar, node, leafTypeDict, names))
            elif realLeafType == "REAL":
                lines.extend(self.MapReal(srcVar, destVar, node, leafTypeDict, names))
            elif realLeafType == "BOOLEAN":
                lines.extend(self.MapBoolean(srcVar, destVar, node, leafTypeDict, names))
            elif realLeafType == "OCTET STRING":
                lines.extend(self.MapOctetString(srcVar, destVar, node, leafTypeDict, names))
            else:
                panicWithCallStack("Basic type %s can't be mapped..." % realLeafType)
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

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
