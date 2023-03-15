#
# process librispeech
#
import argparse
import pandas as pd


def parser_add_args(parser):
    parser.add_argument(
        "--input_file",
        type=str,
        required=True,
        help="input file name",
    )

    return parser


def print_args(args):
    print()
    print("*** Command line arguments ***")
    print(f"INPUT_FILE: {args.input_file}")
    print()


def add_extension(txt):
    return txt + ".flac"


#
# Main
#

# command line parms
parser = argparse.ArgumentParser()
parser = parser_add_args(parser)
args = parser.parse_args()
print_args(args)

colnames = ["file_name", "txt"]
df_input = pd.read_fwf(args.input_file, index_col=False, header=None, names=colnames)

# add ".flac"
df_input["file_name"] = df_input["file_name"].apply(add_extension)

# save as csv
df_input.to_csv("expected.csv", index=None)
