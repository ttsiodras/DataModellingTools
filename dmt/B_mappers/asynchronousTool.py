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
'''
Base class for all asynchronous tools
'''

import re
import os

from typing import Tuple, IO, Any, Dict  # NOQA pylint: disable=unused-import

from ..commonPy.utility import inform, panicWithCallStack
from ..commonPy.asnParser import Typename, AsnNode, AST_Lookup, AST_Leaftypes  # NOQA pylint: disable=unused-import


class ASynchronousToolGlueGenerator:

    ################################################
    # Parts to override for each asynchronous tool

    def Version(self) -> None:  # pylint: disable=no-self-use
        panicWithCallStack("Method undefined in a ASynchronousToolGlueGenerator...")  # pragma: no cover

    def HeadersOnStartup(self,  # pylint: disable=no-self-use
                         unused_asnFile: str,
                         unused_outputDir: str,
                         unused_maybeFVname: str) -> None:
        panicWithCallStack("Method undefined in a ASynchronousToolGlueGenerator...")  # pragma: no cover

    def Encoder(self,  # pylint: disable=no-self-use
                unused_nodeTypename: str,
                unused_node: AsnNode,
                unused_leafTypeDict: AST_Leaftypes,
                unused_names: AST_Lookup,
                unused_encoding: str) -> None:
        panicWithCallStack("Method undefined in a ASynchronousToolGlueGenerator...")  # pragma: no cover

    def Decoder(self,  # pylint: disable=no-self-use
                unused_nodeTypename: str,
                unused_node: AsnNode,
                unused_leafTypeDict: AST_Leaftypes,
                unused_names: AST_Lookup,
                unused_encoding: str) -> None:
        panicWithCallStack("Method undefined in a ASynchronousToolGlueGenerator...")  # pragma: no cover

    ########################################################
    # Parts to possibly override for each synchronous tool

    # noinspection PyMethodMayBeStatic
    def CleanNameAsToolWants(self, name: str) -> str:  # pylint: disable=no-self-use
        return re.sub(r'[^a-zA-Z0-9_]', '_', name)

    ##########################################
    # Common parts for all asynchronous tools

    def __init__(self) -> None:
        # The files written to
        self.asn_name = ""
        self.supportedEncodings = ['native', 'uper', 'acn']
        self.useOSS = False
        self.typesToWorkOn = {}  # type: Dict[str, Tuple[AsnNode, AST_Leaftypes, AST_Lookup]]

    def OnStartup(self, modelingLanguage: str, asnFile: str, outputDir: str, maybeFVname: str, useOSS: bool) -> None:
        self.useOSS = useOSS
        prefix = modelingLanguage
        if prefix == "SDL":
            prefix = "OG"
        outputCheaderFilename = self.CleanNameAsToolWants(prefix) + "_ASN1_Types.h"
        outputCsourceFilename = self.CleanNameAsToolWants(prefix) + "_ASN1_Types.c"

        inform(str(self.__class__) + ": Creating file '%s'...", outputCheaderFilename)
        self.C_HeaderFile = open(outputDir + outputCheaderFilename, 'w')  # pylint: disable=attribute-defined-outside-init

        inform(str(self.__class__) + ": Creating file '%s'...", outputCsourceFilename)
        self.C_SourceFile = open(outputDir + outputCsourceFilename, 'w')  # pylint: disable=attribute-defined-outside-init

        self.asn_name = os.path.basename(os.path.splitext(asnFile)[0])

        ID = modelingLanguage + "_" + self.asn_name.replace(".", "")
        ID = re.sub(r'[^A-Za-z0-9_]', '_', ID).upper()
        self.C_HeaderFile.write("#ifndef __%s_H__\n" % ID)
        self.C_HeaderFile.write("#define __%s_H__\n\n" % ID)
        self.C_HeaderFile.write("#if defined( __unix__ ) || defined( __MSP430__ )\n")
        self.C_HeaderFile.write("#include <stdlib.h> /* for size_t */\n")
        self.C_HeaderFile.write("#else\n")
        self.C_HeaderFile.write("typedef unsigned size_t;\n")
        self.C_HeaderFile.write("#endif\n\n")
        self.C_HeaderFile.write("#ifndef STATIC\n")
        self.C_HeaderFile.write("#define STATIC\n")
        self.C_HeaderFile.write("#endif\n\n")
        self.C_HeaderFile.write("\n")
        self.C_SourceFile.write("#ifdef __unix__\n")
        self.C_SourceFile.write("#include <stdio.h>\n")
        self.C_SourceFile.write("#include <assert.h>\n")
        self.C_SourceFile.write("#endif\n\n")
        self.C_SourceFile.write("#include <string.h>\n\n")
        self.C_SourceFile.write("#include \"%s\"\n\n" % outputCheaderFilename)

        self.HeadersOnStartup(asnFile, outputDir, maybeFVname)

    def Common(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        # Async backends are different: they work on ASN.1 types, not SP params.

        # OG for example, needs macros to be generated, not functions. This breaks the normal
        # encapsulation we followed for synchronous tools, because we can't create encoding
        # and decoding functions that work on their arguments. The reason for this is that
        # in contrast with the synchronous world (SCADE and MATLAB/Simulink), we can't use
        # global variables as targets for OG. Being asynchronous, OG-generated code can call
        # an external function whenever it wishes, and it needs message-specific work inside
        # it. That in itself is not bad, but what is bad is the fact that we can't predict
        # the type name used for the message (it is randomly numbered, and it can't be predicted
        # by the ASN.1 typename alone). We therefore resorted to macros... and we thus can't
        # employ a common scheme for all asynchronous tools where we generate functions
        # in the context of this method... Instead, we have to delegate all work to members
        # defined in the derived classes...
        self.Encoder(nodeTypename, node, leafTypeDict, names, 'uper')
        self.Encoder(nodeTypename, node, leafTypeDict, names, 'acn')
        self.Encoder(nodeTypename, node, leafTypeDict, names, 'native')
        self.Decoder(nodeTypename, node, leafTypeDict, names, 'uper')
        self.Decoder(nodeTypename, node, leafTypeDict, names, 'acn')
        self.Decoder(nodeTypename, node, leafTypeDict, names, 'native')

    def OnBasic(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        realLeafType = leafTypeDict[nodeTypename]
        inform(str(self.__class__) + ": BASE: %s (%s)", nodeTypename, realLeafType)
        self.typesToWorkOn[nodeTypename] = (node, leafTypeDict, names)

    def OnSequence(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        inform(str(self.__class__) + ": SEQUENCE: %s", nodeTypename)
        self.typesToWorkOn[nodeTypename] = (node, leafTypeDict, names)

    def OnSet(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        inform(str(self.__class__) + ": SET: %s", nodeTypename)  # pragma: nocover
        self.typesToWorkOn[nodeTypename] = (node, leafTypeDict, names)  # pragma: nocover

    def OnEnumerated(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        inform(str(self.__class__) + ": ENUMERATED: %s", nodeTypename)
        self.typesToWorkOn[nodeTypename] = (node, leafTypeDict, names)

    def OnSequenceOf(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        inform(str(self.__class__) + ": SEQUENCEOF: %s", nodeTypename)
        self.typesToWorkOn[nodeTypename] = (node, leafTypeDict, names)

    def OnSetOf(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        inform(str(self.__class__) + ": SETOF: %s", nodeTypename)  # pragma: nocover
        self.typesToWorkOn[nodeTypename] = (node, leafTypeDict, names)  # pragma: nocover

    def OnChoice(self, nodeTypename: str, node: AsnNode, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
        inform(str(self.__class__) + ": CHOICE: %s", nodeTypename)
        self.typesToWorkOn[nodeTypename] = (node, leafTypeDict, names)

    def OnShutdown(self, unused_modelingLanguage: str, unused_asnFile: str, unused_maybeFVname: str) -> None:
        for nodeTypename, value in self.typesToWorkOn.items():
            inform(str(self.__class__) + "Really working on " + nodeTypename)
            (node, leafTypeDict, names) = value
            self.Common(nodeTypename, node, leafTypeDict, names)
        self.C_HeaderFile.write("\n#endif\n")
        self.C_HeaderFile.close()
        self.C_SourceFile.close()
