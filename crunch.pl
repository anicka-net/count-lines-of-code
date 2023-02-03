#!/usr/bin/perl -w

# count-parallell postprocessing
# This script reads output of count-parallel.py and removes apparent duplicities arising from
# different fkavours of RPMs containing the same sources

# input is expected on STDIN

use strict;

my ($code_old, $diff_old) = (0, 0);
my ($name, $code, $diff) = (0, 0, 0);
my ($sc, $sd) = (0, 0);

while (<STDIN>) {
	 ($code_old, $diff_old) = ($code, $diff);
	 ($name, $code, $diff) = split(" ", $_);
	 if ( !$code || (($code != $code_old) || ($diff != $diff_old))) {
	 #		 	print("+");
		 	print($name," ",$code, " ", $diff, "\n");
			$sc += $code;
			$sd += $diff;
	 } #else {
	 #	print("-",$name," ",$code, " ", $diff, "\n");
	 #}
}

print ($sc, " ", $sd, "\n");
