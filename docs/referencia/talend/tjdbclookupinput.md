# tjdbclookupinput (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tjdbclookupinput  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tjdbclookupinput -->

# tJDBCLookupInput (deprecated)

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

Reads a database and extracts fields based on a query.

Information noteDeprecation: Spark Streaming is deprecated beginning with the R2026-09 release. Use Spark Structured Streaming instead.

It passes on the extracted data to tMap in order to provide the lookup data to the main flow. It must be directly connected to a tMap component and requires this tMap to use Reload at each row or Reload at each row (cache) for the lookup flow.

This component also allows you to connect and read data from a RDS MariaDB, a RDS PostgreSQL or a RDS SQLServer database.

## tJDBCLookupInput properties for Apache Spark Streaming

These properties are used to configure tJDBCLookupInput running in the Spark Streaming Job framework.

The Spark Streaming tJDBCLookupInput component belongs to the Databases family.

The component in this framework is available in Talend Real-Time Big Data Platform and in Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p>Either <span>Built-In</span> or <span>Repository</span>. </p> </li> <li> <p> <span>Built-In</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the            properties are stored.</p> </li> </ul> |
| Use an existing<br>connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined. |
| JDBC URL | The JDBC URL of the database to be used. For example, the JDBC URL for the Amazon Redshift database is jdbc:redshift://endpoint:port/database.<br><br>If you are using Spark V1.3, this URL should contain the authentication information, such as:<br><br>```<br>jdbc:mysql://XX.XX.XX.XX:3306/Talend?user=ychen&password=talend<br>``` |
| Driver JAR | Complete this table to load the driver JARs needed. To do<br>this, click the [+] button under the table to add<br>as many rows as needed, each row for a driver JAR, then select the cell and click the<br>[...] button at the right side of the cell to<br>open the Module dialog box from which you can select the driver JAR<br>to be used. For example, the driver jar RedshiftJDBC41-1.1.13.1013.jar for the Redshift database.<br><br>For more information, see [Importing a database driver](https://help.qlik.com/talend/r/en-US/8.0/components/jdbc/importing-database-driver). |
| Class Name | Enter the class name for the specified driver between double<br>quotation marks. For example, for the RedshiftJDBC41-1.1.13.1013.jar driver, the name to be entered is<br>com.amazon.redshift.jdbc41.Driver. |
| Username and Password | Enter the authentication information to the database you need to connect to.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings.<br><br>Available only for Spark V1.4. and onwards. |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> </ul> |
| Table Name | Type in the name of the table from which you need to read data. |
| Query type and<br>Query | Specify the database query statement paying particularly attention to the sequence of the fields which must correspond to the schema definition.<br><br>The result of the query must contain only records that match join key you need to use in<br>tMap. In other words, you must use the schema of the<br>main flow to tMap to construct the SQL statement here in<br>order to load only the matched records into the lookup flow.<br><br>This approach ensures that no redundant records are loaded into memory and outputted to<br>the component that follows. |
| Guess Query | Click the Guess Query button to generate the query which<br>corresponds to your table schema in the Query field. |
| Guess schema | Click the Guess schema button to retrieve the table<br>schema. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Additional JDBC<br>parameters | Specify additional connection properties for the database connection you are<br>creating. The properties are separated by semicolon and each property is a key-value<br>pair, for example, *encryption=1;clientname=Talend*.<br><br>This field is not available if the Use an existing<br>connection check box is selected. |
| Connection pool | In this area, you configure, for each Spark executor, the connection pool used to control<br>the number of connections that stay open simultaneously. The default values given to the<br>following connection pool parameters are good enough for most use cases.<br><br><ul> <li> <p> <span>Max total number of connections</span>: enter the maximum number            of connections (idle or active) that are allowed to stay open simultaneously.</p> <p>The default number is <em>8</em>. If you enter <em>-1</em>, you allow unlimited number of open connections at the same                time.</p> </li> <li> <p> <span>Max waiting time (ms)</span>: enter the maximum amount of time                    at the end of which the response to a demand for using a connection should be returned by                    the connection pool. By default, it is -1, that is to say, infinite.</p> </li> <li> <p> <span>Min number of idle connections</span>: enter the minimum number                        of idle connections (connections not used) maintained in the connection pool.</p> </li> <li> <p> <span>Max number of idle connections</span>: enter the maximum number                            of idle connections (connections not used) maintained in the connection pool.</p> </li> </ul> |
| Evict connections | Select this check box to define criteria to destroy connections in the connection pool. The<br>following fields are displayed once you have selected it.<br><br><ul> <li> <p> <span>Time between two eviction runs</span>: enter the time interval                                    (in milliseconds) at the end of which the component checks the status of the connections and                                    destroys the idle ones.</p> </li> <li> <p> <span>Min idle time for a connection to be eligible to                                            eviction</span>: enter the time interval (in milliseconds) at the end of which the idle                                        connections are destroyed.</p> </li> <li> <p> <span>Soft min idle time for a connection to be eligible to                                                eviction</span>: this parameter works the same way as <span>Min idle                                                    time for a connection to be eligible to eviction</span> but it keeps the minimum number                                            of idle connections, the number you define in the <span>Min number of idle                                                connections</span> field.</p> </li> </ul> |
| Trim column | This table is filled automatically with the schema being used. Select the check<br>box(es) corresponding to the column(s) to be trimmed. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as a start component and requires an output link.<br><br>This component should use a tJDBCConfiguration component present in the same Job to connect to a database. You need to drop a tJDBCConfiguration component alongside this component and configure the Basic settings of this component to use tJDBCConfiguration.<br><br>This component, along with the Spark Streaming component Palette it belongs to, appears<br>only when you are creating a Spark Streaming Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a scenario presents<br>only Standard Jobs, that is to say traditional<br>Talend<br>data<br>integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |
