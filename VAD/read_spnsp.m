% load precomputed speech/non-speech file

filename1 = '/share/work/ulpu/puhe_luokitin/data_exp/1DB-224522.exp';

[col1, col2] = textread(filename1,'%n%s%*[^\n]','delimiter',',');

for i=1:length(col1)
    if strcmp('p ',col2(i))
      data(i)=1;
    else
      data(i)=0;
    end
end

% ----------------------
% tulosten katselemiseen

t_end = 60*125*10;

t_stp = 60*125; % 1 min

t_beg = 0;

while t_beg + t_stp <= t_end
   
    disp(t_beg/t_stp)
    plot((1:t_stp)/125,data(t_beg+1:t_beg+t_stp));
    axis([0 60 0 1.2])
    pause
    t_beg = t_beg + t_stp;
end
