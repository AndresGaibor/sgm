# tpostgresqlconnection

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tpostgresqlconnection  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tpostgresqlconnection -->

# tPostgresqlConnection

Opens a connection to the specified database that can then be reused in the subsequent subJob or subJobs.

The tPostgresqlConnection opens a connection to the database for a current transaction.

## tPostgresqlConnection Standard properties

These properties are used to configure tPostgresqlConnection running in the Standard Job framework.

The Standard tPostgresqlConnection component belongs to the Databases and the ELT families.

The component in this framework is available in all Talend products.

This component supports PostgreSQL vector data types. Use the VECTOR or Dynamic DB type in your schema column definition to store and then query vector embeddings. For more information about pgvector, read [the Amazon documentation](https://aws.amazon.com/about-aws/whats-new/2023/05/amazon-rds-postgresql-pgvector-ml-model-integration/).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | Either Built-in or<br>Repository<br><br><ul> <li> <p> <span>Built-in</span>: No property data stored                           centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository                           file in which the properties are stored. The fields that follow are                           completed automatically using the data retrieved.</p> </li> </ul> |
| DB Version | Select the database version in the dropdown list. |
| Host | Enter the database server IP address. |
| Port | Listening port number of DB server. |
| Database | Enter the name of the database. |
| Schema | Enter the name of the PostgreSQL schema. |
| Username and Password | Enter the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Use or register a shared DB Connection | Select this checkbox to share<br>your database connection or fetch a database connection shared by a parent or<br>child Job, and in the Shared DB connection name field<br>displayed, enter the name for the shared database connection. This allows you<br>to share one single database connection (except the database schema setting)<br>among several database connection components from different Job levels that can<br>be either parent or child.<br><br>This option is<br>incompatible with the Use dynamic Job and Use an<br>independent process to run subJob options of the<br>tRunJob component. Using a shared connection together with a<br>tRunJob component with either of these two options enabled<br>will cause your Job to fail.<br><br>This checkbox is not available when the Specify a data source<br>alias checkbox is selected. |
| Specify a data source<br>alias | Select this checkbox and specify the alias of a data source created on the *Talend Runtime* side to use the shared connection pool defined in the data source configuration. This<br>option works only when you deploy and run your Job in *Talend Runtime*.<br><br>This checkbox is not visible when the Use or register a<br>shared DB Connection checkbox is selected. |
| Data source alias | Enter the alias of the data source created on the *Talend Runtime* side.<br><br>This field is available only when the Specify a data<br>source alias checkbox is selected. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Auto Commit | Select this checkbox to commit any changes to the database automatically<br>upon the transaction.<br><br>With this checkbox selected, you cannot use the corresponding commit<br>component to commit changes to the database; likewise, when using the<br>corresponding commit component, this checkbox has to be cleared. By default, the<br>auto commit function is disabled and changes must be committed explicitly using<br>the corresponding commit component.<br><br>Note that the auto commit function commits each SQL statement as a<br>single transaction immediately after the statement is executed while the<br>commit component does not commit only until all of the statements are<br>executed. For this reason, if you need more room to manage your transactions<br>in a Job, it is recommended to use the commit component. |
| tStatCatcher Statistics | Select this checkbox to collect log data at the component level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is more commonly used with other tPostgresql\*<br>components, especially with the tPostgresqlCommit and tPostgresqlRollback components. |
