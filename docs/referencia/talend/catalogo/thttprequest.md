# thttprequest

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/thttprequest  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/thttprequest -->

# tHttpRequest

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

Information noteImportant: This component has been removed from Talend Studio 8.0 R2025-04 onwards. Use tHTTPClient instead.

Sends an HTTP request to the server and outputs the response information locally.

tHttpRequest sends an HTTP request to the server end and gets the corresponding response information from the server end.

## tHttpRequest Standard properties

These properties are used to configure tHttpRequest running in the Standard Job framework.

The Standard tHttpRequest component belongs to the Internet family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit Schema | <ul> <li> <p>A schema is a row description, it defines the number of fields to be							processed and passed on to the next component. The schema is either								<span>Built-in</span> or stored remotely in the								<span>Repository</span>.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-in</span>: You create and store the							schema locally for this component only. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> <li> <p> <span>Repository</span>: You have already created							the schema and stored it in the <span>Repository</span>. You can reuse it in various projects and Job							designs. For more information about a component schema in its <span>Basic settings</span> tab, see <a href="https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/basic-settings-tab" target="_blank">Basic settings tab</a>.</p> </li> </ul> |
| Sync columns | Click this button to retrieve the schema from the preceding<br>component. |
| URI | Type in the Uniform Resource Identifier (URI) that identifies the data<br>resource on the server. A URI is similar to a URL, but more<br>general. |
| Method | Select an HTTP method to define the action to be performed:<br><br><br>Post: Sends data (for example HTML form<br>data) to the server end.<br><br><br>Get: Retrieves data from the server<br>end. |
| Post parameters from file | Browse to, or enter the path to the file that is used to provide<br>parameters (request body) to the POST method. |
| Write response content to file | Select this check box to save the HTTP response to a local file. You<br>can either type in the file path in the input field or click the<br>[...] button to browse to the file path. |
| Create directory if not exists | Select this check box to create the directory defined in the Write response content to file field if it<br>does not exist.<br><br>This check box appears only when the Write<br>response content to file check box is selected and is<br>cleared by default. |
| Headers | Type in the name-value pair(s) for HTTP headers to define the<br>parameters of the requested HTTP operation.<br><br><br>Key: Fill in the name of the header<br>field of an HTTP header.<br><br><br>Value: Fill in the content of the<br>header field of an HTTP header.<br><br>The following<br>gives an example for a Basic authentication<br>implementation.<br><br><ul> <li> <span>Key</span>: <kbd>Authentication</kbd> </li> <li> <span>Value</span>: <kbd>"Basic                           "+java.util.Base64.getEncoder().encodeToString("{your_username}:{your_password}".getBytes())</kbd> </li> </ul><br><br>For more information about definition of HTTP headers, please refer<br>to:<br><br><br>http://en.wikipedia.org/wiki/List\_of\_HTTP\_headers. |
| Need authentication | Select this check box to fill in a user name and a password in the<br>corresponding fields if authentication is needed:<br><br><br>user: Fill in the user name for the<br>authentication.<br><br><br>password: Fill in the password for the<br>authentication.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings.<br><br>Information noteNote: This component supports all the authentication schemas described in [Http Authentication](https://docs.oracle.com/javase/7/docs/technotes/guides/net/http-auth.html). If an<br>authentication schema that requires user and password is enabled on the server<br>side (for example, HTTP Digest authentication,<br>NTLM, HTTP Negotiate (SPNEGO), or<br>Kerberos 5), you need to select this option and provide<br>username and password in the corresponding fields. |
| Die on error | Select the checkbox to stop the execution of the Job when an error<br>occurs.<br><br>Clear the checkbox to skip any rows on error and complete the<br>process for error-free rows. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Set timeout | Select this check box to specify the connect and read timeout values<br>in the following two fields:<br><br><ul> <li> <p> <span>Connect timeout(s)</span>: Enter										the connect timeout value in seconds. An exception will										occur if the timeout expires before the connection can be										established. The value of <em>0</em> indicates an infinite time out. By										default, the connect timeout value is <em>30</em>.</p> </li> <li> <p> <span>Read timeout(s)</span>: Enter										the read timeout value in seconds. An exception will occur										if the timeout expires before there is data available for										read. By default, the read timeout value is <em>0</em>, which indicates an infinite										time out.</p> </li> </ul> |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at a Job<br>level and at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>CONNECTED: the result of whether a connection to the<br>server established. This is an After variable and it returns a Boolean.<br><br><br>RESPONSE\_CODE: the response code returned by the remote HTTP server.<br>This is an After variable and it returns an integer.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component can be used in sending HTTP requests to server and<br>saving the response information. This component can be used as a<br>standalone component. |

**Related concepts**

* [Sending a HTTP request to the server and saving the response information to a local file](https://help.qlik.com/talend/en-US/components/8.0/thttprequest-tlogrow-sending-http-request-to-server-and-saving-response-information-to-local-file-standard-component-this)
