function [lna,num_models]=readLna(name)
  fid=fopen(name,'r');
  num_models=fread(fid,4,'uint8');
  dim=sum(num_models.*[16777216 4096 256 1]');
 % dim
  bytes=fread(fid,1,'int8');
  if bytes==4
    lna=fread(fid,[dim, inf],'float');
  else
    lna=fread(fid,[dim, inf],'short');
  end
  fclose(fid);

  
save('num_models'); % uusi!
