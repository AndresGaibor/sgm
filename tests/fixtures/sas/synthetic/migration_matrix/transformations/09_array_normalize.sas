/* priority: P1 */
data work.month_rows; set work.annual; array amount[3] jan feb mar; do month_no=1 to 3; monthly_amount=amount[month_no]; output; end; keep customer_id month_no monthly_amount; run;
