/* priority: P1 */
%macro monthly(first=1,last=3); %do m=&first %to &last; proc sql; create table work.sum&m as select id,sum(amount) as total from work.data&m group by id; quit; %end; %mend;
%monthly()
