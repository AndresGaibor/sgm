# tfileinputdelimited (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited -->

# tFileInputDelimited

Reads a delimited file row by row to split them up into fields and then sends the fields as defined in the schema to the next component.

### In this section

* [tFileInputDelimited Standard properties](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-standard-properties)
* [tFileInputDelimited properties for Apache Spark Batch](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-properties-for-apache-spark-batch)
* [tFileInputDelimited properties for Apache Spark Streaming (deprecated)](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-properties-for-apache-spark-streaming)

**Related concepts**

* [Reading data from a Delimited file and display the output](https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited-tlogrow-reading-data-from-delimited-file-and-display-output-standard-component-the)
* [Reading data from a remote file in streaming mode](https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited-tfilefetch-tsleep-tlogrow-reading-data-from-remote-file-in-streaming-mode-standard-component-this)
* [Using a pivot column to aggregate data](https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited-tpivottocolumnsdelimited-tpivottocolumnsdelimited-using-pivot-column-to-aggregate-data-standard-component-the)
* [Utilizing Output Stream to save filtered data to a local file](https://help.qlik.com/talend/en-US/components/8.0/tfileoutputdelimited-tfileinputdelimited-tjava-tfileinputdelimited-tjava-utilizing-output-stream-to-save-filtered-data-to-local-file-standard-component-based-on)
* [Writing data in a delimited file](https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-writing-data-in-delimited-file-standard-component-this)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-standard-properties -->

# tFileInputDelimited Standard properties

These properties are used to configure tFileInputDelimited running in the Standard Job framework.

The Standard tFileInputDelimited component belongs to the File family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | <ul> <li> <p>Either <span>Built-In</span> or <span>Repository</span>. </p> </li> <li> <p> <span>Built-In</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the            properties are stored.</p> </li> </ul> |
| Use existing dynamic | Select this check box if you want to use an existing dynamic schema set in a<br>tSetDynamicSchema component. |
| File Name/Stream | File name: Name and path of the file to be processed.<br><br><br>Stream: The data flow to be processed. The data must be added to the flow in order for tFileInputDelimited to fetch these data via the corresponding representative variable.<br><br>This variable can be already pre-defined in Talend Studio or provided by the context or the components you are using along with this<br>component; otherwise, you can define it manually and use it according to the<br>design of your Job, for example, using tJava or tJavaFlex.<br><br>In order to avoid the inconvenience of hand writing, you could select the variable of interest from the auto-completion list (Ctrl+Space) to fill the current field on condition that this variable has been properly defined.<br><br>Information noteWarning: Use absolute path (instead of relative path) for<br>this field to avoid possible errors. |
| Row separator | The separator used to identify the end of a row. |
| Field separator | Enter a character, a string, or a regular expression to separate<br>fields for the transferred data.<br><br>Information noteNote: With CSV<br>options selected, the field separator can only be a<br>single character. In this case, if you enter multiple characters in this<br>field, only the first character acts as the field separator. |
| CSV options | Select this check box to specify the following CSV parameters:<br><br><ul> <li> <p> <span>Escape char</span>: enter the escape character between double                quotation marks. </p> </li> <li> <p> <span>Text enclosure</span>: enter the enclosure character (only one                character) between double quotation marks. For example, <kbd>"""</kbd>                needs to be entered when double quotation marks (") are used as the enclosure                character.</p> </li> </ul><br><br>It is recommended to use standard escape character, that is "\".<br>Otherwise, you should set the same character for Escape char and<br>Text enclosure. For example, if the escape character is set to<br>"\", the text enclosure can be set to any other character. On<br>the other hand, if the escape character is set to other character rather than<br>"\", the text enclosure can be set to any other characters.<br>However, the escape character will be changed to the same character as the text<br>enclosure. For instance, if the escape character is set to "#"<br>and the text enclosure is set to "@", the escape character will<br>be changed to "@", not "#". |
| Header | Enter the number of rows to be skipped in the beginning of file.<br><br>Note that when dynamic schema is used, the first row of<br>the input data is always treated as the header row no matter whether the Header field value is set or not. For more information about<br>dynamic schema, see [Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema). |
| Footer | Number of rows to be skipped at the end of the file. |
| Limit | Maximum number of rows to be processed. If Limit = 0, no row is read or processed. |
| Schema and Edit Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <p>Note that if the input value of any non-nullable primitive field is null, the row of data including that field will be rejected.</p> <p>This component offers the advantage of the                  dynamic schema feature. This allows you to retrieve unknown columns from source                  files or to copy batches of columns from a source without mapping each column                  individually. For further information about dynamic schemas, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema" target="_blank">Dynamic schema</a>.</p> <p>This            dynamic schema feature is designed for the purpose of retrieving unknown columns of a            table and is recommended to be used for this purpose only; it is not recommended for the            use of creating tables.</p> <p>When using the dynamic schema feature, the dynamic column does not contain the actual column names of the input file. If you want your output flow to include the actual column names, make sure that your input file has a header row and the <span>Header</span> value is set properly.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Skip empty rows | Select this checkbox to skip the empty rows. |
| Uncompress as zip file | Select this check box to uncompress the input file. |
| Die on error | Select the checkbox to stop the execution of the Job when an error<br>occurs.<br><br>Clear the checkbox to skip any rows on error and complete the process for<br>error-free rows. When errors are skipped, you can collect the rows on error using a Row &gt; Reject link.<br><br>To catch the FileNotFoundException, you also need to select this check box. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Advanced separator (for numbers) | Select this check box to change the separator used for numbers. By default, the thousands separator is a comma (*,*) and the decimal separator is a period (*.*). |
| Extract lines at random | Select this check box to set the number of lines to be extracted randomly. |
| Encoding | Select the encoding from the list or select Custom<br>and define it manually. This field is compulsory for database data handling. The<br>supported encodings depend on the JVM that you are using. For more information, see<br>[https://docs.oracle.com](https://docs.oracle.com/). |
| Trim all column | Select this check box to remove the leading and trailing whitespaces from all<br>columns. When this check box is cleared, the Check column to<br>trim table is displayed, which lets you select particular columns to<br>trim. |
| Check each row structure against schema | Select this check box to check whether the total number of columns<br>in each row is consistent with the schema. If not consistent, an<br>error message will be displayed on the console. |
| Check date | Select this check box to check the date format strictly against the input schema. |
| Check columns to trim | This table is filled automatically with the schema being used. Select the check<br>box(es) corresponding to the column(s) to be trimmed. |
| Split row before field | Select this check box to split rows before splitting fields. |
| Permit hexadecimal (0xNNN) or octal (0NNNN) for numeric types - it will act the opposite for Byte | Select this check box if any of your numeric types (long, integer, short, or byte type), will<br>be parsed from a hexadecimal or octal string.<br><br>In the table that appears, select the check box next to the column or columns of interest to transform the input string of each selected column to the type defined in the schema.<br><br>Select the Permit hexadecimal or octal check box to select all the columns.<br><br>This table appears only when the Permit hexadecimal (0xNNN) or octal (0NNNN) for numeric types - it will act the opposite for Byte check box is selected. |
| tStatCatcher Statistics | Select this check box to gather the processing metadata at the Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the component when an<br>error occurs. This is an After variable and it returns a string.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | Use this component to read a file and separate fields contained in this file using a defined separator. It allows you to create a data flow using a Row &gt; Main link or via a Row &gt; Reject link in which case the data is filtered by data that does not correspond to the type defined. For further information, please see [Procedure](https://help.qlik.com/talend/en-US/components/8.0/processing/textractxmlfield-tlogrow-tfileinputdelimited-tfileoutputdelimited-procedure-standard-component-drop). |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-properties-for-apache-spark-batch -->

# tFileInputDelimited properties for Apache Spark Batch

These properties are used to configure tFileInputDelimited running in the Spark Batch Job framework.

The Spark Batch tFileInputDelimited component belongs to the File family.

The component in this framework is available in all subscription-based Talend products with Big Data and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Define a storage configuration<br>component | Select the configuration component to be used to provide the configuration<br>information for the connection to the target file system such as HDFS.<br><br>If you leave this check box clear, the target file system is the local<br>system.<br><br>The configuration component to be used must be present in the same Job.<br>For example, if you have dropped a tHDFSConfiguration component in the Job, you can select it to write<br>the result in a given HDFS system. |
| Property type | <ul> <li> <p>Either <span>Built-In</span> or <span>Repository</span>. </p> </li> <li> <p> <span>Built-In</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the            properties are stored.</p> <p>The properties are stored centrally under the <span>Hadoop                Cluster</span> node of the <span>Repository</span>            tree.</p> <p>For more information about the <span>Hadoop            Cluster</span> node, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/managing-hadoop-metadata" target="_blank">Managing Hadoop connection metadata</a>.</p> </li> </ul> |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit schema</span> to make changes to                  the schema. If you make changes, the schema automatically becomes built-in. </p> <p>The dynamic column in the schema is available when you have installed the                     8.0.1-R2022-09 <span>Talend Studio</span> Monthly update or a later one delivered by <span>Talend</span>. For more information, check with your administrator. Note that the dynamic                     column is only available when you set a header. Make sure to put                        <span>1</span> as a value for the <span>Header</span>                     property. When you use the dynamic columns, the columns are loaded as strings                     by default.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Folder/File | Browse to, or enter the path pointing to the data to be used in the file system.<br><br>If the path you set points to a folder, this component will<br>read all of the files stored in that folder, for example,<br>/user/talend/in; if sub-folders exist, the sub-folders are automatically<br>ignored unless you define the property<br>spark.hadoop.mapreduce.input.fileinputformat.input.dir.recursive to be<br>true in the Advanced properties table in the<br>Spark configuration tab.<br><br><ul> <li>Depending on the filesystem to be used, properly configure the corresponding          configuration component placed in your Job, for example, a            <span>tHDFSConfiguration</span> component for HDFS, a            <span>tS3Configuration</span> component for S3 and a            <span>tAzureFSConfiguration</span> for Azure Storage and Azure Data Lake          Storage.</li> </ul><br><br>If the file to be read is a compressed one, enter the file name with<br>its extension; then this component automatically decompresses it at<br>runtime. The supported compression formats and their corresponding<br>extensions are:<br><br><ul> <li> <p>DEFLATE: <em>*.deflate</em> </p> </li> <li> <p>gzip: <em>*.gz</em> </p> </li> <li> <p>bzip2: <em>*.bz2</em> </p> </li> <li> <p>LZO: <em>*.lzo</em> </p> </li> </ul><br><br>The button for browsing does not work with the Spark Local mode; if you are using the other Spark Yarn modes that Talend Studio<br>supports with your distribution, ensure that you have properly configured the connection<br>in a configuration component in the same Job. Use the configuration component depending<br>on the filesystem to be used. |
| Die on error | Select the checkbox to stop the execution of the Job when an error<br>occurs. |
| Use S3 Select | Select this check box to use S3 select to improve your query performance.<br>You need to set the following parameters in the corresponding fields:<br><br>This check<br>box is only available when you use a tS3Configuration<br>component as a storage configuration component and when you run your Job with<br>Spark Universal in either YARN cluster (with an Amazon EMR cluster) or<br>Databricks modes.<br><br><ul> <li> <span>Use GZIP compression</span>: select this check box to use                        GZIP compression on your files.</li> <li> <span>Comment character</span>: enter the character to be used to                        comment.</li> <li> <span>Null value</span>: enter the value to be considered as                        null.</li> <li> <span>Values can contain quoted record delimiters</span>: select                        this check box to allow quoted record delimiters in the values. This option                        applies only for Databricks.</li> </ul><br><br>This option is available only when you have installed the 8.0.1-R2022-12<br>Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Row separator | The separator used to identify the end of a row. |
| Field separator | Enter a character, a string, or a regular expression to separate<br>fields for the transferred data. |
| Header | Enter the number of rows to be skipped in the beginning of file.<br><br>Information noteNote: This option works correctly if you do not enter a large number. |
| CSV options | Select this check box to include CSV specific parameters such as<br>Escape char and Text enclosure.<br><br>Information noteImportant: With Spark version 2.0<br>and onward, special characters must be escaped, that is "\\" and<br>"\"" instead of "\" and<br>""". |
| Splittable | Select this check box to enable your Spark cluster to use<br>multiple executors to read large files in parallel.<br><br>This check<br>box is only available when you select the CSV<br>options check box. |
| Use multiline option | Select this check box to enable two lines to result in one in the input<br>file.<br><br>This check box is only available when you select the<br>CSV options check box. |
| Skip empty rows | Select this checkbox to skip the empty rows. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Set minimum partitions | Select this check box to control the number of partitions to be created from the input<br>data over the default partitioning behavior of Spark.<br><br>In the displayed field, enter, without quotation marks, the minimum number of partitions<br>you want to obtain.<br><br>When you want to control the partition number, you can generally set at least as many partitions as<br>the number of executors for parallelism, while bearing in mind the available memory and the<br>data transfer pressure on your network. |
| Custom Encoding | You may encounter encoding issues when you process the stored data. In that<br>situation, select this check box to display the Encoding list.<br><br>Then select the encoding to be used from the list or select Custom and define it manually. |
| Advanced separator (for number) | Select this check box to change the separator used for numbers. By default, the thousands separator is a comma (*,*) and the decimal separator is a period (*.*). |
| Trim all columns | Select this check box to remove the leading and trailing whitespaces from all<br>columns. When this check box is cleared, the Check column to<br>trim table is displayed, which lets you select particular columns to<br>trim. |
| Check column to trim | This table is filled automatically with the schema being used. Select the check<br>box(es) corresponding to the column(s) to be trimmed. |
| Check each row structure against<br>schema | Select this check box to check whether the total number of columns<br>in each row is consistent with the schema. If not consistent, an<br>error message will be displayed on the console. |
| Check date | Select this check box to check the date format strictly against the input schema. |
| Decode String for long, int, short, byte<br>Types | Select this check box if any of your numeric types (long, integer, short, or byte type), will<br>be parsed from a hexadecimal or octal string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as a start component and requires an<br>output link.<br><br>This component, along with the Spark Batch component Palette it belongs to,<br>appears only when you are creating a Spark Batch Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a<br>scenario presents only Standard Jobs, that is to<br>say traditional<br>Talend<br>data integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-properties-for-apache-spark-streaming -->

# tFileInputDelimited properties for Apache Spark Streaming (deprecated)

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

These properties are used to configure tFileInputDelimited running in the Spark Streaming Job framework.

Information noteDeprecation: Spark Streaming is deprecated beginning with the R2026-09 release. Use Spark Structured Streaming instead.

The Spark Streaming tFileInputDelimited component belongs to the File family.

This component is available in Talend Real-Time Big Data Platform and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Define a storage configuration<br>component | Select the configuration component to be used to provide the configuration<br>information for the connection to the target file system such as HDFS.<br><br>If you leave this check box clear, the target file system is the local<br>system.<br><br>The configuration component to be used must be present in the same Job.<br>For example, if you have dropped a tHDFSConfiguration component in the Job, you can select it to write<br>the result in a given HDFS system. |
| Property type | <ul> <li> <p>Either <span>Built-In</span> or <span>Repository</span>. </p> </li> <li> <p> <span>Built-In</span>: No property data stored centrally.</p> </li> <li> <p> <span>Repository</span>: Select the repository file where the            properties are stored.</p> <p>The properties are stored centrally under the <span>Hadoop                Cluster</span> node of the <span>Repository</span>            tree.</p> <p>For more information about the <span>Hadoop            Cluster</span> node, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/managing-hadoop-metadata" target="_blank">Managing Hadoop connection metadata</a>.</p> </li> </ul> |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit schema</span> to make changes to                  the schema. If you make changes, the schema automatically becomes built-in. </p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Folder/File | Browse to, or enter the path pointing to the data to be used in the file system.<br><br>If the path you set points to a folder, this component will<br>read all of the files stored in that folder, for example,<br>/user/talend/in; if sub-folders exist, the sub-folders are automatically<br>ignored unless you define the property<br>spark.hadoop.mapreduce.input.fileinputformat.input.dir.recursive to be<br>true in the Advanced properties table in the<br>Spark configuration tab.<br><br><ul> <li>Depending on the filesystem to be used, properly configure the corresponding          configuration component placed in your Job, for example, a            <span>tHDFSConfiguration</span> component for HDFS, a            <span>tS3Configuration</span> component for S3 and a            <span>tAzureFSConfiguration</span> for Azure Storage and Azure Data Lake          Storage.</li> </ul><br><br>If the file to be read is a compressed one, enter the file name with<br>its extension; then this component automatically decompresses it at<br>runtime. The supported compression formats and their corresponding<br>extensions are:<br><br><ul> <li> <p>DEFLATE: <em>*.deflate</em> </p> </li> <li> <p>gzip: <em>*.gz</em> </p> </li> <li> <p>bzip2: <em>*.bz2</em> </p> </li> <li> <p>LZO: <em>*.lzo</em> </p> </li> </ul><br><br>The button for browsing does not work with the Spark Local mode; if you are using the other Spark Yarn modes that Talend Studio<br>supports with your distribution, ensure that you have properly configured the connection<br>in a configuration component in the same Job. Use the configuration component depending<br>on the filesystem to be used. |
| Die on error | Select the checkbox to stop the execution of the Job when an error<br>occurs. |
| Row separator | The separator used to identify the end of a row. |
| Field separator | Enter a character, a string, or a regular expression to separate<br>fields for the transferred data. |
| Header | Enter the number of rows to be skipped in the beginning of file. |
| CSV options | Select this check box to include CSV specific parameters such as<br>Escape char and Text enclosure.<br><br>Information noteImportant: With Spark version 2.0<br>and onward, special characters must be escaped, that is "\\" and<br>"\"" instead of "\" and<br>""". |
| Use multiline option | Select this check box to enable two lines to result in one in<br>the input file.<br><br>This check box is only available when you select the<br>CSV options check box. |
| Skip empty rows | Select this checkbox to skip the empty rows. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Set minimum partitions | Select this check box to control the number of partitions to be created from the input<br>data over the default partitioning behavior of Spark.<br><br>In the displayed field, enter, without quotation marks, the minimum number of partitions<br>you want to obtain.<br><br>When you want to control the partition number, you can generally set at least as many partitions as<br>the number of executors for parallelism, while bearing in mind the available memory and the<br>data transfer pressure on your network. |
| Custom Encoding | You may encounter encoding issues when you process the stored data. In that<br>situation, select this check box to display the Encoding list.<br><br>Then select the encoding to be used from the list or select Custom and define it manually. |
| Advanced separator (for number) | Select this check box to change the separator used for numbers. By default, the thousands separator is a comma (*,*) and the decimal separator is a period (*.*). |
| Trim all columns | Select this check box to remove the leading and trailing whitespaces from all<br>columns. When this check box is cleared, the Check column to<br>trim table is displayed, which lets you select particular columns to<br>trim. |
| Check column to trim | This table is filled automatically with the schema being used. Select the check<br>box(es) corresponding to the column(s) to be trimmed. |
| Check each row structure against<br>schema | Select this check box to check whether the total number of columns<br>in each row is consistent with the schema. If not consistent, an<br>error message will be displayed on the console. |
| Check date | Select this check box to check the date format strictly against the input schema. |
| Decode String for long, int, short, byte<br>Types | Select this check box if any of your numeric types (long, integer, short, or byte type), will<br>be parsed from a hexadecimal or octal string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as a start component and requires an output link.<br><br>This component is only used to provide the lookup flow (the right side of a join<br>operation) to the main flow of a tMap component. In this<br>situation, the lookup model used by this tMap must be<br>Load once.<br><br>This component, along with the Spark Streaming component Palette it belongs to, appears<br>only when you are creating a Spark Streaming Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a scenario presents<br>only Standard Jobs, that is to say traditional<br>Talend<br>data<br>integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited-tlogrow-reading-data-from-delimited-file-and-display-output-standard-component-the -->

# Reading data from a Delimited file and display the output

The following scenario creates a two-component Job, which aims at reading each row of a file, selecting delimited data and displaying the output in the Run log console.

![](https://help.qlik.com/talend/en-US/components/Resources/images/UseCase_tFileInputDelimited1.png)

### In this section

* [Dropping and linking components](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tlogrow-dropping-and-linking-components-standard-component-drop)
* [Configuring the components](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tlogrow-configuring-components-standard-component-select)
* [Saving and executing the Job](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tlogrow-saving-and-executing-job-standard-component-press)

**Related concepts**

* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited "Reads a delimited file row by row to split them up into fields and then sends the fields as defined in the schema to the next component.")

**Related information**

* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited-tfilefetch-tsleep-tlogrow-reading-data-from-remote-file-in-streaming-mode-standard-component-this -->

# Reading data from a remote file in streaming mode

This scenario describes a four component Job used to fetch data from a voluminous file almost as soon as it has been read. The data is displayed in the Run view. The advantage of this technique is that you do not have to wait for the entire file to be downloaded, before viewing the data.

![](https://help.qlik.com/talend/en-US/components/Resources/images/Use_Case_tFileInputDelimited2_1.png)

### In this section

* [Dropping and linking components](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfilefetch-tsleep-tlogrow-dropping-and-linking-components-standard-component-drop)
* [Configuring the components](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfilefetch-tsleep-tlogrow-configuring-components-standard-component)
* [Configuring Job execution and executing the Job](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfilefetch-tsleep-tlogrow-configuring-job-execution-and-executing-job-standard-component-click)

**Related concepts**

* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited "Reads a delimited file row by row to split them up into fields and then sends the fields as defined in the schema to the next component.")

**Related information**

* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)
* [tFileFetch](https://help.qlik.com/talend/en-US/components/8.0/internet/tfilefetch)
* [tSleep](https://help.qlik.com/talend/en-US/components/8.0/orchestration/tsleep)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited-tpivottocolumnsdelimited-tpivottocolumnsdelimited-using-pivot-column-to-aggregate-data-standard-component-the -->

# Using a pivot column to aggregate data

The following scenario describes a Job that transposes data from a delimited input file based on a selected pivot column and aggregates the result data based on a defined aggregation criterion.

![](https://help.qlik.com/talend/en-US/components/Resources/images/pve9865.png)

### In this section

* [Dropping and linking components](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tpivottocolumnsdelimited-tpivottocolumnsdelimited-dropping-and-linking-components-standard-component-drop)
* [Configuring the components](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tpivottocolumnsdelimited-tpivottocolumnsdelimited-configuring-components-standard-component)
* [Saving and executing the Job](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tpivottocolumnsdelimited-tpivottocolumnsdelimited-saving-and-executing-job-standard-component-press)

**Related concepts**

* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited "Reads a delimited file row by row to split them up into fields and then sends the fields as defined in the schema to the next component.")

**Related reference**

* [tPivotToColumnsDelimited](https://help.qlik.com/talend/en-US/components/8.0/tpivottocolumnsdelimited "Fine-tunes the selection of data to output.")


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-writing-data-in-delimited-file-standard-component-this -->

# Writing data in a delimited file

This scenario describes a three-component Job that extracts certain data from a file holding information about clients, *customers*, and then writes the extracted data in a delimited file.

In the following example, we have already stored the input schema under the Metadata node in the Repository tree view. For more information about storing schema metadata in the Repository, see [Managing metadata in Talend Studio](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/managing-metadata-in-studio).

![](https://help.qlik.com/talend/en-US/components/Resources/images/Use_Case_tFileOutputDelimited9.png)

### In this section

* [Dropping and linking components](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-dropping-and-linking-components-standard-component-in)
* [Configuring the components](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-configuring-components-standard-component)
* [Saving and executing the Job](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-saving-and-executing-job-standard-component-press)

**Related concepts**

* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/tfileinputdelimited "Reads a delimited file row by row to split them up into fields and then sends the fields as defined in the schema to the next component.")
* [tFileOutputDelimited](https://help.qlik.com/talend/en-US/components/8.0/tfileoutputdelimited "Outputs the input data to a delimited file according to the defined schema.")

**Related information**

* [tMap](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tlogrow-dropping-and-linking-components-standard-component-drop -->

# Dropping and linking components

## Procedure

1. Drop a tFileInputDelimited component and a tLogRow component from the Palette to the design workspace.
2. Right-click on the tFileInputDelimited component and select Row &gt; Main. Then drag it onto the tLogRow component and release when the plug symbol shows up.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tlogrow-configuring-components-standard-component-select -->

# Configuring the components

## Procedure

1. Select the tFileInputDelimited component again, and define its Basic settings:

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tFileInputDelimited.png)
2. Fill in a path to the file in the File Name field. This field is mandatory.

   Information noteWarning:

   If the path of the file contains some accented characters, you will get an error message when executing your Job.
3. Define the Row separator allowing to identify the end of a row. Then define the Field separator used to delimit fields in a row.
4. In this scenario, the header and footer limits are not set. And the Limit number of processed rows is set on 50.
5. Set the Schema as either a local (Built-in) or a remotely managed (Repository) to define the data to pass on to the tLogRow component.
6. You can load and/or edit the schema via the Edit Schema function.
7. Enter the encoding standard the input file is encoded in. This setting is meant to ensure encoding consistency throughout all input and output files.
8. Select the tLogRow and define the Field separator to use for the output display. Related topic: [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow).
9. Select the Print schema column name in front of each value check box to retrieve the column labels in the output displayed.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tlogrow-saving-and-executing-job-standard-component-press -->

# Saving and executing the Job

## Procedure

1. Press Ctrl+S to save your Job.
2. Go to Run tab, and click on Run to execute the Job.

   The file is read row by row and the extracted fields are displayed on the Run log as defined in both components Basic settings.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/UseCase_tFileInputDelimited3.png)

   The Log sums up all parameters in a header followed by the result of the Job.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfilefetch-tsleep-tlogrow-dropping-and-linking-components-standard-component-drop -->

# Dropping and linking components

## Procedure

1. Drop the following components onto the workspace: tFileFetch, tSleep, tFileInputDelimited, and tLogRow.
2. Connect tSleep and tFileInputDelimited using a Trigger &gt; OnComponentOk link and connect tFileInputDelimited to tLogRow using a Row &gt; Main link.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfilefetch-tsleep-tlogrow-configuring-components-standard-component -->

# Configuring the components

## Procedure

1. Double-click tFileFetch to display the Basic settings tab in the Component view and set the properties.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileInputDelimited2_2.png)
2. From the Protocol list, select the appropriate protocol to access the server on which your data is stored.
3. In the URI field, enter the URI required to access the server on which your file is stored.
4. Select the Use cache to save the resource check box to add your file data to the cache memory. This option allows you to use the streaming mode to transfer the data.
5. In the workspace, click tSleep to display the Basic settings tab in the Component view and set the properties.

   By default, tSleep's Pause field is set to *1* second. Do not change this setting. It pauses the second Job in order to give the first Job, containing tFileFetch, the time to read the file data.
6. In the workspace, double-click tFileInputDelimited to display its Basic settings tab in the Component view and set the properties.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileInputDelimited2_3.png)
7. In the File name/Stream field:

   - Delete the default content.

   - Press Ctrl+Space to view the variables available for this component.

   - Select *tFileFetch\_1\_INPUT\_STREAM* from the auto-completion list, to add the following variable to the Filename field: ((java.io.InputStream)globalMap.get("tFileFetch\_1\_INPUT\_STREAM")).
8. From the Schema list, select Built-in and click [...] next to the Edit schema field to describe the structure of the file that you want to fetch. The *US\_Employees* file is composed of six columns: *ID*, *Employee*, *Age*, *Address*, *State*, *EntryDate*.

   Click [+] to add the six columns and set them as indicated in the above screenshot. Click OK.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileInputDelimited2_4.png)
