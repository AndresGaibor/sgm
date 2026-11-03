# tingresconnection

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tingresconnection  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tingresconnection -->

# tIngresConnection

Opens a connection to the specified database that can then be reused in the subsequent subJob or subJobs.

tIngresConnection opens a connection to the database for a current transaction.

Information noteNote:

* This component is available only when you have installed the 8.0.1-R2023-02 Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator.
* If you plan to upgrade from an earlier version of Talend Studio that has Ingres components, please make sure you apply the 8.0.1-R2023-02 Talend Studio Monthly update before starting the upgrade process.

## tIngresConnection Standard properties

These properties are used to configure tIngresConnection running in the Standard Job framework.

The Standard tIngresConnection component belongs to the Databases and the ELT families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or                           <span>Repository</span>.</span> </p> </li> <li> <p> <span>Built-in</span>: No property data stored                     centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file                     in which the properties are stored. The fields that follow are completed                     automatically using the data retrieved.</p> </li> </ul> |
| Server | Database server IP address. |
| Port | Listening port number of DB server. |
| Database | Name of the database |
| Username and Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Use or register a shared DB Connection | Select this checkbox to share<br>your database connection or fetch a database connection shared by a parent or<br>child Job, and in the Shared DB connection name field<br>displayed, enter the name for the shared database connection. This allows you<br>to share one single database connection (except the database schema setting)<br>among several database connection components from different Job levels that can<br>be either parent or child.<br><br>This option is<br>incompatible with the Use dynamic Job and Use an<br>independent process to run subJob options of the<br>tRunJob component. Using a shared connection together with a<br>tRunJob component with either of these two options enabled<br>will cause your Job to fail. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Auto Commit | Select this checkbox to commit any changes to the database automatically<br>upon the transaction.<br><br>With this checkbox selected, you cannot use the corresponding commit<br>component to commit changes to the database; likewise, when using the<br>corresponding commit component, this checkbox has to be cleared. By default, the<br>auto commit function is disabled and changes must be committed explicitly using<br>the corresponding commit component.<br><br>Note that the auto commit function commits each SQL statement as a<br>single transaction immediately after the statement is executed while the<br>commit component does not commit only until all of the statements are<br>executed. For this reason, if you need more room to manage your transactions<br>in a Job, it is recommended to use the commit component. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a<br>Job level as well as at each component level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is more commonly used with other tIngres\*<br>components, especially with the tIngresCommit and tIngresRollback components. |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |

**Related concepts**

* [Loading data to a table in the Ingres DBMS](https://help.qlik.com/talend/en-US/components/8.0/tingresoutputbulkexec-tingresconnection-tfileinputdelimited-tingresconnection-tfileinputdelimited-loading-data-to-table-in-ingres-dbms-standard-component-in-this)
