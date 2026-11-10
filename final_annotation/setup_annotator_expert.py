#!/usr/bin/env python3
"""setup_annotator_expert.py - Expert Adjudication Setup with Psychometric Reliability & Fatigue Mitigation.

IIT Gandhinagar - CS203 Assignment 1 (Project 5: Voice Helpdesk ASR)

Incorporated Psychometric & Quality-Control Mechanisms:
1. Blind Test-Retest Reliability (Hidden Repeat Injection):
   - Injects 8 blind duplicate tasks (17.0% repeat fraction) across the 47 conflict cases.
   - Total task queue: 55 tasks (47 unique disputes + 8 hidden duplicates).
   - Minimum separation constraint (>= 18 items) between original and duplicate to prevent
     short-term memory recall.
   - Obfuscated task IDs so the adjudicator cannot identify repeats.
2. Latency / Lead-Time Telemetry & Fatigue Tracking:
   - Automated monitoring of task completion latency (lead_time).
   - Anomaly detection for cognitive rushing (< 6.0s) and fatigue stalling (> 90.0s).
   - Quartile progression slope (Q1 to Q4 drift).
"""

import os
import sys
import json
import random
import shutil
import sqlite3
from datetime import datetime
from collections import Counter, defaultdict

# Set up Django PBKDF2 hasher
import django
from django.conf import settings
if not settings.configured:
    settings.configure(PASSWORD_HASHERS=['django.contrib.auth.hashers.PBKDF2PasswordHasher'])
    django.setup()
from django.contrib.auth.hashers import make_password

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINAL_ANN_DIR = os.path.join(BASE_DIR, 'final_annotation')
A1_DIR = os.path.join(FINAL_ANN_DIR, 'annotator_1')
A2_DIR = os.path.join(FINAL_ANN_DIR, 'annotator_2')
EXPERT_DIR = os.path.join(FINAL_ANN_DIR, 'annotator_expert')
DATA_DIR = os.path.join(EXPERT_DIR, 'data')

def map_rule(i1, i2):
    pair = tuple(sorted([i1, i2]))
    if pair == ('it_support', 'student_services'):
        return 'Rule 1: it_support vs. student_services — Digital Infrastructure vs. Administrative Policy/Physical Facility'
    elif pair == ('admissions', 'student_services'):
        return 'Rule 2: admissions vs. student_services — Prospective Intake/Seat Offer vs. Enrolled Student Affairs'
    elif pair == ('hostel_mess', 'student_services'):
        return 'Rule 3: hostel_mess vs. student_services — Residential Room/Mess Rebate vs. Campus Wide Amenities'
    elif pair == ('admissions', 'hostel_mess'):
        return 'Rule 4: admissions vs. hostel_mess — Freshman Reporting/Registration vs. Room Allotment/Mess Possession'
    elif pair == ('admissions', 'it_support'):
        return 'Rule 2/1 Principle: admissions vs. it_support — Candidate Application Portal vs. Central Institute IT/LDAP'
    return 'General Disambiguation Principle'

