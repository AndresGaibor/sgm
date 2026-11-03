# tmssqloutputbulk

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tmssqloutputbulk  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmssqloutputbulk -->

# tMSSqlOutputBulk

Prepares the file to be used as parameter in the INSERT query to feed the MSSql database.

The tMSSqlOutputBulk and tMSSqlBulkExec components are used together in a two step process. In the first step, an output file is generated. In the second step, this file is used in the INSERT operation used to feed a database. These two steps are fused together in the tMSSqlOutputBulkExec component, detailed in a separate section. The advantage of using a two step process is that the data can be transformed before it is loaded in the database.

tMSSqlOutputBulk writes a file with columns based on the defined delimiter and the MSSql standards.

## tMSSqlOutputBulk Standard properties

These properties are used to configure tMSSqlOutputBulk running in the Standard Job framework.

The Standard tMSSqlOutputBulk component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

Information noteNote: When building a Job as an OSGI Bundle for ESB, MS SQL Server drivers jtds and mssql-jdbc used by the SQL Server components are not included in the build artifact. To run the artifact in Talend Runtime, you need to deploy the drivers manually by copying the drivers to the &lt;TalendRuntimePath&gt;/lib folder and restart Talend Runtime.

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Property type | Either Built-in or<br>Repository<br>.<br><br><ul> <li> <span>Built-in</span>: No property data stored                        centrally.</li> <li> <span>Repository</span>: Select the repository                        file in which the properties are stored. The fields that follow are                        completed automatically using the data retrieved.</li> </ul> |
| File Name | Enter the name of the file to be generated.<br><br>Information noteNote: This file can<br>be on the same machine as the database server resides or on another machine. If<br>the file is on the same machine as the database server resides, fill the path<br>to the file in the form prompted in the field; if the file is on another<br>machine, fill the universal naming convention (UNC) name (that is,<br>\\{Servername}\{Sharename}\{Path}\{Filename}) of the<br>file in this field. In the second case, you need to have the permission to<br>write the file. See [Bulk importing to SQL Server from a remote<br>data file](https://docs.microsoft.com/en-us/sql/relational-databases/import-export/import-bulk-data-by-using-bulk-insert-or-openrowset-bulk-sql-server?view=sql-server-ver16#bulk-importing-to-sql-server-from-a-remote-data-file) for related information. |
| Append | Select this checkbox to add the new rows at the end of the<br>records. |
| Schema and Edit Schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><br>Built-In: You create and store the schema locally for this component<br>only.<br><br><br>Repository: You have already created the schema and stored it in the<br>Repository. You can reuse it in various projects and Job designs.<br><br>When the schema to be reused has default values that are<br>integers or functions, ensure that these default values are not enclosed within<br>quotation marks. If they are, you must remove the quotation marks manually.<br><br>For more information, see [Retrieving table schemas](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg).<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Authenticate using Azure Active<br>Directory | When selected, this option allows you to pick the authentication mode to use<br>from the Azure Active Directory authentication mode<br>dropdown list:<br><br><ul> <li><span>Service principal (client secret)</span>: use the service                        principal credentials (client ID and client secret) to authenticate.</li> <li><span>User password</span>: use the Azure Active Directory user                        credentials (username and password) to authenticate.</li> </ul><br><br>Read the Usage section of this document for<br>information about Microsoft SQL Server/JDBC encryption<br>requirements. |
| Row separator | String (ex: "\n"on Unix) to distinguish rows. |
| Field separator | Character, string, or regular expression to separate fields. |
| Include header | Select this check to include the column header. |
| Encoding | Select the encoding from the list or select Custom and define it manually. This field is compulsory for DB<br>data handling. |
| tStaCatcher statistics | Select this checkbox to collect log data at the component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| Usage rules | This component is to be used along with tMSSqlBulkExec component. Used together they offer gains in<br>performance while feeding an MSSql database.<br><br>Information noteImportant: Microsoft SQL<br>Server/JDBC encryption requirements<br><br>Starting with recent versions of the<br>Microsoft SQL Server JDBC driver, TLS encryption is enabled by default<br>(encrypt=true;trustServerCertificate=false). This<br>enhances security, but if your SQL Server does not support encrypted<br>connections or does not require clients to use TLS, you must set<br>encrypt=false in the JDBC parameters of this component<br>to connect successfully.<br><br><ul> <li> <p>For production or cloud environments using certificates signed by a                              trusted authority (e.g., Azure, AWS), no changes are needed, the                              default settings will work. </p> </li> <li> <p>For servers using self-signed certificates, use                                 <span>encrypt=true;trustServerCertificate=true</span> or                              specify the trust store details                                 (<span>encrypt=true;trustStore=&lt;your_trust_store&gt;;trustStorePassword=&lt;your_trust_store_password&gt;</span>).                           </p> </li> <li> <p>For non-secure development or test servers, set                                 <span>encrypt=false</span> in the additional JDBC parameters.                           </p> </li> </ul><br><br>For more information on how to use connections with encryption<br>properties, see [Microsoft SQL JDBC documentation](https://learn.microsoft.com/en-us/sql/connect/jdbc/connecting-with-ssl-encryption?view=sql-server-ver17). |
| Component family | Databases/MS SQL Server |
