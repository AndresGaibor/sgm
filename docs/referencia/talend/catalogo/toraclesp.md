# toraclesp

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/toraclesp  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/toraclesp -->

# tOracleSP

Calls an Oracle database stored procedure.

tOracleSP offers a convenient way to centralize multiple or complex queries in a database and call them easily.

## tOracleSP Standard properties

These properties are used to configure tOracleSP running in the Standard Job framework.

The Standard tOracleSP component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined.<br><br>Note that connections that are of<br>WALLET type are for the tCreateTable component, the tOracleInput<br>component, and the tOracleOutput component only. Make sure that the connection selected is<br>not of the WALLET type to prevent possible errors.<br><br>Information noteNote: When a Job contains the parent Job and the child Job, do the following if you<br>want to share an existing connection between the parent Job and the child Job (for example,<br>to share the connection created by the parent Job with the child Job).<br><br><ol> <li>In the parent level, register the database connection to be shared               in the <span>Basic settings</span> view of the               connection component which creates that very database connection. </li> <li>In the child level, use a dedicated connection component to read               that registered database connection. </li> </ol><br><br>For an example about how to share a database connection across Job levels,<br>see [Sharing a database connection](https://help.qlik.com/talend/r/en-US/7.3/studio-user-guide/sharing-database-connection). |
| Connection type | Drop-down list of available drivers:<br><br><br>Oracle OCI: Select this connection<br>type to use Oracle Call Interface with a set of C-language software<br>APIs that provide an interface to the Oracle database.<br><br><br>Oracle Service Name: Select this<br>connection type to use the TNS alias that you give when you connect<br>to the remote database.<br><br><br>Oracle SID: Select this connection<br>type to uniquely identify a particular database on a system.<br><br><br>Oracle Custom: Select this<br>connection type to access a clustered database. |
| Property type | <ul> <li> <p> <span>Either <span>Built-in</span> or										<span>Repository</span> </span>.</p> </li> <li> <p> <span>Built-in</span>: No property data stored								centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository								file in which the properties are stored. The fields that follow are								completed automatically using the data retrieved.</p> </li> </ul> |
| DB Version | Select the Oracle version in use. |
| Host | Database server IP address. |
| Port | Listening port number of DB server. |
| Database | Name of the database. |
| Schema | Name of the schema. |
| Username and<br>Password | DB user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description, it defines the number of fields to								be processed and passed on to the next component. The schema is								either <span>Built-in</span> or stored remotely								in the <span>Repository</span>. </p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| SP Name | Type in the exact name of the Stored Procedure (or<br>Function) |
| Is Function / Return result<br>in | Select this check box, if the stored procedure is a function and<br>one value only is to be returned.<br><br>Select on the list the schema column, the value to be returned is<br>based on. |
| Parameters | <ul> <li> <p>Click the Plus button and select the various <span>Schema Columns</span> that will be required by the								procedures. Note that the SP schema can hold more columns than there								are parameters used in the procedure.</p> </li> <li> <p>Select the <span>Type</span> of								parameter:</p> <p> <span>IN</span>: Input parameter.</p> <p> <span>OUT</span>: Output parameter/return								value.</p> <p> <span>IN OUT</span>: Input parameter is to be								returned as value, likely after modification through the procedure								(function).</p> <p> <span>RECORDSET</span>: Input parameter is to								be returned as a set of values, rather than single value.</p> <div><span>Information note</span><span>Note:</span> <p>Check <a href="https://help.qlik.com/talend/en-US/components/8.0/mysql/tmysqlconnection-tmysqlrollback-tfileinputdelimited-inserting-data-in-mother-daughter-tables-standard-component-the" target="_blank">Inserting data in mother/daughter tables</a> if you want to analyze a set									of records from a database table or DB query and return single									records.</p> </div> </li> <li> <p>The <span>Custom Type</span> is used when a									<span>Schema Column</span> you want to use								is user-defined. Two <span>Custom Type</span>								columns are available in the <span>Parameters</span> table. In the first <span>Custom Type</span> column:</p> <p> - Select the check box in the <span>Custom Type								</span>column when the corresponding <span>Schema Column</span> you want to use is of user-defined								type. </p> <p> - If all listed <span>Schema Columns</span>								in the <span>Parameters</span> table are of								custom type, you can select the check box before <span>Custom Type</span> once for them all.</p> </li> <li> <p>Select a database type from the <span>DB									Type</span> list to map the source database type to the								target database type: </p> <p> <span>- Auto-Mapping</span>: Map the source								database type to the target database type								automatically.(default)</p> <p> <span>- CLOB</span>: Character large								object.</p> <p> <span>- BLOB</span>: Binary large object.</p> <p> <span>- DECIMAL</span>: Decimal numeric								object.</p> <p> <span>- NUMERIC</span>: Character 0 to 9.</p> <p> <span>- XMLTYPE</span>: XML schema								type.</p> <div><span>Information note</span><span>Warning:</span> <p>When mapping a column selected from the <span>Return result in</span> list box or set to the IN or									OUT type of parameter to XMLTYPE, make sure that the column is									of type String in the schema.</p> </div> </li> <li> <p>In the second <span>Custom Type </span>column,								you can precise what the custom type is. The type may be:</p> <p> - <span>STRUCT</span>: used for one element. </p> <p> - <span>ARRAY</span>: used for a collection								of elements.</p> </li> <li> <p>In the <span>Custom name</span> column,								specify the name of the custom type that you have given to this								type.</p> <div><span>Information note</span><span>Warning:</span> <p> <em>When an OUT parameter uses the custom type, make sure										that its corresponding Schema Column has chosen the Object										type in the schema table.</em> </p> </div> </li> </ul> |
| Specify a data source alias | Select this checkbox and specify the alias of a data source created on the *Talend Runtime* side to use the shared connection pool defined in the data source configuration. This<br>option works only when you deploy and run your Job in *Talend Runtime*. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC parameters | Specify additional connection properties for the DB connection you<br>are creating. This option is not available if you have selected the<br>Use an existing connection<br>check box in the Basic<br>settings. |
| NLS Language | In the list, select the language used for the data that are not<br>used in Unicode. |
| NLS Territory | Select the conventions used for date and time formats. The default<br>value is that of the operating system. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a<br>Job level as well as at each component level. |
| Support NLS | Select this option to enable globalization support. See [Overview of Globalization Support](https://docs.oracle.com/en/database/oracle/oracle-database/21/nlspg/overview-of-globalization-support.html) for<br>related information.<br><br>This option is available when the Use an existing<br>connection option is cleared and Oracle 18 and<br>above is selected from the DB Version<br>drop-down list in the Basic settings view.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-09<br>Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as intermediary component. It can be used<br>as start component but only input parameters are thus<br>allowed. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
| Limitation | The Stored Procedures syntax should match the Database<br>syntax.<br><br>When the parameters set in this component are of Custom Type, the tJava family components should be placed before the<br>component in order for users to define values for the custom-type<br>parameters, or after the component so as to read and output the<br>Out-type custom<br>parameters. |

**Related concepts**

* [Checking number format using a stored procedure](https://help.qlik.com/talend/en-US/components/8.0/toracleconnection-toracleinput-toraclesp-tlogrow-checking-number-format-using-stored-procedure-standard-component-the)
