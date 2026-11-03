# trowgenerator (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/trowgenerator  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/trowgenerator -->

# tRowGenerator

### In this section

* [tRowGenerator component](https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-component)
* [tRowGenerator scenario](https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-scenario)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-component -->

# tRowGenerator component

| [tRowGenerator](https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator) | Creates an input flow in a Job for testing purposes, in particular for boundary<br>test sets. |
| --- | --- |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-scenario -->

# tRowGenerator scenario

* [Generating random Java data](https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-tlogrow-generating-random-java-data-standard-component-the)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator -->

# tRowGenerator

Creates an input flow in a Job for testing purposes, in particular for boundary test sets.

tRowGenerator generates as many rows and fields as are required using random values taken from a list.

### In this section

* [tRowGenerator Standard properties](https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-standard-properties)
* [tRowGenerator properties for Apache Spark Batch](https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-properties-for-apache-spark-batch)
* [tRowGenerator properties for Apache Spark Streaming (deprecated)](https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-properties-for-apache-spark-streaming)

**Related tasks**

* [Generating random Java data](https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-tlogrow-generating-random-java-data-standard-component-the "The following scenario creates a two-component Job, generating 50 rows structured as follows: a randomly picked-up ID in a 1-to-3 range, a random ascii First Name and Last Name generation and a random date taken in a defined range.")


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-tlogrow-generating-random-java-data-standard-component-the -->

# Generating random Java data

The following scenario creates a two-component Job, generating 50 rows structured as follows: a randomly picked-up ID in a 1-to-3 range, a random ascii First Name and Last Name generation and a random date taken in a defined range.

![Job description.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tRowGenerator1.png)

## Procedure

1. Place a tRowGenerator and a tLogRow component from the Palette to the design workspace.
2. Right-click tRowGenerator and select Row &gt; Main. Drag this main row link onto the tLogRow component and release when the plug symbol displays.
3. Double-click tRowGenerator to open the Editor.
4. Define the fields to be generated. ![Editor for tRowGenerator.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tRowGenerator2.png)
   * The random ID column is of integer type, the First and Last names are of string type and the Date is of date type.

   * In the Function list, select the relevant function or set on the three dots for custom function.

   * On the Function parameters tab, define the Values to be randomly picked up.![Value column.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tRowGenerator3.png)

   * First\_Name and Last\_Name columns are to be generated using the getAsciiRandomString function that is predefined in the system routines. By default, the length defined is 6 characters long. You can change this if need be.

   * The Date column calls the predefined getRandomDate function. You can edit the parameter values in the Function parameters tab.
5. Set the Number of Rows to be generated to 50.
6. Click OK to validate the setting.
7. Double-click tLogRow to view the Basic settings. The default setting is retained for this Job.
8. Press F6 to run the Job.

   The 50 rows are generated following the setting defined in the tRowGenerator editor and the output is displayed in the Run console.

   ![Job results.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tRowGenerator4.png)

**Related concepts**

* [tRowGenerator](https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator "Creates an input flow in a Job for testing purposes, in particular for boundary test sets.")

**Related information**

* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-standard-properties -->

# tRowGenerator Standard properties

These properties are used to configure tRowGenerator running in the Standard Job framework.

The Standard tRowGenerator component belongs to the Misc family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul><br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| RowGenerator editor | The editor allows you to define the columns and the nature of<br>data to be generated. You can use predefined routines or type in the function<br>to be used to generate the data specified. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this checkbox to collect log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE:<br>the number of rows processed. This is an After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| Usage rules | The tRowGenerator Editor's ease of<br>use allows users without any Java knowledge to generate random data for test<br>purposes.<br><br>Information noteNote: When running on Java 17 or later, the<br>getAsciiRandomString function uses the<br>SHA1PRNG algorithm to generate random strings, restoring<br>the performance of earlier Java versions. If SHA1PRNG is<br>unavailable in your runtime environment, the component falls back to the JDK or<br>OS default algorithm automatically. |

### In this section

* [Defining the schema](https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-trowgenerator-defining-schema-standard-component-first)
* [Defining the function](https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-trowgenerator-defining-function-standard-component-select)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-properties-for-apache-spark-batch -->

# tRowGenerator properties for Apache Spark Batch

These properties are used to configure tRowGenerator running in the Spark Batch Job framework.

The Spark Batch tRowGenerator component belongs to the Misc family.

The component in this framework is available in all subscription-based Talend products with Big Data and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Define a storage configuration<br>component | Select the configuration component to be used to provide the configuration<br>information for the connection to the target file system such as HDFS.<br><br>If you leave this check box clear, the target file system is the local<br>system.<br><br>The configuration component to be used must be present in the same Job.<br>For example, if you have dropped a tHDFSConfiguration component in the Job, you can select it to write<br>the result in a given HDFS system. |
| Schema and Edit<br>schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul><br><br>The schema of tRowGenerator does not support the Object type.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| RowGenerator editor | The editor allows you to define the columns and the nature of data to<br>be generated. You can use predefined routines or type in the function to<br>be used to generate the data specified. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as a start component and requires an<br>output link.<br><br>This component, along with the Spark Batch component Palette it belongs to,<br>appears only when you are creating a Spark Batch Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a<br>scenario presents only Standard Jobs, that is to<br>say traditional<br>Talend<br>data integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/trowgenerator/trowgenerator-properties-for-apache-spark-streaming -->

# tRowGenerator properties for Apache Spark Streaming (deprecated)

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

These properties are used to configure tRowGenerator running in the Spark Streaming Job framework.

Information noteDeprecation: Spark Streaming is deprecated beginning with the R2026-09 release. Use Spark Structured Streaming instead.

The Spark Streaming tRowGenerator component belongs to the Misc family.

This component is available in Talend Real-Time Big Data Platform and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul><br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| RowGenerator editor | The editor allows you to define the columns and the nature of<br>data to be generated. You can use predefined routines or type in the function<br>to be used to generate the data specified.<br><br>The value *-1* in the Number of rows for RowGenerator field in the<br>RowGenerator editor means to generate<br>infinite rows of input data. |
| Input repetition interval (ms) | Enter the time interval (in milliseconds) at the end of which<br>tRowGenerator generates a batch of<br>data. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as a start component and requires an<br>output link.<br><br>This component, along with the Spark Streaming component Palette it belongs to, appears<br>only when you are creating a Spark Streaming Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a scenario presents<br>only Standard Jobs, that is to say traditional<br>Talend<br>data<br>integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |
