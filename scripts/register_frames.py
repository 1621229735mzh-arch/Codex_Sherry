"""Register generated row families with one uniform transform per entire row.

Artwork is only resampled and translated. No pose is redrawn, cropped to fill,
or resized independently. Preserve every within-row vertical displacement.
Atlas composition and quality validation remain the bundled skill scripts.
"""
import json
from pathlib import Path
from PIL import Image

import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run-dir', type=Path, required=True)
args = parser.parse_args()
ROOT = args.run_dir.expanduser().resolve()
STATES=['idle','running-right','running-left','waving','jumping','failed','waiting','running','review']
out=ROOT/'frames'
out.mkdir(exist_ok=True)
manifest={'ok':True,'chroma_key':{'hex':'#00FF00','rgb':[0,255,0],'threshold':96.0},'rows':[]}
report={'target_standing_height':185,'target_ground':203,'rows':[]}
for state in STATES:
    source=ROOT/'qa/rows'/state/'frames'
    original=json.loads((source/'frames-manifest.json').read_text(encoding='utf8'))
    row=next(x for x in original['rows'] if x['state']==state)
    if row['method']!='components':raise RuntimeError(f'{state}: unapproved extraction')
    images=[Image.open(source/state/p.replace(chr(92), '/').rsplit('/', 1)[-1]).convert('RGBA') for p in row['frames']]
    bounds=[a.getchannel('A').point(lambda x:255 if x>16 else 0).getbbox() for a in images]
    height=max(b[3]-b[1] for b in bounds)
    scale=min(1.0,185/height)
    ground=max(b[3] for b in bounds)
    size=(round(192*scale),round(208*scale))
    offset=((192-size[0])//2,203-round(ground*scale))
    target=out/state;target.mkdir(exist_ok=True)
    paths=[]
    for i,image in enumerate(images):
        normalized=Image.new('RGBA',(192,208))
        normalized.alpha_composite(image.resize(size,Image.Resampling.LANCZOS),offset)
        p=target/f'{i:02}.png';normalized.save(p);paths.append(str(p))
    manifest['rows'].append({'state':state,'frames':paths,'method':'components','source_manifest':str(source/'frames-manifest.json')})
    report['rows'].append({'state':state,'source_height':height,'uniform_scale':scale,'uniform_offset':list(offset),'source_baselines':[b[3] for b in bounds]})
(out/'frames-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
(ROOT/'qa/frame-registration.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report))
