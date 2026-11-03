# tmysqloutputbulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tmysqloutputbulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmysqloutputbulkexec -->

# tMysqlOutputBulkExec

Executes the Insert action in the specified MySQL or Aurora database.

As a dedicated component, tMysqlBulkExec improves performance when performing Insert operations to a MySQL or Aurora database.

The tMysqlOutputBulk and tMysqlBulkExec components are used together in a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT statement used to feed a database. These two steps are fused together in the tMysqlOutputBulkExec component.

## tMysqlOutputBulkExec Standard properties

These properties are used to configure tMysqlOutputBulkExec running in the Standard Job framework.

The Standard tMysqlOutputBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| DB Version | Select the version of the database that you are using. |
| Host | Database server IP address |
| Port | Listening port number of DB server. |
| Database | Name of the database |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Action on table | On the table defined, you can perform one of the following<br>operations:<br><br><br>None: No operation is carried<br>out.<br><br><br>Drop and create table: The table is<br>removed and created again.<br><br><br>Create table: The table does not<br>exist and gets created.<br><br><br>Create table if not exists: The<br>table is created if it does not already exist.<br><br><br>Drop table if exists and create:<br>The table is removed if it already exists and created again.<br><br><br>Clear table: The table content is<br>deleted. |
| Table | Name of the table to be written.<br><br>Information noteNote:<br><br>Note that only one table can be written at a time and that the<br>table must already exist for the insert operation to<br>succeed |
| Local FileName | Name of the file to be generated and loaded.<br><br>This file is generated on the same machine where Talend Studio is installed or where the Job using tMysqlOutputBulkExec is deployed. Then it is loaded to the<br>database specified by Host field. |
| Append | Select the check box for this option to append new rows to the end<br>of the file. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description, it defines the number of fields to								be processed and passed on to the next component. The schema is								either <span>Built-in</span> or stored remotely								in the <span>Repository</span>. </p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC parameters | Specify additional connection properties for the DB connection you<br>are creating. This option is not available if you have selected the<br>Use an existing connection<br>check box in the Basic<br>settings.<br><br>Information noteNote:<br><br>You can press Ctrl+Space to<br>access a list of predefined global variables. |
| Row separator | String (ex: "\n"on Unix) to distinguish rows. |
| Field separator | Character, string or regular expression to separate fields. |
| Escape char | Character of the row to be escaped |
| Text enclosure | Character used to enclose the text. |
| Create directory if does not exist | This check box is selected by default. It creates a directory to<br>hold the output table if required. |
| Custom the flush buffer size | Customize the amount of memory used to temporarily store output<br>data. In the Row number field,<br>enter the number of rows after which the memory is to be freed<br>again. |
| Action on data | On the data of the table defined, you can carry out the following<br>opertaions:<br><br><br>Insert records in table: Add new<br>records to the table.<br><br><br>Update records in table: Make<br>changes to existing records.<br><br><br>Replace records in table: Replace<br>existing records with new one. Ignore records<br>in table: Ignore existing records or insert the new<br>ones. |
| Records contain NULL value | This check box is selected by default. It allows you to take<br>account of NULL value fields. If you clear the check box, the NULL<br>values will automatically be replaced with empty values. |
| Encoding | Select the encoding from the list or select Custom and define it manually. This field is<br>compulsory for DB data handling. |
| tStatCatcher Statistics | Select this check box to collect the log data at the component<br>level. |
| Enable parallel execution | Select this check box to perform high-speed data processing, by treating<br>multiple data flows simultaneously. Note that this feature depends on the database or<br>the application ability to handle multiple inserts in parallel as well as the number of<br>CPU affected. In the Number of parallel executions<br>field, either:<br><br><ul> <li>Enter the number of parallel executions desired.</li> <li>Press <span>Ctrl+Space</span> and select               the appropriate context variable from the list. For further information about context               variables, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables" target="_blank">Using contexts and variables</a>. </li> </ul><br><br><ul><li>						            The <span>Action on							table</span> field is not available with the							parallelization function. Therefore, you must use a <span>tCreateTable</span> component if you							want to create a table. 					          </li><li>						            When parallel execution is enabled, it is not							possible to use global variables to retrieve return values in a							subJob.					          </li> </ul> |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is mainly used when no particular transformation is<br>required on the data to be loaded onto the database. |

**Related concepts**

* [Inserting data in bulk in MySQL database](https://help.qlik.com/talend/en-US/components/8.0/tmysqloutputbulkexec-trowgenerator-inserting-data-in-bulk-in-mysql-database-standard-component-this)
* [Inserting transformed data in MySQL database](https://help.qlik.com/talend/en-US/components/8.0/tmysqlbulkexec-tmysqloutputbulk-tmap-inserting-transformed-data-in-mysql-database-standard-component-this)
