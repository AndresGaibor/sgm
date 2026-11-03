# tverticaoutputbulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tverticaoutputbulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tverticaoutputbulkexec -->

# tVerticaOutputBulkExec

Receives data from a preceding component, writes data into a local file, and loads data into a Vertica database from the file using the Vertica COPY SQL statement.

## tVerticaOutputBulkExec Standard properties

These properties are used to configure tVerticaOutputBulkExec running in the Standard Job framework.

The Standard tVerticaOutputBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property Type | Select the way the connection details<br>will be set.<br><br><ul> <li> <p> <span>Built-In</span>: The connection details will be set                                locally for this component. You need to specify the values for all                                related connection properties manually.</p> </li> <li> <p> <span>Repository</span>: The connection details stored                                centrally in <span><span>Repository</span><abbr> &gt; </abbr><span>Metadata</span></span> will be reused by this component. </p> <p>You need to click                                the <span>[...]</span> button next to it and in the pop-up                                    <span>Repository Content</span> dialog box, select the                                connection details to be reused, and all related connection                                properties will be automatically filled in.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>When a Job contains the parent Job and the child Job, if you need to<br>share an existing connection between the two levels, for example, to share the<br>connection created by the parent Job with the child Job, you have to:<br><br><ol> <li> <p>In the parent level, register the database connection to be shared                in the <span>Basic settings</span> view of the connection                component which creates that very database connection.</p> </li> <li> <p>In the child level, use a dedicated connection component to read                that registered database connection.</p> </li> </ol><br><br>For an example about how to share a database connection across Job levels, see<br>[Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Host | Enter the IP address or hostname of the database. |
| Port | Enter the listening port number of the database. |
| DB Name | Enter the name of the database. |
| Schema | Enter the schema of the database. |
| Username and Password | Enter the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Action on data | Select an action that will be performed on the data of the table defined.<br><br><ul> <li> <p> <span>Bulk insert</span>: Insert multiple rows into the table at once                instead of doing single row inserts. If duplicates are found, the Job stops.</p> </li> <li> <p> <span>Bulk update</span>: Make simultaneous updates to multiple rows.</p> </li> </ul> |
| Table | Enter the name of the table into<br>which data will be written. |
| Action on table | Select an operation to be performed on the table defined.<br><br><ul> <li> <p> <span>Default</span>: No operation is carried out.</p> </li> <li> <p> <span>Drop and create table</span>: The table is removed            and created again.</p> </li> <li> <p> <span>Create table</span>: The table does not exist and            gets created.</p> </li> <li> <p> <span>Create table if does not exist</span>: The table is            created if it does not exist.</p> </li> <li> <p> <span>Drop table if exist and create</span>: The table is            removed if it already exists and created again.</p> </li> <li> <p> <span>Clear table</span>: The table content is            deleted. You have the possibility to rollback the operation.</p> </li> </ul> |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>When the schema to be reused has default values that are<br>integers or functions, ensure that these default values are not enclosed within<br>quotation marks. If they are, you must remove the quotation marks manually.<br><br>For more information, see [Retrieving table schemas](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg).<br><br>Click Edit schema to make changes to<br>the schema. If you make changes, the schema automatically becomes built-in.<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| File Name | The path to the file to be generated.<br><br>This file is generated on the same machine where Talend Studio<br>is installed or where your Job using this component is deployed. |
| Append | Select this check box to add new rows at the end of the file. |
| Use schema columns for Copy | Select this check box to use the column option in the COPY statement so that you<br>can restrict the load to one or more specified columns in the table. For more<br>information, see [the Vertica COPY SQL Statement](https://my.vertica.com/docs/9.0.x/HTML/index.htm#Authoring/SQLReferenceManual/Statements/COPY/COPY.htm). |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional JDBC parameters for the database connection created.<br><br>This property is not available when the Use an existing connection check box in the Basic<br>settings view is selected. |
| Stream name | The stream name of a load, which helps identify a particular load.<br><br>This property is available only when<br>you are using Vertica 6.0 and later. |
| Write to ROS (Read Optimized Store) | Select this check box to store data in a physical storage area, in order to optimize<br>the reading, as the data is compressed and pre-sorted. |
| Exit Job if no row was loaded | The Job automatically stops if no row has<br>been loaded. |
| Missing columns as null | Select this check box to insert NULL values for the missing columns when there is<br>insufficient data to match the columns specified in the schema.<br><br>This property is available only when<br>you are using Vertica 6.0 and later. |
| Skip Header | Select this check box and in the field displayed next to it, specify the number of<br>records to skip in the file.<br><br>This property is available only when<br>you are using Vertica 6.0 and later. |
| Record terminator | Select this check box and in the field displayed next to it, specify the literal<br>character string used to indicate the end of each record in the file.<br><br>This property is available only when<br>you are using Vertica 6.0 and later. |
| Enclosed by character | Select this check box to set the character within which data is enclosed.<br><br>This property is available only when<br>you are using Vertica 6.0 and later. |
| Field Separator | The character, string or regular expression to<br>separate fields. |
| Null String | The string displayed to indicate that the value is null. |
| Include Header | Select the check box to include the column header to the file. |
| Encoding | Select an encoding method from the list, or select<br>CUSTOM and define it manually. This field is<br>compulsory for database data handling. |
| Reject not fitted values | Select this check box to reject data rows of type char, varchar, binary, and varbinary<br>if they do not fit the target table.<br><br>This property is available only when<br>you are using Vertica 6.0 and later. |
| Maximum number of rejected records | Select this check box and in the field displayed next to it, specify the maximum number<br>of records that can be rejected before a load fails.<br><br>This property is available only when<br>you are using Vertica 6.0 and later. |
| Stop and rollback if any row is rejected | Select this check box to stop and roll back a load without loading any data if any row<br>is rejected.<br><br>This property is available only when<br>you are using Vertica 6.0 and later. |
| Don't commit | Select this check box to perform a bulk load transaction without committing the results<br>automatically. This is useful if you want to execute multiple bulk loads in a single<br>transaction.<br><br>This property is available only when<br>you are using Vertica 6.0 and later. |
| Rejected data file | Specify the file into which rejected rows will be written.<br><br>This property is available only when<br>Bulk insert is selected from the Action on<br>data drop-down list. |
| Exception log file | Specify the file into which the exception log will be written. This log explains why<br>each rejected row was rejected.<br><br>This property is available only when<br>Bulk insert is selected from the Action on<br>data drop-down list. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| ACCEPTED\_ROW\_NUMBER | The number of rows loaded into the database. This is an After<br>variable and it returns an integer. |
| REJECTED\_ROW\_NUMBER | The number of rows rejected. This is an After variable and<br>it returns an integer. |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is mainly used when no particular transformation<br>is required on the data to be loaded into the database.<br><br><br>Talend Studio and the<br>Vertica database create very fast and affordable data warehouse and data mart applications.<br>For more information about how to configure *Talend Studio* to connect to Vertica, see [Talend and HP Vertica Tips and<br>Techniques](https://www.vertica.com/kb/Vertica-Integration-with-Talend-Connection-Guide/Content/Partner/Vertica-Integration-with-Talend-Connection-Guide.htm). |
