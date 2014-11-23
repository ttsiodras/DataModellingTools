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
'''This contains the implementation of model level mapping
of ASN.1 constructs to C. It is used as a backend of Semantix's
code generator A.'''

import os
import sys

from commonPy.utility import panic


def Version():
    print "Code generator: " + "$Id: ada_A_mapper.py 2382 2012-06-22 08:35:33Z ttsiodras $"  # pragma: no cover


# Especially for the C mapper, since we need to pass the complete ASN.1 files list to ASN1SCC,
# the second param is not asnFile, it is asnFiles


def OnStartup(unused_modelingLanguage, asnFiles, outputDir):
    #print "Use ASN1SCC to generate the structures for '%s'" % asnFile
    if None == os.getenv("ASN1SCC"):
        if None == os.getenv("DMT"):  # pragma: no cover
            panic("DMT environment variable is not set, you must set it.")  # pragma: no cover
        os.putenv("ASN1SCC", os.getenv("DMT") + os.sep + "asn1scc/asn1.exe")  # pragma: no cover
    os.system(
        ("mono " if sys.argv[0].endswith('.py') and sys.platform.startswith('linux') else "") +
        "\"$ASN1SCC\" -wordSize 8 -typePrefix asn1Scc -Ada -uPER -o \"" + outputDir + "\" \"" + "\" \"".join(asnFiles) + "\"")
    os.system("rm -f \"" + outputDir + "\"/*.adb")


def OnBasic(nodeTypename, node, leafTypeDict):
    pass  # pragma: no cover


def OnSequence(nodeTypename, node, leafTypeDict):
    pass  # pragma: no cover


def OnSet(nodeTypename, node, leafTypeDict):
    pass  # pragma: no cover


def OnEnumerated(nodeTypename, node, leafTypeDict):
    pass  # pragma: no cover


def OnSequenceOf(nodeTypename, node, leafTypeDict):
    pass  # pragma: no cover


def OnSetOf(nodeTypename, node, leafTypeDict):
    pass  # pragma: no cover


def OnChoice(nodeTypename, node, leafTypeDict):
    pass  # pragma: no cover


def OnShutdown():
    pass  # pragma: no cover
