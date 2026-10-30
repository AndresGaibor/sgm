/* priority: P0 | synthetic parent Job with a static child dependency chain */
/* Schedule: Weekdays 06:15 for the local synthetic test environment */
%let report_month = 202610;
%let test_mode = Y;

%macro run_step(step_num=, program=);
    %put NOTE: Starting synthetic portfolio step &step_num.;
    %include "&program" / source2;
    %put NOTE: Completed synthetic portfolio step &step_num.;
%mend run_step;

%macro run_daily_portfolio;
    %run_step(step_num=1, program=Programs/Banking/01_load_customers.sas);
    %run_step(step_num=2, program=Programs/Banking/02_load_accounts.sas);
    %run_step(step_num=3, program=Programs/Banking/03_enrich_transactions.sas);
    %run_step(step_num=4, program=Programs/Banking/04_customer_metrics.sas);
    %run_step(step_num=5, program=Programs/Banking/05_credit_risk_scoring.sas);
    %run_step(step_num=6, program=Programs/Banking/06_monthly_report.sas);
    %run_step(step_num=7, program=Programs/Banking/07_append_risk_history.sas);
%mend run_daily_portfolio;

%run_daily_portfolio;
