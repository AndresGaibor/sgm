/* priority: P1 */
data work.current; update work.master work.changes; by customer_id; run;