9. In the workspace, double-click tLogRow to display its Basic settings in the Component view and click Sync Columns to ensure that the schema structure is properly retrieved from the preceding component.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfilefetch-tsleep-tlogrow-configuring-job-execution-and-executing-job-standard-component-click -->

# Configuring Job execution and executing the Job

## Procedure

1. Click the Job tab and then on the Extra view.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileInputDelimited2_5.png)
2. Select the Multi thread execution check box in order to run the two Jobs at the same time. Bear in mind that the second Job has a one second delay according to the properties set in tSleep. This option allows you to fetch the data almost as soon as it is read by tFileFetch, thanks to the tFileDelimited component.
3. Save the Job and press F6 to run it.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileInputDelimited2_6.png)

   The data is displayed in the console as almost as soon as it is read.

   For a scenario concerning the use of dynamic schemas in tFileInputDelimited, see [Writing dynamic columns from a database to an output file](https://help.qlik.com/talend/en-US/components/8.0/dynamic-schema/tmysqlinput-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-writing-dynamic-columns-from-database-to-output-file-standard-component-enterprise-in-this).


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tpivottocolumnsdelimited-tpivottocolumnsdelimited-dropping-and-linking-components-standard-component-drop -->

# Dropping and linking components

## Procedure

1. Drop the following component from the Palette to the design workspace: tFileInputDelimited, tPivotToColumnsDelimited.
2. Link the two components using a Row &gt; Main connection.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tpivottocolumnsdelimited-tpivottocolumnsdelimited-configuring-components-standard-component -->

# Configuring the components

### In this section

* [Set the input component](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tpivottocolumnsdelimited-tpivottocolumnsdelimited-set-input-component-standard-component)
* [Set the output component](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tpivottocolumnsdelimited-tpivottocolumnsdelimited-set-output-component-standard-component)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tpivottocolumnsdelimited-tpivottocolumnsdelimited-saving-and-executing-job-standard-component-press -->

# Saving and executing the Job

## Procedure

1. Press Ctrl+S to save your Job.
2. Press F6 or click Run on the Run tab to execute the Job.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tPivotOutputFile5.png)

   The output file shows the newly aggregated data.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-dropping-and-linking-components-standard-component-in -->

