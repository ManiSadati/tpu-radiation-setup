import os
import re

def count_SDCs(word, filename):
    count = 0
    with open(filename, 'r') as file:
        for line in file:
            count += line.lower().count(word.lower())
    return count

def count_last_ACCtime(filename):
    total = 0
    with open(filename, 'r') as file:
        for line in file:
            if 'AccTime' in line:
                tmp = line.split(":")
                total = float(tmp[-1][:-2])
    return total
# IT 25820 KerTime:0.0258635 AccTime:690.6069257

acctime = {}
sdc = {}
def count_all_files(word, folder):
    # 2024_07_26_13_53_26_run_patch_encoding_v16_ECC_OFF_rasp4-coral
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):  
            occurrences = count_SDCs(word, filepath)
            time = count_last_ACCtime(filepath)
            print(f"{filename}: {occurrences} / {time}")
            m = re.match(r"(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(.*)", filename)
            year, month, day, hour, minutes, seconds, detail = m.groups()
            print(day, month, year, hour, minutes, seconds, detail)
            day  = int(day)
            hour = int(hour)
            if day <= 26 or (day == 27 and hour < 18):
                print("YES")
                continue
            if filename[20:] in acctime:
                acctime[filename[20:]].append(time)
                sdc[filename[20:]].append(occurrences)
            else:
                acctime[filename[20:]] = [time]
                sdc[filename[20:]] = [occurrences]


folder_path = '/home/mani/triumf/triumf24-logs/logs/rasp4-coral'
word_to_search = 'SDC'
count_all_files(word_to_search, folder_path)
for v in acctime.keys():
    print("----------------")
    print("***",v, sum(acctime[v]), sum(sdc[v]))
    # print(v, acctime[v], sdc[v])
