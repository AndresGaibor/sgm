# tftpput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tftpput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tftpput -->

# tFTPPut

Uploads files from a local directory to an FTP directory.

## tFTPPut Standard properties

These properties are used to configure tFTPPut running in the Standard Job framework.

The Standard tFTPPut component belongs to the Internet family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property Type | Select the way the connection details<br>will be set.<br><br><ul> <li> <p> <span>Built-In</span>: The connection details will be set                                locally for this component. You need to specify the values for all                                related connection properties manually.</p> </li> <li> <p> <span>Repository</span>: The connection details stored                                centrally in <span><span>Repository</span><abbr> &gt; </abbr><span>Metadata</span></span> will be reused by this component. </p> <p>You need to click                                the <span>[...]</span> button next to it and in the pop-up                                    <span>Repository Content</span> dialog box, select the                                connection details to be reused, and all related connection                                properties will be automatically filled in.</p> </li> </ul> |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined. |
| Host | The IP address or hostname of the FTP server. |
| Port | The listening port number of the FTP server. |
| Logon type | Select the authentication type to access the FTP server:<br><br><ul> <li><span>Password</span>: Enter the username and password used to                            access the server.</li> <li><span>Password and account</span>: Enter the username,                            password, as well as the associated user account name.</li> </ul><br><br>To enter the password, click the [...] button<br>next to the password field, enter the password in double quotes in the pop-up dialog box,<br>and click OK to save the settings. |
| Local directory | The local directory from which the files will be uploaded to the FTP<br>server. |
| Remote directory | The FTP directory where the uploaded files will be placed. |
| Transfer mode | Select the transfer mode from the list, either ascii or binary. |
| Overwrite file | Select the action to be<br>performed when the file already exists.<br><br><ul> <li> <p> <span>never</span>: Never                                overwrite the file.</p> </li> <li> <p> <span>always</span>:                                Always overwrite the file.</p> </li> <li> <p> <span>size                                    different</span> or: Overwrite the file when the file size                                is different.</p> </li> <li> <p> <span>overwrite</span>:                                Overwrite the existing file.</p> </li> <li> <p> <span>resume</span>:                                Resume downloading the file from the point of interruption.</p> </li> <li> <p> <span>append</span>: Add                                data to the end of the file without overwriting data.</p> </li> </ul><br><br><br>overwrite,<br>resume, and append are available when the SFTP Support check box is selected. |
| Append | Select this check box to append data at the end of the file<br>in order to avoid overwriting data. |
| SFTP Support | Select this check box to connect to the FTP server via an SFTP connection.<br><br>Information noteWarning: This option does not work with an HTTPS proxy. If you need an<br>HTTPS proxy, use the tSetProxy<br>component. |
| Authentication method | Select the SFTP authentication method, Public key, Password, or Public key and<br>password.<br><br><ul> <li> <p> <span>Public key</span>:                                Enter the path to the private key and the passphrase for the key in                                the <span>Private key</span> and                                    <span>Key Passphrase</span> fields                                correspondingly.</p> </li> <li> <p> <span>Password</span>:                                Enter the password required.</p> </li> <li> <span>Public key and                                password</span>: Select this option if the SFTP server requires                            both a public key and a password for authentication. In this case, you                            need to provide the <span>password</span>, the                                <span>private key file</span>, and the                                <span>key passphrase</span> in the                            corresponding fields.</li> </ul><br><br>This property is available only when the SFTP Support check box is selected. |
| Filename encoding | Select this check box to set the encoding used to convert<br>file names from Strings to bytes. It should be the same encoding used on the<br>SFTP server. If the SFTP server's version is greater than 3, the encoding<br>should be UTF-8, or else an error<br>occurs.<br><br>This property is<br>available only when the SFTP Support<br>check box is selected. |
| FTPS Support | Select this check box to connect to the FTP server via an FTPS connection.<br><br>If you are using an HTTP proxy, via a tSetProxy component for example,<br>you need to select this check box and set the connection mode to<br>Passive.<br><br>Information noteNote: If your FTPS server requires session resumption<br>between data and control connections, the tFTP components support this<br>only when the TLS version is set to TLSv1.2 and the following Java 17<br>JVM properties are configured:<br><br>```<br>-Djdk.tls.client.protocols=TLSv1.2<br>-Djdk.tls.allowLegacyResumption=true<br>-Djdk.tls.useExtendedMasterSecret=false<br>-Djdk.tls.client.enableSessionTicketExtension=false<br>```<br><br>This<br>configuration is necessary to allow Java 17 to work with session<br>resumption for FTPS connections. |
| Keystore File | The path to your keystore file, a password protected file<br>containing several keys and certificates.<br><br>Depending on the FTPS server configuration, an FTPS server<br>private key or a client certificate is needed to establish an FTPS<br>connection. You can store the FTP server private key or your client<br>certificate in the keystore file.<br><br>This property is<br>available only when the FTPS Support<br>check box is selected. |
| Keystore Password | The password for your keystore file.<br><br>This property is<br>available only when the FTPS Support<br>check box is selected. |
| Security Mode | Select the security mode from the list, either Implicit or Explicit.<br><br>This property is<br>available only when the FTPS Support<br>check box is selected. |
| Use Perl5 Regex Expression as Filemask | Select this check box to use Perl5 regular expressions in<br>the or Files field as file filters.<br>This is useful when the name of the file to be processed contains special<br>characters such as parentheses.<br><br>For more information about Perl5 regular expression syntax,<br>see [Perl5 Regular Expression<br>Syntax](http://perldoc.perl.org/perlre.html#Regular-Expressions). |
| Use Perl5 Regex Expression as Filemask | Select this check box to use Perl5 regular expressions in<br>the or Files field as file filters.<br>This is useful when the name of the file to be processed contains special<br>characters such as parentheses.<br><br>For more information about Perl5 regular expression syntax,<br>see [Perl5 Regular Expression<br>Syntax](http://perldoc.perl.org/perlre.html#Regular-Expressions). |
| Files | Specify the files to be uploaded.<br><br><ul> <li> <p> <span>Filemask</span>: the file names or the                           path to the files to be uploaded.</p> </li> <li> <p> <span>New name</span>: the name to give the                           file after the transfer.</p> </li> </ul><br><br>You can specify multiple files in a line by using<br>wildcards or a regular expression. |
| Connection mode | Select the connection mode from the list, either Passive or Active. |
| Encoding | Specify the encoding type by selecting an encoding type from<br>the list or selecting CUSTOM and<br>enter the encoding type manually. |
| Die on error | Select the checkbox to stop the execution of the Job when an error occurs.<br><br>Clear the checkbox to skip any error and continue the Job execution process. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use Socks Proxy | Select this check box if you are using a proxy, and in the<br>Proxy host, Proxy port, Proxy<br>user and Proxy<br>password fields displayed, specify the proxy server settings<br>information. |
| Ignore Failure At Quit (FTP) | Select this check box to ignore library closing errors or<br>FTP closing errors. |
| Connection timeout | Specify the timeout value (in ms) for the connection. A<br>value of 0 or any negative values will be ignored. In this case, the default<br>value (that is, 60000ms) will be used. |
| Data Channel Protection Level | The data channel protection level with which data is<br>transferred between the client and the server. For more information, see<br>[RFC 2228: FTP Security<br>Extensions](https://www.rfc-editor.org/rfc/rfc2228.txt).<br><br>This<br>property is available only when the FTPS<br>Support check box is selected. |
| Protection Buffer Size | The maximum size (in bytes) of the encoded data blocks to be<br>transferred between the client and the server. For more information, see<br>[RFC 2228: FTP Security<br>Extensions](https://www.rfc-editor.org/rfc/rfc2228.txt).<br><br>This<br>property is available only when the FTPS<br>Support check box is selected. |
| Enable Remote Verification | Select this option to enable remote verification. This option solves FTPS server architecture<br>compatibility issues. See [setRemoteVerificationEnabled](https://commons.apache.org/proper/commons-net/apidocs/org/apache/commons/net/ftp/FTPClient.html#setRemoteVerificationEnabled-boolean-) for<br>related information.<br><br>This option is available when FTPS Support is selected in<br>the Basic settings view. |
| Use strict reply parsing | Select this option to use strict reply parsing. |
| Config client | Select this option to set JSch encryption algorithm properties. To set an encryption algorithm<br>property, add a row in the table that appears by clicking the plus button on<br>the bottom of the table and enter property name and property value in the<br>Client parameter and Value<br>columns. See [Fork of JSch-0.1.55](https://github.com/mwiede/jsch) and the<br>*setConfig* section at [Class JSch](http://epaul.github.io/jsch-documentation/javadoc/) for related information.<br><br>This option is available when the Use an existing connection<br>option is not selected and the SFTP Support option is<br>selected in the Basic settings view.<br><br>Information noteNote: This option is available only when you have installed the 8.0.1-R2022-07<br>Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. |
| NB\_FILE | The number of the files processed. This is an After variable<br>and it returns an integer. |
| CURRENT\_STATUS | The execution result of the component. This is a Flow<br>variable and it returns a string. |
| CURRENT\_FILE\_EXISTS | The result of whether the current file exists. This is a Flow<br>variable and it returns a boolean. |
| TRANSFER\_MESSAGES | The file transferred information. This is an After variable<br>and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is typically used as a single-component subJob but can also<br>be used as output component. |

**Related concepts**

* [Putting files onto an FTP server](https://help.qlik.com/talend/en-US/components/8.0/tftpconnection-tftpput-tftpclose-putting-files-onto-ftp-server-standard-component "Here is an example of using Talend FTP components to put several files in a local directory onto an FTP server.")
