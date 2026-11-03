# tfileoutputdelimited (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tfileoutputdelimited  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfileoutputdelimited -->

# tFileOutputDelimited

Outputs the input data to a delimited file according to the defined schema.

### In this section

* [tFileOutputDelimited Standard properties](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited-standard-properties)
* [tFileOutputDelimited properties for Apache Spark Batch](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited-properties-for-apache-spark-batch)
* [tFileOutputDelimited properties for Apache Spark Streaming (deprecated)](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited-properties-for-apache-spark-streaming)

**Related concepts**

* [Utilizing Output Stream to save filtered data to a local file](https://help.qlik.com/talend/en-US/components/8.0/tfileoutputdelimited-tfileinputdelimited-tjava-tfileinputdelimited-tjava-utilizing-output-stream-to-save-filtered-data-to-local-file-standard-component-based-on)
* [Writing data in a delimited file](https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-writing-data-in-delimited-file-standard-component-this)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited-standard-properties -->

# tFileOutputDelimited Standard properties

These properties are used to configure tFileOutputDelimited running in the Standard Job framework.

The Standard tFileOutputDelimited component belongs to the File family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p>Either <span>Built-In</span> or <span>Repository</span>. </p> </li> <li> <p> <span>Built-In</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the            properties are stored.</p> </li> </ul> |
| Use Output Stream | Select this check box process the data flow of<br>interest. Once you have selected it, the Output<br>Stream field displays and you can type in the data flow of<br>interest.<br><br>The data flow to be processed must be added to the flow in order for this component to fetch<br>these data via the corresponding representative variable.<br><br>This variable can be already pre-defined in Talend Studio or provided by the context or the components you are using along with this<br>component; otherwise, you can define it manually and use it according to the<br>design of your Job, for example, using tJava or tJavaFlex.<br><br>In order to avoid the inconvenience of<br>hand writing, you could select the variable of interest from the<br>auto-completion list (Ctrl+Space) to fill<br>the current field on condition that this variable has been properly<br>defined.<br><br>For further information about how to use a stream,<br>see [Reading data from a remote file in streaming mode](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfilefetch-tsleep-tlogrow-reading-data-from-remote-file-in-streaming-mode-standard-component-this). |
| File Name | Name or path to the output file and/or the variable<br>to be used.<br><br>This field becomes unavailable once you have<br>selected the Use Output Stream check<br>box.<br><br>For further information about how to define and use a<br>variable in a Job, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables).<br><br>Information noteWarning: Use absolute path (instead of relative path) for<br>this field to avoid possible errors. |
| Row Separator | The separator used to identify the end of a row. |
| Field Separator | Enter a character or a string to separate fields for the transferred data.<br><br>Information noteNote: With CSV options selected in the<br>Advanced settings view, the field<br>separator can only be a single character. In this case, if you enter multiple<br>characters in this field, only the first character acts as the field<br>separator. |
| Append | Select this check box to add the new rows at the end<br>of the file. |
| Include Header | Select this check box to include the column header to<br>the file. |
| Compress as zip file | Select this check box to compress the output file in<br>zip format. |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <p> </p> <p>This component offers the advantage of the                  dynamic schema feature. This allows you to retrieve unknown columns from source                  files or to copy batches of columns from a source without mapping each column                  individually. For further information about dynamic schemas, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema" target="_blank">Dynamic schema</a>.</p> <p>This            dynamic schema feature is designed for the purpose of retrieving unknown columns of a            table and is recommended to be used for this purpose only; it is not recommended for the            use of creating tables.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Sync columns | Click to synchronize the output file schema with the<br>input file schema. The Sync function only displays once the Row connection is linked with the output<br>component. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Advanced separator (for numbers) | Select this check box to change the separator used for numbers. By default, the thousands separator is a comma (*,*) and the decimal separator is a period (*.*).<br><br><br>Thousands separator: define separators<br>for thousands.<br><br><br>Decimal separator: define separators for<br>decimals. |
| CSV options | Select this check box to specify the following CSV parameters:<br><br><ul> <li> <p> <span>Escape char</span>: enter the escape character between double                quotation marks. </p> </li> <li> <p> <span>Text enclosure</span>: enter the enclosure character (only one                character) between double quotation marks. For example, <kbd>"""</kbd>                needs to be entered when double quotation marks (") are used as the enclosure                character.</p> </li> </ul><br><br>It is recommended to use standard escape character, that is "\".<br>Otherwise, you should set the same character for Escape char and<br>Text enclosure. For example, if the escape character is set to<br>"\", the text enclosure can be set to any other character. On<br>the other hand, if the escape character is set to other character rather than<br>"\", the text enclosure can be set to any other characters.<br>However, the escape character will be changed to the same character as the text<br>enclosure. For instance, if the escape character is set to "#"<br>and the text enclosure is set to "@", the escape character will<br>be changed to "@", not "#". |
| Create directory if not exists | This check box is selected by default. It creates the directory<br>that holds the output delimited file, if it does not already exist. |
| Split output in several files | In case of very big output files, select this check box to<br>divide the output delimited file into several files.<br><br><br>Rows in each output file: set the number<br>of lines in each of the output files. |
| Custom the flush buffer size | Select this check box to define the number of lines to write<br>before emptying the buffer.<br><br><br>Row Number: set the number of lines to<br>write. |
| Output in row mode | Select this check box to ensure atomicity of the flush so that<br>each row of data can remain consistent as a set and incomplete rows of data are<br>never written to a file.<br><br>This check box is mostly useful when using this component in<br>the multi-thread situation. |
| Encoding | Select the encoding from the list or select Custom<br>and define it manually. This field is compulsory for database data handling. The<br>supported encodings depend on the JVM that you are using. For more information, see<br>[https://docs.oracle.com](https://docs.oracle.com/). |
| Don't generate empty file | Select this check box if you do not want to generate empty<br>files. |
| Throw an error if the file already exist | Select this check box to throw an exception if the output file specified in the<br>File Name field on the Basic<br>settings view already exists.<br><br>Clear this check box to overwrite the existing file. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at<br>a Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>FILE\_NAME: the<br>name of the file being processed. This is a Flow variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | Use this component to write<br>a delimited file and separate fields using a field separator value.<br><br>This component does not support the use of tSetDynamicSchema. |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited-properties-for-apache-spark-batch -->

# tFileOutputDelimited properties for Apache Spark Batch

These properties are used to configure tFileOutputDelimited running in the Spark Batch Job framework.

The Spark Batch tFileOutputDelimited component belongs to the File family.

The component in this framework is available in all subscription-based Talend products with Big Data and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Define a storage configuration<br>component | Select the configuration component to be used to provide the configuration<br>information for the connection to the target file system such as HDFS.<br><br>If you leave this check box clear, the target file system is the local<br>system.<br><br>The configuration component to be used must be present in the same Job.<br>For example, if you have dropped a tHDFSConfiguration component in the Job, you can select it to write<br>the result in a given HDFS system. |
| Property type | <ul> <li> <p>Either <span>Built-In</span> or <span>Repository</span>. </p> </li> <li> <p> <span>Built-In</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the            properties are stored.</p> <p>The properties are stored centrally under the <span>Hadoop                Cluster</span> node of the <span>Repository</span>            tree.</p> <p>The fields that come after are pre-filled in using the fetched                            data.</p> <p>For more information about the <span>Hadoop            Cluster</span> node, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/managing-hadoop-metadata" target="_blank">Managing Hadoop connection metadata</a>.</p> </li> </ul> |
| ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Save_Icon.png) | Click this icon to open a database connection wizard and store the<br>database connection parameters you set in the component Basic<br>settings view.<br><br>For more information about setting up and storing database connection<br>parameters, see [Centralizing database metadata](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/centralizing-database-metadata). |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Folder | Browse to, or enter the path pointing to the data to be used in the file system.<br><br>Note that this path must point to a folder rather than a file.<br><br>The button for browsing does not work with the Spark Local mode; if you are using the other Spark Yarn modes that Talend Studio<br>supports with your distribution, ensure that you have properly configured the connection<br>in a configuration component in the same Job. Use the configuration component depending<br>on the filesystem to be used. |
| Action | Select an operation for writing data:<br><br><br>Create: Creates a file and write data<br>in it.<br><br><br>Overwrite: Overwrites the file<br>existing in the directory specified in the Folder field.<br><br>When you want to sort the rows, row order is not guaranteed with this<br>component. |
| Use OS line separator as row separator when CSV Row Separator is set<br>to CR, LF or CRLF | Select this check box to automatically select the appropriate row separator<br>for the OS on which you run the Job:<br><br><ul> <li>LF, for Linux</li> <li>CR or CRLF for Windows</li> </ul><br><br>If you leave the check box cleared, you can specify the row separator to<br>be used regardless of the OS.<br><br>This option is available only when you<br>select the CSV options check box from the<br>Advanced settings view. |
| Row separator | The separator used to identify the end of a row. |
| Field separator | Enter a character, a string, or a regular expression to separate<br>fields for the transferred data. |
| Include Header | Select this check box to include the column header to the file. |
| Custom encoding | You may encounter encoding issues when you process the stored data. In that<br>situation, select this check box to display the Encoding list.<br><br>Select the encoding from the list or select Custom<br>and define it manually. This field is compulsory for database data handling. The<br>supported encodings depend on the JVM that you are using. For more information, see<br>[https://docs.oracle.com](https://docs.oracle.com/). |
| Compress the data | Select the Compress the data check box to compress the<br>output data.<br><br>Hadoop provides different compression formats that help reduce the space needed<br>for storing files and speed up data transfer. When reading a compressed file, Talend Studio needs to<br>uncompress it before being able to feed it to the input flow. |
| Merge result to single file | Select this check box to merge the final *part* files into a single file and put that file in a<br>specified directory.<br><br>Once selecting it, you need to enter the path to, or browse to the<br>folder you want to store the merged file in. This directory is<br>automatically created if it does not exist.<br><br>The following check boxes are used to manage the source and the<br>target files:<br><br><ul> <li> <p> <span>Remove source dir</span>: select                  this check box to remove the source files after the merge.</p> </li> <li> <p> <span>Override target file</span>:                  select this check box to override the file already existing in the target                  location. This option does not override the folder.</p> </li> </ul><br><br><br>If this component is writing merged files with a Databricks cluster, add the following<br>parameter to the Spark configuration console of your<br>cluster:<br><br>```<br>spark.sql.sources.commitProtocolClass org.apache.spark.sql.execution.datasources.SQLHadoopMapReduceCommitProtocol<br>```<br><br>This<br>parameter prevents the merge file including the log file automatically generated by the<br>DBIO service of Databricks.<br><br>This option is not available for a Sequence file. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Advanced separator (for number) | Select this check box to change the separator used for numbers. By default, the thousands separator is a comma (*,*) and the decimal separator is a period (*.*).<br><br>This option is not available for a Sequence file. |
| CSV options | Select this check box to include CSV specific parameters such as<br>Escape char and Text enclosure.<br><br>Information noteImportant: With Spark version 2.0<br>and onward, special characters must be escaped, that is "\\" and<br>"\"" instead of "\" and<br>""". |
| Use local timezone for date | Select this check box to use the local date of the machine in which your Job is executed. If leaving this check box clear, UTC is automatically used to format the Date-type data. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an end component and requires an input link.<br><br>This component, along with the Spark Batch component Palette it belongs to,<br>appears only when you are creating a Spark Batch Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a<br>scenario presents only Standard Jobs, that is to<br>say traditional<br>Talend<br>data integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited-properties-for-apache-spark-streaming -->

