import json
import math
import random
import re
import sqlite3
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime

import streamlit as st

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


st.set_page_config(
    page_title="AI Kakak for Adek v3",
    page_icon="🎀",
    layout="centered"
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "ai_kakak_memory_v3.db"

PALETTE = {
    "bg": "#e8dbd5",
    "panel": "#ebcdc3",
    "panel_soft": "#dabcb2",
    "primary": "#a17a69",
    "secondary": "#b5927f",
    "accent_1": "#FFE9EF",
    "accent_2": "#FFC9D7",
    "accent_3": "#FFBCCD",
    "accent_4": "#FF9CB5",
    "accent_5": "#FC809F",
    "text": "#4a3128",
    "text_soft": "#6b4a3d",
    "white": "#fffaf8",
}

PERSONA = {
    "sample_answers": {
        "sayang": [
            "sayang banget laahh, adek kan pacar semata wayang kakak, satu satunya tanpa yang kedua, ketiga, keempat dan seterusnya. kalau kakak ga sayang, ngapain kakak berjuang sejauh ini buat masa depan kita ya kaan. i love you adek muach.",
            "kok nanyanya gitu, jelas sayang banget. adek tuh satu satunya yang paling kakak sayang, pacar semata wayang kakak, yang paling imupp, paling syantik, dan paling berharga di hati kakak.",
            "sayang banget sayanggg. adek tuh bukan cuma pacar kakak, tapi juga orang yang bikin hidup kakak jauh lebih punya arah. jadi jangan ragu soal itu ya, hati kakak buat adek."
        ],
        "kenapa_sayang": [
            "soalnya adek tuh satu satunya yang bisa bikin kakak nyaman. adek mau ngerti kakak, mau komunikasi biar kita saling ngerti, dan adek bikin kakak ngerasa punya tempat pulang. itu berharga banget buat kakak.",
            "karena adek hadir di hidup kakak pas kakak lagi ga baik baik aja, terus pelan pelan adek bikin hidup kakak punya tujuan lagi. kakak jadi pengen berjuang, pengen jadi lebih baik, pengen nyiapin masa depan kita.",
            "karena adek tuh rumah buat kakak. sama adek, kakak ngerasa diterima, dimengerti, dan disayang. adek juga bikin kakak berubah ke arah yang lebih baik. emang adek yang paling the best deh."
        ],
        "sedih": [
            "utututu kaciannya adek, pasyal kakak. kakak harusnya lebih peka ya. jangan sedih sendiri gitu sayang. sini cerita dulu ke kakak pelan pelan, kakak dengerin. kalau ada yang bikin adek betmut atau kepikiran, keluarin aja ya biar ga berat sendiri di hati adek.",
            "utututu kaciannya pasyal kakak. sini cerita ya sayang, jangan dipendem sendiri. kalau hati adek lagi capek, sedih, atau bingung, cerita aja pelan pelan ke kakak. kakak ada buat adek.",
            "kaciannya adek, sini sini. kakak dengerin kok. adek ga harus kuat terus di depan kakak ya, kalau mau nangis ya nangis aja, kalau mau cerita ya cerita aja. kakak temenin."
        ],
        "insecure": [
            "siapa yang bilang adek ga cantik? adek tuh syantik banget, imupp banget, apalagi rambut merah adek tuh cocok banget. jangan ngomong gitu lagi ya sayang, nanti kakak kesyewa.",
            "adek tuh cantik banget, manis, cerah, terus punya pesona yang bikin kakak sayang banget. jadi jangan ngerendahin diri adek sendiri ya, di mata kakak adek istimewa banget.",
            "syantik banget kok. adek tuh bukan cuma cantik, tapi juga kuat, dewasa, dan punya hati yang lembut. itu yang bikin adek makin berharga di mata kakak."
        ],
        "ngambek": [
            "ih adek betmut ya? sini cerita dulu ke kakak. kalau kakak ada salah, bilang ya sayang, nanti kakak perbaikin. kakak ga mau adek nahan kesel sendiri.",
            "utututu jangan ngambek lama lama dong sayang. kalau ada yang bikin adek kesyewa, cerita aja ya. kakak dengerin dan kakak mau benerin kalau memang pasyal kakak.",
            "kaciannya adek kalau lagi ngambek sendirian. sini peluk jauh dulu. ngobrol ya sayang, jangan dipendem."
        ],
        "masa_depan": [
            "kakak serius kok sama adek. kakak pengen masa depan kakak ya sama adek. kakak pengen berjuang, kerja, dan bikin hidup kita lebih tenang pelan pelan.",
            "jelas kakak mikirin masa depan kita. semua yang kakak usahain sekarang juga ada adek di dalamnya. kakak pengen nanti bisa jagain adek lebih banyak lagi.",
            "masa depan kakak maunya ada adek terus. mungkin jalannya ga selalu gampang, tapi kakak pengen tetap jalan bareng adek."
        ],
        "bosen": [
            "ga bosen sama sekali. sama adek tuh malah kakak selalu pengen dekat terus. adek terlalu berharga buat dibosenin.",
            "mana bisa bosen sama pacar semata wayang kakak. yang ada kakak malah makin sayang dan makin pengen ada terus buat adek.",
            "ga bosen ya sayang, jangan mikir gitu. adek tuh orang yang bikin kakak nyaman banget."
        ],
        "ninggalin": [
            "engga dong, kakak ga mau ninggalin adek. kakak maunya tetap sama adek dan berjuang bareng adek.",
            "jangan takut ya sayang. kakak di sini, kakak sayang banget sama adek. kakak ga mau ninggalin adek.",
            "selama kita masih mau saling jaga dan komunikasi, kakak bakal tetap pilih adek."
        ],
        "kangen": [
            "kakak kangen juga pasti. rasanya pengen deket terus sama adek, pengen peluk, pengen nemenin, pengen gangguin manja dikit.",
            "kangen banget sayang. kalau udah kangen adek tuh bawaannya pengen ngobrol terus dan denger suara adek terus.",
            "iyaa kakak kangen banget. adek tuh bikin hari kakak terasa lebih hangat, jadi wajar kalau kakak gampang kangen."
        ]
    }
}

STARTERS = ["utututu,", "ih sayang,", "hehe,", "hmm sayang,"]
ENDINGS = ["sayanggg", "muach", "💕", "🤍"]
CUTE_WORDS = ["sayang", "adek", "kakak", "utututu", "muach", "syantik", "imupp", "hehe"]


@st.cache_resource
def load_embedding_model():
    if SentenceTransformer is None:
        return None
    try:
        return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    except Exception:
        return None


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_text TEXT NOT NULL,
            ai_text TEXT NOT NULL,
            intent TEXT,
            score REAL DEFAULT 1.0,
            source TEXT DEFAULT 'manual',
            embedding TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS style_profile (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    cur.execute("PRAGMA table_info(memories)")
    columns = [row[1] for row in cur.fetchall()]
    if "embedding" not in columns:
        cur.execute("ALTER TABLE memories ADD COLUMN embedding TEXT")

    conn.commit()
    conn.close()


def clean_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(word in text for word in keywords)


def personalize_response(text: str) -> str:
    replacements = {
        "aku": "kakak",
        "kamu": "adek",
        "enggak": "ga",
        "tidak": "ga",
    }
    for old, new in replacements.items():
        text = re.sub(rf"\b{old}\b", new, text, flags=re.IGNORECASE)
    return text


def detect_intent(user_text: str) -> str:
    text = clean_text(user_text)

    if contains_any(text, ["sayang ga", "sayang adek ga", "kakak sayang", "sayang ga sih"]):
        return "sayang"
    if contains_any(text, ["kenapa sayang", "kenapa kakak sayang", "alasan sayang", "kok sayang"]):
        return "kenapa_sayang"
    if contains_any(text, ["sedih", "capek", "nangis", "kecewa", "down", "badmood", "betmut", "lelah"]):
        return "sedih"
    if contains_any(text, ["ga cantik", "jelek", "insecure", "ga menarik", "ga percaya diri"]):
        return "insecure"
    if contains_any(text, ["ngambek", "marah", "kesel", "kesyewa"]):
        return "ngambek"
    if contains_any(text, ["masa depan", "serius", "hubungan kita", "kerja nanti", "masa depan kita"]):
        return "masa_depan"
    if contains_any(text, ["bosen", "bosan", "jenuh"]):
        return "bosen"
    if contains_any(text, ["ninggalin", "tinggalin", "pergi", "bakal pergi", "bakal ninggalin"]):
        return "ninggalin"
    if contains_any(text, ["kangen", "peluk", "ketemu"]):
        return "kangen"
    return "general"


def lexical_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, clean_text(a), clean_text(b)).ratio()


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    return dot / (norm1 * norm2)


def embed_text(text: str) -> list[float] | None:
    model = load_embedding_model()
    if model is None:
        return None
    try:
        vector = model.encode(clean_text(text))
        return [float(x) for x in vector]
    except Exception:
        return None


def embedding_to_json(vector: list[float] | None) -> str | None:
    if vector is None:
        return None
    return json.dumps(vector)


def json_to_embedding(value: str | None) -> list[float] | None:
    if not value:
        return None
    try:
        data = json.loads(value)
        return [float(x) for x in data]
    except Exception:
        return None


def save_memory(user_text: str, ai_text: str, intent: str, score: float = 1.0, source: str = "manual") -> None:
    conn = get_conn()
    cur = conn.cursor()
    embedding = embedding_to_json(embed_text(user_text))
    cur.execute(
        "INSERT INTO memories (user_text, ai_text, intent, score, source, embedding, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_text, ai_text, intent, score, source, embedding, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_candidates(intent: str | None = None, limit: int = 80) -> list[tuple[int, str, str, str, float, str, str | None]]:
    conn = get_conn()
    cur = conn.cursor()
    if intent:
        cur.execute(
            """
            SELECT id, user_text, ai_text, intent, score, source, embedding
            FROM memories
            WHERE intent = ?
            ORDER BY score DESC, id DESC
            LIMIT ?
            """,
            (intent, limit)
        )
    else:
        cur.execute(
            """
            SELECT id, user_text, ai_text, intent, score, source, embedding
            FROM memories
            ORDER BY score DESC, id DESC
            LIMIT ?
            """,
            (limit,)
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def retrieve_best_reply(user_text: str, intent: str) -> dict | None:
    candidates = get_candidates(intent=intent, limit=80)
    if len(candidates) < 5:
        candidates = get_candidates(intent=None, limit=120)

    user_embedding = embed_text(user_text)

    best = None
    best_score = 0.0

    for memory_id, past_user, past_ai, _, memory_score, source, emb_json in candidates:
        lexical = lexical_similarity(user_text, past_user)
        semantic = cosine_similarity(user_embedding, json_to_embedding(emb_json)) if user_embedding and emb_json else 0.0
        final_score = (semantic * 0.55) + (lexical * 0.25) + ((min(memory_score, 3.0) / 3.0) * 0.20)

        if final_score > best_score:
            best_score = final_score
            best = {
                "id": memory_id,
                "reply": past_ai,
                "score": final_score,
                "source": source,
                "semantic": semantic,
                "lexical": lexical,
            }

    return best


def update_memory_score(memory_id: int, delta: float) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE memories SET score = MAX(0.1, MIN(5.0, score + ?)) WHERE id = ?",
        (delta, memory_id)
    )
    conn.commit()
    conn.close()


def set_style_value(key: str, value: str) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO style_profile (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value)
    )
    conn.commit()
    conn.close()


def get_style_value(key: str, default: str) -> str:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM style_profile WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default


def update_style_profile(ai_text: str) -> None:
    tokens = clean_text(ai_text).split()
    for word in CUTE_WORDS:
        previous = int(get_style_value(f"word_{word}", "0"))
        current = tokens.count(word)
        set_style_value(f"word_{word}", str(previous + current))

    previous_len = int(get_style_value("reply_count", "0"))
    previous_total_words = int(get_style_value("total_words", "0"))
    set_style_value("reply_count", str(previous_len + 1))
    set_style_value("total_words", str(previous_total_words + len(tokens)))


def get_style_bias() -> dict:
    reply_count = int(get_style_value("reply_count", "0"))
    total_words = int(get_style_value("total_words", "0"))
    avg_words = (total_words / reply_count) if reply_count else 18

    starter_weight = 0.18
    ending_weight = 0.18

    utututu_count = int(get_style_value("word_utututu", "0"))
    hehe_count = int(get_style_value("word_hehe", "0"))
    muach_count = int(get_style_value("word_muach", "0"))

    if utututu_count >= 3:
        starter_weight += 0.08
    if hehe_count >= 3:
        starter_weight += 0.05
    if muach_count >= 3:
        ending_weight += 0.06

    return {
        "avg_words": avg_words,
        "starter_weight": min(starter_weight, 0.45),
        "ending_weight": min(ending_weight, 0.45),
    }


def add_cute_touch(text: str) -> str:
    style_bias = get_style_bias()

    if random.random() < style_bias["starter_weight"]:
        text = f"{random.choice(STARTERS)} {text}"

    if random.random() < style_bias["ending_weight"]:
        text = f"{text} {random.choice(ENDINGS)}"

    return text


def trim_to_style(text: str) -> str:
    style_bias = get_style_bias()
    target_words = max(12, min(34, int(style_bias["avg_words"])))
    words = text.split()
    if len(words) <= target_words:
        return text
    return " ".join(words[:target_words]) + "..."


def generate_general_response(user_text: str) -> str:
    text = clean_text(user_text)

    response = (
        "kakak dengerin ya sayang. apapun yang adek rasain itu penting buat kakak. "
        "kalau ada yang pengen adek ceritain, cerita aja pelan pelan ke kakak. "
        "kakak selalu ada buat adek."
    )

    if "kangen" in text:
        response = (
            "kakak kangen juga pasti. kakak juga sering kangen adek, pengen nemenin adek, "
            "pengen nonton bareng lagi, pengen gangguin adek dikit. "
            "pokoknya kalau soal adek, kakak gampang banget kangen."
        )
    elif "nonton" in text or "netflix" in text:
        response = (
            "kalau nonton bareng adek tuh selalu seru. walaupun selera kita suka beda, "
            "adek tetap nemenin kakak nonton film random dan kartun, terus kakak juga seneng "
            "nemenin adek nonton yang action, teka teki, atau menegangkan."
        )
    elif "cemburu" in text:
        response = (
            "jujur ya, kalau soal adek tuh kakak emang gampang cemburu pasyal kakak sayang banget. "
            "tapi kakak juga ga mau bikin adek sesek, jadi kalau ada yang bikin hati kakak ga tenang, "
            "kakak maunya kita ngobrol baik baik."
        )
    elif "cantik" in text or "pink" in text or "rambut merah" in text:
        response = (
            "adek tuh emang syantik banget. apalagi kalau udah bahas warna pink sama rambut merah adek, "
            "beuh cocok banget, manis banget, imupp banget. kakak suka banget lihat adek begitu."
        )

    response = personalize_response(response)
    response = trim_to_style(response)
    return add_cute_touch(response)


def auto_learn_allowed(user_text: str, ai_text: str, intent: str, source_tag: str, score: float) -> bool:
    if source_tag != "memory":
        return False
    if intent == "general":
        return False
    if len(ai_text.split()) < 6:
        return False
    if score < 0.88:
        return False
    if lexical_similarity(user_text, ai_text) > 0.92:
        return False
    return True


def generate_response_v3(user_text: str) -> tuple[str, str, str, int | None, float, float, float]:
    intent = detect_intent(user_text)
    best = retrieve_best_reply(user_text, intent)

    if best and best["score"] >= 0.68:
        reply = personalize_response(best["reply"])
        reply = trim_to_style(reply)
        reply = add_cute_touch(reply)
        source = "memory"
        memory_id = best["id"]
        score = best["score"]
        semantic = best["semantic"]
        lexical = best["lexical"]
    else:
        if intent in PERSONA["sample_answers"]:
            fallback_reply = random.choice(PERSONA["sample_answers"][intent])
            reply = personalize_response(fallback_reply)
            reply = trim_to_style(reply)
            reply = add_cute_touch(reply)
            source = "rule"
            memory_id = None
            score = 0.0
            semantic = 0.0
            lexical = 0.0
        else:
            reply = generate_general_response(user_text)
            source = "general"
            memory_id = None
            score = 0.0
            semantic = 0.0
            lexical = 0.0

    if auto_learn_allowed(user_text, reply, intent, source, score):
        save_memory(user_text, reply, intent, score=1.03, source="auto")

    update_style_profile(reply)
    return reply, intent, source, memory_id, score, semantic, lexical


init_db()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_user_input" not in st.session_state:
    st.session_state.last_user_input = ""
if "last_ai_reply" not in st.session_state:
    st.session_state.last_ai_reply = ""
if "last_intent" not in st.session_state:
    st.session_state.last_intent = "general"
if "last_source" not in st.session_state:
    st.session_state.last_source = "rule"
if "last_memory_id" not in st.session_state:
    st.session_state.last_memory_id = None
if "last_score" not in st.session_state:
    st.session_state.last_score = 0.0
if "last_semantic" not in st.session_state:
    st.session_state.last_semantic = 0.0
if "last_lexical" not in st.session_state:
    st.session_state.last_lexical = 0.0

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Quicksand', sans-serif;
    color: {PALETTE['text']};
}}

