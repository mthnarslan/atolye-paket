import sys, shutil, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import sf, sf_scenes as S
d = Path(__file__).parent / 'work' / '_tpl'; (d / 'compositions').mkdir(parents=True, exist_ok=True)
A = sf.SAMPLE
if not (d / 'assets').exists():
    (d / 'assets').mkdir(); shutil.copytree(A / 'fonts', d / 'assets/fonts'); shutil.copytree(A / 'img', d / 'assets/img'); (d / 'assets/clips').mkdir()
    for n, f in (('a', 'flow/f02_tornado.mp4'), ('b', 'footage/a.mp4')):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(A / f), '-t', '6', '-an', '-vf', 'scale=1280:720,fps=25', '-c:v', 'libx264', '-preset', 'veryfast', str(d / f'assets/clips/{n}.mp4')])
for f in ('hyperframes.json', 'package.json'): shutil.copy(A.parent / f, d / f)
sc = [
 dict(type='number', kicker='May 21, 2024', number='300', unit='MPH', label='Radar-measured winds', sub='Doppler on Wheels', at=0),
 dict(type='document', header='NATIONAL WEATHER SERVICE · DES MOINES', title='DAMAGE SURVEY — GREENFIELD, IA', lines=[['RATING', 'EF4'], ['PEAK WIND', '185 MPH'], ['PATH', '44 MI'], ['DEATHS', '5']], ring=0, strike=None, note='only EF4?'),
 dict(type='print_number', clips=['a'], number='2,250', unit='FT', label='Path width', source='NWS survey', at=0),
 dict(type='map', kicker='The path', title='Southwest Iowa', stops=['Prescott', 'Corning', 'Greenfield', 'Lorimor'], note='44 miles'),
 dict(type='compare', kicker='Two measures', title='Radar vs survey', items=[['Radar', 309, '309 MPH'], ['Survey', 185, '185 MPH']]),
 dict(type='statement', kicker='The record', text='NOT AN EF5', strike='the strongest ever'),
 dict(type='title', kicker='PART III', title='THE RADAR', subtitle='what the truck saw'),
 dict(type='monitor', clips=['b'], kicker='Doppler on Wheels', line='Scan at 3:39 PM'),
 dict(type='full', clips=['a', 'b'], kicker='Greenfield, Iowa', line='The town of 2,000'),
 dict(type='print', clips=['b', 'a'], kicker='Exhibit', line='Wind turbines down'),
 dict(type='datetime', kicker='Tuesday', time='3:39 PM', line='The tornado reaches town'),
 dict(type='questions', items=['Why EF4?', 'What did the radar measure?']),
 dict(type='memorial', text='In memory of the 5 people killed.'),
 dict(type='endcard'),
]
hosts = []; a = 0
for k, x in enumerate(sc):
    x.update(a=a, d=4.5, beats=[0, 2.2])
    sid = f's{k:02d}'; comp, ev = S.render_scene(sid, x, [f'assets/clips/{c}.mp4' for c in x.get('clips', [])])
    (d / 'compositions' / f'{sid}.html').write_text(comp, encoding='utf8')
    hosts.append(f'<div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{a}" data-duration="4.5" data-track-index="1" data-width="1920" data-height="1080" style="z-index:1"></div>')
    a += 4.5
(d / 'compositions/chrome.html').write_text(sf.chrome_comp('CASE FILE 04 · GREENFIELD IOWA', a), encoding='utf8')
(d / 'index.html').write_text(sf.index_html('\n'.join(hosts), a, a), encoding='utf8')
print('ok', a)
