/* priority: P1 */
/* Variable creada desde datos, candidata a contexto/variable global con alcance revisado. */
data _null_; set work.run_parameters; call symputx('batch_period',period); run;
