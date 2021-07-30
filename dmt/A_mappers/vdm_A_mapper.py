#
# Wrapper around vdm.stg (packaged in the ASN1SCC compiler)
#
'''
This contains the implementation of model level mapping of
ASN.1 constructs to VDM (via the excellent StringTemplate
file created by Maxime Perrotin.
'''

import os
from distutils import spawn

from typing import List, Union
from ..commonPy.utility import panic
from ..commonPy.cleanupNodes import SetOfBadTypenames
from ..commonPy.asnAST import AsnBasicNode, AsnSequenceOrSet, AsnSequenceOrSetOf, AsnEnumerated, AsnChoice
from ..commonPy.asnParser import AST_Leaftypes


def Version() -> None:
    print("Code generator: " + "$Id: vdm_A_mapper.py 2382 2012-06-22 08:35:33Z ttsiodras $")  # pragma: no cover


# Especially for the C mapper, since we need to pass the complete ASN.1 files list to ASN1SCC,
# the second param is not asnFile, it is asnFiles


def OnStartup(unused_modelingLanguage: str, asnFile: Union[str, List[str]], outputDir: str, unused_badTypes: SetOfBadTypenames) -> None:  # pylint: disable=invalid-sequence-index
    # print "Use ASN1SCC to generate the structures for '%s'" % asnFile
    asn1SccPath = spawn.find_executable('asn1scc')
    if not asn1SccPath:
        panic("ASN1SCC seems to be missing from your system (asn1scc not found in PATH).\n")  # pragma: no cover
    asn1SccFolder = os.path.dirname(asn1SccPath)
    cmd = "\"{}\" -customStg \"{}\"/vdm.stg:\"{}\"/out.vdm \"".format(
        asn1SccPath, asn1SccFolder, outputDir)
    if isinstance(asnFile, str):
        cmd += asnFile + "\""
    else:
        cmd += "\" \"".join(asnFile) + "\""
    if os.system(cmd) != 0:
        panic("ASN1SCC failed...")
    else:
        print("Generated:", os.path.realpath("\"{}\"/out.vdm".format(outputDir)).replace('/"./"/', ''))


def OnBasic(unused_nodeTypename: str, unused_node: AsnBasicNode, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnSequence(unused_nodeTypename: str, unused_node: AsnSequenceOrSet, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnSet(unused_nodeTypename: str, unused_node: AsnSequenceOrSet, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnEnumerated(unused_nodeTypename: str, unused_node: AsnEnumerated, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnSequenceOf(unused_nodeTypename: str, unused_node: AsnSequenceOrSetOf, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnSetOf(unused_nodeTypename: str, unused_node: AsnSequenceOrSetOf, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnChoice(unused_nodeTypename: str, unused_node: AsnChoice, unused_leafTypeDict: AST_Leaftypes) -> None:
    pass  # pragma: no cover


def OnShutdown(unused_badTypes: SetOfBadTypenames) -> None:
    pass  # pragma: no cover
