<!-- guidelines_v1.md: First-round annotation guidelines.
     Used in Round 1 labelling.
     Revised to v2 after disagreement analysis. See guidelines_v2.md. -->

# Annotation Guidelines v1
## Voice Helpdesk ASR — CS203 Project 5
**Date**: 2026-10-14
**Version**: v1 (used in Round 1)

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

**Rule**: Each word gets the script of the language it belongs to. Do NOT transliterate.

---

## 3. Transcript Normalisation Rules

- **Abbreviations**: Expand — "CS dept" → "CS department", "IIT" → keep as-is (proper noun)
- **Numbers**: Write as spoken — "five hundred rupees", not "₹500"
- **Fillers**: OMIT unless they affect meaning — um, uh, hmm → delete
- **Repeated words**: transcribe once — "aaa admission admission" → "admission"
- **Incomplete words**: transcribe as heard — "adm-" (speaker cut off)
- **Background noise**: `[NOISE]`
- **Background music**: `[MUSIC]`
- **Unintelligible word**: `[UNK]`
- **Fully unintelligible clip**: `[UNK]` for entire transcript

---

## 4. Intent Definitions

| Intent | Description | Typical keywords |
|--------|-------------|-----------------|
| **admissions** | Admission process, forms, deadlines, seat availability, fee structure | admission, apply, seat, merit, form, deadline |
| **hostel_mess** | Hostel rooms, mess food/timings, hostel complaints, warden | hostel, mess, room, warden, food, allotment |
| **it_support** | WiFi, email/accounts, software licenses, printers, lab PCs | WiFi, password, account, software, printer, lab |
| **student_services** | Library, health center, transport, student ID cards, certificates | library, doctor, bus, ID card, certificate |

**When in doubt**: Choose the DOMINANT/PRIMARY topic of the query.

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

- **Multi-topic query**: "WiFi kaam nahi kar raha aur mess khana bhi kharab tha" → Label dominant topic: `it_support` (mentioned first, longer)
- **Completely inaudible**: Transcript = `[UNK]`, Intent = best guess from any audible word, note in comments
- **Non-target language** (e.g., Marathi): Transcribe in appropriate script, flag in Label Studio comments
