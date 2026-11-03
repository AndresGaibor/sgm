# tjdbcscdelt (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tjdbcscdelt  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tjdbcscdelt -->

# tJDBCSCDELT

Tracks data changes in a source database table using SCD (Slowly Changing Dimensions) Type 1 method and/or Type 2 method and writes both the current and historical data into a specified SCD dimension table.

## tJDBCSCDELT Standard properties

These properties are used to configure tJDBCSCDELT running in the Standard Job framework.

The Standard tJDBCSCDELT component belongs to two families: Business Intelligence and Databases.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property Type | Select the way the connection details<br>will be set.<br><br><ul> <li> <p> <span>Built-In</span>: The connection details will be set                                locally for this component. You need to specify the values for all                                related connection properties manually.</p> </li> <li> <p> <span>Repository</span>: The connection details stored                                centrally in <span><span>Repository</span><abbr> &gt; </abbr><span>Metadata</span></span> will be reused by this component. </p> <p>You need to click                                the <span>[...]</span> button next to it and in the pop-up                                    <span>Repository Content</span> dialog box, select the                                connection details to be reused, and all related connection                                properties will be automatically filled in.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined. |
| JDBC URL | The JDBC URL of the database to be used. For example, the JDBC URL for the Amazon Redshift database is jdbc:redshift://endpoint:port/database. |
| Driver JAR | Complete this table to load the driver JARs needed. To do<br>this, click the [+] button under the table to add<br>as many rows as needed, each row for a driver JAR, then select the cell and click the<br>[...] button at the right side of the cell to<br>open the Module dialog box from which you can select the driver JAR<br>to be used. For example, the driver jar RedshiftJDBC41-1.1.13.1013.jar for the Redshift database.<br><br>For more information, see [Importing a database driver](https://help.qlik.com/talend/r/en-US/8.0/components/jdbc/importing-database-driver). |
| Driver Class | Enter the class name for the specified driver between double<br>quotation marks. For example, for the RedshiftJDBC41-1.1.13.1013.jar driver, the name to be entered is<br>com.amazon.redshift.jdbc41.Driver. |
| Username and Password | Enter the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| DB Schema | Specify the name of the database schema. For the<br>database that does not support schema, just leave this field empty. |
| Source table | Specify the name of the source input table whose<br>data changes will be captured by SCD. |
| Table | Specify the name of the dimension table into which the<br>data captured by SCD will be written. |
| Action on<br>table | Select an operation to be performed on the table defined.<br><br><ul> <li> <p> <span>None</span>: No operation is carried out.</p> </li> <li> <p> <span>Drop and create table</span>: The table is removed            and created again.</p> </li> <li> <p> <span>Create table</span>: The table does not exist and            gets created.</p> </li> <li> <p> <span>Create table if does not exist</span>: The table is            created if it does not exist.</p> </li> <li> <p> <span>Drop table if exist and create</span>: The table is            removed if it already exists and created again.</p> </li> <li> <p> <span>Clear table</span>: The table content is            deleted. You have the possibility to rollback the operation.</p> </li> <li> <p> <span>Truncate table</span>: The table content is            deleted. You do not have the possibility to rollback the operation.</p> </li> </ul> |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>Click Edit schema to make changes to<br>the schema. If you make changes, the schema automatically becomes built-in.<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Surrogate key | Set the column where the generated surrogate key<br>will be stored. A surrogate key can be generated based on a method selected on the<br>Creation list. |
| Creation | Select any of the following methods to be used<br>for generating the surrogate key.<br><br><ul> <li> <p> <span>Auto                  increment</span>: an auto-incrementing integer will be used.</p> </li> <li> <p> <span>DB                  sequence</span>: a sequence will be used.</p> </li> </ul> |
| Source keys | Specify one or more columns used as the key(s)<br>that ensure the unicity of the incoming data. |
| Use SCD type 0 fields | Select this check box and in the SCD type 0 fields table displayed, specify the column(s)<br>whose value changes will be tracked using Type 0 SCD.<br><br>This option only supports these databases: Exasol, MySql, MSSql, Oracle, Postgresql, and Snowflake. |
| Use SCD type 1 fields | Select this check box and in the SCD type 1 fields table displayed, specify the column(s)<br>whose value changes will be tracked using Type 1 SCD. |
| SCD type 1 fields | Click the [+] button to add as many rows as needed, each row for a column, then<br>click the right side of the cell and from the drop-down list displayed select the column<br>whose value changes will be tracked using Type 1 SCD. |
| Use SCD type 2 fields | Select this check box and in the SCD type 2 fields table displayed, specify the column(s)<br>whose value changes will be tracked using Type 2 SCD. |
| SCD type 2 fields | Click the [+] button to add as many rows as needed, each row for a column. Click<br>the arrow on the right side of the cell and select the column whose value changes will<br>be tracked using Type 2 SCD from the drop-down list displayed .<br><br>This table is available only when the Use SCD type 2 fields<br>option is selected. |
| Start date | Specify the column that holds the start date for<br>type 2 SCD.<br><br>This list is available only when the Use SCD type 2 fields<br>option is selected. |
| End date | Specify the column that holds the end date for type<br>2 SCD.<br><br>This list is available only when the Use SCD type 2 fields<br>option is selected.<br><br>Information noteNote: To avoid duplicated change records, it is recommended to<br>select a column that can identify each change for this field. |
| Log active status | Select this check box and from the<br>Active field drop-down list displayed, select<br>the column that holds the true or false status value, which helps to spot the active<br>record for type 2 SCD.<br><br>This option is available only when the Use SCD type 2 fields<br>option is selected. |
| Log versions | Select this check box and from the Version field drop-down list displayed, select the column<br>that holds the version number of the record for type 2 SCD.<br><br>This option is available only when the Use SCD type 2 fields<br>option is selected. |
| Mapping | Specify the metadata mapping file<br>for the database to be used. The metadata mapping file is used for the data<br>type conversion between database and Java. For more information about the<br>metadata mapping, see the related documentation for Type mapping.<br><br>Information noteNote: You can use Hive mapping to support Databricks Delta<br>Lake. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Source fields value include<br>Null | Select this check box to allow the source<br>columns to have Null values. The source columns here refer to the fields defined in the<br>SCD type 1 fields and SCD type 2 fields tables. |
| Debug mode | Select this check box to display each step during<br>processing the data in a database. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| Usage rule | This component can be used as a standalone component of a Job or<br>subJob. |

**Related concepts**

* [Tracking data changes in a PostgreSQL table using the tPostgreSQLSCDELT component](https://help.qlik.com/talend/en-US/components/8.0/tjdbcscdelt-tfixedflowinput-tjdbcinput-tlogrow-tracking-data-changes-in-postgresql-table-using-tpostgresqlscdelt-component-standard-component-the "This scenario describes a Job that captures the employee data changes in a PostgreSQL table using SCD (Slowly Changing Dimensions) Type 1 and Type 2 methods implemented by the tPostgreSQLSCDELT component, and writes both the current and historical data in a SCD dimension table.")
* [Tracking data changes in a Snowflake table using the tJDBCSCDELT component](https://help.qlik.com/talend/en-US/components/8.0/tjdbcscdelt-tfixedflowinput-tjdbcinput-tlogrow-tracking-data-changes-in-snowflake-table-using-tjdbcscdelt-component-standard-component-the "This scenario describes a Job that captures the employee data changes in a Snowflake table using SCD (Slowly Changing Dimensions) Type 1 and Type 2 methods implemented by the tJDBCSCDELT component, and writes both the current and historical data in a SCD dimension table.")
