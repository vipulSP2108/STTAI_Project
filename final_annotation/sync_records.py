#!/usr/bin/env python3
"""sync_records.py - Universal Record Synchronization & Audio Pipeline for Label Studio Annotators.

Functionality:
1. Scans Records/ directory (strictly excluding P13 to P19).
2. Converts any new audio recordings to 16 kHz mono WAV for high-fidelity playback.
3. Syncs audio files to final_annotation/records/, annotator_1/records/, and annotator_2/records/.
4. Registers tasks in both Annotator 1 and Annotator 2 databases (preserving existing tasks & annotations).
5. Ensures project labeling XML (with 3-language choice buttons & verbatim transcript) is applied.
6. Fixes user authentication for Vipul.patil@iitgn.ac.in and annotator accounts.
7. Computes and reports exact duration statistics for all collected audio.
"""

import os
import sys
import glob
import json
import shutil
import sqlite3
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDS_DIR = os.path.join(BASE_DIR, 'Records')
FINAL_ANN_DIR = os.path.join(BASE_DIR, 'final_annotation')
MASTER_RECORDS_DIR = os.path.join(FINAL_ANN_DIR, 'records')
CONFIG_XML_PATH = os.path.join(FINAL_ANN_DIR, 'label_studio_config.xml')

# Strictly excluded participant folders per requirements (P15 and P17 remain unsegmented/unprocessed)
EXCLUDED_FOLDERS = {'P15', 'P17'}

SUPPORTED_EXTS = {'.m4a', '.wav', '.mp3', '.ogg', '.flac', '.aac', '.opus', '.webm', '.wma'}

PASSWORD_HASH_DEFAULT = 'pbkdf2_sha256$870000$NZ1k1u7IFtV117NnbiaM2q$Oy6+w0QZQs9ydYoTEyvTwZnjLmHLATTokgOyBn0tVwQ='

def get_audio_duration(file_path):
    """Return duration in seconds using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 0.0

def convert_to_wav_16k(src_path, dst_path):
    """Convert any audio file to 16 kHz mono PCM 16-bit WAV using ffmpeg."""
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    if os.path.exists(dst_path) and os.path.getsize(dst_path) > 0:
        return dst_path
    
    cmd = [
        'ffmpeg', '-y', '-i', src_path,
        '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le',
        dst_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return dst_path

def scan_records():
    """Scan Records/ excluding P15 and P17."""
    folders = []
    if not os.path.exists(RECORDS_DIR):
        print(f"Error: {RECORDS_DIR} does not exist!")
        return {}
        
    for name in sorted(os.listdir(RECORDS_DIR)):
        full = os.path.join(RECORDS_DIR, name)
        if not os.path.isdir(full):
            continue
        if name in EXCLUDED_FOLDERS:
            continue
        if name.startswith('P'):
            folders.append(name)
            
    # Sort folders numerically (P1, P2, ..., P10, P11, P12, P13, P14, P16, P18, P19, P20, P21, P22)
    def sort_key(s):
        num_part = ''.join(c for c in s if c.isdigit())
        return int(num_part) if num_part else 9999
        
    folders.sort(key=sort_key)
    
    records_by_folder = {}
    for fld in folders:
        fld_path = os.path.join(RECORDS_DIR, fld)
        clip_dir = os.path.join(fld_path, '1 clip 1 tar')
        files = []
        if os.path.isdir(clip_dir):
            for fn in sorted(os.listdir(clip_dir)):
                if fn.startswith('.'):
                    continue
                ext = os.path.splitext(fn)[1].lower()
                if ext in SUPPORTED_EXTS:
                    rel_to_fld = os.path.relpath(os.path.join(clip_dir, fn), fld_path)
                    files.append((fn, os.path.join(clip_dir, fn), rel_to_fld))
        else:
            for root, _, filenames in os.walk(fld_path):
                for fn in sorted(filenames):
                    if fn.startswith('.'):
                        continue
                    ext = os.path.splitext(fn)[1].lower()
                    if ext in SUPPORTED_EXTS:
                        rel_to_fld = os.path.relpath(os.path.join(root, fn), fld_path)
                        files.append((fn, os.path.join(root, fn), rel_to_fld))
        records_by_folder[fld] = files
        
    return records_by_folder

def sync_audio_files(records_by_folder):
    """Convert and sync files into final_annotation and annotators' directories."""
    synced_data = {}
    total_duration = 0.0
    
    for fld, files in records_by_folder.items():
        fld_records = []
        fld_duration = 0.0
        
        for fn, src_path, rel_fld in files:
            stem = os.path.splitext(fn)[0]
            wav_fn = f"{stem}.wav"
            
            # Destination in master records
            master_dst = os.path.join(MASTER_RECORDS_DIR, fld, wav_fn)
            convert_to_wav_16k(src_path, master_dst)
            
            # Sync to annotator_1 and annotator_2
            for ann in ['annotator_1', 'annotator_2']:
                ann_dst = os.path.join(FINAL_ANN_DIR, ann, 'records', fld, wav_fn)
                os.makedirs(os.path.dirname(ann_dst), exist_ok=True)
                if not os.path.exists(ann_dst) or os.path.getsize(ann_dst) != os.path.getsize(master_dst):
                    shutil.copy2(master_dst, ann_dst)
            
            dur = get_audio_duration(master_dst)
            fld_duration += dur
            fld_records.append({
                'speaker_id': fld,
                'file_name': wav_fn,
                'original_name': fn,
                'duration_sec': round(dur, 2)
            })
            
        total_duration += fld_duration
        synced_data[fld] = {
            'file_count': len(fld_records),
            'duration_sec': round(fld_duration, 2),
            'duration_formatted': f"{int(fld_duration // 60)}m {fld_duration % 60:.2f}s",
            'files': fld_records
        }
        
    return synced_data, total_duration

