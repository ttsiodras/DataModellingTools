#!/usr/bin/perl -w
use strict;

use Term::ANSIColor;

while(<>) {
    if (/pragma: no cover/) {
	print color 'reset';
	print substr($_, 2);
    } elsif (/^!/) {
	print color 'bold green';
	print substr($_, 2);
    } else {
	print color 'reset';
	print substr($_, 2);
    }
}
print color 'reset';
