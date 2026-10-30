/* priority: P1 */
data work.normalized_dates; set work.raw_dates; event_day=datepart(event_timestamp); month_start=intnx('month',event_day,0,'beginning'); format event_day month_start date9.; run;
