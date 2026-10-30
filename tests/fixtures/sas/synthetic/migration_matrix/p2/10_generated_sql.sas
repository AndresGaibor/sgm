/* priority: P2 */
%macro generated; proc sql; create table work.out as select &column_list from &source_table; quit; %mend;
%generated
