#
# Check the sample rate for all files in a dir
#
import argparse
from os import path
import glob

from utils import check_sample_rate

from config import (
    COMPARTMENT_ID,
    NAMESPACE,
    EXT,
    JSON_EXT,
    WAV_DIR,
    JSON_DIR,
    DEBUG,
)


def parser_add_args(parser):
    parser.add_argument(
        "--wav_dir",
        type=str,
        required=True,
        help="Input wav files directory",
    )
    parser.add_argument(
        "--sample_rate",
        type=str,
        required=True,
        help="Expected sample rate (es: 16000)",
    )

    return parser


parser = argparse.ArgumentParser()
parser = parser_add_args(parser)
args = parser.parse_args()

WAV_DIR = args.wav_dir
SAMPLE_RATE = int(args.sample_rate)

print()
print("Checking the sampling rate of audio files..")
print(f"Expected sample_rate is: {SAMPLE_RATE}")
print()

list_wav = sorted(glob.glob(path.join(WAV_DIR, f"*.{EXT}")))

for f_name in list_wav:
    is_ok = check_sample_rate(f_name, SAMPLE_RATE)
    print(f"Checking {f_name}, OK: {is_ok}")

print()
