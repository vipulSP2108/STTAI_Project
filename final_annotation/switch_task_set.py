#!/usr/bin/env python3
"""Helper script to toggle between 19 newly added files vs all 33 files in P21 + P22."""
import os, sys, json, sqlite3
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
final_ann = os.path.join(base_dir, 'final_annotation')

mode = sys.argv[1] if len(sys.argv) > 1 else '19_new'

for annotator_id in ['annotator_1', 'annotator_2']:
    ann_dir = os.path.join(final_ann, annotator_id)
    rec_dir = os.path.join(ann_dir, 'records')
    db_path = os.path.join(ann_dir, 'data', 'label_studio.sqlite3')
    
    tasks = []
    task_id = 1
    
    if mode == '33_all':
        # All P21 + P22
        for fld in ['P21', 'P22']:
            fld_path = os.path.join(rec_dir, fld)
            for f in sorted(os.listdir(fld_path)):
                if f.endswith('.wav'):
                    rel_p = f'final_annotation/{annotator_id}/records/{fld}/{f}'
                    tasks.append({'id': task_id, 'data': {'audio': f'/data/local-files/?d={rel_p}', 'speaker_id': fld, 'file_name': f, 'clip_id': f'{fld}_{task_id}'}})
                    task_id += 1
    else:
        # 19 new files
        p21_new = [
            'WhatsApp Ptt 2026-11-06 at 2.35.34 PM.wav',
            'WhatsApp Ptt 2026-11-06 at 2.36.04 PM.wav',
            'WhatsApp Ptt 2026-11-06 at 2.36.31 PM.wav',
            'WhatsApp Ptt 2026-11-06 at 2.37.16 PM.wav'
        ]
        for f in p21_new:
            rel_p = f'final_annotation/{annotator_id}/records/P21/{f}'
            tasks.append({'id': task_id, 'data': {'audio': f'/data/local-files/?d={rel_p}', 'speaker_id': 'P21', 'file_name': f, 'clip_id': f'P21_{task_id}'}})
            task_id += 1
            
        p22_dir = os.path.join(rec_dir, 'P22')
        for f in sorted(os.listdir(p22_dir)):
            if f.endswith('.wav'):
                rel_p = f'final_annotation/{annotator_id}/records/P22/{f}'
                tasks.append({'id': task_id, 'data': {'audio': f'/data/local-files/?d={rel_p}', 'speaker_id': 'P22', 'file_name': f, 'clip_id': f'P22_{task_id}'}})
                task_id += 1

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('DELETE FROM task WHERE project_id = 1')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    for t in tasks:
        cur.execute('''INSERT INTO task (id, data, created_at, updated_at, is_labeled, project_id, meta, overlap, inner_id, total_annotations, cancelled_annotations, total_predictions, comment_count, unresolved_comment_count, allow_skip) VALUES (?, ?, ?, ?, 0, 1, '{}', 1, ?, 0, 0, 0, 0, 0, 1)''', (t['id'], json.dumps(t['data']), now, now, t['id']))
    conn.commit()
    conn.close()
    print(f'{annotator_id}: Loaded {len(tasks)} tasks (mode: {mode}).')

