package score;
use POSIX;
$fs_orig=16000;


sub score {
  my $fs_new=shift(@_);
  my $name_out=shift(@_);
  my $name_phn=shift(@_);
  my $sp_sp=shift(@_);
  my $sp_nsp=shift(@_);
  my $nsp_sp=shift(@_);
  my $nsp_nsp=shift(@_);
  my $corr_cnt=shift(@_);
  my $frame_cnt=shift(@_);

  print "frame $frame_cnt\n";
  print "corr $corr_cnt\n";
  $convert_fac=$fs_new/$fs_orig;

  $last_fr=phn_to_exp($name_phn,$convert_fac); #expand phn to frame rate
  # transfer last frame index to 
  recout_to_exp($name_out,$last_fr); # expand classficiation result
                                     # to frames 


  open(OUT,"<exp_out.txt");
  open(TRG,"<phn_exp.txt");

  #print "kukkuu\n";
  while(<OUT>) {
    $line=$_;
    $line=~s/\n$//;
    $line=~s/<w>/__/;
    #print "$line";
    $line_target=<TRG>;
    $line_target=~s/\n$//;
    #print "$line_target\n";
    if ($line_target=~$line) {
      $corr_cnt=$corr_cnt+1;
    }
    if ($line_target=~/p/) {
      if ($line=~/p/){
	$sp_sp=$sp_sp+1;
      }
      else {
	$sp_nsp=$sp_nsp+1;
      }
      $frame_cnt=$frame_cnt+1;
    }
    if ($line_target=~/__/) {
      if($line=~/__/) {
	$nsp_nsp=$nsp_nsp+1;
      }
      else {
	$nsp_sp=$nsp_sp+1;
      }
      $frame_cnt=$frame_cnt+1;
    }
  }

  $recall_sp=floor(1000*($sp_sp/($sp_sp+$sp_nsp))+0.5)/10;
  $prec_sp=floor(1000*($sp_sp/($sp_sp+$nsp_sp))+0.5)/10;

  $prec_nsp=floor(1000*($nsp_nsp/($nsp_nsp+$sp_nsp))+0.5)/10;
  $recall_nsp=floor(1000*($nsp_nsp/($nsp_nsp+$nsp_sp))+0.5)/10;
  
  $corr=floor(1000*($corr_cnt/$frame_cnt)+0.5)/10;

  $speech_tot=($sp_sp+$sp_nsp);
  $speech_rel=$speech_tot/$frame_cnt;
  $speech_rel_rnd=floor(1000*($speech_tot/$frame_cnt)+0.5)/10;
  $nsp_tot=$nsp_nsp+$nsp_sp;
  $nsp_rel=$nsp_tot/$frame_cnt;
  $nsp_rel_rnd=floor(1000*($nsp_tot/$frame_cnt)+0.5)/10;
  
  $tot_min=floor(10*($speech_tot+$nsp_tot)/125/60+0.5)/10;
  print "speech recall $recall_sp\n";
  print "speech precision $prec_sp\n";
  print "nsp recall $recall_nsp\n";
  print "nsp precision $prec_nsp\n";
  print "correct $corr_cnt\n";
  print "frames $frame_cnt\n";
  print "$nsp_tot\n";
  print "$speech_tot\n";
  print "accuracy $corr\n";
  print "speech rel $speech_rel\n";
  print "nsp rel $nsp_rel\n";
  print "tot $tot_min\n";
  close(OUT);
  close(TRG);
  return ($sp_sp,$sp_nsp,$nsp_sp,$nsp_nsp,$corr_cnt,$frame_cnt);
}

# expand phn:s to frame rate

sub phn_to_exp{
  my $name_phn = shift(@_);
  my $convert_fac = shift(@_);
  print "in phn_to_exp $name_phn\n";
  open(OUT,$name_phn) || die("can't open $name_phn");;
  $i=0;
  @arr_num_st=();
  @arr_num_end=();
  @arr_lab=();
  #print "kukkuu\n";
  while(<OUT>) {
    $line=$_;
    $line=~s/\n$//;
    #print "$line\n";
    @words = split(/ /, $line);
    $j=0;
    foreach $tmp (@words) {
      if ($tmp=~/\d/) {
	#print "$tmp ";
	if ($j==0){
	  $arr_num_st[$i]=floor(0.5+$convert_fac*$tmp);
	}
	elsif($j==1){
	  $arr_num_end[$i]=floor(0.5+$convert_fac*$tmp);	  
	}
	$j++
      }
      else {
	#print "$tmp\n";
	$arr_lab[$i]=$tmp;
	$i++
      }
    }
    #}
  }
  
  close(OUT);
  
  $i=0;
  $sum_sp=0;
  $sum_nsp=0;
  @expnd=();
  # run through array of labels and 
  foreach $lab (@arr_lab) {    
    $st=$arr_num_st[$i];
    $end=$arr_num_end[$i];
    # run using step size of frame rate
    for $tmp ($st..$end) {
      if  ($tmp=~/\d/) {
	$expnd[$tmp]=$lab;
      }
    }
    $i++;
  }
  
  $ii=0;
  # write expanded phn to a file
  open(EXP_OUT,">phn_exp.txt");
  foreach $tmp (@expnd) {
    print EXP_OUT "$ii $expnd[$ii] \n";
    $ii++;
  }
  $last_fr=$ii;
  close(EXP_OUT);
  return $last_fr;
}

sub recout_to_exp {
  my $name_out = shift(@_);
  my $last_fr = shift(@_);
  print "in recout_toexp $name_out\n";

  @arr_num = ();
  @arr_lab = ();
  
  $convert_fac=1;
  open(OUT,"$name_out");
  $i=0;
  while(<OUT>) {
    $line=$_;
    #print "$line";
    if ($line=~/REC/){
      $line=~s/REC://;
      $line=~s/\n$//;
      $line=~s/\s+$//;
      #  print "here $last_fr\n";
      $line="$line $last_fr"; 
      #print "$line";
      @words = split(/ /, $line);
      foreach $tmp (@words) {
	if ($tmp=~/\d/) {
	  #print "$tmp ";
	  $arr_num[$i]=$tmp;
	}
	else {
	  #print "$tmp\n";
	  $arr_lab[$i]=$tmp;
	  $i++
	}
      }
    }
  }
  
  close(OUT);
  
  $i=0;
  $sum_sp=0;
  $sum_nsp=0;
  @expnd=();
  # run through array of labels
  foreach $lab (@arr_lab) {    
    $st=floor(0.5+$convert_fac*$arr_num[$i]);
    $end=floor(0.5+$convert_fac*$arr_num[$i+1]);
    # step size is frame rate
    for $tmp ($st..$end) {
      #   print "there $tmp $lab\n";
      if  ($tmp=~/\d/) {
	$expnd[$tmp]=$lab;
	#print "there $tmp $expnd[$tmp]\n";
      }
    }
    $i++;
  }

  $ii=0;
  #open(EXP_OUT,">exp_out.txt");
  open(EXP_OUT,">$name_out");
  # write to file
  foreach $tmp (@expnd) {
    print EXP_OUT "$ii $expnd[$ii] \n";
    $ii++;
  }
  close(EXP_OUT)

}

1;
