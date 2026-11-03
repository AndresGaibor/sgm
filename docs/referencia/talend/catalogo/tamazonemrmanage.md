# tamazonemrmanage

> Fuente oficial: https://help.qlik.com/talend/en-US/components/8.0/tamazonemrmanage  
> Descargado: 2026-11-03.


---

<!-- fuente: https://help.qlik.com/talend/en-US/components/8.0/tamazonemrmanage -->

# tAmazonEMRManage

Launches or terminates a cluster on Amazon EMR (Elastic MapReduce).

## tAmazonEMRManage Standard properties

These properties are used to configure tAmazonEMRManage running in the Standard Job framework.

The Standard tAmazonEMRManage component belongs to the Cloud family.

The component in this framework is available in all Talend products.

## Basic settings

| Properties | Description |
| --- | --- |
| Access key and Secret key | Specify the access keys (the access key ID in the Access<br>key field and the secret access key in the Secret<br>key field) required to access the Amazon Web Services. For more<br>information on AWS access keys, see [Access keys (access key ID and secret access key)](http://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys).<br><br>To enter the secret key, click the [...]<br>button next to the secret key field, and then in the pop-up dialog box enter the password<br>between double quotes and click OK to save the<br>settings. |
| Inherit credentials from AWS role | Select this checkbox to leverage the instance profile credentials. The credentials<br>can be used on Amazon EC2 instances or AWS ECS, and are delivered through the<br>Amazon EC2 metadata service. To use this option, your Job must be running within<br>Amazon EC2 or other services that can leverage IAM Roles for access to resources.<br>For more information, see [Using an IAM Role to Grant Permissions to Applications Running<br>on Amazon EC2 Instances](http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html). |
| Assume role | If you temporarily need some access permissions associated to an AWS IAM<br>role that is not granted to your user account, select this checkbox to assume that<br>role. Then specify the values for the following parameters to create a new assumed<br>role session. |
| Action | Select an action to be performed from the<br>list, either Start or Stop.<br><br><ul> <li> <p> <span>Start</span>: launch an Amazon EMR                                        cluster.</p> </li> <li> <p> <span>Stop</span>: terminate an Amazon                                        EMR cluster.</p> </li> </ul> |
| Region | Specify the AWS region by selecting a<br>region name from the list or entering a region between double quotation<br>marks (for example *"us-east-1"*).<br>For more information about how to specify the AWS region, see [Choose an AWS<br>Region](http://docs.aws.amazon.com/ElasticMapReduce/latest/ManagementGuide/emr-plan-region.html). |
| Cluster name | Enter the name of the cluster. |
| Cluster version | Select the version of the cluster.<br><br>You can also select the Customize Version and Application check box on the<br>Advanced settings view to<br>customize the cluster version information.<br><br>This property is not available when the Customize Version and Application check<br>box is selected. |
| Application | Select the applications to be installed<br>on the cluster.<br><br>You can also select the Customize Version and Application check box on the<br>Advanced settings view to<br>customize the applications information.<br><br>This property is available when an EMR<br>version is selected from the Cluster version list and the Customize Version and Application check box is<br>cleared. |
| Service role | Enter the IAM (Identity and Access<br>Management) role for the Amazon EMR service. The default role is *EMR\_DefaultRole*. To use this<br>default role, you must have already created it. |
| Job flow role | Enter the IAM role for the EC2 instances<br>that Amazon EMR manages. The default role is *EMR\_EC2\_DefaultRole*. To use this default role,<br>you must have already created it. |
| Enable log | Select this check box to enable logging<br>and in the field displayed specify the path to a folder in an S3 bucket<br>where you want Amazon EMR to write the log data. |
| Use EC2 key pair | Select this check box to associate an<br>Amazon EC2 (Elastic Compute Cloud) key pair with the cluster and in the<br>field displayed enter the name of your EC2 key pair. |
| Predicate | Specify the cluster(s) that you want to<br>stop:<br><br><ul> <li> <p> <span>All running clusters</span>: all                                        running clusters will be stopped.</p> </li> <li> <p> <span>All running clusters with predefined                                            name</span>: the running cluster with a given name                                        will be stopped. In the <span>Cluster name</span> field                                        displayed, you need to specify the name of the cluster to be                                        stopped.</p> </li> <li> <p> <span>Running cluster with predefined                                            id</span>: the running cluster with a given ID will                                        be stopped. In the <span>Cluster id</span> field displayed,                                        you need to specify the ID of the cluster to be stopped.</p> </li> </ul><br><br>This list is available only when<br>Stop is<br>selected from the Action list. |
| Instance count | Enter the number of Amazon EC2 instances<br>to initialize.<br><br>This field is available only if you select Start from the Action drop-down list in the Basic settings view and if the<br>Use multiple master nodes<br>check box is cleared. |
| Slave instance<br>count | Enter the number of Amazon EC2 slave instances to<br>initialize.<br><br>This field is available only if you select Start from the Action drop-down list in the Basic settings view and if you select<br>the Use multiple master nodes<br>check box in the Advanced<br>settings view. |
| Master instance type | Select the type of the master instance<br>to initialize. |
| Slave instance type | Select the type of the slave instance to<br>initialize. |

## Advanced settings

| Properties | Description |
| --- | --- |
| STS Endpoint | Select this check box to specify the AWS Security<br>Token Service (STS) endpoint from which to retrieve the session credentials.<br>For example, enter sts.amazonaws.com.<br><br>This checkbox is available only when the Assume<br>role checkbox is selected. |
| Signing region | Select the AWS region of the STS service. If the region is<br>not in the list, you can enter its name between double quotation marks. The<br>default value is us-east-1.<br><br>This dropdown list is available only when the Assume role<br>checkbox is selected. |
| External ID | If the administrator of the account to which the role<br>belongs provided you with an external ID, enter its value here. The<br>External Id is a unique<br>identifier that allows a limited set of users to assume the role.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Serial number | When you assume a role, the trust policy of this role might<br>require Multi-Factor Authentication (MFA). In this case, you must indicate<br>the identification number of the hardware or virtual MFA device that is<br>associated with the user who assumes the role.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Token code | When you assume a role, the trust policy of this role might<br>require Multi-Factor Authentication (MFA). In this case, you must indicate a<br>token code. This token code is a time-based one-time password produced by<br>the MFA device.<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Tags | List session tags in the form of key-value pairs. You can<br>then use these session tags in policies to allow or deny access to requests.<br><br><br>Transitive: select this checkbox to indicate that a tag<br>will persist to the next role in a role chain.<br><br>For more information about tags, see [Passing Session Tags in AWS<br>STS](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_session-tags.html#id_session-tags_role-chaining)<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| IAM policy ARNs | Enter the Amazon Resource Names (ARNs) of the IAM managed<br>policies that you want to use as managed session policies. Use managed<br>session policies to limit the permissions of the session. The policies must<br>exist in the same account as the role. The resulting session's permissions<br>are the intersection of the role's identity-based policy and the session<br>policies.<br><br>For more information about session policies, see the<br>corresponding section in [Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_session)<br><br>This field is available only when the Assume role checkbox<br>is selected. |
| Policy | Enter an IAM policy in JSON format that you want to use as a<br>session policy. Use session policies to limit the permissions of the<br>session. The resulting session's permissions are the intersection of the<br>role's identity-based policy and the session policies.<br><br>For more information about session policies, see the<br>corresponding section in [Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_session)<br><br>This field is available only when the Assume role check box<br>is selected. |
| Wait for cluster ready | Select this check box to let your Job<br>wait until the launch of the cluster is completed. |
| Visible to all users | Select this check box to make the<br>cluster visible to all IAM users. |
| Termination Protect | Select this check box to enable<br>termination protection to prevent instances in the cluster from shutting<br>down due to errors or issues during processing. |
| Enable debug | Select this check box to enable the<br>debug mode. |
| Customize Version and<br>Application | Select this check box to customize the version of the<br>cluster and the applications to be installed on the cluster.<br><br><ul> <li> <p> <span>Cluster                                        version</span>: enter the version of the cluster.</p> </li> <li> <p> <span>Applications</span>: click the <span>[+]</span> button below the table to                                    add as many rows as needed, each row for an application, and                                    specify the application by clicking the right side of the cell                                    and selecting the application from the drop-down list displayed,                                    or just entering the application name in the cell if it is not                                    in the list.</p> </li> </ul> |
| Use multiple master<br>nodes | Select this check box to enable high availability and<br>launch a cluster with multiple master nodes with the Amazon EMR distribution<br>in version 5.23 or later.<br><br>Information noteImportant: If you select this check box, you must<br>specify the identifier of the Amazon VPC subnet in the Subnet id field. |
| Subnet id | Specify the identifier of the Amazon VPC<br>(Virtual Private Cloud) subnet where you want the Job flow to<br>launch. |
| Availability Zone | Specify the availability zone for your<br>cluster's EC2 instances. |
| Master security group | Specify the security group for the<br>master instance. |
| Additional master security groups | Specify additional security groups for<br>the master instance and separate them with a comma, for example, *gname1, gname2, gname3*. |
| Slave security group | Specify the security group for the slave<br>instances. |
| Additional slave security groups | Specify additional security groups for<br>the slave instances and separate them with a comma, for example, *gname1, gname2, gname3*. |
| Service Access Security<br>Group | Specify the identifier of the Amazon EC2 security group<br>for the Amazon EMR service to access clusters in VPC private subnet.<br><br>For how to create a private subnet to enable service<br>access security group on Amazon EMR, see [Scenario 2: VPC with Public and<br>Private Subnets (NAT)](https://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_Scenario2.html). |
| Actions | Specify the bootstrap actions associated<br>with the cluster, by clicking the [+] button below the table to add as<br>many rows as needed, each row for a bootstrap action, and setting the<br>following parameters for each action:<br><br><ul> <li> <p> <span>Name</span>: enter the name of the                                    bootstrap action.</p> </li> <li> <p> <span>Script location</span>: specify the                                    location of the script run by the bootstrap action, for example,                                        <em>s3://ap-northeast-1.elasticmapreduce/bootstrap-actions/run-if</em>.</p> </li> <li> <p> <span>Arguments</span>: enter the list of                                    command line arguments (separated by commas) passed to the                                    bootstrap action script, for example, <em>"arg0","arg1","arg2"</em>.</p> </li> </ul><br><br>For more information about the bootstrap<br>actions, see [BootstrapActionConfig](http://docs.aws.amazon.com/ElasticMapReduce/latest/API/API_BootstrapActionConfig.html). |
| Steps | Specify the Job flow step(s) to be<br>invoked on the cluster after its launch, by clicking the [+] button below the<br>table to add as many rows as needed, each row for a step, and setting<br>the following parameters for each step:<br><br><ul> <li> <p> <span>Name</span>: enter the name of the job                                    flow step.</p> </li> <li> <p> <span>Action on Failure</span>: click the                                    cell and from the drop-down list select the action to take if                                    the Job flow step fails.</p> </li> <li> <p> <span>Main Class</span>: enter the name of                                    the main class in the specified Java file. If not specified, the                                    JAR file should specify a Main-Class in its manifest file.</p> </li> <li> <p> <span>Jar</span>: enter the path to the JAR                                    file run during the step, for example, <em>"s3://inputjar/test.jar"</em>.</p> </li> <li> <p> <span>Args</span>: enter the list of command                                    line arguments (separated by commas) passed to the JAR file's                                    main function when executed, for example, <em>"arg0","arg1","arg2"</em>.</p> </li> </ul><br><br>For more information about the Job flow<br>steps, see [StepConfig](http://docs.aws.amazon.com/ElasticMapReduce/latest/API/API_StepConfig.html). |
| Keep alive after steps complete | Select this check box to keep the job<br>flow alive after completing all steps. |
| Wait for steps to complete | Select this check box to let your Job<br>wait until the Job flow steps are completed.<br><br>This check box is available only when<br>the Wait for cluster<br>ready check box is selected. |
| Properties | Specify the classification and property<br>information supplied to the configuration object of the EMR cluster to<br>be created, by clicking the [+] button below the table to add as many rows as<br>needed, each row for a property, and setting the following<br>parameters:<br><br><ul> <li> <p> <span>Classification</span>: specify the                                    classification of the configuration.</p> </li> <li> <p> <span>Key</span>: enter the key of the                                    property.</p> </li> <li> <p> <span>Value</span>: enter the value of the                                    property.</p> </li> </ul><br><br>This field is available only if you select Start from the Action drop-down list in the Basic settings view and if the<br>Use multiple master nodes<br>check box is cleared. |
| Properties in<br>JSON | Enter, in JSON format, the classification and property<br>information supplied to the configuration object of the EMR clusters to<br>be created.<br><br>This field is available only if you select Start from the Action drop-down list in the Basic settings view and if you select<br>the Use multiple master nodes<br>check box in the Advanced<br>settings view. |
| tStatCatcher Statistics | Select this checkbox to gather the Job processing metadata at the Job level<br>as well as at each component level. |

## Global Variables

| Variables | Description |
| --- | --- |
| CLUSTER\_FINAL\_ID | The ID of the cluster. This is an After variable and it<br>returns a string. |
| CLUSTER\_FINAL\_NAME | The name of the cluster. This is an After variable and it<br>returns a string. |
| ERROR\_MESSAGE | The error message generated by the component when an error<br>occurs. This is an After variable and it returns a string. |

## Usage

| Usage guidance | Description |
| --- | --- |
| **Usage<br>rule** | tAmazonEMRManage is<br>usually used as a standalone component. |

**Related concepts**

* [Managing an Amazon EMR cluster](https://help.qlik.com/talend/en-US/components/8.0/tamazonemrmanage-tamazonemrresize-tamazonemrlistinstances-tjava-managing-amazon-emr-cluster-standard-component "Here's an example of using Talend components to manage an Amazon EMR cluster.")
