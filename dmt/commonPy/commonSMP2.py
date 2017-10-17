import re
import sys

from lxml import etree

from typing import List, Union, Optional, Any, Tuple, Dict, NoReturn  # NOQA pylint: disable=unused-import

from .asnAST import (
    AsnBool, AsnInt, AsnReal, AsnEnumerated, AsnOctetString, AsnSequenceOf,
    AsnSet, AsnSetOf, AsnSequence, AsnChoice, AsnMetaMember, AsnNode)
from .asnParser import AST_Lookup

# Level of verbosity
g_verboseLevel = 0

# colors (used when calling 'info')
ESC = chr(27)
red = ESC + "[31m"
green = ESC + "[32m"
white = ESC + "[0m"
yellow = ESC + "[33m"
colors = [red, green, white, yellow]


# Lookup table for SMP2 types that map to AsnBasicNodes
class MagicSmp2SimpleTypesDict(dict):
    def __getitem__(self, name: str) -> Any:
        # strip 'http://www.esa.int/XXXX/YY/Smp#Bool'
        # to    'http://www.esa.int/Smp#Bool'
        name = re.sub(r'/\d{4}/\d{2}/', '/', name)
        return super(MagicSmp2SimpleTypesDict, self).__getitem__(name)

    # ---------------------------------------------------------------------------
    def __contains__(self, name: Any) -> bool:
        name = re.sub(r'/\d{4}/\d{2}/', '/', name)
        return super(MagicSmp2SimpleTypesDict, self).__contains__(name)

    # ---------------------------------------------------------------------------
    def has_key(self, name: str) -> bool:
        name = re.sub(r'/\d{4}/\d{2}/', '/', name)
        # return name in super(MagicSmp2SimpleTypesDict, self)  # pylint: disable=unsupported-membership-test
        return super(MagicSmp2SimpleTypesDict, self).__contains__(name)


simpleTypesTable = MagicSmp2SimpleTypesDict({
    'http://www.esa.int/Smp#Bool': (AsnBool, None, None),
    'http://www.esa.int/Smp#Char8': (AsnInt, 0, 255),
    'http://www.esa.int/Smp#DateTime': (AsnOctetString, 30, 30),
    'http://www.esa.int/Smp#Duration': (AsnInt, 0, 2147483647),
    'http://www.esa.int/Smp#Int8': (AsnInt, -128, 127),
    'http://www.esa.int/Smp#Int16': (AsnInt, -32768, 32767),
    'http://www.esa.int/Smp#Int32': (AsnInt, -2147483648, 2147483647),
    'http://www.esa.int/Smp#Int64': (AsnInt, -9223372036854775808, 9223372036854775807),
    'http://www.esa.int/Smp#UInt8': (AsnInt, 0, 255),
    'http://www.esa.int/Smp#UInt16': (AsnInt, 0, 65535),
    'http://www.esa.int/Smp#UInt32': (AsnInt, 0, 4294967295),
    'http://www.esa.int/Smp#UInt64': (AsnInt, 0, 9223372036854775807),
    'http://www.esa.int/Smp#Float32': (AsnReal, -3.4E37, 3.4E37),
    'http://www.esa.int/Smp#Float64': (AsnReal, -1.8E307, 1.8E307)
})


def setVerbosity(level: int) -> None:
    global g_verboseLevel
    g_verboseLevel = level


def info(level: int, *args: Any) -> None:
    """Checks the 'level' argument against g_verboseLevel and then prints
    the rest of the args, one by one, separated by a space. It also
    has logic to deal with usage of one of the colors as arguments
    (in which case it avoids printing spurious spaces).
    """
    if not args:
        panic("You called info without args")  # pragma: no cover
    if level <= g_verboseLevel:
        for i in range(len(args)):  # pylint: disable=consider-using-enumerate
            if i != 0 and args[i - 1] not in colors:
                sys.stdout.write(' ')
            sys.stdout.write(args[i])
        for i in range(len(args) - 1, -1, -1):
            if args[i] in colors:
                continue
            if not args[i].endswith('\n'):
                sys.stdout.write('\n')
                return


