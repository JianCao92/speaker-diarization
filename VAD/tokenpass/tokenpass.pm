package tokenpass;
use score;
use Cwd;
sub test_token_pass {
  my $fs = shift(@_);
  my $mod_name = shift(@_);
  my $recipe = shift(@_);
  my $lna_dir = shift(@_);
  #my $phn_dir = shift(@_);
  my $exp_dir = shift(@_);
  open(RECIPE,"<$recipe");
  $sp_sp=0;
  $sp_nsp=0;
  $nsp_sp=0;
  $nsp_nsp=0;
  $corr_cnt=0;
  $frame_cnt=0;
  $mod_name="$mod_name.ph";

  while(<RECIPE>) {
    $line=$_;  
    @words = split(/ /, $line);

    $phn_name=$words[0];
    $name_base=$phn_name;
    chomp($name_base);
    # NOTE: this should change the file extension to .lna
    $name_base=~s/.wav$//;
    $name_base=~s/.pre$//;
    $name_base=~s/.FI0$//;
    $name_base=~s/.FI1$//;
    $name_base=~s/.FI2$//;
    $name_base=~s/audio=//;
    #$phn_name=~s/(\/)$//;
    $name_base=~s/\/.+\///;
    $name_lna="$lna_dir$name_base.lna";
    $name_out="$exp_dir$name_base.exp";
    #$name_phn="$phn_dir$name_base.phn";
    #$name_phn=~s/_16//;
    #print "$words[1] $name_lna\n";
    print("./test_token_pass -model $mod_name -ins_pen 1 -lm_scale 10 -trans_scale 1 -lna $name_lna > $name_out\n");
    system("./test_token_pass -model $mod_name -ins_pen 1 -lm_scale 10 -trans_scale 1 -lna $name_lna > $name_out");
    #$corr_cnt=0;
    #$frame_cnt=0;
    #$sp_sp=0;
    #$sp_nsp=0;
    #$nsp_sp=0;
    #$nsp_nsp=0;
    #($sp_sp,$sp_nsp,$nsp_sp,$nsp_nsp,$corr_cnt,$frame_cnt)=score::score($fs,$name_out,$name_phn,$sp_sp,$sp_nsp,$nsp_sp,$nsp_nsp,$corr_cnt,$frame_cnt);

    # NOTE: the following should match the filename from shift_dec_bord.m
    $cwd=cwd();
    $last_frame_file = "$lna_dir/$name_base.last_frame";
    print "$last_frame_file\n";
    open(LAST_FRAME, $last_frame_file) or die "could not read last frame: $!";
    $last_fr = <LAST_FRAME>;
    close(LAST_FRAME);
    system("rm -f $last_frame_file");
    score::recout_to_exp($name_out,$last_fr);
  }
  
  close(RECIPE);
}
1;
