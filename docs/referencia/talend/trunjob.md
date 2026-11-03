# trunjob (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/trunjob  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/trunjob -->

# tRunJob

Manages complex Job systems which need to execute one Job after another.

tRunJob executes the Job called in the component's properties, in the frame of the context defined.

Information noteWarning: Using recursive Jobs in tRunJob components is not supported any more for new projects from Talend 8.0 onwards, as they are likely to cause performance issues when building Jobs. For more information, see [Configuring build settings](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2024-12/configure-build-settings).

For the latest version, see [Setting up the Java version to build artifacts in Talend Studio](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/setting-compiler-compliance-level).

### In this section

* [tRunJob Standard properties](https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-standard-properties?id=3833)
* [tRunJob properties for Apache Spark Batch (deprecated)](https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-properties-for-apache-spark-batch?id=3834)

**Related concepts**

* [Calling a Job and passing the parameter needed to the called Job](https://help.qlik.com/talend/en-US/components/8.0/trunjob-tfilelist-tfileinputdelimited-tlogrow-calling-job-and-passing-parameter-needed-to-called-job-standard-component-this)
* [Modifying a variable during a Job execution](https://help.qlik.com/talend/en-US/components/8.0/tsetenv-trunjob-tmsgbox-trunjob-tmsgbox-modifying-variable-during-job-execution-standard-component-the)
* [Passing a value from a parent Job to a child Job](https://help.qlik.com/talend/en-US/components/8.0/component-trunjob-pass-value-from-parent-to-child "Passing a value from a parent Job to a child Job is a common real world requirement. In this example, you read data from a text file in a parent Job and pass fields from each row to a child Job. The data is used in the child Job.")
* [Propagating the buffered output data from the child Job to the parent Job](https://help.qlik.com/talend/en-US/components/8.0/trunjob-tfixedflowinput-tbufferoutput-tlogrow-propagating-buffered-output-data-from-child-job-to-parent-job-standard-component-in-this)
* [Running a list of child Jobs dynamically](https://help.qlik.com/talend/en-US/components/8.0/tflowtoiterate-trunjob-tfixedflowinput-tlogrow-running-list-of-child-jobs-dynamically-standard-component-the "This scenario describes a Job that calls specific child Jobs dynamically in a given order based on a child Job list.")


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-standard-properties?id=3833 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Orchestration (Integration)](/talend/en-US/components/8.0/orchestration)
3. [Orchestration (Integration) components](/talend/en-US/components/8.0/orchestration/orchestration-component)
4. [tRunJob](/talend/en-US/components/8.0/orchestration/trunjob?id=3832)

# tRunJob Standard properties

Last updated: 11/3/2026

These properties are used to configure tRunJob running in the
Standard Job framework.

The Standard
tRunJob component belongs to the System
and the Orchestration families.

The component in this framework is available in all Talend
products.

Information noteWarning:

The tRunJob component is supported with limitations, which means
that only S4 (Minor) support cases are accepted and no patches are provided. If you
use tRunJob within Data Services and Routes (with
cTalendJob), support is provided on a "best effort" basis
only. In most cases, there are class loading issues which can sometimes be resolved
but not always.

This is because tRunJob is not designed to work in a Service/Route
style (ESB) deployment, so regular support is not provided if you decide to use it,
even though it may work in many cases. If you used tRunJob in the
past, it is recommended to change your Job Design to use Joblets instead.

For DI and non-ESB use cases, it is still a valuable component and has support.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit Schema | * A schema is a row description. It defines the number of fields   (columns) to be processed and passed on to the next component. When you create a Spark   Job, avoid the reserved word `line` when naming the   fields.  Click Edit   schema to make changes to the schema. If the current schema is of the Repository type, three options are available:    + View schema: choose this     option to view the schema only.   + Change to built-in property:     choose this option to change the schema to Built-in for local changes.   + Update repository connection:     choose this option to change the schema stored in the repository and decide whether     to propagate the changes to all the Jobs upon completion.  If you just want to     propagate the changes to the current Job, you can select No upon completion and choose this schema metadata     again in the Repository Content     window. This component offers the advantage of the   dynamic schema feature. This allows you to retrieve unknown columns from source   files or to copy batches of columns from a source without mapping each column   individually. For further information about dynamic schemas, see [Dynamic schema](/talend/r/en-US/8.0/studio-user-guide/dynamic-schema).  This   dynamic schema feature is designed for the purpose of retrieving unknown columns of a   table and is recommended to be used for this purpose only; it is not recommended for the   use of creating tables. * Built-In: You create and store the schema locally for this component   only. * Repository: You have already created the schema and stored it in the   Repository. You can reuse it in various projects and Job designs. |
| Copy Child Job Schema | Click to fetch the child Job schema. |
| Use dynamic job | Select this check box to allow multiple Jobs to be called and processed. When this option is enabled, only the latest version of the Jobs can be called and processed. An independent process will be used to run the subJob. The Context and the Use an independent process to run subJob options disappear. Information noteWarning:  * The Use dynamic job option is not compatible with   the Talend JobServer cache. Therefore, the execution may fail if you run a Job that   contains tRunjob with this check box selected in   Talend Administration Center. * This option is incompatible with the Use or register a shared   DB Connection option of database connection components.   When tRunJob works together with a database   connection component, enabling both options will cause your Job to   fail. * This option is not supported within ESB Routes or Data Services. * To avoid incompatibility with continuous integration, we recommend   clearing this check box when using tRunJob in Joblets. |
| Context job | This field is visible only when the Use dynamic job option is selected. Enter the name of the Job that you want to call from the list of Jobs selected. |
| Job | Select the Job to be called in and processed. Make sure you already executed once the Job called, beforehand, in order to ensure a smooth run through tRunJob. |
| Version | Select the child Job version that you want to use. |
| Context | If you defined contexts and variables for the Job to be called by this component, select the applicable context entry from the list. |
| Use an independent process to run subJob | Select this check box to use an independent process to run the subJob. This helps in solving issues related to memory limits. Information noteWarning:  * This option is not compatible with the Talend JobServer cache. Therefore, the execution may fail if you run a Job that   contains tRunJob with this check   box selected in Talend Administration Center. * This option is incompatible with the Use or   register a shared DB Connection option of database   connection components. When tRunJob works together with a database connection   component, enabling both options will cause your Job to fail. * This option is not supported within ESB Routes or Data Services. |
| Die on child error | Clear this check box to execute the parent Job even though there is an error when executing the child Job. |
| Transmit whole context | Select this check box to get all the context variables from the parent Job. Deselect it to get all the context variables from the child Job. If this check box is selected when the parent and child Jobs have the same context variables defined:  * variable values for the parent Job will be used during   the child Job execution if no relevant values are defined in the   Context Param table. * otherwise, values defined in the Context Param table will be used during   the child Job execution. |
| Context Param | You can change the value of selected context parameters. Click the [+] button to add the parameters defined in the Context view of the child Job. For more information on context parameters, see [Using contexts and variables](/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). The values defined here will be used during the child Job execution even if Transmit whole context is selected. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Propagate the child result to the output schema | Select this check box to propagate the output data stored in the buffer memory via the tBufferOutput component in the child Job to the output component in the parent Job. This property takes effect only when there is data coming from an input component such as tFixedFlowInput. This check box is cleared by default. It is invisible when the Use dynamic job or Use an independent process to run subJob check box is selected. |
| Print Parameters | Select this check box to display the internal and external parameters in the Console. |
| JVM Setting | Set JVM settings for the Job to be called or processed. * Use child Job JVM arguments: select this option to   use the Child Job JVM arguments. * Overwrite child Job JVM arguments: select this   option to use customized JVM arguments. To added a customized argument,   click the plus button under the JVM frame and edit   the new line added in the frame. |
| Use dynamic context for subJob | Select this option to specify a context variable group for the subJob to be called. After selecting this option, enter a variable name in the text field to the right of this option. Note that the value of the variable needs to be the name of an existing context variable group. Information noteNote: This option take precedence over the Context option in the Basic settings view. |
| Use extra classpath for subJob | Select this option to specify extra class paths for the subJob to be called. After selecting this option, provide one or multiple class paths in the text field to the right of this option. If you provide multiple paths, separate the paths using `;` (for Windows) or `:` (for Linux). Information noteNote: This option is available when Use dynamic job or Use an independent process to run subjob is selected in the Basic settings view. |
| Load context parameters from file | Select this check box to create a temporary file where the context parameters used in the Job are written. The child Job then reads the temporary file to retrieve context parameters, and the file is deleted at the end of the execution. Spark local execution is the only supported mode for Spark Batch and Spark Streaming Jobs as the temporary file is created on the local machine. The distributed Job cannot load the temporary file from the client node.  Information noteNote: This option is available when Use dynamic job or Use an independent process to run subjob is selected in the Basic settings view. |
| Use Base64 (for byte[]) | This option is selected by default and makes sure the Base64 encoding scheme is used to transfer byte arrays. |
| tStatCatcher Statistics | Select this check box to gather the processing metadata at the Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the component when an error occurs. This is an After variable and it returns a string. This variable functions only if the Die on error checkbox is cleared, if the component has this checkbox.  CHILD\_RETURN\_CODE: the return code of a child Job. This is an After variable and it returns an integer.  CHILD\_EXCEPTION\_STACKTRACE: the exception stack trace from a child Job. This is an After variable and it returns a string.  A Flow variable functions during the execution of a component while an After variable functions after the execution of the component.  To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from it.  For more information about variables, see [Using contexts and variables](/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component can be used as a standalone Job or can help clarifying complex Job by avoiding having too many subJobs all together in one Job. If you want to create a reusable group of components to be inserted in several Jobs or several times in the same Job, you can use a Joblet. Unlike the tRunJob, the Joblet uses the context variables of the Job in which it is inserted. For more information on Joblets, see [What is a Joblet](/talend/r/en-US/8.0/studio-user-guide/what-is-joblet).  This component also allows you to call a Job of a different framework, such as a Spark Batch Job or a Spark Streaming Job. |
| Connections | Outgoing links (from this component to another): Row: Main. Trigger: On Subjob Ok; On Subjob Error; Run if; On Component Ok; On Component Error Incoming links (from one component to this one):  Row: Main; Reject; Iterate. Trigger: On Subjob Ok; On Subjob Error; Run if; On Component Ok; On Component Error; Synchronize; Parallelize. For further information regarding connections, see [Using connections in a Job](/talend/r/en-US/8.0/studio-user-guide/using-connections-in-job). |

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-properties-for-apache-spark-batch?id=3834 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Orchestration (Integration)](/talend/en-US/components/8.0/orchestration)
3. [Orchestration (Integration) components](/talend/en-US/components/8.0/orchestration/orchestration-component)
4. [tRunJob](/talend/en-US/components/8.0/orchestration/trunjob?id=3832)

# tRunJob properties for Apache Spark Batch (deprecated)

Last updated: 11/3/2026

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

Information noteDeprecation: This component is deprecated since the
8.0.1-R2024-08 release and removed since the 8.0.1-R2025-02 release.

These properties are used to configure tRunJob running in the Spark Batch Job framework.

The Spark Batch
tRunJob component belongs to the System family.

The component in this framework is available in all
subscription-based Talend products
with Big Data and Talend Data Fabric.

## Basic settings

| Properties | Description |
| --- | --- |
| Use dynamic job | Select this check box to allow multiple Jobs to be called and processed. When this option is enabled, only the latest version of the Jobs can be called and processed. An independent process will be used to run the subJob. The Context and the Use an independent process to run subJob options disappear.  Information noteWarning: The Use dynamic job option is not compatible with the Talend JobServer cache. Therefore, the execution may fail if you run a Job that contains tRunjob with this check box selected in Talend Administration Center. |
| Context job | This field is visible only when the Use dynamic job option is selected. Enter the name of the Job that you want to call from the list of Jobs selected. |
| Job | Select the Job to be called in and processed. Make sure you already executed once the Job called, beforehand, in order to ensure a smooth run through tRunJob.  It is not recommended to call a Standard Job from a Spark Batch Job as it causes many issues. |
| Version | Select the child Job version that you want to use. |
| Context | If you defined contexts and variables for the Job to be run by the tRunJob, select the applicable context entry on the list. |
| Die on child error | Clear this check box to execute the parent Job even though there is an error when executing the child Job. |
| Transmit whole context | Select this check box to get all the context variables from the parent Job. Deselect it to get all the context variables from the child Job.  If this check box is selected when the parent and child Jobs have the same context variables defined:  * variable values for the parent Job will be used during   the child Job execution if no relevant values are   defined in the Context   Param table. * otherwise, values defined in the Context Param table will be used during   the child Job execution. |
| Context Param | You can change the value of selected context parameters. Click the [+] button to add the parameters defined in the Context view of the child Job. For more information on context parameters, see [Using contexts and variables](/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables).  The values defined here will be used during the child Job execution even if Transmit whole context is selected. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Print Parameters | Select this check box to display the internal and external parameters in the Console. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used with no need to be connected to other components.  This component, along with the Spark Batch component Palette it belongs to, appears only when you are creating a Spark Batch Job.  Note that in this documentation, unless otherwise explicitly stated, a scenario presents only Standard Jobs, that is to say traditional  Talend  data integration Jobs. |
| Spark Connection | In the Spark Configuration tab in the Run view, define the connection to a given Spark cluster for the whole Job. In addition, since the Job expects its dependent jar files for execution, you must specify the directory in the file system to which these jar files are transferred so that Spark can access these files:  * Yarn mode (Yarn client or Yarn cluster):   + When using Google Dataproc, specify a bucket in the     Google Storage staging bucket     field in the Spark configuration     tab.   + When using HDInsight, specify the blob to be used for Job     deployment in the Windows Azure Storage     configuration area in the Spark     configuration tab.   + When using Altus, specify the S3 bucket or the Azure     Data Lake Storage for Job deployment in the Spark     configuration tab.   + When using on-premises distributions, use     the configuration component corresponding to the file system     your cluster is using. Typically, this system is HDFS and so     use [tHDFSConfiguration](/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration). * Standalone mode: use the   configuration component corresponding to the file system your cluster is   using, such as [tHDFSConfiguration Apache Spark Batch](/talend/r/en-US/8.0/components/hdfs/thdfsconfiguration-properties-for-apache-spark-batch) or [tS3Configuration Apache Spark Batch](/talend/r/en-US/8.0/components/amazon-s3/ts3configuration-properties-for-apache-spark-batch).  If you are using Databricks without any configuration component present   in your Job, your business data is written directly in DBFS (Databricks   Filesystem).  This connection is effective on a per-Job basis. |

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/trunjob-tfilelist-tfileinputdelimited-tlogrow-calling-job-and-passing-parameter-needed-to-called-job-standard-component-this -->

# Calling a Job and passing the parameter needed to the called Job

This scenario describes a two-component Job named ParentJob that calls another Job named ChildJob to display the content of files specified in the ParentJob on the Run console.

![](https://help.qlik.com/talend/en-US/components/Resources/images/use_case_trunjob1.png)

### In this section

* [Setting up the child Job](https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-tfilelist-tfileinputdelimited-tlogrow-setting-up-child-job-standard-component-create?id=3845)
* [Setting up the parent Job](https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-tfilelist-tfileinputdelimited-tlogrow-setting-up-parent-job-standard-component-create?id=3846)
* [Executing the parent Job](https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-tfilelist-tfileinputdelimited-tlogrow-executing-parent-job-standard-component-press?id=3847)

**Related concepts**

* [tRunJob](https://help.qlik.com/talend/en-US/components/8.0/trunjob "Manages complex Job systems which need to execute one Job after another.")

**Related information**

* [tFileList](https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist)
* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited)
* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/trunjob-tfixedflowinput-tbufferoutput-tlogrow-propagating-buffered-output-data-from-child-job-to-parent-job-standard-component-in-this -->

# Propagating the buffered output data from the child Job to the parent Job

In this scenario, a three-component Job calls a two-component child Job and displays the buffered output data of the child Job, instead of the data from the input flow of the parent Job, on the console.

### In this section

* [Setting up the child Job](https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-tfixedflowinput-tbufferoutput-tlogrow-setting-up-child-job-standard-component-create?id=3866)
* [Setting up the parent Job](https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-tfixedflowinput-tbufferoutput-tlogrow-setting-up-parent-job-standard-component-create?id=3867)
* [Executing the parent Job](https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-tfixedflowinput-tbufferoutput-tlogrow-executing-parent-job-standard-component-press?id=3868)

**Related concepts**

* [tRunJob](https://help.qlik.com/talend/en-US/components/8.0/trunjob "Manages complex Job systems which need to execute one Job after another.")

**Related information**

* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)
* [tFixedFlowInput](https://help.qlik.com/talend/en-US/components/8.0/tfixedflowinput/tfixedflowinput)
* [tBufferOutput](https://help.qlik.com/talend/en-US/components/8.0/buffer/tbufferoutput)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-tfilelist-tfileinputdelimited-tlogrow-setting-up-child-job-standard-component-create?id=3845 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Orchestration (Integration)](/talend/en-US/components/8.0/orchestration)
3. [Orchestration (Integration) scenarios](/talend/en-US/components/8.0/orchestration/orchestration-scenario)
4. [Calling a Job and passing the parameter needed to the called Job](/talend/en-US/components/8.0/orchestration/trunjob-tfilelist-tfileinputdelimited-tlogrow-calling-job-and-passing-parameter-needed-to-called-job-standard-component-this?id=3844)

# Setting up the child Job

Last updated: 11/3/2026

## Procedure

1. Create a new Job `ChildJob` and add a
   tFileInputDelimited component and a
   tLogRow component to it.
2. Connect the tFileInputDelimited component to
   the tLogRow component using a Row > Main link.
3. Double-click the tFileInputDelimited component to open its Basic settings view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case_trunjob3.png)
4. Click in the File Name field
   and then press F5 to open the New Context Parameter dialog box and configure the
   context variable.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case_trunjob4.png)
5. In the Name field, enter a
   name for this new context variable, `FilePath` in this
   example.
6. In the Default value field,
   enter the full path to the default input file.
7. Click Finish to validate the
   context parameter setup and fill the File Name
   field with the context variable.

   You can also create or edit a context parameter in the Context view beneath the design workspace. For more
   information, see [Using contexts and variables](/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables).
8. Click the [...] button next
   to Edit schema to open the Schema dialog box where you can configure the schema
   manually.
9. In the dialog box, click the [+] button to add columns and name them according to the input file
   structure. 

   In this example, this component will actually read files defined in the parent
   Job, and these files contain up to five columns. Therefore, add five string type
   columns and name them `Column1`,
   `Column2`, `Column3`,
   `Column4`, and `Column5`
   respectively, and then click OK to validate
   the schema configuration and close the Schema
   dialog box.
10. Double-click the tLogRow
    component and on its Basic settings view,
    select the Table option to view displayed content in table
    cells.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-tfilelist-tfileinputdelimited-tlogrow-setting-up-parent-job-standard-component-create?id=3846 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Orchestration (Integration)](/talend/en-US/components/8.0/orchestration)
3. [Orchestration (Integration) scenarios](/talend/en-US/components/8.0/orchestration/orchestration-scenario)
4. [Calling a Job and passing the parameter needed to the called Job](/talend/en-US/components/8.0/orchestration/trunjob-tfilelist-tfileinputdelimited-tlogrow-calling-job-and-passing-parameter-needed-to-called-job-standard-component-this?id=3844)

# Setting up the parent Job

Last updated: 11/3/2026

## Procedure

1. Create a new Job `ParentJob` and add a
   tFileList component and a tRunJob component to it.
2. Connect the tFileList component to the
   tRunJob component using a Row > Iterate link.
3. Double-click the tFileList
   component to open its Basic settings
   view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case_trunjob5.png)
4. In the Directory field,
   specify the path to the directory that holds the files to be processed, or click the
   [...] button next to the field to browse to
   the directory.

   In this example, the directory is `D:/tRunJob_Input_Files`
   that holds three delimited files with up to five columns.
5. In the FileList Type list,
   select `Files`.
6. Select the Use Glob Expressions as
   Filemask check box, and then click the [+] button to add a line in the Files area and define a filter to match files. In this example, enter
   `"*.csv"` to retrieve all delimited files.
7. Double-click the tRunJob
   component to display its Basic settings
   view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case_trunjob7.png)
8. Click the [...] button next
   to the Job field and in the pop-up dialog box,
   select the child Job you want to execute and click OK to close
   the dialog box. The name of the selected Job appears in the
   Job field.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case_trunjob2-tosbd.png)
9. In the Context Param area,
   click the [+] button to add a line and define the context
   parameter. The only context parameter defined in the child Job, named
   `FilePath`, appears in the Parameters cell.
10. Click in the Values cell,
    press Ctrl+Space on your keyboard to access
    the list of context variables, and select
    `tFileList_1.CURRENT_FILEPATH`.

    The corresponding context variable
    `((String)globalMap.get("tFileList_1_CURRENT_FILEPATH"))`
    appears in the Values cell.

    For more information on context variables, see [Using contexts and variables](/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables).

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-tfilelist-tfileinputdelimited-tlogrow-executing-parent-job-standard-component-press?id=3847 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Orchestration (Integration)](/talend/en-US/components/8.0/orchestration)
3. [Orchestration (Integration) scenarios](/talend/en-US/components/8.0/orchestration/orchestration-scenario)
4. [Calling a Job and passing the parameter needed to the called Job](/talend/en-US/components/8.0/orchestration/trunjob-tfilelist-tfileinputdelimited-tlogrow-calling-job-and-passing-parameter-needed-to-called-job-standard-component-this?id=3844)

