/* priority: P0 */
proc sql; create table work.labeled as select p.id,c.category from work.products p left join work.categories c on p.cat_id=c.id; quit;
