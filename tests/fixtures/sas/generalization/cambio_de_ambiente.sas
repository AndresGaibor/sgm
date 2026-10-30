/* priority: P1 | Resuelve servidor y esquema según el ambiente de ejecución y calcula saldos del día. */
%let amb = DESA;

%if &amb = DESA %then %do;
  %let servidor = srv-desa;
  %let esquema = raw_d;
%end;
%else %if &amb = CERT %then %do;
  %let servidor = srv-cert;
  %let esquema = raw_c;
%end;
%else %if &amb = PROD %then %do;
  %let servidor = srv-prod;
  %let esquema = raw_p;
%end;
%else %do;
  %put ERROR: ambiente &amb desconocido;
  %abort cancel;
%end;

/* La biblioteca depende del ambiente elegido arriba. */
libname ods "/&servidor/&esquema";

/* Saldo del día por cuenta. */
proc sql;
  create table work.saldos_hoy as
  select cuenta,
         sum(saldo) as saldo_total
  from ods.saldos_diarios
  where fecha = today()
  group by cuenta;
quit;

/* Conteo para el log. */
proc sql noprint;
  select count(*) into :n_saldos trimmed from work.saldos_hoy;
quit;

%put NOTE: procesadas &n_saldos cuentas en &servidor;

/* Salida persistente en el mismo esquema. */
proc sql;
  create table ods.saldos_resumen as
  select cuenta, saldo_total
  from work.saldos_hoy
  where saldo_total <> 0;
quit;
