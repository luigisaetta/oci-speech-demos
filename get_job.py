from os import path
import sys

import oci
from oci.config import from_file
from ocifs import OCIFileSystem
from tqdm import tqdm
import glob

ai_client = oci.ai_speech.AIServiceSpeechClient(oci.config.from_file())

JOB_ID = "ocid1.aispeechtranscriptionjob.oc1.eu-frankfurt-1.amaaaaaangencdya7ao5sopbf3uyc3q4too6xwf4kat3ylrlx6e3y6vzx4fq"

try:
    transcription_job = ai_client.get_transcription_job(JOB_ID)

    print(transcription_job.data)
    print()
    print(transcription_job.data.lifecycle_state)
except Exception as e:
    print(e)
