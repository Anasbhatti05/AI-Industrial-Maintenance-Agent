import streamlit as st
from app.config import APP_NAME, OPENAI_API_KEY, GROQ_API_KEY
from app.agent import analyze_issue

st.set_page_config(page_title=APP_NAME, page_icon='🛠️', layout='wide')


def render_result_overview(result: dict) -> None:
    severity = str(result.get('severity', 'Medium')).strip() or 'Medium'
    priority = int(result.get('priority_score', 0) or 0)
    severity_color = {
        'Low': '#22c55e',
        'Medium': '#f59e0b',
        'High': '#f97316',
        'Critical': '#ef4444',
    }.get(severity, '#60a5fa')
    knowledge_text = result.get('knowledge_summary', '')
    llm_text = result.get('llm_summary', '')

    st.markdown(
        f"""
        <div class='glass' style='margin-top: 1rem; margin-bottom: 1rem;'>
          <div style='display:flex; justify-content:space-between; align-items:center; gap:0.8rem; flex-wrap:wrap; margin-bottom: 0.8rem;'>
            <h3 style='margin:0; color:#f8fbff;'>Maintenance diagnosis overview</h3>
            <span class='status-pill' style='background: rgba(15,23,42,0.8); border: 1px solid {severity_color}; color: {severity_color};'> {severity} </span>
          </div>
          <div class='summary-grid'>
            <div class='summary-item'>
              <div class='summary-label'>Severity</div>
              <div class='summary-value'>{severity}</div>
            </div>
            <div class='summary-item'>
              <div class='summary-label'>Priority Score</div>
              <div class='summary-value'>{priority}/100</div>
            </div>
            <div class='summary-item'>
              <div class='summary-label'>Known Matches</div>
              <div class='summary-value'>{len(result.get('matches', []))}</div>
            </div>
            <div class='summary-item'>
              <div class='summary-label'>Manual Context</div>
              <div class='summary-value'>{'Yes' if knowledge_text else 'No'}</div>
            </div>
          </div>
          <div style='margin-top: 0.9rem; color: #dfeafc; line-height: 1.6;'>{(llm_text[:500] + '...') if len(llm_text) > 500 else llm_text or knowledge_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #071425 0%, #0e1d31 32%, #111827 100%) !important;
        color: #edf4ff !important;
    }
    [data-testid="stHeader"] {
        background: rgba(8, 15, 26, 0.8) !important;
        top: 0.25rem !important;
        box-shadow: none !important;
    }
    .main { background: transparent !important; }
    .block-container { padding-top: 2.4rem !important; padding-bottom: 2rem; max-width: 1360px; }
    @media (max-width: 768px) {
        .block-container { padding-left: 0.6rem !important; padding-right: 0.6rem !important; }
        .topbar { padding: 0.8rem 0.9rem !important; border-radius: 14px !important; }
        .brand { font-size: 1rem !important; width: 100% !important; justify-content: center !important; }
        .hero-inner { flex-direction: column !important; align-items: flex-start !important; }
        .hero-card { width: 100% !important; min-width: 0 !important; }
        .hero-text h1 { font-size: clamp(1.6rem, 8vw, 2.3rem) !important; }
        .summary-grid { grid-template-columns: repeat(2, minmax(120px, 1fr)) !important; }
        [data-testid="stHorizontalBlock"] { gap: 0.5rem !important; }
        [data-testid="stHorizontalBlock"] > div { width: 100% !important; min-width: 0 !important; }
        .stButton > button { width: 100% !important; font-size: 0.8rem !important; padding: 0.7rem 0.9rem !important; }
        .stTabs [role="tab"] { font-size: 0.75rem !important; padding: 0.55rem 0.7rem !important; }
        .glass { padding: 0.9rem 0.85rem !important; }
    }
    .topbar {
        background: rgba(9, 17, 29, 0.78);
        border: 1px solid rgba(148, 163, 184, 0.2);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 1.1rem 1.3rem;
        margin-top: 0.75rem;
        margin-bottom: 1.6rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 12px 30px rgba(2, 6, 23, 0.4);
    }
    .brand {
        display: flex; align-items: center; gap: 0.8rem; font-size: 1.4rem; font-weight: 800; color: #f8fbff;
    }
    .brand-badge {
        width: 42px; height: 42px; border-radius: 14px; background: linear-gradient(135deg, #60a5fa, #2563eb, #1d4ed8);
        display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 30px rgba(37, 99, 235, 0.5); font-size: 1.2rem;
    }
    .hero {
        position: relative; background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(37, 99, 235, 0.2), rgba(15, 118, 110, 0.18));
        border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 24px; padding: 1.5rem 1.4rem; box-shadow: 0 18px 46px rgba(2, 6, 23, 0.5); overflow: hidden; margin-bottom: 1rem;
    }
    .hero::before {
        content: ""; position: absolute; width: 400px; height: 400px; right: -80px; top: -120px;
        background: radial-gradient(circle, rgba(96,165,250,0.45), transparent 60%); filter: blur(8px); animation: float 12s ease-in-out infinite;
    }
    .hero::after {
        content: ""; position: absolute; width: 300px; height: 300px; left: -80px; bottom: -150px;
        background: radial-gradient(circle, rgba(45,212,191,0.24), transparent 65%); filter: blur(10px); animation: float 16s ease-in-out infinite reverse;
    }
    .hero-inner { position: relative; z-index: 1; display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
    .hero-text h1 { margin: 0; font-size: clamp(2rem, 4vw, 3.2rem); line-height: 1.1; color: #f8fbff !important; }
    .hero-sub { margin-top: 0.7rem; color: #d7ebff !important; font-size: 1.02rem; opacity: 0.9; }
    .hero-card {
        background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(148, 163, 184, 0.25); border-radius: 18px;
        padding: 1rem 1.1rem; min-width: 260px; box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
    }
    .hero-card .mini-title { font-size: 0.76rem; letter-spacing: 0.08em; color: #9dc3ff; text-transform: uppercase; margin-bottom: 0.5rem; }
    .hero-card .mini-value { font-size: 2rem; font-weight: 800; color: #f8fbff !important; }
    .glass {
        background: linear-gradient(180deg, rgba(15,23,42,0.95), rgba(17,24,39,0.82)); border: 1px solid rgba(148,163,184,0.18);
        border-radius: 18px; padding: 1.2rem 1.3rem; box-shadow: 0 12px 30px rgba(2, 6, 23, 0.35);
        transition: transform 0.25s ease, box-shadow 0.25s ease; animation: fadeUp 0.8s ease-out; word-wrap: break-word; overflow-wrap: anywhere;
    }
    .glass:hover { transform: translateY(-3px); box-shadow: 0 18px 40px rgba(37,99,235,0.18); }
    .summary-grid { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 0.8rem; margin-top: 0.2rem; }
    .summary-item { background: rgba(15, 23, 42, 0.70); border: 1px solid rgba(148, 163, 184, 0.18); border-radius: 14px; padding: 0.8rem 0.9rem; min-height: 82px; }
    .summary-label { color: #9dc3ff; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; font-weight: 700; }
    .summary-value { color: #f8fbff; font-size: 1.35rem; font-weight: 800; }
    .status-pill { display: inline-flex; align-items: center; justify-content: center; border-radius: 999px; padding: 0.38rem 0.8rem; font-weight: 800; font-size: 0.82rem; letter-spacing: 0.04em; text-transform: uppercase; }
    .styled-upload { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(96, 165, 250, 0.4); border-radius: 18px; padding: 0.2rem 0.25rem 0.4rem; }
    div[data-testid="stFileUploaderDropzone"] { border: 2px dashed rgba(96, 165, 250, 0.7) !important; border-radius: 16px !important; background: rgba(255, 255, 255, 0.96) !important; min-height: 110px !important; box-shadow: inset 0 1px 1px rgba(15, 23, 42, 0.05); }
    div[data-testid="stFileUploaderDropzone"] > div, div[data-testid="stFileUploaderDropzone"] p, div[data-testid="stFileUploaderDropzone"] span, div[data-testid="stFileUploaderDropzone"] strong { color: #0f172a !important; font-weight: 700; }
    .stFileUploader label, .stTextInput label, .stTextArea label, .stNumberInput label { color: #f8fbff !important; font-weight: 700; }
    .stFileUploader button, [data-testid="baseButton-secondary"] { background: linear-gradient(180deg, #edf6ff, #dfeafd) !important; color: #0f172a !important; border: 1px solid rgba(96, 165, 250, 0.6) !important; font-weight: 700 !important; border-radius: 10px !important; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stNumberInput > div > div > input { background: rgba(255, 255, 255, 0.96) !important; color: #111827 !important; border: 1px solid rgba(148, 163, 184, 0.75) !important; border-radius: 12px !important; padding: 0.8rem 0.9rem !important; font-size: 1rem !important; font-weight: 500 !important; box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.06) !important; min-height: 48px !important; }
    .stTextArea > div > div > textarea { min-height: 130px !important; }
    .stTextInput > div > div > input::placeholder, .stTextArea > div > div > textarea::placeholder { color: #4b5563 !important; opacity: 0.9; }
    .stAlert, .stInfo, .stSuccess, .stWarning { border-radius: 14px; background: rgba(15, 23, 42, 0.86); border: 1px solid rgba(148,163,184,0.2); }
    .stTabs [role="tablist"] { gap: 0.6rem; }
    .stTabs [role="tab"] { background: rgba(148,163,184,0.10); border-radius: 10px 10px 0 0; padding: 0.68rem 1rem; border: 1px solid rgba(148,163,184,0.14); color: #dfeafc !important; font-weight: 600; }
    .stTabs [role="tab"][aria-selected="true"] { background: linear-gradient(135deg, #2f6fe4, #1f5fe0); color: white !important; box-shadow: 0 8px 24px rgba(37,99,235,0.35); }
    .stButton > button { background: linear-gradient(90deg, #60a5fa, #2563eb 52%, #1d4ed8); color: white !important; border: none; border-radius: 12px; font-weight: 800; padding: 0.82rem 1.5rem; box-shadow: 0 10px 24px rgba(37,99,235,0.35); transition: transform 0.2s ease, box-shadow 0.2s ease; min-height: 46px; }
    .stButton > button:hover { transform: translateY(-1px) scale(1.01); box-shadow: 0 14px 28px rgba(37,99,235,0.45); }
    div[data-testid="stFormSubmitButton"] > button { width: 100% !important; justify-content: center !important; }
    .footer { margin-top: 1.3rem; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-top: 0.9rem; color: #cfe0ff; font-size: 0.9rem; opacity: 0.85; text-align: center; }
    @keyframes fadeUp { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes float { 0%, 100% { transform: translateY(0px) translateX(0px); } 50% { transform: translateY(-18px) translateX(15px); } }
    </style>
    """,
    unsafe_allow_html=True,
)

