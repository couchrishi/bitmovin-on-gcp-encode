import time

from bitmovin_api_sdk import AacAudioConfiguration, MuxingStream, PresetConfiguration, \
    Encoding, Mp4Muxing, H264VideoConfiguration, FragmentedMp4MuxingManifestType, \
    Status, Stream, StreamInput, ProfileH264, TsMuxing, InfrastructureSettings, CloudRegion, GceAccount

from os import path

import utils as Utils
import config as Config

"""
This example demonstrates how to create H264 video and AAC encoded output with MP4 and MPEG2 TS muxings.

"""

EXAMPLE_NAME = "SonyLIVEncodingVODPreset"
EXAMPLE_DESCRIPTION = "Basic encoding example for SonyLIV with Preset VOD configuration"

bitmovin_api = Utils.init_bitmovin_api()
encoding_api = bitmovin_api.encoding

def encoding_h264_vod_preset(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    file = event
    Config.ASSET_NAME=file['name']
    #print("Encoding Input Asset: ", Config.ASSET_NAME):

    #gce_account = Utils.create_gce_account()
    infrastructure = InfrastructureSettings(
        cloud_region=CloudRegion[Config.CLOUD_REGION],
        infrastructure_id=Config.GCE_ACCOUNT_ID
    )

    encoding = _create_encoding_external_gce_infra(
        name=EXAMPLE_NAME + "-" + Config.ASSET_NAME,
        description=EXAMPLE_DESCRIPTION,
        infra=infrastructure
    )

    input = Utils.get_gcs_input(reuse_existing=False)
    input_file_path = Utils.build_absolute_input_path("", Config.ASSET_NAME);
    output = Utils.get_gcs_output(reuse_existing=False)

    # Add H.264 video streams to the encoding
    video_configurations = [
        _create_h264_video_configuration(height=1080, width=1980, bitrate=3500000, profile=ProfileH264.HIGH),
        _create_h264_video_configuration(height=720, width=1280, bitrate=2000000, profile=ProfileH264.HIGH),
        _create_h264_video_configuration(height=720, width=1280, bitrate=1200000, profile=ProfileH264.MAIN),
        _create_h264_video_configuration(height=540, width=960, bitrate=900000, profile=ProfileH264.MAIN),
        _create_h264_video_configuration(height=360, width=640, bitrate=664000, profile=ProfileH264.BASELINE),
        _create_h264_video_configuration(height=288, width=512, bitrate=412000, profile=ProfileH264.BASELINE),
        _create_h264_video_configuration(height=216, width=384, bitrate=224000, profile=ProfileH264.BASELINE)
    ]

    for video_configuration in video_configurations:
        video_stream = _create_stream(encoding=encoding,
                                      encoding_input=input,
                                      input_path=input_file_path,
                                      codec_configuration=video_configuration)
        _create_mp4_muxing(encoding=encoding,
                           output=output,
                           output_path="video/mp4/clear/" + str(video_configuration.height) + "-" + str(video_configuration.width) + "-" + str(video_configuration.bitrate),
                           filename="video",
                           fragment_duration=4000,
                           stream=video_stream)

        _create_ts_muxing(encoding=encoding,
                            output=output,
                            output_path="video/ts/clear/" + str(video_configuration.height) + "-" + str(video_configuration.width) + "-" + str(video_configuration.bitrate),
                            stream=video_stream)

    # Add AAC audio streams to the encoding
    aac_audio_configurations = [
        _create_aac_audio_configuration(bitrate=256000),
        _create_aac_audio_configuration(bitrate=128000),
        _create_aac_audio_configuration(bitrate=96000),
        _create_aac_audio_configuration(bitrate=64000)
    ]

    for audio_configuration in aac_audio_configurations:
        audio_stream = _create_stream(encoding=encoding,
                                      encoding_input=input,
                                      input_path=input_file_path,
                                      codec_configuration=audio_configuration)
        _create_mp4_muxing(encoding=encoding,
                           output=output,
                           output_path="audio/mp4/clear/" + str(audio_configuration.bitrate),
                           filename="audio",
                           fragment_duration=4000,
                           stream=audio_stream)

        _create_ts_muxing(encoding=encoding,
                           output=output,
                           output_path="audio/ts/clear/" + str(audio_configuration.bitrate),
                           stream=audio_stream)

    Utils.add_webhooks(encoding=encoding)

    # Execute the encoding
    _execute_encoding(encoding=encoding)


def _execute_encoding(encoding):
    # type: (Encoding) -> None
    """
    Starts the actual encoding process and periodically polls its status until it reaches a final state

    <p>API endpoints:
    https://bitmovin.com/docs/encoding/api-reference/all#/Encoding/PostEncodingEncodingsStartByEncodingId
    https://bitmovin.com/docs/encoding/api-reference/sections/encodings#/Encoding/GetEncodingEncodingsStatusByEncodingId

    <p>Please note that you can also use our webhooks API instead of polling the status. For more
    information consult the API spec:
    https://bitmovin.com/docs/encoding/api-reference/sections/notifications-webhooks

    :param encoding: The encoding to be started
    """

    bitmovin_api.encoding.encodings.start(encoding_id=encoding.id)

    time.sleep(5)
    task = bitmovin_api.encoding.encodings.status(encoding_id=encoding.id)
    print("Encoding status is {} (progress: {} %)".format(task.status, task.progress))

    if task.status is Status.ERROR:
        Utils.log_task_errors(task=task)
        raise Exception("Encoding failed")

    print("Encoding started successfully")


def _create_encoding_external_gce_infra(name, description, infra):
    # type: (str, str, InfrastructureSettings) -> Encoding
    """
    Creates an Encoding object. This is the base object to configure your encoding.

    API endpoint:
    https://bitmovin.com/docs/encoding/api-reference/sections/encodings#/Encoding/PostEncodingEncodings

    :param name: A name that will help you identify the encoding in our dashboard (required)
    :param description: A description of the encoding (optional)
    """

    encoding = Encoding(
        name=name,
        description=description,
        infrastructure=infra,
        cloud_region=CloudRegion.EXTERNAL
    )

    return bitmovin_api.encoding.encodings.create(encoding=encoding)


def _create_h264_video_configuration(height, width, bitrate, profile):
    # type: () -> H264VideoConfiguration
    """
    Creates a configuration for the H.264 video codec to be applied to video streams.

    <p>The output resolution is defined by setting the height to 1080 pixels. Width will be
    determined automatically to maintain the aspect ratio of your input video.

    <p>To keep things simple, we use a quality-optimized VoD preset configuration, which will apply
    proven settings for the codec. See <a
    href="https://bitmovin.com/docs/encoding/tutorials/how-to-optimize-your-h264-codec-configuration-for-different-use-cases">How
    to optimize your H264 codec configuration for different use-cases</a> for alternative presets.

    <p>API endpoint:
    https://bitmovin.com/docs/encoding/api-reference/sections/configurations#/Encoding/PostEncodingConfigurationsVideoH264
    """

    config = H264VideoConfiguration(
        name="H.264 "+ str(height) +"p " + str(bitrate/1000) + " Kbit/s",
        preset_configuration=PresetConfiguration.VOD_STANDARD,
        height=height,
        width=width,
        bitrate=bitrate,
        profile=profile
    )

    return bitmovin_api.encoding.configurations.video.h264.create(h264_video_configuration=config)


def _create_stream(encoding, encoding_input, input_path, codec_configuration):
    # type: (Encoding, Input, str, CodecConfiguration) -> Stream
    """
    Adds a video or audio stream to an encoding

    <p>API endpoint:
    https://bitmovin.com/docs/encoding/api-reference/sections/encodings#/Encoding/PostEncodingEncodingsStreamsByEncodingId

    :param encoding: The encoding to which the stream will be added
    :param encoding_input: The input resource providing the input file
    :param input_path: The path to the input file
    :param codec_configuration: The codec configuration to be applied to the stream
    """

    stream_input = StreamInput(
        input_id=encoding_input.id,
        input_path=input_path
    )

    stream = Stream(
        input_streams=[stream_input],
        codec_config_id=codec_configuration.id
    )

    return bitmovin_api.encoding.encodings.streams.create(encoding_id=encoding.id, stream=stream)


def _create_aac_audio_configuration(bitrate):
    # type: () -> AacAudioConfiguration
    """
    Creates a configuration for the AAC audio codec to be applied to audio streams.

    <p>API endpoint:
    https://bitmovin.com/docs/encoding/api-reference/sections/configurations#/Encoding/PostEncodingConfigurationsAudioAac
    """

    config = AacAudioConfiguration(
        name="AAC " + str(bitrate/1000) + " kbit/s",
        bitrate=bitrate
    )

    return bitmovin_api.encoding.configurations.audio.aac.create(aac_audio_configuration=config)

def _create_mp4_muxing(encoding, output, output_path, filename, fragment_duration, stream):
    # type: (Encoding, Output, str, str, Stream) -> Mp4Muxing
    """
    Creates an MP4 muxing.

    <p>API endpoint:
    https://bitmovin.com/docs/encoding/api-reference/sections/encodings#/Encoding/PostEncodingEncodingsMuxingsMp4ByEncodingId

    :param encoding: The encoding to add the MP4 muxing to
    :param output: The output that should be used for the muxing to write the segments to
    :param output_path: The output path where the fragments will be written to
    :param filename: The filename for the MP4 file
    :param stream: The stream to be added to the muxing
    """

    muxing = Mp4Muxing(
        filename=filename,
        outputs=[Utils.build_encoding_output(output_id=output.id,
                                             asset_name=Config.ASSET_NAME,
                                             output_path=output_path)],
        streams=[MuxingStream(stream_id=stream.id)],
        fragment_duration=fragment_duration,
        fragmented_mp4_muxing_manifest_type=FragmentedMp4MuxingManifestType.DASH_ON_DEMAND
    )

    return encoding_api.encodings.muxings.mp4.create(encoding_id=encoding.id, mp4_muxing=muxing)

def _create_ts_muxing(encoding, output, output_path, stream):
    # type: (Encoding, Output, str, Stream) -> TsMuxing
    """
    Creates a fragmented MP4 muxing. This will generate segments with a given segment length for
    adaptive streaming.

    <p>API endpoint:
    https://bitmovin.com/docs/encoding/api-reference/all#/Encoding/PostEncodingEncodingsMuxingsFmp4ByEncodingId

    @param encoding The encoding where to add the muxing to
    @param output The output that should be used for the muxing to write the segments to
    @param output_path The output path where the fragmented segments will be written to
    @param stream The stream that is associated with the muxing
    """

    muxing = TsMuxing(
        segment_length=4.0,
        outputs=[Utils.build_encoding_output(output_id=output.id,
                                             asset_name=Config.ASSET_NAME,
                                             output_path=output_path)],
        streams=[MuxingStream(stream_id=stream.id)]
    )

    return bitmovin_api.encoding.encodings.muxings.ts.create(encoding_id=encoding.id, ts_muxing=muxing)

