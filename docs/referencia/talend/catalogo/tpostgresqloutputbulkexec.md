# tpostgresqloutputbulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tpostgresqloutputbulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tpostgresqloutputbulkexec -->

# tPostgresqlOutputBulkExec

Improves performance during Insert operations to a Postgresql database.

The tPostgresqlOutputBulkExec executes the Insert action on the data provided.

The tPostgresqlOutputBulk and tPostgresqlBulkExec components are generally used together as part of a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT operation used to feed a database. These two steps are fused together in the tPostgresqlOutputBulkExec component.

## tPostgresqlOutputBulkExec Standard properties

These properties are used to configure tPostgresqlOutputBulkExec running in the Standard Job framework.

The Standard tPostgresqlOutputBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

This component supports PostgreSQL vector data types. Use the VECTOR or Dynamic DB type in your schema column definition to store and then query vector embeddings. For more information about pgvector, read [the Amazon documentation](https://aws.amazon.com/about-aws/whats-new/2023/05/amazon-rds-postgresql-pgvector-ml-model-integration/).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | Either Built-in or<br>Repository<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined. |
| DB Version | Select the database version in the dropdown list. |
| Host | Enter the database server IP address. |
| Port | Listening port number of DB server. |
| Database | Enter the name of the database. |
| Schema | Enter the name of the PostgreSQL schema. |
| Username and Password | Enter the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | Enter the name of the table to be written. Note that only one table can be<br>written at a time and that the table must exist for the insert operation to<br>succeed. |
| Action on table | Select the operation to be performed on the defined table:<br><br><br>None: No operation is carried out.<br><br><br>Drop and create table: The table is<br>removed and created again.<br><br><br>Create table: The table does not exist<br>and gets created.<br><br><br>Create table if not exists: The table is<br>created if it does not exist.<br><br><br>Drop table if exists and create: The<br>table is removed if already exists and created again.<br><br><br>Clear a table: The table content is<br>deleted. |
| File Name | Enter the name of the file to be generated and loaded.<br><br>Information noteWarning: This file is generated on the machine specified by the URI in<br>the Host field and it should be on the<br>same machine as the database server. |
| Schema and Edit Schema | A schema is a row description, it defines the number of fields to be<br>processed and passed on to the next component. The schema is either Built-in or stored remotely in the Repository.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul><br><br>This component supports PostgreSQL vector data types. Use the<br>VECTOR or Dynamic DB type in your schema<br>column definition to store and then query vector embeddings. For more information about<br>pgvector, read [the Amazon documentation](https://aws.amazon.com/about-aws/whats-new/2023/05/amazon-rds-postgresql-pgvector-ml-model-integration/). |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional JDBC parameters for the<br>database connection created. |
| Action on data | Select the action to be performed on the table data:<br><br><ul> <li> <span>Bulk Insert</span>: Add multiple entries                           to the table. If duplicates are found, the Job stops.</li> <li> <p> <span>Bulk Update</span>: Make simultaneous                              changes to multiple entries.</p> </li> </ul> |
| Copy the OID for each row | Retrieve the ID item for each row. |
| Contains a header line with the names of each<br>column in the file | Specify that the table contains header. |
| Use local file for copy (for DB server 8.2 or newer) | (Enabled by default) Select this check box to copy files from the PostgreSQL<br>client machine. |
| Encoding | Select the encoding standard from the list, or select CUSTOM and define it manually. This field is<br>compulsory for DB data handling. |
| File type | Select the type of file being handled. |
| Null string | String displayed to indicate that the value is null. |
| Row separator | String (ex: "\n"on Unix) to distinguish rows. |
| Fields terminated by | Character, string, or regular expression to separate fields. |
| Escape char | Character of the row to be escaped. |
| Text enclosure | Character used to enclose text. |
| Activate standard\_conforming\_string | Activate the variable. |
| Force not null for<br>columns | Define the column nullability.<br><br><br>Force not null: Select the checkbox next<br>to the column you want to define as not null. |
| tStatCatcher Statistics | Select this checkbox to collect log data at the component level. |
| Enable parallel execution | Select this check box to perform high-speed data processing, by treating<br>multiple data flows simultaneously. Note that this feature depends on the database or<br>the application ability to handle multiple inserts in parallel as well as the number of<br>CPU affected. In the Number of parallel executions<br>field, either:<br><br><ul> <li>Enter the number of parallel executions desired.</li> <li>Press <span>Ctrl+Space</span> and select               the appropriate context variable from the list. For further information about context               variables, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables" target="_blank">Using contexts and variables</a>. </li> </ul><br><br>Note that when parallel execution is enabled, it is not possible to use global<br>variables to retrieve return values in a subJob.<br><br><ul><li>						            The <span>Action on							table</span> field is not available with the							parallelization function. Therefore, you must use a <span>tCreateTable</span> component if you							want to create a table. 					          </li><li>						            When parallel execution is enabled, it is not							possible to use global variables to retrieve return values in a							subJob.					          </li> </ul> |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is mainly used when no particular transformation is required<br>on the data to be loaded onto the database.<br><br>This component supports PostgreSQL<br>vector data types. |
| Limitation | The database server must be installed on the same machine where Talend Studio<br>is installed or where the Job using tPostgresqlOutputBulkExec is deployed, so that the component<br>functions correctly. |