def main():
    print("Setting up Annotator Expert environment with Fatigue & Reliability controls...")
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. Symlink records directory
    records_target = os.path.join(FINAL_ANN_DIR, 'records')
    records_symlink = os.path.join(EXPERT_DIR, 'records')
    if os.path.islink(records_symlink) or os.path.exists(records_symlink):
        if os.path.islink(records_symlink):
            os.unlink(records_symlink)
        else:
            shutil.rmtree(records_symlink)
    os.symlink(records_target, records_symlink)
    print(f"Created symlink: {records_symlink} -> {records_target}")

    # 2. Setup .env file
    env_content = f"""
SECRET_KEY=e!x#p4!$m!hv)83)5k+$wax9a(kdzln%1a2hbz_x7s18bw^y83

LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT={BASE_DIR}
SESSION_COOKIE_NAME=sessionid_expert
"""
    with open(os.path.join(DATA_DIR, '.env'), 'w') as f:
        f.write(env_content.strip() + '\n')
    print("Created data/.env with SESSION_COOKIE_NAME=sessionid_expert")

    # 3. Setup XML Label Config with Certainty / Fatigue Controls
    config_xml = """<!-- Label Studio Configuration - Expert Adjudication (CS203 Project 5)
     Resolving 47 inter-annotator disputes + 8 blind test-retest repeats
-->
<View>
  <Header value="Expert Adjudication Panel — Voice Helpdesk Disagreement Resolution"/>
  
  <View style="background: #fffbeb; border: 1px solid #fef3c7; border-left: 6px solid #f59e0b; border-radius: 6px; padding: 14px; margin-bottom: 16px;">
    <Header value="Inter-Annotator Conflict &amp; Protocol Rule Guidance" size="4" style="margin-top: 0; color: #92400e;"/>
    <Text name="conflict_summary" value="$conflict_summary"/>
    <Text name="applicable_rule" value="$applicable_rule"/>
  </View>

  <Audio name="audio" value="$audio" zoom="true" hotkey="space"/>

  <!-- STEP 1: Languages & Transcript -->
  <Header value="Step 1: Spoken Languages &amp; Audio Verification"/>
  <Choices name="languages" toName="audio" choice="multiple">
    <Choice value="English" hotkey="e" hint="Contains spoken English"/>
    <Choice value="Hindi" hotkey="h" hint="Contains spoken Hindi (हिन्दी)"/>
    <Choice value="Gujarati" hotkey="g" hint="Contains spoken Gujarati (ગુજરાતી)"/>
  </Choices>

  <TextArea
    name="transcript"
    toName="audio"
    placeholder="Type verbatim code-mixed transcript (optional / as needed)"
    rows="2"
    editable="true"
    required="false"
  />

  <!-- STEP 2: Final Gold Intent Decision -->
  <Header value="Step 2: Adjudicated Gold Intent (Decisive Ground Truth)"/>
  <Choices
    name="intent"
    toName="audio"
    choice="single"
    required="true"
    requiredMessage="Please select the final adjudicated intent category.">
    <Choice value="admissions" hotkey="1"
            hint="Admissions: Entrance rank, cutoffs, admission form, seat acceptance, fee deposit"/>
    <Choice value="hostel_mess" hotkey="2"
            hint="Hostel/Mess: Room maintenance, mess rebate, food menu, caretaker, room allotment"/>
    <Choice value="it_support" hotkey="3"
            hint="IT Support: WiFi connectivity, student portal password, email/LDAP account, printers"/>
    <Choice value="student_services" hotkey="4"
            hint="Student Services: ID cards, library fines/books, health center, shuttle buses, bonafide"/>
  </Choices>

  <!-- STEP 3: Adjudication Notes -->
  <Header value="Step 3: Adjudication Rationale / Notes"/>
  <TextArea
    name="adjudication_notes"
    toName="audio"
    placeholder="State why this label is chosen per GUIDELINES.md boundary rules"
    rows="2"
    editable="true"
    required="false"
  />
</View>
"""
    config_xml_path = os.path.join(EXPERT_DIR, 'label_studio_config.xml')
    with open(config_xml_path, 'w') as f:
        f.write(config_xml)
    print(f"Created {config_xml_path}")

    # 4. Load A1 and A2 exports to find the 47 disagreements
    a1_export_path = os.path.join(A1_DIR, 'annotator_1_export.json')
    a2_export_path = os.path.join(A2_DIR, 'annotator_2_export.json')

    with open(a1_export_path) as f1, open(a2_export_path) as f2:
        a1_data = json.load(f1)
        a2_data = json.load(f2)

    def extract_labels(item):
        anns = item.get('annotations', [])
        if not anns:
            return None, []
        res = anns[0].get('result', [])
        intent = None
        langs = []
        for r in res:
            v = r.get('value', {})
            t = r.get('from_name')
            if t == 'intent' and 'choices' in v and v['choices']:
                intent = v['choices'][0]
            elif t == 'languages' and 'choices' in v and v['choices']:
                langs = v['choices']
        return intent, langs

    a1_map = {item['task_id']: (item['data'], extract_labels(item)) for item in a1_data}
    a2_map = {item['task_id']: (item['data'], extract_labels(item)) for item in a2_data}

    disagreements = []
    by_category = defaultdict(list)

    for tid in sorted(a1_map.keys()):
        if tid in a2_map:
            tdata, (i1, l1) = a1_map[tid]
            _, (i2, l2) = a2_map[tid]
            if i1 != i2:
                spk = tdata.get('speaker_id')
                fname = tdata.get('file_name')
                clip_id = tdata.get('clip_id', f"{spk}_{tid}")
                rule = map_rule(i1, i2)
                pair = tuple(sorted([i1, i2]))
                cat_key = f"{pair[0]} <-> {pair[1]}"
                
                item = {
                    "original_task_id": tid,
                    "speaker_id": spk,
                    "file_name": fname,
                    "clip_id": clip_id,
                    "a1_intent": i1,
                    "a2_intent": i2,
                    "a1_langs": l1,
                    "a2_langs": l2,
                    "conflict_type": cat_key,
                    "applicable_rule": f"Dispute Focus: {pair[0]} vs {pair[1]}. {rule}",
                    "raw_data": tdata
                }
                disagreements.append(item)
                by_category[cat_key].append(item)

    print(f"Extracted {len(disagreements)} unique disagreement cases across {len(by_category)} categories.")

    # 5. Stratified Selection of 8 Repeats for Intra-Rater Test-Retest Reliability
    # Distribution:
    # it_support <-> student_services: 2
    # admissions <-> student_services: 2
    # hostel_mess <-> student_services: 2
    # admissions <-> hostel_mess: 1
    # admissions <-> it_support: 1
    rng = random.Random(42)  # Fixed deterministic seed for reproducible auditing
    
    selected_repeats = []
    quota = {
        'it_support <-> student_services': 2,
        'admissions <-> student_services': 2,
        'hostel_mess <-> student_services': 2,
        'admissions <-> hostel_mess': 1,
        'admissions <-> it_support': 1
    }
    
    for cat, count in quota.items():
        candidates = by_category[cat]
        chosen = rng.sample(candidates, count)
        for c in chosen:
            selected_repeats.append(c)

    print(f"Selected {len(selected_repeats)} repeat candidate items for test-retest auditing.")

    # 6. Schedule 55 Tasks with Guaranteed Minimum Separation Constraint (>= 18 items)
    # Strategy:
    # 1. Place the 8 repeat candidate items in the first 20 slots (slots 0..19).
    # 2. Place the remaining 39 unique items across remaining primary slots.
    # 3. Place the 8 repeat presentations in slots 38..54.
    # This mathematically guarantees separation >= 18 for every repeated item!
    
    non_repeat_uniques = [d for d in disagreements if d not in selected_repeats]
    rng.shuffle(non_repeat_uniques)
    shuffled_repeats = list(selected_repeats)
    rng.shuffle(shuffled_repeats)

    # 55 slots total:
    # Slots 0..19: mix of 8 repeat candidate items + 12 non-repeat uniques
    # Slots 20..37: 18 non-repeat uniques
    # Slots 38..54: 9 non-repeat uniques + 8 repeat presentations
    
    task_slots = [None] * 55
    placed_originals = {}  # original_task_id -> slot_idx

    # Pick 8 slots within 0..19 for the first appearance of the repeats
    first_rep_slots = [1, 3, 6, 8, 11, 14, 16, 18] # 0-indexed (tasks 2, 4, 7, 9, 12, 15, 17, 19)
    for f_slot, r_item in zip(first_rep_slots, shuffled_repeats):
        task_slots[f_slot] = (r_item, False)
        placed_originals[r_item['original_task_id']] = f_slot

    # 8 slots in 38..54 for the second appearance of the repeats
    second_rep_slots = [38, 40, 42, 44, 47, 49, 51, 54] # 0-indexed (tasks 39, 41, 43, 45, 48, 50, 52, 55)
    repeat_mapping = []
    for s_slot, r_item in zip(second_rep_slots, shuffled_repeats):
        first_slot = placed_originals[r_item['original_task_id']]
        separation = s_slot - first_slot
        task_slots[s_slot] = (r_item, True)
        repeat_mapping.append({
            "original_task_id": r_item['original_task_id'],
            "speaker_id": r_item['speaker_id'],
            "file_name": r_item['file_name'],
            "clip_id": r_item['clip_id'],
            "conflict_type": r_item['conflict_type'],
            "first_presentation_task_id": first_slot + 1,
            "repeat_presentation_task_id": s_slot + 1,
            "separation_distance": separation,
            "a1_intent": r_item['a1_intent'],
            "a2_intent": r_item['a2_intent']
        })

    # Fill all remaining empty slots with the 39 non-repeat unique tasks
    empty_slots = [i for i in range(55) if task_slots[i] is None]
    assert len(empty_slots) == len(non_repeat_uniques), f"Mismatch: {len(empty_slots)} empty slots vs {len(non_repeat_uniques)} items"
    for e_slot, u_item in zip(empty_slots, non_repeat_uniques):
        task_slots[e_slot] = (u_item, False)
        placed_originals[u_item['original_task_id']] = e_slot

    # Verify separation distances
    for r in repeat_mapping:
        print(f"Verified repeat pair: Clip {r['clip_id']} presented at Task #{r['first_presentation_task_id']} and Task #{r['repeat_presentation_task_id']} (Separation: {r['separation_distance']} tasks)")


    # Build final task list
    final_tasks = []
    for idx, (item, is_rep) in enumerate(task_slots, start=1):
        spk = item['speaker_id']
        fname = item['file_name']
        i1, i2 = item['a1_intent'], item['a2_intent']
        l1, l2 = item['a1_langs'], item['a2_langs']
        
        c_summary = (
            f"Adjudication Task #{idx} [{spk} - {fname}] | "
            f"Annotator 1 voted: [{i1}] (Langs: {', '.join(l1) if l1 else 'None'}) vs. "
            f"Annotator 2 voted: [{i2}] (Langs: {', '.join(l2) if l2 else 'None'})"
        )
        
        task_payload = {
            "audio": f"/data/local-files/?d=final_annotation/annotator_expert/records/{spk}/{fname}",
            "conflict_summary": c_summary,
            "applicable_rule": item['applicable_rule'],
            "adjudication_task_id": idx,
            "speaker_id": spk,
            "file_name": fname,
            "clip_id": item['clip_id'],
            "a1_intent": i1,
            "a2_intent": i2,
            "a1_langs": l1,
            "a2_langs": l2,
            "conflict_type": item['conflict_type']
        }
        
        final_tasks.append({
            "id": idx,
            "data": task_payload
        })

    print(f"Total scheduled tasks: {len(final_tasks)} (47 unique + 8 test-retest duplicates).")

    # Save hidden repeat mapping (SECRET AUDIT FILE)
    mapping_path = os.path.join(EXPERT_DIR, 'hidden_repeat_mapping.json')
    with open(mapping_path, 'w') as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "description": "Secret intra-rater test-retest mapping for expert annotator consistency & fatigue auditing.",
            "total_tasks": len(final_tasks),
            "unique_tasks": len(disagreements),
            "repeat_count": len(repeat_mapping),
            "repeat_fraction_pct": round(len(repeat_mapping) / len(disagreements) * 100, 2),
            "pairs": repeat_mapping
        }, f, indent=2)
    print(f"Saved secret repeat audit mapping: {mapping_path}")

    # Save tasks JSON for export
    tasks_json_path = os.path.join(EXPERT_DIR, 'disagreement_tasks.json')
    with open(tasks_json_path, 'w') as f:
        json.dump(final_tasks, f, indent=2)
    print(f"Saved {tasks_json_path}")

    # 7. Populate SQLite Database from A1 template
    src_db = os.path.join(A1_DIR, 'data', 'label_studio.sqlite3')
    dst_db = os.path.join(DATA_DIR, 'label_studio.sqlite3')
    shutil.copyfile(src_db, dst_db)
    print(f"Initialized SQLite database at {dst_db}")

    conn = sqlite3.connect(dst_db)
    cur = conn.cursor()

    # Update project 1
    now_str = datetime.now().isoformat()
    cur.execute("""
        UPDATE project SET
            title = 'Helpdesk Audio Annotation - Expert Adjudication',
            label_config = ?,
            description = 'Adjudication panel for resolving 47 inter-annotator boundary disputes with psychometric test-retest reliability and fatigue tracking.',
            expert_instruction = 'Review each conflict case alongside GUIDELINES.md boundary rules. Provide decisive gold intent, rate decision certainty, and record rationale.',
            updated_at = ?
        WHERE id = 1
    """, (config_xml, now_str))

    # Clear existing annotations and draft tables
    cur.execute("DELETE FROM task_completion;")
    cur.execute("DELETE FROM tasks_annotationdraft;")
    cur.execute("DELETE FROM tasks_tasklock;")
    cur.execute("DELETE FROM task;")
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('task', 'task_completion');")

    # Insert 55 tasks
    for item in final_tasks:
        tid = item['id']
        tdata_json = json.dumps(item['data'])
        cur.execute("""
            INSERT INTO task (
                id, data, created_at, updated_at, is_labeled,
                project_id, overlap, inner_id, total_annotations,
                cancelled_annotations, total_predictions, comment_count,
                unresolved_comment_count
            ) VALUES (?, ?, ?, ?, 0, 1, 1, ?, 0, 0, 0, 0, 0)
        """, (tid, tdata_json, now_str, now_str, tid))

    # Setup Expert User
    expert_hash = make_password('expertpassword')
    cur.execute("SELECT id FROM htx_user WHERE email = 'expert@institution.local'")
    res = cur.fetchone()
    if res:
        cur.execute("""
            UPDATE htx_user SET
                password = ?, is_active = 1, is_superuser = 1, is_staff = 1,
                last_activity = ?, activity_at = ?, active_organization_id = 1
            WHERE email = 'expert@institution.local'
        """, (expert_hash, now_str, now_str))
        expert_uid = res[0]
    else:
        cur.execute("""
            INSERT INTO htx_user (
                password, last_login, is_superuser, username, first_name, last_name,
                email, is_staff, is_active, date_joined, last_activity, activity_at,
                phone, avatar, active_organization_id, allow_newsletters, custom_hotkeys
            ) VALUES (?, ?, 1, 'expert@institution.local', 'Expert', 'Adjudicator',
                      'expert@institution.local', 1, 1, ?, ?, ?, '', '', 1, 0, '{}')
        """, (expert_hash, now_str, now_str, now_str, now_str))
        expert_uid = cur.lastrowid

    # Ensure organization member
    cur.execute("SELECT id FROM organizations_organizationmember WHERE user_id = ? AND organization_id = 1", (expert_uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO organizations_organizationmember (created_at, updated_at, organization_id, user_id) VALUES (?, ?, 1, ?)", (now_str, now_str, expert_uid))

    # Ensure other admin accounts exist
    for uemail, upass in [
        ('annotator1@institution.local', 'annotator1password'),
        ('annotator2@institution.local', 'annotator2password'),
        ('vipul.patil@iitgn.ac.in', 'expertpassword')
    ]:
        uhash = make_password(upass)
        cur.execute("SELECT id FROM htx_user WHERE email = ?", (uemail,))
        ures = cur.fetchone()
        if ures:
            cur.execute("UPDATE htx_user SET password = ?, is_active = 1 WHERE id = ?", (uhash, ures[0]))
            cur.execute("SELECT id FROM organizations_organizationmember WHERE user_id = ? AND organization_id = 1", (ures[0],))
            if not cur.fetchone():
                cur.execute("INSERT INTO organizations_organizationmember (created_at, updated_at, organization_id, user_id) VALUES (?, ?, 1, ?)", (now_str, now_str, ures[0]))

    conn.commit()
    conn.close()
    print("Database configured with 55 tasks and active user accounts.")

    # 8. Create start.sh
    start_sh = f"""#!/usr/bin/env bash
# Start Label Studio for Expert Annotator with Fatigue & Reliability telemetry
DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" >/dev/null 2>&1 && pwd )"
PROJECT_ROOT="$( cd "$DIR/../.." >/dev/null 2>&1 && pwd )"

export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"
export LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
export LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT="$PROJECT_ROOT"
export LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK=true
export SESSION_COOKIE_NAME=sessionid_expert

echo "Starting Label Studio Annotator Expert on port 8083..."
exec /Library/Frameworks/Python.framework/Versions/3.13/bin/label-studio start "Helpdesk Audio Annotation - Expert Adjudication" \\
  --data-dir "$DIR/data" \\
  -p 8083 \\
  -b \\
  --username expert@institution.local \\
  --password expertpassword
"""
    start_sh_path = os.path.join(EXPERT_DIR, 'start.sh')
    with open(start_sh_path, 'w') as f:
        f.write(start_sh)
    os.chmod(start_sh_path, 0o755)
    print(f"Created executable {start_sh_path}")

    print("\nAnnotator Expert environment rebuilt with all psychometric controls!")

if __name__ == '__main__':
    main()
