# tmysqlsp

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tmysqlsp  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmysqlsp -->

# tMysqlSP

Calls a MySQL database stored procedure.

tMysqlSP offers a convenient way to centralize multiple or complex queries in a database and call them easily.

## tMysqlSP Standard properties

These properties are used to configure tMysqlSP running in the Standard Job framework.

The Standard tMysqlSP component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Host | Database server IP address |
| Port | Listening port number of DB server. |
| Database | Name of the database |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| SP Name | Type in the exact name of the Stored Procedure |
| Is Function / Return result<br>in | Select this check box, if a value only is to be returned.<br><br>Select on the list the schema column, the value to be returned is<br>based on. |
| Parameters | Click the Plus button and select the various Schema Columns that will be required by the<br>procedures. Note that the SP schema can hold more columns than there<br>are paramaters used in the procedure.<br><br>Select the Type of<br>parameter:<br><br><br>IN: Input parameter.<br><br><br>OUT: Output parameter/return<br>value.<br><br><br>IN OUT: Input parameter is to be<br>returned as value, likely after modification through the procedure<br>(function).<br><br><br>RECORDSET: Input parameter is to<br>be returned as a set of values, rather than single value.<br><br>Information noteNote:<br><br>Check [Inserting data in mother/daughter tables](https://help.qlik.com/talend/en-US/components/8.0/mysql/tmysqlconnection-tmysqlrollback-tfileinputdelimited-inserting-data-in-mother-daughter-tables-standard-component-the) if you want to analyze a set of records from a<br>database table or DB query and return single records. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional connection properties for the DB connection you are<br>creating. This option is not available if you have selected the Use an<br>existing connection check box in the Basic<br>settings.<br><br>Information noteTip: You can press Ctrl+Space to access a list<br>of predefined global variables. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a Job level<br>as well as at each component level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as intermediary component. It can be used<br>as start component but only input parameters are thus allowed. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | The Stored Procedures syntax should match the Database syntax. |

**Related concepts**

* [Using tMysqlSP to find a State Label using a stored procedure](https://help.qlik.com/talend/en-US/components/8.0/tmysqlsp-trowgenerator-tlogrow-tlogrow-using-tmysqlsp-to-find-state-label-using-stored-procedure-standard-component-the)
