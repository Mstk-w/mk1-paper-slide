import streamlit as st
import json
import os
import google.generativeai as genai
from generate_slide import create_a3_slide
import time

# --- Page Config ---
st.set_page_config(layout="wide", page_title="1-Paper Slide Generator", initial_sidebar_state="expanded")

# --- Session State Restoration & Init ---
keys_to_init = {
    "step": 1,  # 1: Setup, 2: Proposal/Edit, 3: Generation
    "slide_json": {},
    "genai_models": ["gemini-1.5-flash", "gemini-1.5-pro"],
    "api_ok": False,
    "theme_mode": "Dark",   # Default Dark
    "topic": "",
    "overview": "",
    "box_count": "AIにおまかせ (Auto)",
    "analysis_result": "",  # 6W3H Result
    "ppt_buffer": None
}
for k, v in keys_to_init.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- Theme & Styling ---
def apply_theme():
    is_dark = st.session_state.theme_mode == "Dark"
    bg_color = "#1e1e1e" if is_dark else "#ffffff"
    text_color = "#e0e0e0" if is_dark else "#333333"
    accent_color = "#4CAF50" # Green for connection
    card_bg = "#2d2d2d" if is_dark else "#f8f9fa"
    shadow = "0 4px 6px rgba(0,0,0,0.3)" if is_dark else "0 2px 5px rgba(0,0,0,0.1)"
    
    
    # CSS Definition
    css = f"""
    <style>
    /* Main Background */
        .stApp {{
            background-color: {bg_color} !important;
        }}

    /* Force text color on all basic elements */
        .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, .stTextInput label, .stTextArea label, .stSelectbox label {{
            color: {text_color} !important;
        }}
        
        /* Input Fields Background & Text */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
            background-color: {card_bg} !important;
            color: {text_color} !important;
            border: 1px solid #ccc; /* Add border for better definition */
        }}
        
        /* Placeholder styling */
        ::placeholder {{
            color: {text_color} !important;
            opacity: 0.7;
        }}
        
        /* Selectbox specific fixes */
        div[data-baseweb="select"] span {{
            color: {text_color} !important;
        }}
        
        .usage-card {{
            background-color: {card_bg};
            padding: 20px;
            border-radius: 10px;
            box-shadow: {shadow};
            margin-bottom: 20px;
        }}
        .step-header {{
            font-size: 1.2rem;
            font-weight: bold;
            color: {text_color} !important;
            margin-bottom: 10px;
            border-bottom: 2px solid {text_color};
            padding-bottom: 5px;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

apply_theme()

# --- Sidebar: Configuration ---
with st.sidebar:
    st.title("⚙️ 設定 (Settings)")
    
    # Theme Toggle
    theme = st.radio("テーマ (Theme)", ["Dark", "Light"], index=0 if st.session_state.theme_mode=="Dark" else 1)
    if theme != st.session_state.theme_mode:
        st.session_state.theme_mode = theme
        st.rerun()

    st.markdown("---")
    
    # API Key
    default_key = st.secrets.get("GEMINI_API_KEY", "")
    api_key = st.text_input("Gemini API Key", value=default_key, type="password", help="Google Cloud Console or AI Studio key")
    
    if st.button("接続テスト & モデル取得 (Connect)"):
        if not api_key:
            st.error("API Keyを入力してください")
        else:
            try:
                genai.configure(api_key=api_key)
                models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        models.append(m.name.replace("models/", ""))
                
                valid_models = sorted([m for m in models if "gemini" in m])
                if valid_models:
                    st.session_state.genai_models = valid_models
                    st.session_state.api_ok = True
                    st.success(f"接続成功! {len(valid_models)}個のモデルを読み込みました")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("有効なGeminiモデルが見つかりませんでした")
            except Exception as e:
                st.session_state.api_ok = False
                st.error(f"接続エラー: {e}")

    # Model Selection
    if st.session_state.api_ok:
        selected_model = st.selectbox("使用モデル (Model)", st.session_state.genai_models, index=0)
    else:
        selected_model = "gemini-1.5-flash" # Fallback
        st.info("API未接続: ダミーモードまたは制限モードで動作します")
        if api_key: genai.configure(api_key=api_key) # Try to configure anyway if key exists

# --- Helper: AI Logic ---
def analyze_and_structure(topic, overview, count_str, model_name):
    """
    1. 6W3H Analysis
    2. JSON Structure Proposal
    """
    if "Auto" in count_str:
        num_instruction = "最適なボックス数（4〜8個）を提案してください。"
    else:
        num = int(count_str.split("個")[0])
        num_instruction = f"必ず【{num}個】のボックス（セクション）で構成してください。"

    prompt = f"""
    あなたは優秀な行政コンサルタント兼資料作成のプロです。
    ユーザーの依頼に基づき、「A3・1枚スライド」の構成案を作成します。

    【依頼内容】
    テーマ: {topic}
    概要・補足: {overview}
    
    【タスク1: 6W3H分析】
    この資料の方向性を定めるため、以下を分析してください。
    - Who（主体）, Whom（ターゲット）, When（時期）, Where（対象範囲）, Why（目的）, What（内容）
    - How（手段）, How much（予算）, How many（規模）
    
    【タスク2: 構成案の作成】
    分析に基づき、スライドの構成（JSON）を作成してください。
    レイアウト要件:
    - 左右2カラム構成（左：現状・課題など / 右：解決策・未来など）。
    - {num_instruction}
    - 各ボックスには「タイトル（label）」と「内容の箇条書きドラフト（text）」を含めます。
    
    【重要な指示：視覚的要素の強化】
    1. **見出しへのアイコン付与**: 各見出し（label）の先頭に、内容を表す適切な「絵文字」を必ず1つ追加してください。（例: "💡 提案", "⚠️ 課題", "📉 現状"）
    2. **図解パターンの指定**: 内容が「手順」「ステップ」「時系列」の場合は、`layout_type`を `"flow_horizontal"` に指定してください。通常の箇条書きは `"text"` とします。

    【出力フォーマット】
    以下のJSON形式のみを出力してください（Markdownコードブロックで囲んでください）。
    {{
        "analysis": "6W3H分析の要約（200文字以内）...",
        "theme": "提案するスライドのタイトル（より魅力的で行政文書として適切なもの）",
        "department": "担当部署名（推定）",
        "content": [
            {{ "column": "left", "label": "📉 01. 背景", "text": "・...", "layout_type": "text" }},
            {{ "column": "left", "label": "⚠️ 02. 課題", "text": "・...", "layout_type": "text" }},
            ...
            {{ "column": "right", "label": "🚀 05. 施策", "text": "Step1: ...", "layout_type": "flow_horizontal" }},
            ...
        ]
    }}
    """
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        txt = response.text
        
        # Extract JSON
        json_str = txt
        if "```json" in txt:
            json_str = txt.split("```json")[1].split("```")[0]
        elif "{" in txt:
            start = txt.find("{")
            end = txt.rfind("}") + 1
            json_str = txt[start:end]
            
        data = json.loads(json_str)
        return data
    except Exception as e:
        st.error(f"AI生成エラー: {e}")
        return None

# --- Main Layout ---

st.title("1ペーパー説明スライド生成 Ver.1.0")
st.caption("AI-Powered Administrative Document Assistant")

# Progress Bar
steps = ["1. Project Setup", "2. AI Analysis & Edit", "3. Download"]
current_progress = (st.session_state.step / 3)
st.progress(current_progress)

# ==========================
# STEP 1: Project Setup
# ==========================
if st.session_state.step == 1:
    with st.container():
        st.markdown('<div class="usage-card"><div class="step-header">STEP 1: どのような資料を作成しますか？</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.session_state.topic = st.text_input("資料タイトル / テーマ (Topic)", 
                                                   value=st.session_state.topic, 
                                                   placeholder="例: 公用車EV化導入計画")
            st.session_state.overview = st.text_area("概要・入れたい要素 (Overview)", 
                                                     value=st.session_state.overview, 
                                                     height=150,
                                                     placeholder="背景：CO2削減目標の達成が必要。\n課題：初期コストが高い。\n解決策：補助金の活用とリース契約。\n目標：2030年までに50%EV化。")
        with col2:
            st.session_state.box_count = st.selectbox("構成ボックス数 (Sections)", 
                                                      ["AIにおまかせ (Auto)", "4個 (シンプル)", "6個 (標準)", "8個 (詳細)"],
                                                      index=0)
            
            st.info("💡 6W3Hフレームワークを用いて、AIが最適な構成を提案します。")
        
        if st.button("AIと壁打ちして構成案を作成 (Start Analysis) 🚀", disabled=not st.session_state.topic):
            if not st.session_state.api_ok:
                st.warning("APIキーが設定されていないか、接続テストを行っていません。ダミーデータを使用する可能性があります。")
            
            with st.spinner("AIが6W3H分析および構成案を作成中..."):
                if st.session_state.api_ok:
                    res = analyze_and_structure(
                        st.session_state.topic, 
                        st.session_state.overview, 
                        st.session_state.box_count,
                        selected_model
                    )
                else:
                    time.sleep(2) # Fake wait
                    res = {
                        "analysis": "API未接続のためダミー分析を表示します。ターゲットは庁内決裁者、目的は予算承認と仮定します。",
                        "theme": st.session_state.topic,
                        "department": "未設定部局",
                        "content": [
                            {"column": "left", "label": "01. 背景", "text": "・ダミーテキスト\n・APIキーを設定してください"},
                            {"column": "left", "label": "02. 課題", "text": "・自動生成機能が使えません"},
                            {"column": "right", "label": "03. 対策", "text": "・サイドバーからKeyを入力"},
                            {"column": "right", "label": "04. 効果", "text": "・AIによる素晴らしい体験"}
                        ]
                    }
                
                if res:
                    st.session_state.slide_json = res
                    st.session_state.step = 2
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# STEP 2: Edit & Refine
# ==========================
elif st.session_state.step == 2:
    with st.container():
        # Header Area
        st.button("← 戻る (Back)", on_click=lambda: st.session_state.update({"step": 1}))
        
        # Analysis Result Display
        if "analysis" in st.session_state.slide_json:
            st.info(f"📊 **AI Analysis (6W3H)**: {st.session_state.slide_json['analysis']}")

        # Meta Info
        c1, c2 = st.columns(2)
        with c1:
            new_theme = st.text_input("タイトル案", value=st.session_state.slide_json.get("theme", ""))
            st.session_state.slide_json["theme"] = new_theme
        with c2:
            new_dept = st.text_input("部局名", value=st.session_state.slide_json.get("department", ""))
            st.session_state.slide_json["department"] = new_dept

        st.divider()

        # Dynamic Columns Editor
        content_items = st.session_state.slide_json.get("content", [])
        
        # Sort/Filter for display
        left_items = [item for item in content_items if item.get("column") == "left"]
        right_items = [item for item in content_items if item.get("column") == "right"]
        if not left_items and not right_items:
            # Fallback for old format or unexpected json
            left_items = content_items[:len(content_items)//2]
            right_items = content_items[len(content_items)//2:]

        col_l, col_r = st.columns(2)
        
        with col_l:
            st.subheader("Left Column (Why/What)")
            for i, item in enumerate(left_items):
                with st.expander(f"{item.get('label', 'Section')}", expanded=True):
                    item["label"] = st.text_input(f"見出し #{i+1}L", value=item.get("label", ""))
                    item["text"] = st.text_area(f"内容 #{i+1}L", value=item.get("text", ""), height=120)

        with col_r:
            st.subheader("Right Column (How/Future)")
            for i, item in enumerate(right_items):
                with st.expander(f"{item.get('label', 'Section')}", expanded=True):
                    item["label"] = st.text_input(f"見出し #{i+1}R", value=item.get("label", ""))
                    item["text"] = st.text_area(f"内容 #{i+1}R", value=item.get("text", ""), height=120)

        # Re-save to session
        # (References in list are mutable, so st.session_state.slide_json is already updated,
        # but explicit re-assignment ensures Streamlit catches it if needed)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("✨ スライドを生成する (Generate PPTX)", type="primary", use_container_width=True):
            with st.spinner("PowerPointをレンダリング中..."):
                try:
                    # Convert list-based content back to dict if generate_slide expects it?
                    # Actually, I should update generate_slide to handle this list format OR 
                    # create a temporary adapter.
                    # For now, let's keep the JSON structure clean as a dict for legacy compat OR list.
                    # Wait, the PLAN said "Dynamic inputs". The existing generate_slide expects specific keys (box1...).
                    # I MUST UPDATE generate_slide.py to handle this new list-based dynamic JSON.
                    # For this step, I will assume generate_slide will be updated next.
                    
                    from datetime import datetime
                    today_str = datetime.now().strftime("%Y%m%d")
                    safe_title = st.session_state.slide_json.get("theme", "Untitled").replace(" ", "_").replace("/", "-")
                    output_path = "output_slide.pptx"
                    download_filename = f"{today_str}_{safe_title}.pptx"
                    
                    create_a3_slide(st.session_state.slide_json, output_path)
                    
                    with open(output_path, "rb") as f:
                        st.session_state.ppt_buffer = f.read()
                        st.session_state.download_filename = download_filename # Store for button
                    
                    st.session_state.step = 3
                    st.rerun()
                except Exception as e:
                    st.error(f"生成エラー: {e}")

# ==========================
# STEP 3: Download
# ==========================
elif st.session_state.step == 3:
    st.balloons()
    st.markdown('<div class="usage-card"><div class="step-header">🎉 完成しました (Complete)</div>', unsafe_allow_html=True)
    st.success("スライドの生成が完了しました！")
    
    
    if st.session_state.ppt_buffer:
        st.download_button(
            label="📥 PowerPointファイルをダウンロード (.pptx)",
            data=st.session_state.ppt_buffer,
            file_name=st.session_state.get("download_filename", "generated_slide.pptx"),
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            type="primary"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("最初に戻る (Create Another)"):
        st.session_state.step = 1
        st.session_state.slide_json = {}
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
