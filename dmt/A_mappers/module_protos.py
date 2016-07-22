from types import ModuleType
from typing import List, Union

from ..commonPy.asnAST import AsnNode  # NOQA pylint: disable=unused-import
from ..commonPy.asnParser import Filename, Typename, AST_Lookup, AST_TypesOfFile, AST_Leaftypes  # NOQA pylint: disable=unused-import
from ..commonPy.cleanupNodes import SetOfBadTypenames


Filename_Or_ListOfFilenames = Union[str, List[str]]  # pylint: disable=invalid-sequence-index


class A_Mapper(ModuleType):
    def OnStartup(
            self, modelingLanguage: str, asnFile: Filename_Or_ListOfFilenames,
            outputDir: str, badTypes: SetOfBadTypenames) -> None:
        pass

    def OnBasic(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes) -> None:
        pass

    def OnSequence(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes) -> None:
        pass

    def OnSet(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes) -> None:
        pass

    def OnChoice(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes) -> None:
        pass

    def OnSequenceOf(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes) -> None:
        pass

    def OnSetOf(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes) -> None:
        pass

    def OnEnumerated(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes) -> None:
        pass

    def OnShutdown(self, badTypes: SetOfBadTypenames) -> None:
        pass
