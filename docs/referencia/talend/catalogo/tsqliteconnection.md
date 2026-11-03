# tsqliteconnection

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsqliteconnection  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsqliteconnection -->

# tSQLiteConnection

Opens a connection to the database for a current transaction.

## tSQLiteConnection Standard properties

These properties are used to configure tSQLiteConnection running in the Standard Job framework.

The Standard tSQLiteConnection component belongs to the Databases and the ELT families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or                           <span>Repository</span>.</span> </p> </li> <li> <p> <span>Built-in</span>: No property data stored                     centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file                     in which the properties are stored. The fields that follow are completed                     automatically using the data retrieved.</p> </li> </ul> |
| Database | Name of the database. |
| Use or register a shared DB Connection | Select this checkbox to share<br>your database connection or fetch a database connection shared by a parent or<br>child Job, and in the Shared DB connection name field<br>displayed, enter the name for the shared database connection. This allows you<br>to share one single database connection (except the database schema setting)<br>among several database connection components from different Job levels that can<br>be either parent or child.<br><br>This option is<br>incompatible with the Use dynamic Job and Use an<br>independent process to run subJob options of the<br>tRunJob component. Using a shared connection together with a<br>tRunJob component with either of these two options enabled<br>will cause your Job to fail. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Auto Commit | Select this checkbox to commit any changes to the database automatically<br>upon the transaction.<br><br>With this checkbox selected, you cannot use the corresponding commit<br>component to commit changes to the database; likewise, when using the<br>corresponding commit component, this checkbox has to be cleared. By default, the<br>auto commit function is disabled and changes must be committed explicitly using<br>the corresponding commit component.<br><br>Note that the auto commit function commits each SQL statement as a<br>single transaction immediately after the statement is executed while the<br>commit component does not commit only until all of the statements are<br>executed. For this reason, if you need more room to manage your transactions<br>in a Job, it is recommended to use the commit component. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a<br>Job level as well as at each component level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is more commonly used with other tSQLite\* components, especially with<br>the tSQLiteCommit and tSQLiteRollback components. |
