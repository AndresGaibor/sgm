# Talend Studio 8.0 (R2026-09): guía de usuario, diseño de Jobs y contextos

> Fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/  
> Descargado: 2026-11-03, versión Markdown oficial de help.qlik.com. Incluye los temas raíz y sus subtemas enlazados (joblets, variables de contexto).


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/designing-a-job -->

# Designing a Joblet

## What is a Joblet

A Joblet is a specific component that replaces Job component groups. It factorizes recurrent processing or complex transformation steps to ease the reading of a complex Job. Joblets can be reused in different Jobs or several times in the same Job.

At runtime, the Joblet code is integrated into the Job code itself. No separate code is generated, the same Java class being used.

This way, the Joblet use does not have any drawbacks on the performance side. The execution time is unchanged whether your Job includes a Joblet or the whole subJob directly.

Moreover if you intend to log and monitor the whole Job statistics and execution error or warnings, the Joblets included in your Job will be monitored without requiring further log component (such as tLogCatcher, tStatCatcher or tFlowCatcher).

A Joblet is easily identified as it is enclosed in a dotted square on a green background.

![Joblet example.](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/JobwithJoblet.png)

This specific component can be used like any other usual component in a Job. For more information on how to design a Job, see [What is a Job design?](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/what-is-job-design).

Note that:

* a Standard Job supports the Standard Joblets only
  * Available in:
  * Big Data
  * Big Data Platform
  * Cloud Big Data
  * Cloud Big Data Platform
  * Cloud Data Fabric
  * Data Fabric
  * Qlik Cloud Enterprise Edition
  * Qlik Talend Cloud Enterprise Edition
  * Qlik Talend Cloud Premium Edition
  * Real-Time Big Data Platform
* a Spark Job supports the Spark Joblets only

Unlike for the tRunJob component, the Joblet code is automatically included in the Job code at runtime, thus using less resources. As it uses the same context variables as the Job itself, the Joblet is easier to maintain.

To use a group of components as a standalone Job, you can use the tRunJob component. Unlike the Joblet, the tRunJob has its own context variables.

### In this section

* [Creating a Joblet from scratch](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/creating-joblet-from-scratch)
* [Creating a Joblet from a Job](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/creating-joblet-from-job)
* [Using a Joblet in a Job](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/using-joblet-in-job)
* [Using a Joblet in the beginning of a Job](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/using-joblet-in-beginning-of-job)
* [Launching a Joblet](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/launching-joblet)
* [Editing a Joblet](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/editing-joblet)
* [Organizing Joblets](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/organizing-joblets)
* [Applying a context variable to a Joblet](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/applying-context-variable-to-joblet)
* [Setting up code dependencies on a Joblet](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/setting-up-code-dependencies-on-joblet)


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/designing-a-joblet -->

# Designing a Joblet

## What is a Joblet

A Joblet is a specific component that replaces Job component groups. It factorizes recurrent processing or complex transformation steps to ease the reading of a complex Job. Joblets can be reused in different Jobs or several times in the same Job.

At runtime, the Joblet code is integrated into the Job code itself. No separate code is generated, the same Java class being used.

This way, the Joblet use does not have any drawbacks on the performance side. The execution time is unchanged whether your Job includes a Joblet or the whole subJob directly.

Moreover if you intend to log and monitor the whole Job statistics and execution error or warnings, the Joblets included in your Job will be monitored without requiring further log component (such as tLogCatcher, tStatCatcher or tFlowCatcher).

A Joblet is easily identified as it is enclosed in a dotted square on a green background.

![Joblet example.](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/JobwithJoblet.png)

This specific component can be used like any other usual component in a Job. For more information on how to design a Job, see [What is a Job design?](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/what-is-job-design).

Note that:

* a Standard Job supports the Standard Joblets only
  * Available in:
  * Big Data
  * Big Data Platform
  * Cloud Big Data
  * Cloud Big Data Platform
  * Cloud Data Fabric
  * Data Fabric
  * Qlik Cloud Enterprise Edition
  * Qlik Talend Cloud Enterprise Edition
  * Qlik Talend Cloud Premium Edition
  * Real-Time Big Data Platform
