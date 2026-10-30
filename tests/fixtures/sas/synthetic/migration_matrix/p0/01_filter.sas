/* priority: P0 */
data work.clean; set work.orders; where status='PAID'; net=amount-discount; run;
