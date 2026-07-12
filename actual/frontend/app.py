import streamlit as st
import requests
import base64
import io
import secrets
from datetime import datetime
from PIL import Image

# --- Configuration ---
FASTAPI_URL = "http://localhost:8000/analyze"

# --- Page Configuration ---
st.set_page_config(
    page_title="DermaScan AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Session bookkeeping ---
if "session_id" not in st.session_state:
    st.session_state.session_id = secrets.token_hex(3).upper()
if "result" not in st.session_state:
    st.session_state.result = None
if "result_key" not in st.session_state:
    st.session_state.result_key = None

# =============================================================================
# STYLE
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
  --bg-page: #F4F7F9;
  --bg-panel: #FFFFFF;
  --border: #E2E8F0;
  --ink: #0F172A;
  --ink-muted: #64748B;
  --accent: #0EA5E9;
  --accent-strong: #0284C7;
  --accent-light: #E0F2FE;
  --viewfinder-bg: #0B1120;
  --sev-low: #10B981;
  --sev-mod: #F59E0B;
  --sev-high: #EF4444;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: var(--bg-page); }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1180px; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: var(--ink) !important; }

/* Hero Banner */
.hero-banner {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 32px;
  background: linear-gradient(rgba(15, 23, 42, 0.75), rgba(15, 23, 42, 0.9)), url('https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=2000&q=80') center/cover;
  box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
  padding: 32px 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  color: white;
}
.header-left { display: flex; align-items: center; gap: 20px; }
.logo-img { width: 52px; height: 52px; filter: drop-shadow(0 0 8px rgba(14,165,233,0.5)); }
.app-title { font-family: 'Space Grotesk', sans-serif; font-size: 28px; font-weight: 700; letter-spacing: 0.02em; line-height: 1.2; }
.app-subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; font-weight: 400; }
.header-right { text-align: right; font-family: 'IBM Plex Mono', monospace; }
.session-id { font-size: 13px; font-weight: 600; letter-spacing: 0.05em; color: var(--accent); background: rgba(14,165,233,0.15); padding: 6px 12px; border-radius: 20px; border: 1px solid rgba(14,165,233,0.3); }
.session-date { font-size: 12px; color: #94A3B8; margin-top: 10px; }

/* Eyebrow labels */
.eyebrow { font-family: 'IBM Plex Mono', monospace; font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-muted); margin-bottom: 16px; display: flex; align-items: center; font-weight: 600; }
.eyebrow::before { content: ''; display: inline-block; width: 8px; height: 8px; background: var(--accent); border-radius: 50%; margin-right: 10px; flex-shrink: 0; box-shadow: 0 0 6px var(--accent); }

/* Panels */
.panel { background: var(--bg-panel); border: 1px solid var(--border); border-radius: 12px; padding: 28px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03); }

/* File uploader */
[data-testid="stFileUploaderDropzone"], [data-testid="stFileUploadDropzone"] {
  background: #FFFFFF !important;
  border: 2px dashed #CBD5E1 !important;
  border-radius: 12px !important;
  transition: border-color 0.3s ease, background 0.3s ease;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--accent) !important; background: var(--accent-light) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] div,
[data-testid="stFileUploaderDropzoneInstructions"] span { color: var(--ink-muted) !important; font-weight: 500; }

/* Buttons */
.stButton>button {
  background: var(--ink);
  color: #FFFFFF;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  width: 100%;
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 600;
  font-size: 14px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(15,23,42,0.2);
}
.stButton>button:hover { background: var(--accent); box-shadow: 0 6px 16px rgba(14,165,233,0.3); transform: translateY(-2px); }
.stButton>button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

