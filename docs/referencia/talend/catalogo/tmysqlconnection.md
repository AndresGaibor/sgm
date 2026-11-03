# tmysqlconnection

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tmysqlconnection  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmysqlconnection -->

# Checking customer table against a given DQ rule to select customer records

This scenario applies only to Talend Data Management Platform, Talend Big Data Platform, Talend Real-Time Big Data Platform, Talend Data Services Platform, and Talend Data Fabric.

This example is a three-component Job that checks a MySQL customer table against a given data quality rule so as to query specific customer records.

![](https://help.qlik.com/talend/en-US/components/Resources/images/use_case-tmysqlinvalidrows-dq_rules1.png)

The components used in the Job are:

* tMysqlConnection: this component creates the connection to the MySQL database so that the other components can reuse it.

* tMySQLInvalidRows: this component reuses the connection created by tMysqlConnection and query the customer records against the given data quality rule.

* tLogRow: this component presents the result of running this Job.

  Information noteRemember: The connection components, including tMysqlConnection and tMySQLInvalidRows, have been regrouped into the tDBConnection component. They are automatically converted into this component when you place them on the workspace.

### In this section

* [Dropping and linking the components](https://help.qlik.com/talend/en-US/components/8.0/mysql-validation/tmysqlconnection-tmysqlinvalidrows-tlogrow-tmysqlinvalidrows-tlogrow-dropping-and-linking-components-standard-component-enterprise-from?id=1237)
* [Configuring the connection to the database](https://help.qlik.com/talend/en-US/components/8.0/mysql-validation/tmysqlconnection-tmysqlinvalidrows-tlogrow-tmysqlinvalidrows-tlogrow-configuring-connection-to-database-standard-component-enterprise-to?id=1238)
* [Configuring the query of the customer records](https://help.qlik.com/talend/en-US/components/8.0/mysql-validation/tmysqlconnection-tmysqlinvalidrows-tlogrow-tmysqlinvalidrows-tlogrow-configuring-query-of-customer-records-of-interest-standard-component-enterprise?id=1239)
* [Executing the Job](https://help.qlik.com/talend/en-US/components/8.0/mysql-validation/tmysqlconnection-tmysqlinvalidrows-tlogrow-tmysqlinvalidrows-tlogrow-executing-job-standard-component-enterprise-the?id=1240)

**Related reference**

* [tMysqlConnection](https://help.qlik.com/talend/en-US/components/8.0/tmysqlconnection "Opens a connection to the specified MySQL database for reuse in the subsequent subJob or subJobs.")
* [tMySQLInvalidRows](https://help.qlik.com/talend/en-US/components/8.0/tmysqlinvalidrows "Checks MySQL database rows against specific Data Quality patterns (regular expression) or Data Quality rules (business rule).")

**Related information**

* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)
