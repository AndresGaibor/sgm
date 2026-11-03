# toraclebulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/toraclebulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/toraclebulkexec -->

# tOracleBulkExec

Offers gains in performance during operations performed on data of an Oracle database.

tOracleBulkExec inserts, appends, replaces or truncate data in an Oracle database.

The tOracleOutputBulk and tOracleBulkExec components are used together in a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT operation used to feed a database. These two steps are fused together in the tOracleOutputBulkExec component, detailed in a separate section. The advantage of using two separate steps is that the data can be transformed before it is loaded in the database.

## tOracleBulkExec Standard properties

These properties are used to configure tOracleBulkExec running in the Standard Job framework.

The Standard tOracleBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: The database server/client must be installed on the same machine where Talend Studio is installed or where the Job using tOracleBulkExec is deployed, so that the component functions properly.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p>Either <span>Built-in</span> or <span>Repository</span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Note that connections that are of<br>WALLET type are for the tCreateTable component, the tOracleInput<br>component, and the tOracleOutput component only. Make sure that the connection selected is<br>not of the WALLET type to prevent possible errors.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Connection type | Drop-down list of available drivers:<br><br><br>Oracle OCI: Select this connection<br>type to use Oracle Call Interface with a set of C-language software<br>APIs that provide an interface to the Oracle database.<br><br><br>Oracle Service Name: Select this<br>connection type to use the TNS alias that you give when you connect<br>to the remote database.<br><br><br>Oracle SID: Select this connection<br>type to uniquely identify a particular database on a system.<br><br><br>Oracle Custom: Select this<br>connection type to access a clustered database. |
| DB Version | Select the Oracle version in use. |
| Host | IP address of the database server. |
| Port | Port number listening the database server. |
| Database | Database name. |
| Schema | Schema name. |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | Name of the table to be written. Note that only one table can be<br>written at a time. |
| Action on table | On the table defined, you can perform one of the following<br>operations:<br><br><br>None: No operation is carried<br>out.<br><br><br>Drop and create table: The table is<br>removed and created again.<br><br><br>Create table: The table does not<br>exist and gets created.<br><br><br>Create table if not exists: The<br>table is created if it does not exist.<br><br><br>Drop table if exists and create:<br>The table is removed if it already exists and created again.<br><br><br>Clear table: The table content is<br>deleted.<br><br><br>Truncate table: The table content<br>is deleted. You do not have the possibility to rollback the<br>operation. |
| Data file name | Name of the file to be loaded.<br><br>Information noteWarning: This file should be located on the same<br>machine as the Talend JobServer. |
| Action on data | On the data of the table defined, you can perform:<br><br><br>Insert: Insert data to an empty table.<br>If the table already contains data, the Job stops and the existing data<br>remains in the table.<br><br><br>Update: Update the existing data. You<br>have to set the key on the schema if this option is selected.<br><br><br>Append:<br>Append data to the table, whether the table is empty or not.<br><br><br>Replace:<br>if the table already contains data, delete all the existing data and insert the new<br>data. If the table is empty, insert the new data.<br><br><br>Truncate: If the table already contains<br>data, truncate all the existing data and insert the new data. If the<br>table is empty, insert the new data. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description, it defines the number of fields to								be processed and passed on to the next component. The schema is								either <span>Built-in</span> or stored remotely								in the <span>Repository</span>.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Advanced separator (for number) | Select this check box to change the separator used for the<br>numbers. |
| Use existing control file | Select this check box if you use a control file (.ctl) and specify<br>its path in the .ctl file name<br>field. |
| Record format | Define the record format:<br><br><br>Default: format parameters are set<br>by default.<br><br><br>Stream: set Record terminator.<br><br><br>Fixed: set the Record length.<br><br><br>Variable: set the Field size of the record length. |
| Specify .ctl file's INTO TABLE clause manually | Select this check box to manually fill in the INTO TABLE clause of the control file. |
| Fields terminated by | Character, string or regular expression to separate fields:<br><br><br>None: no separator is used.<br><br><br>Whitespace: the separator used is a<br>space.<br><br><br>EOF (used for loading LOBs from<br>lobfile): the separator used is an EOF character (End<br>Of File).<br><br><br>Other terminator: Set another<br>terminator in the Field terminator<br>field. |
| Use fields enclosure | Select this check box if you want to use enclosing characters for<br>the text:<br><br><br>Fields enclosure (left part):<br>character delimiting the left of the field.<br><br><br>Field enclosure (right part):<br>character delimiting the right of the field. |
| Use schema's Date Pattern to load Date field | Select this check box to use the date pattern of the schema in the<br>date field. |
| Specify field condition | Select this check box to define data loading condition. |
| Preserve blanks | Select this check box to preserve the blanks. |
| Trailing null columns | Select this check box to load null columns. |
| Load options | Click + to add data loading<br>options:<br><br><br>Parameter: select a loading<br>parameter from the list.<br><br><br>Value: enter a value for the<br>parameter selected. |
| NLS Language | In the list, select the language used for the data that are not<br>used in Unicode. |
| Set Parameter NLS\_TERRITORY | Select this check box to modify the territory conventions used for<br>day and weeks numbering. Your OS value is the default value<br>used. |
| Encoding | Select the encoding from the list, or enter the encoding between double quotes<br>if it does not exist in the list. This field is compulsory for database data<br>handling. |
| Output | Select the type of output for the standard output of the Oracle<br>database:<br><br><br>to console,<br><br><br>to global variable. |
| Convert columns and table names to uppercase | Select this check box to uppercase the names of the columns and<br>the name of the table. |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level. |
| Support NLS | Select this option to enable globalization support. See [Overview of Globalization Support](https://docs.oracle.com/en/database/oracle/oracle-database/21/nlspg/overview-of-globalization-support.html) for<br>related information.<br><br>This option is available when the Use an existing<br>connection option is cleared and Oracle 18 and<br>above is selected from the DB Version<br>drop-down list in the Basic settings view.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-09<br>Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE\_DATA: the number of rows read. This is an After variable and it<br>returns an integer.<br><br><br>NB\_LINE\_BAD: the number of rows rejected. This is an<br>After variable and it returns an integer.<br><br><br>NB\_LINE\_INSERTED: the number of<br>rows inserted. This is an After variable and it returns an integer.<br><br><br>RETURN\_CODE: the return code indicating<br>the result of processing. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This dedicated component offers performance and flexibility of<br>Oracle DB query handling. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |

**Related concepts**

* [Truncating and inserting file data into an Oracle database](https://help.qlik.com/talend/en-US/components/8.0/toracleinput-toraclebulkexec-tfileoutputdelimited-toraclebulkexec-tfileoutputdelimited-truncating-and-inserting-file-data-into-oracle-database-standard-component-this)
