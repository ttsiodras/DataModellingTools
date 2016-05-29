#!/usr/bin/env python2
import os
import sys
enums = []
for line in open(sys.argv[1] + '.h', 'r'):
    if '_PRESENT' in line and not line.startswith('#define'):
        enums.append(line.strip().replace(",", ""))
enums_dump = "\n    ".join(
    'printf("%s = %%d\\n", %s);' % (e,e)
    for e in enums
)
uniq = os.getpid()
extractor_filename ="/tmp/enums_%d" % uniq
f = open(extractor_filename + ".c", 'w')
f.write("""
#include <stdio.h>
#include "%(base)s.h"

void main()
{
%(enums_dump)s
}""" % {"enums_dump":enums_dump, "base":sys.argv[1]})
f.close()
if 0 != os.system(
        "gcc -o %s -I. %s.c" % (extractor_filename, extractor_filename)):
    print "Failed to extract CHOICE enum values..."
    sys.exit(1)
os.system(extractor_filename + ">> DV.py")
os.unlink(extractor_filename + ".c")
os.unlink(extractor_filename)