* a Spark Job supports the Spark Joblets only

Unlike for the tRunJob component, the Joblet code is automatically included in the Job code at runtime, thus using less resources. As it uses the same context variables as the Job itself, the Joblet is easier to maintain.

To use a group of components as a standalone Job, you can use the tRunJob component. Unlike the Joblet, the tRunJob has its own context variables.

### In this section

* [Creating a Joblet from scratch](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/creating-joblet-from-scratch)
* [Creating a Joblet from a Job](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/creating-joblet-from-job)
* [Using a Joblet in a Job](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/using-joblet-in-job)
* [Using a Joblet in the beginning of a Job](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/using-joblet-in-beginning-of-job)
* [Launching a Joblet](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/launching-joblet)
* [Editing a Joblet](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/editing-joblet)
* [Organizing Joblets](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/organizing-joblets)
* [Applying a context variable to a Joblet](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/applying-context-variable-to-joblet)
* [Setting up code dependencies on a Joblet](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/setting-up-code-dependencies-on-joblet)


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/defining-variables -->

# Defining context variables

## Procedure

1. Click the [+] button to add lines in the table.

   ![Context view.](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/studio-context-view-for-job-or-route.png)
2. Click in the Name field and enter the name of the variable you are creating.

   Name the first variable host for this example.
3. From the Type list, select the type of the variable.

   Information noteWarning: If you change the type of a variable that has already a value, the value will be cleared and you need to set it again.
4. If needed, click in the Comment field and enter a comment to describe the variable.
5. Click in the value field for each context environment and enter the variable value.

   For different variable types, the value field appears slightly different when you click in it and functions differently:
   | Type | Value field |
   | --- | --- |
   | String (default type) | Editable text field |
   | Boolean | Drop-down list box with two options:<br>true and<br>false |
   | Character,<br>Double,<br>Integer,<br>Long,<br>Short,<br>Object,<br>BigDecimal | Editable text field |
   | Date | Editable text field, with a button to open<br>theSelect Date & Time dialog<br>box. |
   | File | Editable text field, with a button to open the<br>Open dialog box for file<br>selection. |
   | Directory | Editable text field, with a button to open the<br>Browse for Folder dialog box for<br>folder selection. |
   | List of Value | Editable text field, with a button to open the<br>Configure Values dialog box for<br>list creation and configuration. |
   | Password | Editable text field; text entered appears<br>encrypted. |
   | Resource | Editable text field, with a button to open the<br>Select a Resource dialog box for<br>you to select a resource defined under<br>Resources in the Repository.<br><br><br>For more information, see [Using resources in Jobs](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/using-resources-in-jobs "You can create resources in Talend Studio and use them in your Jobs for file handling. This way, when exporting your Jobs, for example, you can pack the resource files as Job dependencies and deploy your Jobs without having to copy the files to the target system."). |
6. Optional: To display a prompt for the variable value and to edit it when running your Job or Route in a context environment, select the Enable prompt check box.

   This check box is applied globally to all context environments and the context variable name is used as the prompt label.
7. Repeat the above steps to define all the variables for the different contexts.
   * port, type String,
   * database, type String,
   * username, type String,
   * password, type Password,
   * table, type String.

## Results

All the variables created and their values under different context environments are displayed in the table and are ready for use in your Job. You can further edit the variables in this view if needed.

You can also add a built-in context variable to the Repository to make it reusable across different Jobs. For more information, see [Adding a built-in context variable to the Repository](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/adding-built-in-context-variable-to-repository).

Related topics:

* [Defining context variables from the Component view](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/defining-variables-from-component-view)
* [Centralizing context variables in the Repository](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/centralizing-context-variables-in-repository)
* [Using variables in a Job or Route](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/using-variables-in-job-or-route)
* [Running a Job or Route in a selected context environment](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/running-job-or-route-in-selected-context)


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/applying-context-variable-to-joblet -->

# Applying a context variable to a Joblet

The context variable stored in the repository can be applied to a Joblet the same way as to any other Jobs.

