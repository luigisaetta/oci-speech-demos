import os
from os import path
import glob
import time

import oci
from ocifs import OCIFileSystem

from config import DEBUG, SLEEP_TIME


def print_debug(txt=None):
    if DEBUG:
        if txt is not None:
            print(txt)
        else:
            print("")


# to clean appo local and json dir
def clean_directory(dir, file_ext):
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


# loop until the job status is completed
def wait_for_job_completion(ai_client, job_id):
    status = "ACCEPTED"

    # here we start a loop until the job completes
    i = 1
    while status in ["ACCEPTED", "IN_PROGRESS"]:
        print(f"{i} Waiting for job to complete...")
        time.sleep(SLEEP_TIME)

        current_job = ai_client.get_transcription_job(job_id)
        status = current_job.data.lifecycle_state
        i += 1

    # final status
    print()
    print(f"JOB final status is: {status}")
    print()
