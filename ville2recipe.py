#!/usr/bin/python2

fin = open('./Keski-Suomen_uutiset_20090913_spkr_correct.txt', 'r')
fout = open('./ville_turnseg_true_unmerged.recipe', 'w')

lna = 1
for l in fin:
    ll = l.split()
    fout.write('audio=/share/puhe/maciasa1/ville_demo/Keski-Suomen_uutiset_20090913-mono-16k.wav lna=a_' +
               str(lna) + ' start-time=' + ll[1] + ' end-time=' + ll[2] + ' speaker=speaker_\n')
    lna += 1
