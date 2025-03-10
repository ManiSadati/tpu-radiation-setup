import argparse
import os
import re
import sys
import csv
import statistics
import numpy as np


parser = argparse.ArgumentParser()

parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                    help='Verbosity')

parser.add_argument('-n', '--log_number', dest='log_number', type=int, default=0,
                    help='Integer for log number or empty for all logs')

parser.add_argument('-t', '--threshold', dest='neutron_count_threshold', type=int, default=1,
                    help='Minimum Neutron Count Threshold')

parser.add_argument('--logits_repo', dest='logits_repo', type=str,
                    default=os.path.expanduser("~/vit_models/logits_from_corrupted"),
                    help='Repository for logits')

parser.add_argument('-b', '--benchmark_name', dest='benchmark_name', type=str,
                    default="run_main_block_from_image_v16", help='Microbenchmark name')


args = parser.parse_args()


# Constants
LOGITS_REPO = args.logits_repo
NEUTRON_COUNT_THRESHOLD = args.neutron_count_threshold


total_critical_sdcs = 0


def read_golden_arr(benchmark_name):
    benchmark_golden_dict = {
        "run_main_block_from_image_v16": "vit_base_16_golden_MAIN_BLOCK_TO_LOGITS.npy",
        "run_mha_from_image_v16": "vit_base_16_golden_MHA_from_image_TO_LOGITS.npy",
        "run_patch_encoding_v16": "vit_base_16_golden_PATCH_ENCODING_TO_LOGITS.npy",
        "run_patch_encoding_v8": "vit_base_8_golden_PATCH_ENCODING_TO_LOGITS.npy",
        "run_mha_from_image_v8": "vit_base_8_golden_MAIN_BLOCK_TO_LOGITS.npy",
        "run_main_block_from_image_v8": "vit_base_8_golden_MHA_from_image_TO_LOGITS.npy",
    }

    golden_filepath = LOGITS_REPO + "/golden/" + benchmark_golden_dict[benchmark_name]

    with open(golden_filepath, 'r') as f:
        golden_np = np.load(golden_filepath)
        return golden_np


def count_critical_SDCs(filename, img_id, golden_arr):
    count_critical_sdc = 0

    with open(filename, 'r') as f:
        predicted_np = np.load(filename)

    golden = np.argmax(golden_arr[img_id])
    predicted = np.argmax(predicted_np)

    if golden != predicted:
        print("Golden = ", golden, "\tPredicted = ", predicted)
        count_critical_sdc += 1

    return count_critical_sdc


def convert_to_timestamp(year, month, day, hour, minutes, seconds):
    return f"{year}-{month}-{day} {hour}:{minutes:02d}:00"


def count_all_files(folder, rasp_id, benchmark_name, golden_arr):
    global total_critical_sdcs

    exclude_timestamps_str = ["2024-07-28 13:00:00", "2024-07-28 14:00:00",
                              "2024-07-28 15:00:00", "2024-07-28 16:00:00",
                              "2024-07-30 06:00:00", "2024-07-30 07:00:00",
                              "2024-07-30 08:00:00"]
    exclude_timestamps = []

    for timestamp in exclude_timestamps_str:
        exclude_timestamps.append(timestamp)

    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath) and benchmark_name in filename:

            m = re.search(r"ID_(\d+)_LOG_FILE_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(.*)", filename)
            img_id, year, month, day, hour, minutes, seconds, detail = m.groups()

            hour_timestamp = convert_to_timestamp(year, month, day, hour, 0, 0)

            if hour_timestamp in exclude_timestamps:
                continue

            total_critical_sdcs += count_critical_SDCs(filepath, int(img_id), golden_arr)


def main():
    rasp_list = []

    if args.log_number == 1:
        rasp_list.append("")
    elif args.log_number == 2:
        rasp_list.append("2")
    else:
        rasp_list = ["","2"]

    benchmark_name = args.benchmark_name
    golden_arr = read_golden_arr(benchmark_name)

    for rasp_id in rasp_list:
        folder_path = os.path.join(LOGITS_REPO, "rasp4-coral" + rasp_id)
        count_all_files(folder_path, rasp_id, benchmark_name, golden_arr)

    print("\nCritical SDCs = ", total_critical_sdcs)

if __name__ == "__main__":
    main()

