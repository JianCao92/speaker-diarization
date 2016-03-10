function writeLna(name,data)
%  name
  load num_models;
  fid=fopen(name,'w');
  fwrite(fid,num_models,'uint8');
  %dim
  fwrite(fid,4,'int8');
  %if bytes==4
    lna=fwrite(fid,data,'float');
  %else
  %  lna=fwrite(fid,data,'short');
  %end
  fclose(fid);
  