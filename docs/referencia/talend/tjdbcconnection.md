# tjdbcconnection (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tjdbcconnection  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tjdbcconnection -->

# tJDBCConnection

Opens a connection to the specified database that can then be reused in the subsequent subJob or subJobs.

## tJDBCConnection Standard properties

These properties are used to configure tJDBCConnection running in the Standard Job framework.

The Standard tJDBCConnection component belongs to the Databases and the ELT families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property Type | Select the way the connection details<br>will be set.<br><br><ul> <li> <p> <span>Built-In</span>: The connection details will be set                                locally for this component. You need to specify the values for all                                related connection properties manually.</p> </li> <li> <p> <span>Repository</span>: The connection details stored                                centrally in <span><span>Repository</span><abbr> &gt; </abbr><span>Metadata</span></span> will be reused by this component. </p> <p>You need to click                                the <span>[...]</span> button next to it and in the pop-up                                    <span>Repository Content</span> dialog box, select the                                connection details to be reused, and all related connection                                properties will be automatically filled in.</p> </li> </ul> |
| JDBC URL | The JDBC URL of the database to be used. For example, the JDBC URL for the Amazon Redshift database is jdbc:redshift://endpoint:port/database. |
| Drivers | Complete this table to load the driver JARs needed. To do<br>this, click the [+] button under the table to add<br>as many rows as needed, each row for a driver JAR, then select the cell and click the<br>[...] button at the right side of the cell to<br>open the Module dialog box from which you can select the driver JAR<br>to be used. For example, the driver jar RedshiftJDBC41-1.1.13.1013.jar for the Redshift database.<br><br>For more information, see [Importing a database driver](https://help.qlik.com/talend/r/en-US/8.0/components/jdbc/importing-database-driver). |
| Driver Class | Enter the class name for the specified driver between double<br>quotation marks. For example, for the RedshiftJDBC41-1.1.13.1013.jar driver, the name to be entered is<br>com.amazon.redshift.jdbc41.Driver. |
| User Id and Password | The database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Use or register a shared DB Connection | Select this checkbox to share<br>your database connection or fetch a database connection shared by a parent or<br>child Job, and in the Shared DB connection name field<br>displayed, enter the name for the shared database connection. This allows you<br>to share one single database connection (except the database schema setting)<br>among several database connection components from different Job levels that can<br>be either parent or child.<br><br>This option is<br>incompatible with the Use dynamic Job and Use an<br>independent process to run subJob options of the<br>tRunJob component. Using a shared connection together with a<br>tRunJob component with either of these two options enabled<br>will cause your Job to fail.<br><br>This checkbox is not available when the Specify a data source<br>alias checkbox is selected. |
| Specify a data source alias | Select this checkbox and in the<br>Data source alias field displayed, specify the alias of<br>a data source created on Talend Runtime<br>side to use the shared connection pool defined in the data source configuration.<br>This option works only when you deploy and run your Job in Talend Runtime.<br><br>This checkbox is not available when the Use or register a shared DB<br>Connection checkbox is selected. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use Auto-Commit | Select this checkbox to activate the auto commit mode. |
| Auto Commit | Select this checkbox to commit any changes to the database automatically<br>upon the transaction.<br><br>With this checkbox selected, you cannot use the corresponding commit<br>component to commit changes to the database; likewise, when using the<br>corresponding commit component, this checkbox has to be cleared. By default, the<br>auto commit function is disabled and changes must be committed explicitly using<br>the corresponding commit component.<br><br>Note that the auto commit function commits each SQL statement as a<br>single transaction immediately after the statement is executed while the<br>commit component does not commit only until all of the statements are<br>executed. For this reason, if you need more room to manage your transactions<br>in a Job, it is recommended to use the commit component. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is more commonly used with other tJDBC\*<br>components, especially with the tJDBCCommit and tJDBCRollback components. |
