/* priority: P2 */
%let root=/not-mounted/example;
%let job=daily;
%include "&root./&job..sas";
