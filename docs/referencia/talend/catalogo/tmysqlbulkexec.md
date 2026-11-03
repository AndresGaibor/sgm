# tmysqlbulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tmysqlbulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmysqlbulkexec -->

# tMysqlBulkExec

Offers gains in performance while executing the Insert operations on a MySQL or Aurora database.

The tMysqlOutputBulk and tMysqlBulkExec components are used together in a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT statement used to feed a database. These two steps are fused together in the tMysqlOutputBulkExec component, detailed in a separate section. The advantage of using two separate steps is that the data can be transformed before it is loaded in the database.

## tMysqlBulkExec Standard Properties

These properties are used to configure tMysqlBulkExec running in the Standard Job framework.

The Standard tMysqlBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| DB Version | Select the version of the database that you are using. |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Host | Database server IP address |
| Port | Listening port number of DB server. |
| Database | Name of the database |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Action on table | On the table defined, you can perform one of the following<br>operations:<br><br><br>None: No operation is carried<br>out.<br><br><br>Drop and create table: The table is<br>removed and created again.<br><br><br>Create table: The table does not<br>exist and gets created.<br><br><br>Create table if not exists: The<br>table is created if it does not exist.<br><br><br>Drop table if exists and create:<br>The table is removed if it already exists and created again.<br><br><br>Clear table: The table content is<br>deleted. You have the possibility to rollback the operation.<br><br><br>Truncate table: The table content<br>is deleted. You do not have the possibility to rollback the<br>operation. |
| Table | Name of the table to be written. Note that only one table can be<br>written at a time and that the table must exist for the insert<br>operation to succeed. |
| Local file Name | Name of the file to be loaded.<br><br>This file should be located on the same machine where Talend Studio is installed or where the Job using tMysqlBulkExec is deployed. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description, it defines the number of fields to								be processed and passed on to the next component. The schema is								either <span>Built-in</span> or stored remotely								in the <span>Repository</span>. </p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC parameters | Specify additional connection properties for the DB connection you<br>are creating. This option is not available if you have selected the<br>Use an existing connection<br>check box in the Basic<br>settings. |
| Lines terminated by | Character or sequence of characters used to separate lines. |
| Fields terminated by | Character, string or regular expression to separate fields. |
| Enclosed by | Character used to enclose text. |
| Action on data | On the data of the table defined, you can perform:<br><br><br>Insert records in table: Add new<br>records to the table.<br><br><br>Update records in table: Make<br>changes to existing records.<br><br><br>Replace records in table: Replace<br>existing records with new ones. Ignore records<br>in table: Ignore the existing records, or insert the<br>new ones. |
| Records contain NULL value | Check this box if you want to retrieve the null values from the<br>input data flow. If you do not check this box, the null values from<br>the input data flow will be considered as empty fields in the output<br>data flow. |
| Encoding | Select the encoding from the list or select Custom and define it manually. This field is<br>compulsory for DB data handling. |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is to be used along with tMysqlOutputBulk component. Used together, they<br>can offer gains in performance while feeding a MySQL or Aurora database. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |

**Related concepts**

* [Inserting transformed data in MySQL database](https://help.qlik.com/talend/en-US/components/8.0/tmysqlbulkexec-tmysqloutputbulk-tmap-inserting-transformed-data-in-mysql-database-standard-component-this)
