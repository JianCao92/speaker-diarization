
recipe_name=char(textread('recipe.txt','%s'));
list=textread(recipe_name,'%s%*[^\n]');

fid = fopen('matlab_lnapath.txt');
lna_path=fscanf(fid, '%s');
fclose(fid)

shift_bord=0.2; % oli: 1.5

for i=1:length(list)
  name_body=extr_name(char(list(i)));
  name_body=name_body(1:length(name_body)-4);
  name=[lna_path,name_body,'.lna'];
  fprintf(1,'%s\n',name);
  lna=readLna(name);
  lna_exp=exp(lna);
  lna_exp(2,:)=shift_bord*lna_exp(2,:);
  su=sum(lna_exp);
  lna_exp=lna_exp./[su; su];
  lna_new=log(lna_exp);
  writeLna(name,lna_new);

  % save last frame index
  last_fr=(length(lna));
  name=[pwd,'/',name_body,'.last_frame'];
  fid=fopen(name,'w');
  fprintf(fid,'%d',last_fr);
  fclose(fid);
end
exit
