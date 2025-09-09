import streamlit as st
import pandas as pd
import random
from datetime import datetime
from zoneinfo import ZoneInfo   # Python 3.9+ sudah ada built-in

# ==============================
# Konfigurasi
# ==============================
st.set_page_config(page_title="Mini Quiz Karier v17", page_icon="🎯", layout="centered")

# ------------------------------
# CSS
# ------------------------------
st.markdown("""
<style>
.block-container { padding-top: 1.5rem; padding-bottom: 2.5rem; }
.banner { background: linear-gradient(135deg,#f0f7ff 0%,#fff0fb 100%);
  border:1px solid #e6e7eb;border-radius:18px;padding:18px 22px;margin-bottom:14px; }
.banner h1 { font-size:1.6rem;margin:0;line-height:1.25; }
.muted { color:#5f6b7a; }
.card { border:1px solid #e6e7eb;border-radius:16px;background:#fff;
  padding:16px;box-shadow:0 1px 2px rgba(0,0,0,.04);margin-bottom:16px; }
.result-title { font-size:1.35rem;font-weight:800;margin:0; }
.badge { display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:999px;
  background:#eef6ff;color:#164e63;font-weight:700;border:1px solid #dbeafe;font-size:.95rem; }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Header
# ------------------------------
st.markdown("""
<div class="banner">
  <h1>🎉 Quiz ala horoscope tapi versi karier 🚀</h1>
  <div class="muted">Cari tahu apakah kamu lebih cocok jadi <b>Programmer</b>, <b>Designer</b>, atau <b>Data Scientist</b>!</div>
</div>
""", unsafe_allow_html=True)

# ------------------------------
# Pertanyaan berbobot
# ------------------------------
QUESTIONS = [
    {
        "q": "Aktivitas yang paling bikin kamu puas:",
        "options": {
            "Menyelesaikan masalah logika/algoritma": {"Programmer": 5, "Data Scientist": 4, "Designer": 2},
            "Membuat desain visual": {"Designer": 5, "Programmer": 2, "Data Scientist": 2},
            "Menginterpretasi data/statistik": {"Data Scientist": 5, "Programmer": 4, "Designer": 2},
            "Berkoordinasi & memimpin tim": {"Programmer": 3, "Designer": 3, "Data Scientist": 3},
        },
    },
    {
        "q": "Tools yang paling ingin kamu kuasai:",
        "options": {
            "VS Code, GitHub": {"Programmer": 5, "Data Scientist": 3, "Designer": 1},
            "Figma, Adobe, Canva": {"Designer": 5, "Programmer": 2, "Data Scientist": 1},
            "Python, R, Pandas": {"Data Scientist": 5, "Programmer": 4, "Designer": 1},
            "Trello, Miro, Notion": {"Programmer": 3, "Designer": 3, "Data Scientist": 3},
        },
    },
    {
        "q": "Cara menghadapi masalah kompleks:",
        "options": {
            "Debugging step-by-step": {"Programmer": 5, "Data Scientist": 3, "Designer": 1},
            "Riset data & uji hipotesis": {"Data Scientist": 5, "Programmer": 3, "Designer": 1},
            "User testing & iterasi desain": {"Designer": 5, "Programmer": 2, "Data Scientist": 1},
            "Brainstorm bareng tim": {"Programmer": 3, "Designer": 3, "Data Scientist": 3},
        },
    },
    {
        "q": "Hasil kerja yang bikin kamu bangga:",
        "options": {
            "Aplikasi berjalan stabil": {"Programmer": 5, "Designer": 2, "Data Scientist": 2},
            "UI/UX cantik & ramah pengguna": {"Designer": 5, "Programmer": 2, "Data Scientist": 2},
            "Model statistik akurat": {"Data Scientist": 5, "Programmer": 3, "Designer": 2},
            "Dokumentasi jelas & bisa dipahami": {"Programmer": 3, "Designer": 3, "Data Scientist": 3},
        },
    },
    {
        "q": "Jika diberi 1 minggu belajar sesuatu:",
        "options": {
            "Algoritma & struktur data": {"Programmer": 5, "Data Scientist": 3, "Designer": 1},
            "Prinsip warna & tipografi": {"Designer": 5, "Programmer": 2, "Data Scientist": 1},
            "Machine learning dasar": {"Data Scientist": 5, "Programmer": 3, "Designer": 1},
            "Manajemen proyek & komunikasi": {"Programmer": 3, "Designer": 3, "Data Scientist": 3},
        },
    },
]
CATEGORIES = ["Programmer", "Designer", "Data Scientist"]

TIPS = {
    "Programmer": "💡 Coba belajar Git, Python, atau ikutan competitive programming.",
    "Designer": "💡 Explore Figma, dan baca buku 'Don't Make Me Think'.",
    "Data Scientist": "💡 Mulai dari Pandas, Kaggle dataset, dan dasar Machine Learning.",
}

QUOTES = {
    "Programmer": [
        "“Talk is cheap. Show me the code.” 💻",
        "“Programmer: a machine that turns coffee into code.” ☕💻",
        "“Code never lies, comments sometimes do.” 🔍",
    ],
    "Designer": [
        "“Design is intelligence made visible.” 🎨",
        "“Good design is obvious. Great design is transparent.” ✨",
        "“People ignore design that ignores people.” 👥",
    ],
    "Data Scientist": [
        "“Without data, you’re just another person with an opinion.” 📊",
        "“Data is the new oil.” ⛽📊",
        "“The goal is to turn data into information, and information into insight.” 🔎",
    ],
}

# ------------------------------
# State
# ------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# ------------------------------
# Form
# ------------------------------
with st.form("quiz", clear_on_submit=False):
    answered = 0
    for idx, item in enumerate(QUESTIONS):
        st.markdown(f"#### {idx+1}. {item['q']}")
        opts = list(item["options"].keys())
        default_index = None
        prev = st.session_state.get(f"q{idx}")
        if prev in opts:
            default_index = opts.index(prev)
        ans = st.radio("Pilih jawaban:", opts, index=default_index, key=f"q{idx}", label_visibility="collapsed")
        if ans is not None:
            answered += 1
    st.progress(answered / len(QUESTIONS))
    submitted = st.form_submit_button("🔎 Lihat Hasil")

# ------------------------------
# Util
# ------------------------------
def all_answered():
    return all(st.session_state.get(f"q{i}") is not None for i in range(len(QUESTIONS)))

def calc_scores():
    tally = {c: 0 for c in CATEGORIES}
    for i, item in enumerate(QUESTIONS):
        ans = st.session_state.get(f"q{i}")
        if ans:
            for cat, pts in item["options"][ans].items():
                tally[cat] += pts
    return pd.DataFrame([tally])

def join_atau(names):
    if len(names) == 1: return names[0]
    if len(names) == 2: return f"{names[0]} atau {names[1]}"
    return ", ".join(names[:-1]) + f" atau {names[-1]}"

# ------------------------------
# Hasil
# ------------------------------
if submitted:
    if not all_answered():
        st.warning("Masih ada pertanyaan yang belum dijawab.")
    else:
        df = calc_scores()
        max_score = df.iloc[0].max()
        top_cats = [c for c in CATEGORIES if df.iloc[0][c] == max_score]
        rekom = join_atau(top_cats)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="result-title">✅ Rekomendasi Karier Kamu</div>', unsafe_allow_html=True)

        if len(top_cats) == 3:
            st.subheader("✨ Wah, kamu All Role!")
            st.markdown("<span class='badge'>Fleksibel banget, bisa jadi Programmer, Designer, atau Data Scientist 🎭</span>", unsafe_allow_html=True)
            st.info("Kamu seimbang di semua kategori. Pilih yang paling bikin kamu enjoy sekarang, atau eksplor peran hybrid 🔀")
        else:
            st.subheader(rekom)
            if len(top_cats) == 2:
                funny_badge = "🤹 Wah, kamu hibrida! Cocok di dua dunia sekaligus."
            else:
                funny_badge_map = {
                    "Programmer": "Siap siap ngopi jam 2 pagi sambil debug bug misterius 😆",
                    "Designer": "Debat warna #FFFFFF vs #FAFAFA itu serius banget loh 🤯",
                    "Data Scientist": "Anggap dataset sebagai sahabat sejati 🤭",
                }
                funny_badge = funny_badge_map[top_cats[0]]
            st.markdown(f"<span class='badge'>{funny_badge}</span>", unsafe_allow_html=True)
            for cat in top_cats:
                st.info(TIPS[cat])
            st.success(random.choice(QUOTES[top_cats[0]]))

        st.markdown("</div>", unsafe_allow_html=True)

        # Simpan riwayat dengan Asia/Jakarta & format 24 jam
        now = datetime.now(ZoneInfo("Asia/Jakarta"))
        row = {
            "tanggal": now.strftime("%d/%m/%Y"),
            "jam": now.strftime("%H:%M:%S"),   # 24 jam
            **df.iloc[0].to_dict(),
            "hasil": rekom,
        }
        st.session_state.history.append(row)

# ------------------------------
# Riwayat
# ------------------------------
if st.session_state.history:
    with st.expander("📒 Riwayat Kuis (klik untuk lihat/sembunyikan)", expanded=False):
        hist_df = pd.DataFrame(st.session_state.history)
        st.dataframe(hist_df, use_container_width=True)
        csv_bytes = hist_df.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button("💾 Unduh Riwayat (.csv)", data=csv_bytes, file_name="riwayat_quiz_v17.csv", mime="text/csv")
else:
    st.caption("Belum ada riwayat kuis.")

st.markdown("---")
st.caption("Made with ❤️ — Fawwaz")