# Executing the parent Job

Last updated: 11/3/2026

## Procedure

1. Press Ctrl+S to save your
   Jobs.
2. Press F6 to execute the
   parent Job.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case_trunjob6.png)

   The parent Job calls the child Job, which reads the files defined in the parent
   Job, and the content of the files is displayed on the Run console.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-tfixedflowinput-tbufferoutput-tlogrow-setting-up-child-job-standard-component-create?id=3866 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Orchestration (Integration)](/talend/en-US/components/8.0/orchestration)
3. [Orchestration (Integration) scenarios](/talend/en-US/components/8.0/orchestration/orchestration-scenario)
4. [Propagating the buffered output data from the child Job to the parent Job](/talend/en-US/components/8.0/orchestration/trunjob-tfixedflowinput-tbufferoutput-tlogrow-propagating-buffered-output-data-from-child-job-to-parent-job-standard-component-in-this?id=3865)

# Setting up the child Job

Last updated: 11/3/2026

## About this task

![](/talend/en-US/components/8.0/Content/Resources/images/components-trunjob_scenario3_1.png)

## Procedure

1. Create a Job named *child*, and add two
   components by typing their names on the design workspace or dropping them
   from the Palette to the design
   workspace:
   * a tFixedFlowInput, to generate a
     message
   * a tBufferOutput, to store the
     generated message in the buffer memory
