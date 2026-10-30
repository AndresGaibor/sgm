/* priority: P0 */
proc sql; create table work.contacts as select id,channel from work.web union all select id,channel from work.store; quit;