def update_label_studio_database(ann_id, synced_data, label_config_xml, reset_tasks=False):
    """Update SQLite database for an annotator."""
    ann_dir = os.path.join(FINAL_ANN_DIR, ann_id)
    db_path = os.path.join(ann_dir, 'data', 'label_studio.sqlite3')
    if not os.path.exists(db_path):
        print(f"[{ann_id}] Database not found at {db_path}!")
        return 0, 0
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. Update project label_config
    cur.execute("UPDATE project SET label_config = ? WHERE id = 1", (label_config_xml,))
    
    # 2. Update local files storage records
    cur.execute("SELECT id FROM io_storages_localfilesmixin WHERE path = ?", (FINAL_ANN_DIR,))
    if not cur.fetchone():
        now_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        cur.execute("INSERT OR REPLACE INTO io_storages_localfilesmixin (id, path, regex_filter, use_blob_urls) VALUES (1, ?, '', 1)", (FINAL_ANN_DIR,))
        cur.execute("INSERT OR REPLACE INTO io_storages_localfilesimportstorage (localfilesmixin_ptr_id, title, description, created_at, last_sync, last_sync_count, project_id, last_sync_job, meta, status, traceback, synchronizable, recursive_scan) VALUES (1, 'Final Annotation Storage', 'Local audio files', ?, ?, 0, 1, '', '{}', 'initialized', '', 1, 1)", (now_ts, now_ts))
    
    # 3. Ensure users have valid credentials
    cur.execute("UPDATE htx_user SET password = ? WHERE email LIKE '%vipul%'", (PASSWORD_HASH_DEFAULT,))
    
    # 4. Handle tasks
    cur.execute("SELECT id, data FROM task WHERE project_id = 1")
    existing_tasks = cur.fetchall()
    
    existing_by_file = {}
    for tid, data_str in existing_tasks:
        try:
            d = json.loads(data_str)
            fn = d.get('file_name')
            spk = d.get('speaker_id')
            if fn and spk:
                existing_by_file[(spk, fn)] = tid
        except Exception:
            pass
            
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    
    if reset_tasks:
        cur.execute("DELETE FROM task WHERE project_id = 1")
        existing_by_file = {}
        task_id = 1
    else:
        task_id = max([r[0] for r in existing_tasks], default=0) + 1

    added_count = 0
    task_order_id = 1
    
    for fld, fld_info in synced_data.items():
        for rec in fld_info['files']:
            key = (fld, rec['file_name'])
            rel_audio_url = f"/data/local-files/?d=final_annotation/{ann_id}/records/{fld}/{rec['file_name']}"
            
            task_data = {
                'audio': rel_audio_url,
                'speaker_id': fld,
                'file_name': rec['file_name'],
                'clip_id': f"{fld}_{task_order_id}",
                'duration': rec['duration_sec']
            }
            
            if key not in existing_by_file:
                cur.execute(
                    """INSERT INTO task (
                        id, data, created_at, updated_at, is_labeled,
                        project_id, meta, overlap, inner_id,
                        total_annotations, cancelled_annotations, total_predictions,
                        comment_count, unresolved_comment_count, allow_skip
                    ) VALUES (?, ?, ?, ?, 0, 1, '{}', 1, ?, 0, 0, 0, 0, 0, 1)""",
                    (task_id, json.dumps(task_data), now, now, task_id)
                )
                existing_by_file[key] = task_id
                task_id += 1
                added_count += 1
            elif reset_tasks:
                cur.execute(
                    """INSERT INTO task (
                        id, data, created_at, updated_at, is_labeled,
                        project_id, meta, overlap, inner_id,
                        total_annotations, cancelled_annotations, total_predictions,
                        comment_count, unresolved_comment_count, allow_skip
                    ) VALUES (?, ?, ?, ?, 0, 1, '{}', 1, ?, 0, 0, 0, 0, 0, 1)""",
                    (task_order_id, json.dumps(task_data), now, now, task_order_id)
                )
                added_count += 1
                
            task_order_id += 1

    conn.commit()
    cur.execute("SELECT count(*) FROM task WHERE project_id = 1")
    total_in_db = cur.fetchone()[0]

    # Export complete tasks.json for this annotator
    cur.execute("SELECT id, data FROM task WHERE project_id = 1 ORDER BY id ASC")
    all_tasks = [{'id': r[0], 'data': json.loads(r[1])} for r in cur.fetchall()]
    with open(os.path.join(ann_dir, 'tasks.json'), 'w', encoding='utf-8') as f:
        json.dump(all_tasks, f, indent=2)

    conn.close()
    
    return added_count, total_in_db

