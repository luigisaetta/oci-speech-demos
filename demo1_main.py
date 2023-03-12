#
# OCI Speech Demo1
# takes some wav files from a local dir and transcribe it using OCI Speech API
# can be launched from your laptop, using api keys
#
import argparse
import os
from os import path
import time
import glob
import json
import oci
from ocifs import OCIFileSystem

from oci.ai_speech.models import (
    TranscriptionModelDetails,
    ObjectLocation,
    ObjectListInlineInputLocation,
    OutputLocation,
    CreateTranscriptionJobDetails,
)

from utils import (
    print_debug,
    clean_directory,
    get_ocifs,
    copy_files_to_oss,
    copy_json_from_oss,
    wait_for_job_completion,
)

#
# global config
#
from config import (
    COMPARTMENT_ID,
    NAMESPACE,
    EXT,
    JSON_EXT,
    WAV_DIR,
    JSON_DIR,
    DEBUG,
)

# end global config


#
# Functions
#
def parser_add_args(parser):
    parser.add_argument(
        "--job_prefix",
        type=str,
        required=True,
        help="Job name and prefix",
    )
    parser.add_argument(
        "--audio_dir",
        type=str,
        required=False,
        help="Input dir for wav or flac files",
    )
    parser.add_argument(
        "--input_bucket",
        type=str,
        required=True,
        help="Input bucket",
    )
    parser.add_argument(
        "--output_bucket",
        type=str,
        required=True,
        help="Output bucket",
    )
    parser.add_argument(
        "--language_code",
        type=str,
        required=True,
        help="Language code (ex: it-IT)",
    )

    return parser


def print_args(args):
    print()
    print("*** Command line arguments ***")
    print(f"JOB prefix: {args.job_prefix}")
    print(f"INPUT_BUCKET: {args.input_bucket}")
    print(f"OUTPUT_BUCKET: {args.output_bucket}")
    print(f"LANGUAGE_CODE: {args.language_code}")
    print()


def create_transcription_job_details():
    # prepare the request
    MODE_DETAILS = TranscriptionModelDetails(
        domain="GENERIC", language_code=LANGUAGE_CODE
    )
    OBJECT_LOCATION = ObjectLocation(
        namespace_name=NAMESPACE,
        bucket_name=INPUT_BUCKET,
        object_names=FILE_NAMES,
    )
    INPUT_LOCATION = ObjectListInlineInputLocation(
        location_type="OBJECT_LIST_INLINE_INPUT_LOCATION",
        object_locations=[OBJECT_LOCATION],
    )
    OUTPUT_LOCATION = OutputLocation(
        namespace_name=NAMESPACE, bucket_name=OUTPUT_BUCKET, prefix=JOB_PREFIX
    )

    transcription_job_details = CreateTranscriptionJobDetails(
        display_name=DISPLAY_NAME,
        compartment_id=COMPARTMENT_ID,
        description="",
        model_details=MODE_DETAILS,
        input_location=INPUT_LOCATION,
        output_location=OUTPUT_LOCATION,
    )

    return transcription_job_details


def visualize_transcriptions():
    list_local_json = sorted(glob.glob(path.join(JSON_DIR, f"*.{JSON_EXT}")))

    for f_name in list_local_json:
        only_name = f_name.split("/")[-1]

        # build a nicer name, remove PREFIX and .json
        # OCI speech add this PREFIX, we remove it
        PREFIX = NAMESPACE + "_" + INPUT_BUCKET + "_"
        only_name = only_name.replace(PREFIX, "")
        only_name = only_name.replace(f".{JSON_EXT}", "")

        print(f"Audio file: {only_name}")
        with open(f_name) as f:
            d = json.load(f)
            # print only the transcription
            print(d["transcriptions"][0]["transcription"])
            print()


#
# Main
#

# command line parms
parser = argparse.ArgumentParser()
parser = parser_add_args(parser)
args = parser.parse_args()
print_args(args)

JOB_PREFIX = args.job_prefix
DISPLAY_NAME = JOB_PREFIX
INPUT_BUCKET = args.input_bucket
OUTPUT_BUCKET = args.output_bucket
# example "it-IT"
LANGUAGE_CODE = args.language_code

if args.audio_dir is not None:
    # get wav_dir from command line
    AUDIO_DIR = args.audio_dir

print("*** Starting JOB ***")
print()

# copy all files contained in DIR_WAV in INPUT_BUCKET
#

# This code try to get an instance of OCIFileSystem
fs = get_ocifs()

FILE_NAMES = copy_files_to_oss(fs, AUDIO_DIR, INPUT_BUCKET)

#
# Launch the job
#

# create the client
ai_client = oci.ai_speech.AIServiceSpeechClient(oci.config.from_file())

# prepare the request
transcription_job_details = create_transcription_job_details()

# create and launch the transcription job
transcription_job = None
print("*** Create transcription JOB ***")
t_start = time.time()

try:
    transcription_job = ai_client.create_transcription_job(
        create_transcription_job_details=transcription_job_details
    )
    # get the job id for later
    JOB_ID = transcription_job.data.id

    print(f"JOB ID is: {transcription_job.data.id}")
    print()
except Exception as e:
    print(e)

# WAIT while JOB is in progress
wait_for_job_completion(ai_client, JOB_ID)

t_ela = time.time() - t_start
print(f"JOB execution time: {round(t_ela, 1)} sec.")
print()

#
# Download the output from JSON files
#
# clean local dir
clean_directory(JSON_DIR, JSON_EXT)

# get from JOB
OUTPUT_PREFIX = transcription_job.data.output_location.prefix

copy_json_from_oss(fs, JSON_DIR, JSON_EXT, OUTPUT_PREFIX, OUTPUT_BUCKET)

# visualizing all the transcriptions
# get the file list
print()
print("*** Visualizing transcriptions ***")
print()
visualize_transcriptions()
