import os

## Bitmovin API Details
BITMOVIN_API_KEY = ""
BITMOVIN_TENANT_ORG_ID = ""

## GCE Account Related Details
GCE_SERVICE_ACCOUNT_EMAIL = ""
GCE_PROJECT_ID = ""
GCE_ACCOUNT_ID = ""
CLOUD_REGION = "GOOGLE_US_CENTRAL_1"


# Override with local config settings
try:
    from config_local import *
except ImportError:
    print('no local settings to import')
