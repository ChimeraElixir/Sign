import streamlit as st
import sqlite3
import tempfile
from pathlib import Path
from typing import Optional

try:
    from inference_sdk import InferenceHTTPClient
except ImportError:
    InferenceHTTPClient = None

def get_db_connection():
    conn = sqlite3.connect("sign_language.db")
    conn.row_factory = sqlite3.Row
    return conn

# Set page config for a wider layout
st.set_page_config(layout="wide", page_title="Sign Language Translator", page_icon="🤟")

st.markdown("<h1 style='text-align: center;'>🤟 Sign Language Translator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray; font-size: 1.2rem;'>Seamlessly translate between English text and Sign Language.</p>", unsafe_allow_html=True)
st.divider()

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "static" 
ROBOFLOW_API_URL = "https://serverless.roboflow.com"
ROBOFLOW_API_KEY = "uHq3AKnSX4ferar0SXnE"
ROBOFLOW_MODEL_ID = "american-sign-language-v36cz/1"

if InferenceHTTPClient is not None:
    CLIENT = InferenceHTTPClient(
        api_url=ROBOFLOW_API_URL,
        api_key=ROBOFLOW_API_KEY
    )
else:
    CLIENT = None

def get_prediction_list(result):
    """Handle multiple Roboflow response shapes and return a prediction list."""
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]

    if not isinstance(result, dict):
        return []

    direct = result.get("predictions")
    if isinstance(direct, list):
        return [item for item in direct if isinstance(item, dict)]
    if isinstance(direct, dict):
        nested = direct.get("predictions")
        if isinstance(nested, list):
            return [item for item in nested if isinstance(item, dict)]

    # Fallback: search recursively for the first plausible prediction list.
    for value in result.values():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            if "class" in value[0] or "class_name" in value[0]:
                return value
        if isinstance(value, dict):
            nested = get_prediction_list(value)
            if nested:
                return nested

    return []


def resolve_image_path(img_name: str) -> Optional[str]:
    """Resolve DB image names to a real file path for Streamlit."""
    candidates = [
        BASE_DIR / img_name,
        BASE_DIR / "static" / img_name,
        IMAGE_DIR / img_name,
    ]

    # If DB value already includes "images/" or other relative dirs, try it directly.
    if "/" in img_name or "\\" in img_name:
        candidates.insert(0, BASE_DIR / Path(img_name))

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def extract_predictions(result):
    """Extract all predictions from Roboflow infer() output."""
    predictions = []
    for item in get_prediction_list(result):
        if not isinstance(item, dict):
            continue
        class_name = item.get("class") or item.get("class_name")
        confidence = item.get("confidence")
        if isinstance(class_name, str) and class_name.strip():
            predictions.append({
                "label": class_name.strip(),
                "confidence": confidence if isinstance(confidence, (int, float)) else None
            })
    return predictions

def run_sign_to_text_inference(uploaded_file):
    if CLIENT is None:
        return {
            "error": "Inference SDK not installed. Install it with: pip install inference-sdk"
        }

    suffix = Path(uploaded_file.name).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_path = temp_file.name

    try:
        result = CLIENT.infer(temp_path, model_id=ROBOFLOW_MODEL_ID)
        predictions = extract_predictions(result)
        all_labels = [pred["label"] for pred in predictions]

        return {
            "raw": result,
            "predictions": predictions,
            "text": " ".join(all_labels) if all_labels else "No labels detected."
        }
    finally:
        Path(temp_path).unlink(missing_ok=True)

# Fetch data from the database at startup
conn = get_db_connection()
try:
    signs = conn.execute('SELECT text, image FROM signs WHERE type = "alphabet"').fetchall()