In addition, a Job containing a Joblet allows its Joblet to use different context variables from those the Job is using. To do so, simply drop the group of contexts you want to use onto the Joblet in the workspace of the Job.

For more information on how to apply a context variable to a Job from the repository, see [Applying Repository context variables to a Job or Route](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/applying-repository-context-variables-to-job-or-route).


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/creating-joblet-from-job -->

# Creating a Joblet from a Job

## About this task

You can create a Joblet directly from an existing Job. To do so:

## Procedure

1. Open the Job in Talend Studio.

   ![Standard Job with tMap component.](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/refactor_to_joblet1.png)
2. Right-click the component(s) you want to transform to a Joblet and select Refactor to Joblet from the contextual menu to open the New Joblet dialog box. In this example, tMap will be transformed to a Joblet.
3. In the New Joblet dialog box, fill in at least the Name field to designate the Joblet. You can also add information to ease the Joblet management, such as: Description, Version, Author and Status.

   New Joblet parametersNew JobletNew Joblet parameters
   | Field | Description |
   | --- | --- |
   | Name | Enter a name for your new Joblet. A message comes up if you enter prohibited characters. |
   | Purpose | Enter the Joblet purpose or any useful information regarding the Job in use. |
   | Description | Enter a description if need. |
   | Author | This field is read-only as it shows by default the current user login. |
   | Locker | This field is read-only as it shows by default the current user login. |
   | Version | The version is read-only. You can manually increment the version using the M and m buttons. |
   | Status | Select a status from the list. By default, the status you can select is development, testing, or<br>production. To define more statuses, see [Status settings](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/status-settings). |
   | Path | This field is read-only. It refers to the item access path in the repository. This field<br>is empty when the item is created in the root folder. |
4. Click Finish to validate your settings and close the dialog box.

   The design workspace opens showing the Joblet name as tab label. The input and output Joblet components are automatically included in the Joblet during its creation and the transformation component selected for creating the Joblet, tMap in this example. ![Joblet "SimpleTransformation 0.1"](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/Joblet.png)

   The tMap component is then automatically replaced by the Joblet component in the Job.

   ![Joblet "SimpleDataTransformation 0.1"](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/JobwithJoblet.png)
5. Save your Job and press F6 to execute it.

## Results

You can as well include other transformation steps after your Joblet, if necessary. For more information about modifying a Joblet, see [Editing a Joblet](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/editing-joblet).


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/creating-joblet-from-scratch -->

# Creating a Joblet from scratch

## Procedure

1. In Talend Studio Repository tree view, right-click the Job Designs node or Joblets under the Job Designs node, and select Create Joblet on the contextual menu.

   !["Create Joblet" option from the contextual menu.](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/Repository_joblet1.png)
2. In the New Joblet dialog box, fill in at least the Name field to designate the Joblet. You can also add information to ease the Joblet management, such as: Description, Version, Author and Status.

   New Joblet parametersNew JobletNew Joblet parameters
   | Field | Description |
   | --- | --- |
   | Name | Enter a name for your new Joblet. A message comes up if you enter prohibited characters. |
   | Purpose | Enter the Joblet purpose or any useful information regarding the Job in use. |
   | Description | Enter a description if need. |
   | Author | This field is read-only as it shows by default the current user login. |
   | Locker | This field is read-only as it shows by default the current user login. |
   | Version | The version is read-only. You can manually increment the version using the M and m buttons. |
   | Status | Select a status from the list. By default, the status you can select is development, testing, or<br>production. To define more statuses, see [Status settings](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/status-settings). |
   | Path | This field is read-only. It refers to the item access path in the repository. This field<br>is empty when the item is created in the root folder. |
3. Click Finish to validate your settings and close the dialog box.

   The design workspace opens showing the Joblet name as tab label. By default the newly created Joblet includes an input and an output Joblet component.

   The INPUT component is only to be used if there is a flow coming from the main Job that should be used in the Joblet, and the OUTPUT component is only to be used if there is a flow going out of the Joblet that needs be used in the main Job. You can remove either or both of them as needed.

   ![INPUT and OUTPUT components.](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/Joblet_New2.png)
