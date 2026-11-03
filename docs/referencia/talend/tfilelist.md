# tfilelist (Talend Studio 8.0)

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tfilelist  
> Descargado: 2026-11-03, desde help.qlik.com (versión Markdown o HTML convertido). Orden: página principal y subpáginas enlazadas.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfilelist -->

# tFileList

### In this section

* [tFileList component](https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist-component)
* [tFileList scenarios](https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist-scenario)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist-component -->

# tFileList component

| [tFileList](https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist) | Iterates a set of files or folders in a given directory based on a<br>filemask pattern. |
| --- | --- |


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist-scenario -->

# tFileList scenarios

* [Finding duplicate files between two folders](https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist-titeratetoflow-tfileoutputdelimited-tlogrow-finding-duplicate-files-between-two-folders-standard-component-this)
* [Iterating on a file directory](https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist-tfileinputdelimited-tlogrow-tlogrow-iterating-on-file-directory-standard-component-the)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist -->

# tFileList

Iterates a set of files or folders in a given directory based on a filemask pattern.

## tFileList Standard properties

These properties are used to configure tFileList running in the Standard Job framework.

The Standard tFileList component belongs to the File and the Orchestration families.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Directory | Path to the directory where the files are stored.<br><br>Information noteWarning: Use absolute path (instead of relative path) for<br>this field to avoid possible errors. |
| FileList Type | Select the type of input you want to iterate on from the<br>list:<br><br><br>Files if the input is a set of<br>files,<br><br><br>Directories if the input is a set<br>of directories,<br><br><br>Both if the input is a set of the<br>above two types. |
| Include subdirectories | Select this check box if the selected input source type includes<br>sub-directories. |
| Case Sensitive | Set the case mode from the list to either create or not create<br>case sensitive filter on filenames. |
| Generate Error if no file found | Select this check box to generate an error message if no files or<br>directories are found. |
| Use Glob Expressions as Filemask | This check box is selected by default. It filters the results<br>using a Global Expression (Glob<br>Expressions). |
| Files | Click the plus button to add as many filter lines as needed:<br><br><br>Filemask: in the added filter<br>lines, type in a filename or a filemask using special characters or<br>regular expressions. |
| Order by | The folders are listed first of all, then the files. You can<br>choose to prioritise the folder and file order either:<br><br><br>By default: alphabetical order, by<br>folder then file;<br><br><br>By file name: alphabetical order or<br>reverese alphabetical order;<br><br><br>By file size: smallest to largest<br>or largest to smallest;<br><br><br>By modified date: most recent to<br>least recent or least recent to most recent.<br><br>Information noteNote:<br><br>If ordering by file name, in<br>the event of identical file names then modified date takes precedence. If ordering<br>by file size, in the event<br>of identical file sizes then file<br>name takes precedence. If ordering by modified date, in the event of<br>identical dates then file name<br>takes precedence. |
| Order action | Select a sort order by clicking one of the<br>following radio buttons:<br><br><br>ASC: ascending order;<br><br><br>DESC: descending<br>order; |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use Exclude Filemask | Select this check box to enable Exclude Filemask field to exclude<br>filtering condition based on file type:<br><br><br>Exclude<br>Filemask: Fill in the field with file types to be<br>excluded from the Filemasks in<br>the Basic settings view.<br><br>Information noteNote: File types in this field should be quoted with<br>double quotation marks and seperated by comma. |
| Format file path to slash(/) style(useful on<br>Windows) | Select this check box to format the file path to<br>slash(/) style which is useful on Windows. |
| tStatCatcher Statistics | Select this check box to gather the Job processing<br>metadata at a Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | CURRENT\_FILE: the<br>current file name. This is a Flow variable and it returns a string.<br><br><br>CURRENT\_FILEPATH:<br>the current file path. This is a Flow variable and it returns a string.<br><br><br>CURRENT\_FILEEXTENSION: the extension of the<br>current file. This is a Flow variable and it returns a string.<br><br><br>CURRENT\_FILEDIRECTORY: the current file directory. This is a Flow<br>variable and it returns a string.<br><br><br>NB\_FILE:<br>the number of files iterated upon so far. This is a Flow variable and it returns an<br>integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | tFileList provides a list of<br>files or folders from a defined directory on which it iterates |
| Connections | Outgoing links (from this component to another):<br><br><br>Row: Iterate<br><br><br>Trigger: On Subjob Ok; On Subjob<br>Error; Run if; On Component Ok; On Component Error.<br><br>Incoming links (from one component to this one):<br><br><br>Row: Iterate.<br><br><br>Trigger: Run if; On Subjob Ok; On<br>Subjob Error; On component Ok; On Component Error; Synchronize;<br>Parallelize.<br><br>For further information regarding connections, see [Using connections in a Job](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/using-connections-in-job). |