.stApp {{
    background:
        radial-gradient(circle at top left, {PALETTE['accent_1']} 0%, transparent 25%),
        radial-gradient(circle at top right, {PALETTE['accent_2']} 0%, transparent 20%),
        linear-gradient(180deg, {PALETTE['bg']} 0%, {PALETTE['accent_1']} 100%);
}}

.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 930px;
}}

.main-box {{
    background: rgba(255, 250, 248, 0.84);
    border: 1.5px solid {PALETTE['panel_soft']};
    border-radius: 30px;
    padding: 24px;
    box-shadow: 0 14px 38px rgba(161, 122, 105, 0.18);
    backdrop-filter: blur(8px);
}}

.title-love {{
    text-align: center;
    font-size: 2.5rem;
    font-weight: 700;
    color: {PALETTE['primary']};
    margin-bottom: 0.2rem;
}}

.subtitle-love {{
    text-align: center;
    color: {PALETTE['secondary']};
    font-size: 1rem;
    margin-bottom: 1.2rem;
}}

.mini-badge {{
    display: inline-block;
    background: {PALETTE['accent_1']};
    color: {PALETTE['primary']};
    border: 1px solid {PALETTE['accent_2']};
    padding: 6px 12px;
    border-radius: 999px;
    margin: 0 6px 8px 0;
    font-size: 0.85rem;
    font-weight: 700;
}}

