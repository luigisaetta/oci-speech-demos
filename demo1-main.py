#
# OCI Speech Demo1
#
import argparse
import os
from os import path
import time
import sys

import oci
from oci.config import from_file
from ocifs import OCIFileSystem

from oci.ai_speech.models import (
    TranscriptionModelDetails,
    ObjectLocation,
    ObjectListInlineInputLocation,
    OutputLocation,
    ChangeTranscriptionJobCompartmentDetails,
    UpdateTranscriptionJobDetails,
    CreateTranscriptionJobDetails,
)
from tqdm import tqdm
import glob
import json

#
# global config
#
from config import (
    SLEEP_TIME,
    COMPARTMENT_ID,
    NAMESPACE,
    EXT,
    JSON_EXT,
    WAV_DIR,
    JSON_DIR,
)

DEBUG = True


# end global config


def print_debug(txt=None):
    if DEBUG:
        if txt is not None:
            print(txt)
        else:
            print("")


#
# Main
#
parser = argparse.ArgumentParser()

parser.add_argument(
    "--job_prefix",
    type=str,
    required=True,
    help="Job name and prefix",
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

args = parser.parse_args()

print()
print("*** Command line arguments ***")
print(f"JOB prefix: {args.job_prefix}")
print(f"INPUT_BUCKET: {args.input_bucket}")
print(f"OUTPUT_BUCKET: {args.output_bucket}")
print(f"LANGUAGE_CODE: {args.language_code}")
print()

JOB_PREFIX = args.job_prefix
DISPLAY_NAME = JOB_PREFIX
INPUT_BUCKET = args.input_bucket
OUTPUT_BUCKET = args.output_bucket
# example "it-IT"
LANGUAGE_CODE = args.language_code

print()
print("*** Starting JOB ***")
print()

# copy all wav files contained in DIR_WAV in INPUT_BUCKET
#

# This code try to get an instance of OCIFileSystem
# first try using Resource Principal, otherwise use api keys
#
try:
    rps = oci.auth.signers.get_resource_principals_signer()

    # if here, we can use rp
    print_debug("Using RP for auth...")

    fs = OCIFileSystem()
except:
    print_debug("Using API Key for auth...")

    default_config = oci.config.from_file()

    # validate the default config file
    oci.config.validate_config(default_config)

    fs = OCIFileSystem(config="~/.oci/config", profile="DEFAULT")

# copy wav files
n_copied = 0

list_wav = glob.glob(path.join(WAV_DIR, f"*.{EXT}"))

print()
print("*** Copy audio files to transcribe ***")

FILE_NAMES = []
for f_name in tqdm(list_wav):
    print(f"Copying {f_name}...")

    only_name = f_name.split("/")[-1]

    fs.put(f_name, f"{INPUT_BUCKET}@{NAMESPACE}/{only_name}")
    FILE_NAMES.append(only_name)

    n_copied += 1

print()
print(f"Copied {n_copied} files to bucket {INPUT_BUCKET}.")
print()

#
# Launch the job
#

# create the client
ai_client = oci.ai_speech.AIServiceSpeechClient(oci.config.from_file())

# prepare the request
MODE_DETAILS = TranscriptionModelDetails(domain="GENERIC", language_code=LANGUAGE_CODE)
OBJECT_LOCATION = ObjectLocation(
    namespace_name=NAMESPACE, bucket_name=INPUT_BUCKET, object_names=FILE_NAMES
)
INPUT_LOCATION = ObjectListInlineInputLocation(
    location_type="OBJECT_LIST_INLINE_INPUT_LOCATION",
    object_locations=[OBJECT_LOCATION],
)
OUTPUT_LOCATION = OutputLocation(
    namespace_name=NAMESPACE, bucket_name=OUTPUT_BUCKET, prefix=JOB_PREFIX
)
COMPARTMENT_DETAILS = ChangeTranscriptionJobCompartmentDetails(
    compartment_id=COMPARTMENT_ID
)
UPDATE_JOB_DETAILS = UpdateTranscriptionJobDetails(
    display_name=DISPLAY_NAME, description=""
)

transcription_job_details = CreateTranscriptionJobDetails(
    display_name=DISPLAY_NAME,
    compartment_id=COMPARTMENT_ID,
    description="",
    model_details=MODE_DETAILS,
    input_location=INPUT_LOCATION,
    output_location=OUTPUT_LOCATION,
)

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
current_job = ai_client.get_transcription_job(JOB_ID)
status = current_job.data.lifecycle_state

i = 1
while status in ["ACCEPTED", "IN_PROGRESS"]:
    print(f"{i} Waiting for job to complete...")
    time.sleep(SLEEP_TIME)

    current_job = ai_client.get_transcription_job(JOB_ID)
    status = current_job.data.lifecycle_state
    i += 1

print()
print(f"JOB status is: {status}")
print()

t_ela = time.time() - t_start
print(f"JOB execution time: {round(t_ela, 1)} sec.")
print()

#
# Download the output from JSON files
#
# clean local dir
files = glob.glob(path.join(JSON_DIR, f"*.{JSON_EXT}"))

for f in files:
    os.remove(f)

# get from JOB
OUTPUT_PREFIX = transcription_job.data.output_location.prefix

# get the list all files in OUTPUT_BUCKET/OUTPUT_PREFIX
list_json = fs.glob(f"{OUTPUT_BUCKET}@{NAMESPACE}/{OUTPUT_PREFIX}/*.{JSON_EXT}")

# copy all the files in JSON_DIR
print(f"Copy JSON result files to: {JSON_DIR} local directory...")
print()

for f_name in tqdm(list_json):
    only_name = f_name.split("/")[-1]
    fs.get(f_name, path.join(JSON_DIR, only_name))


# visualizing all the transcriptions
# get the file list
print()
print("*** Visualizing transcriptions ***")
print()
list_local_json = sorted(glob.glob(path.join(JSON_DIR, f"*.{JSON_EXT}")))

for f_name in list_local_json:
    only_name = f_name.split("/")[-1]

    # build a nicer name, remove prefix and .json
    PREFIX = NAMESPACE + "_" + INPUT_BUCKET + "_"
    only_name = only_name.replace(PREFIX, "")
    only_name = only_name.replace(f".{JSON_EXT}", "")

    print(f"Audio file: {only_name}")
    with open(f_name) as f:
        d = json.load(f)
        # print only the transcription
        print(d["transcriptions"][0]["transcription"])
        print()