4. Include the transformation components you need and connect them to the Joblet input and the output components.

   In the example below, the input component is removed, and a tMap component is used for the transformation step.

   If you need lookup connections, include them here as well.

   ![Joblet "Transformation 0.1"](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/Joblet_New3.png)
5. Define the input component schema of the Joblet.

   As for any component requiring a schema definition, you can define your schema as Built-in, import it from an XML file or retrieve it from the Repository tree view.

## Results

The output schema is automatically retrieved from the preceding component (likely the transformation component) but you can also change it if you like. The next step is to use the Joblet you have just created in your usual Job in order to replace the transformation steps.

Information noteNote: Note that you can also include Joblets in a Joblet.


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/editing-joblet -->

# Editing a Joblet

## About this task

You can edit a Joblet just like any other Job in the Integration perspective of Talend Studio.

You can make changes to a Joblet and get your changes reflected in the actual Job execution output. These changes can be made directly in the Job or in a separate tab view.

Note that you can not modify the links of the Joblet directly in the Job.

## Editing the Joblet in the Job

### Procedure

1. Click the [+] sign to expand the Joblet.

   ![Job containing the "SimpleTransformation_1" Joblet.](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/JobwithExpandedJoblet.png)
2. Double-click any component to open its Basic settings view and modify its properties.
3. Press Ctrl+S to save your changes.

## Editing the Joblet in a new tab view

### Procedure

1. Double-click the Joblet you want to edit. You can also right-click it and select Open Joblet Component from the contextual menu.

   The Joblet is automatically locked.

   Information noteNote: If you do not want the Joblet to open when double-clicking on it, see [Changing specific component settings](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/how-to-change-specific-component-settings-talend-components).
2. Make your changes on your Joblet.
3. If you modify any trigger link connected to the Trigger Input or to the Trigger Output component, be sure to update the Job using this Joblet accordingly.
4. Press Ctrl+S to save your changes.


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/launching-joblet -->

# Launching a Joblet

## About this task

It is possible to use a Joblet as a step in a procedure. You can start a Joblet, or a subJob after the execution of a Joblet, using the Trigger Input and Trigger Output components from the Palette. In this example, the created Joblet is called Transformation.

## Using triggers in a Joblet

### Procedure

1. Drag the Trigger Input component from the Palette and drop it above your Joblet.
2. Right-click Trigger Input, select a link of the type Trigger &gt; OnSubjobOk and then click the input component of the Joblet so that your Joblet starts after the execution of the first subJob.
3. Drag the Trigger Output component from the Palette and drop it below the Joblet.
4. Right-click the input component of the Joblet and select a link of the type Trigger &gt; OnSubjobOk and then click the Trigger Output component so that your third subJob starts after the execution of your Joblet.
   ### Example

   ![Joblet with triggers.](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/Joblet_trigger_input_output.png)

## Launching the Joblet in a Job

### Procedure

1. Create a new Job.
2. From the Repository tree view, click the created Joblet (Transformation) and drop it in the Job.
3. Drop a tFileOutputDelimited component next to the Joblet component, drop a tWarn component above the Joblet component, and drop a tMsgBox component below the Joblet component.
4. Right-click the Joblet component and then select the Row &gt; Joblet OUTPUT\_1 link and click tFileOutputDelimited.
5. Double-click tFileOutputDelimited to display its basic settings and then define the path to the folder and file to be created in the File Name field.
6. Right-click the tWarn component and select the link of the type Trigger &gt; On Subjob Ok (TRIGGER\_INPUT\_1) and then click the Joblet component.
7. Double-click the component that represents the Joblet to display its basic settings view.

   In the Joblet TRIGGER\_INPUT\_1 field, the link type defined in the Joblet is read-only.

   Information noteTip: If you use many Triggers Input components in the Joblet and corresponding launching components in the Job, verify that the right component is attached with the right launching link in the Attached node field of the Basic settings view.
8. From the Version list, select the Joblet version you want to use in your Job. In this example, we use the latest version of the Joblet.
   ### Example

   ![Basic settings view of the "Transformation" Joblet.](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/Joblet_BasicSettings_TriggerInput.png)
