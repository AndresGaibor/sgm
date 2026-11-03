# tpostgresqlrow

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tpostgresqlrow  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tpostgresqlrow -->

# tPostgresqlRow

Acts on the actual DB structure or on the data (although without handling data), depending on the nature of the query and the database. The SQLBuilder tool helps you write easily your SQL statements.

The tPostgresqlRow is the specific component for the database query. It executes the SQL query stated onto the specified database. The row suffix means the component implements a flow in the Job design although it doesn't provide output.

## tPostgresqlRow Standard properties

These properties are used to configure tPostgresqlRow running in the Standard Job framework.

The Standard tPostgresqlRow component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | Either Built-in or<br>Repository.<br><br><ul> <li> <p> <span>Built-in</span>: No property data stored                           centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository                           file in which the properties are stored. The fields that follow are                           completed automatically using the data retrieved.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| DB Version | Select the database version in the dropdown list. |
| Host | Enter the database server IP address. |
| Port | Listening port number of DB server. |
| Database | Enter the name of the database. |
| Schema | Enter the name of the PostgreSQL schema. |
| Username and Password | Enter the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Schema and Edit Schema | A schema is a row description, it defines the number of fields to be<br>processed and passed on to the next component. The schema is either Built-in or stored remotely in the Repository.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul><br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>This component supports PostgreSQL vector data types. Use the<br>VECTOR or Dynamic DB type in your schema<br>column definition to store and then query vector embeddings. For more information about<br>pgvector, read [the Amazon documentation](https://aws.amazon.com/about-aws/whats-new/2023/05/amazon-rds-postgresql-pgvector-ml-model-integration/). |
| Query type | Either Built-in<br>or Repository.<br><br><ul> <li> <p> <span>Built-in</span>: Fill in manually the                           query statement or build it graphically using SQLBuilder</p> </li> <li> <p> <span>Repository</span>: Select the relevant                           query stored in the Repository. The Query field gets accordingly filled                           in.</p> </li> </ul> |
| Query | Enter your DB query paying particularly attention to properly sequence the<br>fields in order to match the schema definition. |
| Specify a data source alias | Select this checkbox and specify the alias of a data source created on the *Talend Runtime* side to use the shared connection pool defined in the data source configuration. This<br>option works only when you deploy and run your Job in *Talend Runtime*.<br><br>This checkbox is not available when the Use an existing<br>connection checkbox is selected. |
| Data source alias | Enter the alias of the data source created on the *Talend Runtime* side.<br><br>This field is available only when the Specify a data<br>source alias checkbox is selected. |
| Die on error | This checkbox is selected by default. Clear the checkbox to<br>skip the row on error and complete the process for error-free rows. If needed,<br>you can retrieve the rows on error via a Row &gt; Rejects<br>link. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional JDBC parameters for the database connection created.<br><br>This property is not available when the Use an existing connection check box in the Basic<br>settings view is selected. |
| Propagate QUERY's recordset | Select this checkbox to insert the result of the query into a COLUMN of the<br>current flow. Select this column from the use<br>column list.<br><br>Information noteNote: This option allows the component<br>to have a different schema from that of the preceding component. Moreover, the<br>column that holds the QUERY's recordset should be set to the type of *Object* and this component is usually followed by<br>tParseRecordSet. |
| Use PreparedStatement | Select this checkbox if you want to query the database using a<br>PreparedStatement. In the Set PreparedStatement<br>Parameter table, define the parameters represented by "?" in the<br>SQL instruction of the Query field in the<br>Basic Settings tab.<br><br><br>Parameter Index: Enter the parameter<br>position in the SQL instruction.<br><br><br>Parameter Type: Enter the parameter<br>type.<br><br><br>Parameter Value: Enter the parameter<br>value.<br><br>Information noteNote: This option is very useful if you need to<br>execute the same query several times. Performance levels are<br>increased |
| Commit every | Number of rows to be completed before committing batches of rows together<br>into the DB. This option ensures transaction quality (but not rollback) and above<br>all better performance on executions. |
| tStat<br>Catcher Statistics | Select this checkbox to collect log data at the component level. |
| Enable parallel execution | Select this check box to perform high-speed data processing, by treating<br>multiple data flows simultaneously. Note that this feature depends on the database or<br>the application ability to handle multiple inserts in parallel as well as the number of<br>CPU affected. In the Number of parallel executions<br>field, either:<br><br><ul> <li>Enter the number of parallel executions desired.</li> <li>Press <span>Ctrl+Space</span> and select               the appropriate context variable from the list. For further information about context               variables, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables" target="_blank">Using contexts and variables</a>. </li> </ul><br><br>Note that when parallel execution is enabled, it is not possible to use global<br>variables to retrieve return values in a subJob.<br><br><ul><li>						            The <span>Action on							table</span> field is not available with the							parallelization function. Therefore, you must use a <span>tCreateTable</span> component if you							want to create a table. 					          </li><li>						            When parallel execution is enabled, it is not							possible to use global variables to retrieve return values in a							subJob.					          </li> </ul> |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | QUERY: the query statement<br>being processed. This is a Flow variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component offers the flexibility benefit of the DB query and covers all<br>possible SQL queries.<br><br>This component supports PostgreSQL vector data<br>types. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
