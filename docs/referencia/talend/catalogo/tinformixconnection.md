# tinformixconnection

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tinformixconnection  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tinformixconnection -->

# tInformixConnection

Opens a connection to the specified database that can then be reused in the subsequent subJob or subJobs.

tInformixConnection is closely related to tInformixCommit and tInformixRollback. They are generally used along with tInformixConnection, with tInformixConnection opening the connection for the transaction.

## tInformixConnection Standard properties

These properties are used to configure tInformixConnection running in the Standard Job framework.

The Standard tInformixConnection component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or                           <span>Repository</span>.</span> </p> </li> <li> <p> <span>Built-in</span>: No property data stored                     centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file                     in which the properties are stored. The fields that follow are completed                     automatically using the data retrieved.</p> </li> </ul> |
| Host | Database server IP address. |
| Port | DB server listening port. |
| Database | Name of the database. |
| Schema | Name of the schema |
| Username and Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Instance | Name of the Informix instance to be used. This information can<br>generally be found in the SQL hosts file. |
| Additional JDBC parameters | Specify additional connection properties for the DB connection<br>you are creating. This option is not available if you have selected the<br>Use an existing connection check box<br>in the Basic settings. |
| Use or register a shared DB Connection | Select this checkbox to share<br>your database connection or fetch a database connection shared by a parent or<br>child Job, and in the Shared DB connection name field<br>displayed, enter the name for the shared database connection. This allows you<br>to share one single database connection (except the database schema setting)<br>among several database connection components from different Job levels that can<br>be either parent or child.<br><br>This option is<br>incompatible with the Use dynamic Job and Use an<br>independent process to run subJob options of the<br>tRunJob component. Using a shared connection together with a<br>tRunJob component with either of these two options enabled<br>will cause your Job to fail. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use Transaction | Clear this check box when the database is configured in NO\_LOG.<br>mode. If the check box is selected, you can choose whether to<br>activate the Auto Commit option. |
| Auto Commit | Select this checkbox to commit any changes to the database automatically<br>upon the transaction.<br><br>With this checkbox selected, you cannot use the corresponding commit<br>component to commit changes to the database; likewise, when using the<br>corresponding commit component, this checkbox has to be cleared. By default, the<br>auto commit function is disabled and changes must be committed explicitly using<br>the corresponding commit component.<br><br>Note that the auto commit function commits each SQL statement as a<br>single transaction immediately after the statement is executed while the<br>commit component does not commit only until all of the statements are<br>executed. For this reason, if you need more room to manage your transactions<br>in a Job, it is recommended to use the commit component. |
| tStatCatcher Statistics | Select this check box to collect the log data at a component<br>level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is generally used with other Informix components,<br>particularly tInformixCommit and<br>tInformixRollback. |
| Database Family | Databases/Informix |
| Limitation | This component requires installation of its related jar files. |
