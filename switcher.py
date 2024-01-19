#!/bin/env python3

import subprocess
import argparse
import re


def move_sink_input(sink_input, sink):
    print("Moving sink-input {} to sink {}".format(sink_input, next_sink))
    subprocess.run(["pactl", "move-sink-input", str(sink_input),
                   str(sink)], env={"XDG_RUNTIME_DIR": "/run/user/1001"})


def parse_properties(sinks_output):
    properties_blocks = sinks_output.split('Properties:')
    id_nick_pairs = {}

    for block in properties_blocks:
        lines = block.split('\n')
        object_id = None
        node_nick = None

        for line in lines:
            if 'object.id' in line:
                object_id = line.split('=')[1].strip().strip(
                    '"')  # Remove double quotes
            elif 'node.nick' in line:
                node_nick = line.split('=')[1].strip().strip(
                    '"')  # Remove double quotes

            if object_id and node_nick:
                id_nick_pairs[int(object_id)] = node_nick
                break

    return id_nick_pairs


parser = argparse.ArgumentParser()
parser.add_argument(
    "--reverse", help="Cycle through PA sinks in reverse order", action="store_true")
args = parser.parse_args()
if args.reverse:
    print("reverse enabled")

# Build map of sink ID's and nicknames
cp = subprocess.run(["pactl", "list", "sinks"],
                    capture_output=True, env={"XDG_RUNTIME_DIR": "/run/user/1001"})
so = cp.stdout.decode("utf-8")
nick_map = parse_properties(so)

# build map of connections of sink-inputs (these are like audio streams; things you listen to) and sinks
# that can play them - like headphone sockets, HDMI connections, built in speakers, etc.
# Each application might have one or more streams. Like firefox playing a youtube video, eg.
cp = subprocess.run(["pactl", "list", "short", "sink-inputs"],
                    capture_output=True, env={"XDG_RUNTIME_DIR": "/run/user/1001"})
so = cp.stdout.decode("utf-8")
lines = so.split('\n')

sinkmap = []
sink_inputs = []
for l in lines:
    fields = l.split('\t')
    if len(fields) == 5:
        sink_input = fields[0]
        sink = fields[1]
        if sink_input.isnumeric() and sink.isnumeric():
            sinkmap.append([int(sink_input), int(sink)])

print("sinkmap")
print(sinkmap)
# Now build a list of sink indices.
cp = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, env={
                    "XDG_RUNTIME_DIR": "/run/user/1001"})
so = cp.stdout.decode("utf-8")
lines = so.split('\n')

sinks = []
for l in lines:
    i = l.split('\t')[0]
    if i.isnumeric():
        sinks.append(int(i))
print("sinks:")
print(sinks)


print("First sink_input {} is currently connected to sink {}".format(
    sinkmap[0][0], sinkmap[0][1]))
if args.reverse:
    next_sink_index = sinks.index(sinkmap[0][1]) - 1
    if next_sink_index == -1:
        next_sink_index = len(sinks) - 1
else:
    next_sink_index = sinks.index(sinkmap[0][1]) + 1
    if next_sink_index == len(sinks):
        next_sink_index = 0

next_sink = sinks[next_sink_index]
print("Moving all inputs to next_sink: {}, nickname: {}".format(
    next_sink, nick_map[next_sink]))

id = subprocess.run(["makoctl", "dismiss", "-a"])
id = subprocess.run(["notify-send", "-p", "-t", "2000",
                     "Moving audio sources", nick_map[next_sink]])

for s in sinkmap:
    move_sink_input(s[0], next_sink)

# set default sink so it's easy to set volume
subprocess.run(["pactl", "set-default-sink", str(next_sink)],
               capture_output=True, env={"XDG_RUNTIME_DIR": "/run/user/1001"})
