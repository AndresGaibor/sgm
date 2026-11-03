# tingresoutputbulkexec

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tingresoutputbulkexec  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tingresoutputbulkexec -->

# tIngresOutputBulkExec

Inserts data in bulk to a table in the Ingres DBMS for performance gain.

tIngresOutputBulk and tIngresBulkExec are generally used together in a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT operation used to feed a database. These two steps are fused together in the tIngresOutputBulkExec component.

tIngresOutputBulkExec prepares an output file and uses it to feed a table in the Ingres DBMS.

Information noteNote:

* This component is available only when you have installed the 8.0.1-R2023-02 Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator.
* If you plan to upgrade from an earlier version of Talend Studio that has Ingres components, please make sure you apply the 8.0.1-R2023-02 Talend Studio Monthly update before starting the upgrade process.

## tIngresOutputBulkExec Standard properties

These properties are used to configure tIngresOutputBulkExec running in the Standard Job framework.

The Standard tIngresOutputBulkExec component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or <span>Repository</span> </span>. </p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Table | Name of the table to be filled. |
| VNode | Name of the virtual node.<br><br>The database server must be installed on the same machine where<br>Talend Studio is installed or where the Job using tIngresOutputBulkExec is deployed. |
| Database | Name of the database. |
| Action on table | Actions that can be taken on the table defined:<br><br><br>None: No operation made to the<br>table.<br><br><br>Truncate: Delete all the rows in<br>the table and release the file space back to the operating<br>system. |
| File name | Name of the file to be generated and loaded.<br><br>Information noteWarning:<br><br>This file is generated on the machine specified by the<br>VNode field so it should be<br>on the same machine as the database server. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Delete Working Files After Use | Select this check box to delete the files that are created during<br>the execution. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Field Separator | Character, string or regular expression to separate fields. |
| Row Separator | String (ex: "\n"on Unix) to separate rows |
| On Error | Policy of error handling:<br><br><br>Continue: Continue the<br>execution.<br><br><br>Terminate: Terminate the<br>execution. |
| Reject Row File | Path and name of the file that holds the rejected rows.<br><br>Available when Continue is<br>selected from the On Error<br>list. |
| Error Count | Number of errors to trigger the termination of the<br>execution.<br><br>Available when Terminate is<br>selected from the On Error<br>list. |
| Rollback | Enable or disable rollback. |
| Null Indicator | Value of the null indicator. |
| Session User | User of the defined session (the connection to the<br>database). |
| Allocation | Number of pages initially allocated to the table or index. |
| Extend | Number of pages by which a table or index grows. |
| Fill Factor | Specify the percentage (from 1 to 100) of each primary data page<br>that must be filled with rows, under ideal conditions. For example,<br>if you specify a fillfactor of 40, the DBMS Server fills 40% of each<br>of the primary data pages in the restructured table with<br>rows. |
| Min Pages/Max<br>Pages | Specify the minimum/maximum number of primary pages a hash table<br>must have. The Min. pages and Max. pages must be at least 1. |
| Leaf Fill | A bulk copy from can specify a leaffill value. This clause<br>specifies the percentage (from 1 to 100) of each B-tree leaf page<br>that must be filled with rows during the copy. This clause can be<br>used only on tables with a B-tree storage structure. |
| Non Leaf Fill | A bulk copy from can specify a nonleaffill value. This clause<br>specifies the percentage (from 1 to 100) of each B-tree non-leaf<br>index page that must be filled with rows during the copy. This<br>clause can be used only on tables with a B-tree storage structure. |
| Row Estimate | Specify the estimated number of rows to be copied from a file to a<br>table during a bulk copy operation. |
| Trailing WhiteSpace | Selected by default, this check box is designed to trim the<br>trailing white spaces and applies only to such data types as<br>VARCHAR, NVARCHAR and TEXT. |
| Output | Where to output the error message:<br><br><br>to console: Message output to the<br>console.<br><br><br>to global variable: Message<br>output to the global variable. |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | Usually deployed along with tIngresConnection or tIngresRow, tIngresOutputBulkExec prepares an output file and<br>feeds its data in bulk to the Ingres DBMS for performance<br>gain. |
| Limitation | The database server/client must be installed on the same<br>machine where Talend Studio is installed or where the Job using tIngresOutputBulkExec is deployed, so that the component<br>functions properly.<br><br>Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |

**Related concepts**

* [Loading data to a table in the Ingres DBMS](https://help.qlik.com/talend/en-US/components/8.0/tingresoutputbulkexec-tingresconnection-tfileinputdelimited-tingresconnection-tfileinputdelimited-loading-data-to-table-in-ingres-dbms-standard-component-in-this)
