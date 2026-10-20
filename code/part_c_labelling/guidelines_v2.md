<!-- guidelines_v2.md: Revised after Round 1 disagreement analysis.
     Key changes from v1 are marked with [REVISED]. -->

# Annotation Guidelines v2
## Voice Helpdesk ASR — CS203 Project 5
**Date**: 2026-10-17  
**Version**: v2 (used in Round 2)  
**Changes from v1**: See Section 7 below for detailed revision rationale.

---

## 1. Purpose
Label code-mixed English/Hindi/Gujarati helpdesk speech queries with:
1. **Transcript**: Write exactly what was said
2. **Intent**: Choose the primary helpdesk category

---

## 2. Script Rules (Which Script for Which Language)

| Language | Script | Example words |
|----------|--------|---------------|
| Hindi words | Devanagari | मेस, छात्रावास, प्रवेश, दाखिला |
| Gujarati words | Gujarati script | મેસ, હૉસ્ટેલ, પ્રવેશ |
| English words | Roman (Latin) | admission, hostel, WiFi, fee |
| Mixed sentence | Per-word rule | "मेरा hostel room कब मिलेगा?" |

**Rule**: Each word gets the script of the language it belongs to. Do NOT transliterate English into Devanagari or Devanagari into Latin.

---

## 3. Transcript Normalisation Rules

- **Abbreviations**: Expand common administrative abbreviations — "CS dept" → "CS department", "admin" → "administration". Keep institutional proper nouns as-is ("IIT", "LDAP").
- **Numbers**: Write as spoken — "five hundred rupees", not "₹500".
- **Fillers [REVISED in v2]**: ALWAYS omit fillers: `um`, `uh`, `hmm`, `haan`, `huh`, `ha`.
- **Repeated words**: Transcribe once if accidental stutter ("aaa admission admission" → "admission").
- **Incomplete words**: Transcribe as heard ("adm-" when speaker cuts off).
- **Background noise**: Mark with `[NOISE]`
- **Background music**: Mark with `[MUSIC]`
- **Unintelligible word**: Mark with `[UNK]`
- **Fully unintelligible clip**: Mark `[UNK]` for entire transcript

---

## 4. Intent Definitions

| Intent | Description | Typical keywords |
|--------|-------------|-----------------|
| **admissions** | Admission process, forms, deadlines, seat availability, fee structure | admission, apply, seat, merit, form, deadline, tuition fee |
| **hostel_mess** | Hostel rooms, mess food/timings, hostel complaints, warden, laundry | hostel, mess, room, warden, food, allotment, laundry, rebate |
| **it_support** | WiFi, email/accounts, software licenses, printers, lab PCs, HPC | WiFi, password, account, software, printer, lab, LDAP, eduroam, cluster |
| **student_services** | Library, health center, transport, student ID cards, certificates | library, doctor, bus, ID card, certificate, gym, railway concession |

**Tie-breaking [REVISED in v2]**: If a query mentions multiple categories equally, choose the FIRST mentioned topic.

---

## 5. Worked Examples

**Example 1**
- Audio: "Admission ke liye konsa form fill karna hai?"
- Transcript: `Admission के लिए कौनसा form fill करना है?`
- Intent: `admissions`

**Example 2**
- Audio: "Maru hostel room number shu chhe?"
- Transcript: `મારો hostel room number શું છે?`
- Intent: `hostel_mess`

**Example 3**
- Audio: "WiFi ka password kya hai mujhe connect karna hai"
- Transcript: `WiFi का password क्या है मुझे connect करना है`
- Intent: `it_support`

**Example 4**
- Audio: "Library books kab return karna hai?"
- Transcript: `Library books कब return करना है?`
- Intent: `student_services`

**Example 5**
- Audio: "[loud noise] ...fee submit... [inaudible]..."
- Transcript: `[NOISE] fee submit [UNK]`
- Intent: `admissions`

---

## 6. Edge Cases

- **Multi-topic query**: Follow Section 7.3 first-mention rule.
- **Completely inaudible**: Transcript = `[UNK]`, Intent = best guess from context.
- **Non-target language**: Transcribe in native script, flag in notes.

---

## 7. Changes from v1 [REVISED]

Based on Round 1 disagreement analysis (see `supporting_files/agreement_calculations/agreement_report.json`):

### 7.1 Filler words [REVISED]
- **v1 Rule**: "OMIT unless they affect meaning"
- **v2 Rule**: **Always omit** the following conversational filler tokens: `um`, `uh`, `hmm`, `haan`, `huh`, `ha`.
- **Reason**: In Round 1, annotators disagreed on whether "haan" was affirmative or a filler pause. Enforcing strict deletion eliminated 7 WER discrepancies.

### 7.2 Code-mixed Hindi words in Roman script [REVISED]
- **v1 Rule**: Ambiguous on colloquial Hindi words often texted in Latin script.
- **v2 Rule**: If a speaker utters a Hindi word colloquially, write it in Devanagari (e.g., `मेरा hostel` rather than `mera hostel`). Institutional acronyms (WiFi, LDAP, ERP) remain in Roman script.
- **Reason**: Standardized lexical representation across both annotators.

### 7.3 Multi-topic intent tie-breaking [REVISED]
- **v1 Rule**: "Choose dominant topic" (subjective when topics have equal emphasis).
- **v2 Rule**: If two topics are equally prominent, choose the **FIRST mentioned topic**.
- **Reason**: Annotators disagreed on 8 dual-intent queries in Round 1 (e.g., WiFi + mess rebate). The first-mention rule eliminated ambiguity and brought Cohen's kappa to 1.000 in Round 2.

### 7.4 Partial sentences [REVISED]
- **v2 Rule**: If the speaker restarts a sentence mid-clip, transcribe both clauses. Do not truncate at clause boundaries.
