
## There are about 15 Utlity functions we will be creating for several actions. These functions would be invoked/triggered by the encoding.py 

from os import path
#import config as Config
import config as Config
import json
from bitmovin_api_sdk import AclEntry, AclPermission, EncodingOutput, MessageType, BitmovinApi, BitmovinApiLogger, \
    GcsOutput, Task, GcsInput, InputListQueryParams, Webhook, WebhookHttpMethod, Encoding, OutputListQueryParams, GceAccount


bitmovin_api = None

## Return Bitmovin API reference when called
def init_bitmovin_api():
    global bitmovin_api
    if bitmovin_api is None:
        bitmovin_api = BitmovinApi(api_key=Config.BITMOVIN_API_KEY,
                                   tenant_org_id=Config.BITMOVIN_TENANT_ORG_ID,
                                   logger=BitmovinApiLogger())

    return bitmovin_api

def create_gce_account(name, desc):
    # type: () -> GceAccount
    """
    Creates an GceAccount object.

    API endpoint:
    https://bitmovin.com/docs/encoding/api-reference/sections/encodings#/Encoding/PostEncodingEncodings

    :param name: A name that will help you identify the encoding in our dashboard (required)
    :param description: A description of the encoding (optional)
    """
    gce_account = GceAccount(
        name=name,
        description=desc,
        service_account_email=Config.GCE_SERVICE_ACCOUNT_EMAIL,
        private_key=Config.GCE_PRIVATE_KEY,
        project_id=Config.GCE_PROJECT_ID
    );

    gce_infra_account = bitmovin_api.encoding.infrastructure.gce.create(gce_account);
    print("Created GceInfra with ID {}.", gce_infra_account.id);
    return gce_infra_account;
