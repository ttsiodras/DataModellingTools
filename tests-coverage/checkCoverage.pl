#!/usr/bin/perl -w
use strict;

use Term::ANSIColor;

my $foundDiff = 0;
while(<>) {
    next if /pragma: no cover/;
    if (/^!/) {
	$foundDiff = 1;
    }
}
exit $foundDiff;
