#!/bin/sh
#

# Set name for this job that will be shown by qstat
#$ -N make_lnas

# Specify which shell to use
#$ -S /bin/sh

# Send mail to these users
#$ -M ulpu@cis.hut.fi
# Mail at beginning/end/if suspended/or aborted
#$ -m ea

# job requirements
#$ -l t=50:00:00,mem=2.5G
#$ -soft -q helli.q

export LD_LIBRARY_PATH="/share/puhe/x86_64/lib/"
#cd /home/ulpu/aku/
#make feacat
#cd /share/puhe/ulpu/test_aku/
#/share/puhe/ulpu/test_aku/calculate_noise.pl
/home/maciasa1/Work/Tools/SAD/tokenpass/classify_speecon.pl