# tredshiftclose

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tredshiftclose  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tredshiftclose -->

# tRedshiftClose

Closes the transaction committed in the connected DB.

This component is used together with tRedShiftConnection and tRedshiftCommit to ensure the integrity of the transaction performed into the database.

## tRedshiftClose Standard properties

These properties are used to configure tRedshiftClose running in the Standard Job framework.

The Standard tRedshiftClose component belongs to the Cloud and the Databases families.

The component in this framework is available in all Talend products.

Information noteNote: This component is a specific version of a dynamic database connector. The properties related to database settings vary depending on your database type selection. For more information about dynamic database connectors, see [DB Generic components](https://help.qlik.com/talend/r/en-US/8.0/components/db-generic/db-generic-component).

## Basic settings

| Properties | Description |
| --- | --- |
| Database | Select the desired database type from the list and click<br>Apply. |
| Component list | Select the tRedshiftConnection<br>component in the list if more than one connection are planned for<br>the current Job. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStat<br>Catcher<br>Statistics | Select this check box to collect log data at the component<br>level. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is to be used along with Amazon Redshift<br>components, especially with tRedshiftConnection and tRedshiftCommit. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>Once a dynamic parameter is defined, the Component List box in the Basic<br>settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |

**Related concepts**

* [Handling data with Redshift](https://help.qlik.com/talend/en-US/components/8.0/tredshiftconnection-tredshiftinput-tlogrow-handling-data-with-redshift-standard-component-this)
