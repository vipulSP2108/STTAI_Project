"""Local Streamlit UI for the revised release API."""

import json
import os
from pathlib import Path

import httpx
import streamlit as st

from revised_data import ROOT, examples, release_rows


API = "http://127.0.0.1:8000"
AUDIO_DIR = Path(os.getenv("RELEASE_AUDIO_DIR", ROOT / "revised_audio"))
VALIDATION_JSON = Path(os.getenv("RELEASE_VALIDATION_JSON", "/evidence/revised_validation.json"))

st.set_page_config(page_title="Revised Voice Helpdesk")
st.title("Voice Helpdesk")
try:
    response = httpx.get(f"{API}/version", timeout=4)
    response.raise_for_status()
    version = response.json()
except httpx.HTTPError:
    st.error("The local inference API is unavailable. Check the container logs and refresh.")
    st.stop()

st.caption(f"{version['model_version']} · {version['git_commit']} · {version['source_tree']}")
source = st.radio("Audio input", ("Example", "Upload WAV", "Microphone"), horizontal=True)
data = None
if source == "Example":
    sample = st.selectbox("Validation example", examples(release_rows()), format_func=lambda row: row["intent"].replace("_", " "))
    audio = AUDIO_DIR / f"{sample['uuid']}.wav"
    if audio.is_file():
        data = audio.read_bytes()
        st.audio(data, format="audio/wav")
    else:
        st.info("Examples are included in the release image. You can upload a WAV here.")
elif source == "Upload WAV":
    upload = st.file_uploader("WAV file", type=["wav"],
                              help="Mono and stereo WAVs are converted automatically. Maximum upload size is 12 MiB.")
    data = upload.getvalue() if upload else None
else:
    recording = st.audio_input("Record a helpdesk question")
    data = recording.getvalue() if recording else None

if st.button("Transcribe and route", disabled=data is None):
    try:
        with st.spinner("Decoding on the local CPU"):
            response = httpx.post(f"{API}/predict", files={"file": ("input.wav", data, "audio/wav")}, timeout=180)
            response.raise_for_status()
        result = response.json()
    except httpx.HTTPStatusError as error:
        st.error(error.response.json().get("detail", "The local API rejected this request."))
    except httpx.HTTPError:
        st.error("Could not reach the local inference API.")
    else:
        st.write(result["transcript"] or "No speech decoded")
        st.write(f"Intent · {result['intent'] or 'Unrouted'}")
        st.metric("Routing confidence", f"{result['confidence']:.1%}")
        st.metric("CPU latency", f"{result['latency_ms']:.0f} ms")
        st.write(f"CPU real-time factor · {result['rtf']}")

with st.expander("Offline validation results"):
    if VALIDATION_JSON.is_file():
        report = json.loads(VALIDATION_JSON.read_text(encoding="utf-8"))
        if any(report.get(key) != version[key] for key in version):
            st.warning("The saved validation result describes a different model or build.")
        else:
            st.json({key: report[key] for key in ("split", "sample_count", "wer", "cer", "intent_accuracy", "intent_macro_f1")})
    else:
        st.info("Run the release validator and mount its JSON to display the measured results.")
