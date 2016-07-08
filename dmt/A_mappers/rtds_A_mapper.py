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
'''Implementation of mapping ASN.1 constructs
to RTDS. It is used by the backend of Semantix's code generator A.'''

import re

from ..commonPy.cleanupNodes import SetOfBadTypenames
from ..commonPy.asnParser import AST_Leaftypes, AsnNode
from ..commonPy.asnAST import AsnSequenceOrSet, AsnSequenceOrSetOf, AsnEnumerated, AsnChoice

g_outputDir = ""
g_asnFile = ""


def Version() -> None:
    print("Code generator: " + "$Id: og_A_mapper.py 1879 2010-05-17 10:13:12Z ttsiodras $")  # pragma: no cover


def OnStartup(unused_modelingLanguage: str, asnFile: str, outputDir: str, unused_badTypes: SetOfBadTypenames) -> None:
    global g_asnFile
    g_asnFile = asnFile
    global g_outputDir
    g_outputDir = outputDir


def OnBasic(unused_nodeTypename: str, unused_node: AsnNode, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass


def OnSequence(unused_nodeTypename: str, unused_node: AsnSequenceOrSet, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass


def OnSet(unused_nodeTypename: str, unused_node: AsnSequenceOrSet, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnEnumerated(unused_nodeTypename: str, unused_node: AsnEnumerated, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass


def OnSequenceOf(unused_nodeTypename: str, unused_node: AsnSequenceOrSetOf, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass


def OnSetOf(unused_nodeTypename: str, unused_node: AsnSequenceOrSetOf, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnChoice(unused_nodeTypename: str, unused_node: AsnChoice, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass


# obsolete, now the grammar is re-created from the AST (PrintGrammarFromAST)
#
# def ClearUp(text):
#     outputText = ""
#     lParen = 0
#     for c in text:
#         if c == '(':
#             lParen += 1
#         if c == ')':
#             lParen -= 1
#         if 0 == lParen:
#             outputText += c.replace('-', '_')
#         else:
#             outputText += c
#     return outputText

def OnShutdown(unused_badTypes: SetOfBadTypenames) -> None:
    # text = open(g_asnFile, 'r').read()
    # text = re.sub(r'^.*BEGIN', 'Datamodel DEFINITIONS ::= BEGIN', text)
    # text = re.sub(r'--.*', '', text)
    # outputFile = open(g_outputDir + "DataView.pr", 'w')
    # outputFile.write('Datamodel DEFINITIONS ::= BEGIN\n\n')
    # import commonPy.xmlASTtoAsnAST
    # commonPy.xmlASTtoAsnAST.PrintGrammarFromAST(outputFile)
    # outputFile.write('END\n')
    # outputFile.close()

    outputFile = open(g_outputDir + "RTDSdataView.asn", 'w')
    outputFile.write(re.sub(r'^.*BEGIN', 'RTDSdataView DEFINITIONS ::= BEGIN', open(g_asnFile, 'r').read()))
    outputFile.close()
