from os import path
import sys

import oci
from oci.config import from_file
from ocifs import OCIFileSystem
from tqdm import tqdm
import glob

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

# end config


def print_debug(txt=None):
    if DEBUG:
        if txt is not None:
            print(txt)
        else:
            print("")


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


#
# Download the output
#
OUTPUT_PREFIX = (
    "test1/job-amaaaaaangencdyadp4z3qjhq5c6tm3qxkajmieegnqgzd3cweokrbsrarhq/"
)

# get the list all files in OUTPUT_BUCKET
list_json = fs.glob(f"{OUTPUT_BUCKET}@{NAMESPACE}/{OUTPUT_PREFIX}/*.{JSON_EXT}")

# copy all the files in DIR_JSON
print()
print(f"Copy JSON files to {DIR_JSON} local directory...")
print()

for f_name in tqdm(list_json):
    only_name = f_name.split("/")[-1]
    fs.get(f_name, path.join(DIR_JSON, only_name))
