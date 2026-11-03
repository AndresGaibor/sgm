# tsybaseoutputbulk

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsybaseoutputbulk  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsybaseoutputbulk -->

# tSybaseOutputBulk

Prepares the file to be used as parameter in the INSERT query to feed the Sybase database.

The tSybaseOutputBulk and tSybaseBulkExec components are generally used together as parts of a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT operation used to feed a database. These two steps are fused together in the tSybaseOutputBulkExec component, detailed in a separate section. The advantage of using two separate components is that the data can be transformed before it is loaded in the database.

Writes a file with columns based on the defined delimiter and the Sybase standards.

## tSybaseOutputBulk Standard properties

These properties are used to configure tSybaseOutputBulk running in the Standard Job framework.

The Standard tSybaseOutputBulk component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p>Either <span>Built-in</span> or <span>Repository</span>. </p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| File Name | Name of the file to be generated.<br><br>Information noteWarning:<br><br>This file is generated on the local machine or a shared folder<br>on the LAN. |
| Append | Select this check box to add the new rows at the end of the<br>file. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Row separator | String (ex: "\n"on Unix) to distinguish rows. |
| Field separator | Character, string or regular expression to separate fields.<br><br>Information noteWarning:<br><br><br>*Fully in line with the Java syntax, this<br>component does not allow the use of Sybase-orientated<br>row/field separators, such as \x09.* |
| Include header | Select this check box to include the column header in the file. |
| Encoding | Select the encoding from the list or select Custom and define it<br>manually. This field is compulsory for DB data handling. |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component requires installation of its related jar files.<br><br>This component is to be used along with tSybaseBulkExec component. Used together they offer<br>gains in performance while feeding a Sybase database. |
| Component family | Databases/Sybase |
