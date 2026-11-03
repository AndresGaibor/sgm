# tjdbcrow (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tjdbcrow  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tjdbcrow -->

# tJDBCRow

Acts on the actual DB structure or on the data (although without handling data) using the SQLBuilder tool to write easily your SQL statements.

tJDBCRow is the component for any type database using a JDBC API. It executes the SQL query stated onto the specified database. The row suffix means the component implements a flow in the Job design although it doesn't provide output.

## tJDBCRow Standard properties

These properties are used to configure tJDBCRow running in the Standard Job framework.

The Standard tJDBCRow component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property Type | Select the way the connection details<br>will be set.<br><br><ul> <li> <p> <span>Built-In</span>: The connection details will be set                                locally for this component. You need to specify the values for all                                related connection properties manually.</p> </li> <li> <p> <span>Repository</span>: The connection details stored                                centrally in <span><span>Repository</span><abbr> &gt; </abbr><span>Metadata</span></span> will be reused by this component. </p> <p>You need to click                                the <span>[...]</span> button next to it and in the pop-up                                    <span>Repository Content</span> dialog box, select the                                connection details to be reused, and all related connection                                properties will be automatically filled in.</p> </li> </ul><br><br>This property is not available when other connection component is selected from<br>the Connection Component dropdown list. |
| Component list | Select the component that opens the database connection to be reused by this<br>component. |
| JDBC URL | The JDBC URL of the database to be used. For example, the JDBC URL for the Amazon Redshift database is jdbc:redshift://endpoint:port/database. |
| Drivers | Complete this table to load the driver JARs needed. To do<br>this, click the [+] button under the table to add<br>as many rows as needed, each row for a driver JAR, then select the cell and click the<br>[...] button at the right side of the cell to<br>open the Module dialog box from which you can select the driver JAR<br>to be used. For example, the driver jar RedshiftJDBC41-1.1.13.1013.jar for the Redshift database.<br><br>For more information, see [Importing a database driver](https://help.qlik.com/talend/r/en-US/8.0/components/jdbc/importing-database-driver). |
| Driver Class | Enter the class name for the specified driver between double<br>quotation marks. For example, for the RedshiftJDBC41-1.1.13.1013.jar driver, the name to be entered is<br>com.amazon.redshift.jdbc41.Driver. |
| User Id and Password | The database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>Click Edit schema to make changes to<br>the schema. If you make changes, the schema automatically becomes built-in.<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Table | Enter the name of the table to be processed. |
| Query Type and Query | Specify the database query statement paying particularly attention to the sequence of the fields which must correspond to the schema definition.<br><br><ul> <li> <p> <span>Built-In</span>: Fill in the query statement in the <span>Query</span> field manually or click the <span>[...]</span> button next to the <span>Query</span> field to build the statement graphically using the SQLBuilder.</p> </li> <li> <p> <span>Repository</span>: Select the relevant query stored in the Repository by clicking the <span>[...]</span> button next to it and in the pop-up <span>Repository Content</span> dialog box, select the query to be used, and the <span>Query</span> field will be automatically filled in.</p> </li> </ul> |
| Guess Query | Click this button to generate query in the Query field based on the defined table and schema. |
| Specify a data source alias | Select this checkbox and in the<br>Data source alias field displayed, specify the alias of<br>a data source created on Talend Runtime<br>side to use the shared connection pool defined in the data source configuration.<br>This option works only when you deploy and run your Job in Talend Runtime.<br><br>If you use the component's own DB configuration, your data source<br>connection will be closed at the end of the component. To prevent this from<br>happening, use a shared DB connection with the data source alias specified.<br><br>This property is not available when other connection component is selected from<br>the Connection Component dropdown list. |
| Die on error | Select the checkbox to stop the execution of the Job when an error<br>occurs.<br><br>Clear the checkbox to skip any rows on error and complete the<br>process for error-free rows.<br><br>When errors are skipped, you can collect the rows on error<br>using a Row &gt; Reject connection. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Propagate record set | Select this check box to propagate the result of the query to the output flow. From the<br>use column list displayed, you need to select a column into<br>which the query result will be inserted.<br><br>This option allows the component to have a different schema from that of the preceding<br>component. Moreover, the column that holds the query's recordset should be set to the<br>Object type and this component is usually followed by a<br>tParseRecordSet component. |
| Use PreparedStatement | Select this check box if you want to query the database using a prepared statement. In<br>the Set PreparedStatement Parameters table displayed, specify the<br>value for each parameter represented by a question mark ? in the<br>SQL statement defined in the Query field.<br><br><ul> <li> <p> <span>Parameter Index</span>: the position of the parameter in the SQL                statement.</p> </li> <li> <p> <span>Parameter Type</span>: the data type of the parameter.</p> </li> <li> <p> <span>Parameter Value</span>: the value of the parameter.</p> </li> </ul><br><br>For a related use case of this property, see [Using PreparedStatement objects to query data](https://help.qlik.com/talend/en-US/components/8.0/mysql/tmysqlrow-tparserecordset-tfileinputdelimited-tfileoutputdelimited-using-preparedstatement-objects-to-query-data-standard-component-this). |
| Use query timeout | Select this option to set a timeout period for the query or the batch query.<br>The Job will be terminated if the query or the batch query is timed out. You<br>can set the timeout period (in seconds) in the Timeout<br>field.<br><br>Information noteNote:<br><br><ul> <li>It varies with the driver implementations whether this option applies to                           an individual SQL statement or a set of SQL statements (that is, a batch                           query). Refer to your driver vendor documentation for details.</li> <li>This option is available only when you have installed the R2021-12                              <span>Talend Studio</span> Monthly update or a later one delivered by <span>Talend</span>. For more information, check with your administrator.</li> </ul> |
| Detect error on multiple statements | Select this option to detect errors that occur when executing the SQL query<br>statements.<br><br>With this option selected, an error caused by a SQL query<br>statement stops the Job execution and will be prompted. |
| Commit every | Specify the number of rows to be processed before committing<br>batches of rows together into the database.<br><br>This option ensures transaction quality (but not rollback) and, above all,<br>better performance at executions.<br><br>When used with an existing JDBC connection, tJDBCRow<br>ignores this option at runtime. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. |
| QUERY | The query statement being processed. This is a Flow variable<br>and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component offers the flexibility of<br>the DB query for any database using a JDBC connection and covers all<br>possible SQL queries. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
