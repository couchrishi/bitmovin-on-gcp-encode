from os import path
import config as Config

import json

from bitmovin_api_sdk import AclEntry, AclPermission, EncodingOutput, MessageType, BitmovinApi, BitmovinApiLogger, \
    GcsOutput, Task, GcsInput, InputListQueryParams, Webhook, WebhookHttpMethod, Encoding, OutputListQueryParams, GceAccount

bitmovin_api = None

def init_bitmovin_api():
    global bitmovin_api
    if bitmovin_api is None:
        bitmovin_api = BitmovinApi(api_key=Config.BITMOVIN_API_KEY,
                                   tenant_org_id=Config.BITMOVIN_TENANT_ORG_ID,
                                   logger=BitmovinApiLogger())

    return bitmovin_api


def get_gcs_input(reuse_existing=True):
    # type: (bool) -> GcsInput
    """
    Retrieves or create an GCS Input bucket

    :param reuse_existing: setting this to False will force creating a new input object every time
    :return:
    """

    if not reuse_existing:
        return create_gcs_input()
    else:
        params = InputListQueryParams(name=Config.GCS_INPUT_UNIQUE_NAME)
        named_inputs = bitmovin_api.encoding.inputs.list(query_params=params)

        if named_inputs.total_count > 0:
            return named_inputs.items[0]
        else:
            return create_gcs_input()


def get_gcs_output(reuse_existing=True):
    # type: (bool) -> GcsOutput
    """
    Retrieves or create an Gcs Output bucket

    :param reuse_existing: setting this to False will force creating a new input object every time
    :return:
    """

    if not reuse_existing:
        return create_gcs_output()
    else:
        params = OutputListQueryParams(name=Config.GCS_OUTPUT_UNIQUE_NAME)
        named_outputs = bitmovin_api.encoding.outputs.list(query_params=params)

        if named_outputs.total_count > 0:
            return named_outputs.items[0]
        else:
            return create_gcs_output()


def create_gcs_output():
    # type: () -> GcsOutput
    """
    Creates a resource representing a Google Cloud Storage(GCS) bucket to which generated content will be transferred.
    For alternative output methods see
    <a href="https://bitmovin.com/docs/encoding/articles/supported-input-output-storages">
    list of supported input and output storages</a>

    <p>The provided credentials need to allow <i>read</i>, <i>write</i> and <i>list</i> operations.
    <i>delete</i> should also be granted to allow overwriting of existing files. See <a
    href="https://bitmovin.com/docs/encoding/faqs/how-can-i-create-access-secret-keys-for-google-cloud-storage">
    for creating access and secret keys for GCS.</a>
    <a
    href="https://bitmovin.com/docs/encoding/faqs/how-can-i-create-access-secret-keys-for-google-cloud-storage">
    for creating access and secret keys for GCS.</a> for further information

    <p>For reasons of simplicity, a new output resource is created on each execution of this
    example. In production use, this method should be replaced by a
    <a href="https://bitmovin.com/docs/encoding/api-reference/sections/outputs#/Encoding/GetEncodingOutputsGcs">
    get call</a> retrieving an existing resource.

    <p>API endpoint:
    https://bitmovin.com/docs/encoding/api-reference/sections/outputs#/Encoding/PostEncodingOutputsGcs
    """

    gcs_output = GcsOutput(
        name=Config.GCS_OUTPUT_UNIQUE_NAME,
        bucket_name=Config.GCS_OUTPUT_BUCKET_NAME,
        access_key=Config.GCS_OUTPUT_ACCESS_KEY,
        secret_key=Config.GCS_OUTPUT_SECRET_KEY
    )

    return bitmovin_api.encoding.outputs.gcs.create(gcs_output=gcs_output)


def create_gcs_input():
    # type: () -> GcsInput
    """
    Creates a resource representing an Google Cloud Storage bucket from which generated content will be read.

    <p>For reasons of simplicity, a new output resource is created on each execution of this
    example. In production use, this method should be replaced by a
    <a href="https://bitmovin.com/docs/encoding/api-reference/sections/outputs#/Encoding/GetEncodingOutputsGcs">
    get call</a> retrieving an existing resource.

    <p>API endpoint:
    https://bitmovin.com/docs/encoding/api-reference/sections/outputs#/Encoding/PostEncodingOutputsGcs

    """

    gcs_input = GcsInput(
        name=Config.GCS_INPUT_UNIQUE_NAME,
        bucket_name=Config.GCS_INPUT_BUCKET_NAME,
        access_key=Config.GCS_INPUT_ACCESS_KEY,
        secret_key=Config.GCS_INPUT_SECRET_KEY
    )

    return bitmovin_api.encoding.inputs.gcs.create(gcs_input=gcs_input)

def create_gce_account():
    # type: () -> GceAccount
    """
    Creates an GceAccount object.

    API endpoint:
    https://bitmovin.com/docs/encoding/api-reference/sections/encodings#/Encoding/PostEncodingEncodings

    :param name: A name that will help you identify the encoding in our dashboard (required)
    :param description: A description of the encoding (optional)
    """
    gce_account = GceAccount(
        name="Name your infrastructure",
        description="Add a description here",
        service_account_email=Config.GCE_SERVICE_ACCOUNT_EMAIL,
        private_key=Config.GCE_PRIVATE_KEY,
        project_id=Config.GCE_PROJECT_ID
    );

    gce_infra_account = bitmovin_api.encoding.infrastructure.gce.create(gce_account);
    print("Created GceInfra with ID {}.", gce_infra_account.id);
    return gce_infra_account;

