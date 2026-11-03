# tjavarow (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tjavarow  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tjavarow -->

# tJavaRow

Provides a code editor that lets you enter the Java code to be applied to each row of the flow.

tJavaRow allows you to enter customized code which you can integrate in a Talend program.

### In this section

* [tJavaRow Standard properties](https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-standard-properties)
* [tJavaRow properties for Apache Spark Batch](https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-properties-for-apache-spark-batch)
* [tJavaRow properties for Apache Spark Streaming (deprecated)](https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-properties-for-apache-spark-streaming)

**Related concepts**

* [Transforming data line by line using tJavaRow](https://help.qlik.com/talend/en-US/components/8.0/tjavarow-tfileinputdelimited-transforming-data-line-by-line-using-tjavarow-standard-component-in-this)
* [Using tJavaRow to handle file content based on a dynamic schema](https://help.qlik.com/talend/en-US/components/8.0/tjavarow-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-using-tjavarow-to-handle-file-content-based-on-dynamic-schema-standard-component-enterprise-this)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-standard-properties -->

# tJavaRow Standard properties

These properties are used to configure tJavaRow running in the Standard Job framework.

The Standard tJavaRow component belongs to the Custom Code family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>This component offers the advantage of the                  dynamic schema feature. This allows you to retrieve unknown columns from source                  files or to copy batches of columns from a source without mapping each column                  individually. For further information about dynamic schemas, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema" target="_blank">Dynamic schema</a>.</p> <p>This            dynamic schema feature is designed for the purpose of retrieving unknown columns of a            table and is recommended to be used for this purpose only; it is not recommended for the            use of creating tables.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <p>Click <span>Sync        columns</span> to retrieve the schema from the previous component connected in the      Job.</p> </li> </ul> |
| Generate code | Click this button to automatically generate the code in the Code field to map the columns of the input schema with those of the output<br>schema. This generation does not change anything in your schema.<br><br>The principle of this mapping is to relate the columns that have the same column name.<br>Then you can adapt the generated code depending on the actual map you need. |
| Code | Enter the Java code to be applied to each line of the data<br>flow. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Import | Enter the Java code to import, if necessary, external libraries<br>used in the Code field of the Basic settings view. |
| tStatCatcher Statistics | Select this check box to collect the log data at a component<br>level.. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables).<br><br>To enter a global variable (for example *COUNT* of tFileRowCount) in the Code box, you need to type in the entire piece of code manually, that<br>is to say *((Integer)globalMap.get("tFileRowCount\_COUNT"))*. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediary between two other<br>components. It must be linked to both an input and an output<br>component. |
| Function | tJavaRow allows you to enter<br>customized code which you can integrate in a Talend programme. With tJavaRow, you can enter the Java code to be<br>applied to each row of the flow. |
| Purpose | tJavaRow allows you to broaden the<br>functionality of<br>Talend<br>Jobs, using the<br>Java language. |
| Limitation | Knowledge of Java language is necessary. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-properties-for-apache-spark-batch -->

# tJavaRow properties for Apache Spark Batch

These properties are used to configure tJavaRow running in the Spark Batch Job framework.

The Spark Batch tJavaRow component belongs to the Custom Code family.

The component in this framework is available in all subscription-based Talend products with Big Data and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <p>Click <span>Sync        columns</span> to retrieve the schema from the previous component connected in the      Job.</p> <p>Note that the input schema and the output schema of this component can                            be different.</p> </li> </ul> |
| Map type | Select the type of the Map transformation you need to write. This<br>allows the component to automatically select the method accordingly and<br>declare the variables to be used in your custom code.<br><br>The available types are:<br><br><ul> <li> <p> <span>Map</span>: it returns only one                                        output record for each input record. It uses Spark's                                            <em>PairFunction</em>                                        method</p> </li> <li> <p> <span>FlatMap</span>: it returns 0 or                                        more output records for each input record. It uses Spark's                                            <em>FlatMapFunction</em>                                        method.</p> </li> </ul><br><br>For further information about these methods, see Apache Spark's<br>documentation about its Java API in https://spark.apache.org/docs/latest/api/java/index.html. |
| Generate code | Click this button to automatically generate the code in the Code field to map the columns of the input schema with those of the output<br>schema. This generation does not change anything in your schema.<br><br>The generated sample code shows what the pre-defined variables are for the input and the<br>output RDDs and how these variables can be used. |
| Code | Write the custom body of the method you have selected from the<br>Map type drop-down list. You need<br>to use the input schema and the output schema to manage the columns of<br>the input and the output RDD records. This custom code is applied on a<br>row-by-row basis in the RDD records.<br><br>For example, the input schema contains a *user* column, then you need to use the *input.user* variable to get the *user* column of each input record.<br><br>For further information about the available variables in writing the<br>custom code, see the default comment displayed in this field. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Import | Enter the Java code to import, if necessary, external libraries<br>used in the Code field of the Basic settings view. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables).<br><br>To enter a global variable (for example *COUNT* of tFileRowCount) in the Code box, you need to type in the entire piece of code manually, that<br>is to say *((Integer)globalMap.get("tFileRowCount\_COUNT"))*. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate step.<br><br>This component, along with the Spark Batch component Palette it belongs to,<br>appears only when you are creating a Spark Batch Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a<br>scenario presents only Standard Jobs, that is to<br>say traditional<br>Talend<br>data integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |
| Limitation | Knowledge of Spark and Java language is necessary. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-properties-for-apache-spark-streaming -->

