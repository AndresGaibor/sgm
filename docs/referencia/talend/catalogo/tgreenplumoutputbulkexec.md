# tgreenplumoutputbulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tgreenplumoutputbulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tgreenplumoutputbulkexec -->

# tGreenplumOutputBulkExec

Provides performance gains during Insert operations to a Greenplum database.

The tGreenplumOutputBulk and tGreenplumBulkExec components are used together in a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT operation used to feed a database. These two steps are fused together in the tGreenplumOutputBulkExec component.

tGreenplumOutputBulkExec executes the action on the data provided.

## tGreenplumOutputBulkExec Standard properties

These properties are used to configure tGreenplumOutputBulkExec running in the Standard Job framework.

The Standard tGreenplumOutputBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Host | Database server IP address.<br><br>Currently, only *localhost*, *127.0.0.1* or the exact IP address of the local machine<br>is allowed for proper functioning. In other words, the database server must be<br>installed on the same machine where Talend Studio is installed or where the Job using tGreenplumOutputBulkExec is deployed. |
| Port | Listening port number of DB server. |
| Database name | Name of the database. |
| Schema | Exact name of the schema. |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | Name of the table to be written.<br><br>Note that only one table can be written at a time and that the<br>table must exist for the insert operation to succeed. |
| Action on table | On the table defined, you can perform one of the following<br>operations:<br><br><br>None: No operation is carried<br>out.<br><br><br>Drop and create a table: The table<br>is removed and created again.<br><br><br>Create a table: The table does not<br>exist and gets created.<br><br><br>Create a table if not exists: The<br>table is created if it does not exist.<br><br><br>Drop table if exists and create:<br>The table is removed if it already exists and created again.<br><br><br>Clear a table: The table content is<br>deleted. You have the possibility to rollback the operation. |
| File Name | Name of the file to be generated and loaded.<br><br>Information noteWarning:<br><br>This file is generated on the machine specified by the URI in<br>the Host field so it should be<br>on the same machine as the database server. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional JDBC parameters for the<br>database connection created. |
| DB driver | Select a database driver from the drop-down list: PostgreSQL,<br>Greenplum(Deprecated), or DataDirect.<br>The default is PostgreSQL.<br><br>Information noteImportant: The Greenplum(Deprecated) driver is deprecated.<br>Migrate to DataDirect, a third-party JDBC driver suggested by<br>Greenplum. |
| Action on data | Select the operation you want to perform:<br><br><br>Bulk insert<br>Bulk update The details asked will be different<br>according to the action chosen. |
| Copy the OID for each row | Retrieve the ID item for each row. |
| Contains a header line with the names of each column in<br>the file | Specify that the table contains header. |
| File type | Select the file type to process. |
| Null string | String displayed to indicate that the value is null. |
| Row separator | String (ex: "\n"on Unix) to distinguish rows. |
| Fields terminated by | Character, string or regular expression to separate fields. |
| Escape char | Character of the row to be escaped |
| Text enclosure | Character used to enclose text. |
| Force not null for columns | Define the columns nullability<br><br><br>Force not null: Select the check<br>box next to the column you want to define as not null. |
| tStatCatcherStatistics | Select this check box to collect log data at the component<br>level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is mainly used when no particular transformation is<br>required on the data to be loaded onto the database. |
| Limitation | The database server must be installed on the same machine where<br>Talend Studio is installed or where the Job using tGreenplumOutputBulkExec is deployed, so that the component<br>functions properly. |
