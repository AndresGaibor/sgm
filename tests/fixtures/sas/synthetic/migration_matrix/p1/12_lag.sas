/* priority: P1 */
data work.delta; set work.daily; previous=lag(value); if not missing(previous) then change=value-previous; run;