def panic(x: str, coloredBanner: str="") -> NoReturn:
    """Notifies the user that something fatal happened and aborts. """
    info(0, yellow + coloredBanner + white + '\n' + x)
    sys.exit(1)


class DashUnderscoreAgnosticDict(dict):
    """A dictionary that automatically replaces '_' to '-' in its keys. """
    def __setitem__(self, key: Any, value: Any) -> None:
        super(DashUnderscoreAgnosticDict, self).__setitem__(key.replace('_', '-'), value)

    def __getitem__(self, key: Any) -> Any:
        return super(DashUnderscoreAgnosticDict, self).__getitem__(key.replace('_', '-'))

    def __contains__(self, key: Any) -> bool:
        return super(DashUnderscoreAgnosticDict, self).__contains__(key.replace('_', '-'))


class Attributes:
    """Helper class, to ease access to XML attributes.
    It allows us to write code like this...

            a = Attributes(lxmlEtreeNode)
            whatever = a.href
            print a.title

        ...instead of this:

            whatever = lxmlEtreeNode.get('href', None)
            print a.get('title', None)
    """
    base = None  # type: str
    sourceline = None  # type: int

    def __init__(self, t: Dict[str, Any]) -> None:
        """Argument t is an lxml Etree node."""
        self._attrs = {}  # type: Dict[str, Any]
        for k, v in list(t.items()):
            endBraceIdx = k.find('}')
            if endBraceIdx != -1:
                k = k[endBraceIdx + 1:]
            self._attrs[k] = v

    def __getattr__(self, x: str) -> Any:
        return self._attrs.get(x, None)


def Clean(fieldName: str) -> str:
    """When mapping field names and type names from SMP2 to ASN.1,
    we need to change '_' to '-'. """
    return re.sub(r'[^a-zA-Z0-9-]', '-', fieldName)


