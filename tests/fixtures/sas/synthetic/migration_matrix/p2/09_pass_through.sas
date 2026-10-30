/* priority: P2 */
proc sql; connect to odbc as ext (noprompt='DSN=NOT_CONFIGURED'); select * from connection to ext (select id from sample_table); disconnect from ext; quit;
