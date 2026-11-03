# tbigquerysqlrow

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tbigquerysqlrow  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tbigquerysqlrow -->

# tBigQuerySQLRow

Connects to Google BigQuery and performs queries to select data from tables row by row or create or delete tables in Google BigQuery.

## tBigQuerySQLRow Standard properties

These properties are used to configure tBigQuerySQLRow running in the Standard Job framework.

The Standard tBigQueryInput component belongs to the Big Data family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Schema and Edit Schema | <ul> <li> <p>A schema is a row description. It defines the number of fields            (columns) to be processed and passed on to the next component. When you create a Spark            Job, avoid the reserved word <kbd>line</kbd> when naming the            fields.</p> <p>Click <span>Edit        schema</span> to make changes to the schema. If the current schema is of the <span>Repository</span> type, three options are available:</p> <ul> <li> <p> <span>View schema</span>: choose this                option to view the schema only.</p> </li> <li> <p> <span>Change to built-in property</span>:                choose this option to change the schema to <span>Built-in</span> for local changes.</p> </li> <li> <p> <span>Update repository connection</span>:                choose this option to change the schema stored in the repository and decide whether                to propagate the changes to all the Jobs upon completion.</p> <p>If you just want to                propagate the changes to the current Job, you can select <span>No</span> upon completion and choose this schema metadata                again in the <span>Repository Content</span>                window.</p> </li> </ul> </li> <li> <p> <span>Built-In</span>: You create and store the schema locally for this component                only.</p> </li> <li> <p> <span>Repository</span>: You have already created the schema and stored it in the                Repository. You can reuse it in various projects and Job designs.</p> </li> </ul> |
| Authentication mode | Select the mode to be used to authenticate to your project.<br><br><ul> <li><span>Service account</span>: authenticate using a Google account                        that is associated with your Google Cloud Platform project. When selecting                        this mode, the credentials must be provided in the <span>Service                           account credentials file</span> field.</li> <li><span>Workload Identity Federation</span>: authenticate                        through a Google Workload Identity Pool, allowing integration with identity providers such as                        AWS, Azure, or OIDC, without needing a service account key. When selecting                        this mode, the identity federation configuration must be provided in the                           <span>Client library configuration file</span> field.</li> <li><span>Application Default Credentials</span>: authenticate using                        the Application Default Credentials. When selecting this mode, no additional                        parameters need to be defined as credentials are automatically found based                        on the application environment.</li> <li> <span>OAuth 2.0 - Authorization Code grant</span>: authenticate                        using OAuth credentials. The OAuth parameters must be provided in the                           <span>Client ID</span>, <span>Client secret</span>,                           <span>Authorization code</span>, and <span>Redirect                           URI</span> fields. Only Desktop application credentials are                        supported. For more information, read <a href="https://support.google.com/googleapi/answer/6158849#zippy=%2Cnative-applications%2Cdesktop-apps" target="_blank">Desktop apps</a> and <a href="https://help.qlik.com/talend/en-US/components/8.0/accessing-bigquery-using-oauth-2-0-authentication-mode" title="Use OAuth 2.0 - Authorization Code grant to connect BigQuery components to Google BigQuery in a Standard Job.">Accessing BigQuery using OAuth 2.0 authentication mode</a>.</li> <li> <span>OAuth Access Token</span>: authenticate using an OAuth                        access token. When selecting this mode, the token must be provided in the                           <span>OAuth Access Token</span> file. </li> </ul><br><br>To know more about the Google Cloud authentication process, read [the Google Cloud documentation](https://cloud.google.com/docs/authentication/). |
| Service account credentials file | Enter the path to the credentials file created for the service account to be<br>used. This file must be stored in the machine in which your Talend<br>Job is actually launched and executed.<br><br>This property is only available when you<br>authenticate using Service account. |
| Client ID and Client secret | Paste the client ID and the client secret, both created and viewable<br>on the API Access tab view of the project hosting the Google BigQuery service and<br>the Cloud Storage service you need to use.<br><br>To enter the client secret, click the [...]<br>button next to the client secret field, and then in the pop-up dialog box enter the client<br>secret between double quotes and click OK to save the<br>settings.<br><br>This property is only available when you authenticate using OAuth<br>2.0 - Authorization Code grant. |
| OAuth Access Token | Enter an access token.<br><br>The lifetime of the token is one hour. The<br>component does not perform the token refresh operation but will fetch the new<br>access token to operate beyond the one-hour limit.<br><br>This property is only<br>available when you authenticate using OAuth Access<br>Token. |
| Redirect URI | Enter the redirect URI for your Google OAuth desktop application.<br><br>Use a loopback URI such as http://127.0.0.1:&lt;port&gt; or http://localhost:&lt;port&gt;.<br><br>This value must exactly match one of the redirect URIs configured in your Google OAuth client.<br><br>For more information, see [redirect_uri parameter](https://developers.google.com/identity/protocols/oauth2/native-app#request-parameter-redirect_uri) and [loopback IP address](https://developers.google.com/identity/protocols/oauth2/native-app#redirect-uri_loopback) in Google documentation.<br><br>This property is only available when you authenticate using OAuth<br>2.0 - Authorization Code grant. |
| Authorization code | Paste the authorization code provided by Google for the access you are<br>building.<br><br>To obtain the authorization code, you need to execute the Job using this<br>component and when this Job pauses execution to print out an URL address, you navigate<br>to this address to copy the authorization code displayed. For more information, read<br>[Accessing BigQuery using OAuth 2.0 authentication mode](https://help.qlik.com/talend/en-US/components/8.0/accessing-bigquery-using-oauth-2-0-authentication-mode "Use OAuth 2.0 - Authorization Code grant to connect BigQuery components to Google BigQuery in a Standard Job.").<br><br>This property is only available when you authenticate using OAuth<br>2.0 - Authorization Code grant. |
| Project ID | Paste<br>the ID of the project hosting the Google BigQuery service you need to<br>use.<br><br>The ID of your project can be<br>found in the URL of the Google API Console, or by hovering your mouse<br>pointer over the name of the project in the BigQuery Browser<br>Tool. |
| Use legacy SQL and Query | Enter the query you need to use.<br><br>If the<br>query to be used is the legacy SQL of BigQuery, select this Use<br>legacy SQL checkbox. For further information about this legacy<br>SQL, see [Legacy SQL query reference](https://cloud.google.com/bigquery/docs/reference/legacy-sql) in the Google Cloud<br>documentation. |

## Advanced settings

| Properties | Description |
| --- | --- |
| Use a custom endpoint | Select this check box to use a private endpoint rather than the default one.<br><br>When selected, enter the URL in the Google BigQuery Private API<br>URL property, by respecting the following format:<br>"https://bigquery.googleapis.com".<br><br>For more information,<br>see [Access Google APIs through endpoints](https://cloud.google.com/vpc/docs/configure-private-service-connect-apis) in<br>the Google Cloud documentation.<br><br>This property is only available when you<br>authenticate using Service account. |
| *token<br>properties File Name* | Enter the path to, or<br>browse to the refresh token file you need to use.<br><br>At the first Job execution using the Authorization code you have obtained from Google BigQuery, the<br>value in this field is the directory and the name of that refresh token file to be<br>created and used; if that token file has been created and you need to reuse it, you<br>have to specify its directory and file name in this field.<br><br>With only the token file name entered, Talend Studio considers the directory of that token file to be the root of the<br>Talend Studio folder.<br><br>For further information<br>about the refresh token, see the manual of Google BigQuery. |
| Advanced Separator for numbers | Select this check box to change the separator used for the numbers. |
| Encoding | Select the encoding from the list or select Custom<br>and define it manually. This field is compulsory for database data handling. The<br>supported encodings depend on the JVM that you are using. For more information, see<br>[https://docs.oracle.com](https://docs.oracle.com/). |
| Force single query execution | Select this check box to let the component return the result of the whole<br>query. If you clear this check box, the component executes each sub-query<br>separately and returns the result of each query sequentially. |
| Result size | Select the option depending on the<br>volume of the query result.<br><br>By default, the<br>Small option is used, but<br>when the query result is larger than the [maximum response size](https://cloud.google.com/bigquery/quota-policy#queries), you<br>need to select the Large<br>option.<br><br>If the volume of the result is not<br>certain, select Auto. |
| tStatCatcher Statistics | Select this check box to collect the log data at the component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. This variable<br>functions only if the Die on error<br>check box is selected. |
| JOBID | The ID of the Job. This is an After variable and it returns<br>a string. |
| STATISTICS | The statistics of the Job. This is an After variable and it<br>returns a string. |
| STATISTICS\_CHILD | The statistics of the child Job. This is an After variable<br>and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | It can be a starting or an end component. When starting a Job, it sends the extracted data to the component that follows it; When ending a Job, it deletes a given table.<br><br>This component automatically detects and supports both<br>multi-regional locations and regional locations. When using the regional locations,<br>the buckets and the datasets to be used must be in the same locations. |
