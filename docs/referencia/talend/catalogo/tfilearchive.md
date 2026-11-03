# tfilearchive

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tfilearchive  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfilearchive -->

# tFileArchive

Creates a new zip, gzip, or tar.gz archive file from one or more files or folders.

The archive file can be compressed using different compression method.

## tFileArchive Standard properties

These properties are used to configure tFileArchive running in the Standard Job framework.

The Standard tFileArchive component belongs to the File family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Directory | Specify the directory that contains the files to be added to the<br>archive file.<br><br>This field is available when zip<br>or tar.gz is selected from the<br>Archive format list.<br><br>Information noteWarning: Use absolute path (instead of relative path) for<br>this field to avoid possible errors. |
| Subdirectories | Select this check box if you want to add the files in the<br>subdirectories to the archive file.<br><br>This field is available only when zip is selected from the Archive format list. |
| Source File | Specify the path to the file that you want to add to the archive<br>file.<br><br>This field is available only when gzip is selected from the Archive format list. |
| Archive file | Specify the path to the archive file to be created.<br><br>Information noteWarning: Use absolute path (instead of relative path) for<br>this field to avoid possible errors. |
| Create directory if does not exist | Select this check box to create the destination folder if it does<br>not exist. |
| Archive format | Select an archive file format from the list: zip, gzip, or<br>tar.gz. |
| Compress level | Select the compression level you want to apply.<br><br><ul> <li> <p> <span>Best</span>: the compression                                        quality will be optimum, but the compression time will be                                        long.</p> </li> <li> <p> <span>Normal</span>: the compression                                        quality and time will be average. </p> </li> <li> <p> <span>Fast (no compression)</span>:                                        the compression will be fast, but the quality will be                                        lower.</p> </li> </ul> |
| All files | Select this check box if all files in the specified directory will<br>be added to the archive file. Clear it to specify the file(s) you<br>want to add to the archive file in the Files<br>table.<br><br><br>Filemask: type in the file name<br>or the file mask using a special character or a regular<br>expression.<br><br>This check box is available when zip or tar.gz is<br>selected from the Archive format<br>list. |
| Encoding | Select an encoding type from the list or select CUSTOM and define it manually. This field<br>is compulsory for DB data handling.<br><br>This list is available when zip<br>is selected from the Archive format<br>list. |
| Overwrite Existing Archive | This check box is selected by default. This allows you to save an<br>archive by replacing the existing one. But if you clear the check<br>box, an error is reported, the replacement fails and the new archive<br>cannot be saved.<br><br>Information noteNote:<br><br>When the replacement fails, the Job runs. |
| Encrypt files | Select this check box if you want the archive file to be password<br>protected.<br><br><br>Encrypt method: select an encrypt<br>method from the list, Java Encrypt,<br>Zip4j AES, or Zip4j STANDARD.<br><br><br>AES Key Strength: select a key<br>strength for the Zip4j AES method,<br>either AES 128 or AES 256.<br><br><br>Enter Password: enter the<br>encryption password.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings.<br><br>This check box is available only when zip is selected from the Archive format list. With this check box selected,<br>the compressed archive file can be decompressed only by the<br>tFileUnarchive component and<br>not by a common archiver. For more information about tFileUnarchive, see [tFileUnarchive](https://help.qlik.com/talend/en-US/components/8.0/archive-unarchive/tfileunarchive). |
| ZIP64 mode | This option allows for archives with the .zip64 extension to be<br>created, with three modes available:<br><br><ul> <li> <p> <span>ASNEEDED</span>: archives                                            with the .zip64 extension will be automatically created                                            based on the file size.</p> </li> <li> <p> <span>ALWAYS</span>: archives with                                            the .zip64 extension will be created, no matter what                                            size the file may be.</p> </li> <li> <p> <span>NEVER</span>: no archives                                            with the .zip64 extension will be created, no matter                                            what size the file may be.</p> </li> </ul><br><br>Note that if the file size or the total size of the archive<br>exceeds 4GB or there are more than 65536 files inside the archive,<br>you need to set the mode to ALWAYS. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use sync flush | Select this check box to flush the compressor before flushing the<br>output stream. Clear this check box to flush only the output<br>stream.<br><br>This check box is available when gzip or tar.gz is<br>selected from the Archive format<br>list. |
| tStatCatcher Statistics | Select this check box to gather the processing metadata at the Job<br>level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ARCHIVE\_FILEPATH:<br>the path to the archive file. This is an After variable and it returns a string.<br><br><br>ARCHIVE\_FILENAME: the name of the archive file. This is an After<br>variable and it returns a string.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component must be used as a standalone component. |
| Connections | Outgoing links (from this component to another):<br><br><br>Row: Main; Reject; Iterate.<br><br><br>Trigger: On Subjob Ok; On Subjob<br>Error; Run if; On Component Ok; On Component Error.<br><br>Incoming links (from one component to this one):<br><br><br>Row: Main; Reject; Iterate.<br><br><br>Trigger: Run if; On Subjob Ok; On<br>Subjob Error; On component Ok; On Component Error; Synchronize;<br>Parallelize.<br><br>For further information regarding connections, see [Using connections in a Job](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/using-connections-in-job). |

**Related concepts**

* [Zipping files using a tFileArchive](https://help.qlik.com/talend/en-US/components/8.0/tfilearchive-zipping-files-using-tfilearchive-standard-component "This scenario creates a Job with a unique component. It aims at zipping files and recording them in the selected directory.")
