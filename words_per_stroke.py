#!/usr/bin/python

import sys

# Plover setup
from plover.config import CONFIG_FILE, Config
from plover.registry import registry
from plover import system
from plover.dictionary.base import create_dictionary, load_dictionary

def setup():
    config = Config()
    config.target_file = CONFIG_FILE
    with open(config.target_file, 'rb') as f:
        config.load(f)
        registry.load_plugins()
        registry.update()
        system_name = config.get_system_name()
        system.setup(system_name)


setup()

from argparse import ArgumentParser
import log_reader
import plover.formatting


arg_parser = ArgumentParser(description="Calculate strokes per word in plover logs.")
arg_parser.add_argument("logs", nargs="+", help="log file paths")
arg_parser.add_argument("-r", "--resume", help="start recording after encountering this translation")
arg_parser.add_argument("-s", "--suspend", help="stop recording when encountering this translation")
args = arg_parser.parse_args()

log = []
for log_file in args.logs:
    with open(log_file) as data_file:
        log += data_file.readlines()

UNDO_PREFIX = "{UNDO} "


actions_buffer = []

stroke_count = 0
character_count = 0

def process_translation(undo_translations, translation, is_undo):
    global actions_buffer

    global stroke_count
    global character_count


    if not is_undo:
        stroke_count += 1

    for translation_ in undo_translations:
        actions = plover.formatting._translation_to_actions(
            translation_.translation,
            actions_buffer[-1] if len(actions_buffer) > 0 else plover.formatting._Action(),
            False)

        for action in reversed(actions):
            if action == actions_buffer[-1]:
                actions_buffer.pop()
                character_count -= len(action.text)
            else:
                # Error undoing actions
                break

    actions = plover.formatting._translation_to_actions(
        translation.translation,
        actions_buffer[-1] if len(actions_buffer) > 0 else plover.formatting._Action(),
        False)

    actions_buffer += actions

    for action in actions:
        character_count += len(action.text)

log_reader.process_log(log, process_translation, args.resume, args.suspend)

word_count = character_count*0.2

print("Strokes per word = "
    + (str(float(stroke_count)/word_count) if character_count > 0 else "n/a")
    + " (" + str(stroke_count) + "/" + str(word_count) + ")")
