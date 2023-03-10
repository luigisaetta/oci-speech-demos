#
# UI for OCI Speech
# upload a set of wav/flac files using Streamlit and get transcription
#
import streamlit as st
import os
from os import path
from os.path import basename
import time
import glob
import json
from PIL import Image

import oci

# the class incapsulate the Speech API, to simplify
from speech_client import SpeechClient

from utils import (
    clean_directory,
    clean_bucket,
    check_sample_rate,
    get_ocifs,
    copy_files_to_oss,
    copy_json_from_oss,
)

# global config
#
from config import (
    COMPARTMENT_ID,
    NAMESPACE,
    EXT,
    JSON_EXT,
    JSON_DIR,
    SAMPLE_RATE,
    AUDIO_FORMAT_SUPPORTED,
)

LOCAL_DIR = "appo_local"
INPUT_BUCKET = "speech_input"
OUTPUT_BUCKET = "speech_output"

# list of supported audio files
audio_supported = AUDIO_FORMAT_SUPPORTED
LANG_SUPPORTED = ["en", "it"]
dict_lang_codes = {"it": "it-IT", "en": "en-GB", "es": "es-ES", "fr": "fr-FR"}

# end config


#
# Functions
#


# extract transcriptions from json
def get_transcriptions():
    list_local_json = sorted(glob.glob(path.join(JSON_DIR, f"*.{JSON_EXT}")))

    list_txts = []

    for f_name in list_local_json:
        # with basename should be os independent
        only_name = basename(f_name)

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

# add a logo
image = Image.open("oracle.png")
img_widg = st.sidebar.image(image)

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
            clean_directory(LOCAL_DIR)

            # clean remote bucket
            fs = get_ocifs()
            clean_bucket(fs, INPUT_BUCKET)

            # copy the list of files to LOCAL_DIR
            for v_file in input_files:
                audio_path = path.join(LOCAL_DIR, v_file.name)

                with open(audio_path, "wb") as f:
                    f.write(v_file.read())

                # added check of the sample rate
                assert check_sample_rate(audio_path, SAMPLE_RATE)

            # copy all files from LOCAL_DIR to Object Storage
            FILE_NAMES = copy_files_to_oss(fs, LOCAL_DIR, INPUT_BUCKET)

            # transcribe JOB
            JOB_PREFIX = "test_ui"
            DISPLAY_NAME = JOB_PREFIX

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
            speech_client.wait_for_job_completion(JOB_ID)

            # prepare to copy json
            clean_directory(JSON_DIR, JSON_EXT)

            # get from JOB
            OUTPUT_PREFIX = transcription_job.data.output_location.prefix

            # copy json with transcriptions from Object Storage
            copy_json_from_oss(fs, JSON_DIR, JSON_EXT, OUTPUT_PREFIX, OUTPUT_BUCKET)

            # extract only txt from json
            list_transcriptions = get_transcriptions()

            # visualize transcriptions and audio widget
            transcription_col.subheader("Audio transcriptions:")
            print()
            for txt in list_transcriptions:
                print(txt)
                transcription_col.markdown(txt)

            media_col.subheader("Audio:")
            for v_file in input_files:
                # add audio widget to enable to listen to audio
                media_col.audio(data=v_file)

            t_ela = round(time.time() - t_start, 1)

            print()
            print(f"Transcription end; Total elapsed time: {t_ela} sec.")
            print()