2. Connect the tFixedFlowInput component to
   the tBufferOutput component using a
   Row > Main connection.
3. Double-click the tFixedFlowInput
   component to open its Basic settings
   view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/components-trunjob_scenario3_2.png)
4. Click the [...] button next to Edit schema to open the Schema dialog box and define the schema of the input data.
   In this example, the schema has only one column *message* of the string type.

   ![](/talend/en-US/components/8.0/Content/Resources/images/components-trunjob_scenario3_3.png)

   When done, click OK to validate the
   changes and then click Yes in the pop-up
   Propagate dialog box to propagate the
   schema to the next component.
5. In the Mode area, select Use Single Table option, and define the
   corresponding value for the *message*
   column in the Values table. In this
   example, the value is *"message from the child
   job"*.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-tfixedflowinput-tbufferoutput-tlogrow-setting-up-parent-job-standard-component-create?id=3867 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Orchestration (Integration)](/talend/en-US/components/8.0/orchestration)
3. [Orchestration (Integration) scenarios](/talend/en-US/components/8.0/orchestration/orchestration-scenario)
4. [Propagating the buffered output data from the child Job to the parent Job](/talend/en-US/components/8.0/orchestration/trunjob-tfixedflowinput-tbufferoutput-tlogrow-propagating-buffered-output-data-from-child-job-to-parent-job-standard-component-in-this?id=3865)

