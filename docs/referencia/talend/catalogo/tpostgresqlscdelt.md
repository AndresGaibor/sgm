# tpostgresqlscdelt

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tpostgresqlscdelt  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tpostgresqlscdelt -->

# tPostgresqlSCDELT

Addresses Slowly Changing Dimension needs through SQL queries (server-side processing mode), and logs the changes into a dedicated DB2 SCD table.

The tPostgresqlSCDELT reflects and tracks changes in a dedicated Postgresql SCD table.

## tPostgresqlSCDELT Standard properties

These properties are used to configure tPostgresqlSCDELT running in the Standard Job framework.

The Standard tPostgresqlSCDELT component belongs to the Business Intelligence and the Databases families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | Either Built-in or Repository.<br><br><ul> <li> <p> <span>Built-in</span>: No property data stored                           centrally. Enter properties manually.</p> </li> <li> <p> <span>Repository</span>: Select the repository                           file where Properties are stored. The fields that come after are                           pre-filled in using the fetched data.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| DB Version | Select the database version in the dropdown list. |
| Host | Enter the database server IP address. |
| Port | Listening port number of DB server. |
| Database | Enter the name of the database. |
| Schema | Enter the name of the PostgreSQL schema. |
| Username and Password | Enter the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Source table | Enter the name of the input DB2 SCD table. |
| Table | Enter the name of the table to be written. Note that only one table can be<br>written at a time |
| Action on table | Select to perform one of the following operations on the table defined:<br><br><br>None: No action carried out on the<br>table.<br><br><br>Drop and create table: The table is<br>removed and created again<br><br><br>Create table: A new table gets<br>created.<br><br><br>Create table if not exists: A table gets<br>created if it does not exist.<br><br><br>Clear table: The table content is<br>deleted. You have the possibility to rollback the operation.<br><br><br>Truncate table: The table content is<br>deleted. You don not have the possibility to rollback the<br>operation. |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-in</span>: The schema is created								and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already								exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul><br><br>This component supports PostgreSQL vector data types. Use the<br>VECTOR or Dynamic DB type in your schema<br>column definition to store and then query vector embeddings. For more information about<br>pgvector, read [the Amazon documentation](https://aws.amazon.com/about-aws/whats-new/2023/05/amazon-rds-postgresql-pgvector-ml-model-integration/). |
| Surrogate Key | Select the surrogate key column from the list. |
| Creation | Select the method to be used for the surrogate key generation.<br><br>For more information regarding the creation methods, see [SCD management methodology](https://help.qlik.com/talend/en-US/components/8.0/scd/scd-management-methodology). |
| Source Keys | Select one or more columns to be used as keys, to ensure the unicity of<br>incoming data. |
| Use SCD Type 1 fields | Use type 1 if tracking changes is not necessary. SCD Type 1 should be used<br>for typos corrections for example. Select the columns of the schema that will be<br>checked for changes. |
| Use SCD Type 2 fields | Use type 2 if changes need to be tracked down. SCD Type 2 should be used to<br>trace updates for example. Select the columns of the schema that will be checked<br>for changes. |
| SCD type 2 fields | Click the [+] button to add as many rows as needed, each row for a column. Click<br>the arrow on the right side of the cell and select the column whose value changes will<br>be tracked using Type 2 SCD from the drop-down list displayed .<br><br>This table is available only when the Use SCD type 2 fields<br>option is selected. |
| Start date | Specify the column that holds the start date for<br>type 2 SCD.<br><br>This list is available only when the Use SCD type 2 fields<br>option is selected. |
| End date | Specify the column that holds the end date for type<br>2 SCD.<br><br>This list is available only when the Use SCD type 2 fields<br>option is selected.<br><br>Information noteNote: To avoid duplicated change records, it is recommended to<br>select a column that can identify each change for this field. |
| Log active status | Select this check box and from the<br>Active field drop-down list displayed, select<br>the column that holds the true or false status value, which helps to spot the active<br>record for type 2 SCD.<br><br>This option is available only when the Use SCD type 2 fields<br>option is selected. |
| Log versions | Select this check box and from the Version field drop-down list displayed, select the column<br>that holds the version number of the record for type 2 SCD.<br><br>This option is available only when the Use SCD type 2 fields<br>option is selected. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional JDBC parameters for the database connection created.<br><br>This property is not available when the Use an existing connection check box in the Basic<br>settings view is selected. |
| Debug mode | Select this checkbox to display each step during processing entries in a<br>database. |
| tStat<br>Catcher Statistics | Select this checkbox to collect log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an output component. It requires an<br>input component and Row main link as input.<br><br>This component supports PostgreSQL vector data types. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
