data _null_;
  call system("proceso_ejemplo --lote 1 &");
run;
data _null_;
  do i = 1 to 3;
    call system("ps -ef | grep proceso_ejemplo | wc -l");
  end;
run;
