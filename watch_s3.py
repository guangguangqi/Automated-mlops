import subprocess
import time
import boto3
import re
import os

# Define structural configurations
BUCKET_NAME = "my-bioinfo-sequencing-data"  # 💡 Updated with your new bucket name
PREFIX = "raw/"
PROJECT_DIR = os.path.expanduser("~/slurm_project")
SEEN_DB_FILE = os.path.join(PROJECT_DIR, ".processed_samples.txt")

# Initialize S3 Client 
s3 = boto3.client('s3', region_name='us-east-1')

def get_processed_samples():
    if not os.path.exists(SEEN_DB_FILE):
        return set()
    with open(SEEN_DB_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def mark_sample_processed(sample_id):
    with open(SEEN_DB_FILE, "a") as out:
        out.write(f"{sample_id}\n")

def main():
    print(f"Initializing On-Premises MLOps S3 Watcher for bucket: s3://{BUCKET_NAME}/{PREFIX}")
    print("Press Ctrl+C to terminate.")
    
    while True:
        try:
            processed_samples = get_processed_samples()
            
            # Scan S3 bucket raw ingress directory
            response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX)
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    file_key = obj['Key']
                    
                    # Gatekeeper: Capture Forward Reads only
                    if "_R1.fastq.gz" in file_key:
                        filename = file_key.split('/')[-1]
                        sample_id = re.sub(r'_R1\.fastq\.gz$', '', filename)
                        
                        # Trigger if this sample has never been seen by the queue before
                        if sample_id not in processed_samples:
                            print(f"\n[NEW DATA DETECTED] Found s3://{BUCKET_NAME}/{file_key}")
                            
                            # Construct the exact sbatch terminal trigger execution string
                            s3_full_path = f"s3://{BUCKET_NAME}/{file_key}"
                            sbatch_cmd = f"cd {PROJECT_DIR} && sbatch run_pipeline.sh '{s3_full_path}'"
                            
                            print(f"Launching local Slurm workflow queue dispatch: {sbatch_cmd}")
                            
                            # Execute sbatch natively on your local system bash thread
                            result = subprocess.run(sbatch_cmd, shell=True, capture_output=True, text=True)
                            
                            if result.returncode == 0:
                                print(f"Success: {result.stdout.strip()}")
                                mark_sample_processed(sample_id)
                            else:
                                print(f"Error submitting to Slurm: {result.stderr.strip()}")
                                
        except Exception as e:
            print(f"[ERROR] Connection fallback loop error: {str(e)}")
            
        time.sleep(10) # Wait 10 seconds before polling S3 again

if __name__ == "__main__":
    main()
