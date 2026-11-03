# teltinput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/teltinput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/teltinput -->

# Aggregating Snowflake data using ELT components

This scenario shows you an example of aggregating Snowflake data from two source tables STUDENT and TEACHER to one target table FULLINFO using the ELT components.

The ELT components, that is, tELTInput, tELTMap, and the tELTOutput components, are closely related. They work jointly to generate SQL statements from database tables. The SQL statement is then executed by the tELTOutput component to perform specified actions to a specific database table. The Job in this scenario shows a common way in which the ELT components are connected to generate SQL statements from multiple database tables. The following list describes the functions of the components.

* tELTInput specifies input database table and schema. You can use multiple database tables as the input by connecting multiple tELTInput components to a tELTMap component and specifying a database table for each of the tELTInput components.
* tELTMap defines how the schema columns of the input database tables are mapped to the output columns. This component also allows you to set the mapping conditions.
* tELTOutput generates the SQL statement according to the mapping relationship defined in tELTMap and the actions (including action on table and action on data). The SQL statement is stored in the Query variable of the tELTOutput component.

In this example, context variables are used to hold all the input and output table names and connection names.

### In this section

* [Creating the Job](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltinput-teltmap-tsnowflakeinput-tlogrow-creating-job-a-new?id=1755)
* [Connecting to Snowflake](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltinput-teltmap-tsnowflakeinput-tlogrow-connecting-to-snowflake-standard-component?id=1756)
* [Configuring the input components](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltinput-teltmap-tsnowflakeinput-tlogrow-configuring-input-components?id=1757)
* [Configuring the output component](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltinput-teltmap-tsnowflakeinput-tlogrow-configuring-output-component?id=1758)
* [Configuring the map component for aggregating Snowflake data](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltinput-teltmap-tsnowflakeinput-tlogrow-configuring-map-component-for-aggregating-snowflake-data-click?id=1759)
* [Closing the Snowflake connection](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltinput-teltmap-tsnowflakeinput-tlogrow-closing-snowflake-connection?id=1760)
* [Executing the Job](https://help.qlik.com/talend/en-US/components/8.0/elt-greenplum/teltinput-teltmap-tsnowflakeinput-tlogrow-executing-job-press?id=1761)

**Related concepts**

* [tSnowflakeInput](https://help.qlik.com/talend/en-US/components/8.0/tsnowflakeinput "Reads data from a Snowflake table into the data flow of your Job based on an SQL query.")

**Related reference**

* [tSnowflakeConnection](https://help.qlik.com/talend/en-US/components/8.0/tsnowflakeconnection "Opens a connection to Snowflake that can then be reused by other Snowflake components.")
* [tSnowflakeClose](https://help.qlik.com/talend/en-US/components/8.0/tsnowflakeclose "Closes an active Snowflake connection to release the occupied resources.")

**Related information**

* [tELTInput](https://help.qlik.com/talend/en-US/components/8.0/elt-jdbc/teltinput)
* [tELTMap](https://help.qlik.com/talend/en-US/components/8.0/elt-jdbc/teltmap)
* [tELTOutput](https://help.qlik.com/talend/en-US/components/8.0/elt-jdbc/teltoutput)
* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)
