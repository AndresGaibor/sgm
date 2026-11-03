# tgsput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tgsput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tgsput -->

# tGSPut

Uploads files from a local directory to Google Cloud Storage so that you can manage them with Google Cloud Storage.

## tGSPut Standard properties

These properties are used to configure tGSPut running in the Standard Job framework.

The Standard tGSPut component belongs to the Big Data and the Cloud families.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Use an existing connection | Select this check box and in the Component List click the<br>relevant connection component to reuse the connection details you<br>already defined. |
| Credential type | Select the mode to be used to authenticate to your project.<br><br><ul> <li><span>Service account</span>: authenticate using a Google account                     that is associated with your Google Cloud Platform project. When selecting this                     mode, the access key must be provided in the <span>Service account                        key</span> field.</li> <li><span>Workload Identity Federation</span>: authenticate using an                     external identity provider, such as AWS, Azure, or OIDC, without needing a                     service account key. When selecting this mode, the identity federation                     configuration must be provided in the <span>Client library configuration                        file</span> field.</li> <li><span>Application Default Credentials</span>: authenticate using the                     Application Default Credentials. When selecting this mode, no additional                     parameters need to be defined as credentials are automatically found based on                     the application environment.</li> <li> <span>OAuth Access Token</span>: authenticate using an OAuth access                     token. When selecting this mode, the token must be provided in the                        <span>OAuth Access Token</span> field. </li> </ul><br><br>To know more about the Google Cloud authentication process, read [the Google Cloud documentation](https://cloud.google.com/docs/authentication/). |
| Service account key | Click the [...] button next to the service account key<br>field to browse for the JSON file that contains your service account key.<br><br>This property is only available when you authenticate using Service<br>account. |
| OAuth Access Token | Enter an access token.<br><br>The lifetime of the token is one hour. The component<br>does not perform the token refresh operation but will fetch the new access token<br>to operate beyond the one-hour limit.<br><br><br>This property is only available when you<br>authenticate using OAuth Access Token. |
| Bucket name | Type in the name of the bucket into which<br>you want to upload files. |
| Project ID | When the credential type is set to OAuth Access Token, specify the project ID<br>into which you want to upload files. |
| Local directory or file | Type in the full path of or browse to the local file or<br>directory where the files to be uploaded are located.<br><br>If you select the Use files list check box, you can only<br>specify a directory in this field.<br><br>If you unselect the Use files list check box, you can<br>specify a file or directory in this field. |
| Google Storage directory | Type in the Google Storage directory to<br>which you want to upload files. |
| Use files list | Select this check box and complete the Files table with the files to be uploaded.<br><br><ul> <li> <p> <span>Filemask</span>: enter the                           pattern used to match the file or files you want to upload. </p> <p>If you enter part of a file name, you can use the "*" character to                           replace any number of characters in the file name. </p> <p>For example, <span>sales_*.csv</span> would look for both                           <span>sales_112023.csv</span> and                           <span>sales_122023.csv</span> </p> </li> <li> <p> <span>New name</span>: enter a                           new name for the file to be uploaded.</p> </li> </ul> |
| Die on error | This check box is cleared by default,<br>meaning to skip the row on error and to complete the process for<br>error-free rows. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use a custom endpoint | Select this check box to use a private endpoint rather than the default one.<br><br>When selected, enter the URL in the Google Storage Private API<br>URL property, by respecting the following format:<br>"https://storage.goggleapis.com".<br><br>For more information,<br>see [Access Google APIs through endpoints](https://cloud.google.com/vpc/docs/configure-private-service-connect-apis) from<br>Google documentation.<br><br>This property is only available when you authenticate<br>using Service account and Application Default<br>Credentials. |
| Part size(Mb) | Specify the part size (in MB) when uploading an object in parts. The property<br>work as follows:<br><br><ul> <li> <p>If the value is 0, the object is uploaded without being divided into                              parts. </p> </li> <li> <p>If the value is bigger than 0, the object that is bigger than the part                              size is uploaded in parts.</p> </li> <li> <p>If the value is bigger than 0, the object that is smaller is uploaded                              without being divided into parts.</p> </li> </ul><br><br>The file should not be larger than 2147483647 bytes when the value is 0.<br><br>This option is available with all credential types. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at the Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component can be used together with other components, particularly the tGSGet component. |

**Related concepts**

* [Managing files with Google Cloud Storage](https://help.qlik.com/talend/en-US/components/8.0/tgscopy-tgslist-tlogrow-managing-files-with-google-cloud-storage-standard-component-the)
