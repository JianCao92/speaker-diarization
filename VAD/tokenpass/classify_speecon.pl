#!/usr/bin/perl
use Cwd;

#$model_root="/share/work/ulpu/puhe_luokitin/tokenpass/hmms/";
$cwd=cwd();
$model_root=$cwd."/hmms/";

# *** select speech vs. non-speech model

# mallit esim.:
# mfcc_16g_9.10.2007_10 # public place noise
# mfcc_16g_11.10.2007_10 # more public place noise
# mfcc_16g_15.10.2007_10 # even more public place noise

#$model = "mfcc_16g_9.10.2007_10";
$model = "mfcc_16g_11.10.2007_10"; # usually this one is used
#$model = "mfcc_16g_15.10.2007_10";

$model="$model_root$model";
# *** recipe: lists the audio files

$recipe = shift(@ARGV);

#$fileformat = "-R"; # Empty for wav-files, -R for raw

open(RECIPE,">recipe.txt");
print RECIPE "$recipe";
close(RECIPE);


# *** where to write information:
$LNADIR = shift(@ARGV);
$exp_dir = shift(@ARGV);
# $LNADIR="/share/puhe/maciasa1/yleuutiset-wavs/sad-lna/"; # sp/nsp probablities
# $exp_dir="/share/puhe/maciasa1/yleuutiset-wavs/sad-exp/"; # classification results

# system "mkdir $LNADIR";
# system "mkdir $exp_dir";

$fs_frame=125;

use generate_lnas_yle;
use tokenpass;

# 1 generate state (speech or non-speech) probabilites -> lna-files
#generate_lnas_yle::generate_lnas($model,$recipe,$LNADIR,$fileformat);

# 2 shift decision border
#system("./start_matlab.pl $LNADIR");

# 3 speech/non-speech classification
tokenpass::test_token_pass($fs_frame,$model,$recipe,$LNADIR,$exp_dir);
