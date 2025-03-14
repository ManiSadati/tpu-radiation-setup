import argparse
import os
import re
import sys
import csv

import matplotlib.pyplot as plt
import matplotlib.patches as patches


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

parser.add_argument('--log_filename', dest='triumf_log_filename', type=str,
                    default="TNF_July2024_Paolo_Neutron.csv", help='Filename for log from TRIUMF')


args = parser.parse_args()


# Constants
TRIUMF_LOG_REPO = args.triumf_log_repo
TRIUMF_LOG_FILENAME = args.triumf_log_filename
NEUTRON_COUNT_THRESHOLD = args.neutron_count_threshold


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


def count_all_files(word, folder, acctime, sdc, rasp_id):
    triumf_dict = read_triumf_log()
    minutes_in_hour = 60
    neutron_count_dict = {}

    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            occurrences = count_SDCs(word, filepath)
            time = count_last_acctime(filepath)

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

            benchmark = filename[20:].split('.')[0]


    neutron_count_key = []
    neutron_count_values = []

    first_key_num_timestamps = 14
    first_key = True

    for key in sorted(neutron_count_dict):
        neutron_count_key.append(key)

        if first_key:
            neutron_count_values.append(neutron_count_dict[key]/first_key_num_timestamps)
            first_key = False
        else:
            neutron_count_values.append(neutron_count_dict[key]/60)


    fig, ax = plt.subplots()
    ax.plot(neutron_count_key, neutron_count_values, linewidth=2)
    ax.set(ylim=(0,1600))
    plt.xlim(left=0, right=len(neutron_count_values)-1)
    plt.xticks(rotation=90, ha="center", fontsize=8)
    plt.xlabel("Timestamp", fontsize=14)
    plt.ylabel("Average Neutron Monitor Count per Hour", fontsize=14)

    rect = patches.Rectangle((19, 0), 7, 1410, linewidth=1, edgecolor='b', facecolor='r', alpha=0.5)
    ax.add_patch(rect)

    rect2 = patches.Rectangle((39, 0), 3, 1440, linewidth=1, edgecolor='b', facecolor='r', alpha=0.5)
    ax.add_patch(rect2)

    plt.savefig('graphs/neutron_count_noise_removal.pdf', bbox_inches='tight')
    #plt.show()


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


    for rasp_id in rasp_list:
        folder_path = os.path.join(TRIUMF_LOG_REPO, "logs/rasp4-coral" + rasp_id)
        word_to_search = 'SDC'

        count_all_files(word_to_search, folder_path, acctime, sdc, rasp_id)


if __name__ == "__main__":
    main()

