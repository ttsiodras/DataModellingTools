#
# (C) Semantix Information Technologies.
#
# Copyright 2014-2015 IB Krates <info@krates.ee>
#       QGenc code generator integration
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
This is the implementation of the code mapper for Ada code.
As initially envisioned, ASSERT technology is not supposed
to support manually-made systems. A migration path, however,
that allows legacy hand-written code and modelling-tool
generated code to co-exist, can be beneficial in allowing
for a smooth transition. To that end, this backend (as well as
the C one) are written.

This is a backend for Semantix's code generator B (aadl2glueC).

Ada is a member of the asynchronous "club" (SDL, etc);
The subsystem developer (or rather, the APLC developer) is using
native Ada code to work with code generated by modelling tools.
To that end, this backend creates "glue" functions for input and
output parameters, which have Ada callable interfaces.
'''

# from commonPy.utility import panic
# from recursiveMapper import RecursiveMapper
# from asynchronousTool import ASynchronousToolGlueGenerator

from . import c_B_mapper
from ..commonPy.asnAST import AsnBasicNode, AsnSequence, AsnSet, AsnEnumerated, AsnSequenceOf, AsnSetOf, AsnChoice
from ..commonPy.asnParser import AST_Lookup, AST_Leaftypes

isAsynchronous = True
cBackend: c_B_mapper.C_GlueGenerator


# All the ada B mapper is now Obsolete, we are using ASN1SCC for Dumpables


def OnStartup(unused_modelingLanguage: str, asnFile: str, outputDir: str, maybeFVname: str, useOSS: bool) -> None:
    global cBackend
    # 2009-02-10: Since we now use ASN1SCC structures as dumpables (even for Ada)
    # we no longer need these Ada-specific Dumpable structures.
    cBackend = c_B_mapper.C_GlueGenerator()
    cBackend.OnStartup("C", asnFile, outputDir, maybeFVname, useOSS)


def OnBasic(nodeTypename: str, node: AsnBasicNode, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    cBackend.OnBasic(nodeTypename, node, leafTypeDict, names)


def OnSequence(nodeTypename: str, node: AsnSequence, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    cBackend.OnSequence(nodeTypename, node, leafTypeDict, names)


def OnSet(nodeTypename: str, node: AsnSet, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    cBackend.OnSet(nodeTypename, node, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename: str, node: AsnEnumerated, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    cBackend.OnEnumerated(nodeTypename, node, leafTypeDict, names)


def OnSequenceOf(nodeTypename: str, node: AsnSequenceOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    cBackend.OnSequenceOf(nodeTypename, node, leafTypeDict, names)


def OnSetOf(nodeTypename: str, node: AsnSetOf, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    cBackend.OnSetOf(nodeTypename, node, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename: str, node: AsnChoice, leafTypeDict: AST_Leaftypes, names: AST_Lookup) -> None:
    cBackend.OnChoice(nodeTypename, node, leafTypeDict, names)


def OnShutdown(unused_modelingLanguage: str, asnFile: str, maybeFVname: str) -> None:
    cBackend.OnShutdown("C", asnFile, maybeFVname)