# Setting up the parent Job

Last updated: 11/3/2026

## About this task

![](/talend/en-US/components/8.0/Content/Resources/images/components-trunjob_scenario3_4.png)

## Procedure

1. Create a Job, and add three components by typing their names on the design
   workspace or dropping them from the Palette
   to the design workspace:
   * a tFixedFlowInput, to generate a
     message
   * a tRunJob, to call the Job named
     *child*
   * a tLogRow, to display the
     execution result on the console
2. Connect the tFixedFlowInput component to
   the tRunJob component and the tRunJob component to the tLogRow component using the Row > Main
   connections.
3. Double-click the tFixedFlowInput
   component to open its Basic settings
   view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/components-trunjob_scenario3_5.png)
4. Click the [...] button next to Edit schema to open the Schema dialog box and define the schema of the input data.
   In this example, the schema has only one column *message* of the string type.

   ![](/talend/en-US/components/8.0/Content/Resources/images/components-trunjob_scenario3_3.png)

   When done, click OK to validate the
   changes.
5. In the Mode area, select the Use Single Table option, and define the
   corresponding value for the *message*
   column in the Values table. In this
   example, the value is *"message from the parent
   job"*.
6. Click the tRunJob component and then
   click the Component tab to open its
   Basic settings view.

   ![](/talend/en-US/components/8.0/Content/Resources/images/components-trunjob_scenario3_6.png)