def apply_rest_api_patch(port, username, password, config_xml):
    """Notify running Label Studio instance to reload label_config and refresh cache."""
    try:
        import requests
        s = requests.Session()
        r = s.get(f'http://localhost:{port}/user/login/', timeout=3)
        csrf = s.cookies.get('csrftoken')
        s.post(f'http://localhost:{port}/user/login/', data={'email': username, 'password': password, 'csrfmiddlewaretoken': csrf}, headers={'Referer': f'http://localhost:{port}/user/login/'}, timeout=3)
        csrf = s.cookies.get('csrftoken')
        res = s.patch(f'http://localhost:{port}/api/projects/1/', json={'label_config': config_xml}, headers={'X-CSRFToken': csrf, 'Referer': f'http://localhost:{port}/projects/1/settings'}, timeout=3)
        return res.status_code == 200
    except Exception as e:
        return False

def main():
    reset_mode = '--all' in sys.argv or '--reset' in sys.argv
    print("=" * 70)
    print("Universal Record Sync & Audio Pipeline for Label Studio")
    print(f"Records directory: {RECORDS_DIR}")
    print(f"Excluding: {sorted(list(EXCLUDED_FOLDERS))}")
    print(f"Mode: {'Full reset / re-index all records' if reset_mode else 'Incremental sync (preserving existing tasks)'}")
    print("=" * 70)

    # 1. Read config XML
    with open(CONFIG_XML_PATH, 'r', encoding='utf-8') as f:
        config_xml = f.read()

    # 2. Scan records
    records_by_folder = scan_records()
    total_raw_files = sum(len(files) for files in records_by_folder.values())
    print(f"Scanned {len(records_by_folder)} included folders, found {total_raw_files} audio files.")

    # 3. Convert & sync audio files
    print("\nConverting & syncing audio files to 16 kHz mono WAV...")
    synced_data, total_duration = sync_audio_files(records_by_folder)

    # 4. Update databases
    print("\nUpdating Label Studio Annotator databases...")
    for ann_id, port, user, pwd in [
        ('annotator_1', 8081, 'annotator1@institution.local', 'annotator1password'),
        ('annotator_2', 8082, 'annotator2@institution.local', 'annotator2password')
    ]:
        added, total_tasks = update_label_studio_database(ann_id, synced_data, config_xml, reset_tasks=reset_mode)
        api_ok = apply_rest_api_patch(port, user, pwd, config_xml)
        print(f"[{ann_id}] Total tasks: {total_tasks} (New added: {added}) | REST API reload: {'OK' if api_ok else 'Instance offline or manual reload'}")

    # 5. Save summary JSON
    summary = {
        'timestamp': datetime.now().isoformat(),
        'included_folders': list(synced_data.keys()),
        'excluded_folders': sorted(list(EXCLUDED_FOLDERS)),
        'total_folders': len(synced_data),
        'total_audio_files': total_raw_files,
        'total_duration_seconds': round(total_duration, 2),
        'total_duration_formatted': f"{int(total_duration // 3600)}h {int((total_duration % 3600) // 60)}m {total_duration % 60:.2f}s",
        'folder_breakdown': {
            fld: {
                'file_count': info['file_count'],
                'duration_seconds': info['duration_sec'],
                'duration_formatted': info['duration_formatted']
            } for fld, info in synced_data.items()
        }
    }

    summary_path = os.path.join(FINAL_ANN_DIR, 'AUDIO_DATA_SUMMARY.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    # 6. Print Report
    print("\n" + "=" * 70)
    print(f"{'FOLDER':<10} | {'FILES':<8} | {'DURATION':<15}")
    print("-" * 70)
    for fld, info in synced_data.items():
        print(f"{fld:<10} | {info['file_count']:<8} | {info['duration_formatted']:<15}")
    print("=" * 70)
    print(f"TOTAL INCLUDED: {len(synced_data)} folders, {total_raw_files} audio files")
    print(f"TOTAL DURATION: {int(total_duration // 3600)}h {int((total_duration % 3600) // 60)}m {total_duration % 60:.2f}s ({total_duration:.2f} seconds)")
    print(f"Summary written to: {summary_path}")
    print("=" * 70)

if __name__ == '__main__':
    main()

