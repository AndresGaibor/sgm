# tsqltemplatemerge

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsqltemplatemerge  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsqltemplatemerge -->

# tSQLTemplateMerge

Merges data into a database table directly on the DBMS by creating and executing a MERGE statement.

tSQLTemplateMerge creates an SQL MERGE statement to merge data into a database table.

## tSQLTemplateMerge Standard properties

These properties are used to configure tSQLTemplateMerge running in the Standard Job framework.

The Standard tSQLTemplateMerge component belongs to the ELT family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Database Type | Select the type of database you want to work on from the drop-down<br>list. |
| Component list | Select the relevant DB connection component from the list if you<br>use more than one connection in the current Job. |
| Source table name | Name of the database table holding the data you want to merge into<br>the target table. |
| Target table name | Name of the table you want to merge data into. |
| Schema and Edit<br>schema | <ul> <li> <p>This component involves two schemas: source schema and target								schema. </p> <p> A schema is a row description, that is to say, it defines the								number of fields to be processed and passed on to the next								component. The schema is either built-in or remotely stored in the								Repository.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-in</span>: The schema is created								and stored locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: The schema already								exists and is stored in the Repository, hence can be reused. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul> |
| Merge ON | Specify the target and source columns you want to use as the<br>primary keys. |
| Use UPDATE (WHEN MATCHED) | Select this check box to update existing records. With the check<br>box selected, the UPDATE Columns<br>table appears, allowing you to define the columns in which records<br>are to be updated. |
| Specify additional output columns | Select this check box to update records in additional columns<br>other than those listed in the UPDATE<br>Columns table. With this check box selected, the<br>Additional UPDATE Columns table<br>appears, allowing you to specify additional columns. |
| Specify UPDATE WHERE clause | Select this check box and type in a WHERE clause in the WHERE clause field to filter data during<br>the update operation.<br><br>Information noteNote:<br><br>This option may not work with certain database versions,<br>including Oracle 9i. |
| Use INSERT (WHEN MATCHED) | Select this check box to insert new records. With the check box<br>selected, the INSERT Columns table<br>appears, allowing you to specify the columns to be involved in the<br>insert operation. |
| Specify additional output columns | Select this check box to insert records to additional columns<br>other than those listed in the INSERT<br>Columns table. With this check box selected, the<br>Additional INSERT Columns table<br>appears, allowing you to specify additional columns. |
| Specify INSERT WHERE clause | Select this check box and type in a WHERE clause in the WHERE clause field to filter data during<br>the insert operation.<br><br>Information noteNote:<br><br>This option may not work with certain database versions,<br>including Oracle 9i. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a<br>Job level as well as at component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>NB\_LINE\_MERGED: the number of<br>rows merged. This is an After variable and it returns an integer.<br><br><br>QUERY: the query statement<br>being processed. This is a Flow variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used as an intermediate component with other<br>relevant DB components, especially the DB connection and commit<br>components. |
| SQL Template | SQL Template List |

**Related concepts**

* [Merging data directly on the DBMS](https://help.qlik.com/talend/en-US/components/8.0/tsqltemplatemerge-tsqltemplatecommit-tmysqlinput-tmysqlcommit-merging-data-directly-on-dbms-standard-component-this)
