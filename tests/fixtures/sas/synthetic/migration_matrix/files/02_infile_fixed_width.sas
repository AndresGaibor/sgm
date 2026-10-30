/* priority: P1 */
data work.fixed_records; infile '/example/data/records.dat' lrecl=80; input id $ 1-10 region $ 11-12 amount 13-24; run;
