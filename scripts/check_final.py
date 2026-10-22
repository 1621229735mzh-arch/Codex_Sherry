"""Run the bundled exact-byte cleanup/validation and produce final QA sheets."""
from pathlib import Path
import subprocess
import sys
import json
import hashlib

import argparse
from paths import skill_scripts
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run-dir', type=Path, required=True)
parser.add_argument('--skill-dir', type=Path)
args = parser.parse_args()
ROOT = args.run_dir.expanduser().resolve()
SKILL = skill_scripts(args.skill_dir)
def run(script,*args):
    command=[sys.executable,str(SKILL/script),*map(str,args)]
    p=subprocess.run(command,capture_output=True,text=True,encoding='utf8',errors='replace')
    (ROOT/'qa'/f'{script}.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf8')
    if p.returncode:
        print(p.stdout[-5000:]);print(p.stderr[-1000:]);raise SystemExit(p.returncode)
    print(script,'ok')

raw=ROOT/'final/spritesheet-extended-raw.png'
atlas=ROOT/'final/spritesheet-extended.png'
stamp=ROOT/'qa/despill-once.json'
source_hash=hashlib.sha256(raw.read_bytes()).hexdigest()
if stamp.exists():
    record=json.loads(stamp.read_text(encoding='utf8'))
    if record['source_sha256']!=source_hash:raise RuntimeError('New source requires a new named final candidate; do not repeat cleanup blindly')
else:
    run('despill_chroma_edges.py',raw,'--output',atlas,'--json-out',ROOT/'qa/chroma-despill-extended.json','--chroma-key','#00FF00')
    stamp.write_text(json.dumps({'source_sha256':source_hash,'final_sha256':hashlib.sha256(atlas.read_bytes()).hexdigest()},indent=2),encoding='utf8')
run('validate_atlas.py',atlas,'--require-v2','--chroma-key','#00FF00','--json-out',ROOT/'final/validation-extended.json')
run('make_contact_sheet.py',atlas,'--output',ROOT/'qa/final-contact.png')
run('make_direction_qa_sheet.py',atlas,'--output',ROOT/'qa/look-directions.png')
run('measure_direction_continuity.py',atlas,'--json-out',ROOT/'qa/look-continuity.json')
run('make_direction_blind_qa_sheet.py',atlas,'--output',ROOT/'qa/blind-directions.png','--answer-key',ROOT/'qa/blind-answer-key.json')
from PIL import Image
blind=Image.open(ROOT/'qa/blind-directions.png')
for part,(start,end) in enumerate([(0,5),(5,10),(10,14)],1):
    blind.crop((0,start*236,384,end*236)).save(ROOT/'qa'/f'blind-part-{part}.png')
print(json.dumps({'validation':json.loads((ROOT/'final/validation-extended.json').read_text(encoding='utf8')).get('ok'),'atlas_bytes':atlas.stat().st_size,'final_sha256':hashlib.sha256(atlas.read_bytes()).hexdigest()}))
