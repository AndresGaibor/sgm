# tteradatascd

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tteradatascd  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tteradatascd -->

# tTeradataSCD

Addresses Slowly Changing Dimension needs, reading regularly a source of data and logging the changes into a dedicated SCD table.

tTeradataSCD reflects and tracks changes in a dedicated Teradata SCD table.

## tTeradataSCD Standard properties

These properties are used to configure tTeradataSCD running in the Standard Job framework.

The Standard tTeradataSCD component belongs to the Business Intelligence and the Databases families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property Type | <ul> <li> <p>Either <span>Built-In</span> or <span>Repository</span>.</p> </li> <li> <p> <span>Built-In</span>: No property data stored							centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository							file in which the properties are stored. The database connection related							fields that follow are completed automatically using the data							retrieved.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Host | Type in the IP address or hostname of the database. |
| Database | Type in the name of the database you want to use. |
| Username and Password | Type in the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | Type in the name of the table to be written. Note that only one table can be written at<br>a time. |
| Action on table | On the table defined, you can perform one of the following operations:<br><br><ul> <li> <p> <span>None</span>: No operation is										carried out.</p> </li> <li> <p> <span>Create table</span>: The table does not exist and gets										created.</p> </li> <li> <p> <span>Create table if not exists</span>: The table is created if										it does not exist.</p> </li> </ul> |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| SCD Editor | The SCD editor helps to build and configure the data flow for slowly<br>changing dimension outputs.<br><br>For more information, see [SCD management methodology](https://help.qlik.com/talend/en-US/components/8.0/scd/scd-management-methodology). |
| Use memory saving mode | Select this check box to maximize system performance. |
| Source keys include Null | Select this check box to allow the source key columns to have Null<br>values.<br><br>Information noteWarning:<br><br>Special attention should be paid to the uniqueness of the source<br>key(s) values when this option is selected. |
| Die on error | Select the checkbox to stop the execution of the Job when an error<br>occurs.<br><br>Clear the checkbox to skip any rows on error and complete the process for<br>error-free rows. When errors are skipped, you can collect the rows on error using a Row &gt; Reject link. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional connection properties for the database connection<br>you are creating.<br><br>This field is not visible when the Use an existing<br>connection check box is selected. |
| Debug mode | Select this check box to display each step during processing entries<br>in a database. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at the Job<br>level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE\_UPDATED: the number of rows updated.<br>This is an After variable and it returns an integer.<br><br><br>NB\_LINE\_INSERTED: the number of<br>rows inserted. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an Output component. It requires an<br>Input component and a Row &gt;<br>Main link as input. |
| Limitation | This component does not support using SCD type 0 together with other<br>SCD types. |