/* Viewfinder */
.viewfinder-frame { position: relative; background: var(--viewfinder-bg); border-radius: 10px; overflow: hidden; padding: 16px; box-shadow: inset 0 0 20px rgba(0,0,0,0.5); }
.viewfinder-frame::after { content: ''; position: absolute; inset: 0; background-image: linear-gradient(rgba(14, 165, 233, 0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(14, 165, 233, 0.15) 1px, transparent 1px); background-size: 20px 20px; pointer-events: none; opacity: 0.5; }
.viewfinder-img { width: 100%; display: block; border-radius: 4px; position: relative; z-index: 1; }
.corner { position: absolute; width: 20px; height: 20px; border: 3px solid var(--accent); z-index: 2; border-radius: 2px; }
.corner-tl { top: 10px; left: 10px; border-right: none; border-bottom: none; }
.corner-tr { top: 10px; right: 10px; border-left: none; border-bottom: none; }
.corner-bl { bottom: 10px; left: 10px; border-right: none; border-top: none; }
.corner-br { bottom: 10px; right: 10px; border-left: none; border-top: none; }
.scan-line { position: absolute; left: 10px; right: 10px; height: 3px; top: 10px; background: linear-gradient(to right, transparent, #38BDF8, transparent); box-shadow: 0 0 15px 2px #0EA5E9; animation: scanSweep 2s cubic-bezier(0.4, 0, 0.2, 1) infinite; z-index: 3; border-radius: 50%; }
@keyframes scanSweep { 0% { top: 10px; opacity: 0; } 10% { opacity: 1; } 50% { top: calc(100% - 13px); } 90% { opacity: 1; } 100% { top: 10px; opacity: 0; } }
.viewfinder-caption { font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-muted); text-align: center; margin-top: 12px; font-weight: 600; }

/* Empty / processing states */
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 40px 20px; border: 2px dashed #CBD5E1; border-radius: 12px; background: #FFFFFF; color: var(--ink-muted); min-height: 280px; }
.empty-image { width: 100px; height: 100px; object-fit: cover; border-radius: 50%; margin-bottom: 20px; border: 4px solid var(--bg-page); box-shadow: 0 8px 16px rgba(0,0,0,0.06); }
.empty-state-text { font-size: 13.5px; max-width: 280px; line-height: 1.6; font-family: 'Inter', sans-serif; font-weight: 500; }

.processing { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px; border: 2px solid var(--accent-light); border-radius: 12px; background: #FFFFFF; }
.spinner { width: 40px; height: 40px; border: 4px solid var(--accent-light); border-top: 4px solid var(--accent); border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 16px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.processing-text { font-family: 'IBM Plex Mono', monospace; font-size: 13px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink); font-weight: 600; }

/* Gauge */
.gauge-header { display: flex; justify-content: space-between; align-items: baseline; }
.gauge-label { font-family: 'IBM Plex Mono', monospace; font-size: 12px; letter-spacing: 0.12em; color: var(--ink-muted); text-transform: uppercase; font-weight: 600; }
.gauge-readout { font-family: 'IBM Plex Mono', monospace; font-size: 32px; font-weight: 700; }
.gauge-readout-max { font-size: 16px; color: var(--ink-muted); font-weight: 500; }
.gauge-track { position: relative; height: 12px; background: #F1F5F9; border-radius: 6px; margin: 16px 0 8px; overflow: hidden; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1); }
.gauge-fill { height: 100%; border-radius: 6px; transform-origin: left; animation: fillGrow 1.2s cubic-bezier(.16,1,.3,1) forwards; box-shadow: 0 0 10px rgba(255,255,255,0.5) inset; }
@keyframes fillGrow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
.gauge-footer { display: flex; justify-content: space-between; font-family: 'Inter', sans-serif; font-size: 11px; color: #94A3B8; font-weight: 600; text-transform: uppercase; }
.gauge-verdict { font-family: 'IBM Plex Mono', monospace; font-size: 14px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 16px; text-align: right; }

/* Findings */
.finding-item { display: flex; align-items: center; gap: 16px; padding: 14px 0; border-bottom: 1px solid var(--border); }
.finding-item:last-child { border-bottom: none; }
.finding-index { font-family: 'IBM Plex Mono', monospace; font-size: 12px; font-weight: 600; color: var(--accent); background: var(--accent-light); padding: 4px 8px; border-radius: 4px; }
.finding-name { font-size: 15px; color: var(--ink); font-weight: 600; }
.empty-note { font-family: 'Inter', sans-serif; font-size: 14px; color: var(--ink-muted); padding: 10px 0; font-style: italic; }

/* Clinical note */
.clinical-note { border-left: 4px solid var(--accent); background: var(--accent-light); padding: 20px 24px; border-radius: 0 8px 8px 0; margin-top: 24px; }
.clinical-note-label { font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--accent-strong); font-weight: 700; margin-bottom: 10px; }
.clinical-note-body { font-size: 14.5px; line-height: 1.7; color: var(--ink); font-weight: 500; }

[data-testid="stAlert"] { border-radius: 8px; }

.app-footer { margin-top: 60px; padding-top: 24px; border-top: 1px solid var(--border); font-family: 'Inter', sans-serif; font-size: 12px; color: var(--ink-muted); line-height: 1.6; text-align: center; }

@media (prefers-reduced-motion: reduce) {
  .scan-line, .gauge-fill, .spinner { animation: none !important; }
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HELPERS
# =============================================================================
def to_data_uri(raw_bytes: bytes, fallback_mime: str = "image/png") -> str:
    try:
        fmt = Image.open(io.BytesIO(raw_bytes)).format
        mime = f"image/{fmt.lower()}" if fmt else fallback_mime
    except Exception:
        mime = fallback_mime
    b64 = base64.b64encode(raw_bytes).decode()
    return f"data:{mime};base64,{b64}"


def annotated_data_uri(b64_str: str) -> str:
    raw = base64.b64decode(b64_str)
    fmt = (Image.open(io.BytesIO(raw)).format or "PNG").lower()
    return f"data:image/{fmt};base64,{b64_str}"


def severity_meta(score: int):
    if score <= 30:
        return "Low Priority", "var(--sev-low)"
    elif score <= 60:
        return "Moderate Priority", "var(--sev-mod)"
    return "High Priority", "var(--sev-high)"


def viewfinder_html(data_uri: str, caption: str, scanning: bool = False) -> str:
    scan = '<div class="scan-line"></div>' if scanning else ""
    return f"""
    <div class="viewfinder-frame">
      <span class="corner corner-tl"></span>
      <span class="corner corner-tr"></span>
      <span class="corner corner-bl"></span>
      <span class="corner corner-br"></span>
      <img src="{data_uri}" class="viewfinder-img" />
      {scan}
    </div>
    <div class="viewfinder-caption">{caption}</div>
    """


def processing_html() -> str:
    return """
    <div class="processing">
      <div class="spinner"></div>
      <div class="processing-text">Running AI Analysis Model...</div>
    </div>
    """


def empty_html(text: str, img_url: str) -> str:
    return f"""
    <div class="empty-state">
      <img src="{img_url}" class="empty-image" />
      <div class="empty-state-text">{text}</div>
    </div>
    """


def gauge_html(score: int, label: str, color: str) -> str:
    return f"""
    <div class="gauge-header">
      <span class="gauge-label">Severity Index</span>
      <span class="gauge-readout" style="color:{color}">{score}<span class="gauge-readout-max">/100</span></span>
    </div>
    <div class="gauge-track">
      <div class="gauge-fill" style="width:{score}%; background:{color};"></div>
    </div>
    <div class="gauge-footer"><span>Low</span><span>Mod</span><span>High</span></div>
    <div class="gauge-verdict" style="color:{color}">{label}</div>
    """


def findings_html(conditions: list) -> str:
    if not conditions:
        return '<div class="empty-note">No remarkable clinical findings detected in specimen.</div>'
    items = "".join(
        f'<div class="finding-item"><span class="finding-index">{i:02d}</span>'
        f'<span class="finding-name">{c.replace("_", " ").title()}</span></div>'
        for i, c in enumerate(conditions, 1)
    )
    return items


def note_html(text: str) -> str:
    return f"""
    <div class="clinical-note">
      <div class="clinical-note-label">Clinical Assessment Notes</div>
      <div class="clinical-note-body">{text}</div>
    </div>
    """


def reading_html(score: int, label: str, color: str, conditions: list, recommendation: str) -> str:
    return f"""
    <div class="panel">{gauge_html(score, label, color)}</div>
    <div class="panel" style="margin-top:20px;">
      <div class="eyebrow" style="margin-bottom:12px;">Detected Anomalies</div>
      {findings_html(conditions)}
    </div>
    {note_html(recommendation)}
    """


# =============================================================================
# HEADER
# =============================================================================
date_str = datetime.now().strftime("%d %b %Y — %H:%M")
st.markdown(f"""
<div class="hero-banner">
  <div class="header-left">
    <!-- Clean SVG icon for the logo -->
    <svg class="logo-img" viewBox="0 0 24 24" fill="none" stroke="#0EA5E9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <circle cx="12" cy="12" r="6"></circle>
        <circle cx="12" cy="12" r="2"></circle>
    </svg>
    <div>
      <div class="app-title">DERMASCAN AI</div>
      <div class="app-subtitle">Advanced Dermatological Screening Engine</div>
    </div>
  </div>
  <div class="header-right">
    <div class="session-id">SESSION #DS-{st.session_state.session_id}</div>
    <div class="session-date">{date_str}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# LAYOUT
# =============================================================================
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="eyebrow">Specimen Intake Portal</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload skin image",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
    )
    image_slot = st.empty()
    st.markdown("<br>", unsafe_allow_html=True)
    button_slot = st.empty()

with col_right:
    st.markdown('<div class="eyebrow">Analysis & Diagnostics</div>', unsafe_allow_html=True)
    result_slot = st.empty()

# =============================================================================
# LOGIC
# =============================================================================
# Images used for polished empty states
EMPTY_IMG_UPLOAD = "https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=300&q=80"
EMPTY_IMG_READY = "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?auto=format&fit=crop&w=300&q=80"

if uploaded_file is not None:
    current_key = f"{uploaded_file.name}-{uploaded_file.size}"
    original_uri = to_data_uri(uploaded_file.getvalue())

    image_slot.markdown(viewfinder_html(original_uri, "Specimen Ready for Analysis"), unsafe_allow_html=True)
    analyze_clicked = button_slot.button("Run AI Diagnostics")

    if analyze_clicked:
        image_slot.markdown(viewfinder_html(original_uri, "Scanning Specimen Layers…", scanning=True), unsafe_allow_html=True)
        result_slot.markdown(processing_html(), unsafe_allow_html=True)

        try:
            files = {"file": uploaded_file.getvalue()}
            response = requests.post(FASTAPI_URL, files=files, timeout=30)
            response.raise_for_status()
            st.session_state.result = response.json()
            st.session_state.result_key = current_key
        except Exception as e:
            st.session_state.result = None
            st.session_state.result_key = None
            image_slot.markdown(viewfinder_html(original_uri, "Original Specimen"), unsafe_allow_html=True)
            result_slot.error(f"Analysis failed to process via API: {e}")

    if st.session_state.result_key == current_key and st.session_state.result:
        result = st.session_state.result

        display_uri, caption = original_uri, "Original Specimen"
        if result.get("annotated_image"):
            try:
                display_uri = annotated_data_uri(result["annotated_image"])
                caption = "AI Map & Detection Overlay"
            except Exception:
                pass
        image_slot.markdown(viewfinder_html(display_uri, caption), unsafe_allow_html=True)

        score = result.get("severity_score", 0)
        label, color = severity_meta(score)
        conditions = result.get("detected_conditions", [])
        recommendation = result.get("recommendation", "No specific clinical recommendation available at this time.")
        result_slot.markdown(
            reading_html(score, label, color, conditions, recommendation),
            unsafe_allow_html=True,
        )
    elif not analyze_clicked:
        result_slot.markdown(empty_html("Specimen successfully loaded into viewfinder.<br><br><b>Click 'Run AI Diagnostics'</b> to generate a severity reading.", EMPTY_IMG_READY), unsafe_allow_html=True)

else:
    st.session_state.result = None
    st.session_state.result_key = None
    result_slot.markdown(empty_html("Awaiting specimen data.<br><br>Upload a high-resolution dermatological image to begin the AI screening process.", EMPTY_IMG_UPLOAD), unsafe_allow_html=True)

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("""
<div class="app-footer">
  <strong>Disclaimer:</strong> DermaScan AI provides preliminary, AI-assisted visual screening only and does not constitute a definitive medical diagnosis.<br/>
  Always consult a board-certified dermatologist for clinical evaluation and treatment.
</div>
""", unsafe_allow_html=True)