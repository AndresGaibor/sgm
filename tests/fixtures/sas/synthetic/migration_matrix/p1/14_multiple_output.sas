/* priority: P1 */
data work.good work.review; set work.records; if score>0 then output work.good; else output work.review; run;