def MapSMP2Type(
        attrs: Attributes,
        enumOptions: List[Tuple[str, str]],
        itemTypes: List[Any],  # pylint: disable=invalid-sequence-index
        fields: List[Any]) -> AsnNode:  # pylint: disable=invalid-sequence-index
    """
    Core mapping function. Works on the XML attributes of the lxml Etree node,
    and returns a node from commonPy.asnAST.
    """
    location = 'from %s, in line %s' % (attrs.base, attrs.sourceline)
    info(2, "Mapping SMP2 type", location)

    def getMaybe(cast: Any, x: str) -> Optional[Any]:
        try:
            return cast(x)
        except:  # pragma: no cover
            return None  # pragma: no cover
    dataDict = {"asnFilename": attrs.base, "lineno": attrs.sourceline}

    def HandleTypesInteger() -> Union[AsnBool, AsnInt]:
        lowRange = getMaybe(int, attrs.Minimum)
        highRange = getMaybe(int, attrs.Maximum)
        if lowRange == 0 and highRange == 1:
            # Pseudo-boolean from TASTE mapping, as per SpaceBel instructions
            return AsnBool(**dataDict)
        else:
            # Normal integer
            spanRange = [lowRange, highRange] if lowRange is not None and highRange is not None else []
            dataDict["range"] = spanRange
            return AsnInt(**dataDict)

    def HandleTypesFloat() -> AsnReal:
        lowRange = getMaybe(float, attrs.Minimum)
        highRange = getMaybe(float, attrs.Maximum)
        spanRange = [lowRange, highRange] if lowRange is not None and highRange is not None else []
        dataDict["range"] = spanRange
        return AsnReal(**dataDict)

    def HandleTypesArray() -> Union[AsnOctetString, AsnSequenceOf]:
        if not itemTypes:
            panic("Missing mandatory ItemType element", location)  # pragma: no cover
        itemTypeAttrs = Attributes(itemTypes[0])
        arrSize = getMaybe(int, attrs.Size)
        if not arrSize:
            panic("Missing array 'Size' attribute", location)  # pragma: no cover
        dataDict["range"] = [arrSize, arrSize]
        if itemTypeAttrs.href in [
                'http://www.esa.int/2005/10/Smp#Char8',
                'http://www.esa.int/2005/10/Smp#Int8',
                'http://www.esa.int/2005/10/Smp#UInt8']:
            return AsnOctetString(**dataDict)
        else:
            containedHref = itemTypeAttrs.href
            if not containedHref:
                panic("Missing reference to 'href' (file:%s, line:%d)" %
                      (itemTypeAttrs.base, itemTypeAttrs.sourceline))  # pragma: no cover
            idxHash = containedHref.find('#')
            if -1 != idxHash:
                containedHref = containedHref[idxHash + 1:]
            if itemTypeAttrs.href in simpleTypesTable:
                # Create the AsnBasicNode this child maps to.
                cast, lowRange, highRange = simpleTypesTable[itemTypeAttrs.href]
                spanRange = [lowRange, highRange] if lowRange is not None and highRange is not None else []
                childDict = {
                    'asnFilename': itemTypes[0].base,
                    'lineno': itemTypes[0].sourceline
                }
                if spanRange:
                    childDict['range'] = spanRange
                childNode = cast(**childDict)
                dataDict['containedType'] = childNode
            else:
                # Store the 'Id' attribute - we will resolve this
                # in the FixupOutOfOrderIdReferences function.
                dataDict['containedType'] = containedHref
            return AsnSequenceOf(**dataDict)

    def HandleTypesStructure() -> Union[AsnChoice, AsnSequence]:
        members = []
        for field in fields:
            try:
                fieldName = field.get('Name')
                if fieldName != 'choiceIdx':
                    fieldName = Clean(fieldName)
                    fieldName = fieldName[0].lower() + fieldName[1:]
                    try:
                        refTypeAttrs = Attributes(field.xpath("Type")[0])
                    except:  # pragma: no cover
                        loc = 'from %s, in line %s' % \
                              (field.base, field.sourceline)  # pragma: no cover
                        panic("Missing Type child element", loc)  # pragma: no cover
                    refTypeHref = refTypeAttrs.href
                    idxHash = refTypeHref.find('#')
                    if -1 != idxHash:
                        refTypeHref = refTypeHref[idxHash + 1:]
                    if refTypeAttrs.href in simpleTypesTable:
                        cast, lowRange, highRange = simpleTypesTable[refTypeAttrs.href]
                        containedDict = {
                            'asnFilename': field.base,
                            'lineno': field.sourceline
                        }
                        spanRange = [lowRange, highRange] if lowRange is not None and highRange is not None else []
                        if spanRange:
                            containedDict['range'] = [lowRange, highRange]
                        basicNode = cast(**containedDict)
                        members.append((fieldName, basicNode))
                    else:
                        members.append((fieldName, AsnMetaMember(
                            asnFilename=field.base,
                            lineno=field.sourceline,
                            containedType=refTypeHref)))
                else:
                    members.append((fieldName, 'dummy'))
            except Exception as e:  # pragma: no cover
                panic(str(e) + '\nMake sure that:\n'
                      '1. The "Name" attribute exists\n'
                      '2. The "Type" child element, with attribute '
                      '"xlink:title" also exists.',
                      'In %s, line %d:' % (field.base, field.sourceline))  # pragma: no cover
        if not members:
            panic("Empty SEQUENCE is not supported", loc)  # pragma: no cover
        if members[0][0] == 'choiceIdx':
            dataDict['members'] = members[1:]
            return AsnChoice(**dataDict)
        else:
            dataDict['members'] = members
            return AsnSequence(**dataDict)

    if attrs.type == 'Types:Integer':
        return HandleTypesInteger()
    elif attrs.type == 'Types:Float':
        return HandleTypesFloat()
    elif attrs.type == 'Types:Enumeration':
        dataDict["members"] = enumOptions
        return AsnEnumerated(**dataDict)
    elif attrs.type == 'Types:String':
        high = getMaybe(int, attrs.Length)
        span = [high, high] if high is not None else []
        dataDict["range"] = span
        return AsnOctetString(**dataDict)
    elif attrs.type == 'Types:Array':
        return HandleTypesArray()
    elif attrs.type == 'Types:Structure':  # pylint: disable=too-many-nested-blocks
        return HandleTypesStructure()
    panic("Failed to map... (%s)" % attrs.type, location)  # pragma: no cover


