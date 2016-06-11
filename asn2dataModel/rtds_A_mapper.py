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
__doc__ = '''Implementation of mapping ASN.1 constructs
to RTDS. It is used by the backend of Semantix's code generator A.'''

import re

g_outputDir = ""
g_asnFile = ""


def Version():
    print("Code generator: " + "$Id: og_A_mapper.py 1879 2010-05-17 10:13:12Z ttsiodras $")  # pragma: no cover


def OnStartup(unused_modelingLanguage, asnFile, outputDir):
    global g_asnFile
    g_asnFile = asnFile
    global g_outputDir
    g_outputDir = outputDir


def OnBasic(nodeTypename, node, leafTypeDict):
    pass


def OnSequence(nodeTypename, node, leafTypeDict):
    pass


def OnSet(nodeTypename, node, leafTypeDict):
    pass


def OnEnumerated(nodeTypename, node, leafTypeDict):
    pass


def OnSequenceOf(nodeTypename, node, leafTypeDict):
    pass


def OnSetOf(nodeTypename, node, leafTypeDict):
    pass


def OnChoice(nodeTypename, node, leafTypeDict):
    pass


# obsolete, now the grammar is re-created from the AST (PrintGrammarFromAST)
#
#def ClearUp(text):
#    outputText = ""
#    lParen = 0
#    for c in text:
#        if c == '(':
#            lParen += 1
#        if c == ')':
#            lParen -= 1
#        if 0 == lParen:
#            outputText += c.replace('-', '_')
#        else:
#            outputText += c
#    return outputText

def OnShutdown():
#    text = open(g_asnFile, 'r').read()
#    text = re.sub(r'^.*BEGIN', 'Datamodel DEFINITIONS ::= BEGIN', text)
#    text = re.sub(r'--.*', '', text)

#    outputFile = open(g_outputDir + "DataView.pr", 'w')
#    outputFile.write('Datamodel DEFINITIONS ::= BEGIN\n\n')
#    import commonPy.xmlASTtoAsnAST
#    commonPy.xmlASTtoAsnAST.PrintGrammarFromAST(outputFile)
#    outputFile.write('END\n')
#    outputFile.close()

    outputFile = open(g_outputDir + "RTDSdataView.asn", 'w')
    outputFile.write(re.sub(r'^.*BEGIN', 'RTDSdataView DEFINITIONS ::= BEGIN', open(g_asnFile, 'r').read()))
    outputFile.close()
