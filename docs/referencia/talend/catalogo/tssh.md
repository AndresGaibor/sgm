# tssh

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tssh  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tssh -->

# tSSH

Establishes a communication with distant server and returns securely sensible information.

Returns data from a remote computer, based on the secure shell command defined.

## tSSH Standard properties

These properties are used to configure tSSH running in the Standard Job framework.

The Standard tSSH component belongs to the System family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit Schema | A schema is a row description, it defines the number of fields to be<br>processed and passed on to the next component. The schema is either Built-in or stored remotely in the Repository.<br><br><ul> <li> <span>Built-in</span>: You create and store the                        schema locally for this component only. For more information about a                        component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</li> <li> <span>Repository</span>: You have already created                        the schema and stored it in the Repository. You can reuse it in various                        projects and Job flowcharts. For more information about a component schema                        in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</li> </ul><br><br>Click Edit<br>schema to make changes to the schema. If the current schema is of the Repository type, three options are available:<br><br><ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> |
| Host | Enter the IP address of the SSH server. |
| Port | Enter the listening port number of the SSH server. |
| User | Enter the username used to authenticate to the SSH server. |
| Authentication method | Select the authentication method to be used: Public<br>key, Password, or<br>Keyboard Interactive.<br><br><ul> <li> <p> <span>Public key</span>: Enter the path to the private                                    key and the passphrase for the key in the <span>Private                                        key</span> and <span>Key Passphrase</span>                                    fields correspondingly. To enter the passphrase, click the                                        <span>[...]</span> button next to the                                        <span>Key Passphrase</span> field, enter the                                    passphrase between double quotes in the pop-up dialog box, and                                    click <span>OK</span> to save the settings.</p> </li> <li> <p> <span>Password</span>: Enter the password required. To                                    enter the password, click the <span>[...]</span> button next to the                                        <span>Password</span> field, enter the password in                                    double quotes in the pop-up dialog box, and click <span>OK</span> to save the settings.</p> </li> <li> <span>Keyboard Interactive</span>: Enter the required                                password in the <span>Password</span> field. To enter the                                password, click the <span>[...]</span> button next to the                                    <span>Password</span> field, enter the password in                                double quotes in the pop-up dialog box, and click                                    <span>OK</span> to save the settings.</li> </ul> |
| Pseudo terminal | Select this check box to call the<br>interactive shell that performs the terminal operations. |
| Command separator | Type in the command separator required.<br>Once the Pseudo<br>terminal check box is selected, this field becomes<br>unavailable. |
| Commands | Type in the command for the relevant<br>information to be returned from the remote computer. When you select the<br>Pseudo<br>terminal check box, this table becomes a terminal<br>emulator and each row in this table is a single command. |
| Use timeout/timeout in seconds | Define the timeout time period. A<br>timeout message will be generated if the actual response time exceeds<br>this expected processing time. |
| Standard Output | Select the destination to which the<br>standard output is returned. The output may be returned to:<br><br>- to console: the output is displayed in<br>the console of the Run view.<br><br>- to global variable: the output is<br>indicated by the corresponding global variable.<br><br>- both to console and global variable:<br>the output is indicated both of the two means.<br><br>- normal: the output is a standard ssh<br>output. |
| Error Output | Select the destination to which the<br>error output is returned. The output may be returned to:<br><br>- to console: the<br>output is displayed in the console of the Run view.<br><br>- to global variable: the output is<br>indicated by the corresponding global variable.<br><br>- both to console and global variable:<br>the output is indicated both of the two means.<br><br>- normal: the output is a standard ssh<br>output. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use session heartbeat | Enable this option to send a heartbeat message (specifically,<br>'SSH\_MSG\_IGNORE') at regular intervals during the SSH<br>session. This helps keep the session active by preventing timeouts. Specify the<br>interval (in seconds) in the **Heartbeat interval** field. The default value<br>is **1800 seconds** (30 minutes). |
| tStatCatcher Statistics | Select this check box to gather the processing metadata at the Job level as<br>well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>STDOUT: the standard execution<br>output of the remote command. This is an After variable and it returns a string.<br><br><br>STDERR:<br>the error execution output of the remote command. This is an After variable and it<br>returns a string.<br><br><br>EXIT\_CODE: the exit code of the remote command. This is<br>an After variable and it returns an integer.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component can be used as standalone<br>component.<br><br>Note that for some sensitive information<br>such as password and username, you can define the context variables in<br>the Context view<br>and press Ctrl +<br>Space to access them.<br><br>Information noteNote: The data returned by this component may be large in size. Allocate<br>more memory space if the Job takes extra long time to complete. You can<br>set memory space for a Job in the Advanced<br>settings view of the Run tab. |
| Connections | Outgoing links (from this component to<br>another):<br><br><br>Row: Main<br><br><br>Trigger: Run if;<br>On Component Ok; On Component Error; On Subjob Ok; On Subjob Error.<br><br>Incoming links (from one component to<br>this one):<br><br><br>Row: Main;<br>Iterate<br><br><br>Trigger: Run if;<br>On Component Ok; On Component Error; On Subjob Ok; On Subjob Error.<br><br>For further information regarding<br>connections, see [Using connections in a Job](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/using-connections-in-job). |
| Limitation | The component use is optimized for<br>Unix-like systems. |

**Related concepts**

* [Displaying remote system information via SSH](https://help.qlik.com/talend/en-US/components/8.0/tssh-displaying-remote-system-information-via-ssh-standard-component "The following use case describes a basic Job that uses SSH command to display the hostname of the distant server being connected to, and the current date on this remote system.")
