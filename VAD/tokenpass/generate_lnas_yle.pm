package generate_lnas_yle;

use locale;

# Path settings to phone_probs
$BINDIR=".";

# NOTE: this should match your fileformat

sub generate_lnas {
  my $model = shift(@_);
  my $recipe = shift(@_); # Training file list
  my $lna_out = shift(@_);
  my $fileformat=shift(@_);
  mkdir($lna_out);

  #if ($recipe=~/pre/) {
  #  $pre="_pre";
  #}
  #else{
  #  $pre="";
  #}
  print "model $model pre $pre\n";
  print "recipe $recipe pre $pre\n";
  $cmd="$BINDIR/phone_probs -b $model -c ${model}.cfg -r $recipe -a -o $lna_out $fileformat -i 1 --lnabytes=4";
  system("$cmd") && die("phone_probs failed: $cmd\n");
}
1;
