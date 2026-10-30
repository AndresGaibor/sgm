/* priority: P1 */
data work.approved work.review work.rejected; set work.applications; if score>=700 then output work.approved; else if score>=500 then output work.review; else output work.rejected; run;
