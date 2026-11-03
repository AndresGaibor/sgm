# tredshiftconnection

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tredshiftconnection  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tredshiftconnection -->

# tRedshiftConnection

Opens a connection to the specified database that can then be reused in the subsequent subJob or subJobs.

tRedshiftConnection opens a connection to the database for a current transaction.

## tRedshiftConnection Standard properties

These properties are used to configure tRedshiftConnection running in the Standard Job framework.

The Standard tRedshiftConnection component belongs to the Cloud and the Databases families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | Either Built-in or<br>Repository.<br><br><ul> <li> <span>Built-in</span>: No property data stored                       centrally.</li> <li> <span>Repository</span>: Select the repository file                       in which the properties are stored. The fields that follow are completed                       automatically using the data retrieved.</li> </ul> |
| Driver version | Select the Redshift driver version to be used: Driver v1 or<br>Driver v2.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-04<br>Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Host | Host name or IP address of DB server. |
| Port | Listening port number of DB server. |
| Database | Name of the database.<br><br>The bucket and the Redshift database to be used<br>must be in the same region on Amazon. This could avoid the S3ServiceException errors known to<br>Amazon. For further information about these errors, see [S3ServiceException Errors](https://docs.aws.amazon.com/redshift/latest/dg/s3serviceexception-error.html). |
| Schema | Name of the schema. |
| Username and Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Use String JDBC parameters | Set JDBC properties in a string. If you select this option, enter your JDBC parameter string in<br>the Additional JDBC Parameters field; otherwise, enter JDBC<br>properties and property values in the Additional JDBC<br>Parameters table.<br><br>This option is not available if Driver v1 is selected from<br>the Driver version drop-down list.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-04<br>Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Additional JDBC Parameters | Specify additional JDBC properties for the connection you are creating. The<br>properties are separated by ampersand & and each property is a key-value pair. For<br>example, *ssl=true &<br>sslfactory=com.amazon.redshift.ssl.NonValidatingFactory*, which means the<br>connection will be created using SSL.<br><br>This field is not available if Driver v2 is selected<br>from the Driver version drop-down list and the<br>Use String JDBC parameters option is not<br>selected. |
| Additional JDBC Parameters (table) | Specify JDBC properties in table rows.<br><br>To specify a JDBC property, add a row in the table by clicking the plus button on<br>the bottom of this table, enter the property name in the<br>Key column, and then enter the property value in the<br>Value column.<br><br>This table is available when Driver v2 is selected from the<br>Driver version drop-down list and the Use<br>String JDBC parameters option is not selected.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-04<br>Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Use or register a shared DB Connection | Select this checkbox to share<br>your database connection or fetch a database connection shared by a parent or<br>child Job, and in the Shared DB connection name field<br>displayed, enter the name for the shared database connection. This allows you<br>to share one single database connection (except the database schema setting)<br>among several database connection components from different Job levels that can<br>be either parent or child.<br><br>This option is<br>incompatible with the Use dynamic Job and Use an<br>independent process to run subJob options of the<br>tRunJob component. Using a shared connection together with a<br>tRunJob component with either of these two options enabled<br>will cause your Job to fail. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Log file | Specify the path to the log file to be generated during the<br>data retrieval process.<br><br>Note that if the logging information needs to be saved and<br>this component reuses the connection created by a tRedshiftConnection component, you must specify the property *loglevel=1/2/3* in the Additional JDBC Parameters<br>field of the tRedshiftConnection component.<br><br>There is no limitation on the size of the log file. If the specified log<br>file already exists, it will be overwritten. |
| Logging level | Select a logging level from the drop-down list to specify<br>which kind of events will be logged in the log file. |
| Auto Commit | Select this checkbox to commit any changes to the database automatically<br>upon the transaction.<br><br>With this checkbox selected, you cannot use the corresponding commit<br>component to commit changes to the database; likewise, when using the<br>corresponding commit component, this checkbox has to be cleared. By default, the<br>auto commit function is disabled and changes must be committed explicitly using<br>the corresponding commit component.<br><br>Note that the auto commit function commits each SQL statement as a<br>single transaction immediately after the statement is executed while the<br>commit component does not commit only until all of the statements are<br>executed. For this reason, if you need more room to manage your transactions<br>in a Job, it is recommended to use the commit component. |
| JDBC url | Select a way to access to an Amazon Redshift database from the<br>JDBC url drop-down list.<br><br><ul> <li> <span>Standard</span>: Use the          standard way to access the Redshift database.</li> <li> <span>SSO</span>: Use the IAM          Single Sign-ON (SSO) authentication way to access the Redshift Database. Before selecting          this option, ensure that the IAM role added to your Redshift cluster has appropriate          access rights and permissions to this cluster. You can ask the administrator of your AWS          services for more details.<p>This option is available only when <span>Use an existing connection</span> check box is not selected from            the <span>Basic settings</span>. </p> </li> </ul> |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at<br>a Job level as well as at each component level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is more commonly used with other tRedshift\* components,<br>especially with the tRedshiftCommit and<br>tRedshiftRollback<br>components. |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |

**Related concepts**

* [Handling data with Redshift](https://help.qlik.com/talend/en-US/components/8.0/tredshiftconnection-tredshiftinput-tlogrow-handling-data-with-redshift-standard-component-this)
