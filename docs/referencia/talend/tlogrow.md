# tlogrow (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tlogrow  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tlogrow -->

# tLogRow

Displays data or results in the Run console to monitor data processed.

### In this section

* [tLogRow Standard properties](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-standard-properties)
* [tLogRow properties for Apache Spark Batch](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-properties-for-apache-spark-batch)
* [tLogRow properties for Apache Spark Streaming (deprecated)](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-properties-for-apache-spark-streaming)
* [tLogRow properties for Apache Spark Structured Streaming](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-properties-for-apache-spark-structured-streaming)

**Related concepts**

* [Catching flow metrics from a Job](https://help.qlik.com/talend/en-US/components/8.0/tflowmeter-tflowmetercatcher-tmysqlinput-catching-flow-metrics-from-job-standard-component-the)
* [Catching messages triggered by a tWarn component](https://help.qlik.com/talend/en-US/components/8.0/twarn-tlogcatcher-tlogrow-trowgenerator-catching-messages-triggered-by-twarn-component-standard-component "This example shows you how to use the tLogCatcher component to catch the messages triggered by a tWarn component.")
* [Catching the message triggered by a tDie component](https://help.qlik.com/talend/en-US/components/8.0/tdie-tlogcatcher-tjava-catching-message-triggered-by-tdie-component-standard-component "This example shows you how to use the tLogCatcher component to catch the message triggered by a tDie component.")
* [Displaying the statistics log of Job execution](https://help.qlik.com/talend/en-US/components/8.0/tlogrow-tstatcatcher-tfixedflowinput-tfileoutputdelimited-displaying-statistics-log-of-job-execution-standard-component-this)
* [Setting up the assertive condition for a Job execution](https://help.qlik.com/talend/en-US/components/8.0/tassert-tassertcatcher-tfileoutputdelimited-setting-up-assertive-condition-for-job-execution-standard-component-this)
* [Viewing product orders status (on a daily basis) against a benchmark number](https://help.qlik.com/talend/en-US/components/8.0/tassert-tlogrow-tmysqloutput-viewing-product-orders-status-on-daily-basis-against-benchmark-number-standard-component-this)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-standard-properties -->

# tLogRow Standard properties

These properties are used to configure tLogRow running in the Standard Job framework.

The Standard tLogRow component belongs to the Logs & Errors family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <p>This component offers the advantage of the                  dynamic schema feature. This allows you to retrieve unknown columns from source                  files or to copy batches of columns from a source without mapping each column                  individually. For further information about dynamic schemas, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema" target="_blank">Dynamic schema</a>.</p> <p>This            dynamic schema feature is designed for the purpose of retrieving unknown columns of a            table and is recommended to be used for this purpose only; it is not recommended for the            use of creating tables.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Sync columns | Click to synchronize the output file schema with the input<br>file schema. The Sync function is available only when the component is<br>linked with the preceding component using a Row connection. |
| Basic | Displays the output flow in basic mode. |
| Table | Displays the output flow in table cells. |
| Vertical | Displays each row of the output flow as a key-value list.<br><br>With this mode selected, you can choose to show either the unique name<br>or the label of component, or both of them, for each output row. |
| Separator<br><br>(For Basic mode only) | Enter the separator which will delimit data on the Log display. |
| Print header<br><br>(For Basic mode only) | Select this check box to include the header of the input<br>flow in the output display. |
| Print component unique name in front of each<br>output row<br><br>(For Basic mode only) | Select this check box to show the unique name the component in front<br>of each output row to differentiate outputs in case several tLogRow components are used. |
| Print schema column name in front of each<br>value<br><br>(For Basic mode only) | Select this check box to retrieve column labels from output<br>schema. |
| Use fixed length for values<br><br>(For Basic mode only) | Select this check box to set a fixed width for the value<br>display. |
| Print content with log4j | Select this check box to output the data flow content if the log4j<br>feature is activated and the log4j output level is set to INFO or lower<br>than INFO for your Job. For how to activate the log4j feature and<br>customize the log4j output level, refer to *Talend Studio*<br>*User<br>Guide*. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component can be used as intermediate step in a data flow<br>or as an end object in the Job flowchart. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-properties-for-apache-spark-batch -->

# tLogRow properties for Apache Spark Batch

These properties are used to configure tLogRow running in the Spark Batch Job framework.

The Spark Batch tLogRow component belongs to the Misc family.

The component in this framework is available in all subscription-based Talend products with Big Data and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Define a storage configuration<br>component | Select the configuration component to be used to provide the configuration<br>information for the connection to the target file system such as HDFS.<br><br>If you leave this check box clear, the target file system is the local<br>system.<br><br>The configuration component to be used must be present in the same Job.<br>For example, if you have dropped a tHDFSConfiguration component in the Job, you can select it to write<br>the result in a given HDFS system. |
| Schema and Edit schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <p>This component offers the advantage of the                  dynamic schema feature. This allows you to retrieve unknown columns from source                  files or to copy batches of columns from a source without mapping each column                  individually. For further information about dynamic schemas, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema" target="_blank">Dynamic schema</a>.</p> <p>This            dynamic schema feature is designed for the purpose of retrieving unknown columns of a            table and is recommended to be used for this purpose only; it is not recommended for the            use of creating tables.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Sync columns | Click to synchronize the output file schema with the input file schema.<br>The Sync function is available only when the component is linked with the<br>preceding component using a Row<br>connection. |
| Basic | Displays the output flow in basic mode. |
| Table | Displays the output flow in table cells. |
| Vertical | Displays each row of the output flow as a key-value list.<br><br>With this mode selected, you can choose to show either<br>the unique name or the label of component, or both of them, for each<br>output row. |
| Separator<br><br>(For Basic mode only) | Enter the separator which will delimit data on the Log<br>display. |
| Print header<br><br>(For Basic mode only) | Select this check box to include the header of the input flow in the<br>output display. |
| Print component unique name in front of each<br>output row<br><br>(For Basic mode only) | Select this check box to show the unique name the<br>component in front of each output row to differentiate outputs in case<br>several tLogRow components are<br>used. |
| Print schema column name in front of each<br>value<br><br>(For Basic mode only) | Select this check box to retrieve column labels from<br>output schema. |
| Use fixed length for values<br><br>(For Basic mode only) | Select this check box to set a fixed width for the value<br>display. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use local timezone for date | Select this check box to use the local date of the machine in which your Job is executed. If leaving this check box clear, UTC is automatically used to format the Date-type data. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate or an end step.<br><br>This component, along with the Spark Batch component Palette it belongs to,<br>appears only when you are creating a Spark Batch Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a<br>scenario presents only Standard Jobs, that is to<br>say traditional<br>Talend<br>data integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-properties-for-apache-spark-streaming -->

# tLogRow properties for Apache Spark Streaming (deprecated)

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

These properties are used to configure tLogRow running in the Spark Streaming Job framework.

Information noteDeprecation: Spark Streaming is deprecated beginning with the R2026-09 release. Use Spark Structured Streaming instead.

The Spark Streaming tLogRow component belongs to the Misc family.

This component is available in Talend Real-Time Big Data Platform and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Sync columns | Click to synchronize the output file schema with the input file schema. The<br>Sync function is available only when the component is linked with the preceding<br>component using a Row connection. |
| Basic | Displays the output flow in basic mode. |
| Table | Displays the output flow in table cells. |
| Vertical | Displays each row of the output flow as a key-value list.<br><br>With this mode selected, you can choose to show either the<br>unique name or the label of component, or both of them, for each output<br>row. |
| Separator<br><br>(For Basic mode only) | Enter the separator which will delimit data on the Log<br>display. |
| Print header<br><br>(For Basic mode only) | Select this check box to include the header of the input flow in the output<br>display. |
| Print component unique name in front of each output<br>row<br><br>(For Basic mode only) | Select this check box to show the unique name the component in<br>front of each output row to differentiate outputs in case several tLogRow components are used. |
| Print schema column name in front of each<br>value<br><br>(For Basic mode only) | Select this check box to retrieve column labels from output<br>schema. |
| Use fixed length for values<br><br>(For Basic mode only) | Select this check box to set a fixed width for the value<br>display. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use local timezone for date | Select this check box to use the local date of the machine in which your Job is executed. If leaving this check box clear, UTC is automatically used to format the Date-type data. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate or an end step.<br><br>This component, along with the Spark Streaming component Palette it belongs to, appears<br>only when you are creating a Spark Streaming Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a scenario presents<br>only Standard Jobs, that is to say traditional<br>Talend<br>data<br>integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-properties-for-apache-spark-structured-streaming -->

# tLogRow properties for Apache Spark Structured Streaming

[Preview](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/feature-preview-program-overview.htm)

Use these properties to configure tLogRow running in the Spark Structured Streaming Job framework.

The Spark Structured Streaming tLogRow component belongs to the Misc family.

This component is available in Talend Real-Time Big Data Platform and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Basic | Displays the output flow in Basic mode. The following properties are available in this mode:<br><br><ul> <li><span>Field Separator</span>: Enter the separator to delimit data in the log display.</li> <li><span>Print header</span>: Select this check box to include the header of the input flow in the output display.</li> <li><span>Print component unique name in front of each output row</span>: Select this check box to show the unique name of the component in front of each output row, to differentiate outputs when several <span>tLogRow</span> components are used.</li> <li><span>Print schema column name in front of each value</span>: Select this check box to retrieve column labels from the output schema.</li> <li><span>Use fixed length for values</span>: Select this check box to use a fixed length for the value display.</li> </ul> |
| Table | Displays the output flow in table cells. |
| Vertical | Displays each row of the output flow as a key-value list. Select how to identify each output row in the Title printing mode field:<br><br><ul> <li><span>Print unique name</span>: Shows the unique name of the component.</li> <li><span>Print label</span>: Shows the label of the component.</li> <li><span>Print unique name and label</span>: Shows both the unique name and the label.</li> </ul> |
| Output mode | Select the output mode from the drop-down list:<br><br><ul> <li><span>Append</span>: Adds new rows to the output without                        modifying existing rows.</li> <li><span>Complete</span>: Overwrites the entire output with the                        updated result after every trigger.</li> <li><span>Update</span>: Writes only the rows that were updated since                        the last trigger.</li> </ul><br><br>Information noteNote: When groupBy is enabled, set the output mode to<br>Complete or Update. If<br>groupBy is not used, set the output mode to<br>Append. |
| Set trigger | Select this check box to set a trigger for the streaming query:<br><br><ul> <li><span>Available now</span>: Processes all available data and stops.</li> <li><span>Fixed interval</span>: Processes data at a fixed time interval. In the <span>Duration</span> field, enter the interval. For example, <span>10 seconds</span>.</li> </ul> |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use local timezone for date | Select this check box to use the local date of the machine in which your Job is executed. If leaving this check box clear, UTC is automatically used to format the Date-type data. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate or an end step.<br><br>This component, along with the Spark Structured Streaming component Palette it belongs to,<br>appears only when you are creating a Spark Structured Streaming Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a scenario presents<br>only Standard Jobs, that is to say traditional<br>Talend<br>data<br>integration Jobs. |
| Spark Connection | You need to use the Structured Streaming Configuration<br>tab in the Run view to define the connection to a Spark cluster for<br>the whole Job.<br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tlogrow-tstatcatcher-tfixedflowinput-tfileoutputdelimited-displaying-statistics-log-of-job-execution-standard-component-this -->

# Displaying the statistics log of Job execution

This scenario collects the statistics log for the Job execution and displays it on the Run console. Note that, since the tStatCatcher Statistics check box is not selected for the components, the statistics log applies solely to this specific Job.

### In this section

* [Linking the components](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-tstatcatcher-tfixedflowinput-tfileoutputdelimited-linking-components-standard-component-drop)
* [Configuring the components](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-tstatcatcher-tfixedflowinput-tfileoutputdelimited-configuring-components-standard-component)
* [Executing the Job](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-tstatcatcher-tfixedflowinput-tfileoutputdelimited-executing-job-standard-component-press)

**Related concepts**

* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/tlogrow "Displays data or results in the Run console to monitor data processed.")

**Related reference**

* [tStatCatcher](https://help.qlik.com/talend/en-US/components/8.0/tstatcatcher "Gathers the Job processing metadata at the Job level and at the component level and transfers the log data to the subsequent component for display or storage.")

**Related information**

* [tFileOutputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited)
* [tFixedFlowInput](https://help.qlik.com/talend/en-US/components/8.0/tfixedflowinput/tfixedflowinput)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-tstatcatcher-tfixedflowinput-tfileoutputdelimited-linking-components-standard-component-drop -->

# Linking the components

## Procedure

1. Drop tFixedFlowInput, tFileOutputDelimited, tStatCatcher and tLogRow onto the workspace.
2. Link tFixedFlowInput to tFileOutputDelimited using a Row &gt; Main connection.
3. Link tStatCatcher to tLogRow using a Row &gt; Main connection.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case_tstatcatcher_1.png)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-tstatcatcher-tfixedflowinput-tfileoutputdelimited-configuring-components-standard-component -->

# Configuring the components

## Procedure

1. Double-click tFixedFlowInput to open its Basic settings view.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case_tstatcatcher_2.png)
2. Click the Edit schema button to open the schema editor.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case_tstatcatcher_3.png)
3. Click the [+] button to add three columns, namely *ID\_Owners*, *Name\_Customer* and *ID\_Insurance*, of the Integer and String types respectively.
4. Click Ok to validate the setup and close the editor.
5. In the dialog box that appears, click Yes to propagate the changes to the subsequent component.
6. Select the Use Inline Content (delimited file) option.
7. In the Content box, enter 1;Andrew;888.
8. Double-click tFileOutputDelimited to open its Basic settings view.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case_tstatcatcher_5.png)
9. In the File Name field, enter the full name of the file to save the statistics data.
10. Double-click tLogRow to open its Basic settings view.

    ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case_tstatcatcher_6.png)
11. Select Vertical (each row is a key/value list) for a better display of the results.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow-tstatcatcher-tfixedflowinput-tfileoutputdelimited-executing-job-standard-component-press -->

# Executing the Job

## Procedure

1. Press Ctrl + S to save the Job.
2. Press F6 to run the Job.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case_tstatcatcher_7.png)

   As shown above, the statistics log of the Job execution is correctly generated.