# tFileOutputDelimited properties for Apache Spark Streaming (deprecated)

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

These properties are used to configure tFileOutputDelimited running in the Spark Streaming Job framework.

Information noteDeprecation: Spark Streaming is deprecated beginning with the R2026-09 release. Use Spark Structured Streaming instead.

The Spark Streaming tFileOutputDelimited component belongs to the File family.

This component is available in Talend Real-Time Big Data Platform and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Define a storage configuration<br>component | Select the configuration component to be used to provide the configuration<br>information for the connection to the target file system such as HDFS.<br><br>If you leave this check box clear, the target file system is the local<br>system.<br><br>The configuration component to be used must be present in the same Job.<br>For example, if you have dropped a tHDFSConfiguration component in the Job, you can select it to write<br>the result in a given HDFS system. |
| Property type | <ul> <li> <p>Either <span>Built-In</span> or <span>Repository</span>. </p> </li> <li> <p> <span>Built-In</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the            properties are stored.</p> <p>The properties are stored centrally under the <span>Hadoop                Cluster</span> node of the <span>Repository</span>            tree.</p> <p>The fields that come after are pre-filled in using the fetched                            data.</p> <p>For more information about the <span>Hadoop            Cluster</span> node, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/managing-hadoop-metadata" target="_blank">Managing Hadoop connection metadata</a>.</p> </li> </ul> |
| ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Save_Icon.png) | Click this icon to open a database connection wizard and store the<br>database connection parameters you set in the component Basic<br>settings view.<br><br>For more information about setting up and storing database connection<br>parameters, see [Centralizing database metadata](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/centralizing-database-metadata). |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Folder | Browse to, or enter the path pointing to the data to be used in the file system.<br><br>Note that this path must point to a folder rather than a file.<br><br>The button for browsing does not work with the Spark Local mode; if you are using the other Spark Yarn modes that Talend Studio<br>supports with your distribution, ensure that you have properly configured the connection<br>in a configuration component in the same Job. Use the configuration component depending<br>on the filesystem to be used. |
| Action | Select an operation for writing data:<br><br><br>Create: Creates a file and write data<br>in it.<br><br><br>Overwrite: Overwrites the file<br>existing in the directory specified in the Folder field.<br><br>When you want to sort the rows, row order is not guaranteed with this<br>component. |
| Use OS line separator as row separator when CSV Row Separator is set<br>to CR, LF or CRLF | Select this check box to automatically select the appropriate row separator<br>for the OS on which you run the Job:<br><br><ul> <li>LF, for Linux</li> <li>CR or CRLF for Windows</li> </ul><br><br>If you leave the check box cleared, you can specify the row separator to<br>be used regardless of the OS.<br><br>This option is available only when you<br>select the CSV options check box from the<br>Advanced settings view. |
| Row separator | The separator used to identify the end of a row. |
| Field separator | Enter a character, a string, or a regular expression to separate<br>fields for the transferred data. |
| Include Header | Select this check box to include the column header to the file. |
| Custom encoding | You may encounter encoding issues when you process the stored data. In that<br>situation, select this check box to display the Encoding list.<br><br>Select the encoding from the list or select Custom<br>and define it manually. This field is compulsory for database data handling. The<br>supported encodings depend on the JVM that you are using. For more information, see<br>[https://docs.oracle.com](https://docs.oracle.com/). |
| Compress the data | Select the Compress the data check box to compress the<br>output data.<br><br>Hadoop provides different compression formats that help reduce the space needed<br>for storing files and speed up data transfer. When reading a compressed file, Talend Studio needs to<br>uncompress it before being able to feed it to the input flow. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Advanced separator (for number) | Select this check box to change the separator used for numbers. By default, the thousands separator is a comma (*,*) and the decimal separator is a period (*.*).<br><br>This option is not available for a Sequence file. |
| CSV options | Select this check box to include CSV specific parameters such as<br>Escape char and Text enclosure.<br><br>Information noteImportant: With Spark version 2.0<br>and onward, special characters must be escaped, that is "\\" and<br>"\"" instead of "\" and<br>""". |
| Write empty batches | Select this check box to allow your Spark Job to create an empty batch when the<br>incoming batch is empty.<br><br>For further information about when this is desirable<br>behavior, see [this discussion](https://github.com/apache/spark/pull/2132). |
| Use local timezone for date | Select this check box to use the local date of the machine in which your Job is executed. If leaving this check box clear, UTC is automatically used to format the Date-type data. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an end component and requires an input link.<br><br>This component, along with the Spark Streaming component Palette it belongs to, appears<br>only when you are creating a Spark Streaming Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a scenario presents<br>only Standard Jobs, that is to say traditional<br>Talend<br>data<br>integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfileoutputdelimited-tfileinputdelimited-tjava-tfileinputdelimited-tjava-utilizing-output-stream-to-save-filtered-data-to-local-file-standard-component-based-on -->

# Utilizing Output Stream to save filtered data to a local file

Based on the preceding scenario, this scenario saves the filtered data to a local file using output stream.

![](https://help.qlik.com/talend/en-US/components/Resources/images/use_case-tfileoutputdelimited12.png)

### In this section

* [Dropping and linking components](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited-tfileinputdelimited-tjava-tfileinputdelimited-tjava-dropping-and-linking-components-standard-component-drop)
* [Configuring the components](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited-tfileinputdelimited-tjava-tfileinputdelimited-tjava-configuring-components-standard-component)
* [Saving and executing the Job](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited-tfileinputdelimited-tjava-tfileinputdelimited-tjava-saving-and-executing-job-standard-component-press)

**Related concepts**

* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited "Reads a delimited file row by row to split them up into fields and then sends the fields as defined in the schema to the next component.")
* [tFileOutputDelimited](https://help.qlik.com/talend/en-US/components/8.0/tfileoutputdelimited "Outputs the input data to a delimited file according to the defined schema.")

**Related information**

* [tJava](https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjava)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited-tfileinputdelimited-tjava-tfileinputdelimited-tjava-dropping-and-linking-components-standard-component-drop -->

# Dropping and linking components

## Procedure

1. Drop tJava from the Palette to the design workspace.
2. Connect tJava to tFileInputDelimited using a Trigger &gt; On Subjob OK connection.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited-tfileinputdelimited-tjava-tfileinputdelimited-tjava-configuring-components-standard-component -->

# Configuring the components

## Procedure

1. Double-click tJava to open its Basic settings view.
2. In the Code area, type in the following command:
   ```
   new java.io.File("C:/myFolder").mkdirs(); 
   globalMap.put("out_file",new
   java.io.FileOutputStream("C:/myFolder/customerselection.txt",false));
   ```

   Information noteNote:

   In this scenario, the command we use in the Code area of tJava will create a new folder *C:/myFolder* where the output file *customerselection.txt* will be saved. You can customize the command in accordance with actual practice.
3. Double-click tFileOutputDelimited to open its Basic settings view.
4. Select Use Output Stream check box to enable the Output Stream field in which you can define the output stream using command.

   Fill in the Output Stream field with following command:
   ```
   (java.io.OutputStream)globalMap.get("out_file")
   ```

   Information noteNote:

   You can customize the command in the Output Stream field by pressing CTRL+SPACE to select built-in command from the list or type in the command into the field manually in accordance with actual practice. In this scenario, the command we use in the Output Stream field will call the java.io.OutputStream class to output the filtered data stream to a local file which is defined in the Code area of tJava in this scenario.
5. Click Sync columns to retrieve the schema defined in the preceding component.
6. Leave rest of the components as they were in the previous scenario.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited-tfileinputdelimited-tjava-tfileinputdelimited-tjava-saving-and-executing-job-standard-component-press -->

# Saving and executing the Job

## Procedure

1. Press Ctrl+S to save your Job.
2. Press F6 or click Run on the Run tab to execute the Job.

   The three specified columns *Id*, *CustomerName* and *CustomerAddress* are output in the defined output file.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileOutputDelimited11.png)

   For an example of how to use dynamic schemas with tFileOutputDelimited, see [Writing dynamic columns from a database to an output file](https://help.qlik.com/talend/en-US/components/8.0/dynamic-schema/tmysqlinput-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-writing-dynamic-columns-from-database-to-output-file-standard-component-enterprise-in-this).
