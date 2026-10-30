/* priority: P1 */
/* Concatenación por grupo candidata a tDenormalize o agregación de texto. */
proc sort data=work.customer_tags; by customer_id tag_order; run;
data work.customer_tag_list; set work.customer_tags; by customer_id; length tag_list $500; retain tag_list; if first.customer_id then tag_list=''; tag_list=catx(',',tag_list,tag); if last.customer_id then output; run;
