/* priority: P1 */
proc sql; insert into work.audit select record_id,'REVIEWED' from work.review_queue; quit;
