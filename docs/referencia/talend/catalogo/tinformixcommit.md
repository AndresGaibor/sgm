# tinformixcommit

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tinformixcommit  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tinformixcommit -->

# tInformixCommit

Makes a global commit just once instead of commiting every row or batch of rows separately.

This component improves performance and is closely related to tInformixConnection and tInformixRollback. They are generally used to execute transactions together.

tInformixCommit validates data processed in a Job from a connected database.

## tInformixCommit Standard properties

These properties are used to configure tInformixCommit running in the Standard Job framework.

The Standard tInformixCommit component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Component list | If there is more than one connection in the Job,<br>select tInformixConnection from the<br>list. |
| Close connection | This check box is selected by default. It means<br>that the database conenction will be closed once the commit has been<br>made. Clear the check box to continue using the connection once the<br>component has completed its task.<br><br>Information noteWarning:<br><br><br>*If you are using a Row &gt; Main type connection to link tInformixCommit to your Job, your<br>data will be committed row by row. If this is the case, do<br>not select this check bx otherwise the conenction will be<br>closed before the commit of your first row is<br>finalized.* |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher<br>Statistics | Select this check box to collect the log data at a<br>component level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is<br>generally used along with Informix components, particularly<br>tInformixConnection and<br>tInformixRollback. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>Once a dynamic parameter is defined, the Component List box in the Basic<br>settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
