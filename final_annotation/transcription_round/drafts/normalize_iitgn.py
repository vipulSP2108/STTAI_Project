"""User-requested named-entity corrections; no transcription of unheard speech."""
import re

# Specific recognizable service-name errors in the current draft. Other greetings
# (Hello sir, a parent introducing themselves, IT Cell, etc.) are left intact.
PHRASES = [
    ("हेलो आईटीजी एंड हेल्पडेस्ट", "Hello IIT GN Helpdesk"),
    ("हेलो आईटीजी एंड हेल्प डेस्ट", "Hello IIT GN Helpdesk"),
    ("હેલો આયેટી જેન હેલ્પ ડેસ્", "Hello IIT GN Helpdesk"),
    ("हेलो आईएटीजी एंड एलब्डस", "Hello IIT GN Helpdesk"),
    ("allow hydrogen help desk", "Hello IIT GN Helpdesk"),
    ("Hello, I at Aegean Help Desk", "Hello, IIT GN Helpdesk"),
    ("Hello, I am Dijan Haldas", "Hello, IIT GN Helpdesk"),
    ("हेलो आर्टी जैन हेल्प लेस्ट", "Hello IIT GN Helpdesk"),
    ("हेलो आईडीजन हेल्पलेस", "Hello IIT GN Helpdesk"),
    ("हेलो आईटीजन हेल्पडेस्क", "Hello IIT GN Helpdesk"),
    ("हेलो आईएटीजन हेल्पडस", "Hello IIT GN Helpdesk"),
    ("हेलो आईटीजी एंड हेल्पडिस्क", "Hello IIT GN Helpdesk"),
    ("हेलो आईटीजी एंड हेल्प बेस्क", "Hello IIT GN Helpdesk"),
    ("हेलो आईटीजी एंड हेल्प डिस्क", "Hello IIT GN Helpdesk"),
    ("हेलो आईएटीजी एंड हेल्पडेस्ट", "Hello IIT GN Helpdesk"),
    ("हेलो आर्डिजिन हेल्पडस", "Hello IIT GN Helpdesk"),
    ("हेलो आईटी जी एंड हेल्पेस", "Hello IIT GN Helpdesk"),
    ("हेलो आईटी जैन हेल्प दिस्ट", "Hello IIT GN Helpdesk"),
    ("आया तिगांति नगर वॉइस हेल्प डिस्क", "IIT GN Voice Helpdesk"),
    ("hello iot general best", "Hello IIT GN Helpdesk"),
    ("हेलो आईटी जिन हेल्प डेस्क", "Hello IIT GN Helpdesk"),
    ("हेलो आईएडीजी इन हिल्देस", "Hello IIT GN Helpdesk"),
    ("हेलो आईटी जैनल हेल्पडेस्ट", "Hello IIT GN Helpdesk"),
    ("हेलो आईएटीजी एंड हेल्प डेस्क", "Hello IIT GN Helpdesk"),
    ("हेलो आयोटिजियन हेल्प डेस", "Hello IIT GN Helpdesk"),
    ("हेलो आईएटीजन हेल्प देस्ट", "Hello IIT GN Helpdesk"),
    ("hello iot gene help desk", "Hello IIT GN Helpdesk"),
    ("हेलो आईएटीजी एन हेल्प इस", "Hello IIT GN Helpdesk"),
    ("हेलो आईटी जी एंड हेल्प देस्प", "Hello IIT GN Helpdesk"),
    ("hello atg and health test", "Hello IIT GN Helpdesk"),
    ("हेलो ITGN HealthDisk", "Hello IIT GN Helpdesk"),
]

ENTITY_VARIANTS = [
    "आयाटी घांदी नगर",
    "IIT Gandhinagar", "IIT Gandhi Nagar", "IIT Gandhianaga", "IIT kandinagar", "IIT kandinaga",
    "IIT गांधी नगर", "IIT गंधिनागर", "IIT गंधी नगर", "IIT ગાંધી નાકે", "IIT ગાંતી નાગા", "IIT ઘાની નગર",
    "आयाटी गहनिरगर", "आयोटी घंधी नगर", "आईएटी गांधिनगर", "आयाटी गांधी नगर",
    "आयाटी अन्नी नगर", "आईएटी गांधी नगर", "आईटी गंजी नगर", "આયટી ગા�", "આયટી ગાંધીનગર",
]


def normalize(text):
    edits = []
    def replace(pattern, replacement, label):
        nonlocal text
        def apply(match):
            old = match.group()
            new = replacement(match) if callable(replacement) else replacement
            if old != new:
                edits.append({"kind": "user_requested_entity_normalization", "before": old, "after": new, "rule": label})
            return new
        text = re.sub(pattern, apply, text, flags=re.IGNORECASE)
    for old, new in PHRASES:
        replace(re.escape(old), new, "recognized_service_name_variant")
    for variant in sorted(ENTITY_VARIANTS, key=len, reverse=True):
        replace(re.escape(variant), "IIT GN", "institution_name_variant")
    replace(r"\b(?:IIT\s+Jain|ITGN|IRTGN|IDGN|IATG\s+and|ITG\s+and|IT\s+gen|IT\s+GN)\b", "IIT GN", "acronym_misrecognition")
    replace(r"\bIIT\s*G\s*N\b", "IIT GN", "acronym_spacing")
    replace(r"IIT GN[ ,]*(?:U\.S\.\s+Health\s*desk|voice\s+over\s+desk|voice\s+desk)", "IIT GN Voice Helpdesk", "recognized_voice_helpdesk_variant")
    replace(r"IIT GN[ ,]*(voice\s*[, ]*help\s*desk)", "IIT GN Voice Helpdesk", "voice_helpdesk_spacing")
    replace(r"IIT GN[ ,]*(?:help\s*desk|health\s*desk|healthdisk)", "IIT GN Helpdesk", "helpdesk_spacing_or_misrecognition")
    for native in ["वॉइस हेल्प डिस्क", "वाइस हेल्प डेस्क", "वॉइस हेल्प डेस्क", "વોય્સ હેલ્પ ડેસ્ક", "વોઈસ હેલ્પ"]:
        replace(re.escape("IIT GN " + native), "IIT GN Voice Helpdesk", "recognized_voice_helpdesk_native_rendering")
    replace(r"\bhello(?= IIT GN\b)", "Hello", "greeting_capitalization")
    replace(r"^(?:कि लंबर|हुआ है|करूं|करें|कि|average|portal|pro)\s+(?=Hello IIT GN\b)", "", "greeting_decoder_prefix_cleanup")
    return text, edits
