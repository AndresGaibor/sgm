/* priority: P1 */
filename input '/example/data/customers.csv';
data work.customers; infile input dsd dlm=',' firstobs=2 truncover; input id :$12. name :$40. balance :comma12.2; run;
