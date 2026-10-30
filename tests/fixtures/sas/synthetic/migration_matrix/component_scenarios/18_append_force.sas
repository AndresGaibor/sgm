/* priority: P1 */
/* FORCE permite diferencias de atributos: no asumir esquema equivalente. */
proc append base=work.history data=work.new_period force; run;
