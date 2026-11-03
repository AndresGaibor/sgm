# trunjob

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/trunjob  
> Descargado: 2026-11-03.


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
