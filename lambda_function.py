import json
import boto3
import re
import os

# Intercept command execution via AWS Systems Manager
ssm_client = boto3.client('ssm')

# Target specific infrastructure markers
INSTANCE_ID = os.environ.get('SLURM_HEAD_NODE_INSTANCE_ID') # e.g., "i-0abcd1234efgh5678"
PROJECT_DIR = os.environ.get('PROJECT_DIR', '/shared/projects/rnaseq')

def lambda_handler(event, context):
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        file_key = record['s3']['object']['key'] 

        if "_R1.fastq.gz" not in file_key:
            continue

        filename = file_key.split('/')[-1]
        sample_id = re.sub(r'_R1\.fastq\.gz$', '', filename)
        output_prefix = f"s3://{bucket_name}/processed/{sample_id}/"

        r1_key = file_key
        r2_key = file_key.replace('_R1.fastq.gz', '_R2.fastq.gz')

        # Craft terminal command payload destined for Slurm Cluster head node
        slurm_dispatch_cmd = (
            f"cd {PROJECT_DIR} && "
            f"SAMPLE_ID='{sample_id}' "
            f"S3_BUCKET='{bucket_name}' "
            f"S3_KEY_R1='{r1_key}' "
            f"S3_KEY_R2='{r2_key}' "
            f"S3_OUTPUT_DIR='{output_prefix}' "
            f"sbatch run_pipeline.sh"
        )

        try:
            print(f"Dispatching SSM execution instruction to Cluster Master: {slurm_dispatch_cmd}")
            response = ssm_client.send_command(
                InstanceIds=[INSTANCE_ID],
                DocumentName="AWS-RunShellScript",
                Parameters={'commands': [slurm_dispatch_cmd]}
            )
            print(f"SSM Job submitted successfully! Command ID: {response['Command']['CommandId']}")

        except Exception as e:
            print(f"Error handling job routing allocation via SSM: {str(e)}")
            raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Slurm automation payload deployed.')
    }

