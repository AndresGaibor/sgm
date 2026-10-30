/* priority: P1 */
proc sql; update work.accounts set status='DORMANT' where last_activity < '01JAN2020'd; quit;
