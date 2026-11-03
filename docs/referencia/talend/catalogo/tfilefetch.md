# tfilefetch

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tfilefetch  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tfilefetch -->

# tFileFetch

Availability-note[Deprecated](https://help.talend.com/r/en-US/Cloud/labels-on-talend-help-center/availability-deprecated)

This content is deprecated.

Information noteImportant: This component has been removed from Talend Studio 8.0 R2025-04 onwards. Use tHTTPClient instead.

Retrieves a file through the given protocol (HTTP, HTTPS, FTP, or SMB).

## tFileFetch Standard properties

These properties are used to configure tFileFetch running in the Standard Job framework.

The Standard tFileFetch component belongs to the Internet family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Protocol | Select the protocol<br>you want to use from the list and fill in the corresponding fields:<br>http, https, ftp,<br>smb.<br><br>The properties<br>differ slightly depending on the type of protocol selected. The<br>additional fields are defined in this table, after the basic settings.<br><br>Information noteDeprecation: The support for SMBv1 (the smb<br>option) is deprecated. |
| URI | Type in the URI of<br>the site from which the file is to be fetched. |
| Use cache to save<br>resource | Select this check<br>box to save the data in the cache.<br><br>This option allows you to process the file data flow (in streaming<br>mode) without saving it on your drive. This is faster and improves<br>performance. |
| Domain | Enter the Microsoft<br>server domain name.<br><br>Available for<br>the smb<br>protocol. |
| Username and<br>Password | Enter the<br>authentication information required to access the server.<br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings.<br><br>Available for the smb protocol. |
| Destination<br>Directory | Browse to the<br>destination folder where the file fetched is to be placed.<br><br>Information noteWarning: Use absolute path (instead of relative path) for<br>this field to avoid possible errors. |
| Destination<br>Filename | Enter a new name for<br>the file fetched.<br><br>If the Upload file option in the Advanced settings view is selected, the<br>upload response will be saved in this file.<br><br>Information noteWarning: Use absolute path (instead of relative path) for<br>this field to avoid possible errors. |
| Create full path according to<br>URI | It allows you to<br>reproduce the URI directory path. To save the file at the root of your<br>destination directory, clear the check box.<br><br>Available for the http, https and ftp protocols. |
| Add header | Select this check<br>box if you want to add one or more HTTP request headers as fetch<br>conditions. In the Headers table, enter the name(s) of the HTTP header<br>parameter(s) in the Name field and the corresponding value(s) in the<br>Value<br>field.<br><br>Available for the<br>http and<br>https<br>protocols. |
| POST<br>method | This check box is<br>selected by default. It allows you to use the POST method. In the<br>Parameters<br>table, enter the name of the variable(s) in the Name field and the<br>corresponding value in the Value field.<br><br>Clear the check box if you want to use the GET method.<br><br>Available for the http and https<br>protocols. |
| Die on<br>error | Clear this check box<br>to skip the rows in error and to complete the process for the error free<br>rows<br><br>Available for the http, https and ftp<br>protocols. |
| Read<br>Cookie | Select this check<br>box for tFileFetch to load a web authentication cookie.<br><br>Available for the http, https, ftp and smb<br>protocols. |
| Save<br>Cookie | Select this check<br>box to save the web page authentication cookie. This means you will not<br>have to log on to the same web site in the future.<br><br>Available for the http, https, ftp and smb protocols. |
| Cookie<br>file | Type in the full<br>path to the file which you want to use to save the cookie or click<br>[...] and<br>browse to the desired file to save the cookie.<br><br>Available for the http, https, ftp and smb protocols. |
| Cookie<br>policy | Choose a cookie<br>policy from this drop-down list. Four options are available, BROWSER\_COMPATIBILITY,<br>DEFAULT,<br>NETSCAPE and<br>RFC\_2109.<br><br>Available for the http, https, ftp and smb<br>protocols. |
| Single cookie<br>header | Check this box to<br>put all cookies into one request header for maximum compatibility among<br>different servers.<br><br>Available for<br>the http,<br>https,<br>ftp and<br>smb<br>protocols. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher<br>Statistics | Select this check<br>box to collect the log data at each component level. |
| Timeout | Enter the number<br>of milliseconds after which the protocol connection should close.<br><br>Available for the http and https<br>protocols. |
| Encoding for parameters | Select the character encoding for<br>the POST method parameters: US-ASCII, UTF-8, or Windows-1252.<br><br>This option is<br>available when POST method is<br>selected in the Basic settings<br>view. |
| Print response to<br>console | Select this check<br>box to print the server response in the console.<br><br>Available for the http and https protocols. |
| Upload<br>file | Select this check<br>box to upload one or more files to the server. For each file to be<br>uploaded, click the [+] button beneath the table displayed and set the<br>following fields:<br><br><ul> <li> <p> <span>Name</span>: the value of the <span>name</span> attribute of the &lt;input type="file"&gt;                                    field in the original HTML form.</p> </li> <li> <p> <span>File</span>: the full path of the file to upload, e.g.                                        <kbd>"D:/filefetch.txt"</kbd>.</p> </li> <li> <p> <span>Content-Type</span>: the content type of the file to                                    upload. The default value is <kbd>"application/octet-stream"</kbd>.</p> </li> <li> <p> <span>Charset</span>: the character set of the file to                                    upload. The default value is <kbd>"ISO-8859-1"</kbd>.</p> </li> </ul><br><br>This option is available for the http and https<br>protocols, with the POST method option in the<br>Basic settings view selected.<br><br>With this option selected, the<br>upload response will be saved in the file specified in the Destination filename field in the<br>Basic settings<br>view. |
| Enable proxy<br>server | Select this check<br>box if you are connecting via a proxy and complete the fields which<br>follow with the relevant information.<br><br>Available for the http, https and ftp protocols. |
| Enable NTLM<br>Credentials | Select this check<br>box if you are using an NTLM authentication protocol.<br><br><br>Domain: The client domain name.<br><br><br>Host: The client's IP address.<br><br>Available for the http and https<br>protocols. |
| Need<br>authentication | Select this check<br>box and enter the username and password in the relevant fields, if they<br>are required to access the protocol.<br><br>Available for the http and https protocols. |
| Support<br>redirection | Select this check<br>box to repeat the redirection request until redirection is successful<br>and the file can be retrieved.<br><br><br>Force Get method for 302 redirection:<br>Select this check box to send the redirection request with the Get<br>method if the redirection code is 302.<br><br>Available for the http, https and ftp protocols. |
| Trust<br>all servers | Select this option to trust any<br>servers. With this option selected, the component does not validate the<br>server certificates. Not selected by default.<br><br>This option is available when https is selected from the Protocol drop-down list in the Basic settings view. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global<br>Variables | ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br><br>INPUT\_STREAM: the content of the file<br>being fetched. This is a Flow variable and it returns an InputStream.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage<br>rule** | This component is<br>generally used as a start component to feed the input flow of a Job and<br>is often connected to the Job using an OnSubjobOk or OnComponentOk link,<br>depending on the context. |
| Limitation | Due to license incompatibility, one or more JARs required to use this component<br>are not provided. You can install the missing JARs for this particular component by<br>clicking the Install button on the Component tab view. You can also find out and add all missing<br>JARs easily on the Modules tab in the Integration perspective of Talend Studio. For<br>details, see [Installing external modules](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/installing-external-modules). |

**Related concepts**

* [Fetching data through HTTP](https://help.qlik.com/talend/en-US/components/8.0/tfilefetch-tfileinputdelimited-tlogrow-tlogrow-fetching-data-through-http-standard-component-this)
* [Reusing stored cookie to fetch files through HTTP](https://help.qlik.com/talend/en-US/components/8.0/tfilefetch-reusing-stored-cookie-to-fetch-files-through-http-standard-component-this)
