#!/usr/bin/env python3

import log_reader
from argparse import ArgumentParser


arg_parser = ArgumentParser(description="Calculate strokes per word in plover logs. Outputs to standard out.")
arg_parser.add_argument("logs", nargs="+", help="log file paths")
arg_parser.add_argument("-r", "--resume", help="start recording after encountering this translation")
arg_parser.add_argument("-s", "--suspend", help="stop recording when encountering this translation")
args = arg_parser.parse_args()

log = []
for log_file in args.logs:
    with open(log_file) as data_file:
        log += data_file.readlines()

log_strokes = log_reader.process_log(log, args.resume, args.suspend)

stroke_count = 0
undo_stroke_count = 0
character_count = 0

for log_stroke in log_strokes:
    if log_stroke.stroke == "*":
        undo_stroke_count += 1
    else:
        stroke_count += 1

    for translation in log_stroke.undo_translations:
        character_count -= len(translation.text)

    for translation in log_stroke.do_translations:
        character_count += len(translation.text)

word_count = character_count*0.2

total_stroke_count = stroke_count + undo_stroke_count
net_stroke_count = stroke_count - undo_stroke_count

print((str(float(total_stroke_count)/word_count) if character_count > 0 else "n/a")
    + " stroke/word "
    + " (" + str(stroke_count) + "/" + str(word_count) + ")")

print((str(float(net_stroke_count)/word_count) if character_count > 0 else "n/a")
    + " net stroke/word "
    + " (" + str(net_stroke_count) + "/" + str(word_count) + ")")
