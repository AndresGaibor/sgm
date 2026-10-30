/* priority: P1 | Proceso de dos transformaciones rodeado de control de ejecución, log y limpieza. */
options nosource nomprint;
libname src "/data/in";
libname out "/data/out";

%let t_ini = %sysfunc(datetime());
%put NOTE: inicio del proceso &=t_ini;

/* Pausa de cortesía antes de empezar (no transforma datos). */
%let rc = %sysfunc(sleep(5));

/* Preparación de carpetas y archivos con comandos de sistema. */
%sysexec mkdir -p /data/tmp/entrada;
x "mv /data/in/*.csv /data/tmp/entrada";

filename cmd pipe "ls /data/tmp/entrada";

/* Limpieza de WORK de la corrida anterior. */
proc delete data=work._all_; run;

/* Transformación 1: solo movimientos con tipo válido, con signo según el tipo. */
data work.lectura;
  set src.movimientos;
  where tipo in ('D', 'C');
  importe_signo = ifn(tipo = 'D', -importe, importe);
run;

/* Transformación 2: saldo acumulado por cuenta. */
data out.saldo_cuentas;
  set work.lectura;
  by cuenta;
  if first.cuenta then saldo = 0;
  saldo + importe_signo;
  if last.cuenta;
  keep cuenta saldo;
run;

/* Conteo de cuentas para el log (solo se usa para mensajes). */
data _null_;
  set out.saldo_cuentas end=fin;
  n_cuentas + 1;
  if fin then call symputx('n_cuentas', n_cuentas);
run;

%put NOTE: cuentas procesadas = &n_cuentas;

/* Limpieza final de temporales. */
proc delete data=work._all_; run;

/* Medición de tiempos. */
%let t_fin = %sysfunc(datetime());
%put NOTE: duración %sysevalf(&t_fin - &t_ini) segundos;
%put NOTE: fin del proceso;
