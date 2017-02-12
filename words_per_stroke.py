#!/usr/bin/python

import re
import sys


if len(sys.argv) < 2:
    exit()

with open(sys.argv[1]) as data_file:
    log = data_file.readlines()

start_recording_translation = None
stop_recording_translation = None

if len(sys.argv) >= 3:
    start_recording_translation = sys.argv[2]

if len(sys.argv) >= 4:
    stop_recording_translation = sys.argv[3]


recording = start_recording_translation is None
num_strokes = 0
num_words = 0

for line in log:
    match = re.match(r"""
        ^[0-9\-:, ]*
        (?P<removal>\*?)Translation\(
        \((?P<strokes>[A-Z\-,'* ]*)\)
        \s* : \s*
        \"(?P<translation>(?:[^\\\"]|(?:\\\\)*\\[^\"]|(?:\\\\)*\\\")*)\"
        \)
        """,
        line,
        re.VERBOSE)

    if match:
        removal = match.group("removal") == "*"

        strokes = match.group("strokes").split(",")
        words = re.findall(r"[a-zA-Z\-']*", re.sub(r"{.*}", "", match.group("translation")))

        if match.group("translation") == start_recording_translation:
            recording = True
        elif match.group("translation") == stop_recording_translation:
            recording = False
        elif recording:
            entry_num_strokes = 0
            entry_num_words = 0

            for stroke in strokes:
                if not stroke.isspace() and len(stroke) > 0:
                    entry_num_strokes += 1

            for word in words:
                if not word.isspace() and len(word) > 0:
                    entry_num_words += 1

            if removal:
                num_strokes -= entry_num_strokes
                num_words -= entry_num_words
            else:
                num_strokes += entry_num_strokes
                num_words += entry_num_words

print("Strokes per word = "
    + (str(float(num_strokes)/num_words) if num_words > 0 else "n/a")
    + " (" + str(num_strokes) + "/" + str(num_words) + ")")
