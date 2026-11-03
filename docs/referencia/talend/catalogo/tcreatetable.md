# tcreatetable

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tcreatetable  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tcreatetable -->

# tCreateTable

Creates a table for a specific type of database.

## tCreateTable Standard properties

These properties are used to configure tCreateTable running in the Standard Job framework.

The Standard tCreateTable component belongs to the Databases family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Database Type | Select the type of the database. The connection properties may differ slightly<br>according to the database type selected. |
| Property Type | Select the way the connection details<br>will be set.<br><br><ul> <li> <p> <span>Built-In</span>: The connection details will be set                                locally for this component. You need to specify the values for all                                related connection properties manually.</p> </li> <li> <p> <span>Repository</span>: The connection details stored                                centrally in <span><span>Repository</span><abbr> &gt; </abbr><span>Metadata</span></span> will be reused by this component. </p> <p>You need to click                                the <span>[...]</span> button next to it and in the pop-up                                    <span>Repository Content</span> dialog box, select the                                connection details to be reused, and all related connection                                properties will be automatically filled in.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>When a Job contains the parent Job and the child Job, if you need to<br>share an existing connection between the two levels, for example, to share the<br>connection created by the parent Job with the child Job, you have to:<br><br><ol> <li> <p>In the parent level, register the database connection to be shared                in the <span>Basic settings</span> view of the connection                component which creates that very database connection.</p> </li> <li> <p>In the child level, use a dedicated connection component to read                that registered database connection.</p> </li> </ol><br><br>For an example about how to share a database connection across Job levels, see<br>[Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| JDBC Provider | Select the provider of the JDBC driver to be used, either Microsoft (the default, recommended) or Open<br>source JTDS.<br><br>When Microsoft is selected, you need to download the<br>Microsoft JDBC Driver for SQL Server on [Microsoft Download<br>Center](https://www.microsoft.com/en-us/download/details.aspx?id=11774), unpack the downloaded zip file, choose a jar in the<br>unzipped folder based on your JRE version, rename the jar to *mssql-jdbc.jar* and install it manually. For more<br>information about choosing the jar, see the System Requirements<br>information on [Microsoft Download<br>Center](https://www.microsoft.com/en-us/download/details.aspx?id=11774).<br><br>When using this component with Datasource in Talend Runtime, you need<br>to use the Open source JTDS driver.<br><br>This option is available when MSSQLServer is selected from the Database Type drop-down list. |
| DB Version | Select the version of the database. |
| Host | Enter the IP address or the hostname of the database.<br><br>If you select<br>MSSQLServer from the Database<br>Type dropdown list, enter the IP address or the hostname of the<br>database server or the Azure Synapse Analytics to be used in<br>this field. If the SQL Server Browser service is running on<br>the machine where the MSSQL server resides, you can connect to a named instance<br>through a TCP dynamic port by providing the host name and the instance name in<br>this field in the format of {host\_name}\{instance\_name}.<br>In this case, you can leave the Port field empty. See<br>[SQL Server Browser service](https://docs.microsoft.com/en-us/sql/tools/configuration-manager/sql-server-browser-service?view=sql-server-ver16) for related<br>information. |
| Port | Enter the listening port number of the database.<br><br>If you select<br>MSSQLServer from the Database<br>Type dropdown list, enter the listening port number of the<br>database server or the Azure Synapse Analytics to be used in<br>this field. If the SQL Server Browser service is running on<br>the machine where the server resides, you can connect to a named instance<br>through a TCP dynamic port by providing the host name and the instance name in<br>the Host field and leave this field empty. See [SQL Server Browser service](https://docs.microsoft.com/en-us/sql/tools/configuration-manager/sql-server-browser-service?view=sql-server-ver16) for related<br>information. |
| Database name | Enter the name of the database. |
| Schema | Enter the name of the database schema.<br><br>This property is<br>available for DB2, Exasol, Greenplum, Informix, MS SQL Server, Oracle,<br>PostgreSQL, Redshift, Sybase, and Vertica database types. |
| Access File | Enter the path to the Access database file. |
| Firebird File | Enter the path to the Firebird database file. |
| Interbase File | Enter the path to the Interbase database file. |
| SQLite File | Enter the path to the SQLite database file. |
| Running Mode | Select the Server Mode that corresponds to your database setup.<br><br>This property is available only for the HSQLDb database type. |
| Use TLS/SSL Sockets | Select this checkbox to enable the security mode if required.<br><br>This property is available only for the HSQLDb database type. |
| DB Alias | Enter the name of the database.<br><br>This property is available only for the HSQLDb database type. |
| Framework Type | Select the framework type for your database.<br><br>This property is available only for the JavaDb database type. |
| DB Root Path | Browse to your database root.<br><br>This property is available only for the JavaDb database type. |
| ODBC Name | Enter the name of the ODBC database. |
| Connection Type | Select the Oracle database connection type.<br><br><ul> <li> <p> <span>Oracle SID</span>: select this connection type to uniquely                  identify a particular database on a system.</p> </li> <li> <p> <span>Oracle Service</span>: select this connection type to use the TNS                  alias that you give when you connect to the remote database.</p> </li> <li> <p> <span>Oracle OCI</span>: select this connection type to use Oracle Call                  Interface with a set of C-language software APIs that provide an interface to the                  Oracle database.</p> </li> <li> <p> <span>Oracle Custom</span>: select this connection type to access a                  clustered database.</p> </li> <li> <p> <span>WALLET</span>: select this connection type to store credentials                  in an Oracle wallet.</p> </li> </ul> |
| Account | In the Account field, enter, in double<br>quotation marks, the account name that has been assigned to you by Snowflake.<br><br>This property is available only for the Snowflake database type. |
| UserName and Password | Enter the database user authentication data.<br><br>To enter the password, click the [...] button next to the<br>Password field, enter the password in double quotes<br>in the pop-up dialog box, and then click OK.<br><br>If you select MSSQLServer from the<br>Database Type dropdown list, you can use<br>Type 2 integrated authentication on<br>Windows by adding<br>integratedSecurity=true in the Additional<br>JDBC Parameters field and leave these two fields empty. See<br>section *Connecting with integrated authentication On Windows* at<br>[Building the connection URL](https://docs.microsoft.com/en-us/sql/connect/jdbc/building-the-connection-url?redirectedfrom=MSDN) for related<br>information. |
| Role | Enter, in<br>double quotation marks, the default access control role to use to initiate the<br>Snowflake session.<br><br>This role must already exist and<br>has been granted to the user ID you are using to connect to Snowflake. If this field<br>is left empty, the PUBLIC role is automatically granted. For information about<br>Snowflake access control model, see [Understanding the Access Control<br>Model](https://docs.snowflake.net/manuals/user-guide/security-access-control.html).<br><br>This property is available only for the Snowflake database type. |
| Table name | Enter the name of the table to be created. |
| Table Action | Select the action to be carried out on the table.<br><br><ul> <li> <p> <span>Create table</span>: the specified table doesn't exist and gets created.</p> </li> <li> <p> <span>Create table if not exists</span>: the specified table is created if it does not exist.</p> </li> <li> <p> <span>Drop table if exits and create</span>: the table is removed if it already exists and gets created again.</p> </li> </ul> |
| Temporary Table | Select this checkbox to create a temporary table during an operation, which<br>is automatically dropped at the end of the operation. Since temporary tables exist<br>in a special schema, you cannot specify a schema name when creating a temporary<br>table, and the name of the temporary table must be distinct from the name of any<br>other table, sequence, index, and view in the same schema.<br><br>Note that once you<br>select to create a temporary table, you should empty the values when you edit<br>schema.<br><br>This field is available only when<br>Postgresql is selected from the Database<br>Type dropdown list. |
| Unlogged Table | Select this checkbox to create an unlogged table during an operation. This<br>way, data is loaded considerably faster than an ordinary table where the data is<br>logged and then written. However, the data in an unlogged table is not<br>crash-safe.<br><br>This field is available only when<br>Postgresql is selected from the Database<br>Type dropdown list and Temporary Table is<br>not selected. |
| Case Sensitive | Select this checkbox to make the table/column name case sensitive.<br><br>This property is available only for the HSQLDb database type. |
| Temporary Table | Select this checkbox if you want to save the created table temporarily.<br><br>This property is available only for the MySQL database type. |
| Create | Select the type of the table to be created.<br><br><ul> <li> <p> <span>SET TABLE</span>: the table that does not allow duplicate rows.</p> </li> <li> <p> <span>MULTISET TABLE</span>: the table that allows duplicate rows.</p> </li> </ul><br><br>This property is available only for the Teradata database type. |
| Schema and Edit Schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>When the schema to be reused has default values that are<br>integers or functions, ensure that these default values are not enclosed within<br>quotation marks. If they are, you must remove the quotation marks manually.<br><br>For more information, see [Retrieving table schemas](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg).<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC Parameters | Specify additional connection properties for the DB connection you are<br>creating. This option is not available if you have selected the Use an<br>existing connection checkbox in the Basic<br>settings.<br><br>This property is available for the AS/400 and MSSQL<br>Server database types. |
| Authenticate using Azure Active<br>Directory | When selected, this option allows you pick the authentication mode to use<br>from the Azure Active Directory authentication mode<br>dropdown list:<br><br><ul> <li><span>Service principal (client secret)</span>: use the service                        principal credentials (client ID and client secret) to authenticate.</li> <li><span>User password</span>: use the Azure Active Directory user                        credentials (username and password) to authenticate.</li> </ul><br><br>This option is available when<br>MSSQLServer is selected from the Database<br>Type dropdown list and Microsoft is<br>selected from the JDBC Provider dropdown list in the<br>Basic settings view. |
| Create projection | Select this checkbox to create a projection.<br><br>This property is available<br>only for the Vertica database type. |
| Enforce database delimited identifiers | Select this checkbox to enable delimited identifiers.<br><br>This property is<br>available only for the Snowflake database<br>type.<br><br>For more information on delimited identifiers, see https://docs.intersystems.com/latest/csp/docbook/DocBook.UI.Page.cls?KEY=GSQL\_identifiers.<br><br>Information noteNote: If you use special characters in your column<br>names, select this checkbox to avoid possible errors or Job execution<br>failure. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| QUERY | The query statement being processed. This is a Flow variable<br>and it returns a string. |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| Usage rule | This component can be used as a standalone component of a Job or<br>subJob. |

**Related concepts**

* [Creating new table in a Mysql Database](https://help.qlik.com/talend/en-US/components/8.0/tcreatetable-creating-new-table-in-mysql-database-standard-component "The Job described below aims at creating a table in a database, made of a placeholder schema taken from a delimited file schema stored in the Repository. This Job is composed of a single component.")
