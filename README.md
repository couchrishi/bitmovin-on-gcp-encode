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
    1. You need to create a Bitmovin Infra ID. This is not to be confused with GCP account or project IDs
        ./create-bitmovin-infra.sh <name of the infra> <description> 
    2. Key in the necessary values against each variable in the "config.py" file under the "manifest-generator" folder
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
    3. Zip all the files under this folder and upload it to Google Cloud Functions and deploy the scripts.
       You need to choose Python 3.7 as the runtime environment
    4. Once the cloud function is deployed, you should be able to find the HTTP endpoint of this deployed function.
       Copy and paste it somewhere locally. You will need this later.
    5. Follow above steps (1-3) for deploying the core encoding cloud function (under the folder vod-basic-encoder).
       Two changes here
            A) In the config.py file of vod-basic-encoder, you need to add the WEBHOOK_SUCCESS_URL variable
               and set it's value to the HTTP endpoint of the manifest-generator cloud function (You've already copied this)
            B) While creating the cloud functions, you need to choose "Create and Finalize" trigger (not HTTP endpoint)
    6. Ensure both the functions are successfully deployed and then upload a sample input video file into the input GCS bucket
    7. The vod-basic-encoder function will first be triggered, one standard n1.standard-8 VM and mulitple PVMs will be spun
       up.
    8. Once the ts and mp4 segments are successfully generated and uploaded to the GCS output bucket,
       the manifest-generator function will be triggered. This will create the .m3u8 and .mpd files and output them to
       the GCS output location
   
