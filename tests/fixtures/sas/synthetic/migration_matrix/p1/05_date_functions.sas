/* priority: P1 */
data work.renewals; set work.policies; renewal=intnx('month',start_date,12,'same'); months=intck('month',start_date,today()); format renewal date9.; run;
