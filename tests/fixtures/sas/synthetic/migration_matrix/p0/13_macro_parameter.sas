/* priority: P0 */
%macro filter(src=,dst=); data &dst; set &src; where active='Y'; run; %mend;
%filter(src=work.accounts,dst=work.open_accounts)
