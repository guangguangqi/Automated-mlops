import subprocess
import time
import boto3
import re
import os

# Define structural configurations
BUCKET_NAME = "snakemake-qc-mlops-bucket"  
PREFIX = "raw/"
PROJECT_DIR = os.path.expanduser("~/slurm_project")
SEEN_DB_FILE = os.path.join(PROJECT_DIR, ".processed_samples.txt")

# Initialize S3 Client 
s3 = boto3.client('s3', region_name='us-east-1')
ecr = boto3.client('ecr', region_name='us-east-1')

def get_processed_samples():
    if not os.path.exists(SEEN_DB_FILE):
        return set()
    with open(SEEN_DB_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def mark_sample_processed(sample_id):
    with open(SEEN_DB_FILE, "a") as out:
        out.write(f"{sample_id}\n")

def get_ecr_token():
    try:
        response = ecr.get_authorization_token()
        token = response['authorizationData']['authorizationToken']
        import base64
        decoded_token = base64.b64decode(token).decode('utf-8')
        password = decoded_token.split(':')
        return password[1] # 💡 FIX: Return only the actual decrypted token string
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to fetch fresh ECR token: {str(e)}")
        return None

def main():
    print(f"Initializing Secure On-Premises MLOps S3 Watcher for bucket: s3://{BUCKET_NAME}/{PREFIX}")
    print("Press Ctrl+C to terminate.")
    
    cache_dir = os.path.expanduser("~/slurm_project/.apptainer_cache")
    tmp_dir = os.path.expanduser("~/slurm_project/.apptainer_tmp")
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)
    
    while True:
        try:
            processed_samples = get_processed_samples()
            response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX)
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    file_key = obj['Key']
                    
                    if "_R1.fastq.gz" in file_key:
                        filename = file_key.split('/')[-1]
                        sample_id = re.sub(r'_R1\.fastq\.gz$', '', filename)
                        
                        if sample_id not in processed_samples:
                            print(f"\n[NEW DATA DETECTED] Found s3://{BUCKET_NAME}/{file_key}")
                            
                            ecr_password = get_ecr_token()
                            if not ecr_password:
                                continue
                                
                            s3_full_path = f"s3://{BUCKET_NAME}/{file_key}"
                            
                            sbatch_cmd = (
                                f"export APPTAINER_DOCKER_USERNAME='AWS' && "
                                f"export APPTAINER_DOCKER_PASSWORD='{ecr_password}' && "
                                f"export APPTAINER_CACHEDIR='{cache_dir}' && "
                                f"export APPTAINER_TMPDIR='{tmp_dir}' && "
                                f"cd {PROJECT_DIR} && "
                                f"sbatch --export=ALL,APPTAINER_DOCKER_USERNAME,APPTAINER_DOCKER_PASSWORD,APPTAINER_CACHEDIR,APPTAINER_TMPDIR "
                                f"run_pipeline.sh '{s3_full_path}'"
                            )
                            
                            print(f"Launching authenticated Slurm queue dispatch...")
                            result = subprocess.run(sbatch_cmd, shell=True, capture_output=True, text=True)
                            
                            if result.returncode == 0:
                                print(f"Success: {result.stdout.strip()}")
                                mark_sample_processed(sample_id)
                            else:
                                print(f"Error submitting to Slurm: {result.stderr.strip()}")
                                
        except Exception as e:
            print(f"[ERROR] Connection fallback loop error: {str(e)}")
            
        time.sleep(10)

if __name__ == "__main__":
    main()
