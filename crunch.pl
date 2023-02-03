#!/usr/bin/perl -w

# count-parallell postprocessing
# This script reads sorted output of count-parallel.py and removes apparent duplicities arising from
# different flavours of RPMs containing the same sources

# input is expected on STDIN

use strict;
use Digest::SHA qw(sha1);

my ($code_old, $diff_old) = (0, 0);
my ($prefix, $prefix_old) = ("", "");
my ($name, $code, $diff) = (0, 0, 0);
my ($sc, $sd) = (0, 0);
my %hash = ();

while (<STDIN>) {
	 ($code_old, $diff_old) = ($code, $diff);
	 $prefix_old = $prefix;
	 ($name, $code, $diff) = split(" ", $_);
	 my @shortname = split("\\.", $name);
	 my @splitted_name = split("-", $shortname[0]);
	 if (defined $splitted_name[1]) { #there is some - in name
	 	pop(@splitted_name);
         }
	 
	 my $prefix1 = $splitted_name[0];
	 my $sum = Digest::SHA::sha1_hex($prefix1.$code);
	 
	 $prefix = join("-", @splitted_name);
	 if ($shortname[0] eq "kernel-source") {
		 $prefix = "kernel-source";
	 }
	#packages are excluded if they have the same first prefix and  exactly the same size
	#we also exclude copies of gcc
	#we try to exclude kernel packages that differ just a little
	 if ( !$code || ( (!(((abs($code - $code_old) < $code/100)) && ($prefix eq $prefix_old))) && ($prefix1 ne "cross") && !defined($hash{$sum})) ){ 
		 # print("+");
			print($name," ",$code, " ", $diff, "\n");
			$sc += $code;
			$sd += $diff;
	}
	#		else {
			#		print("-",$name," ",$code, " ", $diff, "\n");
			#	}
	$hash{$sum} = 1;
}

print ($sc, " ", $sd, "\n");
