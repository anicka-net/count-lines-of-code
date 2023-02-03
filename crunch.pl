#!/usr/bin/perl -w

# count-parallell postprocessing
# This script reads sorted output of count-parallel.py and removes apparent duplicities arising from
# different flavours of RPMs containing the same sources

# input is expected on STDIN

use strict;

my ($code_old, $diff_old) = (0, 0);
my ($prefix, $prefix_old) = ("", "");
my ($name, $code, $diff) = (0, 0, 0);
my ($sc, $sd) = (0, 0);

while (<STDIN>) {
	 ($code_old, $diff_old) = ($code, $diff);
	 $prefix_old = $prefix;
	 ($name, $code, $diff) = split(" ", $_);
	 my $shortname = split(".", $name);
	 my @splitted_name = split("-", $shortname);
	 if (defined $splitted_name[1]) { #there is some - in name
	 	pop(@splitted_name);
         }
	 $prefix = join("-", @splitted_name);
	 #	 print($prefix."\n");

	 if ( !$code || ( !(((abs($code - $code_old) < $code/100)) && ($prefix eq $prefix_old))) ) { #packages are excluded if they have the same prefix and codesize differs just a little
	 # 	 	print("+");
	 #	 	print($name," ",$code, " ", $diff, "\n");
			$sc += $code;
			$sd += $diff;
	}
	# else {
	#	print("-",$name," ",$code, " ", $diff, "\n");
	#}
}

print ($sc, " ", $sd, "\n");
