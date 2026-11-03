# tsqsinput

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tsqsinput  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tsqsinput -->

# tSQSInput

Retrieves one or more messages, with a maximum limit of ten messages, from an Amazon SQS (Simple Queue Service) queue.

## tSQSInput Standard properties

These properties are used to configure tSQSInput running in the Standard Job framework.

The Standard tSQSInput component belongs to the Cloud family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Property type | Either Built-In or Repository.<br><br><br>Built-In: No property data stored centrally.<br><br><br>Repository: Select the repository file where the<br>properties are stored. |
| Use an existing connection | Select this check box and in the Component<br>List drop-down list, select the desired connection component to<br>reuse the connection details you already defined. |
| Credential provider | Specify the way to obtain AWS security credentials: Static<br>credentials, Inherit credentials from AWS<br>role, or Provider credentials or inherit from AWS<br>role.<br><br><ul> <li><span>Static credentials</span>: Use <span>access key</span>                     and <span>secret key</span> as the AWS security credentials.</li> <li><span>Inherit credentials from AWS role</span>: Obtain AWS security                     credentials from your EMR instance metadata. To use this option, the Amazon EMR                     cluster must be started and your Job must be running on this cluster. For more                     information, see <a href="http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html" target="_blank">Using an IAM Role to Grant Permissions to Applications                        Running on Amazon EC2 Instances</a>. This option enables you to develop                     your Job without having to put any AWS keys in the Job, thus easily comply with                     the security policy of your organization.</li> <li><span>Provider credentials or inherit from AWS role</span>: Obtain                     AWS security credentials from provider credentials or from your EMR instance                     metadata. You can specify the profile configuration file in the                        <span>Profile path</span> field and specify the profile in the                        <span>Profile name</span> field. </li> </ul><br><br>Information noteNote: This drop-down<br>list is available only when you have installed the R2023-07 Talend Studio Monthly update or a later one delivered by Talend. For more information, check with your administrator. |
| Assume role | If you temporarily need some access permissions associated to an AWS IAM<br>role that is not granted to your user account, select this checkbox to assume that<br>role. Then specify the values for the following parameters to create a new assumed<br>role session.<br><br>Ensure that access to this<br>role has been granted to your user account by the trust policy associated to<br>this role. If you are not certain about this, ask the owner of this role or<br>your AWS administrator.<br><br><ul> <li><p><span>ARN</span>: the Amazon Resource Name (ARN) of the role to                           assume. You can find this ARN name on the <span>Summary</span>                           page of the role to be used on your AWS portal, for example, this role                           ARN could read like                              <kbd>am:aws:iam::[aws_account_number]:role/[role_name]</kbd>.                           </p><span>Role session name</span>: enter the                        name you want to use to uniquely identify your assumed role session. This                        name can contain upper- and lower-case alphanumeric characters with no                        spaces. You can also include underscores or any of the following characters:                        =,.@-. </li> <li> <p><span>Session duration                              (minutes)</span>: the duration (in minutes) for which you want                           the assumed role session to be active. This duration cannot exceed the                           maximum duration which your AWS administrator has set. The duration                           defaults to 3600 seconds if you give it no value. </p> </li> </ul><br><br><br>For an example about an IAM role and its related policy types, see [Create and Manage AWS IAM Roles](https://aws.amazon.com/blogs/security/now-create-and-manage-aws-iam-roles-more-easily-with-the-updated-iam-console/) from the AWS<br>documentation. |
| Region | Specify the AWS region by selecting a region name<br>from the list or entering a region between double quotation marks (for<br>example *"us-east-1"*) in the list. For<br>more information on AWS Regions, see [AWS Regions and<br>Endpoints](http://docs.aws.amazon.com/general/latest/gr/rande.html). |
| Queue (Name or URL) | Specify the name or the URL of the queue from which messages will be<br>retrieved. |
| Schema and Edit schema | A schema is a row description. It defines the number of fields<br>(columns) to be processed and passed on to the next component. When you create a Spark<br>Job, avoid the reserved word line when naming the<br>fields.<br><br>The schema of this component is predefined with the following<br>four String type message attributes:<br><br><ul> <li> <p> <span>MessageId</span>: the ID of the                           message.</p> </li> <li> <p> <span>ReceiptHandle</span>: the receipt handle of                           the message.</p> </li> <li> <p> <span>MD5OfBody</span>: the MD5 digest of the                           message body.</p> </li> <li> <p> <span>Body</span>: the message body.</p> </li> </ul><br><br>You can click the ![](https://help.qlik.com/talend/en-US/components/Resources/images/components-button_three_dot.png) button next to Edit<br>schema to view its schema and edit the schema by removing<br>existing attributes or adding standard SQS attributes and customized user<br>attributes. |
| Guess schema | Click this button to retrieve the schema according to your<br>settings. |
| Read standard attributes | Select this check box to retrieve standard Amazon SQS attributes along with<br>each message. For more information on the Amazon SQS attributes, see [ReceiveMessage > Request<br>Parameters](http://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_ReceiveMessage.html). |
| Read custom user attributes | Select this check box to retrieve customized user attributes along with each<br>message. |
| Custom visibility timeout | Select this check box and in the field displayed specify the visibility<br>timeout (in seconds) for the received messages. If not specified, the overall<br>visibility timeout for the queue will be used for the received messages. For more<br>information, see [Visibility Timeout](http://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/AboutVT.html). |
| Custom wait time | Select this check box and in the field displayed specify the duration (in<br>seconds) for which the call will wait for the message to arrive in the queue<br>before returning. |
| Delete the messages while streaming | Select this check box to delete the message while retrieving it from the<br>queue. |
| Read all messages from the queue | Select this check box to retrieve all messages from the queue.<br><br>This check box is not available when the Delete the messages while streaming check box is<br>cleared. |
| Max number of messages to return per request | Specify the maximum number of messages to return per each request. Valid<br>values are 1 to 10. |
| Die on error | Select the checkbox to stop the execution of the Job when an error occurs.<br><br>Clear the checkbox to skip any error and continue the Job execution process. |

## Advanced settings

| Properties | Description |
| --- | --- |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |
| Use a custom region endpoint | Select this check box to use a custom endpoint and in the field displayed,<br>specify the URL of the custom endpoint to be used.<br><br>This option can work as a<br>dynamic parameter and be assigned a value using a context<br>variable. |
| Signing region | Select the AWS region of the STS service. If the region is<br>not in the list, you can enter its name between double quotation marks. The<br>default value is us-east-1.<br><br>This dropdown list is available only when the Assume role<br>checkbox is selected. |
| Specify STS endpoint | Select this check box to specify the AWS Security<br>Token Service (STS) endpoint from which to retrieve the session credentials.<br>For example, enter sts.amazonaws.com.<br><br>This service allows you to request<br>temporary, limited-privilege credentials for the AWS user authentication.<br>Therefore, you still need to provide the access key and secret key to<br>authenticate the AWS account to be used.<br><br>For a list of the STS endpoints you can<br>use, see [AWS Security Token Service](https://docs.aws.amazon.com/general/latest/gr/rande.html#sts_region). For<br>further information about the STS temporary credentials, see [Temporary Security Credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html).<br>Both articles are from the AWS documentation.<br><br>This checkbox is available only when the Assume<br>role checkbox is selected. |
| External ID | If the administrator of the account to which the role<br>belongs provided you with an external ID, enter its value here. The<br>External Id is a unique<br>identifier that allows a limited set of users to assume the role.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Serial number | When you assume a role, the trust policy of this role might<br>require Multi-Factor Authentication (MFA). In this case, you must indicate<br>the identification number of the hardware or virtual MFA device that is<br>associated with the user who assumes the role.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Token code | When you assume a role, the trust policy of this role might<br>require Multi-Factor Authentication (MFA). In this case, you must indicate a<br>token code. This token code is a time-based one-time password produced by<br>the MFA device.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Tags | List session tags in the form of key-value pairs. You can<br>then use these session tags in policies to allow or deny access to requests.<br><br><br>Transitive: select this checkbox to indicate that a tag<br>will persist to the next role in a role chain.<br><br>For more information about tags, see [Passing Session Tags in AWS<br>STS](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_session-tags.html#id_session-tags_role-chaining)<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| IAM policy ARNs | Enter the Amazon Resource Names (ARNs) of the IAM managed<br>policies that you want to use as managed session policies. Use managed<br>session policies to limit the permissions of the session. The policies must<br>exist in the same account as the role. The resulting session's permissions<br>are the intersection of the role's identity-based policy and the session<br>policies.<br><br>For more information about session policies, see the<br>corresponding section in [Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_session)<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Policy | Enter an IAM policy in JSON format that you want to use as a<br>session policy. Use session policies to limit the permissions of the<br>session. The resulting session's permissions are the intersection of the<br>role's identity-based policy and the session policies.<br><br>For more information about session policies, see the<br>corresponding section in [Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_session)<br><br>This field is available only when the Assume role check box<br>is selected. |
| Config client | Select this check box and in the table displayed specify the client<br>configuration parameters. Click the [+] button below the<br>table to add as many rows as needed, each row for a client configuration<br>parameter, and set the value of the following attributes for each parameter:<br><br><ul> <li> <p> <span>Client parameter</span>: click the cell                           and select a parameter from the drop-down list. </p> </li> <li> <p> <span>Value</span>: enter the value for the                           corresponding parameter. </p> </li> </ul> |

## Global variables

| Variables | Description |
| --- | --- |
| NB\_LINE | The number of rows processed. This is an After variable and<br>it returns an integer. |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. This variable<br>functions only if the Die on error<br>check box is selected. |

## Usage

| Usage guidance | Description |
| --- | --- |
| Usage rule | This component is usually used as a start component of a Job or<br>subJob and it always needs an output link. |

**Related concepts**

* [Retrieving messages from an Amazon SQS queue](https://help.qlik.com/talend/en-US/components/8.0/tsqsinput-tsqsconnection-tsqsqueuedelete-tlogrow-retrieving-messages-from-amazon-sqs-queue-standard-component "Here's an example of using Talend components to retrieve all messages from an existing Amazon SQS (Simple Queue Service) queue and then delete the empty queue.")
