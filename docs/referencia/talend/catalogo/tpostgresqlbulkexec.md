# tpostgresqlbulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tpostgresqlbulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tpostgresqlbulkexec -->

# tPostgresqlBulkExec

Improves performance while carrying out the Insert operations to a Postgresql database.

The tPostgresqlBulkExec executes the Insert action on the data provided.

The tPostgresqlOutputBulk and tPostgresqlBulkExec components are used together to first output the file that will be then used as parameter to execute the SQL query stated. These two steps compose the tPostgresqlOutputBulkExec component, detailed in a separate section. The interest in having two separate elements lies in the fact that it allows transformations to be carried out before the data loading in the database.

## tPostgresqlBulkExec Standard properties

These properties are used to configure tPostgresqlBulkExec running in the Standard Job framework.

The Standard tPostgresqlBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | Either Built-in or<br>Repository<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| DB Version | Select the database version in the dropdown list. |
| Host | Enter the database server IP address. |
| Port | Listening port number of DB server. |
| Database | Enter the name of the database. |
| Schema | Enter the name of the PostgreSQL schema. |
| Username and Password | Enter the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | Enter the name of the table to be written. Note that only one table can be<br>written at a time and that the table must exist for the insert operation to<br>succeed. |
| Action on table | Select the operation to be performed on the defined table:<br><br><br>None: No operation is carried out.<br><br><br>Drop and create table: The table is<br>removed and created again.<br><br><br>Create table: The table does not exist<br>and gets created.<br><br><br>Create table if not exists: The table is<br>created if it does not exist.<br><br><br>Drop table if exists and create: The<br>table is removed if it already exists and created again.<br><br><br>Clear table: The table content is<br>deleted.<br><br><br>Truncate table: The table content is<br>deleted. You don not have the possibility to rollback the<br>operation. |
| File Name | Enter the name of the file to be loaded.<br><br>Information noteWarning: This file is located on the machine specified by the URI in the<br>Host field so it should be on the<br>same machine as the database server. |
| Schema and Edit Schema | A schema is a row description, it defines the number of fields to be<br>processed and passed on to the next component. The schema is either Built-in or stored remotely in the Repository<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul><br><br>This component supports PostgreSQL vector data types. Use the<br>VECTOR or Dynamic DB type in your schema<br>column definition to store and then query vector embeddings. For more information about<br>pgvector, read [the Amazon documentation](https://aws.amazon.com/about-aws/whats-new/2023/05/amazon-rds-postgresql-pgvector-ml-model-integration/). |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional JDBC parameters for the database connection created.<br><br>This property is not available when the Use an existing connection check box in the Basic<br>settings view is selected. |
| Action on data | Select the action to be performed on the table data:<br><br><ul> <li> <span>Bulk Insert</span>: Add multiple entries                           to the table. If duplicates are found, the Job stops.</li> <li> <p> <span>Bulk Update</span>: Make simultaneous                              changes to multiple entries.</p> </li> </ul> |
| Copy the OID for each row | Retrieve the ID item for each row. |
| Contains a header line with the names of each<br>column in the file | Specify that the table contains header. |
| Use local file for copy (for DB server 8.2 or newer) | (Enabled by default) Select this checkbox to copy files from the PostgreSQL<br>client machine. |
| Set encoding and Encoding | Select the option to set a specific encoding. Select the encoding standard<br>from the list, or select CUSTOM and define<br>it manually. |
| File type | Select the type of file being handled. |
| Null string | String displayed to indicate that the value is null. |
| Fields terminated by | Character, string, or regular expression to separate fields. |
| Escape char | Character of the row to be escaped. |
| Text enclosure | Character used to enclose text. |
| Activate standard\_conforming\_string | Activate the variable. |
| Force not null for columns | Define the columns nullability.<br><br><br>Force not null: Select the checkbox next<br>to the column you want to define as not null. |
| tStatCatcher Statistics | Select this checkbox to collect log data at the component<br>level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is to be used along with tPostgresqlOutputBulk component. Used together, they can offer<br>gains in performance while feeding a PostgreSQL database.<br><br>This component<br>supports PostgreSQL vector data types. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
