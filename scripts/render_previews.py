"""Render QA artifacts from final encoded pixels; does not draw or alter the pet."""
from pathlib import Path
import json
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
STATES = ['idle', 'running-right', 'running-left', 'waving', 'jumping', 'failed', 'waiting', 'running', 'review']
DURATIONS = [[280,110,110,140,140,320], [120]*7+[220], [120]*7+[220], [140]*3+[280], [140]*4+[280], [140]*7+[240], [150]*5+[260], [120]*5+[220], [150]*5+[280]]

def screen(frame, label):
    result = Image.new('RGB', (320,280), '#f2f2f2')
    ImageDraw.Draw(result).text((12,12), label, fill='#333333')
    result.paste(frame, (64,44), frame)
    return result

def gif(frames, durations, output):
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=durations, loop=0, disposal=2, optimize=False)

import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--image', type=Path, default=ROOT/'assets/sherry.png')
parser.add_argument('--output-dir', type=Path, default=ROOT/'.cache/previews')
args = parser.parse_args()
atlas = Image.open(args.image).convert('RGBA')
if atlas.size != (1536, 2288):
    raise SystemExit('Expected a 1536x2288 v2 sprite sheet')
frames_root = ROOT/'.cache/final-frames'
preview = args.output_dir.expanduser().resolve()
preview.mkdir(parents=True, exist_ok=True)
all_states = []
for row, state in enumerate(STATES):
    path = frames_root/state
    path.mkdir(parents=True,exist_ok=True)
    frames=[]
    for col in range(len(DURATIONS[row])):
        frame=atlas.crop((col*192,row*208,(col+1)*192,(row+1)*208))
        frame.save(path/f'{col:02}.png')
        frames.append(frame)
    all_states.append(frames)
for state, frames, durations in zip(STATES, all_states, DURATIONS):
    gif(frames, durations, preview/f'{state}.gif')

# The installed desktop client multiplies idle durations by six.
idle_durations=[x*6 for x in DURATIONS[0]]
gif([screen(f,'Idle - installed client timing') for f in all_states[0]],idle_durations,preview/'idle-client-timing.gif')
sequence=[]
timings=[]
for row,state in enumerate(STATES):
    sequence.extend(screen(f,state) for f in all_states[row])
    timings.extend(idle_durations if row==0 else DURATIONS[row])
gif(sequence,timings,preview/'all-states.gif')
video=cv2.VideoWriter(str(preview/'all-states.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(320,280))
if not video.isOpened():
    raise RuntimeError('MP4 encoder unavailable')
for frame,duration in zip(sequence,timings):
    bgr=cv2.cvtColor(np.array(frame),cv2.COLOR_RGB2BGR)
    for _ in range(max(1,round(duration*30/1000))):video.write(bgr)
video.release()
jump_frames=[*all_states[0],*all_states[4],*all_states[0]]
gif([screen(f,'Idle -> hover hop -> idle') for f in jump_frames],[*idle_durations,*DURATIONS[4],*idle_durations],preview/'idle-jump-idle.gif')
look=[atlas.crop((col*192,row*208,(col+1)*192,(row+1)*208)) for row in [9,10] for col in range(8)]
gif([screen(f,f'Look {index*22.5:g} deg') for index,f in enumerate(look)],[180]*16,preview/'look-loop.gif')
stills=Image.new('RGB',(192*4,240),'#f2f2f2')
d=ImageDraw.Draw(stills)
for col,row in enumerate([0,4,6,7]):
    f=all_states[row][2 if row==4 else 0]
    stills.paste(f,(col*192,28),f)
    d.text((col*192+8,8),STATES[row],fill='#333333')
stills.save(preview/'four-states.png')
result={'ok':True,'source':args.image.name,'idle_timing':'installed client x6','states':STATES,'mp4_bytes':(preview/'all-states.mp4').stat().st_size}
(preview/'preview-report.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result))
