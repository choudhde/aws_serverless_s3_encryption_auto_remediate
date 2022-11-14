This serverless function looks for any non-compliant S3 bucket
- checks for S3 buckets without encryption AES256 or aws:kms
- automatically applies remediation by adding default AES:256 encryption to the bucket.
- creates an SNS topic 
- creates a subscription (ensure subscription is enabled to receive notification)

It will be invoked based on events when a new bucket is created or encryption is disabled