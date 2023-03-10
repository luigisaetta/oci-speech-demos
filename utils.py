import os
from os import path
from os.path import basename
import glob
import time
from tqdm import tqdm
import soundfile as sf

import oci
from ocifs import OCIFileSystem

from config import DEBUG, SLEEP_TIME, NAMESPACE


def print_debug(txt=None):
    if DEBUG:
        if txt is not None:
            print(txt)
        else:
            print("")


def check_sample_rate(f_name, sample_rate=16000):
    """
    sample_rate: the expected sampling rate
    return true if the sample_rate is the expected
    """
    vet, s_rate = sf.read(f_name)

    return s_rate == sample_rate


# to clean appo local and json dir
def clean_directory(dir, file_ext="*"):
    # remove all files with ext in dir
    files = glob.glob(path.join(dir, f"*.{file_ext}"))

    for f in files:
        os.remove(f)


# check if we can use RP
def is_rp_ok():
    rp_ok = None
    try:
        rps = oci.auth.signers.get_resource_principals_signer()

        # if here, we can use rp
        print_debug("Using RP for auth...")

        rp_ok = True
    except:
        print_debug("Using API Key for auth...")

        rp_ok = False


def get_ocifs():
    # check if we can use RP
    if is_rp_ok():
        fs = OCIFileSystem()
    else:
        fs = OCIFileSystem(config="~/.oci/config", profile="DEFAULT")

    return fs


# to copy files to oss
def copy_files_to_oss(fs, local_dir, dest_bucket, ext="*"):
    """
    copy all the files
    from local_dir
    with extension ext
    to dest_bucket
    """
    n_copied = 0

    list_files = glob.glob(path.join(local_dir, f"*.{ext}"))

    print()
    print("*** Copy audio files to transcribe ***")

    file_names = []
    for f_name in tqdm(list_files):
        print(f"Copying {f_name}...")

        only_name = basename(f_name)

        fs.put(f_name, f"{dest_bucket}@{NAMESPACE}/{only_name}")
        file_names.append(only_name)

        n_copied += 1

    print()
    print(f"Copied {n_copied} files to bucket {dest_bucket}.")
    print()

    return file_names


def copy_json_from_oss(fs, local_json_dir, json_ext, output_prefix, output_bucket):
    # get the list all files in OUTPUT_BUCKET/OUTPUT_PREFIX
    list_json = fs.glob(f"{output_bucket}@{NAMESPACE}/{output_prefix}/*.{json_ext}")

    # copy all the files in JSON_DIR
    print(f"Copy JSON result files to: {local_json_dir} local directory...")
    print()

    file_names = []
    for f_name in tqdm(list_json):
        only_name = basename(f_name)

        fs.get(f_name, path.join(local_json_dir, only_name))
        file_names.append(only_name)

    return file_names


# to clean input bucket
def clean_bucket(fs, bucket_name):
    # get the list, iterate and delete
    list_files = fs.ls(f"{bucket_name}@{NAMESPACE}/")

    for f_name in list_files:
        print(f"Deleting: {f_name}")
        fs.rm(f_name)


# to check the lang code
def check_lang_code(code, dict_lang_codes):
    # check it is in dict_lang_codes
    found = False

    for key, value in dict_lang_codes.items():
        if code == value:
            found = True
            break

    return found
