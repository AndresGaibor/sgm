proc means data=work.a noprint;
  class k;
  var v;
  output out=work.s;
run;
