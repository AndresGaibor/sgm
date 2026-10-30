/* priority: P1 */
proc transpose data=work.monthly out=work.wide prefix=m_; by customer_id; id month; var amount; run;
