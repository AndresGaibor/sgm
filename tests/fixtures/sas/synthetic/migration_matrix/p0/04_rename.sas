/* priority: P0 */
data work.accounts; set work.source(rename=(acct_id=account_id)); run;
