data b;
  set a;
  retain acc 0;
  acc = acc + x;
run;