# tJavaRow properties for Apache Spark Streaming (deprecated)

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

These properties are used to configure tJavaRow running in the Spark Streaming Job framework.

Information noteDeprecation: Spark Streaming is deprecated beginning with the R2026-09 release. Use Spark Structured Streaming instead.

The Spark Streaming tJavaRow component belongs to the Custom Code family.

This component is available in Talend Real-Time Big Data Platform and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> <p>When the schema to be reused has default values that are            integers or functions, ensure that these default values are not enclosed within            quotation marks. If they are, you must remove the quotation marks manually.</p> <p>For more information, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/retrieving-table-schemas?tocId=_C1~eFOlN~GM_JR2qkBYZg" target="_blank">Retrieving table schemas</a>.</p> </li> <li> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> <p>Click <span>Sync        columns</span> to retrieve the schema from the previous component connected in the      Job.</p> <p>Note that the input schema and the output schema of this component can                            be different.</p> </li> </ul> |
| Map type | Select the type of the Map transformation you need to write. This<br>allows the component to automatically select the method accordingly and<br>declare the variables to be used in your custom code.<br><br>The available types are:<br><br><ul> <li> <p> <span>Map</span>: it returns only one                                        output record for each input record. It uses Spark's                                            <em>PairFunction</em>                                        method</p> </li> <li> <p> <span>FlatMap</span>: it returns 0 or                                        more output records for each input record. It uses Spark's                                            <em>FlatMapFunction</em>                                        method.</p> </li> </ul><br><br>For further information about these methods, see Apache Spark's<br>documentation about its Java API in https://spark.apache.org/docs/latest/api/java/index.html. |
| Generate code | Click this button to automatically generate the code in the Code field to map the columns of the input schema with those of the output<br>schema. This generation does not change anything in your schema.<br><br>The generated sample code shows what the pre-defined variables are for the input and the<br>output RDDs and how these variables can be used. |
| Code | Write the custom body of the method you have selected from the<br>Map type drop-down list. You need<br>to use the input schema and the output schema to manage the columns of<br>the input and the output RDD records. This custom code is applied on a<br>row-by-row basis in the RDD records.<br><br>For example, the input schema contains a *user* column, then you need to use the *input.user* variable to get the *user* column of each input record.<br><br>For further information about the available variables in writing the<br>custom code, see the default comment displayed in this field. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Import | Enter the Java code to import, if necessary, external libraries<br>used in the Code field of the Basic settings view. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate step.<br><br>This component, along with the Spark Streaming component Palette it belongs to, appears<br>only when you are creating a Spark Streaming Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a scenario presents<br>only Standard Jobs, that is to say traditional<br>Talend<br>data<br>integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |
| Limitation | Knowledge of Spark and Java language is necessary. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tjavarow-tfileinputdelimited-transforming-data-line-by-line-using-tjavarow-standard-component-in-this -->

# Transforming data line by line using tJavaRow

In this scenario, the information of a few cities read from an input delimited file is transformed using Java code through the tJavaRow component and printed on the console.

