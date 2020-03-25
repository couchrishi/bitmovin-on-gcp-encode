# bitmovin-on-gcp-encode
This repository contains python code that will help you encode your source video files across multiple preset configs

# How to use this repo?
    1. Standalone: In this case, you need to un-comment the "ASSET_NAME" variable under config.py and add the name othe input        video file you want to transcode from the GCS input bucket
    2. Watchfolder: Run it on Google Cloud Functions and integrate it as part of your video pipeline workflow. Any upload to
       the GCS input bucket will trigger the encoding functions

# What do you need from Google Cloud standpoint? 
    1. Create a new service account with Compute Admin privlieges
    2. Set up two firewall rules for VOD encoding
          - Encoder-Service: Allow TCP port 9999 for all source IPs
          - Session Manager External: Allow TCP port 9090 for all source IPs
    3. Set Quota limits - The default quota should suffice. However, if you want to run several encodings in parallel, then
       you will need to increase the quota limit
          - In-use IP addresses = (max# of encodings) * (max# of instances per encoding)
          - CPUs = (max# of encodings) * 8 *)
          - Preemptible CPUs = (max# of encodings) * (max# of instances per encoding) * 8 *)
          - Persistent Disk SSD (TB) = (max. # of encodings * 0.5 TB) + (#instances * #encodings) * 0.05 TB
       Note: You can control the max# of instances basis on your requirement. 
             The general thumb rule is - More the instances, faster the encoding
             This will also directly impact the GCP compute costs
             
# What do you need from Bitmovin standpoint?  
    1. Bitmovin API Key - From the Bitmovin dashboard
    2. Bitmovin Infrastructure ID - Launch the create-bitmovin-infra.sh script
    3. Whitelisting of GCP service account for VM images - You need to provide the service account email to Bitmovin and they        will be able to whitelist the service account email ID in the back-end


# How to get kick-started? 
1. Launch the create-bitmovin-infra.sh script
    - 

GCS_INPUT_BUCKET_NAME
GCS_INPUT_ACCESS_KEY
GCS_INPUT_SECRET_KEY 
GCS_OUTPUT_BUCKET_NAME
GCS_OUTPUT_ACCESS_KEY
GCS_OUTPUT_SECRET_KEY

GCE_SERVICE_ACCOUNT_EMAIL
GCE_PRIVATE_KEY
GCE_PROJECT_ID
GCE_ACCOUNT_ID 
CLOUD_REGION

WEBHOOK_SUCCESS_URL
