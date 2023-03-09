# OCI Speech Demos
This repository contains all the work done for demos on **OCI Speech Service**

Using OCI Speech Service you can easily get accurate transcription of speech contained in audio files.

You can take a set of audio files (for example, in wav format), upload these files to a bucket in the OCI Object Storage and
get json files containing the transcriptions, in few minutes.

In this repository you will find examples and demo showing how to use Python SDK to easily transcribe the audio files.

## Languages Supported
* English
* US English
* Spanish
* Italian
* French
* German
* Hindi
* Portuguese

## Input format
OCI Speech support not only wav format, but also: mp3, ogg, oga, webm, ac3, aac, mp4a, flac, amr.

## Demos:
* [demo1](./demo1_main.py): takes a list of wav files from a local directory, transcribe the audio and output the result to the screen
* [demo2](./demo2.py): built with Streamlit, enables you to upload a file to the UI and get back the audio trascription

## Sampling rate
For all languages 16 Khz is supported. For some languages (english, spanish...) it is also supported 8 Khz.

## Configuration
To be able to use OCI Speech and the demos provided some configuration is needed.
If you want to launch the demo from your laptop you need to have created the keys-pair, to be setup in $HOME/.oci directory

For more details on the needed configuration, see the Wiki.

## Demo Features
In [demo1](./demo1_main.py) you can see: 
* how to copy a set of wav files to Object Storage
* how to **launch a transcription job**
* how to **wait for job completion**
* how to **extract the transcription** from the produced json files.

## Dependencies
* oci
* ocifs
* Streamlit
* tqdm
