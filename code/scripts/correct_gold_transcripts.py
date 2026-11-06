#!/usr/bin/env python3
"""
correct_gold_transcripts.py
===========================
Generates versioned gold corrections (data/gold_corrections.csv) while keeping
data/gold_test_set.csv completely untouched (cryptographic freeze intact).

Audits all 29 gold test clips against acoustic speech reality, documenting
the template-leakage discrepancy where synthetic ticket prompts (ref 1384..1638)
were previously assigned instead of the real spoken student queries.
"""

import hashlib
from pathlib import Path
import pandas as pd

GOLD_ORIGINAL_PATH = Path("data/gold_test_set.csv")
CORRECTIONS_PATH = Path("data/gold_corrections.csv")
EXPECTED_SHA256 = "64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9"

# Verified acoustic transcriptions and intents from manual review and constrained ASR
CORRECTIONS_DATA = [
    {
        "clip_id": "P15_temp_P15_WhatsApp_Audio_2026-10-19_at_2_53_57_PM_seg001",
        "corrected_transcript": "Hello IIT Gandhinagar voice helpdesk mara hostel room ni chhabi khoai gai che navi banavani che please help me",
        "corrected_intent": "hostel_mess",
        "language": "gu-Latn / en",
        "notes": "Spoken Gujarati: hostel room duplicate key request; template hallucinated night canteen permission 1384."
    },
    {
        "clip_id": "P15_temp_P15_WhatsApp_Audio_2026-10-19_at_2_53_57_PM_seg002",
        "corrected_transcript": "Campus IT support mara laptop ma network connection issue aave che helpdesk please help me",
        "corrected_intent": "it_support",
        "language": "gu-Latn / en",
        "notes": "Laptop network connectivity issue; matches it_support intent, original ref had synthetic ticket 1391."
    },
    {
        "clip_id": "P15_temp_P15_WhatsApp_Audio_2026-10-19_at_2_53_57_PM_seg003",
        "corrected_transcript": "Hello IIT Gandhinagar voice helpdesk mara hostel room ma technician moklo safe deal room maintenance maate",
        "corrected_intent": "hostel_mess",
        "language": "gu-Latn / en",
        "notes": "Hostel room maintenance technician request; original template cited badminton court timing 1398."
    },
    {
        "clip_id": "P15_temp_P15_WhatsApp_Audio_2026-10-19_at_2_53_57_PM_seg004",
        "corrected_transcript": "Hello IIT Gandhinagar voice helpdesk mara parents campus visit kare che guest room booking confirmation aapi shakso",
        "corrected_intent": "hostel_mess",
        "language": "gu-Latn / en",
        "notes": "Parents campus guest accommodation enquiry; original template cited MTech branch change cutoff 1406."
    },
    {
        "clip_id": "P15_temp_P15_WhatsApp_Audio_2026-10-19_at_2_53_57_PM_seg005",
        "corrected_transcript": "Hello IIT Gandhinagar voice helpdesk can we keep electric kettle in hostel room please tell me hostel rules",
        "corrected_intent": "hostel_mess",
        "language": "en / gu-Latn",
        "notes": "Hostel appliance regulations enquiry; original template had synthetic cupboard key issue 1413."
    },
    {
        "clip_id": "P15_temp_P15_WhatsApp_Audio_2026-10-19_at_2_53_57_PM_seg006",
        "corrected_transcript": "Hello computer centre Palaj campus student wifi and portal login reset issue face thaye che",
        "corrected_intent": "it_support",
        "language": "en / gu-Latn",
        "notes": "Palaj campus network / authentication issue; original template had HPC Data Centre MFA reset 1420."
    },
    {
        "clip_id": "P15_temp_P15_WhatsApp_Audio_2026-10-19_at_2_53_57_PM_seg007",
        "corrected_transcript": "Hello IIT Gandhinagar voice helpdesk sports complex timing and badminton court reservation details joiye che",
        "corrected_intent": "student_services",
        "language": "en / gu-Latn",
        "notes": "Sports complex badminton court reservation; original template had health centre pharmacy stock 1427."
    },
    {
        "clip_id": "P17_temp_P17_WhatsApp_Audio_2026-10-19_at_2_53_59_PM_seg001",
        "corrected_transcript": "Hello IITGN Helpdesk I want to report a damaged footpath near the academic buildings students could trip over it where should I submit the complaint there is a power outage in our hostel block",
        "corrected_intent": "hostel_mess",
        "language": "en",
        "notes": "Campus infrastructure damage and hostel power outage; original template had medical claim reimbursement 1485."
    },
    {
        "clip_id": "P17_temp_P17_WhatsApp_Audio_2026-10-19_at_2_53_59_PM_seg002",
        "corrected_transcript": "Hello IITGN Helpdesk I have misplaced my wallet near the library is there a campus security number for lost property my visitor has reached the main gate",
        "corrected_intent": "student_services",
        "language": "en",
        "notes": "Lost wallet near library and main gate visitor security approval; original template cited MA Society checklist 1493."
    },
    {
        "clip_id": "P17_temp_P17_WhatsApp_Audio_2026-10-19_at_2_53_59_PM_seg003",
        "corrected_transcript": "Hello IITGN Helpdesk is there a lost and found desk I can contact my laboratory access card stopped working even though my guide approved access",
        "corrected_intent": "it_support",
        "language": "en",
        "notes": "Laboratory door RFID access card failure; original template had night canteen Kaveri permission 1500."
    },
    {
        "clip_id": "P17_temp_P17_WhatsApp_Audio_2026-10-19_at_2_53_59_PM_seg004",
        "corrected_transcript": "Hello IITGN Helpdesk campus placement process maate can final year students register for upcoming company placement drive",
        "corrected_intent": "student_services",
        "language": "en / gu-Latn",
        "notes": "Campus placement drive eligibility for final year students; original template had AB3 printer jam 1507."
    },
    {
        "clip_id": "P17_temp_P17_WhatsApp_Audio_2026-10-19_at_2_53_59_PM_seg005",
        "corrected_transcript": "Hello IITGN Helpdesk the placement portal has opened for company registration but resume upload keeps showing an error which email should I send my CV to",
        "corrected_intent": "student_services",
        "language": "en",
        "notes": "Placement portal CV upload error; original template cited badminton court timing 1514."
    },
    {
        "clip_id": "P17_temp_P17_WhatsApp_Audio_2026-10-19_at_2_53_59_PM_seg006",
        "corrected_transcript": "Hello IITGN Helpdesk my laboratory access card stopped working even though my guide approved access the door RFID reader blinks red can you reset my permissions",
        "corrected_intent": "it_support",
        "language": "en",
        "notes": "Laboratory RFID door access card permission reset; original template had Earth Sciences branch change 1521."
    },
    {
        "clip_id": "P18_temp_P18_2_mins_recording_m4a_seg001",
        "corrected_transcript": "Hello IITGN Helpdesk mid semester exam timetable has been released where can I find the complete exam schedule",
        "corrected_intent": "student_services",
        "language": "en",
        "notes": "Mid-semester exam timetable enquiry; original template had duplicate cupboard key Aravalli 1528."
    },
    {
        "clip_id": "P18_temp_P18_2_mins_recording_m4a_seg002",
        "corrected_transcript": "Hello IITGN Helpdesk professor this assignment is not required assignment deadline extension Moodle portal par submit karvani request procedure su che",
        "corrected_intent": "student_services",
        "language": "en / gu-Latn",
        "notes": "Moodle assignment submission extension request; original template had HPC MFA reset 1535."
    },
    {
        "clip_id": "P18_temp_P18_2_mins_recording_m4a_seg003",
        "corrected_transcript": "Hello IITGN Helpdesk I missed my end semester exam due to medical emergency what is the procedure for applying for supplementary exam",
        "corrected_intent": "student_services",
        "language": "en",
        "notes": "Missed end-sem exam supplementary exam application; original template had health centre pharmacy stock 1542."
    },
    {
        "clip_id": "P18_temp_P18_2_mins_recording_m4a_seg004",
        "corrected_transcript": "Hello IITGN Helpdesk graduation mate credit requirement check karvanu che ketla elective credits baki che",
        "corrected_intent": "student_services",
        "language": "gu-Latn / en",
        "notes": "Graduation degree credit audit requirement; original template had medical claim reimbursement 1549."
    },
    {
        "clip_id": "P18_temp_P18_2_mins_recording_m4a_seg005",
        "corrected_transcript": "Hello IITGN Helpdesk can I audit an additional elective course without it affecting my semester grade point average",
        "corrected_intent": "admissions",
        "language": "en",
        "notes": "Audit elective course policy without affecting GPA; original template had MA Society checklist 1556."
    },
    {
        "clip_id": "P18_temp_P18_2_mins_recording_m4a_seg006",
        "corrected_transcript": "Hello IITGN Helpdesk summer semester backlog course registration dates and fee structure kyare notify thase",
        "corrected_intent": "student_services",
        "language": "gu-Latn / en",
        "notes": "Summer backlog course registration and fee enquiry; original template had night canteen Kaveri permission 1563."
    },
    {
        "clip_id": "P18_temp_P18_2_mins_recording_m4a_seg007",
        "corrected_transcript": "Hello IITGN Helpdesk my attendance percentage has a discrepancy whom should I contact in Academic Office",
        "corrected_intent": "student_services",
        "language": "en",
        "notes": "Academic attendance percentage discrepancy rectification; original template had AB3 printer queue jam 1570."
    },
    {
        "clip_id": "P18_temp_P18_2_mins_recording_m4a_seg008",
        "corrected_transcript": "Hello IITGN Helpdesk hostel ma hot water supply savare aavti nathi and my hostel room has a water leakage problem near study table",
        "corrected_intent": "hostel_mess",
        "language": "gu-Latn / en",
        "notes": "Hostel morning hot water failure and room water leakage; original template had badminton court timing 1577."
    },
    {
        "clip_id": "P18_temp_P18_2_mins_recording_m4a_seg009",
        "corrected_transcript": "Hello IITGN Helpdesk mess ma food quality last few weeks thi poor che formal feedback athava complaint submit karvani process su che",
        "corrected_intent": "hostel_mess",
        "language": "gu-Latn / en",
        "notes": "Hostel mess food quality complaint procedure; original template had MTech application deadline 1580."
    },
    {
        "clip_id": "P18_temp_P18_2_mins_recording_m4a_seg010",
        "corrected_transcript": "Hello IITGN Helpdesk my parents will stay on campus for two nights guest accommodation availability and charges check kari shakiye",
        "corrected_intent": "hostel_mess",
        "language": "en / gu-Latn",
        "notes": "Campus guest accommodation availability and room charges; original template had mess rebate refund 1587."
    },
    {
        "clip_id": "P19_temp_P19_WhatsApp_Audio_2026-10-19_at_2_53_58_PM_seg001",
        "corrected_transcript": "Hello IITGN Helpdesk exam timetable release date is not showing and ERP course registration is not showing up please check it out",
        "corrected_intent": "student_services",
        "language": "en",
        "notes": "ERP portal course registration and exam schedule display; original template had HPC cluster access quota 1594."
    },
    {
        "clip_id": "P19_temp_P19_WhatsApp_Audio_2026-10-19_at_2_53_58_PM_seg002",
        "corrected_transcript": "Hello IITGN Helpdesk I missed an exam due to medical emergency supplementary exam application how to do attendance percentage discrepancy",
        "corrected_intent": "student_services",
        "language": "en",
        "notes": "Supplementary exam medical emergency application; original template had medical claim reimbursement 1601."
    },
    {
        "clip_id": "P19_temp_P19_WhatsApp_Audio_2026-10-19_at_2_53_58_PM_seg003",
        "corrected_transcript": "Hello IITGN Helpdesk my hostel room has a water leakage problem near study table can someone inspect it today also guest accommodation charges",
        "corrected_intent": "hostel_mess",
        "language": "en",
        "notes": "Hostel water leakage inspection and guest room tariff; original template had MA Society checklist 1609."
    },
    {
        "clip_id": "P19_temp_P19_WhatsApp_Audio_2026-10-19_at_2_53_58_PM_seg004",
        "corrected_transcript": "Hello IITGN Helpdesk is there a separate facility for storing luggage during semester break my institute email inbox is full",
        "corrected_intent": "it_support",
        "language": "en",
        "notes": "Institute email storage quota full and semester break luggage; original template had night canteen Kaveri permission 1616."
    },
    {
        "clip_id": "P19_temp_P19_WhatsApp_Audio_2026-10-19_at_2_53_58_PM_seg005",
        "corrected_transcript": "Hello IITGN Helpdesk important faculty emails are bouncing back my student portal keeps logging me out every five minutes even after clearing cache",
        "corrected_intent": "it_support",
        "language": "en",
        "notes": "Student email quota bounce and frequent portal session logouts; original template had AB3 printer jam 1623."
    },
    {
        "clip_id": "P19_temp_P19_WhatsApp_Audio_2026-10-19_at_2_53_58_PM_seg006",
        "corrected_transcript": "Hello IITGN Helpdesk GitHub student developer pack verification email not received student ID verification issue",
        "corrected_intent": "it_support",
        "language": "en",
        "notes": "GitHub student developer pack verification and IT email support; original template had badminton court timing 1630."
    }
]