def FixupOutOfOrderIdReferences(nodeTypename: str, asnTypesDict: AST_Lookup, idToTypeDict: Dict[str, str]) -> None:
    """Based on the uniqueness of the 'Id' elements used in
    'xlink:href' remote references, we resolve the lookups of
    remote types that we stored in AsnMetaMembers during MapSMP2Type()."""
    node = asnTypesDict[nodeTypename]
    if isinstance(node, (AsnChoice, AsnSequence, AsnSet)):
        for idx, child in enumerate(node._members):
            if isinstance(child[1], AsnMetaMember):
                containedType = child[1]._containedType
                if containedType in idToTypeDict:
                    containedType = idToTypeDict[containedType]
                if containedType in asnTypesDict:
                    node._members[idx] = (child[0], asnTypesDict[containedType])
                else:
                    panic("Could not resolve Field '%s' in type '%s' (contained: %s)..." %
                          (child[0], nodeTypename, containedType), node.Location())  # pragma: no cover
    elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
        if isinstance(node._containedType, str):
            containedType = node._containedType
            if containedType in idToTypeDict:
                containedType = idToTypeDict[containedType]
            if containedType in asnTypesDict:
                node._containedType = asnTypesDict[containedType]
            else:
                panic("In type '%s', could not resolve: %s)" %
                      (nodeTypename, containedType), node.Location())  # pragma: no cover