**Related tasks**

* [Finding duplicate files between two folders](https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist-titeratetoflow-tfileoutputdelimited-tlogrow-finding-duplicate-files-between-two-folders-standard-component-this "This scenario describes a Job that iterates on files in two folders, transforms the iteration results to data flows to obtain a list of filenames, and then picks up all duplicates from the list and shows them on the Run console, as a preparation step before merging the two folders, for example.")
* [Iterating on a file directory](https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist-tfileinputdelimited-tlogrow-tlogrow-iterating-on-file-directory-standard-component-the "The following scenario creates a three-component Job, which aims at listing files from a defined directory, reading each file by iteration, selecting delimited data and displaying the output in the Run log console.")


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist-titeratetoflow-tfileoutputdelimited-tlogrow-finding-duplicate-files-between-two-folders-standard-component-this -->

# Finding duplicate files between two folders

This scenario describes a Job that iterates on files in two folders, transforms the iteration results to data flows to obtain a list of filenames, and then picks up all duplicates from the list and shows them on the Run console, as a preparation step before merging the two folders, for example.

![Job description.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/components-use_case-tfilelist_s2-1.png)

## Dropping and linking the components

### Procedure

1. From the Palette, place the following components onto the design workspace:
   * two tFileList components,
   * two tIterateToFlow components,
   * two tFileOutputDelimited components,
   * a tFileInputDelimited component,
   * a tUniqRow component,
   * and a tLogRow component.
2. Link the first tFileList component to the first tIterateToFlow component using a Row &gt; Iterate connection, and the connect the first tIterateToFlow component to the first tFileOutputDelimited component using a Row &gt; Main connection to form the first subJob.
3. Link the second tFileList component to the second tIterateToFlow component using a Row &gt; Iterate connection, and the connect the second tIterateToFlow component to the second tFileOutputDelimited component using a Row &gt; Main connection to form the second subJob.
4. Link the tFileInputDelimited to the tUniqRow component using a Row &gt; Main connection, and the tUniqRow component to the tLogRow component using a Row &gt; Duplicates connection to form the third subJob.
5. Link the three subJobs using Trigger &gt; On Subjob Ok connections so that they will be triggered one after another.

   Label the components to better identify their roles in the Job.

## Configuring the components

### Procedure

1. In the Basic settings view of the first tFileList component, fill the Directory field with the path to the first folder you want to read filenames from, E:/DataFiles/DI/images in this example, and leave the other settings as they are.

   ![Basic settings view for tFileList.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/components-use_case-tfilelist_s2-2.png)
2. Double-click the first tIterateToFlow component to show its Basic settings view.

   ![Basic settings view for tIterateToFlow.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/components-use_case-tfilelist_s2-3.png)
3. Double-click the [...] button next to Edit schema to open the Schema dialog box and define the schema of the text file the next component will write filenames to. When done, click OK to close the dialog box and propagate the schema to the next component.

   In this example, the schema contains only one column: Filename.

   ![Schema with Filename column.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/components-use_case-tfilelist_s2-4.png)
4. In Value field of the Mapping table, press Ctrl+Space to access the autocomplete list of variables, and select the global variable ((String)globalMap.get("tFileList\_1\_CURRENT\_FILE")) to read the name of each file in the input directory, which will be put into a data flow to pass to the next component.
5. In the Basic settings view of the first tFileOutputDelimited component, fill the File Name field with the path of the text file that will store the filenames from the incoming flow, D:/temp/tempdata.csv in this example. This completes the configuration of the first subJob.

   ![Basic settings view for tFileOutputDelimited.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/components-use_case-tfilelist_s2-5.png)
6. Repeat the steps above to complete the configuration of the second subJob, but:
   * fill the Directory field in the Basic settings view of the second tFileList component with the other folder you want to read filenames from, E:/DataFiles/DQ/images in this example.

   * select the Append check box in the Basic settings view of the second tFileOutputDelimited component so that the filenames previously written to the text file will not be overwritten.