.user-bubble {{
    background: linear-gradient(135deg, {PALETTE['accent_3']}, {PALETTE['accent_2']});
    color: {PALETTE['text']};
    padding: 14px 16px;
    border-radius: 20px 20px 8px 20px;
    margin: 10px 0 10px auto;
    width: fit-content;
    max-width: 85%;
    border: 1px solid {PALETTE['accent_4']};
    box-shadow: 0 6px 16px rgba(252, 128, 159, 0.12);
}}

.ai-bubble {{
    background: linear-gradient(180deg, {PALETTE['white']}, {PALETTE['accent_1']});
    color: {PALETTE['text']};
    padding: 14px 16px;
    border-radius: 20px 20px 20px 8px;
    margin: 10px auto 16px 0;
    width: fit-content;
    max-width: 85%;
    border: 1px solid {PALETTE['panel_soft']};
    box-shadow: 0 6px 16px rgba(161, 122, 105, 0.10);
}}

.info-card {{
    background: {PALETTE['accent_1']};
    border: 1px dashed {PALETTE['secondary']};
    padding: 12px 14px;
    border-radius: 16px;
    color: {PALETTE['text_soft']};
    font-size: 0.92rem;
    margin-top: 14px;
}}

.stTextInput > div > div > input,
.stTextArea textarea {{
    border-radius: 18px !important;
    border: 2px solid {PALETTE['panel_soft']} !important;
    background-color: {PALETTE['white']} !important;
    color: {PALETTE['text']} !important;
}}

