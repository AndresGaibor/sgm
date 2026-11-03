# tboxput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tboxput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tboxput -->

# tBoxPut (deprecated)

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

Uploads files to a Box account.

This component uploads data to Box from either a local file or a given data flow.

## tBoxPut Standard properties

Information noteDeprecation: This component is deprecated since Talend Studio 8.0 R2025-11 and removed from Talend Studio 8.0 R2026-09 onwards. Talend recommends you to migrate your Jobs to use the Box v2 components.

These properties are used to configure tBoxPut running in the Standard Job framework.

The Standard tBoxPut component belongs to the Cloud family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Use existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined. |
| Connection/Client Key | Enter the client key required by Box to access the Box API. To obtain the client key and<br>client secret you need to create an account at https://developers.box.com/ and then create a Box App under the Box account to<br>be used. The client key and client secret can be obtained from the account application<br>settings. |
| Connection/Client Secret | Enter the client secret required by Box to access the Box API. To obtain the client key and<br>client secret you need to create an account at https://developers.box.com/ and then create a Box App under the Box account to<br>be used. The client key and client secret can be obtained from the account application<br>settings. |
| Connection/Access Token | Enter the access token required by Box to access a Box account and operate it. For how to get<br>the access token and refresh token, check the Box documentation you can access from https://developers.box.com/. |
| Connection/Refresh Token | Enter the refresh token required by Box to refresh the access token automatically. For how to<br>get the access token and refresh token, check the Box documentation you can access from<br>https://developers.box.com/. |
| Connection/Use HTTP proxy | If you are using a proxy, select this check box and enter the host and port information of<br>that proxy in the corresponding fields that are displayed. |
| Remote Path | Enter the path pointing to the file you need to write contents in. This file will be<br>created on the fly if it does not exist. |
| Replace if Existing | Select this check box to use the uploaded file to replace the<br>existing one. |
| Upload mode | Select the upload mode to be used:<br><br><ul> <li> <p> <span>Upload incoming content as file</span>: Select this radio											button to read data directly from the input flow of the											preceding component and write the data into the file											specified in the <span>Remote												Path</span> field.</p> </li> <li> <p> <span>Upload local file</span>: Select this radio button to											upload a locally stored file to Box. In the <span>File</span> field that is displayed,											you need to enter the path or browse to this											file.</p> </li> <li> <p> <span>Expose as OutputStream</span>: Select this check box to											expose the output stream of this component, which can be											used by the other components to write the file content.											For example, you can use the <span>Use												output stream</span> feature of the <span>tFileOutputDelimited</span>											component to feed a given <span>tBoxPut</span>'s exposed output stream. For											further information, see <a href="https://help.qlik.com/talend/en-US/components/8.0/delimited/tfileoutputdelimited" target="_blank">tFileOutputDelimited</a>.</p> </li> </ul> |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br>Note that the schema of this component is read-only with a single<br>column named content and it<br>receives data from the *content*<br>column of its input schema only. This means that you must use a<br>*content* column in the input<br>data flow to carry the data to be uploaded. This type of column is<br>typically provided by the tFileInputRaw component. For further information,<br>see [tFileInputRaw](https://help.qlik.com/talend/en-US/components/8.0/raw/tfileinputraw).<br><br>The Schema field is not available when you have<br>selected the Expose as OutputStream<br>or the Upload local file upload<br>mode. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to collect log data at the component<br>level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is used either standalone in a subJob to directly upload a local file to<br>Box or as an end component of a Job flow to upload given data being<br>handled in this flow. |

**Related concepts**

* [Uploading and downloading files from Box](https://help.qlik.com/talend/en-US/components/8.0/tboxconnection-tboxput-tboxget-uploading-and-downloading-files-from-box-standard-component-in-this)
