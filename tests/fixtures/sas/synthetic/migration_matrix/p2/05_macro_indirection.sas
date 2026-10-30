/* priority: P2 */
%let table1=work.alpha;
%let index=1;
data work.selected; set &&table&index; run;
