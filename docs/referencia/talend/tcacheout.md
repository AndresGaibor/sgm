# tcacheout (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tcacheout  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tcacheout -->

# tCacheOut

Persists the input RDDs depending on the specific storage level you define in order to offer faster access to these datasets later.

tCacheOut writes RDDs (Resilient Distributed Datasets) to the cache for later use in the same Job.

### In this section

* [tCacheOut properties for Apache Spark Batch](https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-properties-for-apache-spark-batch)
* [tCacheOut properties for Apache Spark Streaming (deprecated)](https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-properties-for-apache-spark-streaming)

**Related concepts**

* [Performing download analysis using a Spark Batch Job](https://help.qlik.com/talend/en-US/components/8.0/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-properties-for-apache-spark-batch -->

# tCacheOut properties for Apache Spark Batch

These properties are used to configure tCacheOut running in the Spark Batch Job framework.

The Spark Batch tCacheOut component belongs to the Processing family.

The component in this framework is available in all subscription-based Talend products with Big Data and Talend Data Fabric.

[Preview](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/feature-preview-program-overview.htm)

Information noteNote: This component is not supported with the Databricks Serverless runtime.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Storage level | From the Storage level drop-down list that is displayed, select how the cached RDDs are<br>stored, such as in memory only or in memory and on disk.<br><br>For further information about each of the storage level, see https://spark.apache.org/docs/latest/programming-guide.html#rdd-persistence. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an end component and requires an input link.<br><br>This component makes datasets persist and is closely related to tCacheIn. Iteratively, tCacheOut stores input<br>data as cache so that tCacheIn can reads the cache without having to calculate again all of the<br>Spark DAG (Directed Acyclic Graph, the model used by Spark for scheduling Spark<br>actions).<br><br>This component, along with the Spark Batch component Palette it belongs to,<br>appears only when you are creating a Spark Batch Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a<br>scenario presents only Standard Jobs, that is to<br>say traditional<br>Talend<br>data integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-properties-for-apache-spark-streaming -->

# tCacheOut properties for Apache Spark Streaming (deprecated)

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

These properties are used to configure tCacheOut running in the Spark Streaming Job framework.

Information noteDeprecation: Spark Streaming is deprecated beginning with the R2026-09 release. Use Spark Structured Streaming instead.

The Spark Streaming tCacheOut component belongs to the Processing family.

This component is available in Talend Real-Time Big Data Platform and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit<br>schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Storage level | From the Storage level drop-down list that is displayed, select how the cached RDDs are<br>stored, such as in memory only or in memory and on disk.<br><br>For further information about each of the storage level, see https://spark.apache.org/docs/latest/programming-guide.html#rdd-persistence. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an end component and requires an input link.<br><br>This component makes datasets persist and is closely related to tCacheIn. Iteratively, tCacheOut stores input<br>data as cache so that tCacheIn can reads the cache without having to calculate again all of the<br>Spark DAG (Directed Acyclic Graph, the model used by Spark for scheduling Spark<br>actions).<br><br>At any given moment, tCacheOut stores only one micro-batch in memory.<br><br>This component, along with the Spark Batch component Palette it belongs to,<br>appears only when you are creating a Spark Batch Job.<br><br>Note that in this documentation, unless otherwise explicitly stated, a<br>scenario presents only Standard Jobs, that is to<br>say traditional<br>Talend<br>data integration Jobs. |
| Spark Connection | In the Spark<br>Configuration tab in the Run<br>view, define the connection to a given Spark cluster for the whole Job. In<br>addition, since the Job expects its dependent jar files for execution, you must<br>specify the directory in the file system to which these jar files are<br>transferred so that Spark can access these files:<br><br><ul> <li> <div> <span>Yarn mode</span> (Yarn client or Yarn cluster):<ul> <li> <p>When using Google Dataproc, specify a bucket in the                                            <span>Google Storage staging bucket</span>                                        field in the <span>Spark configuration</span>                                        tab.</p> </li> <li> <p>When using HDInsight, specify the blob to be used for Job                                        deployment in the <span>Windows Azure Storage                                            configuration</span> area in the <span>Spark                                            configuration</span> tab.</p> </li> <li>When using Altus, specify the S3 bucket or the Azure                                    Data Lake Storage for Job deployment in the <span>Spark                                        configuration</span> tab.</li> <li> <p>When using on-premises distributions, use                                        the configuration component corresponding to the file system                                        your cluster is using. Typically, this system is HDFS and so                                        use <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration">tHDFSConfiguration</a>.</p> </li> </ul> </div> </li> <li> <p> <span>Standalone mode</span>: use the                            configuration component corresponding to the file system your cluster is                            using, such as <a href="https://help.qlik.com/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch">tHDFSConfiguration Apache Spark Batch</a> or <a href="https://help.qlik.com/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch">tS3Configuration Apache Spark Batch</a>.</p> <p>If you are using Databricks without any configuration component present                            in your Job, your business data is written directly in DBFS (Databricks                            Filesystem).</p> </li> </ul><br><br>This connection is effective on a per-Job basis. |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this -->

# Performing download analysis using a Spark Batch Job

This scenario applies only to subscription-based Talend products with Big Data.

In this scenario, you create a Spark Batch Job to analyze how often a given product is downloaded.

![](https://help.qlik.com/talend/en-US/components/Resources/images/use_case-ttop1.png)

In this Job, you analyze the download preference of some specific customers known to your customer base.

The sample data used as the customer base is as follows:

```
10103|Herbert|Clinton|FR|SILVER|28-06-2011|herbert.clinton@msn.com|6571183
10281|Bill|Ford|BE|PLATINUM|13-04-2014|bill.ford@gmail.com|6360604
10390|George|Garfield|GB|SILVER|12-02-2011|george.garfield@gmail.com|7919508
10566|Abraham|Garfield|CN|SILVER|11-10-2012|abraham.garfield@msn.com|9155569
10691|John|Polk|GB|SILVER|05-11-2012|john.polk@gmail.com|6488579
10884|Herbert|Hayes|GB|SILVER|12-10-2007|herbert.hayes@gmail.com|8728181
11020|Chester|Roosevelt|BE|GOLD|28-06-2008|chester.roosevelt@yahoo.com|4172181
11316|Franklin|Madison|BR|SILVER|08-01-2014|franklin.madison@gmail.com|4711801
11707|James|Tyler|ES|GOLD|25-03-2010|james.tyler@gmail.com|7276942
11764|Theodore|McKinley|GB|GOLD|24-08-2013|theodore.mckinley@gmail.com|3224767
11777|Warren|Madison|BE|N/A|23-12-2008|warren.madison@msn.com|6695520
11857|Ronald|Arthur|SG|PLATINUM|01-04-2009|ronald.arthur@msn.fr|6704785
11936|Theodore|Buchanan|NL|SILVER|14-11-2014|theodore.buchanan@yahoo.fr|2783553
11940|Lyndon|Wilson|BR|PLATINUM|27-07-2010|lyndon.wilson@yahoo.com|1247110
12214|Gerald|Jefferson|SG|N/A|06-06-2007|gerald.jefferson@yahoo.com|5879162
12382|Herbert|Taylor|IT|GOLD|22-04-2012|herbert.taylor@msn.com|3873628
12475|Richard|Kennedy|FR|N/A|29-12-2014|richard.kennedy@yahoo.fr|7287388
12479|Calvin|Eisenhower|ES|N/A|06-11-2008|calvin.eisenhower@yahoo.fr|1792573
12531|Chester|Arthur|JP|PLATINUM|23-01-2009|chester.arthur@msn.fr|8772326
12734|Jimmy|Buchanan|IT|SILVER|09-03-2010|jimmy.buchanan@gmail.com|7007786
```

This data contains these customers' ID numbers known to this customer base, their first and last names and country codes, their support levels and registration dates, their email addresses and phone numbers.

The sample web-click log of some of these customers reads as follows:

```
10103|/download/products/talend-open-studio
10281|/services/technical-support
10390|/services/technical-support
10566|/download/products/data-integration
10691|/services/training
10884|/download/products/integration-cloud
11020|/services/training
11316|/download/products/talend-open-studio
11707|/download/products/talend-open-studio
11764|/customers
```

This data contains the ID numbers of the customers who visited different *Talend* web pages and the pages they visited.

By reading this data, you can find that the visits come from customers of different support-levels for different purposes. The Job to be designed is used to identify the sources of these visits against the sample customer base and analyze which product is most downloaded by the Silver-level customers.

Note that the sample data is created for demonstration purposes only.

To replicate this scenario, proceed as follows:

### In this section

* [Linking the components](https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-linking-components-spark-batch-component-in?id=4184)
* [Selecting the Spark mode](https://help.qlik.com/talend/en-US/components/8.0/processing/selecting-spark-mode-spark-batch?id=4185)
* [Configuring the connection to the file system to be used by Spark](https://help.qlik.com/talend/en-US/components/8.0/processing/configuring-connection-to-file-system-to-be-used-by-spark?id=4186)
* [Loading the customer base](https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-loading-customer-base-spark-batch-component?id=4187)
* [Selecting the Silver-level customer data](https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-selecting-silver-level-customer-data-spark-batch-component?id=4188)
* [Accessing the selected data](https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-accessing-selected-data-spark-batch-component?id=4189)
* [Loading the web-click log](https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-loading-web-click-log-spark-batch-component?id=4190)
* [Joining the data](https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-joining-data-spark-batch-component?id=4191)
* [Extracting the fields about the categories of the visited pages](https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-extracting-fields-about-categories-of-visited-pages-spark-batch-component?id=4192)
* [Counting the download of each product](https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-counting-download-of-each-product-spark-batch-component?id=4193)
* [Selecting the most downloaded product](https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-selecting-most-downloaded-product-spark-batch-component?id=4194)
* [Executing the Job](https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-executing-job-spark-batch-component-then-you?id=4195)

**Related concepts**

* [tAggregateRow](https://help.qlik.com/talend/en-US/components/8.0/taggregaterow "Receives a flow and aggregates it based on one or more columns.")
* [tExtractDelimitedFields](https://help.qlik.com/talend/en-US/components/8.0/textractdelimitedfields "Generates multiple columns from a delimited string column.")
* [tCacheOut](https://help.qlik.com/talend/en-US/components/8.0/tcacheout "Persists the input RDDs depending on the specific storage level you define in order to offer faster access to these datasets later.")
* [tTop](https://help.qlik.com/talend/en-US/components/8.0/ttop "Sorts data and outputs several rows from the first one of this data.")
* [tSqlRow](https://help.qlik.com/talend/en-US/components/8.0/tsqlrow "Performs SQL queries over input datasets.")
* [tCacheIn](https://help.qlik.com/talend/en-US/components/8.0/tcachein "Offers faster access to the persistent data.")

**Related information**

* [tFixedFlowInput](https://help.qlik.com/talend/en-US/components/8.0/tfixedflowinput/tfixedflowinput)
* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)
* [tMap](https://help.qlik.com/talend/en-US/components/8.0/tmap/tmap)
* [tMysqlInput](https://help.qlik.com/talend/en-US/components/8.0/mysql/tmysqlinput)
* [tHDFSConfiguration](https://help.qlik.com/talend/en-US/components/8.0/hdfs/thdfsconfiguration)
* [tS3Configuration](https://help.qlik.com/talend/en-US/components/8.0/amazon-s3/ts3configuration)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-linking-components-spark-batch-component-in?id=4184 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Processing (Integration)](/talend/en-US/components/8.0/processing)
3. [Processing (Integration) scenarios](/talend/en-US/components/8.0/processing/processing-scenario)
4. [Performing download analysis using a Spark Batch Job](/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this?id=4183)

# Linking the components

Last updated: 11/3/2026

## Procedure

1. In the Integration perspective of Talend Studio,
   create an empty Spark Batch Job from the Job
   Designs node in the Repository
   tree view.

   For further information about how to create a Spark Batch Job, see
   [Creating Spark Batch Jobs](/talend/r/en-US/8.0/studio-getting-started-guide-data-fabric/creating-spark-batch-job).
2. In the workspace, enter the name of the component to be used and select this
   component from the list that appears. In this scenario, the components are
   tHDFSConfiguration, two tFixedFlowInput components (label one to *customer\_base* and the other to *web\_data*), tSqlRow, tCacheOut, tCacheIn,
   tMap, tExtractDelimitedFields, tAggregateRow, tTop and tLogRow.

   The tFixedFlowInput components are used to load
   the sample data into the data flow. In the real-world practice, you can use
   other components such as tMysqlInput, alone or
   even with a tMap, in the place of tFixedFlowInput to design a sophisticated process to
   prepare your data to be processed.
3. Connect *customer\_base* (tFixedFlowInput), tSqlRow and
   tCacheOut using the Row >
   Main link. In this subJob, the records about the Silver-level
   customers are selected and stored in cache.
4. Connect *web\_data* (tFixedFlowInput) to tMap using
   the Row > Main link. This is the main input
   flow to the tMap component.
5. Do the same to connect tCacheIn to tMap. This is the lookup flow to tMap.
6. Connect tMap to tExtractDelimitedFields using the Row >
   Main link and name this connection in the dialog box that is
   displayed. For example, name it to *output*.
7. Connect tExtractDelimitedFields, tAggregateRow, tTop and
   tLogRow using the Row >
   Main link.
8. Connect *customer\_base* to *web\_data* using the Trigger >
   OnSubjobOk link.
9. Leave the tHDFSConfiguration component alone
   without any connection.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-loading-customer-base-spark-batch-component?id=4187 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Processing (Integration)](/talend/en-US/components/8.0/processing)
3. [Processing (Integration) scenarios](/talend/en-US/components/8.0/processing/processing-scenario)
4. [Performing download analysis using a Spark Batch Job](/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this?id=4183)

# Loading the customer base

Last updated: 11/3/2026

## Procedure

1. Double-click the tFixedFlowIput component labeled
   *customer\_base* to open its Component view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop3.png)
2. Click the [...] button next to Edit
   schema to open the schema editor.
3. Click the [+] button to add the schema columns as shown in
   this image.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop4.png)
4. Click OK to validate these changes and accept the
   propagation prompted by the pop-up dialog box.
5. In the Mode area, select the Use Inline
   Content radio button and paste the above-mentioned sample
   customer base data into the Content field that
   is displayed.
6. In the Field separator field, enter a vertical bar (*|*).

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-selecting-silver-level-customer-data-spark-batch-component?id=4188 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Processing (Integration)](/talend/en-US/components/8.0/processing)
3. [Processing (Integration) scenarios](/talend/en-US/components/8.0/processing/processing-scenario)
4. [Performing download analysis using a Spark Batch Job](/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this?id=4183)

# Selecting the Silver-level customer data

Last updated: 11/3/2026

## Procedure

1. Double-click tSqlRow to open its Component view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop5.png)
2. Click the [...] button next to Edit schema to open the schema editor.
3. In the schema on the output side (the right side), change the column name
   *Support* to *Silver\_Support*.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop6.png)
4. From the SQL context drop-down list, select
   SQL Spark Context.
5. In the SQL Query field, enter the query
   statement to be used to select the records about the Silver-level
   customers.

   ```
   select User_id, FirstName, LastName, Country, Support as Silver_Support, SubscriptionDate, email, telephone from row1 where Support = 'SILVER'
   ```

   You can read that the input link *row1* is
   actually taken as the table in which this query is performed.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-accessing-selected-data-spark-batch-component?id=4189 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Processing (Integration)](/talend/en-US/components/8.0/processing)
3. [Processing (Integration) scenarios](/talend/en-US/components/8.0/processing/processing-scenario)
4. [Performing download analysis using a Spark Batch Job](/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this?id=4183)

# Accessing the selected data

Last updated: 11/3/2026

## Procedure

1. Double-click tCacheOut to open its
   Component view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop7.png)

   This component stores the selected data into the cache.
2. Click the [...] button next to Edit
   schema to open the schema editor to verify the schema is identical to
   the input one. If not so, click Sync
   columns.
3. On the output side of the schema editor, click the
   ![](/talend/en-US/components/8.0/Content/Resources/images/export.png)
   button to export the schema to the local file system and
   click OK to close the editor.
4. From the Storage level list, select Memory only.

   For further information about each of the storage level, see <https://spark.apache.org/docs/latest/programming-guide.html#rdd-persistence>.
5. Double-click tCacheIn to open its
   Component view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop10.png)
6. Click the [...] button next to Edit
   schema to open the schema editor and click the
   ![](/talend/en-US/components/8.0/Content/Resources/images/import.png)
   button to import the schema you exported in the previous
   step. Then click OK to close the editor.
7. From the Output cache list, select the
   tCacheOut component from which you need to read
   the cached data. At runtime, this data is loaded into the lookup flow of the
   subJob that is used to process the web-click log.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-loading-web-click-log-spark-batch-component?id=4190 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Processing (Integration)](/talend/en-US/components/8.0/processing)
3. [Processing (Integration) scenarios](/talend/en-US/components/8.0/processing/processing-scenario)
4. [Performing download analysis using a Spark Batch Job](/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this?id=4183)

# Loading the web-click log

Last updated: 11/3/2026

## Procedure

1. Double-click the tFixedFlowIput component labeled
   *web\_data* to open its Component view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop8.png)
2. Click the [...] button next to Edit
   schema to open the schema editor.
3. Click the [+] button to add the schema columns as shown in
   this image.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop9.png)
4. Click OK to validate these changes and accept the
   propagation prompted by the pop-up dialog box.
5. In the Mode area, select the Use Inline
   Content radio button and paste the above-mentioned sample data
   about the web-click log into the Content field
   that is displayed.
6. In the Field separator field, enter a vertical bar (*|*).

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-joining-data-spark-batch-component?id=4191 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Processing (Integration)](/talend/en-US/components/8.0/processing)
3. [Processing (Integration) scenarios](/talend/en-US/components/8.0/processing/processing-scenario)
4. [Performing download analysis using a Spark Batch Job](/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this?id=4183)

# Joining the data

Last updated: 11/3/2026

## Procedure

1. Double-click tMap to open its
   Map editor.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop11.png)

   On the input side (the left side), the main flow (labeled *row3* in this example) and the lookup flow (labeled
   *row4* in this example) are presented as two
   tables.

   On the output side (the right side), an empty table is present.
