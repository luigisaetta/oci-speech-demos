#
# class to simplify OCI Speech API
#
import time
import oci

from oci.ai_speech.models import (
    TranscriptionModelDetails,
    ObjectLocation,
    ObjectListInlineInputLocation,
    OutputLocation,
    CreateTranscriptionJobDetails,
)

from config import (
    DEBUG,
    SLEEP_TIME,
    COMPARTMENT_ID,
    NAMESPACE,
    SAMPLE_RATE,
    AUDIO_FORMAT_SUPPORTED,
)


class SpeechClient:
    # to enable/disable debug printing

    ai_client = None

    def __init__(self):
        # we assume api key here... TODO: generalize to RP
        self.ai_client = oci.ai_speech.AIServiceSpeechClient(oci.config.from_file())

    def create_transcription_job_details(
        self,
        input_bucket,
        output_bucket,
        file_names,
        job_prefix,
        display_name,
        language_code,
    ):
        # prepare the request
        MODE_DETAILS = TranscriptionModelDetails(
            domain="GENERIC", language_code=language_code
        )
        OBJECT_LOCATION = ObjectLocation(
            namespace_name=NAMESPACE,
            bucket_name=input_bucket,
            object_names=file_names,
        )
        INPUT_LOCATION = ObjectListInlineInputLocation(
            location_type="OBJECT_LIST_INLINE_INPUT_LOCATION",
            object_locations=[OBJECT_LOCATION],
        )
        OUTPUT_LOCATION = OutputLocation(
            namespace_name=NAMESPACE, bucket_name=output_bucket, prefix=job_prefix
        )

        transcription_job_details = CreateTranscriptionJobDetails(
            display_name=display_name,
            compartment_id=COMPARTMENT_ID,
            description="",
            model_details=MODE_DETAILS,
            input_location=INPUT_LOCATION,
            output_location=OUTPUT_LOCATION,
        )

        return transcription_job_details

    def create_transcription_job(self, transcription_job_details):
        transcription_job = self.ai_client.create_transcription_job(
            create_transcription_job_details=transcription_job_details
        )

        return transcription_job

    def wait_for_job_completion(self, job_id):
        """
        wait for the transcription job to complete
        and return the final status
        """
        status = "ACCEPTED"

        # here we start a loop until the job completes
        i = 1
        while status in ["ACCEPTED", "IN_PROGRESS"]:
            print(f"Waiting for job to complete, elapsed: {i*SLEEP_TIME} s....")
            time.sleep(SLEEP_TIME)

            current_job = self.ai_client.get_transcription_job(job_id)
            status = current_job.data.lifecycle_state
            i += 1

        # final status
        print()
        print(f"JOB final status is: {status}")
        print()

        return status
