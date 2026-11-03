# tazuresynapseconnection

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tazuresynapseconnection  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tazuresynapseconnection -->

# tAzureSynapseConnection

Opens a connection to an Azure Synapse Analytics database.

## tAzureSynapseConnection Standard properties

These properties are used to configure tAzureSynapseConnection running in the Standard Job framework.

The Standard tAzureSynapseConnection component belongs to two families: Cloud and Databases.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property Type | Select the way the connection details<br>will be set.<br><br><ul> <li> <p> <span>Built-In</span>: The connection details will be set                                locally for this component. You need to specify the values for all                                related connection properties manually.</p> </li> <li> <p> <span>Repository</span>: The connection details stored                                centrally in <span><span>Repository</span><abbr> &gt; </abbr><span>Metadata</span></span> will be reused by this component. </p> <p>You need to click                                the <span>[...]</span> button next to it and in the pop-up                                    <span>Repository Content</span> dialog box, select the                                connection details to be reused, and all related connection                                properties will be automatically filled in.</p> </li> </ul> |
| JDBC Provider | Select the provider of the JDBC driver to be used. |
| Host | Enter the IP address or the hostname of the database server or the Azure Synapse<br>Analytics to be used.<br><br>If the SQL Server Browser service is running on the<br>machine where the server resides, you can connect to a named instance through a<br>TCP dynamic port by providing the host name and the instance name in this field<br>in the format of {host\_name}\{instance\_name}. In this<br>case, you can leave the Port field empty. See [SQL Server Browser service](https://docs.microsoft.com/en-us/sql/tools/configuration-manager/sql-server-browser-service?view=sql-server-ver16) for related<br>information. |
| Port | Enter the listening port number of the database server or the Azure Synapse<br>Analytics to be used.<br><br>If the SQL Server Browser service is running on the<br>machine where the server resides, you can connect to a named instance through a<br>TCP dynamic port by providing the host name and the instance name in the<br>Host field and leave this field empty. See [SQL Server Browser service](https://docs.microsoft.com/en-us/sql/tools/configuration-manager/sql-server-browser-service?view=sql-server-ver16) for related<br>information. |
| Schema | Enter the name of the Azure Synapse Analytics schema. |
| Database | Specify the name of the Azure Synapse Analytics to be used. |
| Username and<br>Password | Enter the authentication data.<br><br>To enter the password, click the<br>[...] button next to the<br>Password field, enter the password in double<br>quotes in the pop-up dialog box, and then click<br>OK.<br><br>You can use<br>Type 2 integrated authentication on<br>Windows by adding<br>integratedSecurity=true in the<br>Additional JDBC Parameters field and leave<br>these two fields empty. See section *Connecting with integrated<br>authentication On Windows* at [Building the connection URL](https://docs.microsoft.com/en-us/sql/connect/jdbc/building-the-connection-url?redirectedfrom=MSDN) for related<br>information. |
| Additional JDBC Parameters | Specify additional connection properties for the database<br>connection you are creating. The properties are separated by semicolon and<br>each property is a key-value pair. For example, *encrypt=true;trustServerCertificate=false;*<br>*hostNameInCertificate=\*.database.windows.net;loginTimeout=30;* for<br>Azure SQL database connection. |
| Use or register a shared DB Connection | Select this checkbox to share<br>your database connection or fetch a database connection shared by a parent or<br>child Job, and in the Shared DB connection name field<br>displayed, enter the name for the shared database connection. This allows you<br>to share one single database connection (except the database schema setting)<br>among several database connection components from different Job levels that can<br>be either parent or child.<br><br>This option is<br>incompatible with the Use dynamic Job and Use an<br>independent process to run subJob options of the<br>tRunJob component. Using a shared connection together with a<br>tRunJob component with either of these two options enabled<br>will cause your Job to fail.<br><br>This checkbox is not available when the Specify a data source<br>alias checkbox is selected. |
| Specify a data source alias | Select this checkbox and in the<br>Data source alias field displayed, specify the alias of<br>a data source created on Talend Runtime<br>side to use the shared connection pool defined in the data source configuration.<br>This option works only when you deploy and run your Job in Talend Runtime.<br><br>This checkbox is not available when the Use or register a shared DB<br>Connection checkbox is selected. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Authenticate using Azure Active<br>Directory | When selected, this option allows you to pick the authentication mode to use<br>from the Azure Active Directory authentication mode<br>dropdown list:<br><br><ul> <li> <span>Service principal (client secret)</span>: use the service                        principal credentials (client ID and client secret) to authenticate.</li> <li> <span>User password</span>: use the Azure Active Directory user                        credentials (username and password) to authenticate.</li> </ul><br><br>Read the Usage section of this document for<br>information about Microsoft SQL Server/JDBC encryption<br>requirements. |
| Auto Commit | Select this checkbox to commit any changes to the database automatically<br>upon the transaction.<br><br>With this checkbox selected, you cannot use the corresponding commit<br>component to commit changes to the database; likewise, when using the<br>corresponding commit component, this checkbox has to be cleared. By default, the<br>auto commit function is disabled and changes must be committed explicitly using<br>the corresponding commit component.<br><br>Note that the auto commit function commits each SQL statement as a<br>single transaction immediately after the statement is executed while the<br>commit component does not commit only until all of the statements are<br>executed. For this reason, if you need more room to manage your transactions<br>in a Job, it is recommended to use the commit component. |
| Share identity insert in multi table | Select this checkbox to share IDENTITY\_INSERT with multiple tables in one<br>connection. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| Usage rules | This component is more commonly used with other Azure Synapse Analytics<br>components and it opens a connection that can be reused by them.<br><br>Information noteImportant: Microsoft SQL Server/JDBC encryption requirements<br><br>Starting<br>with recent versions of the Microsoft SQL Server JDBC driver, TLS encryption<br>is enabled by default<br>(encrypt=true;trustServerCertificate=false). This<br>enhances security, but if your SQL Server does not support encrypted<br>connections or does not require clients to use TLS, you must set<br>encrypt=false in the JDBC parameters of this component<br>to connect successfully.<br><br><ul> <li> <p>For production or cloud environments using certificates signed by a                              trusted authority (e.g., Azure, AWS), no changes are needed, the                              default settings will work. </p> </li> <li> <p>For servers using self-signed certificates, use                                 <span>encrypt=true;trustServerCertificate=true</span> or                              specify the trust store details                                 (<span>encrypt=true;trustStore=&lt;your_trust_store&gt;;trustStorePassword=&lt;your_trust_store_password&gt;</span>).                           </p> </li> <li> <p>For non-secure development or test servers, set                                 <span>encrypt=false</span> in the additional JDBC parameters.                           </p> </li> </ul><br><br>For more information on how to use connections with encryption<br>properties, see [Microsoft SQL JDBC documentation](https://learn.microsoft.com/en-us/sql/connect/jdbc/connecting-with-ssl-encryption?view=sql-server-ver17). |
| Limitation | Note that some<br>features that are supported by other databases are not supported by<br>Azure Synapse Analytics. For more information, see [Unsupported table<br>features](https://docs.microsoft.com/en-us/azure/sql-data-warehouse/sql-data-warehouse-tables-overview#unsupported-table-features). |
