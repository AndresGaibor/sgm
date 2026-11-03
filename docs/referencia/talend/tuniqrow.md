# tuniqrow (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tuniqrow  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tuniqrow -->

# tUniqRow

Ensures data quality of input or output flow in a Job.

tUniqRow compares entries and sorts out duplicate entries from the input flow.

This component is not shipped with your Talend Studio by default. You need to install it using the Feature Manager. For more information, see [Installing features using the Feature Manager](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/install-features-to-talend-studio).

### In this section

* [tUniqRow Standard properties](https://help.qlik.com/talend/en-US/components/8.0/deduplication/tuniqrow-standard-properties?id=1038)
* [tUniqRow properties for Apache Spark Batch](https://help.qlik.com/talend/en-US/components/8.0/deduplication/tuniqrow-properties-for-apache-spark-batch?id=1039)
* [tUniqRow properties for Apache Spark Streaming](https://help.qlik.com/talend/en-US/components/8.0/deduplication/tuniqrow-properties-for-apache-spark-streaming?id=1040)

**Related concepts**

* [Deduplicating entries based on dynamic schema](https://help.qlik.com/talend/en-US/components/8.0/deduplicating-entries-dynamic-schemas)
* [Deduplicating entries](https://help.qlik.com/talend/en-US/components/8.0/deduplicating-entries)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/deduplication/tuniqrow-standard-properties?id=1038 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Data Quality components](/talend/en-US/components/8.0/data-quality-components-container)
3. [Deduplication](/talend/en-US/components/8.0/deduplication)
4. [Deduplication components](/talend/en-US/components/8.0/deduplication/deduplication-component)
5. [tUniqRow](/talend/en-US/components/8.0/deduplication/tuniqrow?id=1037)

# tUniqRow Standard properties

Last updated: 11/3/2026

These properties are used to configure tUniqRow running in the Standard Job framework.

The Standard
tUniqRow component belongs to the Data Quality family.

The component in this framework is available in all Talend
products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit schema | * A schema is a row description. It defines the number of fields   (columns) to be processed and passed on to the next component. When you create a Spark   Job, avoid the reserved word `line` when naming the   fields.  Click Edit   schema to make changes to the schema. If the current schema is of the Repository type, three options are available:    + View schema: choose this     option to view the schema only.   + Change to built-in property:     choose this option to change the schema to Built-in for local changes.   + Update repository connection:     choose this option to change the schema stored in the repository and decide whether     to propagate the changes to all the Jobs upon completion.  If you just want to     propagate the changes to the current Job, you can select No upon completion and choose this schema metadata     again in the Repository Content     window. This component offers the advantage of the   dynamic schema feature. This allows you to retrieve unknown columns from source   files or to copy batches of columns from a source without mapping each column   individually. For further information about dynamic schemas, see [Dynamic schema](/talend/r/en-US/8.0/studio-user-guide/dynamic-schema).  This   dynamic schema feature is designed for the purpose of retrieving unknown columns of a   table and is recommended to be used for this purpose only; it is not recommended for the   use of creating tables. * Built-In: You create and store the schema locally for this component   only. * Repository: You have already created the schema and stored it in the   Repository. You can reuse it in various projects and Job designs. |
| Unique key | In this area, select one or more columns to carry out deduplication on the particular column(s)  - Select the Key attribute check box to carry out deduplication on all the columns  - Select the Case sensitive check box to differentiate upper case and lower case |

## Advanced settings

| Properties | Description |
| --- | --- |
| Only once each duplicated key | Select this check box if you want to have only the first duplicated entry in the column(s) defined as key(s) sent to the output flow for duplicates. |
| Use of disk (suitable for processing large row set) | Select this check box to enable generating temporary files on the hard disk when processing a large amount of data. This helps to prevent Job execution failure caused by memory overflow. With this check box selected, you need also to define:  - Buffer size in memory: Select the number of rows that can be buffered in the memory before a temporary file is to be generated on the hard disk.  - Directory for temp files: Set the location where the temporary files should be stored.  Information noteWarning: *Make sure that you specify an existing directory for temporary files; otherwise your Job execution will fail.* |
| Ignore trailing zeros for BigDecimal | Select this check box to ignore trailing zeros for BigDecimal data. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_UNIQUES: the number of unique rows. This is an After variable and it returns an integer.  NB\_DUPLICATES: the number of duplicate rows. This is an After variable and it returns an integer.  ERROR\_MESSAGE: the error message generated by the component when an error occurs. This is an After variable and it returns a string. This variable functions only if the Die on error checkbox is cleared, if the component has this checkbox.  A Flow variable functions during the execution of a component while an After variable functions after the execution of the component.  To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from it.  For more information about variables, see [Using contexts and variables](/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component handles flow of data therefore it requires input and output, hence is defined as an intermediary step. |

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/deduplication/tuniqrow-properties-for-apache-spark-batch?id=1039 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Data Quality components](/talend/en-US/components/8.0/data-quality-components-container)
3. [Deduplication](/talend/en-US/components/8.0/deduplication)
4. [Deduplication components](/talend/en-US/components/8.0/deduplication/deduplication-component)
5. [tUniqRow](/talend/en-US/components/8.0/deduplication/tuniqrow?id=1037)

# tUniqRow properties for Apache Spark Batch

Last updated: 11/3/2026

These properties are used to configure tUniqRow running in the Spark Batch Job framework.

The Spark Batch
tUniqRow component belongs to the Processing family.

The component in this framework is available in all
subscription-based Talend products
with Big Data and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit schema | * A schema is a row description. It defines the number of fields   (columns) to be processed and passed on to the next component. When you create a Spark   Job, avoid the reserved word `line` when naming the   fields.  Click Edit   schema to make changes to the schema. If the current schema is of the Repository type, three options are available:    + View schema: choose this     option to view the schema only.   + Change to built-in property:     choose this option to change the schema to Built-in for local changes.   + Update repository connection:     choose this option to change the schema stored in the repository and decide whether     to propagate the changes to all the Jobs upon completion.  If you just want to     propagate the changes to the current Job, you can select No upon completion and choose this schema metadata     again in the Repository Content     window. * Built-In: You create and store the schema locally for this component   only. * Repository: You have already created the schema and stored it in the   Repository. You can reuse it in various projects and Job designs. |
| Unique key | In this area, select one or more columns to carry out deduplication on the particular column(s)  - Select the Key attribute check box to carry out deduplication on all the columns  - Select the Case sensitive check box to differentiate upper case and lower case |

## Advanced settings

| Properties | Description |
| --- | --- |
| Only once each duplicated key | Select this check box if you want to have only the first duplicated entry in the column(s) defined as key(s) sent to the output flow for duplicates. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate step.  This component, along with the Spark Batch component Palette it belongs to, appears only when you are creating a Spark Batch Job.  Note that in this documentation, unless otherwise explicitly stated, a scenario presents only Standard Jobs, that is to say traditional  Talend  data integration Jobs. |
| Spark Connection | In the Spark Configuration tab in the Run view, define the connection to a given Spark cluster for the whole Job. In addition, since the Job expects its dependent jar files for execution, you must specify the directory in the file system to which these jar files are transferred so that Spark can access these files:  * Yarn mode (Yarn client or Yarn cluster):   + When using Google Dataproc, specify a bucket in the     Google Storage staging bucket     field in the Spark configuration     tab.   + When using HDInsight, specify the blob to be used for Job     deployment in the Windows Azure Storage     configuration area in the Spark     configuration tab.   + When using Altus, specify the S3 bucket or the Azure     Data Lake Storage for Job deployment in the Spark     configuration tab.   + When using on-premises distributions, use     the configuration component corresponding to the file system     your cluster is using. Typically, this system is HDFS and so     use [tHDFSConfiguration](/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration). * Standalone mode: use the   configuration component corresponding to the file system your cluster is   using, such as [tHDFSConfiguration Apache Spark Batch](/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch) or [tS3Configuration Apache Spark Batch](/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch).  If you are using Databricks without any configuration component present   in your Job, your business data is written directly in DBFS (Databricks   Filesystem).  This connection is effective on a per-Job basis. |

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/deduplication/tuniqrow-properties-for-apache-spark-streaming?id=1040 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Data Quality components](/talend/en-US/components/8.0/data-quality-components-container)
3. [Deduplication](/talend/en-US/components/8.0/deduplication)
4. [Deduplication components](/talend/en-US/components/8.0/deduplication/deduplication-component)
5. [tUniqRow](/talend/en-US/components/8.0/deduplication/tuniqrow?id=1037)

# tUniqRow properties for Apache Spark Streaming (deprecated)

Last updated: 11/3/2026

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

These properties are used to configure tUniqRow running in the Spark Streaming Job framework.

Information noteDeprecation: Spark Streaming is deprecated beginning with the R2026-09 release.
Use Spark Structured Streaming instead.

The Spark Streaming
tUniqRow component belongs to the Processing family.

This component is available in Talend Real-Time Big Data Platform and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema et Edit schema | * A schema is a row description. It defines the number of fields   (columns) to be processed and passed on to the next component. When you create a Spark   Job, avoid the reserved word `line` when naming the   fields.  Click Edit   schema to make changes to the schema. If the current schema is of the Repository type, three options are available:    + View schema: choose this     option to view the schema only.   + Change to built-in property:     choose this option to change the schema to Built-in for local changes.   + Update repository connection:     choose this option to change the schema stored in the repository and decide whether     to propagate the changes to all the Jobs upon completion.  If you just want to     propagate the changes to the current Job, you can select No upon completion and choose this schema metadata     again in the Repository Content     window. * Built-In: You create and store the schema locally for this component   only. * Repository: You have already created the schema and stored it in the   Repository. You can reuse it in various projects and Job designs. |
| Unique key | In this area, select one or more columns to carry out deduplication on the particular column(s)  - Select the Key attribute check box to carry out deduplication on all the columns  - Select the Case sensitive check box to differentiate upper case and lower case |

## Advanced settings

| Properties | Description |
| --- | --- |
| Only once each duplicated key | Select this check box if you want to have only the first duplicated entry in the column(s) defined as key(s) sent to the output flow for duplicates. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate step.  This component, along with the Spark Streaming component Palette it belongs to, appears only when you are creating a Spark Streaming Job.  Note that in this documentation, unless otherwise explicitly stated, a scenario presents only Standard Jobs, that is to say traditional  Talend  data integration Jobs. |
| Spark Connection | In the Spark Configuration tab in the Run view, define the connection to a given Spark cluster for the whole Job. In addition, since the Job expects its dependent jar files for execution, you must specify the directory in the file system to which these jar files are transferred so that Spark can access these files:  * Yarn mode (Yarn client or Yarn cluster):   + When using Google Dataproc, specify a bucket in the     Google Storage staging bucket     field in the Spark configuration     tab.   + When using HDInsight, specify the blob to be used for Job     deployment in the Windows Azure Storage     configuration area in the Spark     configuration tab.   + When using Altus, specify the S3 bucket or the Azure     Data Lake Storage for Job deployment in the Spark     configuration tab.   + When using on-premises distributions, use     the configuration component corresponding to the file system     your cluster is using. Typically, this system is HDFS and so     use [tHDFSConfiguration](/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration). * Standalone mode: use the   configuration component corresponding to the file system your cluster is   using, such as [tHDFSConfiguration Apache Spark Batch](/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch) or [tS3Configuration Apache Spark Batch](/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch).  If you are using Databricks without any configuration component present   in your Job, your business data is written directly in DBFS (Databricks   Filesystem).  This connection is effective on a per-Job basis. |

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)
