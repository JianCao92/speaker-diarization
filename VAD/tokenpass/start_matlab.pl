#!/usr/bin/perl
$lna_path=shift(@ARGV);
open(MYFILE,'>matlab_lnapath.txt');
print MYFILE $lna_path;
close(MYFILE);
system("matlab -nodisplay -r shift_dec_bord");
