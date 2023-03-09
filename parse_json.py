from os import path
import sys

import oci
from oci.config import from_file
from ocifs import OCIFileSystem
from tqdm import tqdm
import glob
import json

#
# global config
#
DEBUG = True
EXT = "wav"
JSON_EXT = "json"

WAV_DIR = "wav"
DIR_JSON = "json"

NAMESPACE = "frqap2zhtzbe"
INPUT_BUCKET = "speech_input"
OUTPUT_BUCKET = "speech_output"

LANGUAGE_CODE = "en-US"
# set JOB PREFIX
JOB_PREFIX = "test1"
DISPLAY_NAME = "test1"
COMPARTMENT_ID = "ocid1.compartment.oc1..aaaaaaaag2cpni5qj6li5ny6ehuahhepbpveopobooayqfeudqygdtfe6h3a"

# get the file list
list_json = sorted(glob.glob(path.join(DIR_JSON, f"*.{JSON_EXT}")))

for f_name in list_json:
    only_name = f_name.split("/")[-1]
    # remove prefix and .json
    PREFIX = NAMESPACE + "_" + INPUT_BUCKET + "_"

    only_name = only_name.replace(PREFIX, "")
    only_name = only_name.replace(".json", "")

    print(only_name)

    with open(f_name) as f:
        d = json.load(f)
        print(d["transcriptions"][0]["transcription"])
        print()
