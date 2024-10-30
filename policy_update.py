import boto3, json

iam = boto3.client('iam')
sts = boto3.client('sts')

aws_account_id = sts.get_caller_identity()["Account"]
role_name = 'crossplane-provider-aws-rolechain'

trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
		{
			"Effect": "Allow",
			"Principal": {
				"AWS": "arn:aws:iam::{aws_account_id1}:role/use2-dre-controlplane-crossplane-provider-aws"
			},
			"Action": "sts:AssumeRole",
			"Condition": {}
		},
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "AWS": f"arn:aws:iam::{aws_account_id2}:role/crossplane-provider-family-aws"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

iam.update_assume_role_policy(
    RoleName=role_name,
    PolicyDocument=json.dumps(trust_policy)
)
