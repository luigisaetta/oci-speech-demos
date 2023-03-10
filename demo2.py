#
# UI for OCI Speech
# upload a wav file using Streamlit and get transcription
#
import streamlit as st
import os
from os import path
import time
from tqdm import tqdm
import glob
import json
import oci

from oci.ai_speech.models import (
    TranscriptionModelDetails,
    ObjectLocation,
    ObjectListInlineInputLocation,
    OutputLocation,
    ChangeTranscriptionJobCompartmentDetails,
    UpdateTranscriptionJobDetails,
    CreateTranscriptionJobDetails,
)

from utils import (
    clean_directory,
    print_debug,
    is_rp_ok,
    get_ocifs,
    wait_for_job_completion,
)

# global config
#
from config import (
    COMPARTMENT_ID,
    NAMESPACE,
    EXT,
    JSON_EXT,
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
dict_lang_codes = {"it": "it-IT", "en": "en-GB"}

# end config


#
# Functions
#


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

    list_txts = []

    for f_name in list_local_json:
        only_name = f_name.split("/")[-1]

        with open(f_name) as f:
            d_json = json.load(f)
            # get only the transcription text
            txt = d_json["transcriptions"][0]["transcription"]
            list_txts.append(txt)

    return list_txts


#
# Main
#

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
        input_files = st.file_uploader(
            "File", type=audio_supported, accept_multiple_files=True
        )

    language = st.selectbox("Language", options=LANG_SUPPORTED, index=0)
    LANGUAGE_CODE = dict_lang_codes[language]

    transcribe = st.form_submit_button(label="Transcribe")

if transcribe:
    transcription_col, media_col = st.columns(gap="large", spec=[2, 1])

    if len(input_files):
        with st.spinner("Transcription in progress..."):
            t_start = time.time()

            # clean the local dir before upload
            clean_directory(LOCAL_DIR, EXT)

            # copy the list of files to LOCAL_DIR
            for v_file in input_files:
                audio_path = path.join(LOCAL_DIR, v_file.name)

                with open(audio_path, "wb") as f:
                    f.write(v_file.read())

            # copy all files from LOCAL_DIR to Object Storage
            fs = get_ocifs()
            FILE_NAMES = copy_wav_to_oss(fs)

            # transcribe JOB
            JOB_PREFIX = "test_ui"
            DISPLAY_NAME = JOB_PREFIX

            # we assume api key here... TODO: generalize to RP
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
            clean_directory(JSON_DIR, JSON_EXT)

            # get from JOB
            OUTPUT_PREFIX = transcription_job.data.output_location.prefix

            copy_json_from_oss(fs, OUTPUT_PREFIX)

            # extract only txt from json
            list_transcriptions = get_transcriptions()

            transcription_col.subheader("Audio transcriptions:")
            for txt in list_transcriptions:
                print(txt)
                transcription_col.markdown(txt)

            media_col.subheader("Audio:")
            for v_file in input_files:
                # add audio widget to enable to listen to audio
                media_col.audio(data=v_file)

            t_ela = round(time.time() - t_start, 1)

            print()
            print(f"Transcription end. Elapsed time: {t_ela} sec.")
            print()
