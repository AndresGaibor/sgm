# tsybaseoutputbulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsybaseoutputbulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsybaseoutputbulkexec -->

# tSybaseOutputBulkExec

Gains in performance during Insert operations to a Sybase database.

The tSybaseOutputBulk and tSybaseBulkExec components are generally used together as parts of a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT operation used to feed a database. These two steps are fused together in the tSybaseOutputBulkExec component.

## tSybaseOutputBulkExec Standard properties

These properties are used to configure tSybaseOutputBulkExec running in the Standard Job framework.

The Standard tSybaseOutputBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p>Either<span> Built-in</span> or								<span>Repository</span>. </p> </li> <li> <p> <span>Built-in</span>: No property data stored							centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository							file in which the properties are stored. The fields that follow are							completed automatically using the data retrieved.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| DB Version | Select the version of the Sybase database to be used from the<br>drop-down list. |
| Server | Database server IP address<br><br>Currently, only *localhost*, *127.0.0.1* or the exact IP address of the local machine<br>is allowed for proper functioning. In other words, the database server must be<br>installed on the same machine where Talend Studio is installed or where the Job using tSybaseOutputBulkExec is deployed. |
| Port | Listening port number of DB server. |
| Database | Name of the database |
| Username and Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Bcp utility | Name of the utility to be used to copy data over to the<br>Sybase server. |
| Batch row number | Number of lines in each processed batch. |
| Table | Name of the table to be written. Note that only one table<br>can be written at a time and that the table must exist for the insert<br>operation to succeed. |
| Action on table | On the table defined, you can perform one of the<br>following operations:<br><br><br>None: No operation is carried<br>out.<br><br><br>Drop and create a table: The<br>table is removed and created again.<br><br><br>Create a table: The table does<br>not exist and gets created.<br><br><br>Create a table if not exists: The<br>table is created if it does not exist.<br><br><br>Clear a table: The table content<br>is deleted. |
| File Name | Name of the file to be generated and loaded.<br><br>Information noteWarning:<br><br>This file is generated on the machine specified by<br>the URI in the Server field<br>so it should be on the same machine as the database server. |
| Append | Select this check box to add the new rows at the end of<br>the records. |
| Schema and Edit Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use an interface file | Select this check box to specify an interface file in the field<br>Interface file. |
| Additional JDBC parameters | Specify additional connection properties in the existing DB<br>connection, to allow specific character set support. E.G.:<br>CHARSET=KANJISJIS\_OS to get support of Japanese characters. |
| Action on data | On the data of the table defined, you can perform:<br><br><br>Bulk Insert: Add multiple entries<br>to the table. If duplicates are found, job stops.<br><br><br>Bulk Update: Make simultaneous<br>changes to multiple entries. |
| Field terminator | Character, string or regular expression to separate fields.<br><br>Information noteWarning:<br><br><br>*As a combination of tSybaseOutputBulk and tSybaseBulkExec, this component<br>does not allow the use of Sybase-oriented row/field<br>separators, such as \x09. To achieve the desired effect (for<br>example, displaying fields in the tabular form), you need to<br>use tSybaseOutputBulk and<br>tSybaseBulkExec<br>together to replace tSybaseOutputBulkExec, with \t used in the<br>former component and \x09 used in the latter.* |
| DB Row terminator | String (ex: "\n"on Unix) to distinguish rows in the DB. |
| First row NO. of file | Type in the number of the file row where the action should start<br>at. |
| FILE Row terminator | Character, string or regular expression to separate fields in a<br>file. |
| Include Head | Select this heck box to include the column header. |
| Encoding | Regarding the source data, select the appropriate encoding from<br>the list or select Custom and<br>define it manually. This field is compulsory for DB data<br>handling. |
| Sybase encoding type | Select the Sybase-specific encoding type for the data to be<br>processed. This encoding type allows tSybaseOutputBulkExec to properly generate the<br>Sybase Bulk command. |
| Output | Select the type of output for the standard output of the Sybase<br>database:<br><br><br>to console,<br><br><br>to global variable. |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is mainly used when no particular transformation is<br>required on the data to be loaded onto the database. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | This component requires installation of its related jar files.<br><br>The database server/client must be installed on the same<br>machine where Talend Studio is installed or where the Job using tSybaseOutputBulkExec is deployed, so that the component<br>functions properly. |
