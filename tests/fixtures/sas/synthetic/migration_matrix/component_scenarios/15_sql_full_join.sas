/* priority: P1 */
proc sql; create table work.reconciled as select coalesce(a.id,b.id) as id,a.value as source_value,b.value as target_value from work.source_data a full join work.target_data b on a.id=b.id; quit;
