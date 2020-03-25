import os

## Bitmovin API Details
BITMOVIN_API_KEY = ""
BITMOVIN_TENANT_ORG_ID = ""

## GCS Input Details
GCS_INPUT_UNIQUE_NAME = "BitmovinGCSInput"
GCS_INPUT_BUCKET_NAME = ""
GCS_INPUT_ACCESS_KEY = ""
GCS_INPUT_SECRET_KEY = ""

## GCS Output Details
GCS_OUTPUT_UNIQUE_NAME = "BitmovinGCSOutput"
GCS_OUTPUT_BUCKET_NAME = ""
GCS_OUTPUT_ACCESS_KEY = ""
GCS_OUTPUT_SECRET_KEY = ""

## GCE Account Related Details
GCE_SERVICE_ACCOUNT_EMAIL = ""
GCE_PRIVATE_KEY = ""
GCE_ACCOUNT_ID = ""
CLOUD_REGION = "GOOGLE_US_CENTRAL_1"


# Encoding Details
ENCODER_VERSION = "STABLE"
ENCODING_LABELS = []
INPUT_BASE_PATH = ""
OUTPUT_BASE_PATH = ""

# ASSET DETAILS
#ASSET_NAME="high+(1).mp4"

#WEBHOOK DETAILS FOR UPDATING CMS, MODIFYING PATHS etc.
WEBHOOK_ERROR_URL = "http:/www.bitmovin.com"
WEBHOOK_SUCCESS_URL = "<HTTP ENDPOINT URL OF THE MANIFEST GENERATOR CLOUD FUNCTIONS>"
# Override with local config settings
try:
    from config_local import *
except ImportError:
    print('no local settings to import')