2. Drop all of the columns of the schema of the lookup flow into the output flow
   table on the right side, except the *User\_id*
   column, and drop the *user\_id* column and the
   *url* column from schema of the main flow into
   the same output flow table.
3. On the left side, drop the *user\_id* column
   from the main flow table into the Expr.key
   column in the *User\_id* row in the lookup flow
   table. This makes the ID numbers of the customers the key for the join of the
   two input flows.
4. In the lookup flow table, click the wrench icon to display the panel for the
   lookup settings and select Inner Join for the
   Join model property.
5. Click Apply to validate these changes and
   click OK to close this editor.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-extracting-fields-about-categories-of-visited-pages-spark-batch-component?id=4192 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Processing (Integration)](/talend/en-US/components/8.0/processing)
3. [Processing (Integration) scenarios](/talend/en-US/components/8.0/processing/processing-scenario)
4. [Performing download analysis using a Spark Batch Job](/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this?id=4183)

# Extracting the fields about the categories of the visited pages

Last updated: 11/3/2026

## Procedure

1. Double-click tExtractDelimitedFields to open its Component view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop12.png)
2. Click the [...] button next to Edit
   schema to open the schema editor.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop13.png)
3. On the output side, click the [+] button four
   times to add four rows to the output schema table and rename these new schema
   columns to *root*, *page*, *specialization* and
   *product*, respectively. These columns are used
   to carry the fields extracted from the *url*
   column in the input flow.
