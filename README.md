# OCI Speech Demos
![UI demo2](./ui_printscreen.png)

## Introduction.
OCI Speech is an OCI AI service that applies automatic speech recognition technology to transform audio-based content into text. 
Developers can easily make API calls to integrate OCI Speech’s pre-trained models into their applications. OCI Speech can be used for accurate, 
text-normalized, time-stamped transcription via the console and REST APIs as well as command-line interfaces or SDKs. You can also use OCI 
Speech in an OCI Data Science notebook session. With OCI Speech, you can filter profanities, get confidence scores for both single words 
and complete transcriptions, and more. 

## Contents.
This repository contains all the work done for demos on **OCI Speech Service**

Using OCI Speech Service you can easily get accurate transcription of speech contained in audio files.

You can take a set of audio files (wav, flac format), upload these files to a bucket in the OCI Object Storage and
get json files containing the transcriptions, in few minutes.

In this repository you will find examples and demos showing how to use **OCI Python SDK** to easily transcribe the audio files.

## Languages Supported
OCI Speech support the following languages:
* English
* US English
* Spanish
* Italian
* French
* German
* Hindi
* Portuguese

Demos in this repository have been tested using: English, Italian languages.

## Input format
OCI Speech supports not only **wav** format, but also: **mp3, ogg, oga, webm, ac3, aac, mp4a, flac, amr**.

Demos in this repository have been tested using **wav, flac** format. 

## Demos:
* [demo1](./demo1_main.py): command line demo, takes a list of wav/flac files from a local directory, transcribe the audio and output the result to the screen and csv
* [demo2](./demo2.py): a UI, built with Streamlit, enables you to upload a set of audio files and get back the trascriptions; Supports wav and flac formats.
* [demo3](./demo3.py): Compute WER.

I have provided shell file (.sh) to show how to correctly launch the demos.

## Demo Features
In [demo1](./demo1.py) you can see how-to: 
* copy a set of wav files to Object Storage
* **launch an OCI Speech transcription job**
* wait for the job to complete
* **extract the transcription** from the produced json files.
* save transcriptions to csv

In [demo2](./demo2.py) you can see how-to:
* create a UI for OCI Speech, using [Streamlit](https://streamlit.io/)
* **launch a transcription job**
* **extract the transcription** from the produced json files.

In [SpeechClient](./speech_client.py):
* how-to wait for the job to complete

In [utils](./utils.py):
* check audio file sampling rate
* clean a remote bucket
* copy files to/from Object Storage

## Sampling rate
* For all languages **16 Khz** is supported. 
* For some languages (english, spanish...) it is also supported 8 Khz.

If you want to check the sampling rate of your files, you can use the utility provided [here](./check_sample_rate.py).

## Configuration
To be able to use OCI Speech and the demos provided some configuration is needed.

If you want to launch the demo from your laptop you need to have created the keys-pair, to be setup in $HOME/.oci directory

For more details on the needed configuration, see the [Wiki]8https://github.com/luigisaetta/oci-speech-demos/wiki).

## Dependencies
* oci
* ocifs
* Streamlit
* soundfile
* tqdm
* Pandas

The steps needed to create a dedicated conda environment are listed in the [Wiki page](https://github.com/luigisaetta/oci-speech-demos/wiki/Creating-a-conda-env).

## Quotes
The **sentence** that you see last in the picture is from the book "La misura del tempo", G. Carofiglio, p. 119 in the italian edition.

## References.
This repository has been linked in the Oracle Technology Organization GitHub repo.
See [here](https://github.com/oracle-devrel/technology-engineering/tree/main/app-dev/ai-cloud-services/ai-speech) 