def ConvertCatalogueToASN_AST(
        inputSmp2Files: List[str]) -> Tuple[AST_Lookup, Dict[str, str]]:  # pylint: disable=invalid-sequence-index
    """Converts a list of input SMP2 Catalogues into an ASN.1 AST,
    which it returns to the caller."""
    asnTypesDict = DashUnderscoreAgnosticDict()
    idToTypeDict = {}
    allSMP2Types = {}  # type: Dict[str, str]
    # Do a first pass, verifying the primary assumption:
    # That 'Id' elements of types are unique across our set of SMP2 files.
    for inputSmp2File in inputSmp2Files:
        a = etree.parse(open(inputSmp2File))  # type: Any  # mypy bugs in ElementTree handling
        root = a.getroot()
        if len(root) < 1 or not root.tag.endswith('Catalogue'):
            panic('', "You must use an XML file that contains an SMP2 Catalogue")  # pragma: no cover
        for t in root.xpath("//Type"):
            a = Attributes(t)
            if not a.Id:  # Missing attribute Id, don't bother checking for duplicates
                continue
            if a.Id in allSMP2Types:
                catalogue = allSMP2Types[a.Id]  # pragma: no cover
                if catalogue != inputSmp2File:  # pragma: no cover
                    panic("The same Id exists in two files: %s exists in both: %s" %
                          (a.Id, str([catalogue, inputSmp2File])))  # pragma: no cover
            else:
                allSMP2Types[a.Id] = inputSmp2File
    for inputSmp2File in inputSmp2Files:
        a = etree.parse(open(inputSmp2File))
        root = a.getroot()
        if len(root) < 1 or not root.tag.endswith('Catalogue'):
            panic('', "You must use an XML file that contains an SMP2 Catalogue")  # pragma: no cover
        for t in root.xpath("//Type"):
            # Find the enclosing Namespace element
            for namespace in t.iterancestors(tag='Namespace'):
                break
            else:
                panic("No Namespace parent node found (file:%s, line:%d)" %
                      t.base, t.sourceline)  # pragma: no cover

            # Store the namespace 'Name' attribute, and use it to prefix our types
            nsName = namespace.get('Name')  # pylint: disable=undefined-loop-variable
            if not nsName:
                panic("Missing attribute Name from Namespace (file:%s, line:%d)" %
                      namespace.base, namespace.sourceline)  # pragma: no cover pylint: disable=undefined-loop-variable
            cataloguePrefix = Clean(nsName).capitalize() + "_"

            a = Attributes(t)
            a.base = t.base
            a.sourceline = t.sourceline

            if not a.type:
                # Check to see if this is one of the hardcoded types
                if a.href in simpleTypesTable:
                    k = a.href
                    v = simpleTypesTable[k]
                    nodeTypename = a.title
                    if nodeTypename is None:
                        panic("'xlink:href' points to ready-made SMP2 type, but 'xlink:title' is missing! (file:%s, line:%d)" %
                              (a.base, a.sourceline))  # pragma: no cover
                    nodeTypename = Clean(nodeTypename.split()[-1]).capitalize()  # Primitive Int32 -> Int32
                    cast, low, high = v
                    containedDict = {
                        'asnFilename': a.base,
                        'lineno': a.sourceline
                    }
                    span = [low, high] if (low is not None and high is not None) else []
                    if span:
                        containedDict['range'] = [low, high]
                    # Especially for these hardcoded types, don't prefix with namespace.Name
                    asnTypesDict[nodeTypename] = cast(**containedDict)
                else:
                    if a.href is not None and a.href.startswith("http://www.esa.int/"):
                        print("WARNING: Unknown hardcoded (%s) - should it be added in commonSMP2.py:simpleTypesTable?" % a.href)
                    # This <Type> element had no xsi:type, and it's xlink:title was not in the hardcoded list
                    # Skip it.
                    # panic("Both 'xsi:type' and 'Name' are mandatory attributes (file:%s, line:%d)" %
                    #       (a.base, a.sourceline))  # pragma: no cover
                    continue

                # The type was merged in the AST or skipped over - work on the next one
                continue

            if a.type.startswith('Catalogue:'):
                # We only wants Types, nothing more
                continue

            nodeTypename = a.Name
            nodeTypename = nodeTypename[0].upper() + nodeTypename[1:]
            nodeTypename = nodeTypename.replace('_', '-')

            # Gather children node's info:

            # 1. Enumeration data
            enumOptions = []  # type: List[Tuple[str, str]]
            if a.type == 'Types:Enumeration':
                for node in t.xpath("Literal"):
                    nn = node.get('Name').replace('_', '-').lower()  # type: str
                    vv = node.get('Value').replace('_', '-').lower()  # type: str
                    enumOptions.append((nn, vv))

            # 2. ItemType data (used in arrays)
            itemTypes = t.xpath("ItemType")

            # 3. Field data (used in structures)
            fields = t.xpath("Field")

            try:
                description = t.xpath("Description")[0].text
            except:  # pragma: no cover
                location = 'from %s, in line %s' % \
                    (t.base, t.sourceline)  # pragma: no cover
                panic("Missing Description child element", location)  # pragma: no cover
            info(2, "Creating type:", cataloguePrefix + nodeTypename)
            asnNode = MapSMP2Type(a, enumOptions, itemTypes, fields)
            if 'artificial' in description:
                asnNode._isArtificial = True
            asnTypesDict[cataloguePrefix + nodeTypename] = asnNode
            # Store mapping from Id to typename in idToTypeDict
            # (used below, in FixupOutOfOrderIdReferences)
            idToTypeDict[a.Id] = cataloguePrefix + nodeTypename

    for nodeTypename in list(asnTypesDict.keys()):
        FixupOutOfOrderIdReferences(nodeTypename, asnTypesDict, idToTypeDict)
    return asnTypesDict, idToTypeDict

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
