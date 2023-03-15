#
# UI for OCI Speech
# upload a set of wav/flac files using Streamlit and get transcription
#
import streamlit as st
from os import path
from os.path import basename
import time
import glob
import json
import pandas as pd
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
    CSV_NAME,
)

LOCAL_DIR = "appo_local"
INPUT_BUCKET = "speech_input"
OUTPUT_BUCKET = "speech_output"

# list of supported audio files
audio_supported = AUDIO_FORMAT_SUPPORTED

# to translate in the lang codes expected by OCI Speech
DICT_LANG_CODES = {
    "en": "en-GB",
    "it": "it-IT",
    "es": "es-ES",
    "fr": "fr-FR",
    "de": "de-DE",
}
LANG_SUPPORTED = DICT_LANG_CODES.keys()

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
    LANGUAGE_CODE = DICT_LANG_CODES[language]

    do_csv = st.radio(label="Save to csv", horizontal=True, options=["no", "yes"])

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

            # first check sample rate is ok
            with st.spinner("Checking sampling rate..."):
                for v_file in input_files:
                    # added check of the sample rate
                    audio_path = path.join(LOCAL_DIR, v_file.name)
                    assert check_sample_rate(audio_path, SAMPLE_RATE)
                st.info("Sampling rate OK.")

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
            print("*** Create transcription JOB ***")

            try:
                transcription_job = speech_client.create_transcription_job(
                    transcription_job_details
                )

                # get the job id for later
                JOB_ID = transcription_job.data.id

                print(f"JOB ID is: {transcription_job.data.id}")
                print()

                st.info(f"Launched transcription job: {JOB_ID}")
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

            # Visualize output:
            # visualize transcriptions and audio widget
            transcription_col.subheader("Audio transcriptions:")
            media_col.subheader("Audio:")

            print()
            for txt in list_transcriptions:
                print(txt)
                transcription_col.markdown(txt)

            # prepare audio widgets
            for v_file in input_files:
                # add audio widget to enable to listen to audio
                media_col.audio(data=v_file)

            if do_csv == "yes":
                save_csv()

            t_ela = round(time.time() - t_start, 1)

            print()
            print(f"Transcription end; Total elapsed time: {t_ela} sec.")
            print()
