# Voice Helpdesk Annotation Guidelines & Protocol
## CS203: Software Tools and Techniques in AI — Project 5: Voice Helpdesk ASR
**Institutional Affiliation**: Indian Institute of Technology Gandhinagar (IITGN)  
**Standardized Protocol Version**: v2.1 (Comprehensive Consolidated Guidelines)  
**Target Domain**: Multilingual Campus Helpdesk Inquiries (English, Hindi, Gujarati)

---

## 1. Objective and Cognitive Sequencing

This document defines the standardized labeling protocol for the multilingual voice helpdesk speech corpus. Annotators follow a **strict two-level cognitive sequence** to eliminate category-priming bias:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       STEP 1: PERCEPTUAL GROUNDING                          │
│  1. Listen to the audio clip (Zoom waveform, hotkey: Space).               │
│  2. Select all Spoken Languages present (English, Hindi, Gujarati).        │
│  3. Type the verbatim code-mixed transcript in native scripts.              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STEP 2: SEMANTIC CLASSIFICATION                        │
│  4. Select exactly one primary Intent Category:                            │
│     [1] admissions  |  [2] hostel_mess  |  [3] it_support  |  [4] student_services │
└─────────────────────────────────────────────────────────────────────────────┘
```

> **Cognitive Sequencing Rationale**: Annotators must evaluate language mix and acoustic transcription *before* assigning an intent category. Grounding the annotator in verbatim speech prevents high-level domain assumptions from distorting linguistic perception.

---

## 2. Step 1: Spoken Language Identification

The interface provides multi-choice checkboxes with keyboard shortcuts. Annotators check all languages present in the utterance:

| Language Option | Hotkey | Script | Description |
| :--- | :---: | :---: | :--- |
| **English** | `e` | Roman | Utterance contains English syntactic phrases or sentences. |
| **Hindi** | `h` | Devanagari | Utterance contains Hindi grammatical vocabulary (हिन्दी). |
| **Gujarati** | `g` | Gujarati | Utterance contains Gujarati grammatical vocabulary (ગુજરાતી). |

### 2.1 Code-Mixing and Loanword Clarification Rules
A major source of initial annotator divergence was whether individual technical terms constitute code-mixing. The following rule resolves this:
1. **Assimilated Loanwords**: Standalone technical nouns that have been assimilated into everyday Indian collegiate speech (e.g., *"portal"*, *"hostel"*, *"password"*, *"room"*, *"ID card"*, *"ticket"*, *"mess"*, *"fee"*) do **not** trigger the `English` tag if the rest of the sentence is entirely Hindi or Gujarati.
2. **Code-Mixing Trigger**: The `English` tag **must** be selected if:
   - The speaker uses an English clause or verb phrase (e.g., *"please verify my application"*, *"how can I reset"*).
   - The utterance alternates between languages (intra-sentential code-switching).
   - An English greetings/closings phrase is present (e.g., *"Hello IITGN helpdesk"*, *"good afternoon sir"*).

---

## 3. Step 1B: Verbatim Transcription & Script Rules

### 3.1 Script Assignment (Per-Word Rule)
Transcripts must reflect exact phonological utterances using the **native script** of each word:
- **Hindi words**: Devanagari script (e.g., `प्रवेश`, `छात्रावास`, `फीस`, `कब`).
- **Gujarati words**: Gujarati script (e.g., `પ્રવેશ`, `હોસ્ટેલ`, `ઓરડો`, `ક્યારે`).
- **English words**: Latin/Roman script (e.g., `admission`, `hostel`, `WiFi`, `password`).
- **Do not transliterate**: Never write Hindi in Latin script (*"kab milega"* ❌) or English in Devanagari (*"एडमिशन"* ❌). Always write: `Admission कब मिलेगा?` ✅.

### 3.2 Normalization Rules
1. **Numbers**: Write numbers as spoken in the utterance (e.g., write `fifteen hundred rupees` or `पंद्रह सौ रुपये`, not `1500` or `₹1500`).
2. **Abbreviations**: Expand colloquial shorthand to formal spoken terms (`admin` $\rightarrow$ `administration`, `dept` $\rightarrow$ `department`). Retain institutional proper acronyms as spoken (`IITGN`, `HPC`, `VPN`, `GATE`, `JEE`, `LDAP`).
3. **Hesitations & Fillers**: Exclude non-lexical conversational fillers (`um`, `uh`, `hmm`, `haan`, `aah`) to maintain ASR acoustic ground truth.
4. **Special Acoustic Tokens**:
   - `[NOISE]`: Prominent environmental acoustic interference (fan, cafeteria chatter, door bang).
   - `[MUSIC]`: Audible background music or ringtones.
   - `[UNK]`: Completely unintelligible syllables or words.

---

## 4. Step 2: Intent Classification Taxonomy

Every helpdesk inquiry must be assigned to exactly **one** primary category:

### 4.1 `admissions` (Hotkey: `1`)
- **Scope**: Inquiries regarding prospective enrollment, institutional admission procedures, cutoff criteria, application portals, entrance exam verification, and seat allocation.
- **Core Keywords**: `admission`, `apply`, `cutoff`, `merit list`, `counseling`, `GATE score`, `JAM`, `JEE`, `seat acceptance`, `provisional offer`, `intake`, `registration form`.
- **Inclusions**: Queries about admission eligibility criteria, document verification slots for incoming candidates, and entrance fee refund rules.
- **Exclusions**: Semester fee payment for already enrolled continuing students (see `student_services`).

### 4.2 `hostel_mess` (Hotkey: `2`)
- **Scope**: Physical campus living accommodations, dining hall facilities, room maintenance, and residential welfare.
- **Core Keywords**: `hostel`, `mess`, `room allocation`, `warden`, `dining menu`, `caretaker`, `water cooler`, `AC`, `laundry`, `mess rebate`, `vacation mess`, `guest room`.
- **Inclusions**: Requests for room change, complaints regarding mess hygiene or meal schedules, rebate calculation for leaves, and parent guest house bookings.
- **Exclusions**: Network Wi-Fi issues in hostel rooms (see `it_support`).

### 4.3 `it_support` (Hotkey: `3`)
- **Scope**: Digital, network, computational, and institutional software infrastructure.
- **Core Keywords**: `WiFi`, `eduroam`, `password reset`, `institutional email`, `LDAP`, `VPN`, `HPC cluster`, `printer`, `lab computer`, `software license`, `MATLAB`, `firewall`.
- **Inclusions**: Queries about failed portal logins, two-factor authentication (2FA), network port activation, and campus cloud storage quotas.
- **Exclusions**: Physical plastic ID card reprint or lost card recovery (see `student_services`).

### 4.4 `student_services` (Hotkey: `4`)
- **Scope**: General administrative student affairs, campus amenities, health center, library access, transport, and welfare certifications.
- **Core Keywords**: `library`, `health center`, `doctor`, `ambulance`, `shuttle bus`, `student ID card`, `bonafide certificate`, `scholarship`, `grade card`, `transcripts`, `sports gym`.
- **Inclusions**: Requests for railway concession forms, medical leaves, library circulation desks, scholarship disbursement timelines, and lost-and-found.
- **Exclusions**: Direct admission offer acceptance (see `admissions`).

---

## 5. Disambiguation & Decision Boundary Rules

The empirical confusion matrix between Annotator 1 and Annotator 2 revealed four key boundary overlaps. The following hierarchical rules adjudicate all borderline queries:

### Rule 1: `it_support` vs. `student_services` (Digital Infrastructure vs. Administrative Service)
- **Principle**: If the problem relates to **software authentication, server connection, or credentials**, classify as **`it_support`**. If it relates to **institutional policy, physical documents, or office procedures**, classify as **`student_services`**.
- *Example A*: *"My student portal password is not working."* $\rightarrow$ **`it_support`** (Authentication issue).
- *Example B*: *"Where do I collect my physical grade card from student affairs?"* $\rightarrow$ **`student_services`** (Administrative paperwork).
- *Example C*: *"My RFID student card is not opening the library door."* $\rightarrow$ If the card reader does not respond: **`it_support`**; if requesting permission rights: **`student_services`**.

### Rule 2: `admissions` vs. `student_services` (Prospective Intake vs. Enrolled Student Affairs)
- **Principle**: Inquiries from **incoming/prospective candidates** regarding entrance rank, offer letters, or initial seat confirmation belong to **`admissions`**. Inquiries regarding **ongoing semester documentation, scholarships, bonafide letters, or transfer transcripts** belong to **`student_services`**.
- *Example A*: *"GATE seat acceptance proof submit kar diya hai, confirmation kab aayega?"* $\rightarrow$ **`admissions`**.
- *Example B*: *"Dean academic se bonafide certificate sign karwana hai for passport."* $\rightarrow$ **`student_services`**.

### Rule 3: `hostel_mess` vs. `student_services` (Residential Living vs. Campus Amenities)
- **Principle**: Inquiries involving **room condition, mess food, furniture, water, or hostel caretakers** belong to **`hostel_mess`**. Inquiries involving campus shuttle buses, medical centers, or recreation centers belong to **`student_services`**.
- *Example A*: *"Hostel room me water leakage hai caretaker ka number chahiye."* $\rightarrow$ **`hostel_mess`**.
- *Example B*: *"Campus shuttle bus timetable to Gandhinagar railway station."* $\rightarrow$ **`student_services`**.

### Rule 4: `admissions` vs. `hostel_mess` (Freshman Intake vs. Residential Possession)
- **Principle**: Inquiries regarding the **initial room allotment package during freshman admission week** are classified under **`hostel_mess`** if the core question is about room keys, luggage storage, or hostel reporting. They are classified under **`admissions`** only if inquiring about admission eligibility conditions or reporting dates.
- *Example*: *"Hostel reporting date and room allotment for newly admitted BTech students."* $\rightarrow$ **`hostel_mess`**.

### 5.1 Tie-Breaking Rule (Chronological Precedence & Initial Query Topic Prioritization)
If a code-mixed query spans two equally weighted categories without a single dominant theme (e.g., inquiring about prospective enrollment alongside hostel facilities, or foreign national admissions alongside scholarship relief):
- **Core Precedence Principle**: **Per annotation guidelines prioritizing the initial query topic, hence ticket is categorized under Admissions.**
- **Operational Rule**: When a query begins with an admission-related inquiry (prospective cutoffs, application forms, seat acceptance, or candidate eligibility) but subsequent clauses touch upon hostel facilities, campus amenities, or fee concession, the ticket is classified decisively under **`admissions`**. Prioritizing the initial query topic guarantees deterministic routing and prevents annotators from diverging based on secondary administrative clauses.
- *Example A*: *"Foreign national students ke liye admission requirements kya hai and scholarship details mil sakti hai?"* $\rightarrow$ **`admissions`** (Opening topic: admission intake).
- *Example B*: *"BTech admission procedure ke sath hostel allotment aur mess facilities ka kya process hai?"* $\rightarrow$ **`admissions`** (Opening topic: admission procedure).

---

## 6. Worked Annotation Examples

| Audio Speech Utterance | Tagged Languages | Verbatim Transcript | Primary Intent |
| :--- | :--- | :--- | :--- |
| *"BTech admission seat allotment cutoff list portal par kab aayegi?"* | Hindi, English | `BTech admission seat allotment cutoff list portal पर कब आएगी?` | `admissions` |
| *"Hostel Aravalli room 204 me geyser work nahi kar raha please check kijiye."* | Hindi, English | `Hostel Aravalli room 204 में geyser work नहीं कर रहा please check कीजिए।` | `hostel_mess` |
| *"Eduroam WiFi connect nahi ho raha hai invalid credentials show karta hai."* | Hindi, English | `Eduroam WiFi connect नहीं हो रहा है invalid credentials show करता है।` | `it_support` |
| *"Central library ma thi reference book issue karvani chhe process shu chhe?"* | Gujarati, English | `Central library માંથી reference book issue કરવાની છે process શું છે?` | `student_services` |
| *"Mera scholarship status verification pending hai student affairs office me."* | Hindi, English | `मेरा scholarship status verification pending है student affairs office में।` | `student_services` |
| *"Mess rebate form submit karyo hato pan account ma refund nathi aavyo."* | Gujarati, English | `Mess rebate form submit કર્યો હતો પણ account માં refund નથી આવ્યો।` | `hostel_mess` |

---

## 7. Expert Adjudication Framework & Psychometric Fatigue Mitigation (`annotator_expert`)

When independent annotators A1 and A2 disagree on intent classification across the double-annotated corpus (47 residual conflict cases):
1. Conflicting tasks are forwarded to the **Expert Adjudicator** (`annotator_expert` / A3) on Port `8083`.
2. The Adjudicator reviews the 16 kHz audio, inspects the dispute callout banner presenting both peer labels (`A1: intent` vs `A2: intent`) and language tags, and applies the disambiguation decision boundaries detailed in Section 5.

### 7.1 Single-Annotator Fatigue Mitigation & Quality Assurance
Because adjudication is conducted by a single domain expert, psychometric drift, subjective fatigue, and cognitive lapses can potentially compromise gold-standard consistency. To prevent and detect these failure modes, the `annotator_expert` environment incorporates four rigorous controls:

#### 1. Blind Test-Retest Duplication (Intra-Annotator Consistency)
- **Injection Ratio**: Exactly 8 blind duplicate tasks (17.0% repeat fraction) are sampled across all five conflict boundaries and interspersed into the adjudication queue, expanding the task count from 47 to **55 tasks**.
- **Memory Decay Guarantee**: Duplicates are separated from their first presentation by a strict minimum of **35–37 tasks** (first presentations in tasks 1–20; repeat presentations in tasks 38–55). This eliminates short-term working memory recall.
- **Obfuscation**: Task IDs, audio filenames, and dispute summaries are formatted identically without any indicator that a task is a duplicate.
- **Evaluation Metric**: Upon completion, the automated audit script computes the Intra-Annotator Concordance ($P_o^{\text{intra}}$) and Intra-Rater Cohen's $\kappa_{\text{intra}}$. Consistent ratings across repeats confirm high decisional stability ($\kappa_{\text{intra}} \ge 0.80$).

#### 2. Latency / Lead-Time Telemetry & Fatigue Detection
- Label Studio records exact active lead time (`lead_time`, in seconds) per task.
- **Cognitive Rushing Alert (< 6.0 s)**: A task completed in under 6 seconds indicates inattention or skipping the audio waveform; such clips are flagged for immediate audit.
- **Fatigue Stalling Alert (> 90.0 s)**: Tasks exceeding 90 seconds indicate cognitive fatigue, task stalling, or severe ambiguity.
- **Quartile Progression Monitoring**: Mean and median lead times are tracked across annotation quartiles (Q1: tasks 1–14; Q2: 15–28; Q3: 29–42; Q4: 43–55) to quantify fatigue slopes or pacing decay.

#### 3. Automated Psychometric Audit Script
The adjudication evaluation script at `final_annotation/annotator_expert/evaluate_expert_reliability.py` automatically computes test-retest kappa, lead-time drift, fatigue alerts, and deduplicates the 55 tasks into the authoritative 47 dispute resolutions.