nav_labels = ['Dashboard', 'Diagnosis', 'Maintenance', 'Reports']
if 'active_nav' not in st.session_state:
    st.session_state.active_nav = 'dashboard'

nav_map = {'Dashboard': 'dashboard', 'Diagnosis': 'diagnosis', 'Maintenance': 'maintenance', 'Reports': 'reports'}

st.markdown(
    """
    <div class='topbar'>
      <div class='brand'>
        <div class='brand-badge'>⚙️</div>
        <span>AI Industrial Maintenance Agent</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

nav_cols = st.columns(4)
for i, label in enumerate(nav_labels):
    with nav_cols[i]:
        key = f"nav_{label}_{i}"
        is_active = nav_map.get(label) == st.session_state.active_nav
        clicked = st.button(label, key=key, use_container_width=True, type='primary' if is_active else 'secondary')
        if clicked:
            st.session_state.active_nav = nav_map.get(label, 'dashboard')

current_nav = st.session_state.active_nav
active_label = {'dashboard': 'Dashboard', 'diagnosis': 'Diagnosis', 'maintenance': 'Maintenance', 'reports': 'Reports'}.get(current_nav, 'Dashboard')

st.markdown(f"<div class='glass' style='padding: 0.7rem 0.9rem; margin: 0.8rem 0 1rem;'><strong>Active section:</strong> {active_label}</div>", unsafe_allow_html=True)

hero_title = 'Smarter maintenance decisions for industrial operations.'
hero_sub = 'AI-powered troubleshooting across equipment faults, manuals, and historical repair knowledge.'
hero_status = 'Live status'
hero_readiness = 'System readiness'

st.markdown(
    f"""
    <div id='dashboard-panel' class='hero'>
      <div class='hero-inner'>
        <div class='hero-text'>
          <h1>{hero_title}</h1>
          <div class='hero-sub'>{hero_sub}</div>
        </div>
        <div class='hero-card'>
          <div class='mini-title'>{hero_status}</div>
          <div class='mini-value'>98.4%</div>
          <div style='color:#dbeafe; font-size:0.9rem; opacity:0.8;'>{hero_readiness}</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if OPENAI_API_KEY or GROQ_API_KEY:
    provider = 'Groq' if GROQ_API_KEY and not OPENAI_API_KEY else 'OpenAI'
    st.success(f'{provider} integration is enabled for richer summaries.')
else:
    st.info('No API key is set. The app is running in knowledge-base fallback mode.')

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class='glass'>
    <h3>Problem we solve</h3>
    <p>Industrial teams waste time diagnosing faults manually across equipment logs, manuals, and repetitive plant issues.</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class='glass'>
    <h3>What this app does</h3>
    <p>It matches real machine issues against a maintenance knowledge base and PDF manuals to suggest likely causes and next actions.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class='glass' style='padding: 0.9rem 1rem; margin-top: 0.5rem;'>
  <strong style='color:#dfeafc;'>How to test:</strong>
  <div style='margin-top:0.35rem; color:#dfeafc;'>1. Enter the equipment name<br>2. Describe the issue<br>3. Upload a PDF if available<br>4. Click <span style="color:#8ec5ff; font-weight:700;">Analyze issue</span></div>
</div>
""", unsafe_allow_html=True)
st.markdown('---')

st.markdown("<div id='diagnosis-panel'></div>", unsafe_allow_html=True)

st.markdown("<div class='glass' style='padding: 0.5rem 0.8rem 0.8rem;'><h3 style='margin:0 0 0.4rem;'>Upload maintenance manuals (PDF)</h3></div>", unsafe_allow_html=True)

with st.form('issue_form'):
    uploaded_files = st.file_uploader('Upload maintenance manuals (PDF)', type=['pdf'], accept_multiple_files=True, label_visibility='collapsed')
    equipment = st.text_input('Equipment / Machine Name', placeholder='e.g. Industrial Motor', key='equipment_input')
    issue = st.text_area('Describe the maintenance issue', placeholder='e.g. Motor is overheating and making noise', key='issue_input')

    st.markdown("<div class='styled-upload'>", unsafe_allow_html=True)
    image_file = st.file_uploader('Upload equipment image (PNG/JPG)', type=['png', 'jpg', 'jpeg'], accept_multiple_files=False)
    camera_photo = st.camera_input('Or capture a live photo from camera')
    if image_file is not None:
        st.image(image_file, caption='Uploaded equipment image', use_container_width=True)
    if camera_photo is not None:
        st.image(camera_photo, caption='Captured equipment photo', use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    submitted = st.form_submit_button('Analyze issue', use_container_width=True)

if submitted:
    if not equipment or not issue:
        st.warning('Please enter both equipment and issue details.')
    else:
        result = analyze_issue(issue, equipment, files=uploaded_files or [])
        st.success(f'Issue analysis for: {equipment}')

        metric_cols = st.columns(4)
        with metric_cols[0]:
            st.metric('Severity', result.get('severity', 'Medium'))
        with metric_cols[1]:
            st.metric('Priority Score', f"{result.get('priority_score', 0)}/100")
        with metric_cols[2]:
            st.metric('Known Matches', len(result.get('matches', [])))
        with metric_cols[3]:
            st.metric('Manual Files', len(uploaded_files or []))

        render_result_overview(result)

        st.subheader('Knowledge base match')
        st.info(result['knowledge_summary'])

        if result.get('llm_summary'):
            st.subheader('AI summary')
            st.write(result['llm_summary'])

        st.subheader('Possible causes')
        for cause in result['possible_causes']:
            st.markdown(f'- {cause}')

        st.subheader('Recommended actions')
        for action in result['recommended_actions']:
            st.markdown(f'- {action}')

        if result['matches']:
            st.subheader('Similar historical cases')
            for match in result['matches']:
                st.markdown(f"- **{match.get('Machine', '')}** | {match.get('Fault / Incident', '')} | Severity: {match.get('Severity', '')}")
                if match.get('Troubleshooting Guidance'):
                    st.write(match.get('Troubleshooting Guidance'))

        st.subheader('Issue summary')
        st.write(result['issue_summary'])

st.markdown('---')
st.caption('Built for demo impact, industrial relevance, and fast maintenance diagnosis.')

st.markdown(
    """
    <div class='footer'>
      AI Industrial Maintenance Agent • Built for factories, maintenance teams, and operational reliability
    </div>
    """,
    unsafe_allow_html=True,
)