4. Click OK to validate these changes.
5. From the Prev.Comp.Column.List list, select
   the column you need to extract data from. In this example, it is *url* from the input schema.
6. In the Field separator field, enter a slash
   (*/*).

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-counting-download-of-each-product-spark-batch-component?id=4193 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Processing (Integration)](/talend/en-US/components/8.0/processing)
3. [Processing (Integration) scenarios](/talend/en-US/components/8.0/processing/processing-scenario)
4. [Performing download analysis using a Spark Batch Job](/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this?id=4183)

# Counting the download of each product

Last updated: 11/3/2026

## Procedure

1. Double-click tAggregateRow to open its
   Component view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop14.png)
2. Click the [...] button next to Edit
   schema to open the schema editor.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop15.png)
3. On the output side, click the [+] button two times to
   add two rows to the output schema table and rename these new schema columns to
   *product* and *nb\_download*, respectively.
4. Click OK to validate these changes and accept
   the propagation prompted by the pop-up dialog box.
5. In the Group by table, add one row by
   clicking the [+] button and select *product* for both the Output
   column column and the Input column
   position column. This passes data from the *product* column of the input schema to the *product* column of the output schema.
6. In the Operations table, add one row by
   clicking the [+] button.
7. In the Output column column, select *nb\_download*, in the Function column, select *count* and
   in the Input column position column, select
   *product*.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-selecting-most-downloaded-product-spark-batch-component?id=4194 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Processing (Integration)](/talend/en-US/components/8.0/processing)
3. [Processing (Integration) scenarios](/talend/en-US/components/8.0/processing/processing-scenario)
4. [Performing download analysis using a Spark Batch Job](/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this?id=4183)

# Selecting the most downloaded product

Last updated: 11/3/2026

## Procedure

1. Double-click tTop to open its
   Component view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop16.png)
2. In the Number of line selected field, enter
   the number of rows to be output to the next component, counting down from the
   first row of the data sorted by tTop.
3. In the Criteria table, added one row by
   clicking the [+] button.
4. In the Schema column column, select *nb\_download*, the column for which the data is sorted,
   in the sort num or alpha column, select
   *num*, which means the data to be sorted are
   numbers, and in the Order asc or desc column,
   select *desc* to arrange the data in descending
   order.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-executing-job-spark-batch-component-then-you?id=4195 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Processing (Integration)](/talend/en-US/components/8.0/processing)
3. [Processing (Integration) scenarios](/talend/en-US/components/8.0/processing/processing-scenario)
4. [Performing download analysis using a Spark Batch Job](/talend/en-US/components/8.0/processing/tcacheout-textractdelimitedfields-ts3configuration-performing-download-analysis-using-spark-batch-job-spark-batch-component-in-this?id=4183)

# Executing the Job

Last updated: 11/3/2026

## About this task

Then you can run this Job.

The tLogRow component is used to present the execution
result of the
Job.

## Procedure

1. Double-click the tLogRow component to open the Component view.
2. Select the Define a storage configuration component check box
   and select tHDFSConfiguration.
3. Press F6 to run this Job.

## Results

Once done, in the console of the Run view, you can check the execution result.

![](/talend/en-US/components/8.0/Content/Resources/images/use_case-ttop17.png)

It counts two of the total five downloads.

Note that you can manage the level of the execution information to be outputted in this
console by selecting the log4jLevel check box in the
Advanced settings tab and then selecting the level of
the information you want to display.

For more information on the log4j logging levels, see the Apache documentation at <http://logging.apache.org/log4j/1.2/apidocs/org/apache/log4j/Level.html>.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)