except sqlite3.OperationalError:
    # Initialize the database if the table doesn't exist (e.g., on Streamlit Cloud)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS signs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT UNIQUE,
        image TEXT,
        type TEXT
    )
    """)
    data = [
        ('a','a.jpg','alphabet'), ('b','b.png','alphabet'), ('c','c.png','alphabet'), ('d','d.png','alphabet'), ('e','e.png','alphabet'), ('f','f.jpg','alphabet'), ('g','g.png','alphabet'), ('h','h.jpg','alphabet'), ('i','i.png','alphabet'), ('j','j.png','alphabet'), ('k','k.jpg','alphabet'), ('l','l.png','alphabet'), ('m','m.png','alphabet'), ('n','n.png','alphabet'), ('o','o.jpg','alphabet'), ('p','p.jpg','alphabet'), ('q','q.png','alphabet'), ('r','r.png','alphabet'), ('s','s.png','alphabet'), ('t','t.jpg','alphabet'), ('u','u.jpg','alphabet'), ('v','v.jpg','alphabet'), ('w','w.png','alphabet'), ('x','x.png','alphabet'), ('y','y.jpg','alphabet'), ('z','z.png','alphabet'),
        ("hello", "hello.gif", "word"), ("good", "good.png", "word"), ("rainbow", "rainbow.png", "word")
    ]
    conn.executemany("INSERT OR IGNORE INTO signs (text, image, type) VALUES (?, ?, ?)", data)
    conn.commit()
    signs = conn.execute('SELECT text, image FROM signs WHERE type = "alphabet"').fetchall()

conn.close()
alphabet_dict = {sign["text"]: sign["image"] for sign in signs}

# Create two columns for Input and Output
col_input, col_output = st.columns([1, 1], gap="large")

with col_input:
    st.subheader("⚙️ Translation Mode")
    
    # Create a row with options using a horizontal radio button
    mode = st.radio(
        "Select Translation Mode:",
        ("Text to Sign", "Sign to Text"),
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("### 📥 Input")

    if mode == "Text to Sign":
        user_text = st.text_area("Enter text to translate:", placeholder="Type a word or phrase here...")
        if st.button("🚀 Translate to Sign", type="primary", use_container_width=True):
            typed_text = user_text.lower()
            sentence_results = []
            
            # Find matching images for each typed character
            for ch in typed_text:
                if ch in alphabet_dict:
                    sentence_results.append(alphabet_dict[ch])
            
            # Store results in session_state to share with output column
            st.session_state['mode'] = "text_to_sign"
            st.session_state['user_text'] = typed_text
            st.session_state['images'] = sentence_results
            
    elif mode == "Sign to Text":
        uploaded_file = st.file_uploader("Upload a sign language image", type=["jpg", "png", "jpeg"])
            
        if uploaded_file:
            st.image(uploaded_file, caption="Image Preview", width=350)
        if st.button("🔍 Analyze Sign", type="primary", use_container_width=True):
            st.session_state['mode'] = "sign_to_text"
            if not uploaded_file:
                st.session_state['sign_result'] = {"error": "Please upload an image first."}
            else:
                try:
                    st.session_state['sign_result'] = run_sign_to_text_inference(uploaded_file)
                except Exception as exc:
                    st.session_state['sign_result'] = {"error": f"Inference failed: {exc}"}

with col_output:
    st.subheader("✨ Translation Result")

    if 'mode' in st.session_state:
        if st.session_state['mode'] == "text_to_sign" and mode == "Text to Sign":
            st.success(f"Showing sign images for: **{st.session_state['user_text']}**")
            
            images = st.session_state['images']
            if images:
                # Create a grid layout of 5 columns per row to display images side-by-side
                cols = st.columns(5)
                for i, img_name in enumerate(images):
                    img_path = resolve_image_path(img_name)
                    if img_path:
                        cols[i % 5].image(img_path, width=80)
                    else:
                        cols[i % 5].warning(f"Missing: {img_name}")
            else:
                st.warning("No translatable characters found. Try typing alphabet letters.")
        elif st.session_state['mode'] == "sign_to_text" and mode == "Sign to Text":
            result = st.session_state.get("sign_result", {})
            if result.get("error"):
                st.error(result["error"])
            else:
                st.subheader("Prediction")
                st.success(result.get("text", "No labels detected."))
                predictions = result.get("predictions", [])
                if predictions:
                    st.markdown("#### Detected Classes:")
                    for pred in predictions:
                        if pred["confidence"] is None:
                            st.markdown(f"- **{pred['label']}**")
                        else:
                            pc1, pc2 = st.columns([1, 3])
                            pc1.markdown(f"**{pred['label']}**")
                            pc2.progress(float(pred['confidence']), text=f"{pred['confidence']*100:.1f}%")
                with st.expander("Show raw workflow output"):
                    st.json(result.get("raw", {}))
        else:
            st.info("Translation output will appear here.")
    else:
        st.info("Translation output will appear here.")
