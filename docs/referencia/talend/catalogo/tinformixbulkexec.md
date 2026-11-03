# tinformixbulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tinformixbulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tinformixbulkexec -->

# tInformixBulkExec

Executes Insert operations in Informix databases.

tInformixOutputBulk and tInformixBulkExec are generally used together in a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT operation used to feed a database. These two steps are fused together in the tInformixOutputBulkExec component. The advantage of using two components is that data can be transformed before it is loaded in the database.

## tInformixBulkExec Standard properties

These properties are used to configure tInformixBulkExec running in the Standard Job framework.

The Standard tInformixBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in:</span> No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Execution Platform | Select the operating system you are using. |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Host | Database server IP address. |
| Port | DB server listening port. |
| Database | Name of the database. |
| Schema | Name of the schema. |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Instance | Name of the Informix instance to be used. This information can<br>generally be found in the *SQL hosts*<br>file. |
| Table | Name of the table to be written. Note that only one table can be<br>written at a time. |
| Action on table | On the table defined, you can perform one of the following<br>operations:<br><br><br>None: No operation is carried<br>out.<br><br><br>Drop and create a table: The table<br>is removed and created again.<br><br><br>Create a table: The table does not<br>exist and gets created.<br><br><br>Create a table if not exists: The<br>table is created if it does not exist.<br><br><br>Drop a table if exists and create:<br>The table is removed if it already exists and created again.<br><br><br>Clear a table: The table content is<br>deleted. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Informix Directory | Informix installation directory, e.g. *"<br>C:\Program Files\IBM\IBM Informix Dynamic<br>Server\11.50\"*. |
| Data file | Name of the file to be loaded. |
| Action on data | On the data of the table defined, you can perform the following<br>operations:<br><br><br>Insert: Add new data to the table.<br>If duplicates are found, the Job stops.<br><br><br>Update: Update the existing table<br>data.<br><br><br>Insert or<br>update: Insert a new record. If the record with the given reference<br>already exists, an update would be made.<br><br><br>Update or<br>insert: Update the record with the given reference. If the record does<br>not exist, a new record would be inserted.<br><br><br>Delete: Delete the entry data which<br>corresponds to the input flow.<br><br>Information noteWarning:<br><br><br>*You must specify at least one key upon<br>which the Update and Delete operations are to be based. It<br>is possible to define the columns which should be used as<br>the key from the schema, from both the Basic Settings and the Advanced Settings, to optimise these<br>operations.* |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC parameters | Specify additional connection properties for the DB connection you<br>are creating. This option is not available if you have selected the<br>Use an existing connection<br>check box in the Basic<br>settings. |
| Field terminated by | Character, string or regular expression which separates the<br>fields. |
| Set DBMONEY | Select this check box to define the decimal separator in the<br>Decimal separator field. |
| Set DBDATE | Select the date format that you want to apply. |
| Rows Before Commit | Enter the number of rows to be processed before the commit. |
| Bad Rows Before Abort | Enter the number of rows in error at which point the Job should<br>stop. |
| tStat<br>Catcher Statistics | Select this check box to colelct the log data at component<br>level. |
| Output | Where the output should go. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>NB\_LINE\_UPDATED: the number of rows updated.<br>This is an After variable and it returns an integer.<br><br><br>NB\_LINE\_INSERTED: the number of<br>rows inserted. This is an After variable and it returns an integer.<br><br><br>NB\_LINE\_DELETED: the<br>number of rows deleted. This is an After variable and it returns an integer.<br><br><br>QUERY: the query statement processed. This<br>is an After variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component offers database query flexibility and covers all<br>possible DB2 queries which may be required. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | The database server/client must be installed on the same<br>machine where Talend Studio is installed or where the Job using tInformixBulkExec is deployed, so that the component functions<br>properly.<br><br>This component requires installation of its related jar files. |
