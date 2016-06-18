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
from typing import Any, Dict, List  # NOQA pylint: disable=unused-import

import commonPy.asnParser

from commonPy.asnAST import (
    AsnString, AsnBasicNode, AsnSetOf, AsnSequenceOf, AsnSet,
    AsnSequence, AsnChoice, AsnMetaMember, AsnEnumerated,
    AsnNode
)
from commonPy.utility import panic


# Separate cache per ASN.1 AST dictionary (i.e. per 'names' parameter of ScanChildren)
g_ScanChildrenCache = {}  # type: Dict[int, Dict[str, List[str]]]


def CleanName(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def CreatePseudoType(
        pseudoType: str, origASTnode: AsnNode,
        names: Dict[str, AsnNode], results: List[str]) -> str:  # pylint: disable=invalid-sequence-index
    # if such a pseudo type already exists, add "_t" postfix until you get
    # one that doesn't exist.
    if pseudoType in names and names[pseudoType] != origASTnode:
        while pseudoType in names:  # pragma: no cover
            pseudoType += "_t"      # pragma: no cover
    # Add the (artificial) new type to the global type dictionary
    names[pseudoType] = origASTnode
    origASTnode._isArtificial = True
    # and add the pseudo type to the dependency list
    if pseudoType not in results:
        results.append(pseudoType)
    return pseudoType


def ScanChildren(
        nodeTypename: str,
        node: AsnNode,
        names: Dict[str, AsnNode],
        results: List[str],  # pylint: disable=invalid-sequence-index

        isRoot=False,
        createInnerNodesInNames=True):
    '''
    Find all the types that this one (nodeTypename, node) depends on.
    and return them in the 'results' list. Use 'names' to lookup
    typedefs (AsnNode) from their type name, and if createInnerNodesInNames
    is set, create names for unnamed inner types (used e.g. in the
    Simulink/QGen mappers). isRoot is set to True by the caller, but is
    not set in the recursive calls made here.
    '''
    # only for the first call (and not the recursive ones done
    # from within ScanChildren), check to see if the descendants
    # are available in the cache
    if isRoot and nodeTypename in g_ScanChildrenCache.setdefault(id(names), {}):
        results[:] = g_ScanChildrenCache[id(names)][nodeTypename]  # pragma: no cover
        return  # pragma: no cover

    # for typedefs, just add the original type as a dependency
    if id(names) == id(commonPy.asnParser.g_names) and nodeTypename in commonPy.asnParser.g_metatypes:
        results.append(commonPy.asnParser.g_metatypes[nodeTypename])
        return

    if isinstance(node, AsnString):
        # if we are here via a recursive call from a "parent" ScanChildren,
        # add the string's nodeTypename to the dependency list (e.g. the
        # original node was a SEQUENCE OF that contained a string type)
        if (not isRoot) and nodeTypename not in results:
            results.append(nodeTypename)
        # else, is the original call is about a string, there's no dependency
        return
    elif isinstance(node, AsnBasicNode):
        # for all the other Basic nodes (except strings), there's no dependency
        return
    elif isinstance(node, (AsnSetOf, AsnSequenceOf)):
        # For arrays or sets of "stuff", if we are here via a recursive call
        # from a "parent" ScanChildren, add the nodeTypename to the dependency list.
        if (not isRoot) and nodeTypename not in results:
            results.append(nodeTypename)
        if isinstance(node._containedType, str):
            # if the contained type is not nameless (e.g. like Seq Of SomeTypeName)
            # then add SomeTypeName to the dependency list (if it's not there already).
            if node._containedType not in results:
                results.append(node._containedType)
            # Also, find the dependency list of the contained type (SomeTypeName)
            resultsInner = []  # type: List[str]
            ScanChildren(node._containedType, names[node._containedType], names, resultsInner,
                         False, createInnerNodesInNames)
            # ...and add its contents to this dependency list (uniquely)
            for i in resultsInner:
                if i not in results:
                    results.append(i)
        else:
            if createInnerNodesInNames:
                # the contained type is not a string, its an AST node.
                # use a pseudo name...
                pseudoType = "contained_in_" + CleanName(nodeTypename)
                pseudoType = CreatePseudoType(pseudoType, node._containedType, names, results)
                # ... and change the AST, placing the string value (pseudoType)
                # inside the _containedType member (i.e. remove the pointer to the AST node)
                node._containedType = pseudoType
    elif isinstance(node, (AsnSet, AsnSequence, AsnChoice)):  # pylint: disable=too-many-nested-blocks
        # If we are here via a recursive call from a "parent" ScanChildren,
        # add the SET/SEQUENCE/CHOICE nodeTypename to the dependency list.
        if (not isRoot) and nodeTypename not in results:
            results.append(nodeTypename)
        # Now check the contained fields...
        for child in node._members:
            if isinstance(child[1], AsnMetaMember):
                # if the field is of type SomeTypeName, add SomeTypeName to the dependency list
                if child[1]._containedType not in results:
                    results.append(child[1]._containedType)
                # Also, find the dependencies of SomeTypeName...
                resultsInner = []
                ScanChildren(child[1]._containedType, names[child[1]._containedType], names, resultsInner,
                             False, createInnerNodesInNames)
                # ... and add them as well.
                for i in resultsInner:
                    if i not in results:
                        results.append(i)
            elif isinstance(child[1], (AsnSequenceOf, AsnSetOf)):
                # This code is not necessary (and is currently never called) because the
                # asnParser uses VerifyAndFixAST to replace nameless types usage
                # from within SEQUENCE/SET OFs, SEQUENCE/SET and CHOICEs (See end of VerifyAndFixAST)

                # (see comment above about these pragma nocovers)

                # if the field is SET/SEQ OF, find the AST node for the contained type
                if isinstance(child[1]._containedType, str):                                    # pragma: no cover
                    childNode = names[child[1]._containedType]                                  # pragma: no cover
                else:                                                                           # pragma: no cover
                    childNode = child[1]._containedType                                         # pragma: no cover
                if createInnerNodesInNames:                                                     # pragma: no cover
                    # Create a "pseudo" type from the fieldname + "_type"                       # pragma: no cover
                    pseudoType = CleanName(child[0][:1].capitalize() + child[0][1:] + "_type")  # pragma: no cover
                    pseudoType = "TaStE_" + pseudoType                                # pragma: no cover
                    pseudoType = CreatePseudoType(pseudoType, child[1], names, results)         # pragma: no cover
                    # Also, find the dependencies of the pseudo-type...                         # pragma: no cover
                    resultsInner = []                                                           # pragma: no cover
                    if isinstance(child[1]._containedType, str):                                # pragma: no cover
                        ScanChildren(child[1]._containedType, childNode, names, resultsInner,
                                     False, createInnerNodesInNames)                            # pragma: no cover
                    else:                                                                       # pragma: no cover
                        ScanChildren('', childNode, names, resultsInner,
                                     False, createInnerNodesInNames)                            # pragma: no cover
                    # ...and add them as well.                                                  # pragma: no cover
                    for i in resultsInner:                                                      # pragma: no cover
                        if i not in results:
                            results.append(i)                                                   # pragma: no cover
            elif isinstance(child[1], AsnString):
                if createInnerNodesInNames:                                                     # pragma: no cover
                    # if the field is a string, create a unique pseudo-type name
                    # from the fieldname + "_type", and append it to the dependency list
                    pseudoType = CleanName(child[0][:1].capitalize() + child[0][1:] + "_type")  # pragma: no cover
                    pseudoType = "TaStE_" + pseudoType                                          # pragma: no cover
                    pseudoType = CreatePseudoType(pseudoType, child[1], names, results)         # pragma: no cover
                    # store the string's pseudo type name in the _pseudoname attribute.
                    child[1]._pseudoname = pseudoType                                           # pragma: no cover
            elif isinstance(child[1], AsnEnumerated):
                # if the field is an ENUMERATED, create a unique pseudo-type name
                # from the fieldname + "_type", and append it to the dependency list
                # But first, check...
                for x in child[1]._members:                                                     # pragma: no cover
                    if x[1] is None:                                                            # pragma: no cover
                        panic("The mapper needs integer values in the enumeration options (%s)" % node.Location())  # pragma: no cover
                if createInnerNodesInNames:                                                     # pragma: no cover
                    pseudoType = CleanName(child[0][:1].capitalize() + child[0][1:] + "_type")  # pragma: no cover
                    pseudoType = "TaStE_" + pseudoType                                          # pragma: no cover
                    pseudoType = CreatePseudoType(pseudoType, child[1], names, results)         # pragma: no cover
                    # store the string's pseudo type name in the _pseudoname attribute.
                    child[1]._pseudoname = pseudoType                                           # pragma: no cover
    elif isinstance(node, AsnEnumerated):
        pass
    else:  # pragma: no cover
        panic("ScanChildren: Unexpected %s" % str(node))  # pragma: no cover
    if isRoot:
        # when all dependencies are figured out, store them in the cache - but only
        # for the original ScanChildren call, not for the recursive ones that it did itself...
        g_ScanChildrenCache[id(names)][nodeTypename] = results[:]

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
