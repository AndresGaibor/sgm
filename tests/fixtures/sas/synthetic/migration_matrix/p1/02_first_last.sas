/* priority: P1 */
data work.first_event; set work.sorted_events; by customer_id; if first.customer_id then output; run;
