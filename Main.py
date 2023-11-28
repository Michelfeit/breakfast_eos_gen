import os
import re
import shutil


PATH_BREAKFAST = 'breakfast_set'
PATH_TO_TXT_ONLY = 'breakfast_only_txt'
PATH_PROACTIVE_GOALS = 'proactive_data/test_go.txt'
PATH_TEST_TIMES = 'proactive_data/test_ti.txt'
PATH_TO_EOS_TIMES = 'proactive_data/eos_ti.txt'

# from all the data extract the files of each action without redundancy
def copy_all_necessary_files():
    for folder_path, _, files in os.walk(PATH_BREAKFAST):
        # skip to subfolders (cereals, coffee, ...)
        if(folder_path == PATH_BREAKFAST):
            continue
        
        #match regex to name of the first file in ordere to extract the starting number
        match = re.search(r'P(\d{2})_(cam|webcam)(01|02)_P\1_\w+\.txt$', files[0])
        assert(match)

        current_number = int(match.group(1))
        
        for file_name in files:
            match = re.search(r'P(\d{2})_(cam|webcam)(01|02)_P\1_\w+\.txt$', file_name)
            if(match and int(match.group(1)) > current_number):
                #print(current_number, int(match.group(1)))
                current_number = int(match.group(1))
            pattern = re.compile(fr'^P{current_number:02}_(cam|webcam)(01|02)_P{current_number:02}_\w+\.txt$')
            if(pattern.match(file_name)):
                file_path = os.path.join(folder_path, file_name)
                print("File:", file_path)

                src_file_path = os.path.join(folder_path, file_name)
                relative_path = os.path.relpath(src_file_path, PATH_BREAKFAST)
                dest_file_path = os.path.join(PATH_TO_TXT_ONLY, relative_path)

                os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                shutil.copy2(src_file_path, dest_file_path)
                print(f"File {file_name} copied to {dest_file_path} with updated regex")
                print()
                current_number += 1

# all action sequence times of every goal are extracted into one list.
# at every list entry is a list of all action sequences of the breakfast set
def extract_all_necessary_times():
    subfolder_count = len([f for f in os.listdir(PATH_TO_TXT_ONLY) if os.path.isdir(os.path.join(PATH_TO_TXT_ONLY, f))])
    sequence_times_per_goal = [[0.0]] * subfolder_count

    goal_index = 0
    for folder_path, _, files in os.walk(PATH_TO_TXT_ONLY):
        #skip top folder
        if(len(files) == 0):
            continue
        
        sequence_times_per_goal[goal_index] = []
        for file_name in files:
            path = os.path.join(folder_path, file_name)
            upper_limits = get_action_times(path)
            sequence_times_per_goal[goal_index].append(upper_limits)
        goal_index += 1
    
    # has a list of all sequence times at the index of each goal
    return sequence_times_per_goal

def get_action_times(path):
    action_times = [0.0]
    with open(path, 'r') as file:
        entries = file.readlines()
            
    for entry in entries:
        entry_parts = entry.strip().split(' ')
        if len(entry_parts) == 2:
            range_str, _ = entry_parts
            start, end = map(float, range_str.split('-'))
            action_times.append(end)
    return action_times

# for every entry in test set find the ending time of the last action and save it into a text file where the ending time sits at the line of the corresponding action in the test set
# sequence_times: list of all seuqences ordered in lists corresponding to each goal
def get_proactive_end_times_in_list(sequence_times):
    goal_indeces = _get_goal_increment_indeces()
    eos_times = []

    # iterate over list
    for i in range(len(goal_indeces) - 1):
        # for every entry repeat for the given intervall
        for j in range(goal_indeces[i+1] - goal_indeces[i]):
            index_in_test_set = goal_indeces[i] + j
            test_seq = _get_test_sequence_at_line(index_in_test_set)
            for seq in sequence_times[i]:
                if(_are_sequences_equal(test_seq, seq[:-1])):
                    print(test_seq[-1], seq[-1])
                    assert(test_seq[-1] <= seq[-1])
                    eos_times.append(seq[-1])
    print(eos_times)
    return eos_times

def _get_goal_increment_indeces():
    previous_number = None
    increasing_lines = []

    with open(PATH_PROACTIVE_GOALS, 'r') as file:
        for line_number, line in enumerate(file, start=1):
            current_number = int(line.strip())

            if previous_number is None or current_number > previous_number:
                increasing_lines.append(line_number - 1)
                previous_number = current_number
        increasing_lines.append(line_number)
    return increasing_lines

def _get_test_sequence_at_line(index):
    with open(PATH_TEST_TIMES, 'r') as file:
        lines = file.readlines()

    if 0 <= index < len(lines):
        entry_line = lines[index]
        entry_list = [float(value) for value in entry_line.split()]
        return entry_list
    else:
        return None
    
def _are_sequences_equal(listA, listB):
    if len(listA) != len(listB):
        return False

    # Check element-wise equality
    for a, b in zip(listA, listB):
        if a != b:
            return False
    return True

def save_eos_to_txtfile(times):
    with open(PATH_TO_EOS_TIMES, 'w') as file:
        for value in times:
            file.write(f"{value}\n")

def main():
    #copy_all_necessary_files()
    list_of_bf_times = extract_all_necessary_times()
    eos_times = get_proactive_end_times_in_list(list_of_bf_times)
    save_eos_to_txtfile(eos_times)

if __name__ == "__main__":
    main()