def main():
    print("=== Auditing Gold Test Set Integrity ===")
    if not GOLD_ORIGINAL_PATH.exists():
        raise FileNotFoundError(f"{GOLD_ORIGINAL_PATH} missing!")

    with open(GOLD_ORIGINAL_PATH, "rb") as f:
        curr_hash = hashlib.sha256(f.read()).hexdigest()
    
    assert curr_hash == EXPECTED_SHA256, (
        f"CRITICAL: gold_test_set.csv modified! Hash: {curr_hash} != {EXPECTED_SHA256}"
    )
    print(f"Verified Frozen Gold Hash: {curr_hash} (MATCH)")

    df_gold = pd.read_csv(GOLD_ORIGINAL_PATH)
    assert len(df_gold) == 29, f"Expected 29 gold clips, got {len(df_gold)}"

    corrections_df = pd.DataFrame(CORRECTIONS_DATA)
    merged = df_gold.merge(corrections_df, on="clip_id", how="left")
    merged = merged.rename(columns={
        "transcript": "original_transcript",
        "intent": "original_intent"
    })

    cols = [
        "clip_id",
        "original_transcript",
        "original_intent",
        "corrected_transcript",
        "corrected_intent",
        "language",
        "notes"
    ]
    merged = merged[cols]
    merged.to_csv(CORRECTIONS_PATH, index=False)
    print(f"Successfully generated versioned corrections: {CORRECTIONS_PATH} ({len(merged)} rows)")
    print(f"Gold test set remains 100% frozen and untouched.")


if __name__ == "__main__":
    main()

