#
# To compute WER
#
import streamlit as st
from os import path
from os.path import basename
import time
import glob
import pandas as pd
from PIL import Image

# to load WER
from evaluate import load

from utils import (
    clean_directory,
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


#
# Functions
#
def do_checks(result_file, expected_file):
    result_df = pd.read_csv(result_file)
    expected_df = pd.read_csv(expected_file)

    result_file_names = result_df["file_name"]
    expected_file_names = expected_df["file_name"]

    if set(result_file_names) == set(expected_file_names):
        is_ok = True
    else:
        is_ok = False

    return is_ok


def get_txts(result_file, expected_file):
    result_df = pd.read_csv(result_file)
    expected_df = pd.read_csv(expected_file)

    # sort on the file name
    result_df = result_df.sort_values("file_name", ascending=True)
    expected_df = expected_df.sort_values("file_name", ascending=True)

    # extract the transcriptions
    preds = list(result_df["txt"].values)
    expected = list(expected_df["txt"].values)

    return preds, expected


# Set app wide config
st.set_page_config(
    page_title="Compute WER | OCI Speech UI",
    page_icon="🤖",
    layout="wide",
    menu_items={
        "Get Help": "https://luigisaetta.it",
        "Report a bug": "https://luigisaetta.it",
        "About": "This is a UI to compute WER.",
    },
)

# add a logo
image = Image.open("oracle.png")
img_widg = st.sidebar.image(image)

# metric
wer = load("wer")

with st.sidebar.form("input_form"):
    result_csv = st.file_uploader("Choose result file", type=["csv"])
    expected_csv = st.file_uploader("Choose expected result file", type=["csv"])

    compute = st.form_submit_button(label="Compute")

if compute:
    transcription_col, media_col = st.columns(gap="large", spec=[2, 1])

    # clean the local dir before upload
    clean_directory(LOCAL_DIR)

    # copy the list of files to LOCAL_DIR
    #
    for v_file in [result_csv, expected_csv]:
        file_path = path.join(LOCAL_DIR, v_file.name)

        with open(file_path, "wb") as f:
            f.write(v_file.read())

    if do_checks(result_csv.name, expected_csv.name):
        print()
        print("Compute WER")

        preds, expected = get_txts(result_csv.name, expected_csv.name)

        wer_score = wer.compute(predictions=preds, references=expected)

        print(f"WER score is: {round(wer_score, 2)}")
        print()

        st.info(f"The computed WER score is: {round(wer_score, 2)}")

    else:
        st.error("The two files are not OK")
