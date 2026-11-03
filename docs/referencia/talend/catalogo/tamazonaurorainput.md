# tamazonaurorainput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tamazonaurorainput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tamazonaurorainput -->

# tAmazonAuroraInput

Reads an Amazon Aurora database and extracts fields based on a query.

tAmazonAuroraInput executes a database query with a strictly defined order which must correspond to the schema definition. Then it passes on the field list to the next component via a Row &gt;Main link.

## tAmazonAuroraInput Standard properties

These properties are used to configure tAmazonAuroraInput running in the Standard Job framework.

The Standard tAmazonAuroraInput component belongs to the Cloud and the Databases families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property Type | <ul> <li> <p>Either <span>Built-In</span> or                        <span>Repository</span>.</p> </li> <li> <p> <span>Built-In</span>: No property data stored                     centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file                     in which the properties are stored. The database connection fields that follow                     are completed automatically using the data retrieved.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Host | Type in the IP address or hostname of the Amazon Aurora<br>database. |
| Port | Type in the listening port number of the Amazon Aurora<br>database. |
| Database | Type in the name of the database you want to use. |
| Username and Password | Type in the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>This component offers the advantage of the                  dynamic schema feature. This allows you to retrieve unknown columns from source                  files or to copy batches of columns from a source without mapping each column                  individually. For further information about dynamic schemas, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema" target="_blank">Dynamic schema</a>.</p> <p>This            dynamic schema feature is designed for the purpose of retrieving unknown columns of a            table and is recommended to be used for this purpose only; it is not recommended for the            use of creating tables.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Table Name | Type in the name of the table to be read. |
| Query Type and Query | Enter the database query paying particularly attention to the<br>proper sequence of the fields in order to match the schema definition.<br><br><br>*If using the dynamic schema feature, the SELECT query must<br>include the \* wildcard, to retrieve<br>all of the columns from the table selected.* |
| Guess Query | Click the button to generate the query which corresponds to the<br>table schema in the Query field. |
| Guess schema | Click the button to retrieve the schema from the table. |
| Specify a data source alias | Select this checkbox and specify the alias of a data source created on the *Talend Runtime* side to use the shared connection pool defined in the data source configuration. This<br>option works only when you deploy and run your Job in *Talend Runtime*.<br><br>This check box disappears when the Use an existing connection check box is selected. |
| Data source alias | Type in the alias of the data source created on the *Talend Runtime* side.<br><br>This field appears only when the Specify a data source alias check box is selected. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC parameters | Specify additional connection properties for the database<br>connection you are creating. When you need to handle data of the time-stamp<br>type *0000-00-00 00:00:00* using this component, set the<br>parameter to noDatetimeStringSync=true&zeroDa­teTimeBehavior=convertToNull.<br><br>This field disappears when the Use<br>an existing connection check box in the Basic settings view is selected. |
| Enable stream | Select this check box to enable streaming over buffering which<br>allows the code to read from a large table without consuming a large amount of<br>memory in order to optimize the performance. |
| Trim all the String/Char columns | Select this check box to remove leading and trailing whitespace<br>from all the String/Char columns. |
| Trim column | Select the check box(es) in the Trim column to remove leading and trailing whitespace from the<br>corresponding column(s).<br><br>This option disappears when the Trim<br>all the String/Char columns check box is selected. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at<br>the Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>QUERY: the query statement<br>being processed. This is a Flow variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is usually used as a start component of a Job or<br>subJob and it needs an output link. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |

**Related concepts**

* [Handling data with Amazon Aurora](https://help.qlik.com/talend/en-US/components/8.0/tamazonaurorainput-tamazonauroracommit-tlogrow-handling-data-with-amazon-aurora-standard-component-this)
