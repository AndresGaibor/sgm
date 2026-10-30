/* priority: P1 */
proc datasets library=work nolist; copy out=work_backup; delete scratch_one scratch_two; quit;
/* Mantenimiento sobre una tabla real (librería de datos, no WORK): sí es un paso. */
proc datasets library=prod nolist; delete historico_clientes; quit;
