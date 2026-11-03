# tredshiftrow

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tredshiftrow  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tredshiftrow -->

# tRedshiftRow

Acts on the actual DB structure or on the data (although without handling data), depending on the nature of the query and the database.

The SQLBuilder tool helps you write easily your SQL statements.

tRedshiftRow is the specific component for this database query. It executes the SQL query stated onto the specified database. The row suffix means the component implements a flow in the Job design although it does not provide output.

## tRedshiftRow Standard properties

These properties are used to configure tRedshiftRow running in the Standard Job framework.

The Standard tRedshiftRow component belongs to the Cloud and the Databases families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | Either Built-in or Repository<br>.<br><br><ul> <li> <span>Built-in</span>: No property data stored						         centrally.</li> <li> <span>Repository</span>: Select the repository						         file in which the properties are stored. The fields that follow are						         completed automatically using the data retrieved.</li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Driver version | Select the Redshift driver version to be used: Driver v1 or<br>Driver v2.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-04<br>Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Host | Hostname or IP address of the database server. |
| Port | Listening port number of the database server. |
| Database | Name of the database.<br><br>The bucket and the Redshift database to be used<br>must be in the same region on Amazon. This could avoid the S3ServiceException errors known to<br>Amazon. For further information about these errors, see [S3ServiceException Errors](https://docs.aws.amazon.com/redshift/latest/dg/s3serviceexception-error.html). |
| Schema | Exact name of the schema. |
| Username and Password | Database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Use String JDBC parameters | Set JDBC properties in a string. If you select this option, enter your JDBC parameter string in<br>the Additional JDBC Parameters field; otherwise, enter JDBC<br>properties and property values in the Additional JDBC<br>Parameters table.<br><br>This option is not available if Driver v1 is selected from<br>the Driver version drop-down list.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-04<br>Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Additional JDBC Parameters | Specify additional JDBC properties for the connection you are creating. The<br>properties are separated by ampersand & and each property is a key-value pair. For<br>example, *ssl=true &<br>sslfactory=com.amazon.redshift.ssl.NonValidatingFactory*, which means the<br>connection will be created using SSL.<br><br>This field is not available if Driver v2 is selected<br>from the Driver version drop-down list and the<br>Use String JDBC parameters option is not<br>selected. |
| Additional JDBC Parameters (table) | Specify JDBC properties in table rows.<br><br>To specify a JDBC property, add a row in the table by clicking the plus button on<br>the bottom of this table, enter the property name in the<br>Key column, and then enter the property value in the<br>Value column.<br><br>This table is available when Driver v2 is selected from the<br>Driver version drop-down list and the Use<br>String JDBC parameters option is not selected.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-04<br>Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Schema and Edit<br>Schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><br>Built-In: You create and store the schema locally for this component<br>only.<br><br><br>Repository: You have already created the schema and stored it in the<br>Repository. You can reuse it in various projects and Job designs.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Table Name | Name of the table from which the data will be read. |
| Query type | Either Built-in or Repository<br>.<br><br><ul> <li> <span>Built-in</span>: Fill in manually the query						         statement or build it graphically using SQLBuilder.</li> <li> <span>Repository:</span> Select the relevant query						         stored in the Repository. The <span>Query</span>						         field gets accordingly filled in.</li> </ul> |
| Guess Query | Click the Guess Query button to<br>generate the query which corresponds to your table schema in the Query<br>field. |
| Query | Enter your database query paying particularly attention to properly<br>sequence the fields in order to match the schema definition.<br><br>Information noteNote: All statements in<br>this field will be executed in a single transaction. To have multiple<br>statements executed in different transactions, put each of them in a separate<br>tRedshiftRow component. |
| Die on error | This check box is selected by default. Clear the check box to skip the<br>row on error and complete the process for error-free rows. If needed,<br>you can retrieve the rows on error through a Row &gt; Rejects<br>link. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Propagate QUERY's recordset | Select this check box to insert the result of the query into a COLUMN<br>of the current flow. Select this column from the use column list.<br><br>Information noteNote: This option allows the component to have a different schema from<br>that of the preceding component. Moreover, the column that holds the<br>QUERY's recordset should be set to the type of *Object* and this component is usually<br>followed by tParseRecordSet. |
| Use PreparedStatement | Select this check box if you want to query the database using a<br>PreparedStatement. In the Set PreparedStatement<br>Parameter table, define the parameters represented by "?"<br>in the SQL instruction of the Query<br>field in the Basic Settings tab.<br><br><br>Parameter Index: Enter the parameter<br>position in the SQL instruction.<br><br><br>Parameter Type: Enter the parameter<br>type.<br><br><br>Parameter Value: Enter the parameter<br>value.<br><br>Information noteNote: This option is very useful if you need to execute the same query<br>several times. Performance levels are increased. |
| Commit every | Number of rows to be completed before committing batches of rows<br>together into the database. This option ensures transaction quality (but<br>not rollback) and above all better performance on executions. |
| JDBC url | Select a way to access to an Amazon Redshift database from the<br>JDBC url drop-down list.<br><br><ul> <li> <span>Standard</span>: Use the          standard way to access the Redshift database.</li> <li> <span>SSO</span>: Use the IAM          Single Sign-ON (SSO) authentication way to access the Redshift Database. Before selecting          this option, ensure that the IAM role added to your Redshift cluster has appropriate          access rights and permissions to this cluster. You can ask the administrator of your AWS          services for more details.<p>This option is available only when <span>Use an existing connection</span> check box is not selected from            the <span>Basic settings</span>. </p> </li> </ul> |
| tStat<br>Catcher Statistics | Select this check box to collect log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br>Note that if the Propagate QUERY's recordset option is<br>selected in the Advanced settings view, this variable<br>returns the number of single ResultSet, which is 1.<br><br><br>QUERY: the query statement<br>being processed. This is a Flow variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component offers the flexibility benefit of the database query<br>and covers all possible SQL queries. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |
