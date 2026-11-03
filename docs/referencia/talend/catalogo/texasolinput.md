# texasolinput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/texasolinput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/texasolinput -->

# tExasolInput

Retrieves data from an Exasol database based on a query with a strictly defined order which corresponds to the schema definition, and passes the data to the next component.

## tExasolInput Standard properties

These properties are used to configure tExasolInput running in the Standard Job framework.

The Standard tExasolInput component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property Type | Either Built-In or Repository.<br><br><ul> <li> <p> <span>Built-In</span>: No property data                                    stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the                                    repository file in which the properties are stored. The database                                    connection fields that follow are completed automatically using                                    the data retrieved.</p> </li> </ul> |
| ![](https://help.qlik.com/talend/en-US/components/Resources/images/Save_Icon.png) | Click this icon to open a database<br>connection wizard and store the database connection parameters you set<br>in the component Basic<br>settings view.<br><br>For more information about setting up<br>and storing database connection parameters, see [Centralizing database metadata](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/centralizing-database-metadata). |
| Use an existing connection | Select this check box and from the list displayed select the<br>relevant connection component to reuse the connection details you have already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Host name | Enter the host or host list of the Exasol database servers. Exasol can run in a cluster<br>environment. The valid value can be a simple IP address (for example, *172.16.173.128*), an IP range list (for example, *172.16.173.128..130* that represents three servers *172.16.173.128*, *172.16.173.129*, and *172.16.173.130*), or a<br>comma-separated host list (for example, *server1,server2,server3*) of the Exasol database cluster. |
| Port | Enter the listening port number of the Exasol database cluster. |
| Schema name | Enter the name of the schema you want to use. |
| Username and Password | Enter the user authentication data to access the Exasol database.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> <p>This component offers the advantage of the                  dynamic schema feature. This allows you to retrieve unknown columns from source                  files or to copy batches of columns from a source without mapping each column                  individually. For further information about dynamic schemas, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema" target="_blank">Dynamic schema</a>.</p> <p>This            dynamic schema feature is designed for the purpose of retrieving unknown columns of a            table and is recommended to be used for this purpose only; it is not recommended for the            use of creating tables.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Table Name | Enter the name of the table to be<br>queried. |
| Query Type and Query | Enter the database query, paying<br>particularly attention to the proper sequence of the fields in order to<br>match the schema definition. |
| Guess Query | Click the button to generate the query<br>that corresponds to the table schema in the Query field. |
| Guess schema | Click the button to retrieve the schema<br>from the table. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Change fetch size | Select this check box to change the<br>fetch size which specifies the amount of resultset data sent during one<br>single communication step with the database. In the Fetch size field<br>displayed, you need to enter the size in KB. |
| Additional JDBC parameters | Specify additional connection properties for the database connection you are<br>creating. The properties are separated by semicolon and each property is a key-value<br>pair, for example, *encryption=1;clientname=Talend*.<br><br>This field is not available if the Use an existing<br>connection check box is selected. |
| Trim all the String/Char columns | Select this check box to remove leading<br>and trailing whitespaces from all the String/Char columns. |
| Trim column | Select the check box in the Trim column to remove<br>leading and trailing whitespaces from the corresponding field.<br><br>This table is not available if the<br>Trim all the String/Char<br>columns check box is selected. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>QUERY: the query statement<br>being processed. This is a Flow variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is usually used as a<br>start component of a Job or subJob and it needs an output link. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |

**Related concepts**

* [Importing data into an Exasol database table from a local CSV file](https://help.qlik.com/talend/en-US/components/8.0/texasolbulkexec-texasolinput-tfixedflowinput-tlogrow-importing-data-into-exasolution-database-table-from-local-csv-file-standard-component-this)
