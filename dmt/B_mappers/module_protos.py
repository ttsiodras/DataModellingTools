from types import ModuleType

from ..commonPy.asnAST import AsnNode  # NOQA pylint: disable=unused-import
from ..commonPy.aadlAST import ApLevelContainer, Param  # NOQA pylint: disable=unused-import
from ..commonPy.asnParser import Filename, Typename, AST_Lookup, AST_TypesOfFile, AST_Leaftypes  # NOQA pylint: disable=unused-import


class Sync_B_Mapper(ModuleType):
    def OnStartup(
            self, modelingLanguage: str, asnFile: str, sp: ApLevelContainer,
            sp_impl: str, outputDir: str, maybeFVname: str, useOSS: bool) -> None:
        pass

    def OnBasic(
            self, nodeTypename: str, node: AsnNode, sp: ApLevelContainer,
            sp_impl: str, param: Param, leafTypeDict: AST_Leaftypes,
            names: AST_Lookup) -> None:
        pass

    def OnSequence(
            self, nodeTypename: str, node: AsnNode, sp: ApLevelContainer,
            sp_impl: str, param: Param, leafTypeDict: AST_Leaftypes,
            names: AST_Lookup) -> None:
        pass

    def OnSet(
            self, nodeTypename: str, node: AsnNode, sp: ApLevelContainer,
            sp_impl: str, param: Param, leafTypeDict: AST_Leaftypes,
            names: AST_Lookup) -> None:
        pass

    def OnChoice(
            self, nodeTypename: str, node: AsnNode, sp: ApLevelContainer,
            sp_impl: str, param: Param, leafTypeDict: AST_Leaftypes,
            names: AST_Lookup) -> None:
        pass

    def OnSequenceOf(
            self, nodeTypename: str, node: AsnNode, sp: ApLevelContainer,
            sp_impl: str, param: Param, leafTypeDict: AST_Leaftypes,
            names: AST_Lookup) -> None:
        pass

    def OnSetOf(
            self, nodeTypename: str, node: AsnNode, sp: ApLevelContainer,
            sp_impl: str, param: Param, leafTypeDict: AST_Leaftypes,
            names: AST_Lookup) -> None:
        pass

    def OnEnumerated(
            self, nodeTypename: str, node: AsnNode, sp: ApLevelContainer,
            sp_impl: str, param: Param, leafTypeDict: AST_Leaftypes,
            names: AST_Lookup) -> None:
        pass

    def OnShutdown(
            self, modelingLanguage: str, asnFile: str, sp: ApLevelContainer,
            sp_impl: str, maybeFVname: str) -> None:
        pass

    def OnFinal(
            self) -> None:
        pass


class Async_B_Mapper(ModuleType):
    def OnStartup(
            self, modelingLanguage: str, asnFile: str, outputDir: str,
            maybeFVname: str, useOSS: bool) -> None:
        pass

    def OnBasic(
            self, nodeTypename: str, node: AsnNode,
            leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        pass

    def OnSequence(
            self, nodeTypename: str, node: AsnNode,
            leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        pass

    def OnSet(
            self, nodeTypename: str, node: AsnNode,
            leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        pass

    def OnChoice(
            self, nodeTypename: str, node: AsnNode,
            leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        pass

    def OnSequenceOf(
            self, nodeTypename: str, node: AsnNode,
            leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        pass

    def OnSetOf(
            self, nodeTypename: str, node: AsnNode,
            leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        pass

    def OnEnumerated(
            self, nodeTypename: str, node: AsnNode,
            leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        pass

    def OnShutdown(
            self, modelingLanguage: str, asnFile: str, maybeFVname: str) -> None:
        pass