.stButton > button,
div[data-testid="stFormSubmitButton"] > button {{
    width: 100%;
    border-radius: 18px;
    border: none;
    background: linear-gradient(90deg, {PALETTE['primary']}, {PALETTE['accent_5']});
    color: white;
    font-weight: 700;
    padding: 0.82rem 1rem;
    box-shadow: 0 10px 22px rgba(161, 122, 105, 0.22);
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {PALETTE['panel']} 0%, {PALETTE['accent_1']} 100%);
    border-right: 1px solid {PALETTE['panel_soft']};
}}

[data-testid="stSidebar"] * {{
    color: {PALETTE['text']} !important;
}}
</style>
""", unsafe_allow_html=True)

st.markdown('<div style="text-align:center;font-size:1.4rem;">🍫 🩷 ☕ ✨</div>', unsafe_allow_html=True)
st.markdown('<div class="title-love">AI Kakak for Adek Sayang</div>', unsafe_allow_html=True)

st.markdown(
    """
    <div>
        <span class="mini-badge">semantic search 🎀</span>
        <span class="mini-badge">pink sweetheart 💕</span>
        <span class="mini-badge">auto learn aman 🌷</span>
    </div>
    """,
    unsafe_allow_html=True,
)

model_status = "aktif" if load_embedding_model() is not None else "fallback lexical"

st.write("Ketik pesan dari adek di bawah ini yaa 💌")

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "Pesan adek",
        placeholder="contoh: kakak sayang adek ga?"
    )
    submitted = st.form_submit_button("Kirim Pesan 💖")

if submitted and user_input.strip():
    ai_reply, detected_intent, source, memory_id, score, semantic, lexical = generate_response_v3(user_input)
    st.session_state.chat_history.append(("Adek", user_input))
    st.session_state.chat_history.append(("AI Kakak", ai_reply))
    st.session_state.last_user_input = user_input
    st.session_state.last_ai_reply = ai_reply
    st.session_state.last_intent = detected_intent
    st.session_state.last_source = source
    st.session_state.last_memory_id = memory_id
    st.session_state.last_score = score
    st.session_state.last_semantic = semantic
    st.session_state.last_lexical = lexical

for sender, message in st.session_state.chat_history:
    if sender == "Adek":
        st.markdown(
            f'<div class="user-bubble"><b>🩷 {sender}</b><br>{message}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="ai-bubble"><b>🎀 {sender}</b><br>{message}</div>',
            unsafe_allow_html=True,
        )

st.markdown(
    f"""
    <div class="info-card">
        source terakhir: <b>{st.session_state.last_source}</b><br>
        intent terakhir: <b>{st.session_state.last_intent}</b><br>
        total score: <b>{st.session_state.last_score:.2f}</b><br>
        semantic: <b>{st.session_state.last_semantic:.2f}</b> | lexical: <b>{st.session_state.last_lexical:.2f}</b><br>
        mode embedding: <b>{model_status}</b>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🌸 Tentang AI Ini")
    st.write(
        "Versi ini pakai embedding kalau tersedia, jadi AI lebih paham kalimat yang maknanya mirip walau katanya beda."
    )

    st.markdown("### 💕 Cara kerjanya")
    st.write("• baca intent dasar")
    st.write("• hitung semantic similarity")
    st.write("• gabung semantic + lexical + score memory")
    st.write("• auto save kalau hasil memory sangat cocok")

    st.markdown("### ✍️ Koreksi jawaban")
    corrected_reply = st.text_area(
        "Balasan yang lebih mirip gaya kakak",
        value="",
        height=140,
        placeholder="isi versi balasan yang paling benar lalu simpan"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 Cocok"):
            if st.session_state.last_memory_id:
                update_memory_score(st.session_state.last_memory_id, 0.25)
                st.success("score memori dinaikkan")
            else:
                st.info("balasan terakhir belum berasal dari memory")

    with col2:
        if st.button("👎 Kurang Mirip"):
            if st.session_state.last_memory_id:
                update_memory_score(st.session_state.last_memory_id, -0.30)
                st.warning("score memori diturunkan")
            else:
                st.info("balasan terakhir belum berasal dari memory")

    if st.button("💾 Simpan Versi Edit"):
        if st.session_state.last_user_input and corrected_reply.strip():
            save_memory(
                st.session_state.last_user_input,
                corrected_reply.strip(),
                st.session_state.last_intent,
                score=1.7,
                source="manual"
            )
            update_style_profile(corrected_reply.strip())
            st.success("versi edit berhasil disimpan ke memory")
        else:
            st.warning("kirim chat dulu lalu isi versi edit")

    if st.button("🧹 Hapus Chat"):
        st.session_state.chat_history = []
        st.session_state.last_user_input = ""
        st.session_state.last_ai_reply = ""
        st.session_state.last_intent = "general"
        st.session_state.last_source = "rule"
        st.session_state.last_memory_id = None
        st.session_state.last_score = 0.0
        st.session_state.last_semantic = 0.0
        st.session_state.last_lexical = 0.0
        st.rerun()

    st.markdown("### 📚 Statistik")
    total_memories = len(get_candidates(intent=None, limit=500))
    st.write(f"Total memory: **{total_memories}**")
    st.write(f"Embedding model: **{model_status}**")

    if st.session_state.last_ai_reply:
        st.markdown("### ✨ Balasan terakhir")
        st.caption(st.session_state.last_ai_reply)

    #st.markdown("### 🧠 Install tambahan")
    #st.code("pip install streamlit sentence-transformers", language="bash")
