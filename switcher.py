#!/bin/env python3

import subprocess
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--reverse", help="Cycle through PA sinks in reverse order", action="store_true")
args = parser.parse_args()
if args.reverse:
    print("reverse enabled")


cp =  subprocess.run(["pactl", "list", "short", "sink-inputs"], capture_output=True, env={"XDG_RUNTIME_DIR":"/run/user/1001"}) 
so = cp.stdout.decode("utf-8")
lines = so.split('\n')


# build map of connections of sink-inputs (these are like audio streams; things you listen to) and sinks
# that can play them - like headphone sockets, HDMI connections, built in speakers, etc.
# Each application might have one or more streams. Like firefox playing a youtube video, eg.
sinkmap = [] 
sink_inputs = []
for l in lines:
    fields = l.split('\t') 
    if len(fields) == 5:
        sink_input = fields[0]
        sink = fields[1] 
        if sink_input.isnumeric() and sink.isnumeric():
            sinkmap.append([int(sink_input), int(sink)])

print(sinkmap)
# Now build a list of sink indices. 
cp =  subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, env={"XDG_RUNTIME_DIR":"/run/user/1001"}) 
so = cp.stdout.decode("utf-8")
lines = so.split('\n')

sinks = []
for l in lines:
    i = l.split('\t')[0]
    if i.isnumeric():
        sinks.append(int(i))
print(sinks)


print("First sink_input {} is currently connected to sink {}".format( sinkmap[0][0], sinkmap[0][1]))
if args.reverse:
    next_sink_index = sinks.index(sinkmap[0][1]) - 1
    if next_sink_index == -1:
        next_sink_index = len(sinks) - 1
else:
    next_sink_index = sinks.index(sinkmap[0][1]) + 1
    if next_sink_index == len(sinks):
        next_sink_index = 0;

next_sink = sinks[next_sink_index]
print("Moving all inputs to next_sink: {}".format(next_sink))

def move_sink_input(sink_input, sink):
    print ("Moving sink-input {} to sink {}".format(sink_input, next_sink))
    subprocess.run(["pactl", "move-sink-input", str(sink_input), str(sink)], env={"XDG_RUNTIME_DIR":"/run/user/1001"})

for s in sinkmap:
    move_sink_input(s[0], next_sink)
    
#set default sink so it's easy to set volume
subprocess.run(["pactl", "set-default-sink", str(next_sink)], capture_output=True, env={"XDG_RUNTIME_DIR":"/run/user/1001"})
