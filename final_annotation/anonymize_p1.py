#!/usr/bin/env python3
"""anonymize_p1.py - Anonymizes P1 by swapping its data with a randomly chosen participant folder."""

import os
import sys
import json
import random
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDS_DIR = os.path.join(BASE_DIR, 'Records')
FINAL_ANN_DIR = os.path.join(BASE_DIR, 'final_annotation')
MAPPING_FILE = os.path.join(FINAL_ANN_DIR, '.anonymization_mapping.json')

EXCLUDED_FOLDERS = {f'P{i}' for i in range(13, 20)}

def main():
    # Eligible folders: included folders except P1
    eligible_folders = []
    for d in sorted(os.listdir(RECORDS_DIR)):
        if d.startswith('P') and d != 'P1' and d not in EXCLUDED_FOLDERS:
            full_p = os.path.join(RECORDS_DIR, d)
            if os.path.isdir(full_p):
                eligible_folders.append(d)
                
    if not eligible_folders:
        print("No eligible folders found to swap with P1!")
        sys.exit(1)
        
    # Securely select one random partner
    partner = random.choice(eligible_folders)
    
    # Perform swap in Records/
    p1_path = os.path.join(RECORDS_DIR, 'P1')
    partner_path = os.path.join(RECORDS_DIR, partner)
    temp_path = os.path.join(RECORDS_DIR, 'P_ANON_TEMP')
    
    os.rename(p1_path, temp_path)
    os.rename(partner_path, p1_path)
    os.rename(temp_path, partner_path)
    
    # Remove old converted folders so sync_records converts cleanly
    for target in [
        os.path.join(FINAL_ANN_DIR, 'records'),
        os.path.join(FINAL_ANN_DIR, 'annotator_1', 'records'),
        os.path.join(FINAL_ANN_DIR, 'annotator_2', 'records')
    ]:
        for fld in ['P1', partner]:
            fp = os.path.join(target, fld)
            if os.path.exists(fp):
                shutil.rmtree(fp)
                
    # Save the mapping secretly
    mapping_record = {
        'original_p1_now_in': partner,
        'folder_now_in_p1': partner,
        'eligible_pool': eligible_folders
    }
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping_record, f, indent=2)
        
    print("Swap completed in Records/ directory.")
    
    # Run sync_records.py with --reset
    sync_script = os.path.join(FINAL_ANN_DIR, 'sync_records.py')
    res = subprocess.run([sys.executable, sync_script, '--reset'], check=True)
    
    print("Anonymization complete. Pipeline re-indexed and synced.")

if __name__ == '__main__':
    main()