![](https://help.qlik.com/talend/en-US/components/Resources/images/use_case-tjavarow1-1.png)

### In this section

* [Setting up the Job](https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-setting-up-job-standard-component-drop)
* [Configuring the components](https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-configuring-components-standard-component)
* [Saving and executing the Job](https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-saving-and-executing-job-standard-component-press)

**Related concepts**

* [tJavaRow](https://help.qlik.com/talend/en-US/components/8.0/tjavarow "Provides a code editor that lets you enter the Java code to be applied to each row of the flow.")

**Related information**

* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tjavarow-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-using-tjavarow-to-handle-file-content-based-on-dynamic-schema-standard-component-enterprise-this -->

# Using tJavaRow to handle file content based on a dynamic schema

This scenario applies only to subscription-based Talend products.

This scenario describes a three-component Job that uses Java code through a tJavaRow component to display the content of an input file and pass it to the output component. As all the components in this Job support the dynamic schema feature, we can leverage this feature to save the time of configuring each column of the schema.

### In this section

* [Setting up the Job](https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-setting-up-job-standard-component-enterprise-drop)
* [Configuring the input and output components](https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-configuring-input-and-output-components-standard-component-enterprise)
* [Configuring the tJavaRow component](https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-configuring-tjavarow-component-standard-component-enterprise)
* [Saving and executing the Job](https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-saving-and-executing-job-standard-component-enterprise-press)

**Related concepts**

* [tJavaRow](https://help.qlik.com/talend/en-US/components/8.0/tjavarow "Provides a code editor that lets you enter the Java code to be applied to each row of the flow.")

**Related information**

* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited)
* [tFileOutputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-setting-up-job-standard-component-drop -->

# Setting up the Job

## Procedure

1. Drop a tFileInputDelimited component and a tJavaRow component from the Palette onto the design workspace, and label them to better identify their roles in the Job.
2. Connect the two components using a Row &gt; Main connection.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-configuring-components-standard-component -->

# Configuring the components

## Procedure

1. Double-click the tFileInputDelimited component to display its Basic settings view in the Component tab.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tjavarow1-2.png)
2. In the File name/Stream field, type in the path to the input file in double quotation marks, or browse to the path by clicking the [...] button, and define the first line of the file as the header.

   In this example, the input file has the following content:
   ```
   City;Population;LandArea;PopDensity
   Beijing;10233000;1418;7620
   Moscow;10452000;1081;9644
   Seoul;10422000;605;17215
   Tokyo;8731000;617;14151
   New York;8310000;789;10452
   ```
3. Click the [...] button next to Edit schema to open the Schema dialog box, and define the data structure of the input file. Then, click OK to validate the schema setting and close the dialog box.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tjavarow1-3.png)
4. Double-click the tJavaRow component to display its Basic settings view in the Component tab.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tjavarow1-4.png)
5. Click Sync columns to make sure that the schema is correctly retrieved from the preceding component.
6. In the Code field, enter the code to be applied on each line of data based on the defined schema columns.

   In this example, we want to transform the city names to upper case, group digits of numbers larger than 1000 using the thousands separator for ease of reading, and print the data on the console:
   ```
   System.out.print("\n" + input_row.City.toUpperCase() + ":");
   System.out.print("\n - Population: " 
   + FormatterUtils.format_Number(String.valueOf(input_row.Population), ',', '.') + " people");
   System.out.print("\n - Land area: " 
   + FormatterUtils.format_Number(String.valueOf(input_row.LandArea), ',', '.') 
   + " km2");
   System.out.print("\n - Population density: " 
   + FormatterUtils.format_Number(String.valueOf(input_row.PopDensity), ',', '.') + " people/km2\n");
   ```

   Information noteNote:

   In the Code field, input\_row refers to the link that connects to tJavaRow.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-saving-and-executing-job-standard-component-press -->

# Saving and executing the Job

## Procedure

1. Press Ctrl+S to save your Job.
2. Press F6 or click Run on the Run tab to execute the Job.

   The city information is transformed by the Java code set through tJavaRow and displayed on the console.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tjavarow1-5.png)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-setting-up-job-standard-component-enterprise-drop -->

# Setting up the Job

## Procedure

1. Drop tFileInputDelimited, tJavaRow, and tFileOutputDelimited from the Palette onto the design workspace, and label them according to their roles in the Job.
2. Connect the components in a series using Row &gt; Main links.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tjavarow2-1.png)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-configuring-input-and-output-components-standard-component-enterprise -->

# Configuring the input and output components

## Procedure

1. Double-click the tFileInputDelimited component, which is labeled *Source*, to display its Basic settings view.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tjavarow2-2.png)

   Information noteWarning:

   *The dynamic schema feature is only supported in Built-In mode and requires the input file to have a header row.*
2. In the File name/Stream field, type in the path to the input file in double quotation marks, or browse to the path by clicking the [...] button.
3. In the Header field, type in *1* to define the first line of the file as the header.
4. Click the [...] button next to Edit schema to open the Schema dialog box.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tjavarow2-3.png)
5. Click the [+] button to add a column, give a name to the column, *dyna* in this example, and select Dynamic from the Type list. This dynamic column will retrieve the three columns, *FirstName*, *LastName* and *Address*, of the input file.
6. Click OK to validate the setting and close the dialog box.
7. Double-click the tFileOutputDelimited component, which is labeled *Target*, to display its Basic settings view.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tjavarow2-4.png)
8. Define the output file path in the File Name field.
9. Select the Include Header check box to include the header in the output file. Leave all the other settings are they are.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-configuring-tjavarow-component-standard-component-enterprise -->

# Configuring the tJavaRow component

## Procedure

1. Double-click tJavaRow to display its Basic settings view and define the components properties.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tjavarow2-5.png)
2. Click Sync columns to make sure that the schema is correctly retrieved from the preceding component.
3. In the Code field, enter the following code to display the content of the input file and pass the data to the next component based on the defined dynamic schema column:
   ```
   System.out.println(input_row.dyna);
   output_row.dyna = input_row.dyna;
   ```

   Information noteNote:

   In the Code field, input\_row and output\_row correspond to the links to and from tJavaRow.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/java-custom-code/tjavarow-tfileinputdelimited-tfileoutputdelimited-tfileoutputdelimited-saving-and-executing-job-standard-component-enterprise-press -->

# Saving and executing the Job

## Procedure

1. Press Ctrl+S to save your Job.
2. Pressing F6, or click Run on the Run tab to execute the Job.

   The content of the input file is displayed on the console and written to the output file.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/use_case-tjavarow2-6.png)
