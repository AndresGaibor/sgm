# tsortrow (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsortrow  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsortrow -->

# Replicating a flow and sorting two identical flows respectively

The scenario describes a Job that reads an input flow which contains names and states from a CSV file, replicates the input flow, then sorts the two identical flows based on name and state respectively, and displays the sorted data on the console.

![](https://help.qlik.com/talend/en-US/components/Resources/images/use_case_treplicate.png)

### In this section

* [Setting up the Job](https://help.qlik.com/talend/en-US/components/8.0/orchestration/tsortrow-treplicate-tfileinputdelimited-tlogrow-setting-up-job-standard-component-drop?id=3870)
* [Configuring the components](https://help.qlik.com/talend/en-US/components/8.0/orchestration/tsortrow-treplicate-tfileinputdelimited-tlogrow-configuring-components-standard-component?id=3871)
* [Saving and executing the Job](https://help.qlik.com/talend/en-US/components/8.0/orchestration/tsortrow-treplicate-tfileinputdelimited-tlogrow-saving-and-executing-job-standard-component-press?id=3872)

**Related concepts**

* [tSortRow](https://help.qlik.com/talend/en-US/components/8.0/tsortrow "Helps creating metrics and classification table.")
* [tReplicate](https://help.qlik.com/talend/en-US/components/8.0/treplicate "Duplicates the incoming schema into two identical output flows.")

**Related information**

* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)
* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/orchestration/tsortrow-treplicate-tfileinputdelimited-tlogrow-setting-up-job-standard-component-drop?id=3870 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Orchestration (Integration)](/talend/en-US/components/8.0/orchestration)
3. [Orchestration (Integration) scenarios](/talend/en-US/components/8.0/orchestration/orchestration-scenario)
4. [Replicating a flow and sorting two identical flows respectively](/talend/en-US/components/8.0/orchestration/tsortrow-treplicate-tfileinputdelimited-tlogrow-replicating-flow-and-sorting-two-identical-flows-respectively-standard-component-the?id=3869)

# Setting up the Job

Last updated: 11/3/2026

## Procedure

1. Drop the following components from the Palette to the design workspace: one tFileInputDelimited component, one tReplicate component, two tSortRow components, and two tLogRow components.
2. Connect tFileInputDelimited to tReplicate using a Row > Main link.
3. Repeat the step above to connect tReplicate to two tSortRow
   components respectively and connect tSortRow to tLogRow.
4. Label the components to better identify their functions.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/orchestration/tsortrow-treplicate-tfileinputdelimited-tlogrow-configuring-components-standard-component?id=3871 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Orchestration (Integration)](/talend/en-US/components/8.0/orchestration)
3. [Orchestration (Integration) scenarios](/talend/en-US/components/8.0/orchestration/orchestration-scenario)
4. [Replicating a flow and sorting two identical flows respectively](/talend/en-US/components/8.0/orchestration/tsortrow-treplicate-tfileinputdelimited-tlogrow-replicating-flow-and-sorting-two-identical-flows-respectively-standard-component-the?id=3869)

# Configuring the components

Last updated: 11/3/2026

## Procedure

1. Double-click the tFileInputDelimited
   component to open its Basic settings view
   in the Component tab.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case_treplicate1.png)
2. Click the [...] button next to the
   File name/Stream field to browse to the
   file from which you want to read the input flow. In this example, the input
   file is *Names&States.csv*, which
   contains two columns: *name* and *state*.

   ```
   name;state
   Andrew Kennedy;Mississippi
   Benjamin Carter;Louisiana
   Benjamin Monroe;West Virginia
   Bill Harrison;Tennessee
   Calvin Grant;Virginia
   Chester Harrison;Rhode Island
   Chester Hoover;Kansas
   Chester Kennedy;Maryland
   Chester Polk;Indiana
   Dwight Nixon;Nevada
   Dwight Roosevelt;Mississippi
   Franklin Grant;Nebraska
   ```
3. Fill in the Header, Footer and Limit fields
   according to your needs. In this example, type in *1* in the Header field to
   skip the first row of the input file.
4. Click Edit schema to define the data
   structure of the input flow.
   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case_treplicate2.png)
5. Double-click the first tSortRow component
   to open its Basic settings view.
   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case_treplicate3.png)
6. In the Criteria panel, click the
   [+] button to add one row and set the
   sorting parameters for the schema column to be processed. To sort the input
   data by name, select *name* under Schema column. Select *alpha* as the sorting type and *asc* as the sorting order.

   For more information about those parameters, see [tSortRow Standard properties](/talend/en-US/components/8.0/processing/tsortrow-standard-properties).
7. Double-click the second tSortRow
   component and repeat the step above to define the sorting parameters for the
   state column.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case_treplicate4.png)
8. In the Basic settings view of each
   tLogRow component, select Table in the Mode area for a better view of the Job execution
   result.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/orchestration/tsortrow-treplicate-tfileinputdelimited-tlogrow-saving-and-executing-job-standard-component-press?id=3872 -->

Leave your feedback here

[![Close feedback widget](/talend/img/nav/close-white.svg)](javascript:void(0))

1. [Talend Components for Jobs](/talend/en-US/components/8.0)
2. [Orchestration (Integration)](/talend/en-US/components/8.0/orchestration)
3. [Orchestration (Integration) scenarios](/talend/en-US/components/8.0/orchestration/orchestration-scenario)
4. [Replicating a flow and sorting two identical flows respectively](/talend/en-US/components/8.0/orchestration/tsortrow-treplicate-tfileinputdelimited-tlogrow-replicating-flow-and-sorting-two-identical-flows-respectively-standard-component-the?id=3869)

# Saving and executing the Job

Last updated: 11/3/2026

## Procedure

1. Press Ctrl+S to save your Job.
2. Execute the Job by pressing F6 or
   clicking Run on the Run tab.

   ![](/talend/en-US/components/8.0/Content/Resources/images/use_case_treplicate5.png)

   The data sorted by name and state are both displayed on the
   console.

## Did this page help you?

If you find any issues with this page or its content – a typo, a missing step, or a technical error – please let us know!

[Leave your feedback here](#)
