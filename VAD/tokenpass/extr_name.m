function name_chop=extr_name(name)
  le_name=length(name);
  i=0;
  while (not(name(le_name-i)=='/'))
    i=i+1;
  end
  name_chop=name(le_name-i+1:le_name);