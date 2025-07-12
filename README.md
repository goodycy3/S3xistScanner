# S3xistScanner
A fast and efficient Python script to discover if S3 buckets exist in a specified AWS region using a given wordlist. It leverages multithreading to check for bucket existence and can optionally list the contents of found buckets.


# Features
- Multithreaded Scanning: Utilizes multiple threads for high-speed bucket enumeration.

- AWS Profile Integration: Seamlessly uses your existing AWS CLI profiles for authentication.

- Object Listing: Optionally lists the first few objects in publicly accessible buckets.

- Flexible Output: Results can be displayed in the terminal and saved to an output file.

- Error Handling: Gracefully handles common AWS errors and provides informative logging.


# Prerequisites:

✅ Install Python 3 

✅ AWS CLI installed and configured.

✅ An AWS profile with the necessary permissions (`s3:HeadBucket, s3:ListBucket`) configured in your `~/.aws/credentials file`.

### Configure your Profile via AWS CLI

```bash 
aws configure --profile your-profile-name

AWS Access Key ID [None]: YOUR_ACCESS_KEY_ID
AWS Secret Access Key [None]: YOUR_SECRET_ACCESS_KEY
Default region name [None]: us-east-1
Default output format [None]: json
```

## Note
For the S3xistScanner to function properly, the AWS IAM user or role associated with your CLI profile must have the `s3:ListBucket` permission. 
This permission is essential, as the script performs two key S3 API actions:

- `s3:HeadBucket` – Used to check whether a bucket exists.

- `s3:ListBucket` – Enables listing objects within the discovered bucket (triggered when using the -l or --list-objects flag).

✅ Ensure the IAM policy attached to your profile includes the `s3:ListBucket` permission to return accurate and complete results.

# Installation
Clone the repository:

```bash
git clone https://github.com/goodycy3/S3xistScanner.git

cd S3xistScanner
```

# Create and Activate a Virtual Environment 
A virtual environment keeps your project's dependencies separate from your system's global packages.

On macOS/Linux:
```bash
# Create the virtual environment folder
python3 -m venv venv

# Activate the environment
source venv/bin/activate
```

On Windows:
```bash
# Create the virtual environment folder
python -m venv venv

# Activate the environment
.\venv\Scripts\activate
```
Your terminal prompt should now be prefixed with (venv), indicating the environment is active.

# Install the required Python libraries:

```bash
pip install -r requirements.txt
```

# Usage

Basic Syntax
```bash
python3 s3_scanner.py -p YOUR_PROFILE -w WORDLIST_PATH -r AWS_REGION [OPTIONS]
```

## Arguments

| Argument | Short Form | Description | Required |
| :--- | :--- | :--- | :---: |
| `--profile` | `-p` | The AWS CLI profile to use for authentication. | Yes |
| `--wordlist` | `-w` | Path to the wordlist file containing potential bucket names. | Yes |
| `--region` | `-r` | The AWS region to scan (e.g., `us-east-1`). | Yes |
| `--threads` | `-t` | Number of concurrent threads to use (default: 20). | No |
| `--list-objects` | `-l` | If specified, lists objects in buckets where permissions allow. | No |
| `--output` | `-o` | The file path to save the scan results. | No |


## Examples
`Basic Scan`: Scan for S3 buckets in the us-west-2 region using the dev profile and a wordlist named buckets.txt.

```bash
python3 s3_scanner.py -p dump_creds -w buckets.txt -r us-west-2
```

`Scan with Object Listing`:
Perform the same scan as above, but also list the contents of any found buckets.

```bash
python3 s3_scanner.py -p dump_creds -w buckets.txt -r us-west-2 --list-objects
```

`Scan with More Threads and Save to File`:
Use 50 threads for a faster scan and save the results to found_buckets.txt.
```bash
python3 s3_scanner.py -p dump_creds -w common-buckets.txt -r eu-west-1 -t 50 -o found_buckets.txt
```


# Why S3xistScanner over ffuf and S3Scanner
S3xistScanner is more reliable because it uses authenticated AWS API calls (`s3:ListBucket`) to check for a bucket's existence, which uses `s3:HeadBucket` API, and then lists objects within the discovered bucket. This method provides a definitive yes/no answer directly from AWS. In contrast, tools like ffuf and many S3 scanners guess by sending unauthenticated HTTP requests, which AWS now intentionally makes ambiguous to prevent this exact type of enumeration.

### Reliability Comparison

| Aspect | S3xistScanner | ffuf | S3Scanner (Anonymous Tools) |
| :--- | :--- | :--- | :--- |
| **Method** | Authenticated AWS API Call (`s3:ListBucket`) | Unauthenticated HTTP/HTTPS Requests | Unauthenticated HTTP/HTTPS Requests |
| **Authentication** | Native AWS Profile (e.g. `~/.aws/credentials`) | None (Anonymous) | None (Anonymous) |
| **Reliability** | **High** ✅<br>Receives a definitive status (200, 403, 404) directly from the AWS API. | **Low** ⚠️<br>Guesses based on ambiguous HTTP responses, which can be misleading. | **Low** ⚠️<br>Same as ffuf; cannot reliably distinguish a private bucket from a non-existent one. |
| **Primary Use** | Confirming bucket existence with certainty using existing AWS credentials. | General-purpose, high-speed web fuzzing and content discovery. | Finding *publicly accessible* buckets and their contents. |
