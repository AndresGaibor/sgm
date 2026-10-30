/* priority: P1 */
filename report '/example/out/summary.txt';
data _null_; set work.summary; file report; put customer_id $20. total comma12.2; run;
