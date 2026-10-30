/* priority: P1 */
proc sort data=work.account_events out=work.latest_event nodupkey; by account_id descending event_timestamp; run;