# Dropping and linking components

## Procedure

1. In the Repository tree view, expand Metadata and File delimited in succession and then browse to your input schema, *customers*, and drop it on the design workspace. A dialog box displays where you can select the component type you want to use.
2. Click tFileInputDelimited and then OK to close the dialog box. A tFileInputDelimited component holding the name of your input schema appears on the design workspace.
3. Place a tMap component and a tFileOutputDelimited component from the Palette to the design workspace.
4. Link the components together using Row &gt; Main connections.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-configuring-components-standard-component -->

# Configuring the components

### In this section

* [Configuring the input component](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-configuring-input-component-standard-component)
* [Configuring the mapping component](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-configuring-mapping-component-standard-component-in)
* [Configuring the output component](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-configuring-output-component-standard-component-in)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-saving-and-executing-job-standard-component-press -->

# Saving and executing the Job

## Procedure

1. Press Ctrl+S to save your Job.
2. Press F6 or click Run on the Run tab to execute the Job.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileOutputDelimited11.png)

   The three specified columns *Id*, *CustomerName* and *CustomerAddress* are output in the defined output file.

   For an example of how to use dynamic schemas with tFileOutputDelimited, see [Writing dynamic columns from a database to an output file](https://help.qlik.com/talend/r/en-US/8.0/components/dynamic-schema/tmysqlinput-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-writing-dynamic-columns-from-database-to-output-file-standard-component-enterprise-in-this).


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tpivottocolumnsdelimited-tpivottocolumnsdelimited-set-input-component-standard-component -->

# Set the input component

## Procedure

1. Double-click the tFileInputDelimited component to open its Basic settings view.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/dqt884.png)
2. Browse to the input file to fill out the File Name separators, in this example, respectively: carriage return and semi-colon field.

   The file to use as input file is made of 3 columns, including: *ID*, *Question* and the corresponding *Answer*

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tPivotOutputFile2.png)
3. Define the Row and Field
4. As the file contains a header line, define it also.
5. Set the schema describing the three columns: *ID* separators, in this example, respectively: carriage, *Questions*, *Answers*.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tpivottocolumnsdelimited-tpivottocolumnsdelimited-set-output-component-standard-component -->

