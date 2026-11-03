# tmssqlcommit

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tmssqlcommit  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tmssqlcommit -->

# tMSSqlCommit

Commits in one go, using a unique connection, a global transaction instead of doing that on every row or every batch and thus provides gain in performance.

tMSSqlCommit validates the data processed through the Job into the connected DB.

## tMSSqlCommit Standard properties

These properties are used to configure tMSSqlCommit running in the Standard Job framework.

The Standard tMSSqlCommit component belongs to the Databases family.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

Information noteNote: When building a Job as an OSGI Bundle for ESB, MS SQL Server drivers jtds and mssql-jdbc used by the SQL Server components are not included in the build artifact. To run the artifact in Talend Runtime, you need to deploy the drivers manually by copying the drivers to the &lt;TalendRuntimePath&gt;/lib folder and restart Talend Runtime.

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Component list | Select the tMSSqlConnection component<br>in the list if more than one connection are planned for the current Job. |
| Close connection | This check box is selected by default. It allows you to close the database<br>connection once the commit is done. Clear this check box to continue to use the<br>selected connection once the component has performed its task.<br><br>Information noteWarning:<br><br>If you want to use a Row &gt; Main connection to link tMSSqlCommit to your Job, your data will be committed row by<br>row. In this case, do not select the Close<br>connection check box or your connection will be closed before<br>the end of your first row commit. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a job level<br>as well as at each component level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is more commonly used with other tMSSql\* components,<br>especially with the tMSSqlConnection and<br>tMSSqlRollback components. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>Once a dynamic parameter is defined, the Component List box in the Basic<br>settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |

**Related concepts**

* [Inserting data into a database table and extracting useful information from it](https://help.qlik.com/talend/en-US/components/8.0/tmssqlinput-tmssqloutput-tlogrow-inserting-data-into-database-table-and-extracting-useful-information-from-it-standard-component-the)