7. In the Basic settings view of the tFileInputDelimited component, fill the File name/Stream field with the path of the text file that stores the list of filenames, D:/temp/tempdata.csv in this example, and define the file schema, which contains only one column in this example, Filename.

   ![Basic settings view for tFileInputDelimited.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/components-use_case-tfilelist_s2-6.png)
8. In the Basic settings view of the tUniqRow component, select the Key attribute check box for the only column, Filename in this example.

   ![Basic settings view for tUniqRow.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/components-use_case-tfilelist_s2-7.png)
9. In the Basic settings view of the tLogRow component, select the Table (print values in cells of a table) option for better display effect.

## Executing the Job

### Procedure

1. Press Ctrl+S to save your Job.
2. Click Run or press F6 to run the Job.

   All the duplicate files between the selected folders are displayed on the console.

   ![Job results.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/components-use_case-tfilelist_s2-8.png)

### Results

For other scenarios using tFileList, see [tFileCopy](https://help.qlik.com/talend/en-US/components/8.0/tfilecopy/tfilecopy).

**Related reference**

* [tFileList](https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist "Iterates a set of files or folders in a given directory based on a filemask pattern.")

**Related information**

* [tIterateToFlow](https://help.qlik.com/talend/en-US/components/8.0/orchestration/titeratetoflow)
* [tFileOutputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited)
* [tUniqRow](https://help.qlik.com/talend/en-US/components/8.0/deduplication/tuniqrow)
* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited)
* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist-tfileinputdelimited-tlogrow-tlogrow-iterating-on-file-directory-standard-component-the -->

# Iterating on a file directory

The following scenario creates a three-component Job, which aims at listing files from a defined directory, reading each file by iteration, selecting delimited data and displaying the output in the Run log console.

![Job description.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileList.png)

## Dropping and linking the components

### Procedure

1. Place the following components from the Palette to the design workspace:
   * tFileList,
   * tFileInputDelimited,
   * tLogRow.
2. Right-click the tFileList component, and pull an Iterate connection to the tFileInputDelimited component. Then pull a Main row from the tFileInputDelimited to the tLogRow component.

## Configuring the components

### Procedure

1. Double-click tFileList to display its Basic settings view and define its properties.

   ![Basic settings view for tFileList.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileList1.png)
2. Browse to the Directory that holds the files you want to process. To display the path on the Job itself, use the label (\_\_DIRECTORY\_\_) that shows up when you put the pointer anywhere in the Directory field. Type in this label in the Label Format field you can find if you click the View tab in the Basic settings view.

   ![View tab in the Basic settings view.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileList4.png)
3. In the Basic settings view and from the FileList Type list, select the source type you want to process, Files in this example.
4. In the Case sensitive list, select a case mode, Yes in this example to create case sensitive filter on file names.
5. Keep the Use Glob Expressions as Filemask check box selected if you want to use global expressions to filter files, and define a file mask in the Filemask field.
6. Double-click tFileInputDelimited to display its Basic settings view and set its properties.

   ![Basic settings view for tFileInputDelimited.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileList2.png)
7. Enter the File Name field using a variable containing the current filename path, as you filled in the Basic settings of tFileList. Press Ctrl+Space bar to access the autocomplete list of variables, and select the global variable ((String)globalMap.get("tFileList\_1\_CURRENT\_FILEPATH")) . This way, all files in the input directory can be processed.
8. Fill in all other fields as detailed in the tFileInputDelimited section. Related topic: [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited).
9. Select the last component, tLogRow, to display its Basic settings view and fill in the separator to be used to distinguish field content displayed on the console. Related topic: [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow).

## Executing the Job

### Procedure

1. Press Ctrl+S to save your Job.
2. Click Run or press F6 to run the Job.

   The Job iterates on the defined directory, and reads all included files. Then delimited data is passed on to the last component which displays it on the console.

   ![Job results.](https://help.qlik.com/talend/en-US/components/8.0/Resources/images/Use_Case_tFileList3.png)

**Related reference**

* [tFileList](https://help.qlik.com/talend/en-US/components/8.0/tfilelist/tfilelist "Iterates a set of files or folders in a given directory based on a filemask pattern.")

**Related information**

* [tFileInputDelimited](https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileinputdelimited)
* [tLogRow](https://help.qlik.com/talend/en-US/components/8.0/logs-and-errors/tlogrow)
