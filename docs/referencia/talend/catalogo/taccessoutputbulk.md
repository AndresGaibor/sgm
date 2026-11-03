# taccessoutputbulk

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/taccessoutputbulk  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/taccessoutputbulk -->

# tAccessOutputBulk

Prepares the file which contains the data used to feed the Access database.

The tAccessOutputBulk and tAccessBulkExec components are generally used together to output data to a delimited file and then to perform various actions on the file in an Access database, in a two step process. These two steps are fused together in the tAccessOutputBulkExec component, detailed in a separate section. The advantage of using a two step process is that it makes it possible to carry out transformations on the data before loading it in the database.

tAccessOutputBulk writes a delimited file.

## tAccessOutputBulk Standard properties

These properties are used to configure tAccessOutputBulk running in the Standard Job framework.

The Standard tAccessOutputBulk component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | Either Built-in or<br>Repository<br>.<br><br><ul> <li> <span>Built-in</span>: No property data stored						      centrally.</li> <li> <span>Repository</span>: Select the repository						      file in which the properties are stored. The fields that follow are						      completed automatically using the data retrieved.</li> </ul> |
| File Name | Name and path to the file to be created and/or the variable to be<br>used.<br><br>For further information about how to define and use a variable in<br>a Job, [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |
| Create directory if does not<br>exist | Select this check box to create the as yet<br>non-existant file directory that specified in the File Name field. |
| Append | Select this check box to add any new rows to the end of the<br>file. |
| Schema and Edit<br>schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><br>Built-In: You create and store the schema locally for this component<br>only.<br><br><br>Repository: You have already created the schema and stored it in the<br>Repository. You can reuse it in various projects and Job designs.<br><br>When the schema to be reused has default values that are<br>integers or functions, ensure that these default values are not enclosed within<br>quotation marks. If they are, you must remove the quotation marks manually.<br><br>For more information, see [Retrieving table schemas](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg).<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Include header | Select this check box to include the column header in the file. |
| Use text enclosure | Select this check box to enclose the text with characters. You can specify the character used to<br>enclose the text in the Field enclosure field. |
| Encoding | Select the encoding from the list or select Custom and define it manually. This field is<br>compulsory for DB data handling. |
| tStat<br>Catcher Statistics | Select this check box to collect log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is to be used along with tAccessBulkExec component. Used together they offer<br>gains in performance while feeding an Access database. |
| Component family | Databases/Access |
| Limitation | If you are using an ODBC driver, you need to work with Java 7, and make sure that your JVM<br>and ODBC versions match up: both 64-bit or 32-bit.<br><br>When working with Java 8, this component supports only the General collation mode of<br>Access. |
