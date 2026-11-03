# ts3list

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/ts3list  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/ts3list -->

# tS3List

Lists the files on Amazon S3 based on the bucket/file prefix settings.

## tS3List Standard properties

These properties are used to configure tS3List running in the Standard Job framework.

The Standard tS3List component belongs to the Cloud family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | Either Built-In or Repository.<br><br><br>Built-In: No property data stored centrally.<br><br><br>Repository: Select the repository file where the<br>properties are stored. |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined. |
| Credential provider | Specify the way to obtain AWS security credentials.<br><br><ul> <li><span>Static credentials</span>: Use <span>access                           key</span> and <span>secret key</span> as the AWS security                        credentials.</li> <li><span>Inherit credentials from AWS role</span>: Obtain AWS                        security credentials from your EMR instance metadata. To use this option,                        the Amazon EMR cluster must be started and your Job must be running on this                        cluster. For more information, see <a href="http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html" target="_blank">Using an IAM Role to Grant Permissions to Applications                           Running on Amazon EC2 Instances</a>. This option enables you to                        develop your Job without having to put any AWS keys in the Job, thus easily                        comply with the security policy of your organization.</li> <li><span>Web identity token</span>: Use Web token for establishing                        the Amazon S3 connection.</li> <li> <p><span>Profile credentials or inherit from AWS role</span>: Use                           credentials stored in a file (known as profile configuration file) as the                           AWS security credentials or inherit AWS security credentials from the AWS                           role. </p> <p>AWS security credentials can be grouped in profiles in profile                           configuration files. A profile configuration file can contain one or                           multiple profiles. You can optionally specify the profile configuration                           file in the <span>Profile path</span> field and specify the                           profile to be used in the <span>Profile name</span> field. </p> <p>If the <span>Profile path</span> field and the                              <span>Profile name</span> filed are left empty,                              <span>&lt;user folder&gt;/.aws/credentials</span> will be used                           as the profile configuration file and the profile named                              <span>default</span> will be used. </p> <p>In cases of EC2 instances, if the profile (the specified or the default profile) does not exist,                           the component will try to inherit the AWS security credentials from the                           AWS role. </p> </li> </ul><br><br>This option can work as a dynamic parameter and be assigned a value using a<br>context variable.<br><br>Information noteNote: tRedshiftBulkExec, tRedshiftOutputBulk, and tRedshiftOutputBulkExec support<br>S3 connections that are established with Credential<br>Provider being Static Credentials or<br>Inherit credentials from AWS role only. |
| Assume role | If you temporarily need some access permissions associated to an AWS IAM<br>role that is not granted to your user account, select this checkbox to assume that<br>role. Then specify the values for the following parameters to create a new assumed<br>role session.<br><br>Ensure that access to this<br>role has been granted to your user account by the trust policy associated to<br>this role. If you are not certain about this, ask the owner of this role or<br>your AWS administrator.<br><br><ul> <li><p><span>ARN</span>: the Amazon Resource Name (ARN) of the role to                           assume. You can find this ARN name on the <span>Summary</span>                           page of the role to be used on your AWS portal, for example, this role                           ARN could read like                              <kbd>am:aws:iam::[aws_account_number]:role/[role_name]</kbd>.                           </p><span>Role session name</span>: enter the                        name you want to use to uniquely identify your assumed role session. This                        name can contain upper- and lower-case alphanumeric characters with no                        spaces. You can also include underscores or any of the following characters:                        =,.@-. </li> <li> <p><span>Session duration                              (minutes)</span>: the duration (in minutes) for which you want                           the assumed role session to be active. This duration cannot exceed the                           maximum duration which your AWS administrator has set. The duration                           defaults to 3600 seconds if you give it no value. </p> </li> </ul><br><br><br>For an example about an IAM role and its related policy types, see [Create and Manage AWS IAM Roles](https://aws.amazon.com/blogs/security/now-create-and-manage-aws-iam-roles-more-easily-with-the-updated-iam-console/) from the AWS<br>documentation. |
| Region | Specify the AWS region by selecting or entering a region name between double<br>quotation marks (e.g. *"us-east-1"*). For more information about the<br>AWS Region, see [Regions and Endpoints](http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region). |
| List all bucket objects | Select this check box to list all the files on the S3 server.<br><br>Key prefix: Enter the<br>prefix of files to be listed. This way, only files with that prefix will be<br>listed. |
| Bucket | Click the [+] button to add one or<br>more lines for defining the buckets and file prefixes.<br><br><br>Bucket name: Enter the name of the<br>bucket, namely the top level folder, whose files will be listed.<br><br><br>Key prefix: Enter the prefix of files to<br>be listed.<br><br>Not available when List all bucket objects is selected. |
| Die on error | This check box is cleared by default, meaning to skip the row on error and<br>to complete the process for error-free rows. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this check box to collect log data at the component level. |
| Use a custom region endpoint | Select this check box to use a custom endpoint and in the field displayed,<br>specify the URL of the custom endpoint to be used.<br><br>This option can work as a<br>dynamic parameter and be assigned a value using a context<br>variable. |
| Signing region | Select the AWS region of the STS service. If the region is<br>not in the list, you can enter its name between double quotation marks. The<br>default value is us-east-1.<br><br>This dropdown list is available only when the Assume role<br>checkbox is selected. |
| Specify STS endpoint | Select this check box to specify the AWS Security<br>Token Service (STS) endpoint from which to retrieve the session credentials.<br>For example, enter sts.amazonaws.com.<br><br>This service allows you to request<br>temporary, limited-privilege credentials for the AWS user authentication.<br>Therefore, you still need to provide the access key and secret key to<br>authenticate the AWS account to be used.<br><br>For a list of the STS endpoints you can<br>use, see [AWS Security Token Service](https://docs.aws.amazon.com/general/latest/gr/rande.html#sts_region). For<br>further information about the STS temporary credentials, see [Temporary Security Credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html).<br>Both articles are from the AWS documentation.<br><br>This checkbox is available only when the Assume<br>role checkbox is selected. |
| External ID | If the administrator of the account to which the role<br>belongs provided you with an external ID, enter its value here. The<br>External Id is a unique<br>identifier that allows a limited set of users to assume the role.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Serial number | When you assume a role, the trust policy of this role might<br>require Multi-Factor Authentication (MFA). In this case, you must indicate<br>the identification number of the hardware or virtual MFA device that is<br>associated with the user who assumes the role.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Token code | When you assume a role, the trust policy of this role might<br>require Multi-Factor Authentication (MFA). In this case, you must indicate a<br>token code. This token code is a time-based one-time password produced by<br>the MFA device.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Tags | List session tags in the form of key-value pairs. You can<br>then use these session tags in policies to allow or deny access to requests.<br><br><br>Transitive: select this checkbox to indicate that a tag<br>will persist to the next role in a role chain.<br><br>For more information about tags, see [Passing Session Tags in AWS<br>STS](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_session-tags.html#id_session-tags_role-chaining)<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| IAM policy ARNs | Enter the Amazon Resource Names (ARNs) of the IAM managed<br>policies that you want to use as managed session policies. Use managed<br>session policies to limit the permissions of the session. The policies must<br>exist in the same account as the role. The resulting session's permissions<br>are the intersection of the role's identity-based policy and the session<br>policies.<br><br>For more information about session policies, see the<br>corresponding section in [Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_session)<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Policy | Enter an IAM policy in JSON format that you want to use as a<br>session policy. Use session policies to limit the permissions of the<br>session. The resulting session's permissions are the intersection of the<br>role's identity-based policy and the session policies.<br><br>For more information about session policies, see the<br>corresponding section in [Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_session)<br><br>This field is available only when the Assume role check box<br>is selected. |
| Config client | Select this check box and specify the client parameter(s) by clicking the<br>[+] button to add as many rows as<br>needed, each row for a client parameter, and then setting the value of the<br>following fields for each parameter:<br><br><ul> <li> <p> <span>Client parameter</span>: Click the cell                           and select the client parameter from the list. </p> </li> <li> <p> <span>Value</span>: Enter the value for the                           selected parameter. </p> </li> </ul><br><br>This check box is available only when the Use an existing connection check box is cleared.<br><br>For related information, read [the AWS documentation](https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/section-client-configuration.html). |
| Get owner information | Select this check box to retrieve the owner of the S3 bucket. To use this<br>operation, you must have s3:GetObjectAcl<br>permissions. |

## Global Variables

| Variables | Description |
| --- | --- |
| CURRENT\_BUCKET\_NAME | The current bucket name. This is a Flow variable and it<br>returns a string. |
| CURRENT\_ETAG | The hexadecimal MD5 Hash value (128-bit) of the content of<br>the current object. This is a Flow variable and it returns a string. |
| CURRENT\_KEY | The current key. This is a Flow variable and it returns a<br>string. |
| CURRENT\_LASTMODIFIED | The date the current file was last modified. This is a Flow<br>variable and it returns a date (in the format of MM-DD-YYYY). |
| CURRENT\_OWNER | The owner name of the current object. This is a Flow<br>variable and it returns a string. |
| CURRENT\_OWNER\_ID | The owner's AWS ID of the current object. This is a Flow<br>variable and it returns a string. |
| CURRENT\_SIZE | The size of the current file (in bytes). This is a Flow variable and it<br>returns an integer number. |
| CURRENT\_STORAGECLASS | The storage class used for the current object. This is a<br>Flow variable and it returns a string. |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. This variable<br>functions only if the Die on error<br>check box is selected. |
| NB\_BUCKET | The number of buckets. This is an After variable and it<br>returns an integer. |
| NB\_BUCKET\_OBJECT | The number of objects in all buckets. This is an After<br>variable and it returns an integer. |
| NB\_LINE | The number of rows processed. This is an After variable and<br>it returns an integer. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component can be used alone or with other S3 components, e.g.<br>tS3Delete. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>Once a dynamic parameter is defined, the Component List box in the Basic<br>settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |

**Related concepts**

* [Copying an S3 object from one bucket to another](https://help.qlik.com/talend/en-US/components/8.0/ts3copy-ts3connection-tlogrow-copying-s3-object-from-one-bucket-to-another-standard-component-this)
* [Listing files with the same prefix from a bucket](https://help.qlik.com/talend/en-US/components/8.0/ts3list-ts3connection-tlogrow-listing-files-with-same-prefix-from-bucket-standard-component-in-this)