7. Click the Sync columns button and then
   click Yes in the pop-up Propagate dialog box to retrieve the schema
   from the preceding component.
8. Click the [...] button next to the
   Job field to open the Repository Content dialog box.

   ![](/talend/en-US/components/8.0/Content/Resources/images/components-trunjob_scenario3_7.png)

   In the Repository Content dialog box,
   select the Job named *child* and then click
   OK to close the dialog box.
9. In the Advanced settings view of the
   tRunJob component, select the Propagate the child result to the output schema
   check box. With this check box selected, the buffered output of the child
   Job will be propagated to the output component.

   ![](/talend/en-US/components/8.0/Content/Resources/images/components-trunjob_scenario3_8.png)

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/orchestration/trunjob-tfixedflowinput-tbufferoutput-tlogrow-executing-parent-job-standard-component-press?id=3868 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Orchestration (Integration)](/talend/en-US/components/8.0/orchestration)
3. [Orchestration (Integration) scenarios](/talend/en-US/components/8.0/orchestration/orchestration-scenario)
4. [Propagating the buffered output data from the child Job to the parent Job](/talend/en-US/components/8.0/orchestration/trunjob-tfixedflowinput-tbufferoutput-tlogrow-propagating-buffered-output-data-from-child-job-to-parent-job-standard-component-in-this?id=3865)

# Executing the parent Job

Last updated: 11/3/2026

## Procedure

1. Press Ctrl+S to save the Job.
2. Press F6 or click the Run button on the Run console to execute the Job.

   ![](/talend/en-US/components/8.0/Content/Resources/images/components-trunjob_scenario3_9.png)

   The child Job is called and the message specified in the child Job, rather
   than the message defined in the parent Job, is displayed on the
   console.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)
