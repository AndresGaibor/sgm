/* priority: P1 */
data _null_; set work.run_control; call symputx('run_period',period); run;
%put Processing period=&run_period;