def build_encoding_output(output_id, asset_name, output_path):
    # type: (str, str, str) -> EncodingOutput
    """
    Builds an EncodingOutput object which defines where the output content (e.g. of a muxing) will be written to.
    Public read permissions will be set for the files written, so they can be accessed easily via HTTP.

    :param output_id: The id of the output resource to be used by the EncodingOutput
    :param asset_name: The name or house identifier of the asset being processed
    :param output_path: The path where the content will be written to
    """

    acl_entry = AclEntry(
        permission=AclPermission.PUBLIC_READ
    )

    return EncodingOutput(
        output_path=build_absolute_output_path(relative_path=output_path, relative_root=asset_name),
        output_id=output_id,
        acl=[acl_entry]
    )

def build_encoding_output_with_absolute_path(output_id, output_path):
    # type: (str, str, str) -> EncodingOutput
    """
    Builds an EncodingOutput object which defines where the output content (e.g. of a muxing) will be written to.
    Public read permissions will be set for the files written, so they can be accessed easily via HTTP.

    :param output_id: The id of the output resource to be used by the EncodingOutput
    :param asset_name: The name or house identifier of the asset being processed
    :param output_path: The path where the content will be written to
    """

    acl_entry = AclEntry(
        permission=AclPermission.PUBLIC_READ
    )

    return EncodingOutput(
        output_path=output_path,
        output_id=output_id,
        acl=[acl_entry]
    )

def build_absolute_output_path(relative_root, relative_path):
    # type: (str, str) -> str
    """
    Builds an absolute path by concatenating the GCS_OUTPUT_BASE_PATH configuration parameter, the
    name of this example and the given relative path

    <p>e.g.: /gcs/base/path/relativeRoot/relative/path

    :param relative_root: A single common root to use for all outputs. Typically used when multiple encodings are
    performed on the same asset
    :param relative_path: The relative path that is concatenated
    """

    return path.join(Config.OUTPUT_BASE_PATH, relative_root, relative_path)

def build_absolute_input_path(relative_root, relative_path):
    # type: (str, str) -> str
    """
    Builds an absolute path by concatenating the GCS_OUTPUT_BASE_PATH configuration parameter, the
    name of this example and the given relative path

    <p>e.g.: /gcs/base/path/relativeRoot/relative/path

    :param relative_root: A single common root to use for all outputs. Typically used when multiple encodings are
    performed on the same asset
    :param relative_path: The relative path that is concatenated
    """

    return path.join(Config.INPUT_BASE_PATH, relative_root, relative_path)

def retrieve_output_info(encoding_id):
    # type: (str) -> (str, str)
    """
    Retrieves the output information (output ID and base path) for a given encoding.
    WARNING: this assumes that all muxings are output to a single output, and in the same base location!

    :param encoding_id: The identifier of the encoding
    :return: a dict containing output ID and relative root
    """

    all_muxings = bitmovin_api.encoding.encodings.muxings.list(encoding_id=encoding_id)

    # TODO: filter to only return muxings that have an output
    muxing_output = all_muxings.items[0].outputs[0]

    relative_path = path.relpath(muxing_output.output_path, start=Config.OUTPUT_BASE_PATH)
    relative_root = relative_path.split('/')[0]

    return dict(output_id=muxing_output.output_id, output_root=relative_root)


def log_task_errors(task):
    # type: (Task) -> None

    if task is None:
        return

    filtered = filter(lambda msg: msg.type is MessageType.ERROR, task.messages)

    for message in filtered:
        print(message.text)


def add_webhooks(encoding):
    # type: (Encoding) -> None
    webhook_success = Webhook(url=Config.WEBHOOK_SUCCESS_URL,
                              method=WebhookHttpMethod.POST)
    bitmovin_api.notifications.webhooks.encoding.encodings.finished.create_by_encoding_id(
        webhook=webhook_success,
        encoding_id=encoding.id
    )

   # webhook_error = Webhook(url=Config.WEBHOOK_ERROR_URL,
   #                         method=WebhookHttpMethod.POST)
   # bitmovin_api.notifications.webhooks.encoding.encodings.error.create_by_encoding_id(
   #     webhook=webhook_error,
   #     encoding_id=encoding.id
   # )


def write_encoding_info_to_file(codec_type, encoding_id):
    filename = 'encodings.json'
    encoding_data = dict()

    if path.exists(filename):
        with open(filename, 'r') as fp:
            encoding_data = json.load(fp)

    if Config.ASSET_NAME not in encoding_data:
        encoding_data[Config.ASSET_NAME] = dict()

    encoding_data[Config.ASSET_NAME][codec_type] = encoding_id

    with open(filename, 'w') as fp:
        json.dump(encoding_data, fp)


def read_encoding_info_from_file(codec_type):
    filename = 'encodings.json'

    if path.exists(filename):
        with open(filename, 'r') as fp:
            encoding_data = json.load(fp)
    else:
        return None

    if Config.ASSET_NAME in encoding_data:
        return encoding_data[Config.ASSET_NAME][codec_type]
    else:
        return None
