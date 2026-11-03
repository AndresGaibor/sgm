# tsybasebulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsybasebulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsybasebulkexec -->

# tSybaseBulkExec

Gains in performance during Insert operations to a Sybase database.

The tSybaseOutputBulk and tSybaseBulkExec components are generally used together as parts of a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT operation used to feed a database. These two steps are fused together in the tSybaseOutputBulkExec component, detailed in a separate section. The advantage of using two separate components is that the data can be transformed before it is loaded in the database.

## tSybaseBulkExec Standard properties

These properties are used to configure tSybaseBulkExec running in the Standard Job framework.

The Standard tSybaseBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| DB Version | Select the version of the Sybase database to be used from the<br>drop-down list. |
| Server | Database server IP address<br><br>Available when you select Bulk<br>Update from the Action on<br>data list in the Advanced<br>settings view of tSybaseBulkExec. |
| Port | Listening port number of DB server.<br><br>Available when you select Bulk<br>Update from the Action on<br>data list in the Advanced<br>settings view of tSybaseBulkExec. |
| Database | Database name |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Sybase Schema | Name of the database schema you want to use. |
| Bcp Utility | Name of the utility to be used to copy data over to the Sybase<br>server. |
| Server | IP address of the database server for the Bcp utility<br>connection. |
| Batch size | Number of lines in each processed batch. |
| Table | Name of the table to be written. Note that only one table can be<br>written at a time and that the table must exist for the insert<br>operation to succeed. |
| Action on table | On the table defined, you can perform one of the following<br>operations:<br><br><br>None: No operation is carried<br>out.<br><br><br>Drop and create table: The table is<br>removed and created again.<br><br><br>Create table: The table does not<br>exist and gets created.<br><br><br>Create table if not exists: The<br>table is created if it does not exist.<br><br><br>Drop table if exists and create:<br>The table is removed if it already exists and created again.<br><br><br>Clear table: The table content is<br>deleted.<br><br><br>Truncate table: The table content<br>is deleted. You do not have the possibility to rollback the<br>operation. |
| File Name | Name of the file to be loaded.<br><br>Information noteWarning:<br><br>This file should be located on the same machine as the<br>database server. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use an interface file | Select this check box to specify an interface file in the field<br>Interface file. |
| Additional JDBC parameters | Specify additional connection properties in the existing DB<br>connection, to allow specific character set support. E.G.:<br>CHARSET=KANJISJIS\_OS to get support of Japanese characters. |
| Action on data | On the data of the table defined, you can perform:<br><br><br>Bulk Insert: Add multiple entries<br>to the table. If duplicates are found, Job stops.<br><br><br>Bulk Update: Make simultaneous<br>changes to multiple entries. |
| Field Terminator | Character, string or regular expression to separate fields.<br><br>Information noteWarning:<br><br><br>*With the row/field separators compliant<br>with the Sybase syntax, this component allows for the use of<br>Sybase-orientated characters, such as \x09.* |
| Row Terminator | String (ex: "\n" in Unix) to separate lines. |
| Head row | Number of head lines to be ignored in the beginning of a<br>file. |
| Encoding | Select the encoding from the list, or enter the encoding between double quotes<br>if it does not exist in the list. This field is compulsory for database data<br>handling. |
| Output | Select the type of output for the standard output of the Sybase<br>database:<br><br><br>to console,<br><br><br>to global variable. |
| tStataCatcher statistics | Select this check box to gather the Job processing metadata at a<br>Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE\_DATA: the number of rows read. This is an After variable and it<br>returns an integer.<br><br><br>NB\_LINE\_BAD: the number of rows rejected. This is an<br>After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is mainly used when no particular transformation is<br>required on the data to be loaded onto the database. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | The database server/client must be installed on the same<br>machine where Talend Studio is installed or where the Job using tSybaseBulkExec is deployed, so that the component functions<br>properly.<br><br>As opposed to the Oracle dedicated bulk component, no action on<br>data is possible using this Sybase dedicated component.<br><br>This component requires installation of its related jar files. |
