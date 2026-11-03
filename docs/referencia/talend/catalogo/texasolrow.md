# texasolrow

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/texasolrow  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/texasolrow -->

# tExasolRow

Executes SQL queries on an Exasol database.

Depending on the nature of the query and the database, tExasolRow acts on the actual structure of the database, or indeed the data, although without modifying them. The Row suffix indicates that it is used to channel a flow in a Job although it does not produce any output data.

## tExasolRow Standard properties

These properties are used to configure tExasolRow running in the Standard Job framework.

The Standard tExasolRow component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property Type | Either Built-In or Repository.<br><br><ul> <li> <p> <span>Built-In</span>: No property data                                    stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the                                    repository file in which the properties are stored. The database                                    connection fields that follow are completed automatically using                                    the data retrieved.</p> </li> </ul> |
| Use an existing connection | Select this check box and from the list displayed select the<br>relevant connection component to reuse the connection details you have already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Host | Enter the host or host list of the Exasol database servers. Exasol can run in a cluster<br>environment. The valid value can be a simple IP address (for example, *172.16.173.128*), an IP range list (for example, *172.16.173.128..130* that represents three servers *172.16.173.128*, *172.16.173.129*, and *172.16.173.130*), or a<br>comma-separated host list (for example, *server1,server2,server3*) of the Exasol database cluster. |
| Port | Enter the listening port number of the Exasol database cluster. |
| Schema name | Enter the name of the schema you want to use. |
| Username and Password | Enter the user authentication data to access the Exasol database.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Table Name | Enter the name of the table to be<br>processed. |
| Query Type | Either Built-In or Repository<br>.<br><br><ul> <li> <p> <span>Built-In</span>: Enter the query                                    manually or with the help of the SQLBuilder.</p> </li> <li> <p> <span>Repository</span>: Select the                                    appropriate query from the <span>Repository</span>. The <span>Query</span> field is                                    then completed automatically.</p> </li> </ul> |
| Guess Query | Click the Guess Query button to generate the query<br>that corresponds to the table schema in the Query field. |
| Query | Enter the database query paying<br>particularly attention to the proper sequence of the fields in order to<br>match the schema definition. |
| Die on error | Select the checkbox to stop the execution of the Job when an error<br>occurs.<br><br>Clear the checkbox to skip any rows on error and complete the process for<br>error-free rows. When errors are skipped, you can collect the rows on error using a Row &gt; Reject link. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC parameters | Specify additional connection properties for the database connection you are<br>creating. The properties are separated by semicolon and each property is a key-value<br>pair, for example, *encryption=1;clientname=Talend*.<br><br>This field is not available if the Use an existing<br>connection check box is selected. |
| Propagate QUERY's recordset | Select this check box to insert the<br>query results in one of the flow columns. Select the particular column<br>from the use<br>column list. |
| Use PreparedStatement | Select this check box to use prepared<br>statements and in the Set<br>PreparedStatement Parameters table displayed, add as<br>many parameters as needed and set the following attributes for each<br>parameter:<br><br><ul> <li> <p> <span>Parameter Index</span>: enter the                                    index of the prepared statement parameter.</p> </li> <li> <p> <span>Parameter Type</span>: click in the                                    cell and select the type of the parameter from the list.</p> </li> <li> <p> <span>Parameter Value</span>: enter the                                    value of the parameter.</p> </li> </ul> |
| Commit every | Enter the number of rows to be included<br>in each batch before the data is written. This option guarantees the<br>quality of the transaction (although there is no rollback option) and<br>improves performance. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | QUERY: the query statement<br>being processed. This is a Flow variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component offers query flexibility<br>as it covers all possible SQL query requirements. |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |
