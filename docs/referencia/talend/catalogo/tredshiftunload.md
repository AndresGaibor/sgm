# tredshiftunload

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tredshiftunload  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tredshiftunload -->

# tRedshiftUnload

Unloads data on Amazon Redshift to files on Amazon S3.

This component runs a specified query in Amazon Redshift and then unloads the result of the query to one or more files on Amazon S3.

## tRedshiftUnload Standard properties

These properties are used to configure tRedshiftUnload running in the Standard Job framework.

The Standard tRedshiftUnload component belongs to the Cloud and the Databases families.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property Type | Either Built-In or<br>Repository.<br><br><ul> <li> <p> <span>Built-In</span>:                                    No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file in which the                                    properties are stored. The database connection fields that                                    follow are completed automatically using the data retrieved.</p> </li> </ul> |
| Use an existing<br>connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined. |
| Driver version | Select the Redshift driver version to be used: Driver v1 or<br>Driver v2.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-04<br>Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Host | Type in the IP address or hostname of the database<br>server. |
| Port | Type in the listening port number of the database<br>server. |
| Database | Type in the name of the database. |
| Schema | Type in the name of the schema. |
| Username and<br>Password | Type in the database user authentication data.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Use String JDBC parameters | Set JDBC properties in a string. If you select this option, enter your JDBC parameter string in<br>the Additional JDBC Parameters field; otherwise, enter JDBC<br>properties and property values in the Additional JDBC<br>Parameters table.<br><br>This option is not available if Driver v1 is selected from<br>the Driver version drop-down list.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-04<br>Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Additional JDBC<br>Parameters | Specify additional JDBC properties for the connection you are creating. The<br>properties are separated by ampersand & and each property is a key-value pair. For<br>example, *ssl=true &<br>sslfactory=com.amazon.redshift.ssl.NonValidatingFactory*, which means the<br>connection will be created using SSL.<br><br>This field is not available if Driver v2 is selected<br>from the Driver version drop-down list and the<br>Use String JDBC parameters option is not<br>selected. |
| Additional JDBC Parameters (table) | Specify JDBC properties in table rows.<br><br>To specify a JDBC property, add a row in the table by clicking the plus button on<br>the bottom of this table, enter the property name in the<br>Key column, and then enter the property value in the<br>Value column.<br><br>This table is available when Driver v2 is selected from the<br>Driver version drop-down list and the Use<br>String JDBC parameters option is not selected.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-04<br>Talend Studio<br>Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Table Name | Type in the name of the table from which the data will be<br>read. |
| Schema and<br>Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><br>Built-In: You create and store the schema locally for this component<br>only.<br><br><br>Repository: You have already created the schema and stored it in the<br>Repository. You can reuse it in various projects and Job designs.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Query Type and<br>Query | Enter the database query paying particularly attention to<br>the proper sequence of the fields in order to match the schema<br>definition.<br><br>Double-escape each simple quotation marks in the query.<br>For example,<br><br>```<br>SELECT name, birth,\"Add\" FROM my_table WHERE birth between \\'2018-01-01 00:00:00\\' and \\'2019-01-01 00:00:00\\'<br>``` |
| Guess Query | Click the button to generate the query which corresponds<br>to the table schema in the Query<br>field. |
| Use an existing S3<br>connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined. |
| Access Key | Specify the Access Key ID that uniquely identifies an<br>AWS Account. For how to get your Access Key and Access Secret, visit<br>[Getting Your AWS Access<br>Keys](http://docs.aws.amazon.com/ses/latest/DeveloperGuide/get-aws-keys.html).<br><br>This option is not available if Use an existing S3 connection is<br>selected. |
| Secret Key | Specify the Secret Access Key, constituting the security<br>credentials in combination with the access Key.<br><br>To enter the secret key, click the [...]<br>button next to the secret key field, and then in the pop-up dialog box enter the password<br>between double quotes and click OK to save the<br>settings.<br><br>This option is not available if Use an existing S3 connection is<br>selected. |
| Assume Role | Select this checkbox and specify the values for the<br>following parameters used to create a new assumed role session.<br><br><ul> <li> <p> <span>IAM Role ARNs chains</span>: a series of                                chained roles, which may belong to other accounts, that your cluster                                can assume to access resources. </p> <p>You can chain a maximum of 10 roles.</p> </li> <li> <p> <span>Role ARN</span>: the Amazon Resource Name                                (ARN) of the role to assume. </p> </li> </ul><br><br>This option is not available if Use an existing S3 connection is<br>selected.<br><br>For more information on IAM<br>Role ARNs chains, see [Authorizing Redshift service](https://docs.aws.amazon.com/redshift/latest/mgmt/authorizing-redshift-service.html). |
| Bucket | Type in the name of the Amazon S3 bucket, namely the top<br>level folder, to which the data is unloaded. |
| Key prefix | Type in the name prefix for the unload files on Amazon<br>S3. By default, the unload files are written per slice of the Redshift<br>cluster and the file names are written in the format &lt;object\_path&gt;/&lt;name\_prefix&gt;&lt;slice-number&gt;\_part\_&lt;file-number&gt;. |

## Advanced settings

| Properties | Description |
| --- | --- |
| File type | Select the type of the unload files on Amazon S3 from the list:<br><br><ul> <li> <p> <span>Delimited file or CSV</span>: a delimited/CSV file.</p> </li> <li> <p> <span>Fixed width</span>: a fixed-width file.</p> </li> <li> <p> <span>Apache Parquet</span>: an Apache Parquet file.</p> </li> </ul> |
| Fields terminated<br>by | Enter the character used to separate fields.<br><br>This field appears only when Delimited file or CSV is selected from the File type list. |
| Enclosed by | Select the character in a pair of which the fields are<br>enclosed.<br><br>This list appears only when Delimited file or CSV is selected from the File type list. |
| Fixed width<br>mapping | Enter a string that specifies a user-defined column<br>label and column width between double quotation marks. The format of the<br>string is:<br><br><br>ColumnLabel1:ColumnWidth1,ColumnLabel2:ColumnWidth2,....<br><br>Note that the column label in the string has no relation<br>to the table column name and it can be either a text string or an<br>integer. The order of the label/width pairs must match the order of the<br>table columns exactly.<br><br>This field appears only when Fixed width is selected from the File type list. |
| Compressed<br>by | Select this check box and from the list displayed select<br>the compression type of the files. |
| Encrypt | Select this check box to encrypt unload file(s) using Amazon<br>S3 client-side encryption. In the Encryption<br>key field displayed, enter the encryption key used to encrypt<br>the unload file(s).<br><br>Note that only a base64 encoded AES 128-bit or AES 256-bit<br>envelope key is supported. For more information, see [Unloading Encrypted Data Files](http://docs.aws.amazon.com/redshift/latest/dg/t_unloading_encrypted_files.html).<br><br>Because client-side encryption for Parquet files is not supported, this option only<br>works for delimited/CSV files and fixed-width files.<br><br>This option is not available if Use an existing S3 connection is selected. |
| Specify null<br>string | Select this check box and from the list displayed select<br>a string that represents a null value in unload files. |
| Escape | Select this check box to place an escape character (\)<br>before every occurrence of the following characters for CHAR and VARCHAR<br>columns in the delimited unload files: linefeed (\n), carriage return<br>(\r), the delimiter character specified for the unloaded data, the<br>escape character (\), a quote character (" or '). |
| Overwrite s3 object if<br>exist | Select this check box to overwrite the existing Amazon<br>S3 object files. |
| Parallel | Select this check box to write data in parallel to<br>multiple unload files on Amazon S3 according to the number of slices in<br>the Redshift cluster. |
| JDBC<br>url | Select a way to access to an Amazon Redshift database from the<br>JDBC url drop-down list.<br><br><ul> <li> <span>Standard</span>: Use the          standard way to access the Redshift database.</li> <li> <span>SSO</span>: Use the IAM          Single Sign-ON (SSO) authentication way to access the Redshift Database. Before selecting          this option, ensure that the IAM role added to your Redshift cluster has appropriate          access rights and permissions to this cluster. You can ask the administrator of your AWS          services for more details.<p>This option is available only when <span>Use an existing connection</span> check box is not selected from            the <span>Basic settings</span>. </p> </li> </ul> |
| tStatCatcher<br>Statistics | Select this check box to gather the Job processing<br>metadata at the Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global<br>Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage<br>rule** | This component covers all possible<br>SQL queries for the Amazon Redshift database. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>The Dynamic settings table is<br>available only when the Use an existing<br>connection check box is selected in the Basic settings view. Once a dynamic parameter is<br>defined, the Component List box in the<br>Basic settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |

**Related concepts**

* [Loading/unloading data to/from Amazon S3](https://help.qlik.com/talend/en-US/components/8.0/tredshiftinput-tredshiftbulkexec-ts3get-loading-unloading-data-to-from-amazon-s3-standard-component-this)
