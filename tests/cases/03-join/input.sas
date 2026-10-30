data j;
  merge a(in=x) b(in=y);
  by k;
  if x and y;
run;
