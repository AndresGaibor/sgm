proc transpose data=a out=b;
  by x;
  id y;
  var z;
run;

%include "otro_externo.sas";
