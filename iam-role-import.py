import boto3
import json


def export_iam_roles(source_session):
    iam_client = source_session.client('iam')
    roles = []

    paginator = iam_client.get_paginator('list_roles')
    for page in paginator.paginate():
        for role in page['Roles']:
            # Exclude AWS-managed roles
            if not role['Arn'].startswith('arn:aws:iam::aws:policy/'):
                roles.append(role)

    return roles

def import_iam_roles(target_session, roles):
    iam_client = target_session.client('iam')

    for role in roles:
        role_name = role['RoleName']
        assume_role_policy_document = json.dumps(role['AssumeRolePolicyDocument'])

        try:
            iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=assume_role_policy_document,
                Description=role.get('Description', ''),
                MaxSessionDuration=role.get('MaxSessionDuration', 3600),
                Tags=role.get('Tags', [])
            )
            print(f"Role {role_name} imported successfully.")
        except iam_client.exceptions.EntityAlreadyExistsException:
            print(f"Role {role_name} already exists in target account.")

def main():

    # Create a session by assuming the role in the named profile
    session = boto3.Session(profile_name='admin')

    # Source AWS account credentials
    source_session = boto3.Session(
        aws_access_key_id='SOURCE_ACCESS_KEY',
        aws_secret_access_key='SOURCE_SECRET_KEY',
        region_name='us-east-1'
    )

    # Target AWS account credentials
    target_session = boto3.Session(
        aws_access_key_id='TARGET_ACCESS_KEY',
        aws_secret_access_key='TARGET_SECRET_KEY',
        region_name='us-east-1'
    )

    roles = export_iam_roles(source_session)
    import_iam_roles(target_session, roles)

if __name__ == '__main__':
    main()
