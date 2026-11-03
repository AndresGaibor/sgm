# tazuresynapseinput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tazuresynapseinput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tazuresynapseinput -->

# tAzureSynapseInput

Reads data and extracts fields based on a query from an Azure SQL Data Warehouse database.

## tAzureSynapseInput Standard properties

These properties are used to configure tAzureSynapseInput running in the Standard Job framework.

The Standard tAzureSynapseInput component belongs to two families: Cloud and Databases.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>When a Job contains the parent Job and the child Job, if you need to<br>share an existing connection between the two levels, for example, to share the<br>connection created by the parent Job with the child Job, you have to:<br><br><ol> <li> <p>In the parent level, register the database connection to be shared                in the <span>Basic settings</span> view of the connection                component which creates that very database connection.</p> </li> <li> <p>In the child level, use a dedicated connection component to read                that registered database connection.</p> </li> </ol><br><br>For an example about how to share a database connection across Job levels, see<br>[Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Property Type | Select the way the connection details<br>will be set.<br><br><ul> <li> <p> <span>Built-In</span>: The connection details will be set                                locally for this component. You need to specify the values for all                                related connection properties manually.</p> </li> <li> <p> <span>Repository</span>: The connection details stored                                centrally in <span><span>Repository</span><abbr> &gt; </abbr><span>Metadata</span></span> will be reused by this component. </p> <p>You need to click                                the <span>[...]</span> button next to it and in the pop-up                                    <span>Repository Content</span> dialog box, select the                                connection details to be reused, and all related connection                                properties will be automatically filled in.</p> </li> </ul> |
| JDBC Provider | Select the provider of the JDBC driver to be used. |
| Host | Enter the IP address or the hostname of the database server or the Azure Synapse<br>Analytics to be used.<br><br>If the SQL Server Browser service is running on the<br>machine where the server resides, you can connect to a named instance through a<br>TCP dynamic port by providing the host name and the instance name in this field<br>in the format of {host\_name}\{instance\_name}. In this<br>case, you can leave the Port field empty. See [SQL Server Browser service](https://docs.microsoft.com/en-us/sql/tools/configuration-manager/sql-server-browser-service?view=sql-server-ver16) for related<br>information. |
| Port | Enter the listening port number of the database server or the Azure Synapse<br>Analytics to be used.<br><br>If the SQL Server Browser service is running on the<br>machine where the server resides, you can connect to a named instance through a<br>TCP dynamic port by providing the host name and the instance name in the<br>Host field and leave this field empty. See [SQL Server Browser service](https://docs.microsoft.com/en-us/sql/tools/configuration-manager/sql-server-browser-service?view=sql-server-ver16) for related<br>information. |
| Schema | Enter the name of the Azure Synapse Analytics schema. |
| Database | Specify the name of the Azure Synapse Analytics to be used. |
| Username and<br>Password | Enter the authentication data.<br><br>To enter the password, click the<br>[...] button next to the<br>Password field, enter the password in double<br>quotes in the pop-up dialog box, and then click<br>OK.<br><br>You can use<br>Type 2 integrated authentication on<br>Windows by adding<br>integratedSecurity=true in the<br>Additional JDBC Parameters field and leave<br>these two fields empty. See section *Connecting with integrated<br>authentication On Windows* at [Building the connection URL](https://docs.microsoft.com/en-us/sql/connect/jdbc/building-the-connection-url?redirectedfrom=MSDN) for related<br>information. |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>Click Edit schema to make changes to<br>the schema. If you make changes, the schema automatically becomes built-in.<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Table name | Specify the name of the table to be used. |
| Query Type | Select the way the query will be set.<br><br><ul> <li> <p> <span>Built-in</span>: Fill in manually the query statement or                           build it graphically using SQLBuilder.</p> </li> <li> <p> <span>Repository</span>: Select the relevant query stored in                           the Repository. The <span>Query</span> field gets accordingly                           filled in.</p> </li> </ul> |
| Guess Query | Click this button to generate the query which corresponds to your table<br>schema in the Query field. |
| Guess schema | Click this button to generate the schema columns based on the query specified in the Query field. |
| Query | Specify the query paying particularly attention to properly sequence the<br>fields in order to match the schema definition. |
| Specify a data source alias | Select this checkbox and in the<br>Data source alias field displayed, specify the alias of<br>a data source created on Talend Runtime<br>side to use the shared connection pool defined in the data source configuration.<br>This option works only when you deploy and run your Job in Talend Runtime.<br><br>This checkbox is not available when the Use an existing<br>Connection check box is selected. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional connection properties for the database<br>connection you are creating. The properties are separated by semicolon and<br>each property is a key-value pair. For example, *encrypt=true;trustServerCertificate=false;*<br>*hostNameInCertificate=\*.database.windows.net;loginTimeout=30;* for<br>Azure SQL database connection. |
| Authenticate using Azure Active<br>Directory | When selected, this option allows you to pick the authentication mode to use<br>from the Azure Active Directory authentication mode<br>dropdown list:<br><br><ul> <li> <span>Service principal (client secret)</span>: use the service                        principal credentials (client ID and client secret) to authenticate.</li> <li> <span>User password</span>: use the Azure Active Directory user                        credentials (username and password) to authenticate.</li> </ul><br><br>Read the Usage section of this document for<br>information about Microsoft SQL Server/JDBC encryption<br>requirements. |
| Trim all the String/Char columns | Select this checkbox to remove leading and trailing whitespace from all the<br>String/Char columns. |
| Trim column | Select the checkbox(es) in the Trim column to remove<br>leading and trailing whitespace from the corresponding column(s).<br><br>This property<br>is not available if the Trim all the String/Char columns<br>checkbox is selected. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. |
| NB\_LINE | The number of rows processed. This is an After variable and<br>it returns an integer. |
| QUERY | The query statement being processed. This is a Flow variable<br>and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| Usage rules | This component is usually used a an start component of a Job or subJob and it<br>always needs an output link.<br><br>Information noteImportant: Microsoft SQL Server/JDBC encryption requirements<br><br>Starting with recent versions of the Microsoft SQL Server JDBC driver,<br>TLS encryption is enabled by default<br>(encrypt=true;trustServerCertificate=false). This<br>enhances security, but if your SQL Server does not support encrypted<br>connections or does not require clients to use TLS, you must set<br>encrypt=false in the JDBC parameters of this component<br>to connect successfully.<br><br><ul> <li> <p>For production or cloud environments using certificates signed by a                              trusted authority (e.g., Azure, AWS), no changes are needed, the                              default settings will work. </p> </li> <li> <p>For servers using self-signed certificates, use                                 <span>encrypt=true;trustServerCertificate=true</span> or                              specify the trust store details                                 (<span>encrypt=true;trustStore=&lt;your_trust_store&gt;;trustStorePassword=&lt;your_trust_store_password&gt;</span>).                           </p> </li> <li> <p>For non-secure development or test servers, set                                 <span>encrypt=false</span> in the additional JDBC parameters.                           </p> </li> </ul><br><br>For more information on how to use connections with encryption<br>properties, see [Microsoft SQL JDBC documentation](https://learn.microsoft.com/en-us/sql/connect/jdbc/connecting-with-ssl-encryption?view=sql-server-ver17). |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | Note that some<br>features that are supported by other databases are not supported by<br>Azure Synapse Analytics. For more information, see [Unsupported table<br>features](https://docs.microsoft.com/en-us/azure/sql-data-warehouse/sql-data-warehouse-tables-overview#unsupported-table-features). |
