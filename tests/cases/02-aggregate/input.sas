proc means data=work.a noprint nway;
  class k;
  var v;
  output out=work.s(drop=_type_ _freq_) sum=total;
run;
