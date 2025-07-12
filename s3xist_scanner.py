#!/usr/bin/env python3
import argparse
import boto3
from botocore.exceptions import ClientError
import logging
import threading
from queue import Queue

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Suppress boto3's verbose logging to keep output clean
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

# ANSI color codes for terminal output
class colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    ENDC = '\033[0m'

def check_bucket_existence(s3_client, bucket_name):
    """
    Checks if an S3 bucket exists using the head_bucket API call.

    Args:
        s3_client: An initialized boto3 S3 client.
        bucket_name: The name of the bucket to check.

    Returns:
        A string indicating the status: 'FOUND', 'NOT_FOUND', or 'ERROR'.
    """
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return 'FOUND'
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == '403':
            return 'FOUND'
        elif error_code == '404':
            return 'NOT_FOUND'
        else:
            logging.warning(f"An unexpected client error occurred for bucket '{bucket_name}': {e}")
            return 'ERROR'
    except Exception as e:
        logging.error(f"A critical error occurred for bucket '{bucket_name}': {e}")
        return 'ERROR'

def list_bucket_contents(s3_client, bucket_name):
    """Lists the first few objects in a given S3 bucket."""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
        if 'Contents' in response:
            print(f"    {colors.YELLOW}└── Objects found:{colors.ENDC}")
            object_keys = []
            for obj in response['Contents']:
                print(f"        - {obj['Key']}")
                object_keys.append(obj['Key'])
            return object_keys
        else:
            print(f"    {colors.YELLOW}└── Bucket is empty.{colors.ENDC}")
            return []
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == 'AccessDenied':
            print(f"    {colors.RED}└── Access Denied to list objects.{colors.ENDC}")
        else:
            logging.warning(f"Could not list objects for {bucket_name}: {e}")
        return None
    except Exception as e:
        logging.error(f"A critical error occurred while listing objects for {bucket_name}: {e}")
        return None


def worker(q, region, profile_name, should_list_objects, output_file, lock):
    """Worker thread function to process buckets from the queue."""
    session = boto3.Session(profile_name=profile_name, region_name=region)
    s3_client = session.client('s3')
    
    while True:
        bucket_name = q.get()
        if bucket_name is None:
            break
        
        status = check_bucket_existence(s3_client, bucket_name)
        
        if status == 'FOUND':
            print(f"{colors.GREEN}[+] FOUND: {bucket_name.ljust(60)}{colors.ENDC}")
            
            found_objects = None
            if should_list_objects:
                found_objects = list_bucket_contents(s3_client, bucket_name)

            if output_file:
                with lock:
                    with open(output_file, 'a') as f:
                        f.write(f"Bucket: {bucket_name}\n")
                        if found_objects:
                            for obj_key in found_objects:
                                f.write(f"  - Object: {obj_key}\n")

        elif status == 'ERROR':
            print(f"{colors.YELLOW}[!] ERROR: Check logs for bucket {bucket_name.ljust(50)}{colors.ENDC}")
        
        q.task_done()

def main():
    """Main function to parse arguments and run the scanner."""
    parser = argparse.ArgumentParser(description="Scan for S3 buckets using a pre-configured AWS profile.")
    parser.add_argument('-p', '--profile', required=True, help="Your local AWS CLI profile name (should contain assumed role credentials).")
    parser.add_argument('-w', '--wordlist', required=True, help="Path to the wordlist file containing bucket names.")
    parser.add_argument('-r', '--region', required=True, help="The AWS region to target (e.g., us-west-2).")
    parser.add_argument('-t', '--threads', type=int, default=20, help="Number of threads to use for scanning (default: 20).")
    parser.add_argument('-l', '--list-objects', action='store_true', help="List objects in found buckets (if permissions allow).")
    parser.add_argument('-o', '--output', help="Output file to save found buckets and objects.")
    
    args = parser.parse_args()

    q = Queue()
    lock = threading.Lock()
    threads = []

    logging.info(f"Starting scan in region: {args.region} with {args.threads} threads, using profile '{args.profile}'.")

    for _ in range(args.threads):
        thread = threading.Thread(target=worker, args=(q, args.region, args.profile, args.list_objects, args.output, lock))
        thread.start()
        threads.append(thread)

    try:
        with open(args.wordlist, 'r') as f:
            for line in f:
                bucket_name = line.strip()
                if bucket_name:
                    q.put(bucket_name)

        q.join()

    except FileNotFoundError:
        logging.error(f"The wordlist file was not found at: {args.wordlist}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during setup: {e}")
    finally:
        for _ in range(args.threads):
            q.put(None)
        for thread in threads:
            thread.join()
        
        if args.output:
            logging.info(f"Scan complete. Results saved to {args.output}")
        else:
            logging.info("Scan complete.")

if __name__ == "__main__":
    main()
