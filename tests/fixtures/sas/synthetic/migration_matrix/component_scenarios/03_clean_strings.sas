/* priority: P1 */
/* Limpieza y normalización textual, candidata a expresiones tMap. */
data work.cleaned; set work.contacts; normalized_name=compbl(upcase(strip(name))); email_clean=lowcase(strip(email)); run;
