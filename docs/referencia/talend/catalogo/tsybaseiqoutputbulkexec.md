# tsybaseiqoutputbulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsybaseiqoutputbulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsybaseiqoutputbulkexec -->

# tSybaseIQOutputBulkExec

Information noteImportant: Support for Sybase 12 through 15 is removed from 8.0.1-R2024-12 onwards. Use Sybase 16 instead.

Gains in performance during Insert operations to a Sybase IQ database.

tSybaseIQOutputBulkExec executes the Insert action on the data provided.

## tSybaseIQOutputBulkExec Standard properties

These properties are used to configure tSybaseIQOutputBulkExec running in the Standard Job framework.

The Standard tSybaseIQOutputBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property Type | Select the way the connection details<br>will be set.<br><br><ul> <li> <p> <span>Built-In</span>: The connection details will be set                                locally for this component. You need to specify the values for all                                related connection properties manually.</p> </li> <li> <p> <span>Repository</span>: The connection details stored                                centrally in <span><span>Repository</span><abbr> &gt; </abbr><span>Metadata</span></span> will be reused by this component. </p> <p>You need to click                                the <span>[...]</span> button next to it and in the pop-up                                    <span>Repository Content</span> dialog box, select the                                connection details to be reused, and all related connection                                properties will be automatically filled in.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>When reusing an existing Sybase 16 (SQL<br>Anywhere) connection created by a tSybaseConnection component and loading data from a file<br>located on the client side, you need to select Sybase 16 (SQL Anywhere) from the DB<br>Version drop-down list to display the Is client file<br>check box before selecting this check box.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection).<br><br>This property is not available when<br>Sybase IQ 15 is selected from the DB<br>Version drop-down list. |
| DB Version | Select the version of the Sybase database to be used from the<br>drop-down list.<br><br><ul> <li> <p>For Sybase IQ 12 and Sybase IQ 16, the file to be bulk-loaded must be located on                the same machine as the Sybase IQ server.</p> </li> <li> <p>For Sybase IQ 15, the file to be bulk-loaded can be located on the client side,                however, this means certain setup on the Sybase IQ server. For more information, see                  <a href="http://infocenter.sybase.com/help/index.jsp?topic=/com.sybase.infocenter.dc00787.0480/html/etl_nfg/CHDEIAJG.htm" target="_blank">Sybase IQ client-side load support                  enhancements</a>.</p> </li> <li> <p>For Sybase 16 (SQL Anywhere), the file to be bulk-loaded can be located on both the                server side and the client side.</p> <p>Before loading data into Sybase 16 (SQL Anywhere), SQL Anywhere 17 must be                        installed. You can download it <a href="https://archive.sap.com/documents/docs/DOC-35857" target="_blank">here</a>. Once the installation is done, you need to check the system                        variable <kbd>Path</kbd> to make sure the installation path of                        SQL Anywhere 17 has been added to it, and then restart <span>Talend Studio</span> (in certain case restart the computer) to have the new                           <kbd>Path</kbd> variable take effect.</p> </li> </ul> |
| Host | The IP address or hostname of the database.<br><br>This property is not available when<br>Sybase IQ 15 is selected from the DB<br>Version drop-down list. |
| Port | The listening port number of the database.<br><br>This property is not available when<br>Sybase IQ 15 is selected from the DB<br>Version drop-down list. |
| Data Source | Select the type of the data source to be used and complete the corresponding DSN<br>information in the field alongside. The available types are DSN<br>and FILEDSN.<br><br>When FILEDSN is selected, a [...] button<br>is available next to the Data Source field to allow you to browse<br>to the data source file of interest.<br><br>This property is available when Sybase IQ 15 is selected from<br>the DB Version drop-down list. |
| Database | Enter the name of the database. |
| Sybase Schema | The schema of the database. |
| Username and Password | Enter the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | The name of the table to be written. |
| Action on table | On the table defined, you can perform one of the<br>following operations:<br><br><ul> <li> <p> <span>Default</span>: No operation is									carried out.</p> </li> <li> <p> <span>Drop and create table</span>:									The table is removed and created again.</p> </li> <li> <p> <span>Create table</span>: The table									does not exist and gets created.</p> </li> <li> <p> <span>Create table if does not										exist</span>: The table is created if it does not									exist.</p> </li> <li> <p> <span>Drop table if exists and										create</span>: The table is removed if it already									exists and created again.</p> </li> <li> <p> <span>Clear table</span>: The table									content is deleted.</p> </li> </ul> |
| Filename | Enter the name of the file to be generated and loaded. |
| Is client file | Select this check box if you need to load data from the client side.<br><br>This property is available when<br>Sybase 16 (SQL Anywhere) is selected from the DB<br>Version drop-down list. |
| Append the file | Select this check box to add the new rows at the end of<br>the records. |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>When the schema to be reused has default values that are<br>integers or functions, ensure that these default values are not enclosed within<br>quotation marks. If they are, you must remove the quotation marks manually.<br><br>For more information, see [Retrieving table schemas](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg).<br><br>Click Edit schema to make changes to<br>the schema. If you make changes, the schema automatically becomes built-in.<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional connection properties in the existing<br>DB connection, to allow specific character set support. |
| Fields terminated by | Enter the character, string or regular expression used to<br>separate fields.<br><br>Information noteWarning:<br><br>As a combination of tSybaseOutputBulk and tSybaseIQBulkExec, this component does not allow<br>the use of Sybase-oriented row/field separators, such as \x09. To<br>achieve the desired effect (for example, displaying fields in the<br>tabular form), you need to use tSybaseOutputBulk and tSybaseIQBulkExec together to replace tSybaseIQOutputBulkExec, with \t<br>used in the former component and \x09 used in the latter. |
| Lines terminated by | Enter the character or sequence of characters used to<br>separate lines. |
| Use enclosed quotes | Select this check box to use data enclosure<br>characters. |
| Include Head | Select this heck box to include the column header. |
| Blank as null | Select this check box to store the input zero-length<br>varchars as NULLs instead of blanks in the database during the load<br>operation. |
| On file error | Select the action Sybase performs when an error occurs:<br><br><ul> <li> <p> <span>Rollback (default)</span>: rolls back the entire transaction.</p> </li> <li> <p> <span>Finish</span>: finishes the insertions already completed and ends                the load operation.</p> </li> <li> <p> <span>Continue</span>: skips the error and continues the load                operation.</p> </li> </ul><br><br>This property is available when<br>Sybase 16 (SQL Anywhere) is selected from the DB<br>Version drop-down list. |
| Message log file | The path to the MESSAGE LOG file that saves the log information about<br>integrity constraint violations, the types of violations, etc. It must be specified<br>together with the Row log file property.<br><br>This property is available when<br>Sybase 16 (SQL Anywhere) is selected from the DB<br>Version drop-down list. |
| Row log file | The path to the ROW LOG file that saves the log information about reject data, the<br>timestamps of the start and completion of the load, etc. It must be specified together<br>with the Message log file property.<br><br>This property is available when<br>Sybase 16 (SQL Anywhere) is selected from the DB<br>Version drop-down list. |
| Encoding | Select the encoding type from the list or select<br>Custom and define it<br>manually. This field is compulsory for DB data handling. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| **Usage rule** | This component is mainly used when no particular<br>transformation is required on the data to be loaded onto the database. |

**Related concepts**

* [Bulk-loading data to a Sybase IQ 12 database](https://help.qlik.com/talend/en-US/components/8.0/tsybaseiqoutputbulkexec-trowgenerator-bulk-loading-data-to-sybase-iq-12-database-standard-component-this)
