#!/usr/bin/env python3
"""generate_diverse_prompts.py - Generates realistic, diverse, code-mixed helpdesk prompts without template leakage."""

import json
import os
import random

PROMPTS = {
    "admissions": [
        "M.Tech data science program ka cutoff kitna gaya tha last year GATE score pe?",
        "PhD interview call letter kab tak update hoga portal pe?",
        "Sir NRI sponsored candidate ke liye alag se form bharna hoga ya common portal hai?",
        "Can international students apply through the regular online portal or is there a separate office?",
        "Written test offline campus me hoga ya online proctored test conduct kar rahe ho?",
        "Application fee submit ho gayi par transaction status pending dikha raha hai.",
        "Admission brochure me fee waiver eligibility criteria kya diya hua hai?",
        "M.Tech early admit batch ka induction schedule kab announce hoga?",
        "Is there any provision for part-time PhD admission for industry professionals?",
        "Document verification ke time provisional certificate chalega ya original degree mandatory hai?"
    ],
    "hostel_mess": [
        "Room key ghum ho gayi hai, duplicate key banwane ke liye kahan jana padega?",
        "Mess hall 2 me night dinner ka timing kya hai weekend pe?",
        "Mess rebate apply kiya tha portal pe, discount next month ke bill me adjust hoga?",
        "AC maintenance team ko room 304 me bhejo please cooling bilkul nahi ho rahi.",
        "Hostel block 7 ke washing machine floor 2 pe water drainage issue aa raha hai.",
        "Warden sir se evening me milne ka open hours timing kya hai?",
        "Room change request letter submit karna hai special medical grounds pe.",
        "Mess food menu me Jain food options available rehte hain ya request karni padti hai?",
        "Laundry clothes dry karne ke liye drying area me extra racks lagwa do.",
        "Late entry gate pass apply karne ke baad approval status kahan show karega?"
    ],
    "it_support": [
        "Eduroam WiFi connection connect ho ke bar bar disconnect ho raha hai Android phone pe.",
        "LDAP institute account password expire ho gaya, reset link personal email pe nahi aa rahi.",
        "Academic block computer lab me printer paper jam ho gaya hai aur print stuck hai.",
        "Campus network ke bahar se IEEE Xplore access karne ke liye VPN client kaise configure karein?",
        "Lab PC me Ubuntu dual boot bootloader corrupt ho gaya hai boot nahi le raha.",
        "Student webmail quota 95% full dikha raha hai, archiving kaise enable karein?",
        "Hostel LAN port me ethernet cable lagane par no internet access show ho raha hai.",
        "MATLAB license renewal server unreachable error throw kar raha hai.",
        "PyTorch GPU cluster access ke liye Slurm account approval kahan se lena hoga?",
        "Institute email ID par two factor authentication reset karwana hai phone lost ho gaya."
    ],
    "student_services": [
        "Passport renewal ke liye bonafide certificate issue karwane ka procedure kya hai?",
        "Campus shuttle bus Chandkheda metro station ke liye kitne baje depart hoti hai?",
        "Health center pharmacy me prescribed medicine out of stock hai kab tak refill hoga?",
        "Student ID card library me drop ho gaya tha, lost and found register kahan hai?",
        "Railway concession form countersign karwane ke liye student affairs office kab khula rehta hai?",
        "Gymnasium trainer evening timing me available rehte hain kya?",
        "Annual sports meet registration deadline kab tak extend hui hai?",
        "Medical insurance card claim settlement ke liye TPA contact number share kar do.",
        "Library me reserve section ki book kitne days ke liye issue karwa sakte hain?",
        "Bank of India campus branch me new student savings account open karwana hai."
    ]
}

def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_json = os.path.join(root, 'data', 'diverse_helpdesk_prompts.json')
    out_txt = os.path.join(root, 'code', 'scripts', 'helpdesk_prompts.txt')
    
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(PROMPTS, f, indent=2, ensure_ascii=False)
        
    flat_list = []
    for cat, items in PROMPTS.items():
        for item in items:
            flat_list.append(f"[{cat}] {item}")
            
    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(flat_list) + '\n')
        
    print(f"Generated {len(flat_list)} diverse, natural helpdesk prompts across 4 domains.")
    print(f"Saved to: {out_json} and {out_txt}")

if __name__ == '__main__':
    main()

