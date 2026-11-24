#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReubenSoul PeaceUnity LifeHaven — by ReubenSoul4peaceunity

Modules
  1. Fitness Training        – AI pose rep counter (camera/upload), GPS map, analytics
  2. Total Body Assessment   – vitals, risk ratios, elderly functional tests, posture photo analysis, PDF
  3. Care Portal             – resident admissions, search, PDF, optional voice summary
  4. Intake Forms            – 7-section digital admission packet, saved records, PDF
  5. Wellness & Safety       – consent-based check-ins, safe zones, mood trends, PHQ-2/GAD-2, ID card
  6. Phone Security          – guided intruder/stalkerware checkup, fix playbook, link/text scam checker
  7. Translator              – offline care phrasebook (5 languages) + optional live translation/voice
  8. Client Portal           – landing page

Environment variables (all optional)
  DB_PATH                    sqlite path (default /tmp/lifehaven.db)
  APP_PASSWORD               if set, a password gate protects the whole app
  ENABLE_EXTERNAL_TTS        "true" to allow gTTS voice (sends text to Google)
  ENABLE_EXTERNAL_TRANSLATE  "true" to allow live free-text translation (sends text to Google)
"""

import os, io, re, math, json, hmac, random
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import streamlit as st

# ───────────────────────── PAGE CONFIG (must be first st call) ─────────────────────────
st.set_page_config(
    page_title="ReubenSoul PeaceUnity LifeHaven",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────── OPTIONAL DEPENDENCIES (app never crashes on a missing one) ──
try:
    import cv2
    import mediapipe as mp
    HAS_POSE = hasattr(mp, "solutions")
except Exception:
    HAS_POSE = False
try:
    import folium
    from streamlit_folium import st_folium
    HAS_MAP = True
except Exception:
    HAS_MAP = False
try:
    from fpdf import FPDF
    HAS_PDF = True
except Exception:
    HAS_PDF = False
try:
    from gtts import gTTS
    HAS_TTS = True
except Exception:
    HAS_TTS = False
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except Exception:
    HAS_TRANSLATOR = False

EXTERNAL_TTS = os.getenv("ENABLE_EXTERNAL_TTS", "false").lower() == "true"
EXTERNAL_TRANSLATE = os.getenv("ENABLE_EXTERNAL_TRANSLATE", "false").lower() == "true"

DB_PATH = os.getenv("DB_PATH", "/tmp/lifehaven.db")
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)

# ───────────────────────── PASSWORD GATE ─────────────────────────
def gate():
    pw = os.getenv("APP_PASSWORD")
    if not pw or st.session_state.get("authed"):
        return
    entered = st.text_input("Password", type="password")
    if entered:
        if hmac.compare_digest(entered.encode("utf-8"), pw.encode("utf-8")):
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

gate()
st.warning("DEMO ONLY: Use fictional information, not real resident, child, or medical records, "
           "until you have added the access controls, encryption and legal agreements your jurisdiction requires.")

# ───────────────────────── STYLE ─────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700;900&family=Outfit:wght@300;400;500;600;700&display=swap');
:root{--bg:#030c0e;--teal:#00c9a7;--teal2:#00ffe0;--gold:#f0b429;--gold2:#ffe0a0;--sky:#7ee8fa;
--text:#e8f4f2;--muted:rgba(232,244,242,.6);--glass:rgba(255,255,255,.04);--border:rgba(0,201,167,.18);
--glow:0 0 40px rgba(0,201,167,.12)}
html,body,[class*="css"]{font-family:'Outfit',sans-serif;}
.stApp{background:radial-gradient(ellipse 70% 50% at 15% 10%,rgba(0,201,167,.08),transparent 65%),
radial-gradient(ellipse 50% 40% at 85% 80%,rgba(240,180,41,.06),transparent 60%),#030c0e;color:var(--text)}
.block-container{padding:1.5rem 2rem 4rem!important;max-width:1400px!important}
@keyframes ticker{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
.ticker-wrap{overflow:hidden;background:linear-gradient(90deg,rgba(0,80,60,.9),rgba(0,100,75,.9),rgba(0,80,60,.9));
border:1px solid rgba(0,201,167,.2);border-radius:12px;margin-bottom:24px;padding:11px 0}
.ticker-inner{display:inline-flex;animation:ticker 30s linear infinite}
.ticker-item{color:rgba(255,255,255,.9);font-size:.88rem;font-weight:500;letter-spacing:.08em;padding:0 40px;white-space:nowrap}
.ticker-dot{color:var(--teal2);margin-right:8px}
.hero{position:relative;overflow:hidden;padding:48px 36px 40px;border-radius:32px;margin-bottom:28px;
background:linear-gradient(135deg,rgba(0,201,167,.12),rgba(3,12,14,.96) 40%,rgba(240,180,41,.07));
border:1px solid rgba(0,201,167,.18);box-shadow:0 32px 80px rgba(0,0,0,.5),var(--glow)}
.hero-eyebrow{text-align:center;font-size:.78rem;font-weight:600;letter-spacing:.2em;color:var(--teal);text-transform:uppercase;margin-bottom:14px}
.hero-title{font-family:'Cormorant Garamond',serif;font-size:clamp(2.2rem,6vw,4.6rem);font-weight:900;text-align:center;line-height:1.08;
margin-bottom:14px;background:linear-gradient(135deg,var(--teal2),var(--sky) 40%,var(--gold));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero-sub{text-align:center;font-size:1.05rem;color:var(--muted);max-width:640px;margin:0 auto 24px;line-height:1.7}
.badge-row{display:flex;flex-wrap:wrap;justify-content:center;gap:8px}
.badge{padding:6px 14px;border-radius:999px;font-size:.8rem;font-weight:600;background:rgba(0,201,167,.08);border:1px solid rgba(0,201,167,.22);color:var(--teal2)}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#050f12,#030c0e)!important;border-right:1px solid var(--border)}
.sidebar-brand{text-align:center;padding:16px 8px 10px;border-bottom:1px solid var(--border);margin-bottom:14px}
.sidebar-brand-name{font-family:'Cormorant Garamond',serif;font-size:1.5rem;font-weight:900;color:var(--teal2)}
.sidebar-brand-tag{font-size:.72rem;color:var(--muted);letter-spacing:.12em;text-transform:uppercase;margin-top:2px}
.sec-eyebrow{font-size:.72rem;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:var(--teal);margin-bottom:6px}
.sec-title{font-family:'Cormorant Garamond',serif;font-size:2.2rem;font-weight:700;color:var(--text);line-height:1.2}
.sec-sub{font-size:.92rem;color:var(--muted);margin:6px 0 22px;line-height:1.6}
.card,.card-gold,.card-teal,.card-red{padding:22px;border-radius:20px;margin-bottom:18px;box-shadow:0 8px 32px rgba(0,0,0,.3)}
.card{background:var(--glass);border:1px solid var(--border)}
.card-gold{background:linear-gradient(135deg,rgba(240,180,41,.08),rgba(3,12,14,.95));border:1px solid rgba(240,180,41,.22)}
.card-teal{background:linear-gradient(135deg,rgba(0,201,167,.10),rgba(3,12,14,.95));border:1px solid rgba(0,201,167,.25)}
.card-red{background:linear-gradient(135deg,rgba(255,80,80,.12),rgba(3,12,14,.95));border:1px solid rgba(255,100,100,.35)}
.divider{height:1px;background:linear-gradient(90deg,transparent,var(--border),transparent);margin:26px 0}
.metric-row{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0}
.metric-card{padding:18px;border-radius:18px;text-align:center;background:linear-gradient(135deg,rgba(0,201,167,.09),rgba(3,12,14,.95));border:1px solid rgba(0,201,167,.18)}
.metric-val{font-family:'Cormorant Garamond',serif;font-size:2.6rem;font-weight:700;color:var(--teal2);line-height:1}
.metric-label{font-size:.78rem;color:var(--muted);margin-top:4px;letter-spacing:.06em;text-transform:uppercase}
.rep-display{text-align:center;padding:30px 20px;border-radius:24px;background:linear-gradient(135deg,rgba(0,201,167,.12),rgba(3,12,14,.98));border:1px solid rgba(0,201,167,.25)}
.rep-number{font-family:'Cormorant Garamond',serif;font-size:6rem;font-weight:900;color:var(--teal2);line-height:1}
.rep-angle{font-size:1.8rem;font-weight:600;color:var(--sky);margin-top:8px}
.rep-stage{font-size:1rem;font-weight:600;margin-top:10px;letter-spacing:.06em}
.intake-head{font-family:'Cormorant Garamond',serif;font-size:1.3rem;font-weight:700;color:var(--gold);margin:6px 0 12px;padding-bottom:8px;border-bottom:1px solid rgba(240,180,41,.15)}
.check-item{padding:10px 14px;margin-bottom:8px;border-radius:12px;background:var(--glass);border:1px solid var(--border);font-size:.92rem}
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{background:linear-gradient(90deg,var(--teal),#0090bb)!important;color:#030c0e!important;
border-radius:12px!important;border:0!important;font-weight:700!important;letter-spacing:.03em!important;box-shadow:0 6px 20px rgba(0,201,167,.2)!important}
.stTabs [data-baseweb="tab-list"]{gap:4px;border-bottom:1px solid var(--border)}
.stTabs [aria-selected="true"]{color:var(--teal2)!important}
.portal-hero{padding:60px 36px;border-radius:32px;text-align:center;background:linear-gradient(145deg,rgba(0,201,167,.15),rgba(3,12,14,.97) 50%,rgba(240,180,41,.1));border:1px solid rgba(0,201,167,.2)}
.portal-title{font-family:'Cormorant Garamond',serif;font-size:clamp(2rem,5vw,3.8rem);font-weight:900;background:linear-gradient(120deg,var(--teal2),var(--gold));-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:14px}
.portal-sub{color:var(--muted);font-size:1.05rem;margin-bottom:30px;line-height:1.7}
.feature-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-top:36px}
.feature-card{padding:22px 18px;border-radius:20px;text-align:center;background:rgba(255,255,255,.04);border:1px solid var(--border)}
.f-icon{font-size:2.1rem;margin-bottom:10px}.f-name{font-weight:700;color:var(--teal2);margin-bottom:6px}.f-desc{font-size:.82rem;color:var(--muted);line-height:1.5}
.footer{text-align:center;margin-top:56px;padding:22px;border-top:1px solid var(--border);color:var(--muted);font-size:.82rem;letter-spacing:.05em}
.footer b{color:var(--teal)}
</style>
""", unsafe_allow_html=True)

# ───────────────────────── DATABASE ─────────────────────────
@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS residents (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, dob TEXT, medical_info TEXT, medications TEXT,
            allergies TEXT, emergency_contact TEXT, language TEXT, created_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS intake_forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT, submitted_at TEXT, full_name TEXT, dob TEXT, gender TEXT,
            primary_language TEXT, marital_status TEXT, emergency_contact1 TEXT, emergency_contact2 TEXT,
            primary_physician TEXT, chronic_conditions TEXT, allergies TEXT, medications TEXT, immunizations TEXT,
            hospitalizations TEXT, adl_status TEXT, mobility TEXT, cognitive_status TEXT, skin_integrity TEXT,
            dietary TEXT, poa TEXT, directives TEXT, hipaa_consent TEXT, daily_routine TEXT, social_interests TEXT,
            special_equipment TEXT, transportation TEXT, device_type TEXT, security_consent TEXT, phone_concerns TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS wellness_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, dob TEXT, emergency_contact TEXT,
            medical_notes TEXT, medications TEXT, allergies TEXT, crisis_plan TEXT, consent_by TEXT,
            consent_date TEXT, stale_hours INTEGER, created_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS safe_zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT, profile_id INTEGER, label TEXT, lat REAL, lon REAL, radius_m REAL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT, profile_id INTEGER, ts TEXT, mood INTEGER, status TEXT,
            lat REAL, lon REAL, zone_status TEXT, note TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, name TEXT, kind TEXT, data TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS vitals_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, person TEXT, kind TEXT, value REAL, unit TEXT, note TEXT)""")

init_db()

# ───────────────────────── SESSION STATE ─────────────────────────
for k, v in {"reps": 0, "stage": None, "start_time": datetime.now(), "last_img": None,
             "last_pose": None, "ex_log": [], "rpe_log": []}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ───────────────────────── HELPERS ─────────────────────────
def safe(v, f="—"):
    return str(v).strip() if v is not None and str(v).strip() else f

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def angle(a, b, c):
    r = math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0])
    deg = abs(math.degrees(r))
    return 360 - deg if deg > 180 else deg

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def section_header(eyebrow, title, sub):
    st.markdown(f'<div class="sec-eyebrow">◆ {eyebrow}</div><div class="sec-title">{title}</div>'
                f'<div class="sec-sub">{sub}</div>', unsafe_allow_html=True)

def crisis_box():
    st.markdown("""<div class="card-red"><b>🚨 If someone is in immediate danger, call 911.</b><br>
• Suicide &amp; Crisis Lifeline (US): call or text <b>988</b> &nbsp;•&nbsp; Crisis Text Line: text <b>HOME</b> to <b>741741</b><br>
• Missing child: call 911, then NCMEC <b>1-800-843-5678</b> &nbsp;•&nbsp; Child abuse (Childhelp): <b>1-800-422-4453</b><br>
• Dementia / memory loss (Alzheimer's Association 24/7): <b>1-800-272-3900</b> &nbsp;•&nbsp; Eldercare Locator: <b>1-800-677-1116</b><br>
• Domestic violence hotline: <b>1-800-799-7233</b></div>""", unsafe_allow_html=True)

# ───────────────────────── PDF ─────────────────────────
_FALLBACK = {"—": "-", "–": "-", "•": "*", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "...", "°": " deg"}

if HAS_PDF:
    class LifeHavenPDF(FPDF):
        def __init__(self):
            super().__init__()
            self.set_auto_page_break(True, 15)
            folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
            files = {"": "DejaVuSans.ttf", "B": "DejaVuSans-Bold.ttf", "I": "DejaVuSans-Oblique.ttf"}
            self.unicode_ok = False
            self.fam = "Helvetica"
            if all(os.path.exists(os.path.join(folder, f)) for f in files.values()):
                try:
                    for s, f in files.items():
                        self.add_font("LifeHaven", style=s, fname=os.path.join(folder, f))
                    self.fam, self.unicode_ok = "LifeHaven", True
                except Exception:
                    pass

        def t(self, s):
            s = "" if s is None else str(s)
            s = re.sub(r"(\S{60})", r"\1 ", s)          # let very long tokens wrap
            if self.unicode_ok:
                return s
            for k, v in _FALLBACK.items():
                s = s.replace(k, v)
            return s.encode("latin-1", "replace").decode("latin-1")

        def font(self, style="", size=11):
            self.set_font(self.fam, style, size)

        def h1(self, text, size=16):
            self.font("B", size)
            self.cell(0, 10, self.t(text), new_x="LMARGIN", new_y="NEXT", align="C")

        def section(self, text):
            self.font("B", 12); self.set_fill_color(0, 100, 90); self.set_text_color(255, 255, 255)
            self.cell(0, 8, self.t("  " + text), new_x="LMARGIN", new_y="NEXT", fill=True)
            self.set_text_color(0, 0, 0); self.ln(2)

        def kv(self, k, v, kw=55):
            self.font("B", 10)
            self.cell(kw, 7, self.t(f"{k}:"), new_x="RIGHT", new_y="TOP")
            self.font("", 10)
            self.multi_cell(0, 7, self.t(v), new_x="LMARGIN", new_y="NEXT")

        def para(self, text, size=10, style=""):
            self.font(style, size)
            self.multi_cell(0, 6, self.t(text), new_x="LMARGIN", new_y="NEXT")

def pdf_bytes(p):
    return bytes(p.output())

def pdf_unavailable():
    st.error("PDF export needs the `fpdf2` package (add `fpdf2` to requirements.txt).")

# ───────────────────────── VOICE / TRANSLATION ─────────────────────────
@st.cache_data(show_spinner=False)
def _tts(text, lang):
    try:
        buf = io.BytesIO()
        gTTS(text=text, lang=lang).write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None

def voice(text, lang="en"):
    if not (HAS_TTS and EXTERNAL_TTS):
        return None
    return _tts(text, lang)

LANGS = {"English": "en", "Spanish": "es", "French": "fr", "Haitian Creole": "ht", "Portuguese": "pt"}

PHRASES = [
    ("Are you in pain?", {"es": "¿Tiene dolor?", "fr": "Avez-vous mal ?", "ht": "Èske ou gen doulè?", "pt": "Você está com dor?"}),
    ("Where does it hurt?", {"es": "¿Dónde le duele?", "fr": "Où avez-vous mal ?", "ht": "Ki kote ou fè mal?", "pt": "Onde dói?"}),
    ("Are you dizzy?", {"es": "¿Está mareado?", "fr": "Avez-vous des vertiges ?", "ht": "Èske tèt ou ap vire?", "pt": "Você está tonto?"}),
    ("Do you need water?", {"es": "¿Necesita agua?", "fr": "Avez-vous besoin d'eau ?", "ht": "Èske ou bezwen dlo?", "pt": "Você precisa de água?"}),
    ("Are you hungry?", {"es": "¿Tiene hambre?", "fr": "Avez-vous faim ?", "ht": "Èske ou grangou?", "pt": "Você está com fome?"}),
    ("Do you need the bathroom?", {"es": "¿Necesita ir al baño?", "fr": "Avez-vous besoin d'aller aux toilettes ?", "ht": "Èske ou bezwen ale nan twalèt?", "pt": "Você precisa ir ao banheiro?"}),
    ("Please take your medication.", {"es": "Por favor, tome su medicina.", "fr": "Veuillez prendre votre médicament.", "ht": "Tanpri pran medikaman ou.", "pt": "Por favor, tome o seu remédio."}),
    ("Please sit down.", {"es": "Por favor, siéntese.", "fr": "Veuillez vous asseoir.", "ht": "Tanpri chita.", "pt": "Por favor, sente-se."}),
    ("Breathe slowly.", {"es": "Respire despacio.", "fr": "Respirez lentement.", "ht": "Respire dousman.", "pt": "Respire devagar."}),
    ("Do you feel safe?", {"es": "¿Se siente seguro?", "fr": "Vous sentez-vous en sécurité ?", "ht": "Èske ou santi w an sekirite?", "pt": "Você se sente seguro?"}),
    ("Do you want me to call your family?", {"es": "¿Quiere que llame a su familia?", "fr": "Voulez-vous que j'appelle votre famille ?", "ht": "Èske ou vle m rele fanmi ou?", "pt": "Quer que eu ligue para a sua família?"}),
    ("I will help you.", {"es": "Yo le ayudo.", "fr": "Je vais vous aider.", "ht": "M ap ede w.", "pt": "Eu vou ajudar você."}),
    ("Emergency: I am calling for help.", {"es": "Emergencia: estoy llamando para pedir ayuda.", "fr": "Urgence : j'appelle de l'aide.", "ht": "Ijans: m ap rele pou èd.", "pt": "Emergência: estou chamando ajuda."}),
]
FREE_LANGS = {"Spanish": "es", "French": "fr", "Haitian Creole": "ht", "Portuguese": "pt", "Arabic": "ar",
              "Chinese (Simplified)": "zh-CN", "Vietnamese": "vi", "Tagalog": "tl", "Korean": "ko",
              "Russian": "ru", "Yoruba": "yo", "Amharic": "am", "Swahili": "sw", "English": "en"}

def translate_text(text, target):
    if not (HAS_TRANSLATOR and EXTERNAL_TRANSLATE):
        return None
    try:
        return GoogleTranslator(source="auto", target=target).translate(text)
    except Exception:
        return None

# ───────────────────────── POSE ─────────────────────────
def detect_pose(img_bytes):
    """Returns (rgb_image, landmarks_or_None). (None, None) if image can't be decoded."""
    arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return None, None
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    with mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1, min_detection_confidence=0.5) as pose:
        res = pose.process(rgb)
    return rgb, res.pose_landmarks

def draw_pose(rgb, landmarks, label=None, label_xy=None):
    out = rgb.copy()
    du = mp.solutions.drawing_utils
    du.draw_landmarks(out, landmarks, mp.solutions.pose.POSE_CONNECTIONS,
                      du.DrawingSpec(color=(0, 229, 192), thickness=3, circle_radius=5),
                      du.DrawingSpec(color=(240, 180, 41), thickness=2))
    if label and label_xy:
        cv2.putText(out, label, label_xy, cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 229, 192), 3, cv2.LINE_AA)
    return out

def _line_tilt_deg(a, b):
    d = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    if d > 90: d -= 180
    if d < -90: d += 180
    return d

def posture_metrics(lm, view):
    P = lambda i: (lm[i].x, lm[i].y)
    rows = []
    def flag(v, ok, mild):
        return "✅ Within range" if v < ok else ("⚠️ Mild" if v < mild else "🔶 Notable")
    if view == "Front":
        ls, rs, lh, rh, nose = P(11), P(12), P(23), P(24), P(0)
        sh_tilt = abs(_line_tilt_deg(ls, rs)); hip_tilt = abs(_line_tilt_deg(lh, rh))
        sw = abs(ls[0] - rs[0]) + 1e-6
        head_shift = abs(nose[0] - (ls[0] + rs[0]) / 2) / sw * 100
        torso = abs((lh[1] + rh[1]) / 2 - (ls[1] + rs[1]) / 2) + 1e-6
        knee_diff = abs(P(25)[1] - P(26)[1]) / torso * 100
        rows += [
            ("Shoulder tilt", f"{sh_tilt:.1f}°", flag(sh_tilt, 2, 4), f"Higher side: {'left' if ls[1] < rs[1] else 'right'} shoulder"),
            ("Hip tilt", f"{hip_tilt:.1f}°", flag(hip_tilt, 2, 4), f"Higher side: {'left' if lh[1] < rh[1] else 'right'} hip"),
            ("Head shift off midline", f"{head_shift:.0f}% of shoulder width", flag(head_shift, 6, 12), "Head centred over shoulders?"),
            ("Knee height difference", f"{knee_diff:.0f}% of torso", flag(knee_diff, 4, 8), "Can reflect stance or leg-length differences"),
        ]
    else:
        side = "L" if lm[11].visibility >= lm[12].visibility else "R"
        ear, sh, hip = (7, 11, 23) if side == "L" else (8, 12, 24)
        torso = abs(lm[hip].y - lm[sh].y) + 1e-6
        fh = abs(lm[ear].x - lm[sh].x) / torso
        sp = abs(lm[sh].x - lm[hip].x) / torso
        rows += [
            ("Forward head position", f"{fh:.2f} × torso", flag(fh, .15, .30), "Ear vs shoulder alignment"),
            ("Shoulder over hip", f"{sp:.2f} × torso", flag(sp, .10, .20), "Trunk lean / rounded upper back"),
        ]
    return rows

# ───────────────────────── CLASSIFIERS ─────────────────────────
def bmi_cat(b):
    return "Underweight" if b < 18.5 else "Healthy range" if b < 25 else "Overweight" if b < 30 else "Obesity"

def bp_cat(s, d):
    if s > 180 or d > 120: return "HYPERTENSIVE CRISIS — seek urgent care"
    if s >= 140 or d >= 90: return "Stage 2 hypertension range"
    if s >= 130 or d >= 80: return "Stage 1 hypertension range"
    if s >= 120: return "Elevated"
    return "Normal"

CHAIR_STAND_LOW = {  # CDC STEADI 30-second chair stand: below these = below average
    "Male": [(60, 64, 14), (65, 69, 12), (70, 74, 12), (75, 79, 11), (80, 84, 10), (85, 89, 8), (90, 94, 7)],
    "Female": [(60, 64, 12), (65, 69, 11), (70, 74, 10), (75, 79, 10), (80, 84, 9), (85, 89, 8), (90, 94, 4)],
}

def chair_norm(age, sex):
    for lo, hi, thr in CHAIR_STAND_LOW.get(sex, []):
        if lo <= age <= hi:
            return thr
    if age > 94:
        return CHAIR_STAND_LOW[sex][-1][2]
    return None

