#!/usr/bin/env python3
"""
ASN.1 Importer

This is one of the tools that Semantix develops for the European
research project ASSERT. It parses an ASN.1 grammar and generates
references (in AADL) to all the existing types.
"""
import os
import re
import sys
import copy
import shutil
import getopt
import hashlib
import tempfile
import platform
from subprocess import Popen, PIPE
import distutils.spawn as spawn

from .commonPy import configMT
from .commonPy import asnParser
from .commonPy import __version__

from .commonPy.asnAST import (
    AsnBasicNode, AsnBool, AsnReal, AsnInt,
    AsnEnumerated, AsnString, AsnChoice, AsnSequence,
    AsnSequenceOf, AsnSet, AsnSetOf)


from .commonPy.utility import inform, panic, mysystem

# Ada package names per type
g_AdaPackageNameOfType = {}


def cleanNameAsAADLWants(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def cleanNameAsAsn1cWants(name):
    return cleanNameAsAADLWants(name)


g_lowerFloat = -1e350
g_upperFloat = 1e350


def verifyNodeRange(node):
    assert isinstance(node, AsnBasicNode)
    if isinstance(node, AsnInt):
        if not node._range:
            panic("INTEGER (in %s) must have a range constraint inside ASN.1,\n"
                  "or else we might lose accuracy during runtime!" % node.Location())
        # else:
        #     # asn1c uses C long for ASN.1 INTEGER. Assuming that our platform is 32 bit,
        #     # this allows values from -2147483648 to 2147483647
        #     if node._range[0] < -2147483648L:
        #        panic("INTEGER (in %s) must have a low limit >= -2147483648\n" % node.Location())
        #     if node._range[1] > 2147483647L:
        #        panic("INTEGER (in %s) must have a high limit <= 2147483647\n" % node.Location())

    if isinstance(node, AsnReal):
        if not node._range:
            panic(
                "REAL (in %s) must have a range constraint inside ASN.1,\n"
                "or else we might lose accuracy during runtime!" % node.Location())
        else:
            # asn1c uses C double for ASN.1 REAL.
            # this allows values from -1.7976931348623157E308 to 1.7976931348623157E308
            if node._range[0] == g_lowerFloat:
                panic(
                    "REAL (in %s) must have a low limit >= -1.7976931348623157E308\n"
                    % node.Location())
            if node._range[1] == g_upperFloat:
                panic(
                    "REAL (in %s) must have a high limit <= 1.7976931348623157E308\n"
                    % node.Location())


def calculateForNativeAndASN1SCC(absASN1SCCpath, autosrc, names, inputFiles):
    base = "ShowNativeBuffers"

    acn = " -ACN " if any(x.lower().endswith(".acn") for x in inputFiles) else ""
    inputASN1files = [x for x in inputFiles if not x.lower().endswith('.acn')]

    # Spawn ASN1SCC.exe compiler - for MacOS define a new sh file calling mono Asn1f2.exe
    if platform.system() == "Windows" or platform.system() == "Darwin":
        mysystem("%s -c -uPER -o \"%s\" %s %s" % (absASN1SCCpath, autosrc, acn, '"' + '" "'.join(inputFiles) + '"'))
    else:
        cmd = "mono %s -c -uPER -fp AUTO -typePrefix asn1Scc -o \"%s\" %s %s" % (absASN1SCCpath, autosrc, acn, '"' + '" "'.join(inputFiles) + '"')
        res = mysystem(cmd)
        if res != 0:
            panic("This command failed: %s\n" % cmd)

    msgEncoderFile = open(autosrc + os.sep + base + ".stats.c", 'w')

    # msgEncoderFile.write('#include "DumpableTypes.h"\n')

    for a in inputASN1files:
        msgEncoderFile.write('#include "%s.h"\n' % os.path.splitext(os.path.basename(a))[0])

    uniqueASNfiles = {}
    for asnFile in inputASN1files:
        tmpNames = {}
        for name in asnParser.g_typesOfFile[asnFile]:
            tmpNames[name] = asnParser.g_names[name]

        uniqueASNfiles[asnFile] = [
            copy.copy(tmpNames),                            # map Typename to type definition class from asnAST
            copy.copy(asnParser.g_astOfFile[asnFile]),    # list of nameless type definitions
            copy.copy(asnParser.g_leafTypeDict)]   # map from Typename to leafType

    configMT.outputDir = autosrc + os.sep
    # dumpable.CreateDumpableCtypes(uniqueASNfiles)

    for asnTypename in sorted(list(names.keys())):
        node = names[asnTypename]
        if node._isArtificial:
            continue
        cleaned = cleanNameAsAsn1cWants(asnTypename)
        msgEncoderFile.write('static asn1Scc%s sizeof_%s;\n' % (cleaned, cleaned))
        msgEncoderFile.write('char bytesEncoding_%s[asn1Scc%s_REQUIRED_BYTES_FOR_ENCODING];\n' % (cleaned, cleaned))
        if acn != "":
            msgEncoderFile.write('char bytesAcnEncoding_%s[asn1Scc%s_REQUIRED_BYTES_FOR_ACN_ENCODING];\n' % (cleaned, cleaned))
    msgEncoderFile.close()

    # Code generation - asn1c part
    # Create a dictionary to lookup the asn-types from their corresponding c-type
    namesDict = {}
    for asnTypename in sorted(list(names.keys())):
        node = names[asnTypename]
        if node._isArtificial:
            continue
        namesDict[cleanNameAsAsn1cWants(asnTypename)] = asnTypename

    # Get a list of all available compilers
    platformCompilers = ['gcc']
    try:
        pipe = Popen("find-supported-compilers", stdout=PIPE).stdout
        platformCompilers = pipe.read().splitlines()
    except OSError as err:
        print('Not running in a TASTE Environment: {}\nUsing GCC only for computing sizeofs'.format(str(err)))
        platformCompilers = ['gcc'.encode()]
    # Get the maximum size of each asn1type from all platform compilers
    messageSizes = {}
    for cc in platformCompilers:
        # Compile the generated C-file with each compiler
        pwd = os.getcwd()
        os.chdir(autosrc)
        path_to_compiler = spawn.find_executable(cc.decode('utf-8'))
        if path_to_compiler is None:
            os.chdir(pwd)
            continue
        for cfile in os.listdir("."):
            if cfile.endswith(".c"):
                if mysystem('%s -c -std=c99 -I. "%s" 2>"%s.stats.err"' % (path_to_compiler, cfile, base)) != 0:
                    panic("Compilation with %s failed...\n"
                          "(report inside '%s')\n" % (cc, os.path.join(autosrc, base + ".stats.err")))
        os.chdir(pwd)

        # Receive the size information for each value from the compiled object file
        if platform.system() == "Darwin":
            nm = "gnm"
        else:
            nm = "nm"
        for line in os.popen(nm + " --print-size " + autosrc + os.sep + base + ".stats.o").readlines():
            try:
                (dummy, size, dummy2, msg) = line.split()
            except ValueError:
                # Ignore lines that are not well-formatted
                continue

            # Remove prefix
            asnType = msg.split('_', 1)[1]
            # get asn-type from cleaned type
            asnType = namesDict[asnType]
            assert asnType in list(names.keys())
            # Find maximum
            messageSizes.setdefault(asnType, 0)
            messageSizes[asnType] = max(int(size, 16), messageSizes[asnType])

    return messageSizes


def ASNtoACN(asnFilename):
    replaces = {
        ".asn": ".acn",
        ".asn1": ".acn",
        ".ASN": ".ACN",
        ".ASN1": ".ACN",
    }
    for k, v in list(replaces.items()):
        if asnFilename.endswith(k):
            return asnFilename.replace(k, v)
    return asnFilename + ".acn"


def usage():
    panic("""\
Usage: asn2aadlPlus.py <options> <files> outputDataSpec.aadl

Where <files> is a list of ASN.1 and ACN files, and options can be:

    -k, --keep	    Don't delete temporary files
    -a, --aadlv2    Generate AADLv2 compliant output
    -v, --version   Show version number
    -d, --debug	    Enable debug output
    -f, --fast      Do not emit Source_Data_Size lines (invoke ASN1SCC without uPER or ACN options)
    -p, --platform  Comma seperated list of platform compilers (default: gcc)
    -h, --help	    This help message""")


def main():
    if "-pdb" in sys.argv:
        sys.argv.remove("-pdb")  # pragma: no cover
        import pdb  # pragma: no cover pylint: disable=wrong-import-position,wrong-import-order
        pdb.set_trace()  # pragma: no cover

    if "-v" in sys.argv:
        import pkg_resources  # pragma: no cover
        version = pkg_resources.require("dmt")[0].version  # pragma: no cover
        print("asn2aadlPlus v" + str(version))  # pragma: no cover
        sys.exit(1)  # pragma: no cover

    keepFiles = False

    projectCache = os.getenv("PROJECT_CACHE")
    if projectCache is not None and not os.path.isdir(projectCache):
        try:
            os.mkdir(projectCache)
        except:
            panic("The configured cache folder:\n\n\t" + projectCache + "\n\n...is not there!\n")

    # Backwards compatibility - the '-acn' option is no longer necessary
    # (we auto-detect ACN files via their extension)
    while "-acn" in sys.argv:
        ofs = sys.argv.index("-acn")
        del sys.argv[ofs]
    if "-aadlv2" in sys.argv:
        ofs = sys.argv.index("-aadlv2")
        sys.argv[ofs] = '--aadlv2'

    try:
        optlist, args = getopt.gnu_getopt(sys.argv[1:], "hvkadf", ['help', 'version', 'keep', 'aadlv2', 'debug', 'fast', 'platform='])
    except getopt.GetoptError:
        usage()

    bAADLv2 = False
    keepFiles = False
    bFast = False

    for opt, unused_arg in optlist:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-v", "--version"):
            print("ASN2AADL v%s" % __version__)
            sys.exit(0)
        elif opt in ("-d", "--debug"):
            configMT.debugParser = True
        elif opt in ("-f", "--fast"):
            bFast = True
        elif opt in ("-a", "--aadlv2"):
            # Updated, June 2011: AADLv1 no longer supported.
            bAADLv2 = True
        elif opt in ("-k", "--keep"):
            keepFiles = True

    if len(args) < 2:
        usage()

    if 'PATH' not in os.environ or os.environ['PATH'] == '':
        p = os.defpath
    else:
        p = os.environ['PATH']
    for dirent in p.split(os.pathsep):
        if platform.system() == "Windows":
            f = os.path.join(dirent, 'gcc.exe')
        else:
            f = os.path.join(dirent, 'gcc')
        if os.access(f, os.X_OK):
            break
    else:
        panic("No '%s' found in your PATH... Aborting..." %
              "gcc.exe" if platform.version() == "Windows" else "gcc")

    # Check that the ASN.1/ACN files that are passed-in, do in fact exist.
    for x in args[:-1]:
        if not os.path.isfile(x):
            panic("'%s' is not a file!\n" % x)

    aadlFile = args[-1]
    inputFiles = [os.path.abspath(x) for x in args[:-1]]

    def md5(filename):
        hash_md5 = hashlib.md5()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def checkIfNoWorkIsNeeded(asnfiles, aadlfile):
        oldMD5s = {}
        oldBFast = None
        for line in open(aadlfile):
            if 'MadeInFastMode' in line:
                oldBFast = line.split(':')[1] == "True"
            if 'InputASN1FileChecksum' in line:
                md5sum, asnfile = line.split(':')[1:3]
                oldMD5s[asnfile] = md5sum

        # if the output AADL file contained MD5 checksums of the input ASN.1 files
        # and the file was created using the same "--fast" setup...
        if oldMD5s and oldBFast == bFast:
            def ok(f):
                return os.path.exists(f) and md5(f) == oldMD5s[f]
            # ...and all the current input ASN.1 files exist in the 'burned' list
            # that was built inside the previous version of the output AADL file,
            # AND
            # all the current input ASN.1 files exist and their MD5 checksum
            # has remained identical to that burned in the previous version of
            # the output AADL file...
            if all(f in oldMD5s for f in asnfiles) and \
                    all(ok(x) for x in asnfiles):
                # ...then there's no need to redo anything.
                inform("No AADL dataview generation is necessary.")
                sys.exit(0)

    if os.path.exists(aadlFile) and all(os.path.exists(x) for x in inputFiles):
        checkIfNoWorkIsNeeded(inputFiles, aadlFile)

    # Check if we can skip the work altogether!

    # Parse the ASN.1 files (skip the ACN ones)
    asnFiles = [x for x in inputFiles if not x.lower().endswith('.acn')]
    asnParser.ParseAsnFileList(asnFiles)
    autosrc = tempfile.mkdtemp(".asn1c")
    inform("Created temporary directory (%s) for auto-generated files...", autosrc)
    absPathOfAADLfile = os.path.abspath(aadlFile)
    asn1SccPath = spawn.find_executable('asn1.exe')
    if asn1SccPath is None:
        panic("ASN1SCC seems not installed on your system (asn1.exe not found in PATH).\n")
    absASN1SCCpath = os.path.abspath(asn1SccPath)

    # Update the AdaUses dictionary - can now be safely done in all cases,
    # since the information is extracted from the base ASN1SCC AST.
    for asnModuleID, setOfTypenames in asnParser.g_adaUses.items():
        for typeName in setOfTypenames:
            g_AdaPackageNameOfType[typeName] = asnModuleID

    # A, those good old days... I could calculate the buffer size for BER (SIZ), and then compare
    # it to the size for Native (SIZ2, see above) and the max of the two suffices for any conf of the message.
    # CHOICEs, however, changed the picture...  what to put in?
    # Time to use the maximum of Native (SIZ2) and UPER (SIZE) and ACN (SIZ3)...

    if not bFast:
        # If taste-updata-dataview is called, then we just want the GUI to be aware
        # of the list of ASN.1 types - the Ellidiss GUI does not care about the
        # Source_Data_Size values... so skip all GCC-related work!
        messageSizes = calculateForNativeAndASN1SCC(absASN1SCCpath, autosrc, asnParser.g_names, inputFiles)
        for nodeTypename in list(messageSizes.keys()):
            messageSizes[nodeTypename] = [messageSizes[nodeTypename], (8 * (int((messageSizes[nodeTypename] - 1) / 8)) + 8)]

    base = os.path.basename(aadlFile)
    base = re.sub(r'\..*$', '', base)

    # AADL creation
    o = open(absPathOfAADLfile, 'w')
    o.write('--------------------------------------------------------\n')
    o.write('--! File generated by asn2aadl v%s: DO NOT EDIT !\n' % __version__)
    o.write('--------------------------------------------------------\n')

    o.write('--! MadeInFastMode:' + str(bFast) + ':\n')
    for f in inputFiles:
        o.write('--! InputASN1FileChecksum:' + md5(f) + ':' + f + ':\n')
    o.write('--------------------------------------------------------\n\n')
    o.write('package DataView\n\npublic\n\n')
    if bAADLv2:
        o.write('  with Data_Model;\n')
        o.write('  with Taste;\n')
        o.write('  with Base_Types;\n')
        o.write('  with Deployment;\n')
    typesUnusableAsInterfaceParameters = []
    if bAADLv2:
        directiveTypes = [
            "Simulink_Tunable_Parameter", "Timer", "Taste_directive"]
        for typeName in directiveTypes:
            sourceText = ""
            adaPackageName = "TASTE_Directives"
            moduleName = "TASTE-Directives"
            o.write('DATA {typeName}\n'
                    'PROPERTIES\n'
                    '   TASTE::Ada_Package_Name => "{adaPackageName}";\n'
                    '   Type_Source_Name => "{typeNameASN}";\n'
                    '   Deployment::ASN1_Module_Name => "{moduleName}";{sourceText}\n'
                    '   TASTE::Forbid_in_PI => true;\n'
                    'END {typeName};\n'.format(
                        typeName=typeName,
                        typeNameASN=typeName.replace('_', '-'),
                        sourceText=sourceText,
                        adaPackageName=adaPackageName,
                        moduleName=moduleName))

        typesUnusableAsInterfaceParameters = []
        for line in os.popen("badTypes '" + "' '".join(asnFiles) + "'").readlines():
            line = line.strip().replace('-', '_')
            typesUnusableAsInterfaceParameters.append(line)

        o.write('''
data Stream_Element_Buffer
    -- Root type for buffer elements
properties
    Data_Model::Data_Representation => Character;
end Stream_Element_Buffer;
''')
    for asnTypename in sorted(list(asnParser.g_names.keys())):
        node = asnParser.g_names[asnTypename]
        if node._isArtificial:
            continue
        cleanName = cleanNameAsAADLWants(asnTypename)
        o.write('DATA ' + cleanName + '\n')
        o.write('PROPERTIES\n')
        o.write('    -- name of the ASN.1 source file:\n')
        # o.write('    Source_Text => ("%s");\n' % os.path.basename(asnParser.g_names[asnTypename]._asnFilename))
        o.write('    Source_Text => ("%s");\n' % asnParser.g_names[asnTypename]._asnFilename)
        prefix = "TASTE::" if bAADLv2 else ""
        possibleACN = ASNtoACN(asnParser.g_names[asnTypename]._asnFilename)
        if bAADLv2 and os.path.exists(possibleACN):
            prefix2 = "TASTE::" if bAADLv2 else "assert_properties::"
            base = os.path.splitext(os.path.basename(possibleACN))[0]
            fname = base.replace("-", "_")
            o.write('    %sEncodingDefinitionFile => classifier(DataView::ACN_%s);\n' % (prefix2, fname))
        o.write('    %sAda_Package_Name => "%s";\n' % (prefix, g_AdaPackageNameOfType[asnTypename]))
        if bAADLv2:
            o.write('    Deployment::ASN1_Module_Name => "%s";\n' % g_AdaPackageNameOfType[asnTypename].replace('_', '-'))
        if os.getenv('UPD') is None:
            o.write('    Source_Language => (ASN1);\n')
        if not bFast:
            o.write('    -- Size of a buffer to cover all forms of message representation:\n')
            le_size = 0 if asnTypename not in messageSizes else messageSizes[asnTypename][0]
            o.write('    -- Real message size is %d; suggested aligned message buffer is...\n' % le_size)
            le_size_rounded = 0 if asnTypename not in messageSizes else messageSizes[asnTypename][1]
            o.write('    Source_Data_Size => %d B%s;\n' % (le_size_rounded, bAADLv2 and "ytes" or ""))
        o.write('    -- name of the corresponding data type in the source file:\n')
        o.write('    Type_Source_Name => "%s";\n' % asnTypename)
        o.write('    TASTE::Position_In_File => [ line => %s ; column => 1 ; ];\n' % node._lineno)
        o.write('    -- what kind of type is this?\n')
        prefix = "TASTE" if bAADLv2 else "assert_properties"
        o.write('    %s::ASN1_Basic_Type =>' % prefix)
        if isinstance(node, AsnBool):
            o.write('aBOOLEAN;\n')
        elif isinstance(node, AsnInt):
            o.write('aINTEGER;\n')
        elif isinstance(node, AsnReal):
            o.write('aREAL;\n')
        elif isinstance(node, AsnEnumerated):
            o.write('aENUMERATED;\n')
        elif isinstance(node, AsnString):
            o.write('aSTRING;\n')
        elif isinstance(node, AsnChoice):
            o.write('aCHOICE;\n')
        elif isinstance(node, AsnSequence):
            o.write('aSEQUENCE;\n')
        elif isinstance(node, AsnSequenceOf):
            o.write('aSEQUENCEOF;\n')
        elif isinstance(node, AsnSet):
            o.write('aSET;\n')
        elif isinstance(node, AsnSetOf):
            o.write('aSETOF;\n')
        else:
            panic("Unsupported ASN.1 type: %s" % node._leafType)
        if asnTypename in typesUnusableAsInterfaceParameters:
            o.write('    TASTE::Forbid_in_PI => true;\n')
        o.write('END ' + cleanName + ';\n\n')
        o.write('DATA IMPLEMENTATION ' + cleanName + '.impl\n')
        o.write('END ' + cleanName + '.impl;\n\n')
        if os.getenv('UPD') is None:
            o.write('DATA ' + cleanName + '_Buffer_Max\n')
            o.write('END ' + cleanName + '_Buffer_Max;\n\n')

            o.write('DATA IMPLEMENTATION ' + cleanName + '_Buffer_Max.impl\n')
            o.write('    -- Buffer to hold a marshalled data of type ' + cleanName + "\n")
            o.write('PROPERTIES\n')
            o.write('    Data_Model::Data_Representation => array;\n')
            if not bFast:
                o.write('    Data_Model::Dimension => (%d); -- Size of the buffer\n' % le_size_rounded)
                o.write('    Source_Data_Size => %d Bytes; -- Size of the buffer in bytes\n' % le_size_rounded)
            if bAADLv2:
                o.write('    Data_Model::Base_Type => (classifier (DataView::Stream_Element_Buffer));\n')
            else:
                o.write('    Data_Model::Base_Type => (data ASSERT_Types::Stream_Element);\n')
            o.write('END ' + cleanName + '_Buffer_Max.impl;\n\n')

            o.write('DATA ' + cleanName + '_Buffer\n')
            o.write('END ' + cleanName + '_Buffer;\n\n')

            o.write('DATA IMPLEMENTATION ' + cleanName + '_Buffer.impl\n')
            o.write('    -- Buffer to hold a marshalled data of type ' + cleanName + "\n")
            o.write('SUBCOMPONENTS\n')
            o.write('    Buffer : data ' + cleanName + '_Buffer_Max.impl;\n')
            o.write('    Length : data Base_Types::%s;\n' % (bAADLv2 and "Unsigned_32" or "uint32"))
            o.write('PROPERTIES\n')
            o.write('    Data_Model::Data_Representation => Struct;\n')
            if not bFast:
                o.write('    Source_Data_Size => %d Bytes; -- Size of the buffer in bytes\n' % (
                    le_size_rounded + 16))
            o.write('END ' + cleanName + '_Buffer.impl;\n\n')

    # Generate a SYSTEM in the DataView, otherwise Ocarina cannot parse it
    # standalone. This allows buildsupport to get the list of ASN.1 files
    # and modules, which is otherwise not visible unless those for which
    # at least one type is referenced in a provided interface.
    o.write('SYSTEM Taste_DataView\n')
    o.write('END    Taste_DataView;\n\n')
    o.write('SYSTEM IMPLEMENTATION Taste_DataView.others\n')
    o.write('SUBCOMPONENTS\n')
    for asnTypename in sorted(list(asnParser.g_names.keys())):
        node = asnParser.g_names[asnTypename]
        if node._isArtificial:
            continue
        cleanName = cleanNameAsAADLWants(asnTypename)
        o.write('   %s : DATA %s.impl;\n' % (cleanName, cleanName))
    o.write('END Taste_DataView.others;\n')

    listOfAsn1Files = {}
    for asnTypename in sorted(list(asnParser.g_names.keys())):
        listOfAsn1Files[asnParser.g_names[asnTypename]._asnFilename] = 1

    if bAADLv2:
        for asnFilename in sorted(list(listOfAsn1Files.keys())):
            base = os.path.splitext(os.path.basename(asnFilename))[0]
            possibleACN = ASNtoACN(asnFilename)
            if os.path.exists(possibleACN):
                fname = base.replace("-", "_")
                o.write('DATA ACN_' + fname + '\n')
                o.write('PROPERTIES\n')
                o.write('    Source_Text => ("' + possibleACN + '");\n')
                o.write('    Source_Language => (ACN);\n')
                o.write('END ACN_' + fname + ';\n\n')

    o.write('end DataView;\n')
    o.close()

    # Remove generated code
    if not keepFiles:
        shutil.rmtree(autosrc)
    else:
        print("Generated message buffers in '%s'" % autosrc)
    # os.chdir(pwd)


if __name__ == "__main__":
    main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
