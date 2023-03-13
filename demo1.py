#
# OCI Speech Demo1
# takes some wav files from a local dir and transcribe it using OCI Speech API
# can be launched from your laptop, using api keys
#
import argparse
import sys
import os
from os import path
from os.path import basename
import time
import glob
import json
import pandas as pd

import oci
from ocifs import OCIFileSystem

# the class incapsulate the Speech API, to simplify
from speech_client import SpeechClient

from utils import (
    check_lang_code,
    clean_directory,
    clean_bucket,
    get_ocifs,
    copy_files_to_oss,
    copy_json_from_oss,
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
    CSV_NAME,
)

# to check the param for the lang_code
DICT_LANG_CODES = {"it": "it-IT", "en": "en-GB", "es": "es-ES", "fr": "fr-FR"}

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
    parser.add_argument(
        "--save_csv",
        type=str,
        required=False,
        choices={"yes", "no"},
        help="If yes, create csv with output",
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


def visualize_transcriptions():
    list_local_json = sorted(glob.glob(path.join(JSON_DIR, f"*.{JSON_EXT}")))

    for f_name in list_local_json:
        only_name = basename(f_name)

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


def save_csv():
    list_local_json = sorted(glob.glob(path.join(JSON_DIR, f"*.{JSON_EXT}")))

    file_names = []
    list_txts = []

    for f_name in list_local_json:
        only_name = basename(f_name)

        # build a nicer name, remove PREFIX and .json
        # OCI speech add this PREFIX, we remove it
        PREFIX = NAMESPACE + "_" + INPUT_BUCKET + "_"
        only_name = only_name.replace(PREFIX, "")
        only_name = only_name.replace(f".{JSON_EXT}", "")

        file_names.append(only_name)
        with open(f_name) as f:
            d = json.load(f)
            # print only the transcription
            list_txts.append(d["transcriptions"][0]["transcription"])

    # create a pandas DataFrame for easy save to csv
    dict_result = {"file_name": file_names, "txt": list_txts}

    df_result = pd.DataFrame(dict_result)

    # save csv
    df_result.to_csv(CSV_NAME, index=None)


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


# check that LANGUAGE_CODE is correct
if check_lang_code(args.language_code, DICT_LANG_CODES):
    # example "it-IT"
    LANGUAGE_CODE = args.language_code
else:
    print("Invalid LANGUAGE_CODE, valid values are:")

    for key, value in DICT_LANG_CODES.items():
        print(value)
    print()

    # EXIT
    sys.exit(-1)

if args.audio_dir is not None:
    # get wav_dir from command line
    AUDIO_DIR = args.audio_dir

if args.save_csv is not None:
    if args.save_csv == "yes":
        SAVE_CSV = True

print("*** Starting JOB ***")
print()

# copy all files contained in DIR_WAV in INPUT_BUCKET
#

# This code try to get an instance of OCIFileSystem
fs = get_ocifs()

# first: clean bucket destination
clean_bucket(fs, INPUT_BUCKET)

# copy files to process to input bucket
FILE_NAMES = copy_files_to_oss(fs, AUDIO_DIR, INPUT_BUCKET)

#
# Launch the job
#

# the class that incapsulate OCI Speech API
speech_client = SpeechClient()

# prepare the request
transcription_job_details = speech_client.create_transcription_job_details(
    INPUT_BUCKET,
    OUTPUT_BUCKET,
    FILE_NAMES,
    JOB_PREFIX,
    DISPLAY_NAME,
    LANGUAGE_CODE,
)

# create and launch the transcription job
transcription_job = None
print("*** Create transcription JOB ***")
t_start = time.time()

try:
    transcription_job = speech_client.create_transcription_job(
        transcription_job_details
    )

    # get the job id for later
    JOB_ID = transcription_job.data.id

    print(f"JOB ID is: {transcription_job.data.id}")
    print()
except Exception as e:
    print(e)

# WAIT while JOB is in progress
final_status = speech_client.wait_for_job_completion(JOB_ID)

t_ela = time.time() - t_start

#
# Download the output from JSON files
#
# clean local dir
if final_status == "SUCCEEDED":
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

    if SAVE_CSV:
        # save file_names, transcriptions in csv (result.csv)
        save_csv()

    print()
    print(f"Processed {len(FILE_NAMES)} files...")
    print(f"Total execution time: {round(t_ela, 1)} sec.")
    print()
else:
    print()
    print("Error in JOB execution, failed!")
    print()
