/* priority: P1 */
proc sql; create table work.unique_channels as select distinct channel from work.web union select channel from work.branch; quit;
