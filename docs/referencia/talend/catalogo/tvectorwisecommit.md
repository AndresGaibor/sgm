# tvectorwisecommit

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tvectorwisecommit  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tvectorwisecommit -->

# tVectorWiseCommit

Commits a global transaction in one go using a single connection instead of doing so on every row or every batch. This provides a gain in performance

tVectorWiseCommit validates the data processed in a Job into the connected DB.

Information noteNote:

* This component is available only when you have installed the 8.0.1-R2023-02 Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator.
* If you plan to upgrade from an earlier version of Talend Studio that has Vectorwise components, please make sure you apply the 8.0.1-R2023-02 Talend Studio Monthly update before starting the upgrade process.

## tVectorWiseCommit Standard properties

These properties are used to configure tVectorWiseCommit running in the Standard Job framework.

The Standard tVectorWiseCommit component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Component list | Select the tVectorWiseConnection<br>component from the list if more than one connection is planned for<br>the current job. |
| Close connection | This check box is selected by default. It allows you to close the<br>database connection once the commit is done. Clear this check box to<br>continue to use the selected connection once the component has<br>performed its task.<br><br>Information noteWarning: If you want to use a Row &gt;Main connection<br>to link tVectorWiseCommit to your Job,<br>your data will be committed row by row. In this case, do not select the<br>Close connection check box or your<br>connection will be closed before the end of your first row commit. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is more commonly used with other Vectorwise<br>components, especially with the tVectorWiseConnection and tVectorWiseRollback components. |
| Dynamic settings | Click the [+] button to add a row<br>in the table and fill the Code<br>field with a context variable to choose your database connection<br>dynamically from multiple connections planned in your Job.<br><br>Once a dynamic parameter is defined, the Component List box in the Basic<br>settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
