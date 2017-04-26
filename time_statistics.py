#!/usr/bin/env python3

from argparse import ArgumentParser

import log_reader

import datetime
import math
import collections


def speed_filter(strokes, speed_activate, speed_deactivate, sample_duration):
    strokes_buffer = []

    active_periods = []

    activate_time = None

    strokes_i = 0
    while strokes_i < len(strokes):
        popped_stroke = None
        if len(strokes_buffer) > 0 and \
            strokes[strokes_i].time - strokes_buffer[0].time > sample_duration:
            popped_stroke = strokes_buffer[0]
            del strokes_buffer[0]
        else:
            strokes_buffer.append(strokes[strokes_i])
            strokes_i += 1

        speed = len(strokes_buffer)/sample_duration.total_seconds()

        if speed >= speed_activate and activate_time is None:
            activate_time = strokes_buffer[-1].time
        elif speed < speed_deactivate and not activate_time is None:
            deactivate_time = popped_stroke.time
            active_periods.append((activate_time, deactivate_time))
            activate_time = None

    if not activate_time is None:
        deactivate_time = strokes[-1].time
        active_periods.append((activate_time, deactivate_time))
        activate_time = None

    return active_periods

def intersection(a1, a2, b1, b2):
    return (max(a1, b1), min(a2, b2))


class LogStat:
    def __init__(self, period):
        self.period = period

        self.stroke_count = 0
        self.character_count = 0
        self.undo_stroke_count = 0
        self.undo_character_count = 0
        self.active_time = datetime.timedelta(0)

    def add_period(self, period):
        period_intersection = intersection(
            self.period[0], self.period[1],
            period[0], period[1])

        period_intersection_delta = period_intersection[1] - period_intersection[0]

        if period_intersection_delta > datetime.timedelta(0):
            self.active_time += period_intersection_delta

    def add_stroke(self, stroke):
        if stroke.stroke == "*":
            self.undo_stroke_count += 1
        else:
            self.stroke_count += 1

        for translation in stroke.undo_translations:
            self.undo_character_count += len(translation.text)

        for translation in stroke.do_translations:
            self.character_count += len(translation.text)

    def to_csv_row(self, row, add_derived):
        row = str(row)
        return self.period[0].isoformat() + "," \
            + str(self.stroke_count) + "," \
            + str(self.character_count) + "," \
            + str(self.undo_stroke_count) + "," \
            + str(self.undo_character_count) + "," \
            + str(self.active_time.total_seconds()) + "," \
            + (("=B" + row + " + D" + row + "," \
                + "=B" + row + " - D" + row + "," \
                + "=C" + row + " - E" + row + "," \
                + "=I" + row + "/5," \
                + "=G" + row + " / J" + row + "," \
                + "=H" + row + " / J" + row + "," \
                + "=G" + row + " * 60 / F" + row + "," \
                + "=H" + row + " * 60 / F" + row + "," \
                + "=J" + row + " * 60 / F" + row + ","
            ) if add_derived else "")

    @staticmethod
    def csv_header(add_derived):
        return "time," \
            + "strokes," \
            + "characters," \
            + "undo strokes," \
            + "undo characters," \
            + "active time (seconds)," \
            + (("total strokes," \
                + "net strokes," \
                + "net characters," \
                + "net words (characters/5)," \
                + "stroke/word," \
                + "net stroke/word," \
                + "stroke/min," \
                + "net stroke/min," \
                + "net word/min,"
            ) if add_derived else "")


arg_parser = ArgumentParser(description="Measure statistics over time in Plover logs. Outputs as CSV to standard out.")
arg_parser.add_argument("logs", nargs="+", help="log file paths")
arg_parser.add_argument("-r", "--resume", help="start recording after encountering this translation")
arg_parser.add_argument("-s", "--suspend", help="stop recording when encountering this translation")
arg_parser.add_argument("-sa", "--speed_activation", nargs=3, type=float, help="speed to start recording on (stroke/second), speed to stop recording on (stroke/second), length of window to check speed in (seconds)")
arg_parser.add_argument("-w", "--sample-window", required=True, type=float, help="duration of time (seconds) to sample for each discrete statistic")
arg_parser.add_argument("--raw", action="store_true", help="raw statistics only, no derived")
args = arg_parser.parse_args()

log = []
for log_file in args.logs:
    with open(log_file) as data_file:
        log += data_file.readlines()

log_strokes = log_reader.process_log(log, args.resume, args.suspend)

sample_duration = datetime.timedelta(seconds = args.sample_window)

active_periods = [(log_strokes[0].time, log_strokes[-1].time)]
if not args.speed_activation is None:
    active_periods = speed_filter(
        log_strokes,
        args.speed_activation[0],
        args.speed_activation[1],
        datetime.timedelta(seconds = args.speed_activation[2]))

log_stats = []
log_stats.append(LogStat((log_strokes[0].time, log_strokes[0].time + sample_duration)))

stroke_i = 0
for active_period in active_periods:
    while active_period[0] >= log_stats[-1].period[1]:
        log_stats.append(LogStat((
            log_stats[-1].period[1],
            log_stats[-1].period[1] + sample_duration)))

    log_stats[-1].add_period(active_period)

    while log_strokes[stroke_i].time < active_period[0]:
        stroke_i += 1

    while log_strokes[stroke_i].time < active_period[1]:
        stroke = log_strokes[stroke_i]

        while stroke.time >= log_stats[-1].period[1]:
            log_stats.append(LogStat((
                log_stats[-1].period[1],
                log_stats[-1].period[1] + sample_duration)))
            log_stats[-1].add_period(active_period)

        log_stats[-1].add_stroke(stroke)

        stroke_i += 1

print(LogStat.csv_header(not args.raw))
row = 2
for log_stat in log_stats:
    print(log_stat.to_csv_row(row, not args.raw))
    row += 1
