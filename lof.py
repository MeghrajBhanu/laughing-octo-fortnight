import boto3
import os
import json

os.system('clear')

#global variables
AWS_ACCOUNT_ID = '11111'
share_policy = {
    'Sid': 'Allow use of the key',
    'Effect': 'Allow',
    'Principal': { 'AWS': 'arn:aws:iam::{0:s}:root'.format(AWS_ACCOUNT_ID)},
    'Action': [
            # kms:crypt and kms:ReEncrypt are necessary to transfer encrypted EBS resources across accounts.
            'kms:Encrypt',
            'kms:Decrypt',
            'kms:ReEncrypt*',
            # kms:CreateGrant is necessary to transfer encrypted EBS resources across regions.
            'kms:CreateGrant'
            ],
    'Resource': '*'
}

ticket_number = input("enter servicenow ticket number: ")

TagSpecification = {
    'ResourceType': 'snapshot',
    'Tags': [
        {
            'Key': 'Case Number',
            'Value': ticket_number,
        },
    ]
}


region = input("Enter your region name: ")
ec2 = boto3.resource('ec2', region_name=region)

instanceID = input("Please enter your instance ID: ")
instance = ec2.Instance(instanceID)


volumes = instance.volumes.all()
for v in volumes:
    volumeID=v.id
    print("Volume-ID:", volumeID)
    print("KMS_KEY of the above found volume:", v.kms_key_id)
    SnapShotDetails = ec2.create_snapshot(VolumeId=volumeID, TagSpecifications=[ TagSpecification,])
    print("Snapshot-ID of the above found volume:", SnapShotDetails.id)

    
    #adding permission to share the snapshot
    SnapShotDetails.modify_attribute( 
        Attribute='createVolumePermission',
        OperationType='add',
        UserIds=[AWS_ACCOUNT_ID]
    )


    kms = boto3.client('kms', region_name="us-east-2")
    policy = json.loads(kms.get_key_policy(KeyId=v.kms_key_id, PolicyName='default')['Policy'])
    policy['Statement'].append(share_policy)
    KmsKeyDetails = kms.put_key_policy(
    KeyId=v.kms_key_id,
    Policy=json.dumps(policy),
    PolicyName='default'
    )
    print(KmsKeyDetails)


print("========Completed creating Snapshot========")
