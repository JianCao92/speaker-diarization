#!/usr/bin/perl
use File::Basename;

# push(@starts,0);

while(<>) {
    chomp;
    push(@starts,$_);
}

$starts[0] = 0;

$num=$#starts;
$start=$starts[0];
$end=$starts[$num];

print "File type = \"ooTextFile short\"\n";
print "\"TextGrid\"\n";
print "\n";

print "$start\n";
print "$end\n";
print "\<exists\>\n";
print "1\n";

print "\"IntervalTier\"\n";
print "\"$basename\"\n";

print "$start\n";
print "$end\n";
print "$num\n";

for($i=0; $i<=$#starts-1; $i++) {
    $st=$starts[$i];
    $en=$starts[$i+1];
    
    print "$st\n$en\n";
    print "\"\"\n";
} 



