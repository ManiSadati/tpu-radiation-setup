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

parser.add_argument('--log_repo', dest='triumf_log_repo', type=str,
                    default=os.path.expanduser("~/triumf24-logs"),
                    help='Repository for TRIUMF logs')

parser.add_argument('--golden_repo', dest='golden_repo', type=str,
                    default=os.path.expanduser("~/tpu-rad-triumf"),
                    help='Repository for golden repo')

parser.add_argument('-b', '--benchmark_name', dest='benchmark_name', type=str,
                    default="run_base_vit_8", help='Benchmark name')

parser.add_argument('--log_filename', dest='triumf_log_filename', type=str,
                    default="TNF_July2024_Paolo_Neutron.csv", help='Filename for log from TRIUMF')


args = parser.parse_args()


# Constants
TRIUMF_LOG_REPO = args.triumf_log_repo
GOLDEN_REPO = args.golden_repo
TRIUMF_LOG_FILENAME = args.triumf_log_filename
NEUTRON_COUNT_THRESHOLD = args.neutron_count_threshold


total_critical_sdcs = 0

def count_critical_SDCs(filename, benchmark_name):
    benchmark_golden_dict = {
        "run_base_vit_8": "vit_base_8_golden.npy",
        "run_base_vit_16": "vit_base_16_golden.npy",
        "run_final_block_v16": "vit_base_16_golden_FINAL_BLOCK.npy",
    }
    count = 0
    SDC = "sdc"
    INDEX = "index"
    PERF = "perf"

    count_critical_sdc = 0

    with open(filename, 'r') as f:
        golden_filepath = GOLDEN_REPO + "/tpu/data/golden/" + benchmark_golden_dict[benchmark_name]
        golden_np = np.load(golden_filepath)

        golden_arr = None
        predicted_arr = None
        golden = None
        predicted = None

        sdc_begin = False

        for line in f:
            sdc_count = line.lower().count(SDC)
            index_count = line.lower().count(INDEX)
            perf_count = line.lower().count(PERF)

            if sdc_count > 0 and not sdc_begin:
                image_index = int(line.split(':')[1])
                sdc_begin = True
                golden_arr = golden_np[image_index][0]
                predicted_arr = np.copy(golden_arr)
                golden = np.argmax(golden_arr)
            elif index_count > 0 and sdc_begin:
                arr_sdc_index = int(line.split('index:')[1].split(' ')[0])
                arr_orig_value = float(line.split('e:')[1].split(' ')[0])
                arr_sdc_value = float(line.split('r:')[1])
                predicted_arr[arr_sdc_index] = arr_sdc_value
            elif perf_count > 0 and sdc_begin:
                predicted = np.argmax(predicted_arr)
                sdc_begin = False

                if golden != predicted:
                    count_critical_sdc += 1

    return count_critical_sdc


def count_SDCs(word, filename):
    count = 0
    with open(filename, 'r') as f:
        for line in f:
            count += line.lower().count(word.lower())
    return count


def count_last_acctime(filename):
    total = 0
    with open(filename, 'r') as f:
        for line in f:
            if 'AccTime' in line:
                tmp = line.split(":")
                total = float(tmp[-1][:-2])
    return total


def read_triumf_log():
    with open(TRIUMF_LOG_REPO + "/" + TRIUMF_LOG_FILENAME, mode='r') as f:
        next(f)
        reader = csv.reader(f)
        triumf_dict = {rows[0]:int(rows[1]) for rows in reader}
        return triumf_dict


def convert_to_timestamp(year, month, day, hour, minutes, seconds):
    return f"{year}-{month}-{day} {hour}:{minutes:02d}:00"


def count_all_files(word, folder, acctime, sdc, rasp_id, benchmark_name):
    global total_critical_sdcs

    triumf_dict = read_triumf_log()
    minutes_in_hour = 60
    neutron_count_dict = {}

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
            occurrences = count_SDCs(word, filepath)
            time = count_last_acctime(filepath)
            total_critical_sdcs += count_critical_SDCs(filepath, benchmark_name)

            if args.verbose:
                print(f"{filename}: {occurrences} / {time}")

            m = re.match(r"(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(.*)", filename)
            year, month, day, hour, minutes, seconds, detail = m.groups()

            neutron_count_per_hour = 0

            for minute_i in range(minutes_in_hour):
                timestamp = convert_to_timestamp(year, month, day, hour, minute_i, 0)
                if timestamp in triumf_dict:
                    neutron_count_per_hour += triumf_dict[timestamp]

            hour_timestamp = convert_to_timestamp(year, month, day, hour, 0, 0)
            neutron_count_dict[hour_timestamp] = neutron_count_per_hour

            if hour_timestamp in exclude_timestamps:
                continue

            benchmark = filename[20:].split('.')[0]

            if rasp_id:
                benchmark = benchmark[:-1]

            if benchmark in acctime:
                acctime[benchmark].append(time)
                sdc[benchmark].append(occurrences)
            else:
                acctime[benchmark] = [time]
                sdc[benchmark] = [occurrences]


def main():
    acctime = {}
    sdc = {}
    rasp_list = []

    if args.log_number == 1:
        rasp_list.append("")
    elif args.log_number == 2:
        rasp_list.append("2")
    else:
        rasp_list = ["","2"]

    benchmark_name = args.benchmark_name

    for rasp_id in rasp_list:
        folder_path = os.path.join(TRIUMF_LOG_REPO, "logs/rasp4-coral" + rasp_id)
        word_to_search = 'SDC'

        count_all_files(word_to_search, folder_path, acctime, sdc, rasp_id, benchmark_name)

    for v in sorted(acctime.keys()):
        print("***",v, sum(acctime[v]), sum(sdc[v]))

    print("Critical SDCs = ", total_critical_sdcs)

if __name__ == "__main__":
    main()

