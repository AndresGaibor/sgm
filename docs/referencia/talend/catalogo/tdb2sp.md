# tdb2sp

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tdb2sp  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tdb2sp -->

# tDB2SP

Offers a convenient way to call the database stored procedures.

## tDB2SP Standard properties

These properties are used to configure tDB2SP running in the Standard Job framework.

The Standard tDB2SP component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>. </p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| Host | Database server IP address |
| Port | Listening port number of DB server. |
| Database | Name of the database |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| SP Name | Type in the exact name of the Stored Procedure |
| Is Function / Return result<br>in | Check this box, if a value only is to be returned.<br><br>Select on the list the schema column, the value to be returned is<br>based on. |
| Parameters | Click the ![Add](https://help.qlik.com/talend/en-US/components/Resources/images/add.svg) button, and select the various Schema<br>Columns that will be required by the procedures. Note that the<br>SP schema can hold more columns than there are parameters used in the<br>procedure.<br><br>Select the Type of parameter:<br><br><ul> <li> <span>IN</span>: input parameter.</li> <li> <span>OUT</span>: output parameter/return value.</li> <li> <span>IN OUT</span>: input parameter is to be                           returned as value, likely after modification through the procedure                           (function).</li> <li> <span>RECORDSET</span>: input parameter is to                           be returned as a set of values, rather than single value.</li> </ul><br><br>Select a database type from the DB<br>Type list to map the source database type to the target database<br>type:<br><br><ul> <li> <span>AUTO-MAPPING</span>: map the source                           database type to the target database type automatically.</li> <li> <span>DATE</span>: string containing the date in the following                           format <span>YYMMDD</span> </li> <li> <span>TIMESTAMP</span>: string containing the date and time in                           the following format <span>YYYY-MM-DD-HH.MI.SS.999999</span>.</li> <li> <span>TIME</span>: string containing the time in the following                           format <span>HHMISS999</span>.</li> </ul><br><br>Information noteNote:<br><br>Check [Inserting data in mother/daughter tables](https://help.qlik.com/talend/en-US/components/8.0/mysql/tmysqlconnection-tmysqlrollback-tfileinputdelimited-inserting-data-in-mother-daughter-tables-standard-component-the) if you want to analyze a set<br>of records from a database table or DB query and return single<br>records. |
| Specify a data source alias | Select this checkbox and specify the alias of a data source created on the *Talend Runtime* side to use the shared connection pool defined in the data source configuration. This<br>option works only when you deploy and run your Job in *Talend Runtime*.<br><br>This checkbox is not available when the Use an existing<br>connection checkbox is selected. |
| Data source alias | Enter the alias of the data source created on the *Talend Runtime* side.<br><br>This field is available only when the Specify a data<br>source alias checkbox is selected. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC parameters | Specify additional connection properties for the DB connection you<br>are creating.<br><br>Information noteNote:<br><br>You can set the encoding parameters through this field. |
| tStat<br>Catcher<br>Statistics | Select this check box to collect log data at the component<br>level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as intermediary component. It can be used<br>as start component but only input parameters are thus allowed. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