9. Right-click the Joblet component, select the link Trigger &gt; On Subjob Ok (TRIGGER\_OUTPUT\_1), and then click the tMsgBox component.
   ### Example

   ![](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/JobwithJoblet_TriggerInputOutput.png)
10. Run your Job.

### Results

The tWarn component sends a warning massage and launches the next subJob holding the Joblet you created: Transformation. Once the second subJob is successfully executed, it launches a third subJob holding the tMsgBox component indicating at the same time that the transformation has been carried out.


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/organizing-joblets -->

# Organizing Joblets

The same way as for the Job Designs, you can create folders using the right-click menu to gather together families of Joblets.

## Procedure

1. In Talend Studio Repository tree view, click Job Designs &gt; Joblets to expand the Joblets node.
2. Right-click on the Joblets node, and choose Create folder.
3. Give a name to this folder and click OK.
4. If you have already created Joblets that you want to move in this new folder, simply drag and drop them into the folder.


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/setting-up-code-dependencies-on-joblet -->

# Setting up code dependencies on a Joblet

If you want to enable your Joblet to call any function in a routine or custom routine jar, you need to set up code dependencies, namely routine or custom routine jar dependencies, on the Joblet.

You can set up code dependencies on a Joblet in the same way as setting up code dependencies on a Job. For more information, see [Setting up code dependencies on a Job](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/setting-up-code-dependencies-on-job).


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/using-joblet-in-beginning-of-job -->

# Using a Joblet in the beginning of a Job

## About this task

It is possible to use your Joblet in the beginning of a Job. To do so:

## Procedure

1. Open the Joblet you want to use in the beginning of a Job.
2. Click the Joblet tab in the lower part of Talend Studio to display the relevant view and then click Extra.
3. Select the Startable check box.

   !["Startable" check box from the Extra view of the Joblet.](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/Joblet_startable.png)


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/using-joblet-in-job -->

# Using a Joblet in a Job

## About this task

As soon as you have created a Joblet, you will find it in your usual Palette of components and thus you will be able to include it in the place of the transformation steps in your Job.

![Joblet "Transformation" in the Palette.](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/JobletinPalette.png)

## Procedure

1. Like any other component, click the relevant Joblet name in the Palette and drop it to the design workspace to include it in your Job.
2. Connect the Joblet with the input and/or output components of the Job.

   ![Job "DataTransformation 0.1"](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/JobwithJoblet2.png)

   Note that:
   * A Joblet in a Job can be connected using the same types of links which are used inside the Joblet to connect the Trigger Input component to the input component.
   * A Joblet in a Job provides the same types of output links which are used inside the Joblet to connect the input component to the Trigger Output component.

   For more information about how to use triggers in a Joblet, see [Using triggers in a Joblet](https://help.qlik.com/talend/en-US/studio-user-guide/8.0/launching-joblet#using-triggers-in-a-joblet_t).

   Let's take the following Joblet as an example: the Trigger &gt; On SubJob Ok link and the Trigger &gt; On Component Ok link are used to connect the Trigger Input component to the input component and to connect the input component to the Trigger Output component, and both of them can be used as the input and output links of the Joblet in a Job.

   ![Joblet with tJava and trigger options.](https://help.qlik.com/talend/en-US/studio-user-guide/Resources/images/studio-joblet-connections.png)
3. Define all other components properties and context variables, if required, before running the Job like any other Job.
4. Include other transformation steps following the Joblet if required.
5. Save and run your Job as usual.


---

<!-- fuente: https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/using-resources-in-jobs -->

# Using resources in Jobs

You can create resources in Talend Studio and use them in your Jobs for file handling. This way, when exporting your Jobs, for example, you can pack the resource files as Job dependencies and deploy your Jobs without having to copy the files to the target system.

This feature is not shipped with Talend Studio by default. You need to install it using the Feature Manager. For more information, see [Installing features using the Feature Manager](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/install-features-to-talend-studio).

### In this section

* [Creating a resource](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/creating-resource)
* [Using a resource in a Job](https://help.qlik.com/talend/en-US/studio-user-guide/8.0-R2026-09/using-resource-in-job)
