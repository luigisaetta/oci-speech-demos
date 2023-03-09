#
# UI for OCI Speech
# up,oad a wav file using Stremlit and get transcription
#
import streamlit as st
import argparse
import os
from os import path
import time
from tqdm import tqdm
import glob
import json
import oci
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
    DEBUG,
    AUDIO_FORMAT_SUPPORTED,
)

LOCAL_DIR = "appo_local"
INPUT_BUCKET = "speech_input"
OUTPUT_BUCKET = "speech_output"

# list of supported audio files
audio_supported = AUDIO_FORMAT_SUPPORTED
LANG_SUPPORTED = ["it", "en"]
dict_lang_codes = {"it": "it-IT", "en": "en-EN"}

# end config


#
# Functions
#
def print_debug(txt=None):
    if DEBUG:
        if txt is not None:
            print(txt)
        else:
            print("")


def clean_appo_local():
    files = glob.glob(path.join(LOCAL_DIR, f"*.{EXT}"))

    for f in files:
        os.remove(f)


# to use ocifs for uploading/downloading files
# from Object Storage
def get_ocifs():
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

    return fs


def copy_wav_to_oss(fs):
    n_copied = 0

    list_wav = glob.glob(path.join(LOCAL_DIR, f"*.{EXT}"))

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

    return FILE_NAMES


# loop until the job status is completed
def wait_for_job_completion(ai_client, job_id):
    current_job = ai_client.get_transcription_job(job_id)
    status = current_job.data.lifecycle_state

    i = 1
    while status in ["ACCEPTED", "IN_PROGRESS"]:
        print(f"{i} Waiting for job to complete...")
        time.sleep(SLEEP_TIME)

        current_job = ai_client.get_transcription_job(job_id)
        status = current_job.data.lifecycle_state
        i += 1

    # final status
    print()
    print(f"JOB status is: {status}")
    print()


def clean_json_local_dir():
    files = glob.glob(path.join(JSON_DIR, f"*.{JSON_EXT}"))

    for f in files:
        os.remove(f)


def copy_json_from_oss(fs, output_prefix):
    # get the list all files in OUTPUT_BUCKET/OUTPUT_PREFIX
    list_json = fs.glob(f"{OUTPUT_BUCKET}@{NAMESPACE}/{output_prefix}/*.{JSON_EXT}")

    # copy all the files in JSON_DIR
    print(f"Copy JSON result files to: {JSON_DIR} local directory...")
    print()

    for f_name in tqdm(list_json):
        only_name = f_name.split("/")[-1]
        fs.get(f_name, path.join(JSON_DIR, only_name))


def get_transcriptions():
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
            txt = d["transcriptions"][0]["transcription"]

    return txt


# Set app wide config
st.set_page_config(
    page_title="Audio Transcription | OCI Speech UI",
    page_icon="🤖",
    layout="wide",
    menu_items={
        "Get Help": "https://luigisaetta.it",
        "Report a bug": "https://luigisaetta.it",
        "About": "This is a UI for OCI Speech Service.",
    },
)

input_type = st.sidebar.selectbox("Input Type", ["File"])

with st.sidebar.form("input_form"):
    if input_type == "Link":
        url = st.text_input("URL (video works fine)")
    elif input_type == "File":
        # for now only wav supported
        input_file = st.file_uploader("File", type=audio_supported)

    language = st.selectbox("Language", options=LANG_SUPPORTED, index=0)
    LANGUAGE_CODE = dict_lang_codes[language]

    transcribe = st.form_submit_button(label="Transcribe")

if transcribe:
    transcription_col, media_col = st.columns(gap="large", spec=[1, 1])

    if input_file:
        with st.spinner("Transcription in progress..."):
            t_start = time.time()

            # clean the local dir before upload
            clean_appo_local()

            audio_path = path.join(LOCAL_DIR, input_file.name)

            with open(audio_path, "wb") as f:
                f.write(input_file.read())

            # copy file to Object Storage
            fs = get_ocifs()
            FILE_NAMES = copy_wav_to_oss(fs)

            # transcribe JOB
            JOB_PREFIX = "test_ui"
            DISPLAY_NAME = JOB_PREFIX

            ai_client = oci.ai_speech.AIServiceSpeechClient(oci.config.from_file())

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

            # create and launch the transcription job
            transcription_job = None
            print("*** Create transcription JOB ***")

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

            # prepare to copy json
            clean_json_local_dir()

            # get from JOB
            OUTPUT_PREFIX = transcription_job.data.output_location.prefix

            copy_json_from_oss(fs, OUTPUT_PREFIX)

            txt = get_transcriptions()

            print(txt)
            transcription_col.subheader("The transcription:")
            transcription_col.markdown(txt)

            # add audio widget to enable to listen to audio
            transcription_col.audio(data=input_file)

            t_ela = round(time.time() - t_start, 1)

            print()
            print(f"Transcription end. Elapsed time: {t_ela} sec.")
            print()
