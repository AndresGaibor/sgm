/* priority: P1 */
proc format; value $tier 'A'='PREMIUM' 'B'='STANDARD' other='UNKNOWN'; run;
data work.labeled; set work.accounts; label=put(code,$tier.); run;
