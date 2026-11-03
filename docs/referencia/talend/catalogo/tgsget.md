# tgsget

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tgsget  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tgsget -->

# tGSGet

Retrieves objects which match the specified criteria from Google Cloud Storage and outputs them to a local directory.

## tGSGet Standard properties

These properties are used to configure tGSGet running in the Standard Job framework.

The Standard tGSGet component belongs to the Big Data and the Cloud families.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Use an existing connection | Select this check box and in the Component List click the<br>relevant connection component to reuse the connection details you<br>already defined. |
| Credential type | Select the mode to be used to authenticate to your project.<br><br><ul> <li><span>Service account</span>: authenticate using a Google account                     that is associated with your Google Cloud Platform project. When selecting this                     mode, the access key must be provided in the <span>Service account                        key</span> field.</li> <li><span>Workload Identity Federation</span>: authenticate using an                     external identity provider, such as AWS, Azure, or OIDC, without needing a                     service account key. When selecting this mode, the identity federation                     configuration must be provided in the <span>Client library configuration                        file</span> field.</li> <li><span>Application Default Credentials</span>: authenticate using the                     Application Default Credentials. When selecting this mode, no additional                     parameters need to be defined as credentials are automatically found based on                     the application environment.</li> <li> <span>OAuth Access Token</span>: authenticate using an OAuth access                     token. When selecting this mode, the token must be provided in the                        <span>OAuth Access Token</span> field. </li> </ul><br><br>To know more about the Google Cloud authentication process, read [the Google Cloud documentation](https://cloud.google.com/docs/authentication/). |
| Service account key | Click the [...] button next to the service account key<br>field to browse for the JSON file that contains your service account key.<br><br>This property is only available when you authenticate using Service<br>account. |
| OAuth Access Token | Enter an access token.<br><br>The lifetime of the token is one hour. The component<br>does not perform the token refresh operation but will fetch the new access token<br>to operate beyond the one-hour limit.<br><br><br>This property is only available when you<br>authenticate using OAuth Access Token. |
| Key prefix | Specify the prefix to download only<br>objects which keys begin with the specified prefix. |
| Delimiter | Specify the delimiter in order to download<br>only those objects with key names up to the delimiter. |
| Specify project ID | When the credential type is set to OAuth Access<br>Token, select this check box and in the Project ID field enter the project ID from which<br>you want to obtain objects. |
| Use keys | Select this check box and complete the<br>Keys table to<br>define the criteria for objects to be downloaded from Google Cloud<br>Storage.<br><br><ul> <li> <p> <span>Bucket name</span>: type in the name                                    of the bucket from which you want to download objects.</p> </li> <li> <p> <span>Key</span>: type in the key of the                                    object to be downloaded.</p> </li> <li> <p> <span>New name</span>: type in a new name                                    for the object to be downloaded.</p> </li> </ul><br><br>If you select the Use keys check box, the<br>Key prefix<br>and Delimiter<br>fields as well as the Specify<br>project ID check box and the Get files from bucket list check box<br>will not be available. |
| Get files from bucket list | Select this check box and complete the<br>Bucket table<br>to define the criteria for objects to be downloaded from Google Cloud<br>Storage.<br><br><ul> <li> <p> <span>Bucket name</span>: type in the name of                                    the bucket from which you want to download objects.</p> </li> <li> <p> <span>Key prefix</span>: type in the prefix                                    to download objects whose keys start with the specified prefix                                    from the specified bucket.</p> </li> <li> <p> <span>Delimiter</span>: specify the delimiter                                    to download those objects with key names up to the delimiter                                    from the specified bucket.</p> </li> </ul><br><br>If you select the Get files from bucket<br>list check box, the Key prefix and Delimiter fields as well as the<br>Specify project<br>ID check box and the Use keys check box will not be<br>available. |
| Output directory | Specify the directory where you want to<br>store the downloaded objects. |
| Die on error | This check box is cleared by default,<br>meaning to skip the row on error and to complete the process for<br>error-free rows. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use a custom endpoint | Select this check box to use a private endpoint rather than the default one.<br><br>When selected, enter the URL in the Google Storage Private API<br>URL property, by respecting the following format:<br>"https://storage.goggleapis.com".<br><br>For more information,<br>see [Access Google APIs through endpoints](https://cloud.google.com/vpc/docs/configure-private-service-connect-apis) from<br>Google documentation.<br><br>This property is only available when you authenticate<br>using Service account and Application Default<br>Credentials. |
| tStatCatcher Statistics | Select this check box to gather the Job processing metadata at the Job level as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| Global Variables | NB\_LINE: the number<br>of rows read by an input component or transferred to an output component. This is an<br>After variable and it returns an integer.<br><br><br>ERROR\_MESSAGE: the error message generated by the<br>component when an error occurs. This is an After variable and it returns a string. This<br>variable functions only if the Die on error checkbox is<br>cleared, if the component has this checkbox.<br><br>A Flow variable functions during the execution of a component<br>while an After variable functions after the execution of the component.<br><br>To fill up a field or expression with a variable, press Ctrl+Space to access the variable list and choose the variable to use from<br>it.<br><br>For more information about variables, see [Using contexts and variables](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/contexts-and-variables). |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component is usually used together with other Google Cloud Storage components, particularly tGSPut. |
