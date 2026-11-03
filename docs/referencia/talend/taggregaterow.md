# taggregaterow (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/taggregaterow  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/taggregaterow -->

# tAggregateRow

Receives a flow and aggregates it based on one or more columns.

For each output line, are provided the aggregation key and the relevant result of set operations (min, max, sum...).

tAggregateRow helps to provide a set of metrics based on values or calculations.

### In this section

* [tAggregateRow Standard properties](https://help.qlik.com/talend/en-US/components/8.0/processing/taggregaterow-standard-properties)
* [tAggregateRow properties for Apache Spark Batch](https://help.qlik.com/talend/en-US/components/8.0/processing/taggregaterow-properties-for-apache-spark-batch)
* [tAggregateRow properties for Apache Spark Streaming (deprecated)](https://help.qlik.com/talend/en-US/components/8.0/processing/taggregaterow-properties-for-apache-spark-streaming)
* [tAggregateRow properties for Apache Spark Structured Streaming](https://help.qlik.com/talend/en-US/components/8.0/processing/taggregaterow-properties-for-apache-spark-structured-streaming)

**Related concepts**

* [Aggregating values and sorting data](https://help.qlik.com/talend/en-US/components/8.0/taggregaterow-tsortrow-tfixedflowinput-tlogrow-aggregating-values-and-sorting-data-standard-component "This example shows you how to use Talend components to aggregate the students' comprehensive scores and then sort the aggregated scores based on the student names.")
* [Aggregating values based on dynamic schema](https://help.qlik.com/talend/en-US/components/8.0/taggregaterow-tlogrow-tfileoutputdelimited-tfileinputdelimited-aggregating-values-based-on-dynamic-schema-standard-component-enterprise "Here is an example of using the tAggregateRow component to aggregate some task assignment data in a CSV file based on a dynamic schema column.")
* [Performing download analysis using a Spark Batch Job](https://help.qlik.com/talend/en-US/components/8.0/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/taggregaterow-standard-properties -->

# tAggregateRow Standard properties

These properties are used to configure tAggregateRow running in the Standard Job framework.

The Standard tAggregateRow component belongs to the Processing family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <p>This component offers the advantage of the                  dynamic schema feature. This allows you to retrieve unknown columns from source                  files or to copy batches of columns from a source without mapping each column                  individually. For further information about dynamic schemas, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema" target="_blank">Dynamic schema</a>.</p> <p>This            dynamic schema feature is designed for the purpose of retrieving unknown columns of a            table and is recommended to be used for this purpose only; it is not recommended for the            use of creating tables.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Group by | <ul> <li> <p>Define the aggregation sets, the values of which will be							used for calculations.</p> </li> <li> <p> <span>Output Column</span>: Select the column							label in the list offered based on the schema structure you defined. You							can add as many output columns as you wish to make more precise							aggregations. </p> <p> Ex: Select Country to calculate an average of values for							each country of a list or select Country and Region if you want to							compare one country's regions with another country' regions.</p> </li> <li> <p> <span>Input Column</span>: Match the input							column label with your output columns, in case the output label of the							aggregation set needs to be different.</p> </li> </ul> |
| Operations | <ul> <li> <p>Select the type of operation along with the value to use							for the calculation and the output field.</p> </li> <li> <p> <span>Output Column</span>: Select the							destination field in the list.</p> <div> <span>Function</span>: Select the operator among:                        <ul> <li> <p> <span>count</span>: calculates the number of rows</p> </li> <li> <p> <span>min</span>: selects the minimum value</p> </li> <li> <p> <span>max</span>: selects the maximum value</p> </li> <li> <p> <span>avg</span>: calculates the average</p> </li> <li> <p> <span>sum</span>: calculates the sum</p> </li> <li> <p> <span>first</span>: returns the first value</p> </li> <li> <p> <span>last</span>: returns the last value</p> </li> <li> <p> <span>list</span>: lists values of an aggregation by multiple keys.</p> </li> <li> <p> <span>list (object)</span>: lists Java values of an aggregation by multiple keys</p> </li> <li> <p> <span>count (distinct)</span>: counts the number of the distinct rows</p> </li> <li> <p> <span>standard deviation</span>: calculates the                                    variability of a set of value.</p> </li> <li> <p> <span>union (geometry)</span>: makes the union of a set of Geometry objects</p> </li> <li> <span>population standard deviation</span>: calculates the                                spread of a data distribution. Use this function if the data to be                                calculated is considered a population on its own. This calculation                                supports 39 decimal places.</li> <li> <span>sample                                    standard deviation</span>: calculates the spread of a data                                distribution. Use this function if the data to be calculated is                                considered a sample from a larger population. This calculation                                supports 39 decimal places.</li> </ul></div> </li> <li> <p> <span>Input column</span>: Select the input							column from which the values are taken to be aggregated.</p> </li> <li> <p> <span>Ignore null values</span>: Select the							check boxes corresponding to the names of the columns for which you want							the NULL value to be ignored.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Delimiter(only for list<br>operation) | Enter the delimiter you want to use to separate the<br>different operations. |
| Use financial precision, this is the max<br>precision for "sum" and "avg" operations, checked option heaps more<br>memory and slower than unchecked. | Select this check box to use a financial precision. This<br>is a max precision but consumes more memory and slows the<br>processing.<br><br>Information noteWarning:<br><br><br>*We advise you to use the BigDecimal type for the<br>output in order to obtain precise results.* |
| Check type overflow (slower) | Checks the type of data to ensure that the Job doesn't<br>crash. |
| Check ULP (Unit in the Last Place), ensure<br>that a value will be incremented or decremented correctly, only<br>float and double types. (slower) | Select this check box to ensure the most precise results<br>possible for the Float and Double types. |
| tStatCatcher Statistics | Check this box to collect the log data at component level. Note that this<br>check box is not available in the Map/Reduce version of the component. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component handles flow of data therefore it requires<br>input and output, hence is defined as an intermediary step. Usually the<br>use of tAggregateRow is combined<br>with the tSortRow component. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/taggregaterow-properties-for-apache-spark-batch -->

# tAggregateRow properties for Apache Spark Batch

These properties are used to configure tAggregateRow running in the Spark Batch Job framework.

The Spark Batch tAggregateRow component belongs to the Processing family.

The component in this framework is available in all subscription-based Talend products with Big Data and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <div> <div><span>Information note</span><span>Tip:</span> By default, when Spark aggregates BigDecimal, the                                precision and scale are set at the maximum values of the data type.                                You can change the scale and the precision for BigDecimal in the                                corresponding columns of the schema.</div> </div> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Group by | <ul> <li> <p>Define the aggregation sets, the values of which will be used for                            calculations.</p> </li> <li> <p> <span>Output Column</span>: Select the column                            label in the list offered based on the schema structure you defined. You                            can add as many output columns as you wish to make more precise                            aggregations. </p> <p> Ex: Select Country to calculate an average of values for each country                            of a list or select Country and Region if you want to compare one                            country's regions with another country' regions.</p> </li> <li> <p> <span>Input Column</span>: Match the input column                            label with your output columns, in case the output label of the                            aggregation set needs to be different.</p> </li> </ul> |
| Operations | <ul> <li> <p>Select the type of operation along with the value to use for the                            calculation and the output field.</p> </li> <li> <p> <span>Output Column</span>: Select the destination                     field in the list.</p> <p> <span>Function</span>: Select the operator among:</p> </li> <li> <p> <span>Input column</span>: Select the input column                            from which the values are taken to be aggregated.</p> </li> <li> <p> <span>Ignore null values</span>: Select the check                            boxes corresponding to the names of the columns for which you want the                            NULL value to be ignored.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use financial precision, this is the max precision for "sum"<br>and "avg" operations, checked option heaps more memory and slower<br>than unchecked. | Select this check box to use a financial precision. This is a max<br>precision but consumes more memory and slows the processing.<br><br>Information noteWarning:<br><br><br>*We advise you to use the BigDecimal type for the output in<br>order to obtain precise results.* |
| Check type overflow (slower) | Checks the type of data to ensure that the Job doesn't crash. |
| Check ULP (Unit in the Last Place), ensure that a value will<br>be incremented or decremented correctly, only float and double<br>types. (slower) | Select this check box to ensure the most precise results possible for<br>the Float and Double types. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate step.<br><br>This component, along with the Spark Batch component Palette it belongs to,<br>appears only when you are creating a Spark Batch Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a<br>scenario presents only Standard Jobs, that is to<br>say traditional<br>Talend<br>data integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/taggregaterow-properties-for-apache-spark-streaming -->

# tAggregateRow properties for Apache Spark Streaming (deprecated)

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

These properties are used to configure tAggregateRow running in the Spark Streaming Job framework.

Information noteDeprecation: Spark Streaming is deprecated beginning with the R2026-09 release. Use Spark Structured Streaming instead.

The Spark Streaming tAggregateRow component belongs to the Processing family.

This component is available in Talend Real-Time Big Data Platform and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Group by | <ul> <li> <p>Define the aggregation sets, the values of which will be used for                            calculations.</p> </li> <li> <p> <span>Output Column</span>: Select the column                            label in the list offered based on the schema structure you defined. You                            can add as many output columns as you wish to make more precise                            aggregations. </p> <p> Ex: Select Country to calculate an average of values for each country                            of a list or select Country and Region if you want to compare one                            country's regions with another country' regions.</p> </li> <li> <p> <span>Input Column</span>: Match the input column                            label with your output columns, in case the output label of the                            aggregation set needs to be different.</p> </li> </ul> |
| Operations | <ul> <li> <p>Select the type of operation along with the value to use for the                            calculation and the output field.</p> </li> <li> <p> <span>Output Column</span>: Select the destination                            field in the list.</p> <p> <span>Function</span>: Select the operator among:</p> </li> <li> <p> <span>Input column</span>: Select the input column                            from which the values are taken to be aggregated.</p> </li> <li> <p> <span>Ignore null values</span>: Select the check                            boxes corresponding to the names of the columns for which you want the                            NULL value to be ignored.</p> </li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use financial precision, this is the max precision for "sum"<br>and "avg" operations, checked option heaps more memory and slower<br>than unchecked. | Select this check box to use a financial precision. This is a max<br>precision but consumes more memory and slows the processing.<br><br>Information noteWarning:<br><br><br>*We advise you to use the BigDecimal type for the output in<br>order to obtain precise results.* |
| Check type overflow (slower) | Checks the type of data to ensure that the Job doesn't crash. |
| Check ULP (Unit in the Last Place), ensure that a value will<br>be incremented or decremented correctly, only float and double<br>types. (slower) | Select this check box to ensure the most precise results possible for<br>the Float and Double types. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate step.<br><br>This component, along with the Spark Streaming component Palette it belongs to, appears<br>only when you are creating a Spark Streaming Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a scenario presents<br>only Standard Jobs, that is to say traditional<br>Talend<br>data<br>integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/taggregaterow-properties-for-apache-spark-structured-streaming -->

# tAggregateRow properties for Apache Spark Structured Streaming

[Preview](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/feature-preview-program-overview.htm)

Use these properties to configure tAggregateRow running in the Spark Structured Streaming Job framework.

The Spark Structured Streaming tAggregateRow component belongs to the Processing family.

The streaming version of this component is available in Talend Real-Time Big Data Platform and in Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>Click Edit schema to make changes to<br>the schema. If you make changes, the schema automatically becomes built-in.<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Group by | Define the aggregation sets whose values are used for<br>calculations.<br><br>Output Column: Select the column<br>label from the list based on the schema structure you defined. Add as many<br>output columns as needed to refine the aggregation. For example, select<br>Country to calculate an average for each country, or<br>select Country and Region to<br>compare regions across countries.<br><br>Input Column:<br>Match the input column label to the output column when the aggregation set<br>needs a different output label. |
| Operations | Select the type of operation to perform along with the input value and the<br>output field.<br><br>Output Column: Select the destination field<br>from the list.<br><br><br>Function: Select the operator among:<br><br>Input column: Select the input column whose<br>values are aggregated.<br><br>Ignore null values: Select<br>the check boxes for the columns where NULL values should be<br>ignored. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate step.<br><br>This component, along with the Spark Structured Streaming component Palette it belongs to,<br>appears only when you are creating a Spark Structured Streaming Job. |
| Spark Connection | You need to use the Structured Streaming Configuration<br>tab in the Run view to define the connection to a Spark cluster for<br>the whole Job.<br><br>This connection is effective on a per-Job basis. |
