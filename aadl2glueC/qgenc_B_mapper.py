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
This is the implementation of the code mapper for QGenc C code.
'''

# from commonPy.utility import panic
# from recursiveMapper import RecursiveMapper
# from asynchronousTool import ASynchronousToolGlueGenerator

import c_B_mapper

isAsynchronous = True
adaBackend = None
cBackend = None


def Version():
    print "Code generator: " + "$Id: qgenc_B_mapper.py $"  # pragma: no cover

# All the ada B mapper is now Obsolete, we are using ASN1SCC for Dumpables


def OnStartup(unused_modelingLanguage, asnFile, outputDir, maybeFVname, useOSS):
    global cBackend
    # 2009-02-10: Since we now use ASN1SCC structures as dumpables (even for Ada)
    # we no longer need these Ada-specific Dumpable structures.
    #global adaBackend
    #adaBackend = Ada_GlueGenerator()
    cBackend = c_B_mapper.C_GlueGenerator()
    #adaBackend.OnStartup(modelingLanguage, asnFile, outputDir, maybeFVname, useOSS)
    cBackend.OnStartup("C", asnFile, outputDir, maybeFVname, useOSS)


def OnBasic(nodeTypename, node, leafTypeDict, names):
    cBackend.OnBasic(nodeTypename, node, leafTypeDict, names)


def OnSequence(nodeTypename, node, leafTypeDict, names):
    cBackend.OnSequence(nodeTypename, node, leafTypeDict, names)


def OnSet(nodeTypename, node, leafTypeDict, names):
    cBackend.OnSet(nodeTypename, node, leafTypeDict, names)  # pragma: nocover


def OnEnumerated(nodeTypename, node, leafTypeDict, names):
    cBackend.OnEnumerated(nodeTypename, node, leafTypeDict, names)


def OnSequenceOf(nodeTypename, node, leafTypeDict, names):
    cBackend.OnSequenceOf(nodeTypename, node, leafTypeDict, names)


def OnSetOf(nodeTypename, node, leafTypeDict, names):
    cBackend.OnSetOf(nodeTypename, node, leafTypeDict, names)  # pragma: nocover


def OnChoice(nodeTypename, node, leafTypeDict, names):
    cBackend.OnChoice(nodeTypename, node, leafTypeDict, names)


def OnShutdown(unused_modelingLanguage, asnFile, maybeFVname):
    cBackend.OnShutdown("C", asnFile, maybeFVname)
