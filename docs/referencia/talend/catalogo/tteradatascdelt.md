# tteradatascdelt

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tteradatascdelt  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tteradatascdelt -->

# tTeradataSCDELT

Addresses Slowly Changing Dimension needs through SQL queries (server-side processing mode), and logs the changes into a dedicated Teradata SCD table.

tTeradataSCDELT reflects and tracks changes in a dedicated Teradata SCD table.

## tTeradataSCDELT Standard properties

These properties are used to configure tTeradataSCDELT running in the Standard Job framework.

The Standard tTeradataSCDELT component belongs to the Business Intelligence and the Databases families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property Type | Either Built-In or Repository.<br><br><ul> <li> <p> <span>Built-In</span>: No                           property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select                           the repository file in which the properties are stored. The database                           connection fields that follow are completed automatically using the data                           retrieved.</p> </li> </ul> |
| Use an existing<br>connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Host | Enter the IP address or hostname of the<br>database server. |
| Database | Enter the name of the database you want to<br>use. |
| Username and Password | Enter the user authentication data to access<br>the database.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Source table | Enter the name of the input Teradata SCD<br>table. |
| Table | Enter the name of the table to be written. Note<br>that only one table can be written at a time. |
| Action on table | Select one of the following operations to be<br>performed on the table defined:<br><br><ul> <li> <p> <span>None</span>: No action                           carried out on the table.</p> </li> <li> <p> <span>Create table</span>: A                           new table gets created.</p> </li> <li> <p> <span>Drop and create                              table</span>: The table is removed and created again.</p> </li> <li> <p> <span>Create table if not                              exists</span>: A table gets created if it does not exist.</p> </li> <li> <p> <span>Drop table if exists and                              create</span>: The table is removed if it already exists and                           created again.</p> </li> <li> <p> <span>Clear table</span>: The                           table content is deleted. You have the possibility to rollback the                           operation.</p> </li> <li> <p> <span>Truncate table</span>:                           The table content is deleted. You don not have the possibility to                           rollback the operation.</p> </li> </ul> |
| Create | Select the type of the table to be created:<br><br><ul> <li> <p> <span>SET TABLE</span>: creates                           a SET table that does not allow duplicate rows to be inserted.</p> </li> <li> <p> <span>MULTISET TABLE</span>:                           creates a MULTISET table that allows duplicate rows to be inserted.</p> </li> </ul><br><br>This list is available only when Create table, Drop and create table,<br>Create table if not<br>exists, or Drop<br>table if exists and create is selected from the Action on table drop-down<br>list. |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <ul> <li> <p> <span>Built-In</span>: The                           schema is created and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The                           schema already exists and is stored in the Repository, hence can be                           reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Surrogate key | Select the surrogate key column from the<br>list. |
| Creation | Select the method to be used for the surrogate<br>key generation.<br><br>For more information about the creation<br>methods, see [SCD management methodology](https://help.qlik.com/talend/en-US/components/8.0/scd/scd-management-methodology). |
| Source Keys | Select one or more columns to be used as keys,<br>to ensure the unicity of the incoming data. |
| Use SCD type 1 fields | Select this check box to use SCD Type 1 if<br>tracking changes is not necessary. SCD Type 1 should be used for typos<br>corrections for example. |
| SCD type 1 fields | Click the [+] button to add as many rows as needed, and<br>in each row select an input schema column that will be checked for Type 1<br>changes.<br><br>This table is available only when the<br>Use SCD type 1<br>fields check box is selected. |
| Use SCD type 2 fields | Select this check box to use SCD Type 2 if<br>changes need to be tracked down. SCD Type 2 should be used to trace updates for<br>example. |
| SCD type 2 fields | Click the [+] button to add as many rows as needed, each row for a column. Click<br>the arrow on the right side of the cell and select the column whose value changes will<br>be tracked using Type 2 SCD from the drop-down list displayed .<br><br>This table is available only when the Use SCD type 2 fields<br>option is selected. |
| Start date | Specify the column that holds the start date for<br>type 2 SCD.<br><br>This list is available only when the Use SCD type 2 fields<br>option is selected. |
| End date | Specify the column that holds the end date for type<br>2 SCD.<br><br>This list is available only when the Use SCD type 2 fields<br>option is selected.<br><br>Information noteNote: To avoid duplicated change records, it is recommended to<br>select a column that can identify each change for this field. |
| Log active status | Select this check box and from the<br>Active field drop-down list displayed, select<br>the column that holds the true or false status value, which helps to spot the active<br>record for type 2 SCD.<br><br>This option is available only when the Use SCD type 2 fields<br>option is selected. |
| Log versions | Select this check box and from the Version field drop-down list displayed, select the column<br>that holds the version number of the record for type 2 SCD.<br><br>This option is available only when the Use SCD type 2 fields<br>option is selected. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC<br>Parameters | Specify additional connection properties for<br>the database connection you are creating.<br><br>This field is not available if the Use an existing connection<br>check box is selected. |
| Source fields value include<br>Null | Select this check box to allow the source<br>columns to have Null values. The source columns here refer to the fields<br>defined in the SCD type 1<br>fields and SCD type<br>2 fields tables. |
| tStatCatcher Statistics | Select this check box to gather the Job<br>processing metadata at the Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an output component<br>and it always needs an incoming link. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | This component requires installation of its related jar files. |
