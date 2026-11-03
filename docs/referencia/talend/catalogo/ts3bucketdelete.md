# ts3bucketdelete

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/ts3bucketdelete  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/ts3bucketdelete -->

# tS3BucketDelete

Deletes an empty bucket from Amazon S3.

"Bucket" is a term used by AWS for top level folders on S3, which can contain sub folders and store all your data (objects).

## tS3BucketDelete Standard properties

These properties are used to configure tS3BucketDelete running in the Standard Job framework.

The Standard tS3BucketDelete component belongs to the Cloud family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | Either Built-In or Repository.<br><br><br>Built-In: No property data stored centrally.<br><br><br>Repository: Select the repository file where the<br>properties are stored. |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined. |
| Credential provider | Specify the way to obtain AWS security credentials.<br><br><ul> <li><span>Static credentials</span>: Use <span>access                           key</span> and <span>secret key</span> as the AWS security                        credentials.</li> <li><span>Inherit credentials from AWS role</span>: Obtain AWS                        security credentials from your EMR instance metadata. To use this option,                        the Amazon EMR cluster must be started and your Job must be running on this                        cluster. For more information, see <a href="http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html" target="_blank">Using an IAM Role to Grant Permissions to Applications                           Running on Amazon EC2 Instances</a>. This option enables you to                        develop your Job without having to put any AWS keys in the Job, thus easily                        comply with the security policy of your organization.</li> <li><span>Web identity token</span>: Use Web token for establishing                        the Amazon S3 connection.</li> <li> <p><span>Profile credentials or inherit from AWS role</span>: Use                           credentials stored in a file (known as profile configuration file) as the                           AWS security credentials or inherit AWS security credentials from the AWS                           role. </p> <p>AWS security credentials can be grouped in profiles in profile                           configuration files. A profile configuration file can contain one or                           multiple profiles. You can optionally specify the profile configuration                           file in the <span>Profile path</span> field and specify the                           profile to be used in the <span>Profile name</span> field. </p> <p>If the <span>Profile path</span> field and the                              <span>Profile name</span> filed are left empty,                              <span>&lt;user folder&gt;/.aws/credentials</span> will be used                           as the profile configuration file and the profile named                              <span>default</span> will be used. </p> <p>In cases of EC2 instances, if the profile (the specified or the default profile) does not exist,                           the component will try to inherit the AWS security credentials from the                           AWS role. </p> </li> </ul><br><br>This option can work as a dynamic parameter and be assigned a value using a<br>context variable.<br><br>Information noteNote: tRedshiftBulkExec, tRedshiftOutputBulk, and tRedshiftOutputBulkExec support<br>S3 connections that are established with Credential<br>Provider being Static Credentials or<br>Inherit credentials from AWS role only. |
| Assume Role | If you temporarily need some access permissions associated to an AWS IAM<br>role that is not granted to your user account, select this checkbox to assume that<br>role. Then specify the values for the following parameters to create a new assumed<br>role session. |
| Region | Specify the AWS region by selecting or entering a region name between double<br>quotation marks (e.g. *"us-east-1"*). For more information about the<br>AWS Region, see [Regions and Endpoints](http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region). |
| Bucket | Enter the name of the bucket, namely the top level folder, to delete.<br><br>If using Express One Zone (S3 directory buckets), you must specify the full<br>bucket name in the format<br>&lt;bucketBaseName&gt;--&lt;availabilityZoneID&gt;--x-s3,<br>as required by AWS. For more information, see [Directory bucket naming rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/directory-bucket-naming-rules.html).<br><br>Information noteNote:<br><br><ul> <li>The support of S3 Express One Zone comes with the 8.0.1-R2026-01                              <span>Talend Studio</span> monthly update or a later one delivered by <span>Talend</span>.</li> <li>Directory buckets require specific permissions. Standard credentials and                           proper IAM permissions are required. Refer to <a href="https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-express-security-iam.html" target="_blank">Authorizing Regional endpoint API operations with                              IAM</a> for more information.</li> </ul> |
| Die on error | This checkbox is cleared by default, meaning to skip the row on<br>error and to complete the process for error-free rows. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this checkbox to collect log data at the component level. |
| Use a custom region endpoint | Select this checkbox to use a custom endpoint and in the field displayed,<br>specify the URL of the custom endpoint to be used.<br><br>This option can work as a<br>dynamic parameter and be assigned a value using a context<br>variable. |
| Signing region | Select the AWS region of the STS service. If the region is<br>not in the list, you can enter its name between double quotation marks. The<br>default value is us-east-1.<br><br>This dropdown list is available only when the Assume role<br>checkbox is selected. |
| Specify STS endpoint | Select this check box to specify the AWS Security<br>Token Service (STS) endpoint from which to retrieve the session credentials.<br>For example, enter sts.amazonaws.com.<br><br>This checkbox is available only when the Assume<br>role checkbox is selected. |
| External ID | If the administrator of the account to which the role<br>belongs provided you with an external ID, enter its value here. The<br>External Id is a unique<br>identifier that allows a limited set of users to assume the role.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Serial number | When you assume a role, the trust policy of this role might<br>require Multi-Factor Authentication (MFA). In this case, you must indicate<br>the identification number of the hardware or virtual MFA device that is<br>associated with the user who assumes the role.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Token code | When you assume a role, the trust policy of this role might<br>require Multi-Factor Authentication (MFA). In this case, you must indicate a<br>token code. This token code is a time-based one-time password produced by<br>the MFA device.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Tags | List session tags in the form of key-value pairs. You can<br>then use these session tags in policies to allow or deny access to requests.<br><br><br>Transitive: select this checkbox to indicate that a tag<br>will persist to the next role in a role chain.<br><br>For more information about tags, see [Passing Session Tags in AWS<br>STS](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_session-tags.html#id_session-tags_role-chaining)<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| IAM policy ARNs | Enter the Amazon Resource Names (ARNs) of the IAM managed<br>policies that you want to use as managed session policies. Use managed<br>session policies to limit the permissions of the session. The policies must<br>exist in the same account as the role. The resulting session's permissions<br>are the intersection of the role's identity-based policy and the session<br>policies.<br><br>For more information about session policies, see the<br>corresponding section in [Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_session)<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Policy | Enter an IAM policy in JSON format that you want to use as a<br>session policy. Use session policies to limit the permissions of the<br>session. The resulting session's permissions are the intersection of the<br>role's identity-based policy and the session policies.<br><br>For more information about session policies, see the<br>corresponding section in [Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_session)<br><br>This field is available only when the Assume role check box<br>is selected. |
| Config client | Select this checkbox to configure client parameters.<br><br>Client parameter: select client<br>parameters from the list.<br><br>Value: enter the parameter value.<br><br>Not<br>available when Use existing connection<br>is selected. |

## Global Variables

| Variables | Description |
| --- | --- |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. This variable<br>functions only if the Die on error<br>check box is selected. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage rule** | This component can be used alone or with other S3 components, e.g. tS3BucketList. |
| Dynamic settings | Click the [+] button to add a row in the table<br>and fill the Code field with a context<br>variable to choose your database connection dynamically from multiple<br>connections planned in your Job. This feature is useful when you need to<br>access database tables having the same data structure but in different<br>databases, especially when you are working in an environment where you<br>cannot change your Job settings, for example, when your Job has to be<br>deployed and executed independent of Talend Studio.<br><br>Once a dynamic parameter is defined, the Component List box in the Basic<br>settings view becomes unusable.<br><br>For examples on using dynamic parameters, see [Reading data from databases through<br>context-based dynamic connections](https://help.qlik.com/talend/r/en-US/8.0/components/defining-context-groups/reading-data-from-databases-through-context-based-dynamic-connections) and [Reading data from different MySQL databases<br>using dynamically loaded connection parameters](https://help.qlik.com/talend/r/en-US/8.0/components/context/reading-data-from-different-mysql-databases-using-dynamically-loaded-connection-parameters). For more information on<br>Dynamic settings and context variables, see<br>[Dynamic schema](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/dynamic-schema) and [Creating a context group and define context<br>variables in it](https://help.qlik.com/talend/r/en-US/8.0/studio-user-guide/creating-context-group-and-define-context-variables-in-it). |
