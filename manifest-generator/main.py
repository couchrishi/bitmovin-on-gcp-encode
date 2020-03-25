import time

from bitmovin_api_sdk import BitmovinApi, BitmovinApiLogger, AclEntry, AclPermission, Status, MessageType, \
    HlsManifest, AudioMediaInfo, StreamInfo, \
    DashManifest, Period, VideoAdaptationSet, AudioAdaptationSet, \
    DashMp4Representation, DashProfile

from os import path

import utils as Utils

"""
This example demonstrates how to create default DASH and HLS manifests for an encoding.

<p>The following configuration parameters are expected:
  <ul>
   <li>BITMOVIN_API_KEY - Your API key for the Bitmovin API
   <li>GCS_OUTPUT_BASE_PATH - The base path on your GCS output bucket where content will be written.
       Example: /outputs
 </ul>

"""

bitmovin_api = Utils.init_bitmovin_api()
manifest_api = bitmovin_api.encoding.manifests


def generate_hls_dash_manifests(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        OK status
    """
    ENCODING_ID = _check_request(request)
    if ENCODING_ID != '':
        print(f"Encoding {ENCODING_ID} finished successfully, starting Manifest generation")
    else:
        raise Exception("Missing encoding id")

    _generate_hls_ts_manifest(encoding_id=ENCODING_ID,
                              name='HLS Manifest - H264 TS',
                              manifest_name='hls-manifest')
    _generate_dash_mp4_manifest(encoding_id=ENCODING_ID,
                                name='DASH Manifest - H264 MP4',
                                manifest_name='dash-manifest')


def _check_request(request):
    request_json = request.get_json(silent=True)
    request_args = request.args

    print(request_json)

    encoding_id = ''

    if request_json and 'eventType' in request_json:
        event_type = request_json['eventType']

    if event_type != "ENCODING_FINISHED":
        return encoding_id

    if request_json and 'encoding' in request_json:
        encoding_json = request_json['encoding']
        if encoding_json and 'id' in encoding_json:
            encoding_id = encoding_json['id']

    print(encoding_id)
    return encoding_id


def _generate_hls_ts_manifest(encoding_id, name, manifest_name):
    muxings = _retrieve_ts_muxings(encoding_id=encoding_id)

    # This assumes that all similar muxings are written to the same output and path
    output_id = muxings['video'][0].outputs[0].output_id
    output_path = muxings['video'][0].outputs[0].output_path
    output_root = output_path[:output_path.index("/video")]

    manifest = _create_base_hls_manifest(name=name,
                                         manifest_name=manifest_name,
                                         output_id=output_id,
                                         output_path=output_root)

    _add_hls_audio_media_infos(manifest=manifest,
                               encoding_id=encoding_id,
                               muxings=muxings['audio'],
                               language="eng",
                               output_root=output_root)

    _add_hls_video_stream_infos(manifest=manifest,
                                encoding_id=encoding_id,
                                muxings=muxings['video'],
                                output_root=output_root)

    manifest_api.hls.start(manifest_id=manifest.id)

    task = _wait_for_hls_manifest_to_finish(manifest_id=manifest.id)

    while task.status is not Status.FINISHED and task.status is not Status.ERROR:
        task = _wait_for_hls_manifest_to_finish(manifest_id=manifest.id)

    if task.status is Status.ERROR:
        Utils.log_task_errors(task=task)
        raise Exception("HLS TS Manifest failed")

    print("HLS TS Manifest finished successfully")


def _generate_dash_mp4_manifest(encoding_id, name, manifest_name):
    muxings = _retrieve_mp4_muxings(encoding_id=encoding_id)

    # This assumes that all similar muxings are written to the same output and path
    output_id = muxings['video'][0].outputs[0].output_id
    output_path = muxings['video'][0].outputs[0].output_path
    output_root = output_path[:output_path.index("/video")]

    manifest_info = _create_base_dash_manifest(name=name,
                                               manifest_name=manifest_name,
                                               output_id=output_id,
                                               output_path=output_root)
    manifest_id = manifest_info['manifest'].id

    _add_dash_audio_representations(manifest_info=manifest_info,
                                    encoding_id=encoding_id,
                                    muxings=muxings['audio'],
                                    output_root=output_root)

    _add_dash_video_representations(manifest_info=manifest_info,
                                    encoding_id=encoding_id,
                                    muxings=muxings['video'],
                                    output_root=output_root)

    manifest_api.dash.start(manifest_id=manifest_id)

    task = _wait_for_dash_manifest_to_finish(manifest_id=manifest_id)

    while task.status is not Status.FINISHED and task.status is not Status.ERROR:
        task = _wait_for_dash_manifest_to_finish(manifest_id=manifest_id)

    if task.status is Status.ERROR:
        Utils.log_task_errors(task=task)
        raise Exception("DASH MP4 Manifest failed")

    print("DASH MP4 Manifest finished successfully")


# === HLS Manifests +++

def _create_base_hls_manifest(name, manifest_name, output_id, output_path):
    """
    Creates the structure of a basic HLS manifest object
    """
    hls_manifest = HlsManifest(manifest_name='{}.m3u8'.format(manifest_name),
                               outputs=[Utils.build_encoding_output_with_absolute_path(output_id=output_id,
                                                                                       output_path=output_path)],
                               name=name)
    return manifest_api.hls.create(hls_manifest=hls_manifest)


def _add_hls_audio_media_infos(manifest, encoding_id, muxings, language, output_root):
    for muxing in muxings:
        relative_path = _extract_relative_muxing_path(muxing.outputs[0].output_path, output_root)

        _add_hls_audio_media_info(manifest=manifest,
                                  encoding_id=encoding_id,
                                  muxing_id=muxing.id,
                                  stream_id=muxing.streams[0].stream_id,
                                  relative_path=relative_path,
                                  segment_path="",
                                  language=language)
    return


def _add_hls_audio_media_info(manifest, encoding_id, muxing_id, stream_id, relative_path, segment_path, language):
    audio_media = AudioMediaInfo(name="Audio Media Info for muxing {}".format(muxing_id),
                                 group_id='audio',
                                 segment_path=segment_path,
                                 encoding_id=encoding_id,
                                 stream_id=stream_id,
                                 muxing_id=muxing_id,
                                 language=language,
                                 uri='{}audio.m3u8'.format(relative_path))
    return manifest_api.hls.media.audio.create(manifest_id=manifest.id, audio_media_info=audio_media)


def _add_hls_video_stream_infos(manifest, encoding_id, muxings, output_root):
    for muxing in muxings:
        relative_path = _extract_relative_muxing_path(muxing.outputs[0].output_path, output_root)

        _add_hls_video_stream_info(manifest=manifest,
                                   encoding_id=encoding_id,
                                   muxing_id=muxing.id,
                                   stream_id=muxing.streams[0].stream_id,
                                   segment_path="",
                                   relative_path=relative_path)


def _add_hls_video_stream_info(manifest, encoding_id, muxing_id, stream_id, relative_path, segment_path):
    stream_info = StreamInfo(name="Stream Info for muxing {}".format(muxing_id),
                             audio='audio',
                             closed_captions='NONE',
                             segment_path=segment_path,
                             uri='{}video.m3u8'.format(relative_path),
                             encoding_id=encoding_id,
                             stream_id=stream_id,
                             muxing_id=muxing_id)

    return manifest_api.hls.streams.create(manifest_id=manifest.id, stream_info=stream_info)


def _wait_for_hls_manifest_to_finish(manifest_id):
    time.sleep(5)
    task = manifest_api.hls.status(manifest_id=manifest_id)
    print("Manifest status is {} (progress: {} %)".format(task.status, task.progress))
    return task


# === DASH manifests ===

def _create_base_dash_manifest(name, manifest_name, output_id, output_path):
    # Create a standard VOD DASH manifest and add one period with an adapation set for audio and video
    manifest = DashManifest(manifest_name='{}.mpd'.format(manifest_name),
                            outputs=[Utils.build_encoding_output_with_absolute_path(output_id=output_id,
                                                                                    output_path=output_path)],
                            name=name,
                            profile=DashProfile.ON_DEMAND)
    manifest = manifest_api.dash.create(dash_manifest=manifest)

    period = Period()
    period = manifest_api.dash.periods.create(period=period, manifest_id=manifest.id)

    video_adaptation_set = VideoAdaptationSet()
    video_adaptation_set = \
        manifest_api.dash.periods.adaptationsets.video.create(video_adaptation_set=video_adaptation_set,
                                                              manifest_id=manifest.id,
                                                              period_id=period.id)

    audio_adaptation_set = AudioAdaptationSet(lang='eng')
    audio_adaptation_set = \
        manifest_api.dash.periods.adaptationsets.audio.create(audio_adaptation_set=audio_adaptation_set,
                                                              manifest_id=manifest.id,
                                                              period_id=period.id)
    return dict(manifest=manifest,
                period=period,
                video_adaptation_set=video_adaptation_set,
                audio_adaptation_set=audio_adaptation_set)


def _add_dash_audio_representations(manifest_info, encoding_id, muxings, output_root):
    for muxing in muxings:
        relative_path = _extract_relative_muxing_path(muxing.outputs[0].output_path, output_root)

        _add_dash_audio_representation(manifest_info=manifest_info,
                                       encoding_id=encoding_id,
                                       muxing_id=muxing.id,
                                       file_path=relative_path + "audio.mp4")


def _add_dash_audio_representation(manifest_info, encoding_id, muxing_id, file_path):
    representation = DashMp4Representation( encoding_id=encoding_id,
                                            muxing_id=muxing_id,
                                            file_path=file_path)
    return manifest_api.dash.periods.adaptationsets.representations.mp4.create(
        manifest_id=manifest_info['manifest'].id,
        period_id=manifest_info['period'].id,
        adaptationset_id=manifest_info['audio_adaptation_set'].id,
        dash_mp4_representation=representation)


def _add_dash_video_representations(manifest_info, encoding_id, muxings, output_root):
    for muxing in muxings:
        relative_path = _extract_relative_muxing_path(muxing.outputs[0].output_path, output_root)

        _add_dash_video_representation(manifest_info=manifest_info,
                                       encoding_id=encoding_id,
                                       muxing_id=muxing.id,
                                       file_path=relative_path + "video.mp4")


def _add_dash_video_representation(manifest_info, encoding_id, muxing_id, file_path):
    representation = DashMp4Representation( encoding_id=encoding_id,
                                            muxing_id=muxing_id,
                                            file_path=file_path)
    return manifest_api.dash.periods.adaptationsets.representations.mp4.create(
        manifest_id=manifest_info['manifest'].id,
        period_id=manifest_info['period'].id,
        adaptationset_id=manifest_info['video_adaptation_set'].id,
        dash_mp4_representation=representation)


def _wait_for_dash_manifest_to_finish(manifest_id):
    time.sleep(5)
    task = manifest_api.dash.status(manifest_id=manifest_id)
    print("Manifest status is {} (progress: {} %)".format(task.status, task.progress))
    return task


# === Muxings ===

def _retrieve_ts_muxings(encoding_id):
    # type: (str) -> dict
    """
    Retrieves the list of TS muxings from an encoding

    :param encoding_id: identifier of the encoding
    """

    muxings = bitmovin_api.encoding.encodings.muxings.ts.list(encoding_id=encoding_id).items
    return _identify_muxings(muxings)


def _retrieve_mp4_muxings(encoding_id):
    # type: (str) -> dict
    """
    Retrieves the list of MP4 muxings from an encoding

    :param encoding_id: identifier of the encoding
    """

    muxings = bitmovin_api.encoding.encodings.muxings.mp4.list(encoding_id=encoding_id).items
    return _identify_muxings(muxings)


def _identify_muxings(muxings):
    audio_muxings = list()
    video_muxings = list()

    for muxing in muxings:
        if "/audio" in muxing.outputs[0].output_path:
            audio_muxings.append(muxing)
        if "/video" in muxing.outputs[0].output_path:
            video_muxings.append(muxing)

    return dict(video=video_muxings, audio=audio_muxings)


def _extract_relative_muxing_path(full_path, output_root):
    path = full_path
    pos = full_path.find(output_root)
    if pos > -1:
        path = full_path[pos + len(output_root):]

    if path.startswith('/'):
        path = path[1:]

    return path
