# taccessconnection

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/taccessconnection  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/taccessconnection -->

# tAccessConnection

Opens a connection to the specified database that can then be reused in the subsequent subJob or subJobs.

tAccessConnection opens a connection to the database for a current transaction.

## tAccessConnection Standard properties

These properties are used to configure tAccessConnection running in the Standard Job framework.

The Standard tAccessConnection component belongs to the Databases and the ELT families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | Either Built-in or Repository<br>.<br><br><ul> <li> <span>Built-in</span>: No property data stored                     centrally.</li> <li> <span>Repository</span>: Select the repository file                        in which the properties are stored. The fields that follow are completed                        automatically using the data retrieved.</li> </ul> |
| Database | Name of the database. |
| Username and Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Use or register a shared DB Connection | Select this checkbox to share<br>your database connection or fetch a database connection shared by a parent or<br>child Job, and in the Shared DB connection name field<br>displayed, enter the name for the shared database connection. This allows you<br>to share one single database connection (except the database schema setting)<br>among several database connection components from different Job levels that can<br>be either parent or child.<br><br>This option is<br>incompatible with the Use dynamic Job and Use an<br>independent process to run subJob options of the<br>tRunJob component. Using a shared connection together with a<br>tRunJob component with either of these two options enabled<br>will cause your Job to fail. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC parameters | Specify additional connection properties for the DB connection you<br>are creating. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is more commonly used with other tAccess\*<br>components, especially with the tAccessCommit and tAccessRollback components. |
| Limitation | If you are using an ODBC driver, you need to work with Java 7, and make sure that your JVM<br>and ODBC versions match up: both 64-bit or 32-bit.<br><br>When working with Java 8, this component supports only the General collation mode of<br>Access.<br><br>From 8.0.1-R2022-11 monthly release onward, this component uses hsql.2.7.1.jar, a module built in JDK 11, only Java 11 and higher versions are supported. |

**Related concepts**

* [Inserting data in parent/child tables](https://help.qlik.com/talend/en-US/components/8.0/taccessinput-taccessconnection-tlogrow-inserting-data-in-parent-child-tables-standard-component-the)