# Set the output component

## Procedure

1. Double-click the tPivotToColumnsDelimited component to open its Basic settings view.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/cys1795.png)
2. In the Pivot column field, select the pivot column from the input schema. this is often the column presenting most duplicates (pivot aggregation values).
3. In the Aggregation column field, select the column from the input schema that should gets aggregated.
4. In the Aggregation function field, select the function to be used in case duplicates are found out.
5. In the Group by table, add an Input column, that will be used to group by the aggregation column.
6. In the File Name field, browse to the output file path. And on the Row and Field separator fields, set the separators for the aggregated output rows and data.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-configuring-input-component-standard-component -->

# Configuring the input component

## Procedure

1. Double-click tFileInputDelimited to open its Basic settings view. All its property fields are automatically filled in because you defined your input file locally.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileOutputDelimited2.png)
2. If you do not define your input file locally in the Repository tree view, fill in the details manually after selecting Built-in in the Property type list.
3. Click the [...] button next to the File Name field and browse to the input file, *customer.csv* in this example.

   Information noteWarning:

   If the path of the file contains some accented characters, you will get an error message when executing your Job.
4. In the Row Separators and Field Separators fields, enter respectively "*\n*" and "*;*" as line and field separators.
5. If needed, set the number of lines used as header and the number of lines used as footer in the corresponding fields and then set a limit for the number of processed rows.

   In this example, Header is set to 6 while Footer and Limit are not set.
