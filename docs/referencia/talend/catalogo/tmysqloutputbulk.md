# tmysqloutputbulk

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tmysqloutputbulk  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmysqloutputbulk -->

# tMysqlOutputBulk

Writes a file with columns based on the defined delimiter and the MySQL or Aurora standards.

The tMysqlOutputBulk and tMysqlBulkExec components are used together in a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT statement used to feed a database. These two steps are fused together in the tMysqlOutputBulkExec component, detailed in a separate section. The advantage of using two separate steps is that the data can be transformed before it is loaded in the database.

## tMysqlOutputBulk Standard properties

These properties are used to configure tMysqlOutputBulk running in the Standard Job framework.

The Standard tMysqlOutputBulk component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| File Name | Name of the file to be generated.<br><br>This file is generated on the same machine where Talend Studio is installed or where the Job using tMysqlOutputBulk is deployed. |
| Append | Select this check box to add the new rows at the end of the<br>file |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Row separator | String (ex: "\n" on Unix) to distinguish rows. |
| Field separator | Character, string or regular expression to separate fields. |
| Text enclosure | Character used to enclose the text. |
| Create directory if does not exist | This check box is selected by default. It creates a directory to<br>hold the output table if required. |
| Custom the flush buffer size | Customize the amount of memory used to temporarily store output<br>data. In the Row number field,<br>enter the number of rows after which the memory is to be freed<br>again. |
| Records contain NULL value | This check box is selected by default. It allows you to take<br>account of NULL value fields. If you clear the check box, the NULL<br>values will automatically be replaced with empty values. |
| Check disk space | Select the this check box to throw an exception during execution<br>if the disk is full. |
| Encoding | Select the encoding from the list or select Custom and define it manually. This field is<br>compulsory for DB data handling. |
| tStatCatcher Statistics | Select this check box to collect the log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is to be used along with tMySQlBulkExec component. Used together they<br>offer gains in performance while feeding a MySQL or Aurora database. |
| Component family | Databases/MySQL |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |

**Related concepts**

* [Inserting transformed data in MySQL database](https://help.qlik.com/talend/en-US/components/8.0/tmysqlbulkexec-tmysqloutputbulk-tmap-inserting-transformed-data-in-mysql-database-standard-component-this)