def bodyfat_navy(sex, height_cm, waist_cm, neck_cm, hip_cm):
    """US Navy circumference method. Returns % body fat or None if inputs are impossible."""
    try:
        if sex == "Male":
            d = waist_cm - neck_cm
            if d <= 0: return None
            bf = 495 / (1.0324 - 0.19077 * math.log10(d) + 0.15456 * math.log10(height_cm)) - 450
        else:
            d = waist_cm + hip_cm - neck_cm
            if d <= 0: return None
            bf = 495 / (1.29579 - 0.35004 * math.log10(d) + 0.22100 * math.log10(height_cm)) - 450
        return bf if 2 <= bf <= 60 else None
    except Exception:
        return None

def bf_cat(bf, sex):
    cuts = [(6, 14, 18, 25), "Male"] if sex == "Male" else [(14, 21, 25, 32), "Female"]
    e, a, f, h = cuts[0]
    if bf < e: return "Essential/very low", 70
    if bf < a: return "Athletic", 100
    if bf < f: return "Fitness", 100
    if bf < h: return "Average", 80
    return "High (health-risk range)", 40

# Single-leg stance, eyes open: mean hold times by age (Springer et al., 2007), seconds
def sls_ref(age):
    for top, ref in [(40, 43), (50, 40), (60, 37), (70, 27), (80, 15)]:
        if age < top: return ref
    return 9

BORG = {6: "No exertion", 7: "Extremely light", 8: "Extremely light", 9: "Very light", 10: "Very light", 11: "Light",
        12: "Light–somewhat hard", 13: "Somewhat hard", 14: "Somewhat hard", 15: "Hard", 16: "Hard",
        17: "Very hard", 18: "Very hard", 19: "Extremely hard", 20: "Maximal"}

SHOULDER_SCORE = {"Fingers overlap": (100, "Good shoulder mobility"), "Fingertips just touch": (85, "Good shoulder mobility"),
                  "Gap under 5 cm": (60, "Mild shoulder tightness"), "Gap 5 cm or more": (35, "Limited shoulder mobility")}

