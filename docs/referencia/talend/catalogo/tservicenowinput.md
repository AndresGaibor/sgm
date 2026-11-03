# tservicenowinput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tservicenowinput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tservicenowinput -->

# tServiceNowInput

Accesses ServiceNow and retrieves data from it.

tServiceNowInput retrieves data from ServiceNow according to the specified conditions.

## tServiceNowInput Standard properties

These properties are used to configure tServiceNowInput running in the Standard Job framework.

The Standard tServiceNowInput component belongs to the Business and the Cloud families.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Use Existing Connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| URL | Enter the URL of the ServiceNow instance to be connected. |
| Username and Password | Enter the user authentication data to connect to the ServiceNow instance.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Table | Select the name of the table from which the<br>data will be retrieved or select Use<br>Custom Table and in the Custom Table Name field displayed enter the<br>table name. |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Conditions | Specify search conditions to retrieve only the<br>data that matches the criteria by clicking the [+] button to add as many conditions as needed<br>and then setting the following parameters for each condition:<br><br><ul> <li> <p> <span>Input column</span>:                           click in the cell and select the column of the input schema on which the                           search condition is to be set.</p> </li> <li> <p> <span>Operator</span>: click in                           the cell and select an operator for the search condition.</p> </li> <li> <p> <span>Value</span>: enter the                           value for the corresponding column for the search condition.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Trim all columns | Select this check box to remove the leading and<br>trailing whitespaces from all columns. |
| Limit | Enter the maximum number of records to be<br>retrieved.<br><br>Information noteNote:<br><br><ul> <li>This field takes effect only when it holds a positive integer.</li> <li>There is no limit on the record number if you enter <kbd>""</kbd>,                        <kbd>0</kbd>, or leave this field empty. In this case, all the                        records will be retrieved.</li> </ul> |
| Advanced<br>Query | Select this check box to enter filtering conditions combined with AND and OR<br>logical operators. You can enter query statements in this field through<br>copy/paste operations. For information about the logical operators, see [Operators available for filters and<br>queries](https://docs.servicenow.com/bundle/newyork-platform-user-interface/page/use/common-ui-elements/reference/r_OpAvailableFiltersQueries.html) and [Generate an encoded query string through a filter](https://docs.servicenow.com/bundle/newyork-platform-user-interface/page/use/using-lists/task/t_GenEncodQueryStringFilter.html).<br><br>The Conditions field in<br>the Basic settings view is not available<br>if you select this check box. |
| tStatCatcher Statistics | Select this check box to gather the Job<br>processing metadata at the Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is usually used as a start<br>component in a<br>Talend<br>flow and it requires an output component. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
