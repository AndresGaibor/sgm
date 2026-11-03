# tfilterrow (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tfilterrow  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfilterrow -->

# tFilterRow

Filters input rows by setting one or more conditions on the selected columns.

### In this section

* [tFilterRow Standard properties](https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-standard-properties)
* [tFilterRow properties for Apache Spark Batch](https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-properties-for-apache-spark-batch)
* [tFilterRow properties for Apache Spark Streaming (deprecated)](https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-properties-for-apache-spark-streaming)
* [tFilterRow properties for Apache Spark Structured Streaming](https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-properties-for-apache-spark-structured-streaming)

**Related concepts**

* [Filtering a list of names through different logical operations](https://help.qlik.com/talend/en-US/components/8.0/tfilterrow-filtering-list-of-names-through-different-logical-operations-standard-component "Based on the previous scenario, this scenario further filters the input data so that only those records of people from New York and Chicago are accepted. Without changing the filter settings defined in the previous scenario, advanced conditions are added in this scenario to enable both logical AND and logical OR operations in the same tFilterRow component.")
* [Filtering a list of names using simple conditions](https://help.qlik.com/talend/en-US/components/8.0/tfilterrow-tlogrow-tfixedflowinput-tfixedflowinput-filtering-list-of-names-using-simple-conditions-standard-component-the)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-standard-properties -->

# tFilterRow Standard properties

These properties are used to configure tFilterRow running in the Standard Job framework.

The Standard tFilterRow component belongs to the Processing family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>Schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br>The schema of this component is built-in only.<br><br>This component offers the advantage of the<br>dynamic schema feature. This allows you to retrieve unknown columns from source<br>files or to copy batches of columns from a source without mapping each column<br>individually. For further information about dynamic schemas, see [Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema).<br><br>This<br>dynamic schema feature is designed for the purpose of retrieving unknown columns of a<br>table and is recommended to be used for this purpose only; it is not recommended for the<br>use of creating tables. |
| Logical operator used to combine conditions | Select a logical operator to combine simple conditions and to<br>combine the filter results of both modes if any advanced conditions<br>are defined.<br><br><br>And: returns the boolean value of<br>*true* if all conditions are<br>true; otherwise *false*. For each<br>two conditions combined using a logical AND, the second condition is<br>evaluated only if the first condition is evaluated to be<br>true.<br><br><br>Or: returns the boolean value of<br>*true* if any condition is<br>true; otherwise *false*. For each<br>two conditions combined using a logical OR, the second condition is<br>evaluated only if the first condition is evaluated to be<br>false. |
| Conditions | Click the plus button to add as many simple conditions as needed.<br>Based on the logical operator selected, the conditions are evaluated<br>one after the other in sequential order for each row. When<br>evaluated, each condition returns the boolean value of *true* or *false*.<br><br><br>Input column: Select the column of<br>the schema the function is to be operated on<br><br><br>Function: Select the function on<br>the list<br><br><br>Operator: Select the operator to<br>bind the input column with the value<br><br><br>Value: Type in the filtered value,<br>between quotes if needed. |
| Use advanced mode | Select this check box when the operations you want to perform<br>cannot be carried out through the standard functions offered, for<br>example, different logical operations in the same component. In the<br>text field, type in the regular expression as required.<br><br>If multiple advanced conditions are defined, use a logical<br>operator between two conditions:<br><br><br>&& (logical AND): returns the boolean value<br>of *true* if both conditions are<br>true; otherwise *false*. The second<br>condition is evaluated only if the first condition is evaluated to<br>be true.<br><br><br>\|\| (logical OR): returns the boolean value of<br>*true* if either condition is<br>true; otherwise *false*. The second<br>condition is evaluated only if the first condition is evaluated to<br>be false. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at the<br>Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>NB\_LINE\_OK: the<br>number of rows matching the filter. This is an After variable and it returns an<br>integer.<br><br><br>NB\_LINE\_REJECTED: the number of rows rejected. This is an After<br>variable and it returns an integer.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is not startable (green background) and it requires<br>an output component. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-properties-for-apache-spark-batch -->

# tFilterRow properties for Apache Spark Batch

These properties are used to configure tFilterRow running in the Spark Batch Job framework.

The Spark Batch tFilterRow component belongs to the Processing family.

The component in this framework is available in all subscription-based Talend products with Big Data and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>Schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields. |
| Logical operator used to combine conditions | Select a logical operator to combine simple conditions and to<br>combine the filter results of both modes if any advanced conditions<br>are defined.<br><br><br>And: returns the boolean value of<br>*true* if all conditions are<br>true; otherwise *false*. For each<br>two conditions combined using a logical AND, the second condition is<br>evaluated only if the first condition is evaluated to be<br>true.<br><br><br>Or: returns the boolean value of<br>*true* if any condition is<br>true; otherwise *false*. For each<br>two conditions combined using a logical OR, the second condition is<br>evaluated only if the first condition is evaluated to be<br>false. |
| Conditions | Click the plus button to add as many simple conditions as needed.<br>Based on the logical operator selected, the conditions are evaluated<br>one after the other in sequential order for each row. When<br>evaluated, each condition returns the boolean value of *true* or *false*.<br><br><br>Input column: Select the column of<br>the schema the function is to be operated on<br><br><br>Function: Select the function on<br>the list<br><br><br>Operator: Select the operator to<br>bind the input column with the value<br><br><br>Value: Type in the filtered value,<br>between quotes if needed. |
| Use advanced mode | Select this check box when the operations you want to perform<br>cannot be carried out through the standard functions offered, for<br>example, different logical operations in the same component. In the<br>text field, type in the regular expression as required.<br><br>If multiple advanced conditions are defined, use a logical<br>operator between two conditions:<br><br><br>&& (logical AND): returns the boolean value<br>of *true* if both conditions are<br>true; otherwise *false*. The second<br>condition is evaluated only if the first condition is evaluated to<br>be true.<br><br><br>\|\| (logical OR): returns the boolean value of<br>*true* if either condition is<br>true; otherwise *false*. The second<br>condition is evaluated only if the first condition is evaluated to<br>be false. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate step.<br><br>This component, along with the Spark Batch component Palette it belongs to,<br>appears only when you are creating a Spark Batch Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a<br>scenario presents only Standard Jobs, that is to<br>say traditional<br>Talend<br>data integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-properties-for-apache-spark-streaming -->

# tFilterRow properties for Apache Spark Streaming (deprecated)

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

These properties are used to configure tFilterRow running in the Spark Streaming Job framework.

Information noteDeprecation: Spark Streaming is deprecated beginning with the R2026-09 release. Use Spark Structured Streaming instead.

The Spark Streaming tFilterRow component belongs to the Processing family.

This component is available in Talend Real-Time Big Data Platform and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>Schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields. |
| Logical operator used to combine conditions | Select a logical operator to combine simple conditions and to<br>combine the filter results of both modes if any advanced conditions<br>are defined.<br><br><br>And: returns the boolean value of<br>*true* if all conditions are<br>true; otherwise *false*. For each<br>two conditions combined using a logical AND, the second condition is<br>evaluated only if the first condition is evaluated to be<br>true.<br><br><br>Or: returns the boolean value of<br>*true* if any condition is<br>true; otherwise *false*. For each<br>two conditions combined using a logical OR, the second condition is<br>evaluated only if the first condition is evaluated to be<br>false. |
| Conditions | Click the plus button to add as many simple conditions as needed.<br>Based on the logical operator selected, the conditions are evaluated<br>one after the other in sequential order for each row. When<br>evaluated, each condition returns the boolean value of *true* or *false*.<br><br><br>Input column: Select the column of<br>the schema the function is to be operated on<br><br><br>Function: Select the function on<br>the list<br><br><br>Operator: Select the operator to<br>bind the input column with the value<br><br><br>Value: Type in the filtered value,<br>between quotes if needed. |
| Use advanced mode | Select this check box when the operations you want to perform<br>cannot be carried out through the standard functions offered, for<br>example, different logical operations in the same component. In the<br>text field, type in the regular expression as required.<br><br>If multiple advanced conditions are defined, use a logical<br>operator between two conditions:<br><br><br>&& (logical AND): returns the boolean value<br>of *true* if both conditions are<br>true; otherwise *false*. The second<br>condition is evaluated only if the first condition is evaluated to<br>be true.<br><br><br>\|\| (logical OR): returns the boolean value of<br>*true* if either condition is<br>true; otherwise *false*. The second<br>condition is evaluated only if the first condition is evaluated to<br>be false. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate step.<br><br>This component, along with the Spark Streaming component Palette it belongs to, appears<br>only when you are creating a Spark Streaming Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a scenario presents<br>only Standard Jobs, that is to say traditional<br>Talend<br>data<br>integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-properties-for-apache-spark-structured-streaming -->

# tFilterRow properties for Apache Spark Structured Streaming

[Preview](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/feature-preview-program-overview.htm)

Use these properties to configure tFilterRow running in the Spark Structured Streaming Job framework.

The Spark Structured Streaming tFilterRow component belongs to the Processing family.

The streaming version of this component is available in Talend Real-Time Big Data Platform and in Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br><ul> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul><br><br>Click Edit schema to make changes to<br>the schema. If you make changes, the schema automatically becomes built-in.<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Logical operator used to combine conditions | Select a logical operator to combine simple conditions and the filter<br>results of both modes when you define advanced<br>conditions.<br><br>And: Returns true if all conditions<br>are true; otherwise false. The second condition is evaluated only if the<br>first is true.<br><br>Or: Returns true if any<br>condition is true; otherwise false. The second condition is evaluated<br>only if the first is false. |
| Conditions | Click + to add simple conditions. Based on the<br>selected logical operator, the component evaluates conditions sequentially for<br>each row and returns true or false.<br><br>Input column: Select the<br>schema column to apply the function to.<br><br>Function:<br>Select the function from the list.<br><br>Operator:<br>Select the operator to bind the input column with the<br>value.<br><br>Value: Enter the filter value, in<br>quotation marks if required. |
| Use advanced mode | Select this check box when standard functions cannot perform the required<br>operations. Enter a regular expression in the text field.<br><br>If<br>multiple advanced conditions are defined, use a logical operator to combine<br>conditions:<br><br>&& (logical AND): Returns<br>true if both conditions are true. The second condition is evaluated<br>only if the first is true.<br><br>\|\| (logical OR): Returns<br>true if either condition is true. The second condition is evaluated<br>only if the first is false. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate step.<br><br>This component, along with the Spark Structured Streaming component Palette it belongs to,<br>appears only when you are creating a Spark Structured Streaming Job. |
| Spark Connection | You need to use the Structured Streaming Configuration<br>tab in the Run view to define the connection to a Spark cluster for<br>the whole Job.<br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfilterrow-tlogrow-tfixedflowinput-tfixedflowinput-filtering-list-of-names-using-simple-conditions-standard-component-the -->

# Filtering a list of names using simple conditions

The following scenario shows a Job that uses simple conditions to filter a list of records. This scenario will output two tables: the first will list all male persons with a last name shorter than nine characters and aged between 10 and 80 years; the second will list all rejected records. An error message for each rejected record will display in the same table to explain why such a record has been rejected.

![](https://help.qlik.com/talend/en-US/components/Resources/images/Use_Case_tFilterRow1.png)

### In this section

* [Dropping and linking components](https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-tlogrow-tfixedflowinput-tfixedflowinput-dropping-and-linking-components-standard-component-drop)
* [Configuring the components](https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-tlogrow-tfixedflowinput-tfixedflowinput-configuring-components-standard-component)
* [Executing the Job](https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-tlogrow-tfixedflowinput-tfixedflowinput-executing-job-standard-component-save)

**Related concepts**

* [tFilterRow](https://help.qlik.com/talend/en-US/components/8.0/tfilterrow "Filters input rows by setting one or more conditions on the selected columns.")

**Related information**

* [tFixedFlowInput](https://help.qlik.com/talend/en-US/components/8.0/tfixedflowinput/tfixedflowinput)
* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-tlogrow-tfixedflowinput-tfixedflowinput-dropping-and-linking-components-standard-component-drop -->

# Dropping and linking components

## Procedure

1. Drop tFixedFlowInput, tFilterRow and tLogRow from the Palette onto the design workspace.
2. Connect the tFixedFlowInput to the tFilterRow, using a Row &gt; Main link. Then, connect the tFilterRow to the tLogRow, using a Row &gt; Filter link.
3. Drop tLogRow from the Palette onto the design workspace and rename it as *reject*. Then, connect the tFilterRow to the *reject*, using a Row &gt; Reject link.
4. Label the components to better identify their roles in the Job.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-tlogrow-tfixedflowinput-tfixedflowinput-configuring-components-standard-component -->

# Configuring the components

## Procedure

1. Double-click tFixedFlowInput to display its Basic settings view and define its properties.
2. Click the [...] button next to Edit schema to define the schema for the input data. In this example, the schema is made of the following four columns: *LastName* (type String), *Gender* (type String), *Age* (type Integer) and *City* (type String).

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFilterRow3.1.png)

   When done, click OK to validate the schema setting and close the dialog box. A new dialog box opens and asks you if you want to propagate the schema. Click Yes.
3. Set the row and field separators in the corresponding fields if needed. In this example, use the default settings for both, namely the row separator is a carriage return and the field separator is a semi-colon.
4. Select the Use Inline Content(delimited file) option in the Mode area and type in the input data in the Content field.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFilterRow2.png)

   The input data used in this example is shown below:
   ```
   Van Buren;M;73;Chicago
   Adams;M;40;Albany
   Jefferson;F;66;New York
   Adams;M;9;Albany
   Jefferson;M;30;Chicago
   Carter;F;26;Chicago
   Harrison;M;40;New York
   Roosevelt;F;15;Chicago
   Monroe;M;8;Boston
   Arthur;M;20;Albany
   Pierce;M;18;New York
   Quincy;F;83;Albany
   McKinley;M;70;Boston
   Coolidge;M;4;Chicago
   Monroe;M;60;Chicago
   ```
5. Double-click tFilterRow to display its Basic settings view and define its properties.

   ![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFilterRow4.png)
6. In the Conditions table, add four conditions and fill in the filtering parameters.
   * From the InputColumn list field of the first row, select *LastName*, from the Function list field, select Length, from the Operator list field, select Lower than, and in the Value column, type in *9* to limit the length of last names to nine characters.

   * From the InputColumn list field of the second row, select *Gender*, from the Operator list field, select Equals, and in the Value column, type in *M* in double quotes to filter records of male persons.

     Information noteWarning:

     In the Value field, you must type in your values between double quotes for all types of values, except for integer values, which do not need quotes.

   * From the InputColumn list field of the third row, select *Age*, from the Operator list field, select Greater than, and in the Value column, type in *10* to set the lower limit to 10 years.

   * From the InputColumn list field of the four row, select *Age*, from the Operator list field, select Lower than, and in the Value column, type in *80* to set the upper limit to 80 years.
7. To combine the conditions, select And as that only those records that meet all the defined conditions are accepted.
8. In the Basic settings of tLogRow components, select Table (print values in cells of a table) in the Mode area.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tfilterrow-tlogrow-tfixedflowinput-tfixedflowinput-executing-job-standard-component-save -->

# Executing the Job

## Procedure

Save your Job and press F6 to execute it.

![](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFilterRow5.png)

As shown above, the first table lists the records of male persons aged between 10 and 80 years, whose last names are made up of less than nine characters, and the second table lists all the records that do not match the filter conditions. Each rejected record has a corresponding error message that explains the reason of rejection.