6. In the Schema field, schema is automatically set to Repository and your schema is already defined since you have stored your input file locally for this example. Otherwise, select Built-in and click the [...] button next to Edit Schema to open the Schema dialog box where you can define the input schema, and then click OK to close the dialog box.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileOutputDelimited4.png)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-configuring-mapping-component-standard-component-in -->

# Configuring the mapping component

## Procedure

1. In the design workspace, double-click tMap to open its editor.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileOutputDelimited7.png)
2. In the tMap editor, click ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileOutputDelimited12.png) on top of the panel to the right to open the Add a new output table dialog box.
3. Enter a name for the table you want to create, *row2* in this example.
4. Click OK to validate your changes and close the dialog box.
5. In the table to the left, *row1*, select the first three lines (*Id*, *CustomerName* and *CustomerAddress*) and place them to the table to the right.
6. In the Schema editor view situated in the lower left corner of the tMap editor, change the type of *RegisterTime* to String in the table to the right.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileOutputDelimited8.png)
7. Click OK to save your changes and close the editor.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited-tfileoutputdelimited-tmap-tfileoutputdelimited-tmap-configuring-output-component-standard-component-in -->

# Configuring the output component

## Procedure

1. In the design workspace, double-click tFileOutputDelimited to open its Basic settings view and define the component properties.
2. In the Property Type field, set the type to Built-in and fill in the fields that follow manually.
3. Click the [...] button next to the File Name field and browse to the output file you want to write data in, *customerselection.txt* in this example.
4. In the Row Separator and Field Separator fields, set "*\n*" and "*;*" respectively as row and field separators.
5. Select the Include Header check box if you want to output columns headers as well.
6. Click Edit schema to open the schema dialog box and verify if the recuperated schema corresponds to the input schema. If not, click Sync Columns to recuperate the schema from the preceding component.
