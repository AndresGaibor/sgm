/* priority: P0 */
data work.contact_export; set work.customer_master(keep=customer_id email status); where status='ACTIVE'; run;