# ───────────────────────── BROWSER SENSOR COMPONENTS (HTML/JS) ─────────────────────────
PPG_HTML = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#071318;color:#e8f4f2}
.wrap{padding:12px}
button{background:linear-gradient(90deg,#00c9a7,#0090bb);color:#030c0e;border:0;border-radius:12px;padding:12px 18px;font-weight:700;font-size:16px;cursor:pointer;margin-right:8px}
button.alt{background:#16323a;color:#e8f4f2}
select{padding:10px;border-radius:10px;background:#0c1e24;color:#e8f4f2;border:1px solid #0c3a3a;font-size:15px}
#status{margin:12px 0;font-size:15px;line-height:1.45;min-height:44px}
canvas{width:100%;height:110px;background:#030c0e;border:1px solid #0c3a3a;border-radius:10px}
.bar{height:10px;background:#0c1e24;border-radius:6px;overflow:hidden;margin:8px 0}
#fill{height:100%;width:0;background:#00ffe0;transition:width .2s}
.res{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-top:12px}
.card{background:#0c1e24;border:1px solid #0c3a3a;border-radius:12px;padding:10px;text-align:center}
.big{font-size:30px;font-weight:800;color:#00ffe0}.lab{font-size:11px;opacity:.7;text-transform:uppercase;letter-spacing:.05em}
.note{font-size:12px;opacity:.65;margin-top:10px;line-height:1.4}
video{position:absolute;width:1px;height:1px;opacity:0}
</style></head><body><div class="wrap">
<button id="go">▶ Start 30-second reading</button><button id="stop" class="alt">■ Stop</button>
<div id="status">Tap Start, then cover the <b>rear camera AND flash</b> fully with your fingertip. Rest your hand, stay still, breathe normally.</div>
<div class="bar"><div id="fill"></div></div><canvas id="plot" width="600" height="110"></canvas>
<div class="res" id="res"></div>
<div class="note">Experimental camera pulse sensing (photoplethysmography). Not a medical device. Works best on a phone with a rear flash; iPhone Safari cannot switch the flash on, so use bright light. Heart-rate variability and breathing rate are rough estimates for personal trends only.</div>
<video id="v" playsinline muted></video></div><script>

const send=(type,extra)=>window.parent.postMessage(Object.assign({isStreamlitMessage:true,type:type},extra||{}),"*");
send("streamlit:componentReady",{apiVersion:1});send("streamlit:setFrameHeight",{height:640});
function setValue(v){send("streamlit:setComponentValue",{value:v,dataType:"json"});}
const $=id=>document.getElementById(id);
function status(m){$('status').innerHTML=m;}
function card(v,l){return '<div class="card"><div class="big">'+v+'</div><div class="lab">'+l+'</div></div>';}
function movavg(a,n){n=Math.max(1,n|0);const pre=[0];for(let i=0;i<a.length;i++)pre.push(pre[i]+a[i]);const h=Math.floor(n/2),o=new Array(a.length);for(let i=0;i<a.length;i++){const lo=Math.max(0,i-h),hi=Math.min(a.length-1,i+h);o[i]=(pre[hi+1]-pre[lo])/(hi-lo+1);}return o;}
function findPeaks(y,minD,thr){const pk=[];for(let i=2;i<y.length-2;i++){if(y[i]>y[i-1]&&y[i]>=y[i+1]&&y[i]>thr){const d=y[i-1]-2*y[i]+y[i+1];const off=d!==0?0.5*(y[i-1]-y[i+1])/d:0;pk.push({i:i+off,v:y[i]});}}const kept=[];for(const p of pk){if(kept.length&&p.i-kept[kept.length-1].i<minD){if(p.v>kept[kept.length-1].v)kept[kept.length-1]=p;}else kept.push(p);}return kept;}
function analyzePPG(samples){
  const FS=30,SKIP=3000;const S=samples.filter(s=>s.t>=SKIP);
  if(S.length<FS*10)return{ok:false,reason:"Not enough signal. Keep your fingertip still and fully covering the lens."};
  const T0=S[0].t,T1=S[S.length-1].t,N=Math.floor((T1-T0)/1000*FS),x=new Array(N);let j=0;
  for(let i=0;i<N;i++){const t=T0+i*1000/FS;while(j<S.length-2&&S[j+1].t<t)j++;const a=S[j],b=S[j+1];const u=Math.min(1,Math.max(0,(t-a.t)/((b.t-a.t)||1)));x[i]=a.v+(b.v-a.v)*u;}
  const base=movavg(x,Math.round(FS*0.9));let y=movavg(x.map((v,i)=>-(v-base[i])),5);
  const sd=Math.sqrt(y.reduce((s,v)=>s+v*v,0)/y.length)||1e-9;
  const kept=findPeaks(y,FS*0.33,0.35*sd);
  const ibi=[];for(let k=1;k<kept.length;k++)ibi.push((kept[k].i-kept[k-1].i)/FS);
  const ok=ibi.filter(v=>v>=0.33&&v<=1.5);
  if(ok.length<8)return{ok:false,reason:"Could not find a steady pulse. Press a little less hard, stay still, and retry."};
  const med=ok.slice().sort((a,b)=>a-b)[Math.floor(ok.length/2)];
  const good=ok.filter(v=>Math.abs(v-med)/med<0.25);
  const bpm=60/(good.reduce((s,v)=>s+v,0)/good.length);
  const quality=good.length/Math.max(1,ibi.length);
  if(quality<0.6)return{ok:false,reason:"Signal too noisy to trust (steadiness "+Math.round(quality*100)+"%). Stay still, cover lens and flash fully, press lightly, and retry."};
  let hrv=null;const d=[];for(let k=1;k<ibi.length;k++){const a=ibi[k-1],b=ibi[k];if(Math.abs(a-med)/med<0.25&&Math.abs(b-med)/med<0.25)d.push((b-a)*1000);}
  if(d.length>=10)hrv=Math.sqrt(d.reduce((s,v)=>s+v*v,0)/d.length);
  const rf=movavg(x,Math.round(FS*0.7)),rs=movavg(x,Math.round(FS*6)),r=rf.map((v,i)=>v-rs[i]);
  const rsd=Math.sqrt(r.reduce((s,v)=>s+v*v,0)/r.length)||1e-9;
  const rp=findPeaks(r,FS*1.5,0.3*rsd);let resp=null;
  if(rp.length>=3){const span=(rp[rp.length-1].i-rp[0].i)/FS;if(span>5)resp=(rp.length-1)/span*60;}
  return{ok:true,bpm:Math.round(bpm),quality:Math.round(quality*100)/100,hrv:hrv===null?null:Math.round(hrv),resp:resp===null?null:Math.round(resp),beats:good.length,seconds:Math.round((T1-T0)/1000)};
}
function analyzeSway(S){
  if(S.length<50)return{ok:false,reason:"No motion data received. Use a phone and allow motion access."};
  const n0=S.length,cut=Math.floor(n0*0.05);const D=S.slice(cut,n0-cut),n=D.length;
  const T=(D[n-1].t-D[0].t)/1000;
  const g=D.map(s=>{const m=Math.hypot(s.x,s.y,s.z)||1;return[s.x/m,s.y/m,s.z/m];});
  let mx=0,my=0,mz=0;g.forEach(v=>{mx+=v[0];my+=v[1];mz+=v[2];});const mm=Math.hypot(mx,my,mz)||1;mx/=mm;my/=mm;mz/=mm;
  const ang=g.map(v=>Math.acos(Math.min(1,Math.max(-1,v[0]*mx+v[1]*my+v[2]*mz)))*180/Math.PI);
  const rms=Math.sqrt(ang.reduce((s,v)=>s+v*v,0)/n);
  let path=0;for(let i=1;i<n;i++){const a=g[i-1],b=g[i];path+=Math.acos(Math.min(1,Math.max(-1,a[0]*b[0]+a[1]*b[1]+a[2]*b[2])))*180/Math.PI;}
  const score=Math.max(0,Math.min(100,Math.round(100*Math.exp(-rms/3))));
  const label=rms<=0.8?"Steady":rms<=1.8?"Moderate sway":"Unsteady";
  return{ok:true,rms:Math.round(rms*100)/100,path:Math.round(path/T*10)/10,score,label,seconds:Math.round(T),hz:Math.round(n/T)};
}
if(typeof module!=="undefined")module.exports={analyzePPG,analyzeSway};

let stream=null,track=null,running=false,t0=0,samples=[],offStart=0,DUR=33000,torch=false;
const cv=document.createElement('canvas');cv.width=48;cv.height=36;const cx=cv.getContext('2d',{willReadFrequently:true});
const plot=$('plot'),pc=plot.getContext('2d');
function draw(){pc.clearRect(0,0,600,110);const n=Math.min(samples.length,180);if(n<10)return;const a=samples.slice(-n).map(s=>s.v);const m=a.reduce((s,v)=>s+v,0)/n;const d=a.map(v=>-(v-m));const mx=Math.max(1e-6,...d.map(Math.abs));pc.strokeStyle='#00ffe0';pc.lineWidth=2;pc.beginPath();d.forEach((v,i)=>{const x=i/(n-1)*600,y=55-v/mx*45;i?pc.lineTo(x,y):pc.moveTo(x,y);});pc.stroke();}
async function stopCam(){running=false;try{if(track&&torch)await track.applyConstraints({advanced:[{torch:false}]});}catch(e){}try{if(stream)stream.getTracks().forEach(t=>t.stop());}catch(e){}stream=null;track=null;}
function loop(){
  if(!running)return;const v=$('v');
  if(v.videoWidth){cx.drawImage(v,0,0,48,36);const d=cx.getImageData(0,0,48,36).data;let r=0,g=0,b=0,n=d.length/4;for(let i=0;i<d.length;i+=4){r+=d[i];g+=d[i+1];b+=d[i+2];}r/=n;g/=n;b/=n;
    const on=r>80&&r>1.5*g&&r>1.5*b,now=performance.now();
    if(on){offStart=0;if(!samples.length)t0=now;samples.push({t:now-t0,v:r});const p=Math.min(1,samples[samples.length-1].t/DUR);$('fill').style.width=(p*100)+'%';
      status('Reading… '+Math.round(p*100)+'% — hold still. '+(torch?'Flash on.':'No flash control: use bright light.'));draw();
      if(samples[samples.length-1].t>=DUR){finish();return;}}
    else{if(samples.length){if(!offStart)offStart=now;if(now-offStart>800){samples=[];offStart=0;$('fill').style.width='0%';status('⚠️ Finger lost — restarting. Cover the camera <b>and</b> flash fully.');}}else status('Place your fingertip over the rear camera and flash.');}}
  requestAnimationFrame(loop);
}
async function finish(){await stopCam();const r=analyzePPG(samples);
  if(r.ok){status('✅ Done. Quality '+Math.round(r.quality*100)+'%');$('res').innerHTML=card(r.bpm,'Heart rate (bpm)')+card(r.hrv===null?'—':r.hrv,'HRV rough (ms)')+card(r.resp===null?'—':r.resp,'Breaths/min (rough)')+card(Math.round(r.quality*100)+'%','Signal quality');}
  else{status('⚠️ '+r.reason);$('res').innerHTML='';}
  setValue(Object.assign({ts:Date.now()},r));}
$('go').onclick=async()=>{
  await stopCam();samples=[];offStart=0;torch=false;$('res').innerHTML='';$('fill').style.width='0%';
  try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:320},height:{ideal:240},frameRate:{ideal:30}},audio:false});}
  catch(e){status('⚠️ Camera blocked ('+e.name+'). Allow camera access in the browser and try again.');return;}
  track=stream.getVideoTracks()[0];
  try{const c=track.getCapabilities?track.getCapabilities():{};if(c.torch){await track.applyConstraints({advanced:[{torch:true}]});torch=true;}}catch(e){}
  const v=$('v');v.srcObject=stream;try{await v.play();}catch(e){}
  running=true;status('Place your fingertip over the rear camera and flash.');requestAnimationFrame(loop);};
$('stop').onclick=async()=>{await stopCam();status('Stopped.');};
</script></body></html>'''

SWAY_HTML = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#071318;color:#e8f4f2}
.wrap{padding:12px}
button{background:linear-gradient(90deg,#00c9a7,#0090bb);color:#030c0e;border:0;border-radius:12px;padding:12px 18px;font-weight:700;font-size:16px;cursor:pointer;margin-right:8px}
button.alt{background:#16323a;color:#e8f4f2}
select{padding:10px;border-radius:10px;background:#0c1e24;color:#e8f4f2;border:1px solid #0c3a3a;font-size:15px}
#status{margin:12px 0;font-size:15px;line-height:1.45;min-height:44px}
canvas{width:100%;height:110px;background:#030c0e;border:1px solid #0c3a3a;border-radius:10px}
.bar{height:10px;background:#0c1e24;border-radius:6px;overflow:hidden;margin:8px 0}
#fill{height:100%;width:0;background:#00ffe0;transition:width .2s}
.res{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-top:12px}
.card{background:#0c1e24;border:1px solid #0c3a3a;border-radius:12px;padding:10px;text-align:center}
.big{font-size:30px;font-weight:800;color:#00ffe0}.lab{font-size:11px;opacity:.7;text-transform:uppercase;letter-spacing:.05em}
.note{font-size:12px;opacity:.65;margin-top:10px;line-height:1.4}
video{position:absolute;width:1px;height:1px;opacity:0}
</style></head><body><div class="wrap">
<div>Test length: <select id="dur"><option value="15">15 s</option><option value="30" selected>30 s</option></select>
<select id="mode"><option>Feet together, eyes open</option><option>Tandem (heel-to-toe)</option><option>One leg</option><option>Eyes closed (feet together)</option></select></div><br>
<button id="go">▶ Start balance test</button>
<div id="status">Hold the phone flat against your <b>chest</b> (or tuck it in a snug waistband), arms relaxed. Stand beside a counter with someone next to you. Tap Start, you get 5 seconds to get ready.</div>
<div class="bar"><div id="fill"></div></div><div class="res" id="res"></div>
<div class="note">Experimental: the phone's motion sensors measure how much your trunk tilts while standing. Compare your own repeat tests rather than treating the numbers as clinical. Needs a phone with motion sensors and a secure (https) page; iPhones ask for permission.</div>
</div><script>

const send=(type,extra)=>window.parent.postMessage(Object.assign({isStreamlitMessage:true,type:type},extra||{}),"*");
send("streamlit:componentReady",{apiVersion:1});send("streamlit:setFrameHeight",{height:560});
function setValue(v){send("streamlit:setComponentValue",{value:v,dataType:"json"});}
const $=id=>document.getElementById(id);
function status(m){$('status').innerHTML=m;}
function card(v,l){return '<div class="card"><div class="big">'+v+'</div><div class="lab">'+l+'</div></div>';}
function movavg(a,n){n=Math.max(1,n|0);const pre=[0];for(let i=0;i<a.length;i++)pre.push(pre[i]+a[i]);const h=Math.floor(n/2),o=new Array(a.length);for(let i=0;i<a.length;i++){const lo=Math.max(0,i-h),hi=Math.min(a.length-1,i+h);o[i]=(pre[hi+1]-pre[lo])/(hi-lo+1);}return o;}
function findPeaks(y,minD,thr){const pk=[];for(let i=2;i<y.length-2;i++){if(y[i]>y[i-1]&&y[i]>=y[i+1]&&y[i]>thr){const d=y[i-1]-2*y[i]+y[i+1];const off=d!==0?0.5*(y[i-1]-y[i+1])/d:0;pk.push({i:i+off,v:y[i]});}}const kept=[];for(const p of pk){if(kept.length&&p.i-kept[kept.length-1].i<minD){if(p.v>kept[kept.length-1].v)kept[kept.length-1]=p;}else kept.push(p);}return kept;}
function analyzePPG(samples){
  const FS=30,SKIP=3000;const S=samples.filter(s=>s.t>=SKIP);
  if(S.length<FS*10)return{ok:false,reason:"Not enough signal. Keep your fingertip still and fully covering the lens."};
  const T0=S[0].t,T1=S[S.length-1].t,N=Math.floor((T1-T0)/1000*FS),x=new Array(N);let j=0;
  for(let i=0;i<N;i++){const t=T0+i*1000/FS;while(j<S.length-2&&S[j+1].t<t)j++;const a=S[j],b=S[j+1];const u=Math.min(1,Math.max(0,(t-a.t)/((b.t-a.t)||1)));x[i]=a.v+(b.v-a.v)*u;}
  const base=movavg(x,Math.round(FS*0.9));let y=movavg(x.map((v,i)=>-(v-base[i])),5);
  const sd=Math.sqrt(y.reduce((s,v)=>s+v*v,0)/y.length)||1e-9;
  const kept=findPeaks(y,FS*0.33,0.35*sd);
  const ibi=[];for(let k=1;k<kept.length;k++)ibi.push((kept[k].i-kept[k-1].i)/FS);
  const ok=ibi.filter(v=>v>=0.33&&v<=1.5);
  if(ok.length<8)return{ok:false,reason:"Could not find a steady pulse. Press a little less hard, stay still, and retry."};
  const med=ok.slice().sort((a,b)=>a-b)[Math.floor(ok.length/2)];
  const good=ok.filter(v=>Math.abs(v-med)/med<0.25);
  const bpm=60/(good.reduce((s,v)=>s+v,0)/good.length);
  const quality=good.length/Math.max(1,ibi.length);
  if(quality<0.6)return{ok:false,reason:"Signal too noisy to trust (steadiness "+Math.round(quality*100)+"%). Stay still, cover lens and flash fully, press lightly, and retry."};
  let hrv=null;const d=[];for(let k=1;k<ibi.length;k++){const a=ibi[k-1],b=ibi[k];if(Math.abs(a-med)/med<0.25&&Math.abs(b-med)/med<0.25)d.push((b-a)*1000);}
  if(d.length>=10)hrv=Math.sqrt(d.reduce((s,v)=>s+v*v,0)/d.length);
  const rf=movavg(x,Math.round(FS*0.7)),rs=movavg(x,Math.round(FS*6)),r=rf.map((v,i)=>v-rs[i]);
  const rsd=Math.sqrt(r.reduce((s,v)=>s+v*v,0)/r.length)||1e-9;
  const rp=findPeaks(r,FS*1.5,0.3*rsd);let resp=null;
  if(rp.length>=3){const span=(rp[rp.length-1].i-rp[0].i)/FS;if(span>5)resp=(rp.length-1)/span*60;}
  return{ok:true,bpm:Math.round(bpm),quality:Math.round(quality*100)/100,hrv:hrv===null?null:Math.round(hrv),resp:resp===null?null:Math.round(resp),beats:good.length,seconds:Math.round((T1-T0)/1000)};
}
function analyzeSway(S){
  if(S.length<50)return{ok:false,reason:"No motion data received. Use a phone and allow motion access."};
  const n0=S.length,cut=Math.floor(n0*0.05);const D=S.slice(cut,n0-cut),n=D.length;
  const T=(D[n-1].t-D[0].t)/1000;
  const g=D.map(s=>{const m=Math.hypot(s.x,s.y,s.z)||1;return[s.x/m,s.y/m,s.z/m];});
  let mx=0,my=0,mz=0;g.forEach(v=>{mx+=v[0];my+=v[1];mz+=v[2];});const mm=Math.hypot(mx,my,mz)||1;mx/=mm;my/=mm;mz/=mm;
  const ang=g.map(v=>Math.acos(Math.min(1,Math.max(-1,v[0]*mx+v[1]*my+v[2]*mz)))*180/Math.PI);
  const rms=Math.sqrt(ang.reduce((s,v)=>s+v*v,0)/n);
  let path=0;for(let i=1;i<n;i++){const a=g[i-1],b=g[i];path+=Math.acos(Math.min(1,Math.max(-1,a[0]*b[0]+a[1]*b[1]+a[2]*b[2])))*180/Math.PI;}
  const score=Math.max(0,Math.min(100,Math.round(100*Math.exp(-rms/3))));
  const label=rms<=0.8?"Steady":rms<=1.8?"Moderate sway":"Unsteady";
  return{ok:true,rms:Math.round(rms*100)/100,path:Math.round(path/T*10)/10,score,label,seconds:Math.round(T),hz:Math.round(n/T)};
}
if(typeof module!=="undefined")module.exports={analyzePPG,analyzeSway};

let rec=false,S=[],t0=0,DURMS=30000,mode='';
function onMotion(e){if(!rec)return;const a=e.accelerationIncludingGravity;if(!a||a.x==null)return;const now=performance.now()-t0;S.push({t:now,x:a.x,y:a.y,z:a.z});
  const p=Math.min(1,now/DURMS);$('fill').style.width=(p*100)+'%';if(now>=DURMS)done();}
function done(){rec=false;window.removeEventListener('devicemotion',onMotion);try{navigator.vibrate&&navigator.vibrate(200);}catch(e){}
  const r=analyzeSway(S);
  if(r.ok){status('✅ Done — '+r.label);$('res').innerHTML=card(r.rms+'°','Average trunk tilt')+card(r.path+'°/s','Sway speed')+card(r.score,'Stability score (0-100)')+card(r.hz+' Hz','Sensor rate');}
  else{status('⚠️ '+r.reason);$('res').innerHTML='';}
  setValue(Object.assign({ts:Date.now(),mode:mode},r));}
$('go').onclick=async()=>{
  if(typeof DeviceMotionEvent==='undefined'){status('⚠️ No motion sensor in this browser. Open the app on a phone.');return;}
  if(typeof DeviceMotionEvent.requestPermission==='function'){try{const p=await DeviceMotionEvent.requestPermission();if(p!=='granted'){status('⚠️ Motion access was denied. Allow it in Safari settings and retry.');return;}}catch(e){status('⚠️ Could not get motion permission: '+e);return;}}
  DURMS=parseInt($('dur').value)*1000;mode=$('mode').value;$('res').innerHTML='';$('fill').style.width='0%';S=[];
  for(let i=5;i>0;i--){status('Get ready… <b>'+i+'</b> — '+mode);await new Promise(r=>setTimeout(r,1000));}
  status('Hold still…');t0=performance.now();rec=true;window.addEventListener('devicemotion',onMotion);
  setTimeout(()=>{if(rec&&S.length<20){rec=false;window.removeEventListener('devicemotion',onMotion);status('⚠️ No motion data arrived. This device or browser has no accessible motion sensor.');}},3000);};
</script></body></html>'''

PACER_HTML = r'''<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#071318;color:#e8f4f2;font-family:system-ui,sans-serif;text-align:center}
#circle{width:140px;height:140px;border-radius:50%;margin:24px auto 10px;background:radial-gradient(circle,#00ffe0,#0090bb);box-shadow:0 0 40px rgba(0,255,224,.35);transition:transform linear}
#t{font-size:26px;font-weight:800;margin:6px}#s{font-size:14px;opacity:.7}
button,select{padding:10px 16px;border-radius:10px;border:0;font-size:15px;margin:4px}
button{background:linear-gradient(90deg,#00c9a7,#0090bb);color:#030c0e;font-weight:700}select{background:#0c1e24;color:#e8f4f2}
</style></head><body><div style="padding:12px">
<select id="p"><option value="4,0,6,0">Calm 4-6 (in 4, out 6)</option><option value="5.5,0,5.5,0">Resonance 5.5-5.5 (about 5.5 breaths/min)</option><option value="4,4,4,4">Box 4-4-4-4</option><option value="4,7,8,0">Relax 4-7-8</option></select>
<button id="go">Start</button><div id="circle"></div><div id="t">Ready</div><div id="s">Breathe through your nose. Stop if you feel dizzy.</div></div>
<script>
let run=false,timer=null;const c=document.getElementById('circle'),t=document.getElementById('t'),s=document.getElementById('s');
function step(ph,i,cyc){if(!run)return;const[inh,h1,exh,h2]=ph;const seq=[['Breathe in',inh,1.45],['Hold',h1,1.45],['Breathe out',exh,1],['Hold',h2,1]].filter(x=>x[1]>0);
 const k=seq[i%seq.length];t.textContent=k[0];c.style.transition='transform '+k[1]+'s linear';c.style.transform='scale('+k[2]+')';
 timer=setTimeout(()=>step(ph,i+1,cyc),k[1]*1000);}
document.getElementById('go').onclick=function(){if(run){run=false;clearTimeout(timer);this.textContent='Start';t.textContent='Stopped';c.style.transform='scale(1)';return;}
 run=true;this.textContent='Stop';s.textContent='Follow the circle. Slow, easy breaths.';step(document.getElementById('p').value.split(',').map(Number),0,0);};
</script></body></html>'''

PHONE_HTML = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#071318;color:#e8f4f2}
.wrap{padding:12px}
button{background:linear-gradient(90deg,#00c9a7,#0090bb);color:#030c0e;border:0;border-radius:12px;padding:12px 18px;font-weight:700;font-size:16px;cursor:pointer;margin-right:8px}
button.alt{background:#16323a;color:#e8f4f2}
select{padding:10px;border-radius:10px;background:#0c1e24;color:#e8f4f2;border:1px solid #0c3a3a;font-size:15px}
#status{margin:12px 0;font-size:15px;line-height:1.45;min-height:44px}
canvas{width:100%;height:110px;background:#030c0e;border:1px solid #0c3a3a;border-radius:10px}
.bar{height:10px;background:#0c1e24;border-radius:6px;overflow:hidden;margin:8px 0}
#fill{height:100%;width:0;background:#00ffe0;transition:width .2s}
.res{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-top:12px}
.card{background:#0c1e24;border:1px solid #0c3a3a;border-radius:12px;padding:10px;text-align:center}
.big{font-size:30px;font-weight:800;color:#00ffe0}.lab{font-size:11px;opacity:.7;text-transform:uppercase;letter-spacing:.05em}
.note{font-size:12px;opacity:.65;margin-top:10px;line-height:1.4}
video{position:absolute;width:1px;height:1px;opacity:0}
</style></head><body><div class="wrap">
<button id="go">▶ Run phone check (about 12 seconds)</button>
<div id="status">Tap the button. Keep this screen open and don't touch it while the speed tests run. Nothing is sent anywhere except a few tiny requests to this app itself.</div>
<div class="bar"><div id="fill"></div></div><div class="res" id="res"></div>
<div class="note">Runs inside your browser: CPU speed, smoothness (frames per second), connection to this app, memory class, battery, storage and the permissions this page has. A website cannot see your other apps or files.</div>
</div><script>

const send=(type,extra)=>window.parent.postMessage(Object.assign({isStreamlitMessage:true,type:type},extra||{}),"*");
send("streamlit:componentReady",{apiVersion:1});send("streamlit:setFrameHeight",{height:430});
function setValue(v){send("streamlit:setComponentValue",{value:v,dataType:"json"});}
const $=id=>document.getElementById(id);
function status(m){$('status').innerHTML=m;}
function card(v,l){return '<div class="card"><div class="big">'+v+'</div><div class="lab">'+l+'</div></div>';}

const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function prog(p,t){$('fill').style.width=p+'%';status(t);}
function cpuBench(){const runs=[];for(let k=0;k<3;k++){const t0=performance.now();let x=0;for(let i=1;i<6e6;i++){x+=Math.sqrt(i)*Math.sin(i);}const ms=performance.now()-t0;runs.push(ms);if(x===0.123)console.log(x);}runs.sort((a,b)=>a-b);return Math.round(runs[1]);}
function fpsTest(dur){return new Promise(res=>{const ts=[];let last=performance.now(),start=last;function f(now){ts.push(now-last);last=now;if(now-start<dur)requestAnimationFrame(f);else{const a=ts.slice(2);if(a.length<5){res(null);return;}const avg=a.reduce((s,v)=>s+v,0)/a.length;const sorted=a.slice().sort((x,y)=>x-y);const p95=sorted[Math.floor(sorted.length*0.95)];const dropped=a.filter(v=>v>avg*1.8).length;res({fps:Math.round(1000/avg),p95_ms:Math.round(p95),dropped:dropped,frames:a.length});}}requestAnimationFrame(f);});}
async function latencyTest(n){const t=[];let bytes=0;for(let i=0;i<n;i++){const s=performance.now();try{const r=await fetch(location.href.split('#')[0]+'?r='+Math.random(),{cache:'no-store'});const txt=await r.text();bytes=txt.length;t.push(performance.now()-s);}catch(e){return null;}await sleep(60);}t.sort((a,b)=>a-b);return {min:Math.round(t[0]),median:Math.round(t[Math.floor(t.length/2)]),max:Math.round(t[t.length-1]),kb:Math.round(bytes/1024*10)/10};}
$('go').onclick=async()=>{
  $('go').disabled=true;$('res').innerHTML='';const nav=navigator,o={};
  prog(5,'Reading device & browser info…');
  o.ua=nav.userAgent;o.platform=nav.platform||'';o.lang=nav.language;o.cores=nav.hardwareConcurrency||null;o.mem_gb=nav.deviceMemory||null;o.touch=nav.maxTouchPoints||0;
  o.online=nav.onLine;o.cookies=nav.cookieEnabled;o.dnt=(nav.doNotTrack||window.doNotTrack||null);o.gpc=!!nav.globalPrivacyControl;o.secure=window.isSecureContext;
  o.standalone=matchMedia('(display-mode: standalone)').matches||nav.standalone===true;o.tz=(Intl.DateTimeFormat().resolvedOptions().timeZone)||'';
  o.screen={w:screen.width,h:screen.height,dpr:window.devicePixelRatio,depth:screen.colorDepth};o.dark=matchMedia('(prefers-color-scheme: dark)').matches;
  o.inapp=/FBAN|FBAV|Instagram|Snapchat|TikTok|musical_ly|; wv\)|Line\//i.test(nav.userAgent);
  try{if(nav.userAgentData){o.uach={mobile:nav.userAgentData.mobile,platform:nav.userAgentData.platform,brands:(nav.userAgentData.brands||[]).map(b=>b.brand+' '+b.version)};
    try{const h=await nav.userAgentData.getHighEntropyValues(['platformVersion','model','uaFullVersion']);o.uach.platformVersion=h.platformVersion;o.uach.model=h.model;o.uach.fullVersion=h.uaFullVersion;}catch(e){}}}catch(e){}
  prog(15,'Checking battery, network and storage…');
  try{if(nav.getBattery){const b=await nav.getBattery();o.battery={level:Math.round(b.level*100),charging:b.charging,discharging_min:isFinite(b.dischargingTime)?Math.round(b.dischargingTime/60):null};}}catch(e){}
  const c=nav.connection||nav.mozConnection||nav.webkitConnection;if(c)o.net={type:c.effectiveType,downlink:c.downlink,rtt:c.rtt,saveData:c.saveData,conn:c.type||null};
  try{if(nav.storage&&nav.storage.estimate){const e=await nav.storage.estimate();o.storage={quota_mb:Math.round(e.quota/1048576),usage_mb:Math.round(e.usage/1048576)};}}catch(e){}
  if(performance.memory)o.heap={used_mb:Math.round(performance.memory.usedJSHeapSize/1048576),limit_mb:Math.round(performance.memory.jsHeapSizeLimit/1048576)};
  prog(30,'Checking permissions this page has…');
  const perms={};for(const n of ['camera','microphone','geolocation','notifications','clipboard-read','accelerometer','gyroscope','persistent-storage']){try{const r=await nav.permissions.query({name:n});perms[n]=r.state;}catch(e){perms[n]='unsupported';}}o.perms=perms;
  try{const cv=document.createElement('canvas');const gl=cv.getContext('webgl')||cv.getContext('experimental-webgl');if(gl){const ext=gl.getExtension('WEBGL_debug_renderer_info');o.gpu=String(ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER));}}catch(e){}
  prog(45,'CPU speed test…');await sleep(50);o.cpu_ms=cpuBench();
  prog(60,'Smoothness test (don\'t touch the screen)…');o.fps=await fpsTest(2800);
  prog(85,'Connection test to this app…');o.latency=await latencyTest(8);
  prog(100,'Done.');o.ts=Date.now();$('go').disabled=false;
  $('res').innerHTML=card(o.cpu_ms+' ms','CPU test (lower = faster)')+card(o.fps?o.fps.fps+' fps':'—','Smoothness')+card(o.latency?o.latency.median+' ms':'—','Connection delay')+card(o.mem_gb?o.mem_gb+' GB+':'—','Memory class');
  status('✅ Finished. Full analysis is shown below this box.');setValue(o);};
</script></body></html>'''

ADTEST_HTML = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#071318;color:#e8f4f2}
.wrap{padding:12px}
button{background:linear-gradient(90deg,#00c9a7,#0090bb);color:#030c0e;border:0;border-radius:12px;padding:12px 18px;font-weight:700;font-size:16px;cursor:pointer;margin-right:8px}
button.alt{background:#16323a;color:#e8f4f2}
select{padding:10px;border-radius:10px;background:#0c1e24;color:#e8f4f2;border:1px solid #0c3a3a;font-size:15px}
#status{margin:12px 0;font-size:15px;line-height:1.45;min-height:44px}
canvas{width:100%;height:110px;background:#030c0e;border:1px solid #0c3a3a;border-radius:10px}
.bar{height:10px;background:#0c1e24;border-radius:6px;overflow:hidden;margin:8px 0}
#fill{height:100%;width:0;background:#00ffe0;transition:width .2s}
.res{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-top:12px}
.card{background:#0c1e24;border:1px solid #0c3a3a;border-radius:12px;padding:10px;text-align:center}
.big{font-size:30px;font-weight:800;color:#00ffe0}.lab{font-size:11px;opacity:.7;text-transform:uppercase;letter-spacing:.05em}
.note{font-size:12px;opacity:.65;margin-top:10px;line-height:1.4}
video{position:absolute;width:1px;height:1px;opacity:0}
</style></head><body><div class="wrap">
<button id="go">▶ Test ad &amp; tracker blocking (about 8 seconds)</button>
<div id="status">Tap the button. The test tries to load 12 well-known ad/tracker scripts and 2 normal sites. If your DNS, blocker or browser stops the ad ones, they count as <b>blocked</b>.</div>
<div class="bar"><div id="fill"></div></div><div class="res" id="res"></div>
<div class="note">Runs in your browser only. It tests this phone/network right now. A normal site that loads while the ad ones fail means blocking is working.</div>
</div><script>

const send=(type,extra)=>window.parent.postMessage(Object.assign({isStreamlitMessage:true,type:type},extra||{}),"*");
send("streamlit:componentReady",{apiVersion:1});send("streamlit:setFrameHeight",{height:400});
function setValue(v){send("streamlit:setComponentValue",{value:v,dataType:"json"});}
const $=id=>document.getElementById(id);
function status(m){$('status').innerHTML=m;}
function card(v,l){return '<div class="card"><div class="big">'+v+'</div><div class="lab">'+l+'</div></div>';}

const ADS=['https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js','https://securepubads.g.doubleclick.net/tag/js/gpt.js','https://www.googletagservices.com/tag/js/gpt.js',
 'https://ib.adnxs.com/ttj','https://cdn.taboola.com/libtrc/loader.js','https://widgets.outbrain.com/outbrain.js','https://c.amazon-adsystem.com/aax2/apstag.js',
 'https://static.criteo.net/js/ld/publishertag.js','https://www.google-analytics.com/analytics.js','https://static.hotjar.com/c/hotjar-1.js',
 'https://sb.scorecardresearch.com/beacon.js','https://connect.facebook.net/en_US/fbevents.js'];
const CTRL=['https://www.gstatic.com/generate_204','https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js'];
function probe(u){return new Promise(res=>{const ac=new AbortController();const t=setTimeout(()=>{ac.abort();res('blocked');},5000);
  fetch(u+(u.includes('?')?'&':'?')+'r='+Math.random(),{mode:'no-cors',cache:'no-store',signal:ac.signal}).then(()=>{clearTimeout(t);res('reached');}).catch(()=>{clearTimeout(t);res('blocked');});});}
$('go').onclick=async()=>{
  $('go').disabled=true;$('res').innerHTML='';$('fill').style.width='10%';status('Testing normal sites first…');
  const c=await Promise.all(CTRL.map(probe));const ctrl=c.filter(x=>x==='reached').length>=1;
  $('fill').style.width='40%';status('Testing ad and tracker addresses…');
  const r=await Promise.all(ADS.map(probe));$('fill').style.width='100%';
  const blocked=r.filter(x=>x==='blocked').length,pct=Math.round(blocked/ADS.length*100);
  const o={ts:Date.now(),control_ok:ctrl,total:ADS.length,blocked:blocked,percent:pct,details:ADS.map((u,i)=>({d:u.split('/')[2],state:r[i]}))};
  o.status=!ctrl?'inconclusive':pct>=70?'strong':pct>=10?'partial':'none';
  status(!ctrl?'⚠️ Could not reach normal sites — check your connection and retry.':'✅ Finished. Analysis is shown below this box.');
  $('res').innerHTML=card(ctrl?pct+'%':'—','Ads/trackers blocked')+card(blocked+'/'+ADS.length,'Blocked')+card(ctrl?'yes':'no','Normal sites reachable');
  $('go').disabled=false;setValue(o);};
</script></body></html>'''

# ───────────────────────── PHONE PERFORMANCE / GUARDIAN ─────────────────────────
def parse_phone_os(d):
    ua = d.get("ua", "") or ""
    u = d.get("uach") or {}
    is_ios = bool(re.search(r"iPhone|iPad|iPod", ua))
    is_android = "Android" in ua or str(u.get("platform", "")).lower() == "android"
    name, major, reliable = "Unknown", None, False
    if is_android:
        name = "Android"
        pv = str(u.get("platformVersion") or "")
        if re.match(r"\d+", pv):
            major, reliable = int(re.match(r"\d+", pv).group(0)), True
        else:
            m = re.search(r"Android (\d+)", ua); major = int(m.group(1)) if m else None
    elif is_ios:
        name = "iOS / iPadOS"
        m = re.search(r"Version/(\d+)", ua) or re.search(r"OS (\d+)[_.]", ua)
        major, reliable = (int(m.group(1)) if m else None), bool(m)
    elif ua:
        name = str(u.get("platform") or d.get("platform") or "Desktop")
    return name, major, reliable, is_ios, is_android

def analyze_phone(d):
    parts, hyg, tips = [], [], []
    name, major, reliable, is_ios, is_android = parse_phone_os(d)
    cpu = d.get("cpu_ms")
    if cpu:
        sc = 100 if cpu <= 120 else 80 if cpu <= 250 else 55 if cpu <= 500 else 30 if cpu <= 1000 else 15
        parts.append(("CPU speed", f"{cpu} ms", sc))
        if sc <= 55: tips.append("Slow processor result: close heavy apps, let the phone cool, and turn off battery-saver (it throttles the CPU) before re-testing.")
    fp = d.get("fps")
    if fp:
        sc = 100 if fp["fps"] >= 55 else 80 if fp["fps"] >= 45 else 55 if fp["fps"] >= 30 else 25
        parts.append(("Smoothness", f"{fp['fps']} fps · {fp['dropped']} stutters in {fp['frames']} frames", sc))
        if sc <= 55: tips.append("Choppy screen: update the OS and your browser, restart the phone, free storage, and turn off power-saving or low-power mode.")
    mem = d.get("mem_gb")
    if mem:
        sc = 100 if mem >= 6 else 85 if mem >= 4 else 65 if mem >= 3 else 45 if mem >= 2 else 25
        parts.append(("Memory class", f"{mem} GB+ (browser reports a rounded value, capped at 8)", sc))
        if sc <= 45: tips.append("Low-memory phone: keep fewer apps/tabs open, use 'Lite' app versions, and avoid heavy multitasking.")
    lat = d.get("latency")
    if lat:
        m = lat["median"]
        sc = 100 if m <= 80 else 80 if m <= 200 else 55 if m <= 500 else 30
        parts.append(("Connection to this app", f"{m} ms typical (best {lat['min']}, worst {lat['max']})", sc))
        if sc <= 55: tips.append("Slow connection: move closer to the router or switch between Wi-Fi and mobile data; restart the router if every device is slow.")
    net = d.get("net") or {}
    if net.get("saveData"): tips.append("Data Saver is on, which can slow pages and images. Turn it off for testing.")
    bat = d.get("battery")
    if bat and bat["level"] < 20 and not bat["charging"]:
        tips.append(f"Battery is {bat['level']}%: low-power modes slow the phone. Charge and re-run for a fair result.")
    st_ = d.get("storage")
    perf = round(sum(p[2] for p in parts) / len(parts)) if parts else None

    # hygiene / safety checks
    def h(ok, good, bad, detail=""):
        hyg.append(("✅" if ok else "⚠️", good if ok else bad, "" if ok else detail))
    h(bool(d.get("secure")), "Page loaded over a secure (https) connection", "Not a secure connection", "Only use the app over https.")
    h(not d.get("inapp"), "Using a normal browser", "Opened inside another app's built-in browser", "In-app browsers (Facebook, Instagram, TikTok…) track more and limit features. Open the link in Chrome or Safari.")
    if major is not None and name == "Android":
        if reliable:
            if major <= 11: h(False, "", f"Android {major} no longer receives Google security fixes", "Use a supported phone for banking and sensitive accounts.")
            elif major <= 13: h(False, "", f"Android {major}: confirm your phone still gets security updates", "Check your model's update policy; Settings → About phone → Android security update.")
            else: h(True, f"Android {major} is a current-generation version", "")
        else:
            hyg.append(("ℹ️", "Chrome hides your real Android version", "Check Settings → About phone → Android version and security update date."))
    elif major is not None and is_ios:
        if major <= 16: h(False, "", f"iOS {major} is old", "Update in Settings → General → Software Update if your iPhone supports a newer version.")
        else: h(True, f"iOS {major} is relatively recent", "Keep Automatic Updates on.")
    else:
        hyg.append(("ℹ️", "Could not determine the OS version from the browser", "Check it in Settings → About."))
    p = d.get("perms") or {}
    granted = [k for k, v in p.items() if v == "granted" and k in ("camera", "microphone", "geolocation", "notifications", "clipboard-read")]
    hyg.append(("ℹ️" if granted else "✅", "Permissions this site has: " + (", ".join(granted) if granted else "none of camera, mic, location, notifications"),
                "Review in browser Site settings if you did not intend these." if granted else ""))
    if d.get("gpc") or d.get("dnt") == "1":
        hyg.append(("✅", "Do-Not-Track / Global Privacy Control signal is on", ""))
    else:
        hyg.append(("ℹ️", "Privacy signals (Do-Not-Track / GPC) are off", "Optional: enable 'Send a Do Not Track request' or use a privacy-focused browser."))
    if not d.get("cookies"): hyg.append(("ℹ️", "Cookies are disabled", "Some app features need them to keep you signed in."))
    checks = [x for x in hyg if x[0] in ("✅", "⚠️")]
    safety = round(100 * sum(1 for x in checks if x[0] == "✅") / len(checks)) if checks else None

    # platform-specific upkeep tips
    if is_ios:
        tips += ["Restart: hold the side + volume button → slide to power off, wait 30 s. Do it weekly.",
                 "Storage: Settings → General → iPhone Storage → offload unused apps and large videos.",
                 "Battery health: Settings → Battery → Battery Health & Charging (replace the battery under ~80% if the phone is slow or shuts down).",
                 "Privacy: Settings → Privacy & Security → Safety Check and App Privacy Report."]
    elif is_android:
        tips += ["Restart weekly (hold power → Restart) to clear stuck background processes.",
                 "Storage: Settings → Storage (or Files by Google → Clean). Keep at least 15% free.",
                 "Apps: Settings → Apps → sort by 'last used' and remove ones you no longer use; update apps in the Play Store.",
                 "Battery: Settings → Battery → Battery usage; look for apps using far more than expected.",
                 "Security: Play Store → profile → Play Protect → Scan; review Settings → Accessibility and Device admin apps."]
    else:
        tips.append("Run this on the phone itself (open the app's web address in the phone's browser) for meaningful phone results.")
    tips.append("Force-closing apps does not speed a phone up (it can make it slower). Restarting, updating and freeing storage do.")
    return {"os": (name, major, reliable), "parts": parts, "perf": perf, "hygiene": hyg, "safety": safety, "tips": tips}

def zip_guardian():
    import zipfile
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(here, "phone_guardian")
    if not os.path.isdir(folder):
        return None
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for root_, dirs, files in os.walk(folder):
            dirs[:] = [x for x in dirs if x not in ("__pycache__", ".git")]
            for fn in files:
                full = os.path.join(root_, fn)
                z.write(full, os.path.join("peace_unity_phone_guardian", os.path.relpath(full, folder)))
    return buf.getvalue()

# ───────────────────────── VITALS LOG / COMPONENTS / PLAN ─────────────────────────
def log_vital(person, kind, value, unit="", note=""):
    if value is None:
        return
    with db() as c:
        c.execute("INSERT INTO vitals_log (ts,person,kind,value,unit,note) VALUES (?,?,?,?,?,?)",
                  (now_str(), person.strip() or "Unnamed", kind, float(value), unit, note))

def c_to_f(c): return c * 9 / 5 + 32
def f_to_c(f): return (f - 32) * 5 / 9

def _write_component(name, html):
    here = os.path.dirname(os.path.abspath(__file__))
    import tempfile
    for base in (os.path.join(here, "lh_components"), os.path.join(tempfile.gettempdir(), "lh_components")):
        try:
            d = os.path.join(base, name)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
                f.write(html)
            return d
        except Exception:
            continue
    return None

@st.cache_resource
def get_component(name):
    """Browser-side sensor components (camera / motion). Returns None if they cannot be created."""
    try:
        import streamlit.components.v1 as components
        d = _write_component(name, {"ppg": PPG_HTML, "sway": SWAY_HTML, "phone": PHONE_HTML, "adtest": ADTEST_HTML}[name])
        return components.declare_component(f"lifehaven_{name}", path=d) if d else None
    except Exception:
        return None

def hr_text(bpm):
    return ("Low (<50) — fine for very fit people; otherwise mention to a clinician" if bpm < 50 else
            "Lower end of typical (50–59)" if bpm < 60 else "Typical resting range (60–100)" if bpm <= 100 else
            "High for resting (>100) — rest, recheck; persistent high needs a clinician")

def early_warning(df):
    """df columns: ts, kind, value for ONE person. Compares newest values to the person's own recent baseline."""
    flags = []
    def series(k): return df[df["kind"] == k].sort_values("ts")["value"].tolist()
    def base(vals):
        prev = vals[:-1][-7:]
        return float(np.median(prev)) if len(prev) >= 3 else None
    hr = series("hr")
    if len(hr) >= 4 and base(hr) is not None and hr[-1] - base(hr) >= 10:
        flags.append(("🔶", f"Resting heart rate {hr[-1]:.0f} is {hr[-1]-base(hr):.0f} bpm above this person's usual (~{base(hr):.0f}). Early sign of infection, dehydration, stress or poor sleep."))
    t = series("temp_c")
    if t:
        if t[-1] >= 38.0: flags.append(("🔶", f"Fever: {t[-1]:.1f} °C ({c_to_f(t[-1]):.1f} °F)."))
        elif len(t) >= 4 and base(t) is not None and t[-1] - base(t) >= 0.7:
            flags.append(("⚠️", f"Temperature {t[-1]:.1f} °C is {t[-1]-base(t):.1f} °C above usual."))
    o = series("spo2")
    if o:
        if o[-1] < 92: flags.append(("🚨", f"Oxygen {o[-1]:.0f}% is low — seek urgent medical care (below 90%: call 911)."))
        elif o[-1] <= 94: flags.append(("⚠️", f"Oxygen {o[-1]:.0f}% is borderline — recheck; call a clinician if it stays at or below 94%."))
    rr = series("resp")
    if rr and rr[-1] >= 22: flags.append(("⚠️", f"Breathing rate {rr[-1]:.0f}/min is fast (adult normal ≈12–20)."))
    hv = series("hrv")
    if len(hv) >= 4 and base(hv) and hv[-1] <= 0.7 * base(hv):
        flags.append(("⚠️", "Heart-rate variability dropped about 30% or more versus usual (stress, illness or poor recovery)."))
    sc = series("symptom_count")
    if sc and sc[-1] >= 3: flags.append(("⚠️", f"{sc[-1]:.0f} symptoms reported at the last check."))
    return flags

def build_plan(domains, age):
    EXMENU = {
        "Lower-body strength": ["Sit-to-stand from a chair", "Supported squats (hold a counter)", "Step-ups on a low step", "Calf raises at a counter"],
        "Balance & fall risk": ["Single-leg stance at a counter", "Heel-to-toe walking along a wall", "Side steps / weight shifts", "Tandem stance"],
        "Flexibility": ["Seated hamstring stretch", "Hip-flexor stretch", "Doorway chest stretch", "Wall slides for shoulders"],
        "Heart & blood pressure": ["Brisk walking or easy cycling at RPE 11–13", "Marching in place, arms swinging", "Breathing pacer 5 min/day"],
        "Body composition": ["Walking 20–40 min", "Light resistance bands 2×/week", "Meal-quality review with a professional"],
        "Effort tolerance": ["Short easy walks (5–10 min), several times a day", "Interval walking: 1 min brisk, 2 min easy"],
    }
    weak = sorted(domains, key=lambda d: d[1])
    focus = [d[0] for d in weak[:3]] or ["Heart & blood pressure"]
    lines = ["# 4-Week Starter Plan", f"Focus areas: {', '.join(focus)}", "",
             "Effort target: RPE 11–13 on the Borg 6–20 scale (you can speak in full sentences). Stop for chest pain, dizziness or severe breathlessness.", ""]
    for w, txt in enumerate(["Week 1 — learn the moves, 1 set of 8–10, 2–3 days", "Week 2 — add a second set or +5 min walking",
                             "Week 3 — add reps or hold time; 3 days", "Week 4 — keep week-3 load, then RE-TEST the assessment"], 1):
        lines.append(f"## {txt}")
        for f in focus:
            for e in EXMENU.get(f, [])[:3]:
                lines.append(f"- {f}: {e}")
        lines.append("")
    lines.append("Always warm up 5 minutes first and have support nearby for balance work. Review with a clinician before starting if you have heart, lung or joint conditions.")
    return "\n".join(lines)

# ═════════════════════════════════════════════════════════════════════════════
#  HEADER / NAVIGATION
# ═════════════════════════════════════════════════════════════════════════════
items = ["🌿 ReubenSoul PeaceUnity LifeHaven", "💪 AI Fitness Tracking", "🧍 Total Body Assessment",
         "🏥 Elderly Care Management", "📋 Digital Intake Forms", "🧭 Wellness & Safety Check-ins",
         "🔒 Phone Security", "🌐 Translator", "🌍 Health • Peace • Unity"] * 2
ticker_html = "".join(f'<span class="ticker-item"><span class="ticker-dot">◆</span>{i}</span>' for i in items)
st.markdown(f'<div class="ticker-wrap"><div class="ticker-inner">{ticker_html}</div></div>', unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">◆ Premium Care Platform ◆</div>
  <div class="hero-title">ReubenSoul PeaceUnity LifeHaven</div>
  <div class="hero-sub">Elderly Care · AI Fitness · Body Assessment · Wellness Check-ins · Phone Safety · Translation<br>Built with Love by ReubenSoul4peaceunity</div>
  <div class="badge-row">
    <span class="badge">💪 Fitness AI</span><span class="badge">🧍 Body Assessment</span><span class="badge">📋 Digital Intake</span>
    <span class="badge">🧭 Safe-Zone Check-ins</span><span class="badge">🔒 Phone Security</span>
    <span class="badge">🌐 Multilingual</span><span class="badge">📄 PDF Export</span>
  </div>
</div>""", unsafe_allow_html=True)

st.sidebar.markdown("""<div class="sidebar-brand"><div class="sidebar-brand-name">🌿 LifeHaven</div>
<div class="sidebar-brand-tag">ReubenSoul PeaceUnity</div></div>""", unsafe_allow_html=True)

MODULES = ["🏋️ Fitness Training", "🧍 Total Body Assessment", "🏥 Care Portal", "📋 Intake Forms",
           "🧭 Wellness & Safety", "🔒 Phone Security", "🌐 Translator", "🩺 Vitals Lab (Phone Sensors)", "🦠 Illness & Infection Check", "📘 User Guide", "✨ Client Portal"]
menu = st.sidebar.selectbox("Module", MODULES, label_visibility="collapsed")
st.sidebar.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.sidebar.caption("REUBENSOUL4PEACEUNITY · HEALTH • PEACE • UNITY")

# ═════════════════════════════════════════════════════════════════════════════
#  1 — FITNESS TRAINING
# ═════════════════════════════════════════════════════════════════════════════
if menu == "🏋️ Fitness Training":
    section_header("Module 01", "Fitness Training",
                   "AI angle-based rep counter · Pose detection from camera or upload · GPS map · Analytics")
    tab1, tab2, tab3 = st.tabs(["🏃 Live Training", "📍 GPS Map", "📊 Analytics"])

    EX = {
        "Bicep Curl": {"L": (11, 13, 15), "R": (12, 14, 16), "flex": 50, "ext": 160},
        "Squat": {"L": (23, 25, 27), "R": (24, 26, 28), "flex": 100, "ext": 160},
        "Shoulder Press": {"L": (11, 13, 15), "R": (12, 14, 16), "flex": 90, "ext": 160},
    }

    with tab1:
        if not HAS_POSE:
            st.error("Pose detection needs `opencv-python-headless` and `mediapipe` in requirements.txt.")
        else:
            c1, c2, c3 = st.columns(3)
            exercise = c1.selectbox("Exercise", list(EX))
            side = c2.selectbox("Side facing camera", ["Left", "Right"])
            src = c3.radio("Image source", ["Camera", "Upload"], horizontal=True)
            cfg = EX[exercise]
            st.info("📸 Take one photo at the **extended** position (arm straight / standing) and one at the "
                    "**flexed** position (curled / squat bottom / press start). A rep is counted each time you "
                    "return from flexed to extended. Keep your whole body in frame, side-on, in good light.", icon="💡")
            img = st.camera_input("Capture position") if src == "Camera" else \
                st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png"])
            if img is not None:
                data = img.getvalue()
                key = hash(data)
                if key != st.session_state.last_img:          # process each new photo exactly once
                    st.session_state.last_img = key
                    rgb, lms = detect_pose(data)
                    if rgb is None:
                        st.session_state.last_pose = {"error": "Could not decode image."}
                    elif lms is None:
                        st.session_state.last_pose = {"error": "No pose detected. Show your full body in good light.", "img": rgb}
                    else:
                        lm = lms.landmark
                        p1, p2, p3 = cfg["L" if side == "Left" else "R"]
                        ang = angle((lm[p1].x, lm[p1].y), (lm[p2].x, lm[p2].y), (lm[p3].x, lm[p3].y))
                        vis = min(lm[p1].visibility, lm[p2].visibility, lm[p3].visibility)
                        if ang > cfg["ext"]:
                            if st.session_state.stage == "flexed":
                                st.session_state.reps += 1
                            st.session_state.stage = "extended"
                        elif ang < cfg["flex"]:
                            st.session_state.stage = "flexed"
                        h, w = rgb.shape[:2]
                        ann = draw_pose(rgb, lms, f"{int(ang)} deg", (int(lm[p2].x * w) - 50, int(lm[p2].y * h) - 20))
                        st.session_state.last_pose = {"img": ann, "ang": ang, "vis": vis}
                        st.session_state.ex_log.append({"time": now_str(), "exercise": exercise,
                                                        "angle": round(ang, 1), "stage": st.session_state.stage,
                                                        "reps": st.session_state.reps})
                lp = st.session_state.last_pose
                if lp:
                    if "error" in lp:
                        st.warning("⚠️ " + lp["error"])
                    if "img" in lp:
                        st.image(lp["img"], channels="RGB", use_container_width=True)
                    if "ang" in lp:
                        if lp["vis"] < 0.5:
                            st.warning("Some joints were hard to see; angle may be inaccurate. Retake side-on with better light.")
                        stage = st.session_state.stage or "—"
                        msg = {"flexed": "⬆️ FLEXED — now return to the extended position to complete the rep",
                               "extended": "⬇️ EXTENDED — flex for the next rep"}.get(stage, "Between positions — move to a clear end position")
                        st.markdown(f"""<div class="rep-display"><div class="rep-number">{st.session_state.reps}</div>
                          <div style="color:var(--muted);font-size:.8rem;letter-spacing:.12em;text-transform:uppercase">Reps completed</div>
                          <div class="rep-angle">{int(lp['ang'])}° joint angle</div>
                          <div class="rep-stage">{msg}</div></div>""", unsafe_allow_html=True)

            elapsed = (datetime.now() - st.session_state.start_time).seconds
            st.markdown(f"""<div class="metric-row">
              <div class="metric-card"><div class="metric-val">{st.session_state.reps}</div><div class="metric-label">Reps</div></div>
              <div class="metric-card"><div class="metric-val">{round(st.session_state.reps*0.5,1)}</div><div class="metric-label">Calories (rough est.)</div></div>
              <div class="metric-card"><div class="metric-val">{round(elapsed/60,1)}</div><div class="metric-label">Minutes</div></div></div>""",
                        unsafe_allow_html=True)
            st.markdown("**Rate of Perceived Exertion (RPE)** — how hard did that set feel?")
            r1, r2 = st.columns([4, 1])
            rpe_set = r1.select_slider("RPE (Borg CR10): 0 rest · 3 moderate · 5 hard · 7 very hard · 10 maximal",
                                       options=list(range(0, 11)), value=3)
            if r2.button("➕ Log RPE"):
                st.session_state.rpe_log.append({"time": now_str(), "exercise": exercise,
                                                 "reps": st.session_state.reps, "rpe": rpe_set})
                st.success(f"Logged RPE {rpe_set}")
            st.caption("Most general-fitness work should feel like RPE 3–6. Stop and seek help for chest pain, severe breathlessness, dizziness or faintness.")
            if st.button("🔁 Reset Session"):
                st.session_state.update({"reps": 0, "stage": None, "start_time": datetime.now(),
                                         "last_img": None, "last_pose": None, "ex_log": [], "rpe_log": []})
                st.rerun()

    with tab2:
        lat = st.number_input("Latitude", value=34.05, format="%.6f", key="fit_lat")
        lon = st.number_input("Longitude", value=-118.25, format="%.6f", key="fit_lon")
        if not HAS_MAP:
            st.error("Maps need `folium` and `streamlit-folium` in requirements.txt.")
        elif st.button("📍 Show Map"):
            m = folium.Map(location=[lat, lon], zoom_start=14, tiles="CartoDB dark_matter")
            folium.Marker([lat, lon], tooltip="📍 Location", icon=folium.Icon(color="green", icon="heart", prefix="fa")).add_to(m)
            st_folium(m, width=700, height=480, returned_objects=[])

    with tab3:
        elapsed = (datetime.now() - st.session_state.start_time).seconds
        df = pd.DataFrame({"Metric": ["Reps", "Calories (est.)", "Minutes"],
                           "Value": [st.session_state.reps, round(st.session_state.reps * 0.5, 1), round(elapsed / 60, 1)]})
        st.bar_chart(df.set_index("Metric"))
        if st.session_state.ex_log:
            log = pd.DataFrame(st.session_state.ex_log)
            st.line_chart(log.set_index("time")["angle"])
            st.dataframe(log, use_container_width=True)
            st.download_button("📥 Download session CSV", log.to_csv(index=False).encode(), "session.csv", "text/csv")
        else:
            st.caption("Capture a photo in Live Training to see your angle history here.")
        if st.session_state.rpe_log:
            rl = pd.DataFrame(st.session_state.rpe_log)
            st.markdown("**RPE log**")
            st.line_chart(rl.set_index("time")["rpe"])
            st.dataframe(rl, use_container_width=True, hide_index=True)

# ═════════════════════════════════════════════════════════════════════════════
#  2 — TOTAL BODY ASSESSMENT
# ═════════════════════════════════════════════════════════════════════════════
elif menu == "🧍 Total Body Assessment":
    section_header("Module 02", "Total Body Assessment",
                   "Vitals · body ratios · fall-risk screen · functional tests · posture photo analysis · PDF report")
    st.info("This is a **screening and education tool**, not a diagnosis. Share results with a physician or physical therapist.", icon="ℹ️")
    tabA, tabB = st.tabs(["📏 Measurements & Functional Tests", "📸 Posture Photo Analysis"])

    with tabA:
        t1, t2 = st.columns([2, 1])
        demo = t1.checkbox("🎯 Load a sample client (see a full example result instantly)")
        units = t2.radio("Units", ["Metric (cm/kg)", "Imperial (in/lb)"], horizontal=True)
        metric = units.startswith("Metric")
        to_cm = 1.0 if metric else 2.54            # display units → cm
        lb = 1.0 if metric else 2.20462            # kg → display weight
        lu, wu = ("cm", "kg") if metric else ("in", "lb")
        dv = int(demo)
        S = dict(name="Sample Client", age=72, sex="Female", height=165.0, weight=78.0, waist=90.0, hip=102.0, neck=33.0,
                 hr=78, sbp=138, dbp=86, chair=8, tug=13.0, tandem=6.0, slL=4.0, slR=7.0, reach=-8.0,
                 shoulder="Gap 5 cm or more", rpe=14) if demo else \
            dict(name="", age=70, sex="Female", height=165.0, weight=70.0, waist=85.0, hip=100.0, neck=33.0,
                 hr=72, sbp=120, dbp=78, chair=0, tug=0.0, tandem=0.0, slL=0.0, slR=0.0, reach=0.0,
                 shoulder="Not tested", rpe="Not rated")
        if not demo and st.session_state.get("latest_hr"):
            S["hr"] = int(st.session_state["latest_hr"])
            st.caption(f"❤️ Resting heart rate pre-filled from your latest camera reading ({S['hr']} bpm).")
        SH_OPTS = ["Not tested", "Fingers overlap", "Fingertips just touch", "Gap under 5 cm", "Gap 5 cm or more"]
        with st.form(f"body_form_{dv}_{int(metric)}"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Client name *", S["name"])
            age = c2.number_input("Age", 1, 110, S["age"])
            sex = c3.selectbox("Sex (for reference norms)", ["Female", "Male"], index=["Female", "Male"].index(S["sex"]))
            st.markdown("**Body measurements** — see the 📘 User Guide for exactly how to measure")
            c1, c2, c3, c4, c5 = st.columns(5)
            height = c1.number_input(f"Height ({lu})", 10.0, 300.0, round(S["height"] / to_cm, 1)) * to_cm
            weight = c2.number_input(f"Weight ({wu})", 10.0, 700.0, round(S["weight"] * lb, 1)) / lb
            waist = c3.number_input(f"Waist ({lu})", 10.0, 300.0, round(S["waist"] / to_cm, 1)) * to_cm
            hip = c4.number_input(f"Hip ({lu})", 10.0, 300.0, round(S["hip"] / to_cm, 1)) * to_cm
            neck = c5.number_input(f"Neck ({lu})", 5.0, 100.0, round(S["neck"] / to_cm, 1)) * to_cm
            st.markdown("**Heart & blood pressure**")
            c1, c2, c3 = st.columns(3)
            hr = c1.number_input("Resting heart rate (bpm)", 30, 220, S["hr"])
            sbp = c2.number_input("Systolic BP (top number)", 60, 260, S["sbp"])
            dbp = c3.number_input("Diastolic BP (bottom number)", 30, 160, S["dbp"])
            st.markdown("**Strength & balance tests** (leave at 0 if not done)")
            c1, c2, c3 = st.columns(3)
            chair = c1.number_input("30-sec chair stands (reps)", 0, 60, S["chair"])
            tug = c2.number_input("Timed Up & Go (seconds)", 0.0, 120.0, S["tug"], step=0.5)
            tandem = c3.number_input("Tandem-stance hold (sec, max 10)", 0.0, 10.0, S["tandem"], step=0.5)
            c1, c2 = st.columns(2)
            slL = c1.number_input("Single-leg stance — LEFT leg, eyes open (sec, max 30)", 0.0, 30.0, S["slL"], step=0.5)
            slR = c2.number_input("Single-leg stance — RIGHT leg, eyes open (sec, max 30)", 0.0, 30.0, S["slR"], step=0.5)
            st.markdown("**Flexibility** (leave at 0 / Not tested if not done)")
            c1, c2 = st.columns(2)
            reach = c1.number_input(f"Sit-and-reach ({lu}): + past toes, − short of toes", -60.0, 60.0, round(S["reach"] / to_cm, 1), step=0.5)
            shoulder = c2.selectbox("Back-scratch (shoulder) test", SH_OPTS, index=SH_OPTS.index(S["shoulder"]))
            st.markdown("**Effort** — Rate of Perceived Exertion right after the chair-stand or walking test")
            rpe = st.select_slider("RPE (Borg 6–20: 6 none · 11 light · 13 somewhat hard · 15 hard · 17 very hard · 20 max)",
                                   options=["Not rated"] + list(range(6, 21)), value=S["rpe"])
            st.markdown("**Fall-risk screening questions (CDC STEADI)**")
            c1, c2, c3 = st.columns(3)
            q_unsteady = c1.checkbox("Feels unsteady when standing or walking", value=demo)
            q_worry = c2.checkbox("Worries about falling", value=demo)
            q_fell = c3.checkbox("Has fallen in the past year")
            c1, c2 = st.columns(2)
            pain = c1.multiselect("Pain areas", ["Neck", "Shoulders", "Upper back", "Lower back", "Hips", "Knees", "Ankles/feet", "Wrists/hands"],
                                  default=["Knees"] if demo else [])
            activity = c2.slider("Active days per week", 0, 7, 2 if demo else 3)
            notes = st.text_area("Notes / limitations", height=70)
            go = st.form_submit_button("🧮 Run Assessment", use_container_width=True)

        if go:
            if not name.strip():
                st.error("Please enter the client's name.")
            else:
                findings, recs, urgent = [], [], False
                dom = {}
                def put(d, sc): dom.setdefault(d, []).append(sc)

                # ---- Body composition
                bmi = weight / ((height / 100) ** 2)
                whtr = waist / height
                whr = waist / hip
                if age < 18:
                    findings.append(("BMI", f"{bmi:.1f}", "Use pediatric BMI-for-age percentile charts for under 18"))
                else:
                    findings.append(("BMI", f"{bmi:.1f}", bmi_cat(bmi)))
                    put("Body composition", 100 if 18.5 <= bmi < 25 else 60 if bmi < 30 else 30)
                    if bmi >= 25 or bmi < 18.5:
                        recs.append("Discuss weight goals with a clinician; combine daily movement with balanced nutrition.")
                bf = bodyfat_navy(sex, height, waist, neck, hip) if age >= 18 else None
                if bf is not None:
                    cat, sc = bf_cat(bf, sex)
                    findings.append(("Body fat % (US Navy estimate)", f"{bf:.1f}%", cat + " — estimate is typically ±3–4%"))
                    put("Body composition", sc)
                    if sc <= 40:
                        recs.append("Body-fat estimate is in the higher range: build strength training and walking, and review nutrition with a professional.")
                elif age >= 18:
                    findings.append(("Body fat % (US Navy estimate)", "—", "Check neck/waist/hip entries"))
                findings.append(("Waist-to-height ratio", f"{whtr:.2f}", "Increased risk (≥0.50)" if whtr >= .5 else "Healthy (<0.50)"))
                put("Body composition", 100 if whtr < .5 else 50)
                lim = .90 if sex == "Male" else .85
                findings.append(("Waist-to-hip ratio", f"{whr:.2f}", f"Increased risk (>{lim:.2f})" if whr > lim else f"Within range (≤{lim:.2f})"))

                # ---- Heart & blood pressure
                findings.append(("Resting heart rate", f"{hr} bpm",
                                 "Below typical (<60) — normal for fit people, otherwise ask a clinician" if hr < 60
                                 else "Typical (60–100)" if hr <= 100 else "Above typical (>100) — recheck fully rested"))
                bp = bp_cat(sbp, dbp)
                findings.append(("Blood pressure", f"{sbp}/{dbp}", bp))
                bps = 0 if "CRISIS" in bp else 25 if "Stage 2" in bp else 45 if "Stage 1" in bp else 75 if bp == "Elevated" else 100
                put("Heart & blood pressure", bps)
                put("Heart & blood pressure", 100 if 50 <= hr <= 100 else 60)
                if "CRISIS" in bp:
                    urgent = True
                elif "Stage" in bp:
                    recs.append("Blood pressure is in a hypertensive range — arrange a clinician review; recheck seated after 5 minutes of rest.")
                hrmax = 208 - 0.7 * age
                hrr = hrmax - hr
                if hrr > 0:
                    findings.append(("Estimated max HR / moderate zone", f"{hrmax:.0f} bpm / {hr + .4 * hrr:.0f}–{hr + .59 * hrr:.0f} bpm",
                                     "Estimates only. Beta-blockers and some medicines lower heart rate — use RPE instead."))

                # ---- Strength
                if chair:
                    thr = chair_norm(age, sex) if age >= 60 else None
                    if thr is None:
                        findings.append(("30-sec chair stand", f"{chair} reps", "Norms apply to ages 60+"))
                    else:
                        low = chair < thr
                        findings.append(("30-sec chair stand", f"{chair} reps", f"Below average (<{thr}) — lower-body strength work advised" if low else f"At/above average (≥{thr})"))
                        put("Lower-body strength", 50 if low else 100)
                        if low: recs.append("Add sit-to-stand, step-ups and supported squats 2–3×/week.")

                # ---- Balance & fall risk
                if tug:
                    findings.append(("Timed Up & Go", f"{tug:.1f}s", "≥12 s indicates fall risk" if tug >= 12 else "<12 s — lower fall risk"))
                    put("Balance & fall risk", 40 if tug >= 12 else 100)
                    if tug >= 12: recs.append("TUG ≥12 s: request a fall-risk evaluation and gait/balance training.")
                if tandem:
                    findings.append(("Tandem stance", f"{tandem:.1f}s", "<10 s — increased fall risk" if tandem < 10 else "10 s held — good"))
                    put("Balance & fall risk", 50 if tandem < 10 else 100)
                    if tandem < 10: recs.append("Practise supported tandem stance and heel-to-toe walking near a counter.")
                for lab, v in (("LEFT", slL), ("RIGHT", slR)):
                    if v:
                        ref = sls_ref(age)
                        txt = ("Under 5 s — high fall risk" if v < 5 else f"Below typical for age (~{ref} s)" if v < ref else f"Typical or better for age (~{ref} s)")
                        findings.append((f"Single-leg stance, {lab}", f"{v:.1f}s", txt))
                        put("Balance & fall risk", 20 if v < 5 else 60 if v < ref else 100)
                if slL and slR and abs(slL - slR) >= 5:
                    recs.append(f"Left/right balance differs by {abs(slL - slR):.0f} s — train the weaker leg and mention it to a physio.")
                if min([x for x in (slL, slR) if x] or [99]) < 5:
                    recs.append("Single-leg stance under 5 s: practise next to a counter daily (start 10 s, build up) and ask about a fall-prevention program.")
                at_risk = q_unsteady or q_worry or q_fell
                findings.append(("Fall-risk screen", "Positive" if at_risk else "Negative",
                                 "Answered 'yes' to at least one STEADI key question" if at_risk else "No key questions endorsed"))
                put("Balance & fall risk", 50 if at_risk else 100)
                if at_risk:
                    recs.append("Positive fall screen: review medications, vision, footwear and home hazards with a clinician.")

                # ---- Flexibility
                if reach != 0:
                    rc = reach * to_cm   # → cm
                    lab = "Good — reached/passed toes" if rc >= 0 else "Fair — slightly short of toes" if rc >= -7.5 else "Limited — hamstring / low-back tightness"
                    findings.append(("Sit-and-reach", f"{rc:+.1f} cm", lab))
                    put("Flexibility", 100 if rc >= 0 else 65 if rc >= -7.5 else 35)
                    if rc < -7.5: recs.append("Add gentle hamstring and hip stretching daily (hold 20–30 s, no bouncing).")
                if shoulder != "Not tested":
                    sc, lab = SHOULDER_SCORE[shoulder]
                    findings.append(("Back-scratch (shoulder)", shoulder, lab))
                    put("Flexibility", sc)
                    if sc <= 60: recs.append("Add shoulder mobility work (doorway chest stretch, wall slides).")

                # ---- Effort (RPE)
                if rpe != "Not rated":
                    sc = 100 if rpe <= 12 else 80 if rpe <= 14 else 55 if rpe <= 16 else 30
                    findings.append(("Effort on test (RPE 6–20)", f"{rpe} — {BORG[rpe]}",
                                     "Test felt easy-to-moderate" if rpe <= 13 else "Test felt hard for the work done — fitness or fatigue may be limiting"))
                    put("Effort tolerance", sc)
                    if rpe >= 15: recs.append("The test felt hard (RPE ≥15): build gradually with short, easy sessions and re-test.")

                if activity < 3:
                    recs.append("Build toward 150 min/week of moderate activity plus 2 strength sessions, as tolerated.")
                if pain:
                    recs.append("Pain reported in: " + ", ".join(pain) + ". Avoid loading painful areas; seek professional evaluation if persistent.")
                recs.append("Re-assess every 8–12 weeks, under the same conditions, to track change.")

                stat = lambda x: "✅ Good" if x >= 80 else "⚠️ Fair" if x >= 55 else "🔶 Needs work"
                domains = [(d, round(sum(v) / len(v)), stat(round(sum(v) / len(v)))) for d, v in dom.items()]
                overall = round(sum(x[1] for x in domains) / len(domains)) if domains else None
                st.session_state["body_result"] = {"name": name, "age": age, "sex": sex, "findings": findings, "recs": recs,
                                                   "urgent": urgent, "notes": notes, "ts": now_str(),
                                                   "domains": domains, "overall": overall}
                with db() as c:
                    c.execute("INSERT INTO assessments (ts,name,kind,data) VALUES (?,?,?,?)",
                              (now_str(), name, "body", json.dumps(st.session_state["body_result"])))

        r = st.session_state.get("body_result")
        if r:
            if r["urgent"]:
                st.error("🚨 Blood pressure reading is in the hypertensive-crisis range. If this is accurate and there are symptoms "
                         "(chest pain, severe headache, shortness of breath, weakness) call 911; otherwise recheck and contact a clinician today.")
            st.markdown(f"### Results — {r['name']} · {r['age']} · {r['ts']}")
            if r.get("overall") is not None:
                m1, m2 = st.columns([1, 3])
                m1.metric("Overall wellness score", f"{r['overall']} / 100", ("Good" if r["overall"] >= 80 else "Fair" if r["overall"] >= 55 else "Needs work"), delta_color="off")
                m2.bar_chart(pd.DataFrame({"Score": [d[1] for d in r["domains"]]}, index=[d[0] for d in r["domains"]]))
                st.dataframe(pd.DataFrame(r["domains"], columns=["Area", "Score", "Status"]), use_container_width=True, hide_index=True)
                st.caption("The overall score is a simple screening summary of the tests you entered — not a clinical measure.")
            st.markdown("**Detailed results**")
            st.dataframe(pd.DataFrame(r["findings"], columns=["Measure", "Value", "Interpretation"]), use_container_width=True, hide_index=True)
            st.markdown("**Recommendations**")
            for x in r["recs"]:
                st.markdown(f'<div class="check-item">• {x}</div>', unsafe_allow_html=True)
            if r.get("domains"):
                with st.expander("🗓️ 4-week starter plan (built from the weakest areas)"):
                    plan = build_plan(r["domains"], r["age"])
                    st.markdown(plan)
                    st.download_button("📥 Download plan (.txt)", plan.encode("utf-8"), "starter_plan.txt", "text/plain")
            if HAS_PDF:
                p = LifeHavenPDF(); p.add_page()
                p.h1("ReubenSoul PeaceUnity LifeHaven", 18); p.h1("Total Body Assessment Report", 13); p.ln(4)
                p.section("CLIENT"); p.kv("Name", r["name"]); p.kv("Age / Sex", f"{r['age']} / {r['sex']}"); p.kv("Date", r["ts"]); p.ln(2)
                if r.get("overall") is not None:
                    p.section("OVERALL SUMMARY")
                    p.kv("Overall score", f"{r['overall']} / 100 (screening summary)", 60)
                    for d, sc, stt in r["domains"]:
                        p.kv(d, f"{sc} / 100 — {stt}", 60)
                    p.ln(2)
                p.section("DETAILED RESULTS")
                for m, v, i in r["findings"]:
                    p.kv(m, f"{v} — {i}", 60)
                p.ln(2); p.section("RECOMMENDATIONS")
                for x in r["recs"]:
                    p.para("• " + x)
                if r["notes"].strip():
                    p.ln(2); p.section("NOTES"); p.para(r["notes"])
                p.ln(4); p.para("Screening tool only — not a medical diagnosis. Review with a licensed clinician.", 9, "I")
                fn = "".join(x for x in r["name"] if x.isalnum() or x == " ").replace(" ", "_") or "client"
                st.download_button("📥 Download PDF Report", pdf_bytes(p), f"{fn}_body_assessment.pdf", "application/pdf")
            else:
                pdf_unavailable()

    with tabB:
        if not HAS_POSE:
            st.error("Posture analysis needs `opencv-python-headless` and `mediapipe` in requirements.txt.")
        else:
            st.markdown("Stand relaxed ~2–3 m from the camera, full body in frame, plain background. "
                        "Take a **front** photo, then optionally a **side** photo.")
            c1, c2 = st.columns(2)
            view = c1.radio("Photo view", ["Front", "Side"], horizontal=True)
            src = c2.radio("Source", ["Camera", "Upload"], horizontal=True, key="post_src")
            pimg = st.camera_input("Posture photo") if src == "Camera" else st.file_uploader("Upload posture photo", type=["jpg", "jpeg", "png"], key="post_up")
            if pimg is not None:
                rgb, lms = detect_pose(pimg.getvalue())
                if rgb is None:
                    st.error("Could not decode image.")
                elif lms is None:
                    st.warning("No body detected. Step back so your whole body is visible and well lit.")
                else:
                    st.image(draw_pose(rgb, lms), channels="RGB", use_container_width=True)
                    rows = posture_metrics(lms.landmark, view)
                    st.dataframe(pd.DataFrame(rows, columns=["Metric", "Value", "Flag", "Note"]), use_container_width=True, hide_index=True)
                    st.caption("Camera angle and clothing affect these numbers. Treat flags as prompts for a professional posture review, not diagnoses.")
                    # joint angles
                    lm = lms.landmark
                    ja = {"Left elbow": (11, 13, 15), "Right elbow": (12, 14, 16),
                          "Left knee": (23, 25, 27), "Right knee": (24, 26, 28),
                          "Left hip": (11, 23, 25), "Right hip": (12, 24, 26)}
                    st.markdown("**Joint angles**")
                    st.dataframe(pd.DataFrame([(k, f"{angle((lm[a].x, lm[a].y), (lm[b].x, lm[b].y), (lm[c].x, lm[c].y)):.0f}°")
                                               for k, (a, b, c) in ja.items()], columns=["Joint", "Angle"]),
                                 use_container_width=True, hide_index=True)

# ═════════════════════════════════════════════════════════════════════════════
#  3 — CARE PORTAL
# ═════════════════════════════════════════════════════════════════════════════
elif menu == "🏥 Care Portal":
    section_header("Module 03", "Elderly Care Portal", "Add residents, search records, generate PDFs with multilingual voice summaries")
    portal_menu = st.sidebar.radio("Care Menu", ["🆕 New Admission", "🔍 Search Records"])

    if portal_menu == "🆕 New Admission":
        st.markdown('<div class="intake-head">🆕 New Resident Admission</div>', unsafe_allow_html=True)
        lang_choice = st.selectbox("Language / Idioma", list(LANGS))
        lang_code = LANGS[lang_choice]
        name = st.text_input("Full Name *")
        dob = st.text_input("Date of Birth (YYYY-MM-DD)")
        med_info = st.text_area("Medical Conditions", height=80)
        meds = st.text_area("Medications & Dosage", height=80)
        allergies = st.text_area("Allergies", height=68)
        contact = st.text_input("Emergency Contact (Name / Relation / Phone)")
        c1, c2 = st.columns(2)
        if c1.button("💾 Save Resident"):
            if not name.strip():
                st.error("⚠️ Name is required.")
            else:
                with db() as c:
                    c.execute("INSERT INTO residents (name,dob,medical_info,medications,allergies,emergency_contact,language,created_at) VALUES (?,?,?,?,?,?,?,?)",
                              (name, dob, med_info, meds, allergies, contact, lang_code, now_str()))
                st.success(f"✅ {name} saved successfully!")
                st.balloons()
        if c2.button("📄 Generate PDF"):
            if not name.strip():
                st.error("⚠️ Enter a name first.")
            elif not HAS_PDF:
                pdf_unavailable()
            else:
                p = LifeHavenPDF(); p.add_page(); p.h1("LifeHaven — Care Admission Record"); p.ln(4)
                for k, v in {"Name": safe(name), "DOB": safe(dob), "Medical": safe(med_info), "Medications": safe(meds),
                             "Allergies": safe(allergies), "Emergency Contact": safe(contact), "Generated": now_str()}.items():
                    p.kv(k, v, 45)
                fn = "".join(x for x in name if x.isalnum() or x == " ").replace(" ", "_")
                st.download_button("📥 Download PDF", pdf_bytes(p), f"{fn}_admission.pdf", "application/pdf")
        if name.strip() and med_info.strip():
            aud = voice(f"Resident {safe(name)}. Conditions: {safe(med_info)}. Medications: {safe(meds)}.", lang_code)
            if aud:
                st.caption("🔊 Voice Summary"); st.audio(aud, format="audio/mp3")
    else:
        st.markdown('<div class="intake-head">🔍 Search Resident Records</div>', unsafe_allow_html=True)
        query = st.text_input("Search by name (leave blank to list all)")
        if st.button("🔍 Search"):
            with db() as c:
                rows = c.execute("SELECT * FROM residents WHERE name LIKE ? ORDER BY id DESC", (f"%{query}%",)).fetchall()
            if rows:
                st.download_button("📥 Export CSV", pd.DataFrame([dict(r) for r in rows]).to_csv(index=False).encode(), "residents.csv", "text/csv")
                for r in rows:
                    st.markdown(f"""<div class="card-gold">
                      <div style="font-size:1.1rem;font-weight:700;color:var(--gold2)">#{r['id']} — {safe(r['name'])}</div>
                      <div style="color:var(--muted);font-size:.82rem;margin-bottom:10px">DOB: {safe(r['dob'])} · Added: {safe(r['created_at'])}</div>
                      <div>🩺 <b>Medical:</b> {safe(r['medical_info'])}</div><div>💊 <b>Medications:</b> {safe(r['medications'])}</div>
                      <div>⚠️ <b>Allergies:</b> {safe(r['allergies'])}</div><div>📞 <b>Emergency:</b> {safe(r['emergency_contact'])}</div></div>""",
                                unsafe_allow_html=True)
                    aud = voice(f"Resident {safe(r['name'])}. Conditions: {safe(r['medical_info'])}. Medications: {safe(r['medications'])}.", (r["language"] or "en")[:2])
                    if aud: st.audio(aud, format="audio/mp3")
            else:
                st.warning("No records found.")

# ═════════════════════════════════════════════════════════════════════════════
#  4 — INTAKE FORMS
# ═════════════════════════════════════════════════════════════════════════════
elif menu == "📋 Intake Forms":
    section_header("Module 04", "Digital Admission Intake", "Complete all 7 sections · Saves to database · Instant PDF packet")
    tabF, tabR = st.tabs(["📝 New Intake", "🗂️ Saved Intakes"])

    with tabF:
        with st.form("intake_form"):
            st.markdown('<div class="intake-head">👤 Section 1 — Client Profile</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            full_name = c1.text_input("Full Legal Name *")
            dob = c2.date_input("Date of Birth *", value=date(1950, 1, 1), min_value=date(1900, 1, 1), max_value=date.today())
            c3, c4, c5 = st.columns(3)
            gender = c3.selectbox("Gender Identity", ["Male", "Female", "Non-binary", "Prefer not to say", "Other"])
            marital = c4.selectbox("Marital Status", ["Single", "Married", "Widowed", "Divorced", "Separated"])
            prim_lang = c5.selectbox("Primary Language", ["English", "Spanish", "French", "Haitian Creole", "Portuguese", "Other"])

            st.markdown('<div class="intake-head">📞 Section 2 — Emergency Contacts</div>', unsafe_allow_html=True)
            ec1 = st.text_input("Primary Contact — Name / Relationship / Phone")
            ec2 = st.text_input("Secondary Contact — Name / Relationship / Phone")
            physician = st.text_input("Primary Care Physician — Name / Phone")

            st.markdown('<div class="intake-head">🩺 Section 3 — Health History</div>', unsafe_allow_html=True)
            chronic = st.text_area("Chronic Conditions", height=75)
            allergies = st.text_area("Known Allergies", height=75)
            meds_f = st.text_area("Current Medications & Dosage", height=85)
            immunize = st.text_input("Immunization Records")
            hospital = st.text_area("Recent Hospitalizations / Surgeries", height=75)

            st.markdown('<div class="intake-head">🏥 Section 4 — Medical Assessment</div>', unsafe_allow_html=True)
            adl = st.multiselect("ADL — Independent In:", ["Eating", "Bathing", "Dressing", "Toileting", "Transferring", "Continence"])
            mobility = st.selectbox("Mobility Status", ["Fully Ambulatory", "Uses Cane", "Uses Walker", "Uses Wheelchair", "Bedbound"])
            cognitive = st.selectbox("Cognitive Status", ["Alert & Oriented x4", "Mild Impairment", "Moderate Impairment", "Severe Impairment", "Dementia Diagnosed"])
            skin = st.selectbox("Skin Integrity", ["Intact", "Stage I Wound", "Stage II Wound", "Stage III/IV Wound", "Under Treatment"])
            dietary = st.text_input("Dietary Restrictions / Requirements")

            st.markdown('<div class="intake-head">⚖️ Section 5 — Legal Documentation</div>', unsafe_allow_html=True)
            poa = st.selectbox("Power of Attorney on File?", ["Yes — Medical & Financial", "Yes — Medical Only", "Yes — Financial Only", "No", "In Progress"])
            directives = st.selectbox("Advance Directives / DNR", ["Full Code", "DNR on File", "DNI on File", "Comfort Care Only", "Not Established"])
            hipaa = st.checkbox("✅ I acknowledge the HIPAA Privacy Notice and Admission Agreement")

            st.markdown('<div class="intake-head">💛 Section 6 — Care Preferences</div>', unsafe_allow_html=True)
            routine = st.text_area("Daily Routine Preferences", height=75)
            social = st.text_area("Social & Recreational Interests", height=75)
            equipment = st.text_input("Special Equipment (Oxygen, CPAP, Hearing Aid, etc.)")
            transport = st.selectbox("Transportation Needs", ["None", "Medical Appointments Only", "Regular Transport", "Ambulance Only"])

            st.markdown('<div class="intake-head">🔒 Section 7 — Phone Security Setup</div>', unsafe_allow_html=True)
            device = st.selectbox("Device Type", ["iPhone (iOS)", "Android", "Basic Cell Phone", "No Phone", "Other"])
            ph_concern = st.text_area("Known Issues (suspicious calls, strange apps, etc.)", height=80)
            sec_consent = st.checkbox("✅ Client consents to phone security checkup by care staff")
            submitted = st.form_submit_button("📤 Submit Complete Intake Packet", use_container_width=True)

        if submitted:
            if not full_name.strip():
                st.error("⚠️ Full name is required.")
            elif not hipaa:
                st.error("⚠️ HIPAA acknowledgment is required.")
            else:
                adl_str = ", ".join(adl) if adl else "—"
                ts = now_str()
                with db() as c:
                    c.execute("""INSERT INTO intake_forms (submitted_at,full_name,dob,gender,primary_language,marital_status,
                        emergency_contact1,emergency_contact2,primary_physician,chronic_conditions,allergies,medications,
                        immunizations,hospitalizations,adl_status,mobility,cognitive_status,skin_integrity,dietary,poa,
                        directives,hipaa_consent,daily_routine,social_interests,special_equipment,transportation,
                        device_type,security_consent,phone_concerns) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                              (ts, full_name, str(dob), gender, prim_lang, marital, safe(ec1), safe(ec2), safe(physician),
                               safe(chronic), safe(allergies), safe(meds_f), safe(immunize), safe(hospital), adl_str, mobility,
                               cognitive, skin, safe(dietary), poa, directives, "Yes", safe(routine), safe(social),
                               safe(equipment), transport, device, "Yes" if sec_consent else "No", safe(ph_concern)))
                st.success(f"🎉 Intake packet for **{full_name}** saved successfully!")
                st.balloons()
                if HAS_PDF:
                    p = LifeHavenPDF(); p.add_page()
                    p.h1("ReubenSoul PeaceUnity LifeHaven", 18); p.h1("Complete Admission Intake Packet", 13); p.ln(4)
                    secs = [
                        ("CLIENT PROFILE", {"Full Name": full_name, "DOB": str(dob), "Gender": gender, "Marital": marital, "Language": prim_lang}),
                        ("EMERGENCY CONTACTS", {"Primary": safe(ec1), "Secondary": safe(ec2), "Physician": safe(physician)}),
                        ("HEALTH HISTORY", {"Conditions": safe(chronic), "Allergies": safe(allergies), "Medications": safe(meds_f),
                                            "Immunizations": safe(immunize), "Hospitalizations": safe(hospital)}),
                        ("MEDICAL ASSESSMENT", {"ADL": adl_str, "Mobility": mobility, "Cognitive": cognitive, "Skin": skin, "Dietary": safe(dietary)}),
                        ("LEGAL", {"POA": poa, "Directives": directives, "HIPAA": "Acknowledged"}),
                        ("CARE PREFERENCES", {"Routine": safe(routine), "Social": safe(social), "Equipment": safe(equipment), "Transport": transport}),
                        ("PHONE SECURITY", {"Device": device, "Concerns": safe(ph_concern), "Consent": "Yes" if sec_consent else "No"}),
                    ]
                    for sname, fields in secs:
                        p.section(sname)
                        for k, v in fields.items():
                            p.kv(k, v)
                        p.ln(3)
                    p.para(f"Generated: {ts} | ReubenSoul PeaceUnity LifeHaven", 9, "I")
                    fn = "".join(x for x in full_name if x.isalnum() or x == " ").replace(" ", "_")
                    st.download_button("📥 Download Full PDF Intake Packet", pdf_bytes(p), f"{fn}_intake.pdf", "application/pdf")
                else:
                    pdf_unavailable()

    with tabR:
        q = st.text_input("Search saved intakes by name")
        with db() as c:
            rows = c.execute("SELECT * FROM intake_forms WHERE full_name LIKE ? ORDER BY id DESC LIMIT 200", (f"%{q}%",)).fetchall()
        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            st.dataframe(df[["id", "submitted_at", "full_name", "dob", "primary_language", "mobility", "cognitive_status", "directives"]],
                         use_container_width=True, hide_index=True)
            st.download_button("📥 Export all (CSV)", df.to_csv(index=False).encode(), "intakes.csv", "text/csv")
        else:
            st.caption("No saved intakes yet.")

# ═════════════════════════════════════════════════════════════════════════════
#  5 — WELLNESS & SAFETY (consent-based tracking)
# ═════════════════════════════════════════════════════════════════════════════
elif menu == "🧭 Wellness & Safety":
    section_header("Module 05", "Wellness & Safety Check-ins",
                   "Safe-zone location check-ins · mood trends · PHQ-2/GAD-2 screens · emergency ID card — for children, "
                   "people with mental-health needs, and people with memory loss")
    st.markdown("""<div class="card-teal"><b>Consent-first by design.</b> Use this only with the knowledge and agreement of the person
    being supported (or their parent/legal guardian). Tell them what is recorded and who can see it. Secretly tracking another adult
    can be illegal and harmful. Locations here are entered or confirmed at check-in; this app does not secretly read a phone's GPS.</div>""",
                unsafe_allow_html=True)
    tabs = st.tabs(["👤 Profiles", "📍 Check-in", "🗺️ Safe Zones & Map", "📈 Mood Trends", "🧠 Wellness Screen", "🪪 Emergency Card", "☎️ Crisis Help"])

    with db() as c:
        profiles = [dict(r) for r in c.execute("SELECT * FROM wellness_profiles ORDER BY name").fetchall()]
    pmap = {f"{p['name']} ({p['category']}) #{p['id']}": p for p in profiles}

    # ---- Profiles
    with tabs[0]:
        with st.form("wp_form"):
            c1, c2 = st.columns(2)
            wname = c1.text_input("Name *")
            wcat = c2.selectbox("Category", ["Child", "Adult with mental-health condition", "Person with dementia / memory loss", "Elderly resident", "Other"])
            c1, c2 = st.columns(2)
            wdob = c1.text_input("Date of birth (YYYY-MM-DD)")
            wec = c2.text_input("Emergency contact (Name / Relation / Phone)")
            wmed = st.text_area("Medical / support notes", height=70)
            c1, c2 = st.columns(2)
            wmeds = c1.text_input("Medications")
            wall = c2.text_input("Allergies")
            wcrisis = st.text_area("Crisis / calming plan (triggers, what helps, who to call, safe word)", height=80)
            c1, c2 = st.columns(2)
            wby = c1.text_input("Consent given by (the person, or parent/guardian name) *")
            wstale = c2.number_input("Alert if no check-in for (hours)", 1, 72, 6)
            wconsent = st.checkbox("✅ The person (or their legal guardian) knows about and agrees to these check-ins and who can see them")
            if st.form_submit_button("💾 Save profile", use_container_width=True):
                if not wname.strip() or not wby.strip() or not wconsent:
                    st.error("Name, who gave consent, and the consent checkbox are all required.")
                else:
                    with db() as c:
                        c.execute("""INSERT INTO wellness_profiles (name,category,dob,emergency_contact,medical_notes,medications,allergies,
                                     crisis_plan,consent_by,consent_date,stale_hours,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                                  (wname, wcat, wdob, wec, wmed, wmeds, wall, wcrisis, wby, now_str(), int(wstale), now_str()))
                    st.success("Profile saved."); st.rerun()
        if profiles:
            st.dataframe(pd.DataFrame(profiles)[["id", "name", "category", "consent_by", "consent_date", "stale_hours"]], use_container_width=True, hide_index=True)

    def pick_profile(key):
        if not pmap:
            st.info("Create a profile first (👤 Profiles tab).")
            return None
        return pmap[st.selectbox("Person", list(pmap), key=key)]

    def zone_status(pid, lat, lon):
        with db() as c:
            zs = c.execute("SELECT * FROM safe_zones WHERE profile_id=?", (pid,)).fetchall()
        if not zs:
            return "No safe zones set", True
        best = None
        for z in zs:
            d = haversine_m(lat, lon, z["lat"], z["lon"])
            if d <= z["radius_m"]:
                return f"Inside: {z['label']}", True
            if best is None or d < best[1]:
                best = (z["label"], d)
        return f"OUTSIDE all safe zones — nearest is {best[0]} ({best[1]:.0f} m away)", False

    # ---- Check-in
    with tabs[1]:
        p = pick_profile("ci_p")
        if p:
            with db() as c:
                last = c.execute("SELECT * FROM checkins WHERE profile_id=? ORDER BY id DESC LIMIT 1", (p["id"],)).fetchone()
            if last:
                age_h = (datetime.now() - datetime.strptime(last["ts"], "%Y-%m-%d %H:%M")).total_seconds() / 3600
                if age_h > p["stale_hours"]:
                    st.markdown(f'<div class="card-red">⏰ No check-in for {age_h:.1f} h (limit {p["stale_hours"]} h). '
                                f'Call {safe(p["emergency_contact"])} / the person directly. If you cannot reach them and they may be at risk, call 911.</div>',
                                unsafe_allow_html=True)
                else:
                    st.caption(f"Last check-in {last['ts']} — {last['status']} · {safe(last['zone_status'])}")
            else:
                st.caption("No check-ins yet.")
            with st.form("ci_form"):
                c1, c2 = st.columns(2)
                mood = c1.select_slider("How are they feeling?", options=[1, 2, 3, 4, 5], value=3,
                                        format_func=lambda x: {1: "1 Very low", 2: "2 Low", 3: "3 Okay", 4: "4 Good", 5: "5 Great"}[x])
                status = c2.selectbox("Status", ["Safe / OK", "Needs support", "NEED HELP NOW"])
                inc = st.checkbox("Include location", value=True)
                c1, c2 = st.columns(2)
                lat = c1.number_input("Latitude", value=34.05, format="%.6f", key="ci_lat")
                lon = c2.number_input("Longitude", value=-118.25, format="%.6f", key="ci_lon")
                note = st.text_area("Note (optional)", height=60)
                if st.form_submit_button("✅ Record check-in", use_container_width=True):
                    zs, inside = ("Location not shared", True) if not inc else zone_status(p["id"], lat, lon)
                    with db() as c:
                        c.execute("INSERT INTO checkins (profile_id,ts,mood,status,lat,lon,zone_status,note) VALUES (?,?,?,?,?,?,?,?)",
                                  (p["id"], now_str(), mood, status, lat if inc else None, lon if inc else None, zs, note))
                    st.success(f"Recorded · {zs}")
                    if not inside:
                        st.markdown(f'<div class="card-red">📍 {p["name"]} is outside every safe zone. Call them or their contact '
                                    f'({safe(p["emergency_contact"])}) now. If missing or in danger, call 911 (missing child: then NCMEC 1-800-843-5678).</div>',
                                    unsafe_allow_html=True)
                    if status == "NEED HELP NOW" or mood == 1:
                        crisis_box()
                        if p["crisis_plan"]:
                            st.markdown(f"**Crisis plan on file:** {p['crisis_plan']}")

    # ---- Safe zones & map
    with tabs[2]:
        p = pick_profile("sz_p")
        if p:
            with st.form("sz_form"):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                zl = c1.text_input("Label (Home, School…)")
                zlat = c2.number_input("Latitude", value=34.05, format="%.6f", key="z_lat")
                zlon = c3.number_input("Longitude", value=-118.25, format="%.6f", key="z_lon")
                zr = c4.number_input("Radius (m)", 25, 5000, 150, step=25)
                if st.form_submit_button("➕ Add safe zone"):
                    if zl.strip():
                        with db() as c:
                            c.execute("INSERT INTO safe_zones (profile_id,label,lat,lon,radius_m) VALUES (?,?,?,?,?)", (p["id"], zl, zlat, zlon, zr))
                        st.rerun()
                    else:
                        st.error("Give the zone a label.")
            with db() as c:
                zones = [dict(r) for r in c.execute("SELECT * FROM safe_zones WHERE profile_id=?", (p["id"],)).fetchall()]
                cks = [dict(r) for r in c.execute("SELECT * FROM checkins WHERE profile_id=? AND lat IS NOT NULL ORDER BY id DESC LIMIT 20", (p["id"],)).fetchall()]
            if zones:
                st.dataframe(pd.DataFrame(zones)[["id", "label", "lat", "lon", "radius_m"]], use_container_width=True, hide_index=True)
                zdel = st.selectbox("Remove a zone", [None] + [z["id"] for z in zones], format_func=lambda x: "—" if x is None else f"#{x}")
                if zdel and st.button("🗑️ Remove selected zone"):
                    with db() as c:
                        c.execute("DELETE FROM safe_zones WHERE id=?", (zdel,))
                    st.rerun()
            if HAS_MAP and (zones or cks):
                ctr = [cks[0]["lat"], cks[0]["lon"]] if cks else [zones[0]["lat"], zones[0]["lon"]]
                m = folium.Map(location=ctr, zoom_start=14, tiles="CartoDB dark_matter")
                for z in zones:
                    folium.Circle([z["lat"], z["lon"]], radius=z["radius_m"], color="#00c9a7", fill=True, fill_opacity=.15, tooltip=z["label"]).add_to(m)
                for i, k in enumerate(cks):
                    folium.CircleMarker([k["lat"], k["lon"]], radius=8 if i == 0 else 4, color="#f0b429" if i else "#ff6b6b", fill=True,
                                        tooltip=f"{k['ts']} · {k['status']}").add_to(m)
                st_folium(m, width=800, height=480, returned_objects=[])
                st.caption("Green circles = safe zones · red dot = latest check-in · gold dots = earlier check-ins")
            elif not HAS_MAP:
                st.error("Maps need `folium` and `streamlit-folium`.")

    # ---- Mood trends
    with tabs[3]:
        p = pick_profile("mt_p")
        if p:
            with db() as c:
                rows = [dict(r) for r in c.execute("SELECT ts,mood,status,zone_status,note FROM checkins WHERE profile_id=? ORDER BY id", (p["id"],)).fetchall()]
            if rows:
                df = pd.DataFrame(rows)
                st.line_chart(df.set_index("ts")["mood"])
                recent = df["mood"].tail(5)
                if len(recent) >= 3 and recent.mean() <= 2:
                    st.warning("Mood has been low across recent check-ins. Consider reaching out personally and contacting their clinician or counsellor.")
                st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
                st.download_button("📥 Export check-ins (CSV)", df.to_csv(index=False).encode(), "checkins.csv", "text/csv")
            else:
                st.caption("No check-ins recorded yet.")

    # ---- Wellness screen
    with tabs[4]:
        st.markdown("Over the **last 2 weeks**, how often has the person been bothered by the following? "
                    "(PHQ-2 and GAD-2 quick screens — for adults and teens; not diagnostic.)")
        opts = {"Not at all": 0, "Several days": 1, "More than half the days": 2, "Nearly every day": 3}
        qs = ["Little interest or pleasure in doing things", "Feeling down, depressed, or hopeless",
              "Feeling nervous, anxious, or on edge", "Not being able to stop or control worrying"]
        ans = [opts[st.radio(q, list(opts), horizontal=True, key=f"ws{i}")] for i, q in enumerate(qs)]
        selfharm = st.checkbox("Has talked about wanting to die, or about hurting themselves")
        phq, gad = ans[0] + ans[1], ans[2] + ans[3]
        c1, c2 = st.columns(2)
        c1.metric("PHQ-2 (depression) score", f"{phq} / 6", "Positive screen (≥3)" if phq >= 3 else "Below cutoff", delta_color="inverse" if phq >= 3 else "off")
        c2.metric("GAD-2 (anxiety) score", f"{gad} / 6", "Positive screen (≥3)" if gad >= 3 else "Below cutoff", delta_color="inverse" if gad >= 3 else "off")
        if selfharm:
            st.error("Take this seriously. Stay with the person, remove access to means of harm if you safely can, and call or text 988 (US) or 911 if there is immediate danger.")
            crisis_box()
        elif phq >= 3 or gad >= 3:
            st.warning("Positive screen. Encourage a visit with a doctor or mental-health professional; this tool cannot diagnose.")
        else:
            st.success("Below the screening cutoffs. Keep checking in and re-screen if things change.")
        st.caption("For children under 12, ask a pediatrician or school counsellor for age-appropriate screening tools.")

    # ---- Emergency card
    with tabs[5]:
        p = pick_profile("ec_p")
        if p:
            if not HAS_PDF:
                pdf_unavailable()
            else:
                pdf = LifeHavenPDF(); pdf.add_page()
                pdf.h1("EMERGENCY INFORMATION CARD", 18); pdf.ln(3)
                for k, v in {"Name": p["name"], "Category": p["category"], "DOB": safe(p["dob"]), "Emergency contact": safe(p["emergency_contact"]),
                             "Medical notes": safe(p["medical_notes"]), "Medications": safe(p["medications"]), "Allergies": safe(p["allergies"]),
                             "Calming / crisis plan": safe(p["crisis_plan"]), "Consent given by": safe(p["consent_by"])}.items():
                    pdf.kv(k, v, 50)
                pdf.ln(3); pdf.para("In an emergency call 911. Suicide & Crisis Lifeline: 988.", 10, "B")
                st.download_button("📥 Download Emergency Card (PDF)", pdf_bytes(pdf), f"{p['name'].replace(' ', '_')}_emergency_card.pdf", "application/pdf")

    with tabs[6]:
        crisis_box()

# ═════════════════════════════════════════════════════════════════════════════
#  6 — PHONE SECURITY
# ═════════════════════════════════════════════════════════════════════════════
elif menu == "🔒 Phone Security":
    section_header("Module 06", "Phone Security: Intruder Checkup & Cleanup",
                   "Answer real questions about the phone → get a real score and exact fix steps for iPhone or Android")
    st.info("A website **cannot scan or clean a phone** — only the phone's own settings and security apps can. This module walks a person (or "
            "caregiver) through the checks that actually find and remove intruders, then gives a step-by-step cleanup playbook.", icon="🛡️")
    tabC, tabP, tabL, tabF, tabG, tabAd = st.tabs(["✅ Guided Checkup", "🧹 Cleanup Playbook", "🔗 Link / Text Checker", "⚡ Performance Check", "🛡️ Phone Guardian", "🚫 Ad Blocking"])

    # key, question (Yes = good), weight, iOS fix, Android fix
    SEC_Q = [
        ("os", "The phone's software is fully up to date", 3,
         "Settings › General › Software Update › install, and turn on Automatic Updates.",
         "Settings › System › Software update (or About phone) › install; enable auto-updates in Play Store."),
        ("lock", "The phone has a 6-digit+ PIN (or passcode) and Face/Touch ID or fingerprint, and nobody else knows it", 3,
         "Settings › Face ID & Passcode › Change Passcode (6-digit or alphanumeric).",
         "Settings › Security › Screen lock › PIN (6+ digits) and set fingerprint/face."),
        ("apps", "Every installed app is recognised — nothing unknown or oddly named", 3,
         "Settings › General › iPhone Storage: scroll the full app list; delete anything you did not install.",
         "Settings › Apps › See all apps; also check hidden/system apps. Uninstall unknown ones. Play Store › profile › Play Protect › Scan."),
        ("admin", "No unknown profiles, device-admin apps or accessibility services (stalkerware often hides here)", 3,
         "Settings › General › VPN & Device Management: delete unknown profiles. Settings › Privacy & Security › Safety Check (iOS 16+).",
         "Settings › Security › Device admin apps (path varies) and Settings › Accessibility › Installed apps: disable/uninstall anything unfamiliar."),
        ("acct", "Apple ID / Google account shows only my own devices, and two-factor sign-in is on", 3,
         "Settings › [your name]: review the device list, remove unknown devices; turn on two-factor authentication.",
         "myaccount.google.com › Security › Your devices: sign out unknown devices; turn on 2-Step Verification."),
        ("pw", "My email password is unique (not reused) and not known to anyone else", 3,
         "Change it now, then use iCloud Keychain / a password manager.",
         "Change it now, then use Google Password Manager / a password manager."),
        ("sim", "The mobile-carrier account has a PIN/passcode (protects against SIM-swap)", 2,
         "Call or log in to your carrier and set an account PIN and port-out lock.",
         "Call or log in to your carrier and set an account PIN and port-out lock."),
        ("loc", "I reviewed who can see my location (Find My, Google Family, Life360, shared links)", 2,
         "Settings › Privacy & Security › Location Services › Share My Location; Find My › People: remove anyone unexpected.",
         "Google Maps › profile › Location sharing: stop unknown shares; Settings › Location › App permissions."),
        ("store", "Apps only come from the official App Store / Google Play (no sideloaded APKs)", 2,
         "Nothing to sideload on stock iOS; delete any unfamiliar TestFlight/enterprise apps.",
         "Settings › Apps › Special access › Install unknown apps: turn OFF for all apps."),
        ("clicks", "I have not tapped a link or entered a code from an unexpected text/call recently", 2,
         "If you did: change affected passwords, call the bank, and run the Cleanup Playbook.",
         "If you did: change affected passwords, call the bank, and run the Cleanup Playbook."),
        ("odd", "Battery, heat and data use look normal (no unexplained drain or spikes)", 2,
         "Settings › Battery and Settings › Cellular: check which apps use the most.",
         "Settings › Battery and Settings › Network › Data usage: check which apps use the most."),
        ("bt", "I know about every Bluetooth device paired and have not received unknown-tracker alerts", 1,
         "Settings › Bluetooth: remove unknown devices; take 'AirTag found moving with you' alerts seriously.",
         "Settings › Connected devices: remove unknown devices; run an unknown-tracker scan in Safety & emergency."),
        ("ads", "Ad & tracker blocking is on (filtering Private DNS, a privacy browser, or a trusted blocker)", 1,
         "Install a Safari content blocker (AdGuard, 1Blocker, Wipr) and enable it in Settings › Apps › Safari › Extensions; optional: provider DNS profile.",
         "Settings › Network & internet › Private DNS › dns.adguard-dns.com; or use Firefox + uBlock Origin / Brave."),
        ("bak", "Backups are on, so the phone can be safely reset if needed", 1,
         "Settings › [name] › iCloud › iCloud Backup: On.",
         "Settings › Google › Backup: On."),
    ]
    SCORE = {"Yes": 1.0, "Not sure": 0.4, "No": 0.0}

    with tabC:
        c1, c2 = st.columns([2, 1])
        client = c1.text_input("Client name", placeholder="e.g. Mary Johnson")
        platform = c2.selectbox("Phone type", ["iPhone (iOS)", "Android"])
        ios = platform.startswith("iPhone")
        answers = {}
        for key, q, w, fi, fa in SEC_Q:
            answers[key] = st.radio(q, list(SCORE), index=1, horizontal=True, key=f"sq_{key}")
        total = sum(w for _, _, w, _, _ in SEC_Q)
        got = sum(SCORE[answers[k]] * w for k, _, w, _, _ in SEC_Q)
        pct = int(round(got / total * 100))
        color = "#00ffe0" if pct >= 80 else "#f0b429" if pct >= 60 else "#ff6b6b"
        label = "Good" if pct >= 80 else "Needs attention" if pct >= 60 else "High risk — act today"
        st.session_state["phone_checkup_pct"] = pct
        st.markdown(f"""<div class="card-teal"><div style="font-size:.8rem;color:var(--muted)">Security checkup — {safe(client,'Client')} · {platform} · {now_str()}</div>
          <div style="font-size:3rem;font-weight:900;color:{color};font-family:'Cormorant Garamond',serif">{pct}% · {label}</div></div>""", unsafe_allow_html=True)
        fixes = [(q, w, fi if ios else fa, answers[k]) for k, q, w, fi, fa in SEC_Q if answers[k] != "Yes"]
        fixes.sort(key=lambda x: -x[1])
        if fixes:
            st.markdown("**🔧 Fix list (highest priority first)**")
            for q, w, f, a in fixes:
                st.markdown(f'<div class="check-item">{"❌" if a == "No" else "❔"} <b>{q}</b><br><span style="color:var(--muted)">➜ {f}</span></div>', unsafe_allow_html=True)
        else:
            st.success("All checks passed. Re-run monthly.")
        if answers["admin"] != "Yes" or answers["apps"] == "No" or answers["odd"] == "No":
            st.warning("Possible stalkerware/intruder signs. Read the **Cleanup Playbook** tab before removing anything — "
                       "if the person controlling the phone could be dangerous, plan your safety first.")
        if HAS_PDF:
            p = LifeHavenPDF(); p.add_page()
            p.h1("Phone Security Checkup Report", 16); p.ln(2)
            p.kv("Client", safe(client, "Client")); p.kv("Phone", platform); p.kv("Date", now_str()); p.kv("Score", f"{pct}% — {label}"); p.ln(3)
            p.section("FIX LIST")
            for q, w, f, a in fixes:
                p.para(f"[{a}] {q}", 10, "B"); p.para("   -> " + f, 10)
            if not fixes: p.para("All checks passed.")
            p.ln(3); p.para("Real scam/fraud reports: reportfraud.ftc.gov or 1-877-382-4357.", 9, "I")
            st.download_button("📥 Download checkup report (PDF)", pdf_bytes(p), "phone_security_report.pdf", "application/pdf")

    with tabP:
        st.markdown("""
**Before you start — safety first.** If someone you fear (a partner, ex, or family member) may be monitoring this phone, removing their access can alert them.
Use a *different, safe device* to get help: National Domestic Violence Hotline **1-800-799-7233** (or text START to 88788). Save evidence (screenshots) before deleting anything.

**Step 1 — Contain**
1. Turn on Airplane mode while you work; it cuts remote control and live location sharing.
2. From a *different, trusted device*, change your email, Apple ID / Google account, and bank passwords. Turn on two-factor sign-in.
3. Sign out all other devices (Apple ID › device list · myaccount.google.com › Security › Your devices).

**Step 2 — Find the intruder**
- *iPhone:* Settings › Privacy & Security › **Safety Check** (iOS 16+) lets you stop sharing with everyone at once. Then Settings › General › **VPN & Device Management** and delete unknown profiles. Review iPhone Storage for unknown apps.
- *Android:* Play Store › profile › **Play Protect › Scan**. Review **Device admin apps**, **Accessibility** services, **Notification access**, and **Install unknown apps**; remove anything unfamiliar. Menus differ by brand — search Settings for these names.

**Step 3 — Clean**
1. Uninstall unknown apps. Install a reputable mobile security app from the official store and run a full scan.
2. Review app permissions (location, camera, mic, SMS) and revoke what is not needed.
3. Check forwarding: email rules, call forwarding (dial *#21# to check), and carrier account for added lines or devices.

**Step 4 — If it keeps happening: factory reset**
1. Back up photos and contacts only (not apps or settings).
2. iPhone: Settings › General › Transfer or Reset iPhone › **Erase All Content and Settings**. Android: Settings › System › Reset options › **Erase all data**.
3. Set the phone up as **new** (do not restore a full backup, which could bring the intruder back), then sign in and re-add apps one by one from the official store.

**Step 5 — Report & recover**
- Report fraud: reportfraud.ftc.gov · 1-877-382-4357. Identity theft recovery: identitytheft.gov.
- Call your bank and place a fraud alert/credit freeze if financial info was exposed.
- Tell the carrier to add an account PIN and port-out protection.
""")

    with tabL:
        st.markdown("Paste a suspicious **link** or **text message**. This runs red-flag rules on your device's server — it does not open the link.")
        txt = st.text_area("Link or message", height=120)
        if st.button("🔎 Check"):
            flags, t = [], txt.lower()
            urls = re.findall(r"(?:https?://|www\.)[^\s<>\"']+", txt, flags=re.I)
            SHORT = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "cutt.ly", "rb.gy", "buff.ly", "shorturl.at"}
            BAD_TLD = (".zip", ".mov", ".top", ".xyz", ".click", ".tk", ".gq", ".cf", ".ml", ".ga", ".country", ".support")
            for u in urls:
                pu = urlparse(u if "://" in u else "http://" + u)
                host = (pu.hostname or "").lower()
                if host in SHORT: flags.append(f"Shortened link ({host}) hides the real destination")
                if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host): flags.append("Link uses a raw IP address")
                if "@" in pu.netloc: flags.append("Link contains '@' — often used to disguise the real site")
                if host.startswith("xn--") or ".xn--" in host: flags.append("Look-alike (punycode) characters in domain")
                if host.endswith(BAD_TLD): flags.append(f"Domain ending {host.rsplit('.',1)[-1]!r} is frequently abused")
                if host.count("-") >= 3 or host.count(".") >= 4: flags.append("Unusually long/complex domain")
                if pu.scheme == "http": flags.append("Link is not encrypted (http)")
                for brand in ("paypal", "apple", "amazon", "microsoft", "bank", "medicare", "irs", "usps", "fedex", "netflix"):
                    if brand in host and not re.search(rf"(^|\.){brand}\.(com|gov)$", host):
                        flags.append(f"Domain mentions '{brand}' but is not the official site")
                        break
            WORDS = ["urgent", "immediately", "act now", "verify your", "account suspended", "locked", "gift card", "wire transfer",
                     "bitcoin", "social security", "medicare", "refund", "you have won", "winner", "one-time code", "otp", "password",
                     "final notice", "arrest", "do not tell", "grandson", "grandchild in jail", "bail"]
            hit = [w for w in WORDS if w in t]
            if hit: flags.append("Pressure/scam wording: " + ", ".join(hit[:6]))
            if re.search(r"\b\d{6}\b", t) and ("code" in t or "otp" in t):
                flags.append("Asks for or mentions a 6-digit code — never share these")
            if not txt.strip():
                st.warning("Paste something first.")
            elif len(flags) >= 3:
                st.error("🚨 HIGH RISK — very likely a scam. Do not click, reply, or share codes. Delete it and report it (forward texts to 7726).")
            elif flags:
                st.warning("⚠️ Suspicious. Verify by contacting the company using the number on your card or their official site.")
            else:
                st.success("No obvious red flags — but scams can look clean. When in doubt, don't click; go to the official site yourself.")
            for f in flags:
                st.markdown(f'<div class="check-item">⚑ {f}</div>', unsafe_allow_html=True)

    with tabF:
        st.markdown("Measures how **smooth, fast and healthy** the phone is, plus basic safety hygiene. Open this app on the **phone itself**, "
                    "tap the button and leave the screen alone for about 12 seconds.")
        pf_person = st.text_input("Phone owner / device name (to track results over time)", key="pf_person", placeholder="e.g. Mary's Samsung")
        compP = get_component("phone")
        pres = compP(key="phone_c", default=None) if compP else None
        if compP is None:
            st.warning("The browser test component could not be created on this server.")
        if pres:
            an = analyze_phone(pres)
            guided = st.session_state.get("phone_checkup_pct")
            c1, c2, c3 = st.columns(3)
            c1.metric("Performance score", f"{an['perf']}/100" if an["perf"] is not None else "—")
            c2.metric("Safety hygiene checks", f"{an['safety']}%" if an["safety"] is not None else "—")
            c3.metric("Guided checkup (tab 1)", f"{guided}%" if guided is not None else "not done")
            nm, mj, rel, _, _ = an["os"]
            st.caption(f"Detected: {nm} {mj if mj is not None else '?'}{'' if rel else ' (browser may hide the exact version)'} · "
                       f"{pres.get('cores') or '?'} CPU cores · screen {pres.get('screen',{}).get('w','?')}×{pres.get('screen',{}).get('h','?')}"
                       + (f" · GPU {pres['gpu'][:40]}" if pres.get("gpu") else ""))
            if an["parts"]:
                st.dataframe(pd.DataFrame([(a, b, c, "✅ Good" if c >= 80 else "⚠️ Fair" if c >= 55 else "🔶 Slow") for a, b, c in an["parts"]],
                                          columns=["Test", "Result", "Score", "Status"]), use_container_width=True, hide_index=True)
                st.bar_chart(pd.DataFrame({"Score": [x[2] for x in an["parts"]]}, index=[x[0] for x in an["parts"]]))
            st.markdown("**🛡️ Safety hygiene**")
            for ic, a, b in an["hygiene"]:
                st.markdown(f'<div class="check-item">{ic} <b>{a}</b>' + (f'<br><span style="color:var(--muted)">{b}</span>' if b else "") + "</div>", unsafe_allow_html=True)
            bt, nt, stg = pres.get("battery"), pres.get("net") or {}, pres.get("storage")
            extras = []
            if bt: extras.append(f"🔋 Battery {bt['level']}% ({'charging' if bt['charging'] else 'on battery'})")
            if nt.get("type"): extras.append(f"📶 Network {nt['type']} · ~{nt.get('downlink','?')} Mbps · {nt.get('rtt','?')} ms round trip")
            if stg: extras.append(f"💾 This browser may use up to {stg['quota_mb']:,} MB; the app is using {stg['usage_mb']} MB")
            if extras:
                st.markdown("**Device readings**"); [st.markdown("- " + x) for x in extras]
            st.markdown("**🔧 What to do next**")
            for t in an["tips"]:
                st.markdown(f'<div class="check-item">• {t}</div>', unsafe_allow_html=True)
            if st.button("💾 Save this result", key="save_phone"):
                with db() as c:
                    c.execute("INSERT INTO assessments (ts,name,kind,data) VALUES (?,?,?,?)",
                              (now_str(), pf_person.strip() or "Unnamed phone", "phone_perf",
                               json.dumps({"perf": an["perf"], "safety": an["safety"], "os": list(an["os"][:2]), "cpu_ms": pres.get("cpu_ms"),
                                           "fps": (pres.get("fps") or {}).get("fps"), "latency": (pres.get("latency") or {}).get("median")})))
                st.success("Saved.")
            with st.expander("Raw readings"):
                st.json({k: v for k, v in pres.items() if k != "ua"})
        with db() as c:
            hist = [dict(r) for r in c.execute("SELECT ts,name,data FROM assessments WHERE kind='phone_perf' ORDER BY id").fetchall()]
        mine = [h for h in hist if h["name"].lower() == (pf_person.strip() or "unnamed phone").lower()]
        if len(mine) >= 2:
            st.markdown("**Trend for this phone**")
            tr = pd.DataFrame([{"ts": h["ts"], **json.loads(h["data"])} for h in mine]).set_index("ts")
            st.line_chart(tr[["perf", "safety"]])

    with tabG:
        st.markdown("### 🛡️ Phone Guardian — deeper scan that runs on the device")
        st.markdown("A website cannot see your other apps, so the **Guardian** is a small Python tool you run *on the phone or computer*. "
                    "It reports sideloaded apps, apps that read your screen or notifications, device-admin entries, debugging switches, "
                    "patch age, memory, battery temperature, storage, network speed — and flags **new apps since your last scan**.")
        zbytes = zip_guardian()
        if zbytes:
            st.download_button("📥 Download Phone Guardian (zip)", zbytes, "peace_unity_phone_guardian.zip", "application/zip")
        else:
            st.warning("Add the `phone_guardian` folder (from the zip I gave you) to your GitHub repo next to `app.py` to enable the download button here.")
        st.markdown("""
**Android (best support):** install **Termux** from **F-Droid** (the Play Store copy is outdated), then:
```
pkg update && pkg install python
unzip peace_unity_phone_guardian.zip && cd peace_unity_phone_guardian
python guardian.py --selftest      # should print PASS lines
python guardian.py                 # run the scan
python server.py                   # optional dashboard at http://127.0.0.1:8765
```
**Windows / macOS / Linux:** install Python 3, then `python guardian.py` (or `python3`). 
**iPhone / iPad:** Apple does not allow any app to inspect other apps. Use Settings → Privacy & Security → **Safety Check** and **App Privacy Report**, plus the Guided Checkup tab.

When the scan finishes it saves `latest-report.json`. **Upload it below** to view it here.
""")
        up = st.file_uploader("Upload latest-report.json from the Guardian", type=["json"], key="guardian_up")
        if up is not None:
            try:
                raw = up.getvalue()
                if len(raw) > 2_000_000: raise ValueError("File too large")
                g = json.loads(raw.decode("utf-8", "replace"))
                if not isinstance(g, dict) or not isinstance(g.get("findings"), list) or "device" not in g: raise ValueError("Not a Guardian report")
                c1, c2, c3 = st.columns(3)
                c1.metric("Guardian score", f"{g.get('score','?')}/100"); c2.metric("Grade", str(g.get("grade", "?"))[:30])
                c3.metric("Platform", str((g.get("device") or {}).get("platform", "?"))[:20])
                st.caption(f"Scan time: {str((g.get('device') or {}).get('timestamp_utc',''))[:19]} · version {str((g.get('device') or {}).get('version',''))[:10]}")
                order = {"critical": 0, "warning": 1, "review": 2, "limited": 3, "info": 4}
                icon = {"critical": "🚨", "warning": "🔶", "review": "⚠️", "limited": "ℹ️", "info": "✅"}
                fl = [x for x in g["findings"] if isinstance(x, dict)]
                fl.sort(key=lambda x: order.get(str(x.get("level")), 5))
                show_info = st.checkbox("Show informational items too", value=False)
                for x in fl:
                    lv = str(x.get("level", "info"))
                    if lv == "info" and not show_info: continue
                    with st.expander(f"{icon.get(lv, '•')} {str(x.get('title',''))[:120]}  ·  {lv}"):
                        st.text(str(x.get("detail", ""))[:3000])
                        if x.get("action"): st.markdown("**Next step:** " + str(x.get("action"))[:500])
                if st.button("💾 Save Guardian result", key="save_guard"):
                    with db() as c:
                        c.execute("INSERT INTO assessments (ts,name,kind,data) VALUES (?,?,?,?)",
                                  (now_str(), (pf_person.strip() or "Unnamed phone"), "guardian_report",
                                   json.dumps({"score": g.get("score"), "grade": g.get("grade"), "counts": g.get("counts")})))
                    st.success("Saved.")
            except Exception as e:
                st.error(f"Could not read that file: {e}")
        st.markdown("**Link / message checker:** the same offline engine runs in the *Link / Text Checker* tab and in `python guardian.py --check-url`.")

    with tabAd:
        st.markdown("### 🚫 Ads & trackers — block as many as is realistically possible")
        st.markdown("Open this app **on the phone** and run the test. It tells you whether anything on this phone/network is blocking ads and trackers right now.")
        compAd = get_component("adtest")
        ares = compAd(key="adtest_c", default=None) if compAd else None
        if compAd is None:
            st.warning("The ad-blocking test component could not be created on this server.")
        if ares:
            stt = ares.get("status")
            c1, c2, c3 = st.columns(3)
            c1.metric("Ads/trackers blocked", f"{ares['percent']}%" if stt != "inconclusive" else "—")
            c2.metric("Blocked", f"{ares['blocked']} of {ares['total']}"); c3.metric("Normal sites reachable", "yes" if ares.get("control_ok") else "no")
            if stt == "strong": st.success("✅ Strong blocking: most ad and tracker addresses are being stopped.")
            elif stt == "partial": st.warning("⚠️ Partial blocking: some ads/trackers get through. Add a filtering DNS or a browser blocker (steps below).")
            elif stt == "none": st.error("🔶 No blocking detected. Ads and trackers load freely. Use the steps below.")
            else: st.info("Inconclusive — normal sites did not load, so the result can't be trusted. Check your connection and run again.")
            if ares.get("details"):
                st.dataframe(pd.DataFrame([(x["d"], "🚫 blocked" if x["state"] == "blocked" else "📢 loaded") for x in ares["details"]], columns=["Address tested", "Result"]),
                             use_container_width=True, hide_index=True)
        st.markdown("""
#### What actually works (best first)
**1. Filtering Private DNS — Android, system-wide, no app needed**
Settings → Network & internet → **Private DNS** → *Private DNS provider hostname* → type `dns.adguard-dns.com` → Save.
This stops many ad/tracker domains in browsers and apps. For your own allow/block lists use a free **NextDNS** account (hostname looks like `abc123.dns.nextdns.io`).

**2. A browser that blocks**
- **Firefox for Android** → Menu → Add-ons → install **uBlock Origin** (best all-round blocker).
- **Brave** blocks ads and trackers by default. **Samsung Internet** offers ad-blocker add-ons. Chrome on Android cannot use extensions.

**3. iPhone / iPad**
- Install a Safari content blocker (e.g. **AdGuard**, **1Blocker**, **Wipr**), then enable it: Settings → Apps → Safari → **Extensions** (older iOS: Settings → Safari → Content Blockers).
- For system-wide DNS blocking, get the encrypted-DNS profile **from the provider's own website** (AdGuard DNS or NextDNS) and install it in Settings → General → VPN & Device Management.

**4. Computer**
Install **uBlock Origin** in Firefox/Chrome-family browsers; for the whole home network use a router-level DNS filter (AdGuard Home or Pi-hole).

#### Stop pop-ups, notification spam and ads on top of other apps
- **Browser notification spam:** Chrome → Settings → Notifications (or Site settings → Notifications) → remove any site you don't know, and block "Pop-ups and redirects".
- **Ads appearing over other apps or on the lock screen** usually mean adware: Settings → Apps → *Special app access* → **Display over other apps** → turn off anything you don't need, then uninstall unfamiliar apps. Run *Play Protect → Scan*.
- The **Phone Guardian** scan lists apps allowed to draw over other apps and shows whether Private DNS is a filtering provider.

#### Honest limits and safety
- **No tool blocks every ad.** YouTube video ads and ads built into an app's own servers usually can't be blocked by DNS. Blocking can break some sites, logins or apps — if something stops working, turn the blocker off for that site.
- A DNS provider sees the *names* of sites you visit, so pick a reputable one and read its privacy policy.
- **Avoid random free "ad blocker", "cleaner", "booster" or free-VPN apps.** They are a common source of adware and spyware. Stick to well-known options such as AdGuard, NextDNS, uBlock Origin or Brave.
""")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("**📱 Common scams targeting seniors**")
    s1, s2, s3 = st.columns(3)
    s1.markdown('<div class="card"><b style="color:var(--teal2)">👵 Grandparent scam</b><br><span style="color:var(--muted);font-size:.85rem">Caller claims a grandchild is in trouble. Hang up and call the family member directly.</span></div>', unsafe_allow_html=True)
    s2.markdown('<div class="card"><b style="color:var(--teal2)">💊 Medicare scam</b><br><span style="color:var(--muted);font-size:.85rem">Real Medicare never cold-calls for your card number.</span></div>', unsafe_allow_html=True)
    s3.markdown('<div class="card"><b style="color:var(--teal2)">🏦 Bank fraud</b><br><span style="color:var(--muted);font-size:.85rem">"Account locked" texts. Never click — call the number on your card.</span></div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
#  7 — TRANSLATOR
# ═════════════════════════════════════════════════════════════════════════════
elif menu == "🌐 Translator":
    section_header("Module 07", "Care Translator", "Offline care phrasebook in 5 languages · optional live translation and voice")
    st.info("For consent, diagnoses, medication changes or legal matters, use a **qualified medical interpreter**, not a translation tool.", icon="⚕️")
    tabPh, tabFree = st.tabs(["📖 Care Phrasebook (offline)", "✍️ Free Text (online)"])

    with tabPh:
        target = st.selectbox("Translate into", [l for l in LANGS if l != "English"])
        code = LANGS[target]
        rows = [{"English": en, target: tr[code]} for en, tr in PHRASES]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        pick = st.selectbox("Speak a phrase", [en for en, _ in PHRASES])
        phrase = dict(PHRASES)[pick][code]
        st.markdown(f'<div class="card-teal" style="font-size:1.6rem;text-align:center">{phrase}</div>', unsafe_allow_html=True)
        aud = voice(phrase, code)
        if aud:
            st.audio(aud, format="audio/mp3")
        elif not (HAS_TTS and EXTERNAL_TTS):
            st.caption("🔇 Voice is off. Set `ENABLE_EXTERNAL_TTS=true` (and install `gTTS`) to enable it. Text is sent to Google when enabled.")
        else:
            st.caption("Voice not available for this language right now.")

    with tabFree:
        if not (HAS_TRANSLATOR and EXTERNAL_TRANSLATE):
            st.warning("Live translation is off. Add `deep-translator` to requirements.txt and set `ENABLE_EXTERNAL_TRANSLATE=true`. "
                       "Text you translate is sent to Google, so never enter private medical or identifying details.")
        tlang = st.selectbox("Translate into", list(FREE_LANGS))
        src_text = st.text_area("Text to translate (no private health information)", height=120)
        if st.button("🌐 Translate"):
            if not src_text.strip():
                st.warning("Enter some text.")
            else:
                out = translate_text(src_text.strip(), FREE_LANGS[tlang])
                if out:
                    st.markdown(f'<div class="card-teal" style="font-size:1.2rem">{out}</div>', unsafe_allow_html=True)
                    aud = voice(out, FREE_LANGS[tlang])
                    if aud: st.audio(aud, format="audio/mp3")
                else:
                    st.error("Translation unavailable (feature off, offline, or language not supported).")

# ═════════════════════════════════════════════════════════════════════════════
#  6b — VITALS LAB (phone sensors)
# ═════════════════════════════════════════════════════════════════════════════
elif menu == "🩺 Vitals Lab (Phone Sensors)":
    section_header("Module 06b", "Vitals Lab — Phone Sensors",
                   "Camera heart rate · phone-sensor balance · breathing pacer · vitals log with early warning · wearable import")
    st.info("Experimental screening tools to start from — **not medical devices**. Use a validated cuff for blood pressure and a "
            "fingertip oximeter for oxygen. Anything worrying, or any symptoms, needs a clinician.", icon="🧪")
    vperson = st.text_input("Person's name (used for the log)", key="vl_person", placeholder="e.g. Mary Johnson")
    vt = st.tabs(["❤️ Camera Heart Rate", "🧍 Phone Balance", "🌬️ Breathing Pacer", "📈 Log & Early Warning", "⌚ Wearable Import"])

    with vt[0]:
        st.markdown("**How:** open this page on a **phone**, tap Start, cover the rear camera **and** flash with a fingertip, stay still for 30 s. "
                    "Sit and rest 5 minutes first for a true resting heart rate.")
        comp = get_component("ppg")
        res = comp(key="ppg_c", default=None) if comp else None
        if comp is None:
            st.warning("The camera component could not be created on this server. You can still type a heart rate into the log.")
        if res:
            if res.get("ok"):
                st.session_state["latest_hr"] = res["bpm"]
                c1, c2, c3 = st.columns(3)
                c1.metric("Heart rate", f"{res['bpm']} bpm"); c2.metric("HRV (rough)", f"{res['hrv']} ms" if res.get("hrv") is not None else "—")
                c3.metric("Breathing (rough)", f"{res['resp']}/min" if res.get("resp") is not None else "—")
                st.success(hr_text(res["bpm"]) + f" · signal quality {int(res['quality']*100)}%")
                st.caption("Heart rate is now pre-filled in the Total Body Assessment form. HRV and breathing are rough camera estimates for personal trends only.")
                if st.button("💾 Save to vitals log", key="save_ppg"):
                    log_vital(vperson, "hr", res["bpm"], "bpm", "camera")
                    if res.get("hrv") is not None: log_vital(vperson, "hrv", res["hrv"], "ms", "camera, rough")
                    if res.get("resp") is not None: log_vital(vperson, "resp", res["resp"], "/min", "camera, rough")
                    st.success("Saved.")
            else:
                st.warning(res.get("reason", "Reading failed. Try again."))
        st.markdown("**Tips:** light pressure (don't squeeze), warm hands, no talking, steady hand resting on a table, avoid direct sunlight on the lens.")

    with vt[1]:
        st.markdown("**How:** hold the phone flat against your chest, stand next to a counter with a helper beside you, tap Start. "
                    "Try *feet together*, then *tandem*, then *eyes closed*. Lower tilt and higher score = steadier.")
        comp2 = get_component("sway")
        sres = comp2(key="sway_c", default=None) if comp2 else None
        if comp2 is None:
            st.warning("The motion-sensor component could not be created on this server.")
        if sres:
            if sres.get("ok"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Average trunk tilt", f"{sres['rms']}°"); c2.metric("Sway speed", f"{sres['path']}°/s"); c3.metric("Stability score", f"{sres['score']}/100")
                (st.success if sres["label"] == "Steady" else st.warning)(f"{sres['label']} — {sres.get('mode','')}")
                st.caption("Provisional thresholds (steady ≤0.8°, moderate ≤1.8°). Phone placement matters, so compare the same person under the same set-up over time.")
                if st.button("💾 Save balance result", key="save_sway"):
                    log_vital(vperson, "sway_deg", sres["rms"], "deg", sres.get("mode", ""))
                    st.success("Saved.")
            else:
                st.warning(sres.get("reason", "Test failed. Try again."))
        st.caption("If your phone says motion sensors are unavailable (older browsers, some desktops), use the stopwatch tests in the Body Assessment instead.")

    with vt[2]:
        import streamlit.components.v1 as components
        st.markdown("Slow breathing calms the nervous system and can lower stress. Pick a pattern, press Start and follow the circle.")
        components.html(PACER_HTML, height=430)

    with vt[3]:
        with st.form("vital_form"):
            st.markdown("**Add readings** (leave 0 to skip)")
            c1, c2, c3, c4 = st.columns(4)
            vhr = c1.number_input("Resting HR (bpm)", 0, 220, 0)
            vtemp = c2.number_input("Temperature", 0.0, 110.0, 0.0, step=0.1)
            tunit = c3.selectbox("Temp unit", ["°F", "°C"])
            vspo2 = c4.number_input("Oxygen SpO₂ (%)", 0, 100, 0)
            c1, c2, c3, c4 = st.columns(4)
            vsys = c1.number_input("BP systolic", 0, 260, 0)
            vdia = c2.number_input("BP diastolic", 0, 160, 0)
            vrr = c3.number_input("Breaths/min", 0, 60, 0)
            vwt = c4.number_input("Weight (kg)", 0.0, 400.0, 0.0, step=0.1)
            vnote = st.text_input("Note")
            if st.form_submit_button("➕ Add to log", use_container_width=True):
                if not vperson.strip():
                    st.error("Enter the person's name above first.")
                else:
                    if vhr: log_vital(vperson, "hr", vhr, "bpm", vnote)
                    if vtemp: log_vital(vperson, "temp_c", f_to_c(vtemp) if tunit == "°F" else vtemp, "C", vnote)
                    if vspo2: log_vital(vperson, "spo2", vspo2, "%", vnote)
                    if vsys: log_vital(vperson, "bp_sys", vsys, "mmHg", vnote)
                    if vdia: log_vital(vperson, "bp_dia", vdia, "mmHg", vnote)
                    if vrr: log_vital(vperson, "resp", vrr, "/min", vnote)
                    if vwt: log_vital(vperson, "weight_kg", vwt, "kg", vnote)
                    st.success("Added."); st.rerun()
        with db() as c:
            allrows = pd.read_sql_query("SELECT ts,person,kind,value,unit,note FROM vitals_log ORDER BY id", c)
        if vperson.strip():
            sub = allrows[allrows["person"].str.lower() == vperson.strip().lower()]
        else:
            sub = allrows.iloc[0:0]
        if sub.empty:
            st.caption("No entries for this name yet.")
        else:
            flags = early_warning(sub)
            if flags:
                st.markdown("**🔔 Early-warning flags (compared with this person's own recent baseline)**")
                for ic, t in flags:
                    st.markdown(f'<div class="check-item">{ic} {t}</div>', unsafe_allow_html=True)
                st.caption("These flags are prompts to look closer, not a diagnosis. Persistent flags, or any symptoms, deserve a clinician.")
            else:
                st.success("No early-warning flags from the logged values.")
            piv = sub.pivot_table(index="ts", columns="kind", values="value", aggfunc="last").sort_index()
            st.line_chart(piv)
            st.dataframe(sub.iloc[::-1], use_container_width=True, hide_index=True)
            st.download_button("📥 Export log (CSV)", sub.to_csv(index=False).encode(), "vitals_log.csv", "text/csv")

    with vt[4]:
        st.markdown("Upload a **CSV** exported from a wearable or health app (Fitbit, Garmin, Google Fit, Apple Health via a CSV exporter). "
                    "It needs a time/date column and a heart-rate column.")
        up = st.file_uploader("Heart-rate CSV", type=["csv"])
        if up is not None:
            try:
                dfw = pd.read_csv(up)
                tcol = next((c for c in dfw.columns if any(k in c.lower() for k in ("time", "date", "start"))), None)
                vcol = next((c for c in dfw.columns if any(k in c.lower() for k in ("heart", "bpm", "hr", "value"))), None)
                if tcol is None or vcol is None:
                    st.error("Could not find a time column and a heart-rate column. Rename them to something like 'time' and 'heart_rate'.")
                else:
                    dfw["_t"] = pd.to_datetime(dfw[tcol], errors="coerce", utc=True)
                    dfw["_v"] = pd.to_numeric(dfw[vcol], errors="coerce")
                    dfw = dfw.dropna(subset=["_t", "_v"])
                    dfw = dfw[(dfw["_v"] > 25) & (dfw["_v"] < 230)]
                    if dfw.empty:
                        st.error("No valid heart-rate rows found.")
                    else:
                        dfw["day"] = dfw["_t"].dt.date
                        daily = dfw.groupby("day")["_v"].agg(lowest="min", average="mean", highest="max",
                                                              resting_est=lambda x: x.quantile(0.05)).round(0)
                        st.line_chart(daily[["resting_est", "average"]])
                        st.dataframe(daily, use_container_width=True)
                        st.caption("Resting estimate = the 5th-percentile heart rate of each day. "
                                   "Rising resting HR for several days can be an early sign of illness or overtraining.")
                        if vperson.strip() and st.button("💾 Save daily resting estimates to log"):
                            for d, rrow in daily.iterrows():
                                with db() as c:
                                    c.execute("INSERT INTO vitals_log (ts,person,kind,value,unit,note) VALUES (?,?,?,?,?,?)",
                                              (f"{d} 08:00", vperson.strip(), "hr", float(rrow["resting_est"]), "bpm", "wearable import"))
                            st.success("Saved.")
            except Exception as e:
                st.error(f"Could not read that file: {e}")

# ═════════════════════════════════════════════════════════════════════════════
#  6c — ILLNESS & INFECTION CHECK
# ═════════════════════════════════════════════════════════════════════════════
elif menu == "🦠 Illness & Infection Check":
    section_header("Module 06c", "Illness & Infection Check",
                   "Symptom and vitals triage · when to test, stay home or get care · prevention & facility checklist")
    st.info("Guidance tool only — **not a diagnosis**. If you think it's an emergency, call 911. It does not give medicine doses; ask a pharmacist or clinician.", icon="🩺")
    it = st.tabs(["🤒 Symptom & Vitals Check", "🛡️ Prevention & Staying Home", "🏥 Facility Outbreak Checklist"])

    EM_FLAGS = ["Trouble breathing, or breathing very fast at rest", "Chest pain or pressure", "New confusion, or very hard to wake",
                "Bluish or gray lips/face", "Seizure", "Fainting or passing out", "Stiff neck together with fever"]
    URG_FLAGS = ["Cannot keep fluids down / constant vomiting", "No urine for 8+ hours, very dry mouth, no tears (dehydration)",
                 "Got better, then suddenly got worse"]
    SYMS = ["Fever or chills", "Cough", "Sore throat", "Runny or stuffy nose", "Body aches", "Unusual tiredness", "Headache",
            "Loss of taste or smell", "Nausea or vomiting", "Diarrhea", "Rash", "Wheezing"]
    AGES = ["Infant under 3 months", "Infant 3–11 months", "Child 1–4", "Child 5–17", "Adult 18–64", "Older adult 65+"]
    RISKS = ["Pregnant", "Weakened immune system", "Chronic lung / heart / kidney disease", "Diabetes", "Obesity", "Lives in a care facility"]

    def triage(age, risk, temp_c, spo2, rr, hr, em, urg, syms, days):
        E, U, T = [], [], []
        E += [f"Red flag: {x}" for x in em]
        if spo2 and spo2 < 90: E.append(f"Oxygen {spo2}% is very low")
        if age == "Infant under 3 months" and (temp_c >= 38.0 or "Fever or chills" in syms):
            E.append("Fever in an infant under 3 months needs emergency evaluation now")
        U += [f"Warning sign: {x}" for x in urg]
        if spo2 and 90 <= spo2 <= 93: U.append(f"Oxygen {spo2}% is low")
        if temp_c >= 39.4: U.append(f"High fever ({temp_c:.1f} °C / {c_to_f(temp_c):.1f} °F)")
        if temp_c >= 38.0 and days >= 3: U.append("Fever lasting 3 or more days")
        if age == "Infant 3–11 months" and temp_c >= 38.0: U.append("Fever in an infant 3–11 months")
        if rr and age.startswith(("Adult", "Older")) and rr > 24: U.append(f"Fast breathing ({rr}/min)")
        if hr and hr > 120: U.append(f"Fast resting heart rate ({hr} bpm)")
        if days >= 10: U.append("Symptoms for 10+ days without clear improvement")
        resp_sx = any(x in syms for x in ("Fever or chills", "Cough", "Sore throat", "Body aches", "Unusual tiredness"))
        if resp_sx and (risk or age in ("Older adult 65+", "Infant 3–11 months", "Child 1–4")) and days <= 5 and not (E or U):
            U.append("Higher-risk person with flu/COVID-like symptoms: flu and COVID antivirals work best when started early (first few days) — call a clinician today")
        if syms:
            T.append("Stay home and test for flu and COVID (home test or clinic)")
        return E, U, T

    with it[0]:
        c1, c2 = st.columns(2)
        ipers = c1.text_input("Name", key="ill_name")
        iage = c2.selectbox("Age group", AGES, index=4)
        irisk = st.multiselect("Higher-risk factors", RISKS)
        c1, c2, c3, c4 = st.columns(4)
        itemp = c1.number_input("Temperature (0 = not taken)", 0.0, 110.0, 0.0, step=0.1)
        itu = c2.selectbox("Unit", ["°F", "°C"])
        ispo2 = c3.number_input("Oxygen SpO₂ % (0 = not measured)", 0, 100, 0)
        idays = c4.number_input("Days of symptoms", 0, 60, 1)
        c1, c2 = st.columns(2)
        ihr = c1.number_input("Resting heart rate (0 = skip)", 0, 220, int(st.session_state.get("latest_hr", 0)))
        irr = c2.number_input("Breaths per minute (0 = skip)", 0, 60, 0)
        st.markdown("**Emergency warning signs**")
        iem = [x for x in EM_FLAGS if st.checkbox(x, key=f"em_{x}")]
        st.markdown("**Other warning signs**")
        iurg = [x for x in URG_FLAGS if st.checkbox(x, key=f"urg_{x}")]
        st.markdown("**Symptoms**")
        cols = st.columns(3)
        isyms = [x for i, x in enumerate(SYMS) if cols[i % 3].checkbox(x, key=f"sx_{x}")]
        cols = st.columns(2)
        iexp = cols[0].checkbox("Close contact with someone who is sick")
        ivax = cols[1].selectbox("Flu / COVID vaccines up to date?", ["Not sure", "Yes", "No"])
        if st.button("🔎 Check", use_container_width=True):
            tc = (f_to_c(itemp) if itu == "°F" else itemp) if itemp else 0.0
            if itemp:
                isyms_t = isyms + (["Fever or chills"] if tc >= 38.0 and "Fever or chills" not in isyms else [])
            else:
                isyms_t = isyms
            E, U, T = triage(iage, irisk, tc, ispo2, irr, ihr, iem, iurg, isyms_t, idays)
            if E:
                st.markdown('<div class="card-red"><b>🚨 Get emergency care now — call 911</b></div>', unsafe_allow_html=True)
                for x in E: st.markdown(f"- {x}")
                crisis_box()
            elif U:
                st.warning("⚠️ **Contact a clinician or urgent care today** (or call your doctor's after-hours line).")
                for x in U: st.markdown(f"- {x}")
            elif T:
                st.info("🏠 **Probably manageable at home — but test and stay away from others.**")
                for x in T: st.markdown(f"- {x}")
            else:
                st.success("✅ No symptoms or warning signs entered. Keep up prevention habits (see the next tab).")
            if tc and tc >= 38.0: st.caption(f"Fever = 38.0 °C / 100.4 °F or higher. Entered: {tc:.1f} °C ({c_to_f(tc):.1f} °F).")
            st.markdown("**Home-care basics**")
            st.markdown("- Rest, drink fluids steadily, and recheck temperature, oxygen and breathing twice a day.\n"
                        "- Ask a pharmacist or clinician before giving any medicine. **Never give aspirin to children or teens.**\n"
                        "- Escalate right away if breathing gets harder, lips look blue, confusion appears, or fluids can't be kept down.")
            if iexp: st.markdown("- You were exposed: wear a mask around others, watch for symptoms, and consider testing a few days after exposure.")
            if ivax == "No": st.markdown("- Ask a clinician or pharmacist which flu, COVID and (if eligible) RSV vaccines are right for you.")
            if ipers.strip():
                log_vital(ipers, "symptom_count", len(isyms_t), "count", "illness check")
                if tc: log_vital(ipers, "temp_c", round(tc, 1), "C", "illness check")
                if ispo2: log_vital(ipers, "spo2", ispo2, "%", "illness check")
                if ihr: log_vital(ipers, "hr", ihr, "bpm", "illness check")
                if irr: log_vital(ipers, "resp", irr, "/min", "illness check")
                st.caption("Saved to the vitals log, so trends and early-warning flags are available in the Vitals Lab.")

    with it[1]:
        st.markdown("""
**Everyday protection**
- **Wash hands** with soap for 20 seconds (or use 60%+ alcohol rub) after coughing, bathroom, before eating and before touching your face.
- **Fresh air:** open windows, run fans/HEPA filters, and gather outdoors when you can. Most spread happens indoors.
- **Masks:** a well-fitting mask helps when you're sick, when someone is sick around you, or in crowded indoor spaces during surges — especially for older or higher-risk people.
- **Vaccines:** ask a clinician or pharmacist about this season's **flu** and **COVID** vaccines, **RSV** (older adults and pregnancy), and **pneumococcal** protection for older adults and people with chronic conditions.
- **Sleep, movement, nutrition, hydration** all support your immune system. Regular walking and strength work is part of it.
- **Cough/sneeze** into your elbow, toss tissues, wash hands.
- **Clean high-touch surfaces** (door handles, phones, remotes, rails) when someone is sick.

**If you're sick — staying home**
- Stay home and away from others until your **symptoms are getting better overall** and you've had **no fever for 24 hours without fever-reducing medicine**. Then take extra precautions (mask, hand-washing, ventilation, distance from high-risk people) for the next several days.
- Use a separate room and bathroom if you can; ask someone healthy to bring food.
- **Check current CDC and local health-department guidance**, which can change — and follow your workplace, school or facility's rules.

**Higher-risk people** (65+, pregnant, weakened immune system, chronic heart/lung/kidney disease, diabetes, infants): call a clinician early if symptoms start. Flu and COVID antiviral treatment works best when started within the first few days.

**When to seek emergency care:** trouble breathing, chest pain or pressure, confusion or trouble waking, bluish lips, seizure, fainting, stiff neck with fever, or oxygen below 90%.
""")

    with it[2]:
        st.markdown("Use this checklist for a care home, gym, studio or program. Tick what's in place.")
        CK = [
            "Daily symptom screening for staff, clients and visitors (fever, cough, aches, loss of smell/taste)",
            "Anyone with symptoms stays home / is isolated and tested",
            "Hand-rub stations at entrances and in every room, soap at every sink",
            "Masks available; required for symptomatic people and during outbreaks",
            "Ventilation: windows open or HEPA/air purifiers running; filters changed on schedule",
            "High-touch surfaces and shared equipment cleaned between uses (mats, bands, machines, rails)",
            "Flu, COVID and RSV vaccines offered to residents/clients and staff; records kept",
            "Sick-leave policy that lets staff stay home without penalty",
            "Residents/clients at higher risk are identified and have a plan to call a clinician early",
            "Written outbreak plan: who to call, how to separate sick people, how to notify families",
            "Know your local health department's outbreak-reporting rules and phone number",
            "Vitals (temperature, oxygen, heart rate) logged for anyone who is unwell, with escalation rules",
        ]
        done = [x for i, x in enumerate(CK) if st.checkbox(x, key=f"ck_{i}")]
        pct = int(len(done) / len(CK) * 100)
        st.progress(pct / 100, text=f"{len(done)} of {len(CK)} in place ({pct}%)")
        if pct < 100:
            st.markdown("**Still to do:**")
            for x in CK:
                if x not in done: st.markdown(f"- {x}")
        else:
            st.success("All items in place. Review monthly and before each respiratory-virus season.")

# ═════════════════════════════════════════════════════════════════════════════
#  7b — USER GUIDE
# ═════════════════════════════════════════════════════════════════════════════
elif menu == "📘 User Guide":
    section_header("User Guide", "How to Get the Best Results",
                   "Exactly how to take every measurement, run every test, and use every module")
    st.warning("Screening and education only — not medical advice. Stop any test if there is chest pain, dizziness, faintness or severe "
               "breathlessness. Have a spotter within arm's reach for every balance test.", icon="⚠️")

    with st.expander("✅ 10 rules for the best results (read first)", expanded=True):
        st.markdown("""
1. **Be consistent.** Same time of day, same scale/tape/blood-pressure cuff, same clothing, every re-test.
2. **Rest first.** Sit quietly 5 minutes before heart rate and blood pressure. No caffeine, nicotine or exercise in the 30 minutes before.
3. **Measure twice, enter the average.** Especially waist, neck, hip and blood pressure.
4. **Test safely.** Clear floor, shoes off for balance tests, a sturdy chair or counter and a spotter beside you.
5. **Warm up for 5 minutes** (walk in place, arm circles) before strength, balance and flexibility tests.
6. **Never push through pain or dizziness.** Skip the test and note it.
7. **Re-test every 8–12 weeks** and compare. Trends matter more than one number.
8. **For photos (fitness and posture):** whole body in frame, plain background, good light from the front, phone at hip height and steady, fitted clothes, 2–3 m away.
9. **Get consent** before any check-in, tracking or phone checkup of another person (the person, or a parent/guardian).
10. **Use fictional data until you add real security.** Set `APP_PASSWORD` in Render and ask a professional about HIPAA/privacy before storing real records.
""")

    with st.expander("❤️ Resting heart rate"):
        st.markdown("""
**How:** Sit quietly for 5 minutes (best in the morning, before coffee). Find your pulse on the thumb side of the wrist (or the side of the neck).
Count beats for 30 seconds and multiply by 2 — or count a full 60 seconds. A smartwatch is fine. Take it on 3 different mornings and enter the average.

**Typical adult range:** 60–100 bpm. Well-trained people can be lower. Above 100 at rest, or below 50 with dizziness or fainting, deserves a clinician's look.
Stress, poor sleep, illness, heat and caffeine all raise it. Beta-blockers lower it, so use RPE instead of heart rate to judge effort if you take them.
""")

    with st.expander("🩸 Blood pressure"):
        st.markdown("""
**How:** No caffeine, nicotine or exercise for 30 minutes; empty your bladder. Sit with your back supported, feet flat, legs uncrossed.
Rest the bare upper arm on a table so the cuff is at heart level. Use the **right cuff size** on an upper-arm validated monitor.
Stay still and silent. Sit 5 minutes, take **2 readings 1 minute apart**, and enter the average. Ideally repeat on several days.

| Category | Systolic (top) | Diastolic (bottom) |
|---|---|---|
| Normal | under 120 | and under 80 |
| Elevated | 120–129 | and under 80 |
| Stage 1 range | 130–139 | or 80–89 |
| Stage 2 range | 140 or higher | or 90 or higher |
| Crisis | over 180 | and/or over 120 |

A single high reading is not a diagnosis. If you read **over 180/120 with chest pain, severe headache, shortness of breath, weakness or confusion — call 911.**
""")

    with st.expander("📏 Body fat percentage (US Navy tape method)"):
        st.markdown("""
The app estimates body fat from tape measurements. It is an **estimate (typically ±3–4%)**, best used to track change over time, not as an exact number.

**Measure (standing relaxed, tape snug but not squeezing the skin, breathe out normally, read to the nearest 0.5 cm / 0.25 in):**
- **Height:** barefoot, back to a wall, looking straight ahead.
- **Neck:** just below the voice box (Adam's apple), tape level or sloping slightly down at the front.
- **Waist:** men — across the navel; women — at the narrowest point of the waist (usually just above the navel).
- **Hip:** the widest point around the buttocks (needed for women; the app also uses it for the waist-to-hip ratio).
- Take each measurement **3 times and average**.

**Reference ranges used (ACE categories):**

| | Essential | Athletic | Fitness | Average | High |
|---|---|---|---|---|---|
| Men | under 6% | 6–13% | 14–17% | 18–24% | 25%+ |
| Women | under 14% | 14–20% | 21–24% | 25–31% | 32%+ |

Healthy ranges are a little higher with age. Not suitable during pregnancy. Very muscular people can read higher than reality.
""")

    with st.expander("⚖️ Balance tests"):
        st.markdown("""
**Always** stand next to a sturdy counter or wall with a chair behind you and a spotter close. Shoes off, flat floor.

**1. Single-leg stance (eyes open)**
- Hands on hips or arms crossed. Lift one foot a few centimetres off the floor (don't rest it on the other leg).
- Start the timer when the foot leaves the floor; stop when the foot touches down, you hop, you grab for support, or you reach **30 seconds**.
- Do 2 tries per leg, enter the **best** for each leg.
- **Under 5 seconds = high fall risk.** Typical averages for healthy people: about 43 s (under 40), 37 s (50s), 27 s (60s), 15 s (70s), 9 s (80+).
- A difference of 5 s or more between legs is worth training and mentioning to a physio.

**2. Tandem stance (heel-to-toe)**
- Place one foot directly in front of the other, heel touching toes, arms out if needed. Hold up to **10 seconds**. Under 10 s means increased fall risk.

**3. Timed Up & Go (TUG)**
- Use a standard chair (seat about 46 cm / 18 in). Mark a line 3 m (10 ft) away.
- Start seated, back against the chair. On "go": stand, walk at a **comfortable, safe pace** to the line, turn, walk back and sit. Stop the timer when your back touches the chair.
- **12 seconds or more = fall risk.** Use usual shoes and walking aid.

**4. 30-second chair stand (lower-body strength)**
- Straight chair about 43 cm (17 in) high, against a wall. Arms crossed on the chest, feet flat.
- Count full stands in 30 seconds. If you cannot stand once without using your arms, record 0 and stop.
- Below-average cut-offs are built into the app by age and sex (ages 60+).
""")

    with st.expander("🤸 Flexibility tests"):
        st.markdown("""
Warm up 5 minutes first. Move slowly, **no bouncing**, stop at tension (never pain). If you have osteoporosis, a recent back/hip surgery or sciatica, ask a clinician before testing.

**Sit-and-reach (hamstrings and lower back)**
- Sit on the floor, legs straight, bare feet flat against a wall or box. Tape a ruler along the floor so **0 is at your toes**.
- Stack your hands, exhale and reach forward slowly along the ruler. Hold 2 seconds. Do 3 tries; enter the best.
- Enter **+ centimetres past your toes** or **− centimetres short** of your toes. Reaching your toes or beyond is good; more than about 7.5 cm (3 in) short means tight hamstrings/low back.
- Can't sit on the floor? Sit on the edge of a chair with one leg straight and heel on the floor and reach toward the toes — a gentler version.

**Back-scratch test (shoulders)**
- Reach one hand over the same shoulder and down your back; the other hand up your back from below. Try to touch fingertips.
- Choose: *Fingers overlap*, *Fingertips just touch*, *Gap under 5 cm*, or *Gap 5 cm or more*. Test both sides and enter the **tighter** side.
""")

    with st.expander("😮‍💨 Rate of Perceived Exertion (RPE)"):
        st.markdown("""
RPE is how hard the effort **feels** overall — body and breathing together. Rate it **right after** the test or set, not after resting.

**Borg 6–20 scale (used in the Body Assessment):**

| Rating | Feels like |
|---|---|
| 6 | No exertion (sitting) |
| 7–8 | Extremely light |
| 9–10 | Very light |
| 11 | Light |
| 12–13 | Somewhat hard |
| 14–15 | Hard |
| 16–17 | Very hard |
| 18–19 | Extremely hard |
| 20 | Maximal effort |

**CR10 scale (used per set in Fitness Training):** 0 rest · 1 very easy · 3 moderate · 5 hard · 7 very hard · 10 maximal.

**Talk test:** if you can talk in full sentences you're around RPE 11–13 (moderate); a few words at a time is about 15–17 (hard); you can't speak at all is near the maximum.
For most general-fitness and senior programs, aim for **Borg 11–14 (CR10 3–5)**. Because RPE doesn't depend on heart rate, it is the best guide if you take heart-rate-lowering medication.
""")

    with st.expander("📋 Using each module"):
        st.markdown("""
**Fitness Training** — pick the exercise and the side facing the camera. Take a photo at the *extended* position, then at the *flexed* position, then extended again; a rep is counted each time you return from flexed to extended.
Log RPE after each set. Reset clears the session. Analytics shows angle and RPE history and downloads a CSV.

**Total Body Assessment** — tick *Load a sample client* to see a full example result instantly. For a real client, enter measurements and test results (leave 0 / Not tested for any test you skip) and press **Run Assessment**.
You get an overall screening score, a score per area (heart & BP, body composition, strength, balance, flexibility, effort), detailed results, recommendations and a PDF.
The **Posture Photo** tab analyzes front or side photos and joint angles.

**Care Portal / Intake Forms** — admissions, searchable records, PDF packets and CSV export. Fill the intake with the client; the HIPAA box is required.

**Wellness & Safety** — create a profile (consent required), add safe zones (Home, School), then record check-ins with mood and location. Alerts appear if the person is outside every safe zone or hasn't checked in within your time limit.
The PHQ-2/GAD-2 screen and the crisis numbers are there for support, not diagnosis.

**Phone Security** — do the checkup **with** the phone's owner. Choose iPhone or Android, answer each question honestly (*Not sure* counts as unresolved), and follow the fix list. Use the Cleanup Playbook if you suspect an intruder, and the Link/Text Checker for suspicious messages.

**Translator** — the phrasebook works offline. Voice and live translation need the optional settings and send text to Google, so never enter private health details.
""")

    with st.expander("🩺 Vitals Lab — camera heart rate & phone balance (how to get a good reading)"):
        st.markdown("""
**Camera heart rate (works on a phone):** open the app on your phone, go to *Vitals Lab › Camera Heart Rate*, tap **Start**, allow the camera, then cover the **rear camera and flash** with your fingertip.
Press lightly, keep the hand resting and still, no talking, for 30 seconds. Sit and rest 5 minutes first. You get heart rate, rough HRV and a rough breathing rate with a quality %. If quality is poor, wait a moment and retry.
iPhone Safari cannot turn on the flash, so use bright indirect light. The heart rate is pre-filled into the Total Body Assessment.

**Phone balance:** hold the phone flat against your chest, stand beside a counter with a helper, tap **Start** (5-second countdown). Try feet together, tandem, and eyes closed. Lower average tilt and a higher score mean steadier. Compare the same person, same set-up, over time.

**Breathing pacer:** calming patterns (4-6, resonance 5.5, box, 4-7-8). Stop if dizzy.

**Vitals log:** add readings (heart rate, temperature, oxygen, BP, breaths, weight). The app compares the newest values with the person's own recent baseline and raises early-warning flags (e.g. resting HR 10+ bpm above usual, fever, low oxygen).

**Wearable import:** upload a CSV from a watch/band to see daily resting-heart-rate trends.

These are experimental tools to build on, not medical devices.
""")
    with st.expander("🦠 Illness & Infection Check"):
        st.markdown("""
Enter the person's age group, risk factors, temperature, oxygen, symptoms and warning signs. The app tells you whether to **call 911**, **contact a clinician today**, or **stay home and test**, and what home-care and isolation basics apply.
It also logs vitals for early-warning trends. The *Prevention* tab covers hand hygiene, ventilation, masks, vaccines and staying home; the *Facility checklist* helps care homes, gyms and studios prepare for respiratory-virus season.
It gives guidance only — no diagnosis and no medicine doses. Always follow current CDC / local health-department advice.
""")
    with st.expander("🚫 Ad blocking & pop-up prevention"):
        st.markdown("""
Phone Security › **🚫 Ad Blocking**: run the test on the phone to see how many ad/tracker addresses are blocked, then follow the setup steps
(Android Private DNS `dns.adguard-dns.com`, Firefox + uBlock Origin, Brave, Safari content blockers on iPhone, router-level DNS filters).
Also covers browser notification spam and ads drawn over other apps. The Phone Guardian scan checks your Private DNS provider and lists apps allowed to draw over other apps.
No tool blocks every ad — YouTube and in-app ads usually get through DNS blocking — and random free "ad blocker" apps can themselves be adware, so stick to well-known ones.
""")
    with st.expander("📱 Phone Performance Check & Phone Guardian"):
        st.markdown("""
**⚡ Performance Check** (Phone Security › Performance Check): open the app **on the phone**, tap *Run phone check* and leave the screen alone ~12 seconds.
You get CPU speed, smoothness (fps), connection delay, memory class, battery/network/storage readings, OS-age and browser-safety checks, a performance score, a safety-hygiene %, and a to-do list. Save results to see the trend for that phone.

**🛡️ Phone Guardian**: download the zip, run it on the phone with Termux (Android) or Python (computer), then upload `latest-report.json` to see the findings here.
It flags sideloaded apps, accessibility / notification-reading apps, device-admin entries, debugging switches, patch age, battery heat, memory, storage, and **new apps since the last scan**.
Limits: a web page cannot see other apps; iPhones do not allow device scans; a clean report is not a guarantee.

**Best-results routine:** restart the phone, plug it in (or charge above 30%), turn off battery saver, close other tabs, run the Performance Check, then the Guided Checkup, then the Guardian scan.
""")
    with st.expander("☁️ Running it on Render"):
        st.markdown("""
- Set **APP_PASSWORD** in Render › Environment so only people you share it with can open the app.
- On the free plan, saved records are erased when the app restarts. Attach a persistent disk and set **DB_PATH=/data/lifehaven.db** to keep them.
- The first load after the app sleeps takes up to a minute.
- Allow camera access in the browser when asked. The camera only works over HTTPS (Render provides this).
""")

# ═════════════════════════════════════════════════════════════════════════════
#  8 — CLIENT PORTAL
# ═════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("""
    <div class="portal-hero">
      <div style="font-size:.78rem;font-weight:600;letter-spacing:.2em;color:var(--teal);text-transform:uppercase;margin-bottom:16px">◆ Welcome ◆</div>
      <div class="portal-title">LifeHaven Client Portal</div>
      <div class="portal-sub">A premium, secure experience for clients and their families.<br>
        Health records · Digital intake · Fitness · Body assessment · Wellness check-ins · Phone safety · Translation.</div>
      <div class="feature-grid">
        <div class="feature-card"><div class="f-icon">💪</div><div class="f-name">Fitness AI</div><div class="f-desc">Pose-detection rep counter and analytics</div></div>
        <div class="feature-card"><div class="f-icon">🧍</div><div class="f-name">Body Assessment</div><div class="f-desc">Vitals, fall-risk, posture photo analysis, PDF</div></div>
        <div class="feature-card"><div class="f-icon">📋</div><div class="f-name">Digital Intake</div><div class="f-desc">7-section admission packet saved + PDF</div></div>
        <div class="feature-card"><div class="f-icon">🏥</div><div class="f-name">Care Records</div><div class="f-desc">Resident database with PDF and voice summary</div></div>
        <div class="feature-card"><div class="f-icon">🧭</div><div class="f-name">Wellness Check-ins</div><div class="f-desc">Consent-based safe zones and mood trends</div></div>
        <div class="feature-card"><div class="f-icon">🔒</div><div class="f-name">Phone Security</div><div class="f-desc">Intruder checkup, cleanup playbook, scam checker</div></div>
        <div class="feature-card"><div class="f-icon">🌐</div><div class="f-name">Translator</div><div class="f-desc">Care phrases in five languages</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

# ───────────────────────── FOOTER ─────────────────────────
st.markdown("""<div class="footer">🌿 <b>ReubenSoul PeaceUnity LifeHaven</b> &nbsp;·&nbsp; Built by ReubenSoul4peaceunity<br>
Health &nbsp;•&nbsp; Peace &nbsp;•&nbsp; Unity &nbsp;•&nbsp; Technology</div>""", unsafe_allow_html=True)
