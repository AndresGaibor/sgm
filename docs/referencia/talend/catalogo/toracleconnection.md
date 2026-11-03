# toracleconnection

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/toracleconnection  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/toracleconnection -->

# tOracleConnection

Information noteImportant: Support for Oracle 12-7 is removed from 8.0.1-R2024-12 onwards. Use Oracle 18 instead.

Opens a connection to the specified Oracle database for reuse in the subsequent subJob or subJobs.

## tOracleConnection Standard properties

Information noteImportant: Support for Oracle 12-7 is removed from 8.0.1-R2024-12 onwards. Use Oracle 18 instead.

These properties are used to configure tOracleConnection running in the Standard Job framework.

The Standard tOracleConnection component belongs to the Databases and the ELT families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span>                                or <span>Repository</span>.</span> </p> </li> <li> <p> <span>Built-in</span>: No property data stored                            centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository                            file in which the properties are stored. The fields that follow are                            completed automatically using the data retrieved.</p> </li> </ul> |
| Connection Type | Drop-down list of available drivers:<br><br><ul> <li><span>Oracle OCI</span>: Select this                     connection type to use Oracle Call Interface with a set of C-language                     software APIs that provide an interface to the Oracle database.</li> <li><span>Oracle Custom</span>: Select this                     connection type to access a clustered database.</li> <li><span>Oracle Service Name</span>: Select this                     connection type to use the TNS alias that you give when you connect to                     the remote database.</li> <li><span>WALLET</span>: Select this connection                     type to store credentials in an Oracle wallet.</li> <li><span>Oracle SID</span>: Select this                     connection type to uniquely identify a particular database on a                     system.</li> </ul><br><br>Information noteNote: Connections that are of WALLET type are for the<br>tCreateTable component, the tOracleInput component, and the tOracleOutput<br>component only. Errors may occur if connections of the<br>WALLET type are used by any other components. |
| DB Version | Select the Oracle version in use. |
| Use tns file | Select this check box to use the metadata of a context<br>included in a tns file.<br><br>Information noteNote: One tns file may have many contexts.<br><br><br>TNS File: Enter the path to the<br>tns file manually or browse to the file by clicking the [...] button<br>next to the filed.<br><br><br>Select a DB Connection in Tns<br>File: Click the [...] button to display all the<br>contexts held in the tns file and select the desired one. |
| Host | Database server IP address. |
| Port | Listening port number of DB server. |
| Database | Name of the database. |
| Schema | Name of the schema. |
| Username and Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Use SSL | Select this checkbox to use the SSL protocol to protect the communication with<br>your database server.<br><br>This property is available only when ORACLE CUSTOM is<br>selected from the Connection Type dropdown list and<br>Oracle 12-7 or Oracle 18 and<br>above is selected from the DB Version<br>dropdown list. |
| TrustStore file | Enter the path to the TrustStore file used to authenticate your database server<br>in SSL authentication.<br><br>This property is available only when the<br>Use SSL checkbox is selected. |
| TrustStore password | Enter the password for the TrustStore file.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings.<br><br>This property is available only when the<br>Use SSL checkbox is selected. |
| Need Client authentication | Select this checkbox if SSL client authentication is needed.<br><br>This property is available only when the<br>Use SSL checkbox is selected. |
| KeyStore file | Enter the path to the keystore file used for SSL client authentication.<br><br>This property is available only when<br>the Need Client authentication checkbox is selected. |
| KeyStore password | Enter the password for the KeyStore file.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings.<br><br>This property is available only when<br>the Need Client authentication checkbox is selected. |
| Disable CBC protection | Select this checkbox to disable the use of CBC (Cipher Block Chaining) in SSL<br>authentication.<br><br>This property is available only when the<br>Use SSL checkbox is selected. |
| Additional JDBC parameters | Specify additional connection properties for the DB<br>connection you are creating.<br><br>Information noteNote:<br><br>You can set the encoding parameters through this<br>field. |
| Use or register a shared DB Connection | Select this checkbox to share<br>your database connection or fetch a database connection shared by a parent or<br>child Job, and in the Shared DB connection name field<br>displayed, enter the name for the shared database connection. This allows you<br>to share one single database connection (except the database schema setting)<br>among several database connection components from different Job levels that can<br>be either parent or child.<br><br>This option is<br>incompatible with the Use dynamic Job and Use an<br>independent process to run subJob options of the<br>tRunJob component. Using a shared connection together with a<br>tRunJob component with either of these two options enabled<br>will cause your Job to fail.<br><br>This checkbox is not available when the Specify a data source<br>alias checkbox is selected. |
| Specify a data source alias | Select this checkbox and specify the alias of a data source created on the *Talend Runtime* side to use the shared connection pool defined in the data source configuration. This<br>option works only when you deploy and run your Job in *Talend Runtime*. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Auto Commit | Select this checkbox to commit any changes to the database automatically<br>upon the transaction.<br><br>With this checkbox selected, you cannot use the corresponding commit<br>component to commit changes to the database; likewise, when using the<br>corresponding commit component, this checkbox has to be cleared. By default, the<br>auto commit function is disabled and changes must be committed explicitly using<br>the corresponding commit component.<br><br>Note that the auto commit function commits each SQL statement as a<br>single transaction immediately after the statement is executed while the<br>commit component does not commit only until all of the statements are<br>executed. For this reason, if you need more room to manage your transactions<br>in a Job, it is recommended to use the commit component. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a<br>Job level as well as at each component level. |
| Support NLS | Select this option to enable globalization support. See [Overview of Globalization<br>Support](https://docs.oracle.com/en/database/oracle/oracle-database/21/nlspg/overview-of-globalization-support.html) for related information.<br><br>This option is available when Oracle 18 and above is<br>selected from the DB Version drop-down list in<br>the Basic settings view.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-09<br>Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is more commonly used with other<br>Oracle components, especially with the tOracleCommit and tOracleRollback components. |

**Related concepts**

* [Checking number format using a stored procedure](https://help.qlik.com/talend/en-US/components/8.0/toracleconnection-toracleinput-toraclesp-tlogrow-checking-number-format-using-stored-procedure-standard-component-the)

**Related tasks**

* [Using Oracle as a vector database](https://help.qlik.com/talend/en-US/components/8.0/toracleconnection-toracleinput-toracleoutput-toracleclose-tfileinputdelimited-tmap-tlogrow-using-oracle-as-vector-db-standard-component)
