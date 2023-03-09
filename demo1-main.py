#
# OCI Speech Demo1
#
from os import path
import oci
from oci.config import from_file
from ocifs import OCIFileSystem
from tqdm import tqdm
import glob

# 
DEBUG = True
EXT = "wav"
JSON_EXT = "json"

WAV_DIR = "wav"
DIR_JSON = "json"

NAMESPACE = "frqap2zhtzbe"
INPUT_BUCKET = "speech_input"
OUTPUT_BUCKET = "speech_output"

def print_debug(txt=None):
    if DEBUG:
        if txt is not None:
            print(txt)
        else:
            print("")


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
print("Copy files to transcribe..")

for f_name in tqdm(list_wav):
    print(f"Copying {f_name}...")

    only_name = f_name.split("/")[-1]

    fs.put(f_name, f"{INPUT_BUCKET}@{NAMESPACE}/{only_name}")
    n_copied += 1

print()
print(f"Copied {n_copied} files to bucket {INPUT_BUCKET}.")
print()

#
# Launch the job
#

#
# Download the output
#
JOB_ID = "job-amaaaaaangencdyawhpf6ujxiuvdttseffgsvieoe6nl5ywiqyypwjofx37a"

# get the list all files in OUTPUT_BUCKET
list_json = fs.glob(f"{OUTPUT_BUCKET}@{NAMESPACE}/{JOB_ID}/*.{JSON_EXT}")

# copy all the files in DIR_JSON
print()
print(f"Copy JSON files to {DIR_JSON} local directory...")
print()

for f_name in tqdm(list_json):
    only_name = f_name.split("/")[-1]
    fs.get(f_name, path.join(DIR_JSON, only_name))

