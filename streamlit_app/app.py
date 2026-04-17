"""
NuBI VC Review — 투자 타당성 검토 플랫폼 (Railway 배포용)
5-Stage NuBIZ Framework with Multi-LLM Integration

Pipeline: Input → Analyzer (Phase 1) → Validator (Phase 2) → Reporter → Display
"""
import streamlit as st
print("✓ Streamlit imported")

# Set page config FIRST
st.set_page_config(
    page_title="NuBI VC Review",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)
print("✓ Page config set")

import os
import sys
import pdfplumber
import io
import json
import pandas as pd
from datetime import datetime
from docx import Document
import uuid
print("✓ Standard libraries imported")

# Backend imports
streamlit_dir = os.path.dirname(os.path.abspath(__file__))
service_root = os.path.dirname(streamlit_dir)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

try:
    from backend import Analyzer, Validator, Reporter, SchemaValidator
    print("✓ Backend modules imported")
except ImportError as e:
    st.error(f"Backend import failed: {e}")
    import traceback
    st.write(traceback.format_exc())
    st.stop()

MAX_INPUT_CHARS = 30000
MAX_OUTPUT_TOKENS = 8000

PROVIDER_CONFIGS = {
    "Claude": {
        "label": "Anthropic Claude",
        "env_var": "ANTHROPIC_API_KEY",
        "models": [
            "claude-sonnet-4-20250514",
            "claude-opus-4-1-20250805",
        ],
    },
    "OpenAI": {
        "label": "OpenAI GPT",
        "env_var": "OPENAI_API_KEY",
        "models": [
            "gpt-5.2",
            "gpt-5-mini",
        ],
    },
    "Gemini": {
        "label": "Google Gemini",
        "env_var": "GEMINI_API_KEY",
        "models": [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
        ],
    },
}

# ─── CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;800;900&display=swap');
html, body, [class*="st-"], h1, h2, h3, h4, h5, h6, p, span, div, li, a, button, label {
    font-family: 'Noto Sans KR', sans-serif !important;
}
h1, h2, h3 { font-weight: 700 !important; color: #e8eaf2 !important; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] { background: transparent !important; }
.stDeployButton {display: none;}
label, .stTextInput label, .stTextArea label { color: #e8eaf2 !important; }
p, span, div { color: #c9cdd5; }
[data-testid="stExpander"] summary span { color: #e8eaf2 !important; font-weight: 600 !important; }
[data-testid="stExpander"] [data-testid="stIconMaterial"],
[data-testid="stExpander"] [data-testid="stIconMaterial"] * {
    font-family: 'Material Symbols Rounded' !important;
    font-size: 0 !important;
}
[data-testid="stExpander"] [data-testid="stIconMaterial"]::before {
    content: "\\25B6"; font-family: 'Noto Sans KR', sans-serif !important; font-size: 12px !important;
}
[data-testid="stExpander"][open] [data-testid="stIconMaterial"]::before {
    content: "\\25BC";
}
.block-container { max-width: 780px !important; padding-top: 2rem !important; }

.vc-hero {
    text-align: center; padding: 40px 20px 28px;
    background: linear-gradient(180deg, rgba(245,158,11,0.08) 0%, transparent 100%);
    border-radius: 24px; margin-bottom: 28px;
}
.vc-logo {
    font-size: 2.2rem; font-weight: 900; letter-spacing: 2px;
    background: linear-gradient(135deg, #f59e0b, #ef4444);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.vc-badge {
    display: inline-block; margin-top: 8px; padding: 4px 14px;
    background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.25);
    border-radius: 20px; font-size: 0.72rem; font-weight: 600; color: #f59e0b;
    letter-spacing: 1px;
}
.vc-desc { color: #9ca3af; font-size: 0.85rem; margin-top: 14px; line-height: 1.7; }

.llm-panel {
    margin: 0 0 24px;
    padding: 18px 18px 14px;
    border-radius: 18px;
    border: 1px solid #1e293b;
    background: linear-gradient(180deg, rgba(15,23,42,0.92) 0%, rgba(2,6,23,0.88) 100%);
}
.llm-title {
    font-size: 0.84rem; font-weight: 700; color: #e8eaf2; margin-bottom: 10px;
    letter-spacing: 0.02em;
}
.llm-status-row {
    display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 4px;
}
.llm-status-chip {
    display: inline-flex; align-items: center; gap: 6px;
    border-radius: 999px; padding: 6px 10px; font-size: 0.74rem;
    border: 1px solid #243041; background: rgba(15, 23, 42, 0.75); color: #c9cdd5;
}
.llm-status-chip.ready {
    border-color: rgba(34,197,94,0.35); color: #86efac; background: rgba(34,197,94,0.08);
}
.llm-status-chip.missing {
    border-color: rgba(239,68,68,0.35); color: #fca5a5; background: rgba(239,68,68,0.08);
}
.llm-help {
    color: #94a3b8; font-size: 0.75rem; line-height: 1.6; margin-top: 8px;
}

.step-label {
    display: flex; align-items: center; gap: 10px;
    margin: 24px 0 8px; padding-bottom: 6px;
    border-bottom: 1px solid #1e293b;
}
.step-dot {
    width: 24px; height: 24px; line-height: 24px; text-align: center;
    border-radius: 50%; font-weight: 700; font-size: 0.7rem;
    background: linear-gradient(135deg, #f59e0b, #ef4444); color: #fff;
    flex-shrink: 0;
}
.step-text { font-weight: 600; font-size: 0.88rem; color: #e8eaf2; }

.file-chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2);
    border-radius: 8px; padding: 5px 14px; margin: 3px 4px;
    font-size: 0.78rem; color: #f59e0b; font-weight: 500;
}

.vc-footer {
    text-align: center; padding: 24px 0 8px;
    font-size: 0.72rem; color: #374151;
}
</style>
""", unsafe_allow_html=True)

# ─── Hero ───
st.markdown("""
<div class="vc-hero">
    <div class="vc-logo">NuBI VC Review</div>
    <div class="vc-badge">5-STAGE NUBIZ FRAMEWORK</div>
    <div class="vc-desc">
        IR 자료를 업로드하면 AI가 투자 타당성을 2단계로 검토합니다<br>
        <b>Phase 1</b>: 5-Stage 분석 (원천기술/규제/플랫폼/반복매출/RWW)<br>
        <b>Phase 2</b>: VC 의견 검증 (Phase 1 기반 클레임 평가)
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Beta Warning ───
st.markdown("""
<div style="
    background: linear-gradient(135deg, rgba(239,68,68,0.1) 0%, rgba(239,68,68,0.05) 100%);
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 20px;
    text-align: center;
">
    <span style="color: #fca5a5; font-weight: 600; font-size: 0.88rem;">
        ⚠️ 본 보고서는 내부 검토용 초안입니다. 투자판단 최종 근거로 사용 불가.
    </span>
</div>
""", unsafe_allow_html=True)


def get_provider_api_key(provider: str) -> str:
    env_var = PROVIDER_CONFIGS[provider]["env_var"]
    return os.environ.get(env_var, "").strip()


def get_default_provider() -> str:
    for provider in PROVIDER_CONFIGS:
        if get_provider_api_key(provider):
            return provider
    return "Claude"


def get_selected_model(provider: str, preset_model: str, custom_model: str) -> str:
    return custom_model.strip() or preset_model


def format_provider_status_chips() -> str:
    chips = []
    for provider, config in PROVIDER_CONFIGS.items():
        ready = bool(get_provider_api_key(provider))
        status_class = "ready" if ready else "missing"
        status_text = "API Key 설정됨" if ready else "API Key 없음"
        chips.append(
            f'<span class="llm-status-chip {status_class}">{config["label"]} · {status_text}</span>'
        )
    return "".join(chips)


def extract_pdf_text(file_bytes: bytes) -> str:
    """PDF에서 텍스트 추출"""
    text_parts = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
    except Exception as e:
        text_parts.append(f"(PDF 파싱 오류: {e})")
    return "\n\n".join(text_parts)


def extract_docx_text(file_bytes: bytes) -> str:
    """DOCX에서 텍스트 추출"""
    try:
        document = Document(io.BytesIO(file_bytes))
        parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n".join(parts)
    except Exception as e:
        return f"(DOCX 파싱 오류: {e})"


def build_system_prompt():
    return """당신은 NuBI VC Review — TeamNubiz의 5-Stage NuBIZ 투자 분석 AI입니다.

## 분석 규칙
1. 모든 평가에 구체적 근거(텍스트 인용, 수치 데이터, 위험 요소)를 명시하세요
2. 불확실한 항목은 "확인 필요"로 명시하세요
3. 한국어로 작성, Markdown 표 적극 활용
4. 모델의 일반 지식은 활용 가능하되, 제공 문서 우선
5. 평가 기준: 보수적 관점(downside 중심), IPO/acquisition 실현 가능성 중심"""


def build_user_prompt(company, ir_text, vc_opinion_text=None):
    """Build prompt for 5-stage NuBIZ framework Phase 1 analysis."""
    prompt = f"""## Phase 1: 5-Stage NuBIZ 분석

기업명: {company}

아래 IR 자료를 기반으로 NuBI의 5단계 투자 프레임으로 검토해주세요.
각 단계는 10점 만점, 근거 명시 필수.

### Stage 1: 원천기술통제 (Root Technology Control)
**평가 기준:**
- 기술 차별성과 경쟁력 (vs 기존 솔루션)
- 특허/IP 해자의 강도
- 기술 실현 가능성 (TRL 수준)
- 기술의 지속 가능성 (기술 obsolescence 위험)

**근거:** 특허 명세, 기술 명시, 시장에서의 우위성 데이터

### Stage 2: 규제통제 (Regulatory Pathway)
**평가 기준:**
- 규제 환경의 명확성 (FDA, PMDA, MFDS, CLIA 등)
- 승인 경로의 현실성 (일반/특례/급속경로)
- 규제 위험 수준
- 인허가 타이밍

**근거:** 규제 방침, 승인 경로, 경쟁사 사례

### Stage 3: 플랫폼확장 (Platform Expansion)
**평가 기준:**
- TAM/SAM/SOM 규모 및 성장률
- 시장 진입 타이밍의 적절성
- 적응 가능성 (adjacent markets 확대 가능성)
- 플랫폼화 가능성

**근거:** 시장 규모 데이터, 경합 분석, 확장 계획

### Stage 4: 반복매출 (Recurring Revenue)
**평가 기준:**
- 비즈니스 모델의 건전성 (subscription/disposable/SaaS 등)
- 고객 충성도 및 이탈률 (churn)
- 유닛 이코노믹스 (LTV/CAC)
- 매출 계획의 현실성

**근거:** 고객 계약 구조, 보유율 데이터, 재무 계획

### Stage 5: RWW개입 (Right-Way-to-Win Execution)
**평가 기준:**
- 창업자/경영진 도메인 전문성
- 팀 구성의 완전성 (기술/사업/운영)
- 실행 이력 및 traction
- 자본 효율성 및 경영 역량

**근거:** 이력서, 성과, 이전 exits, 실행 증거

---

## 출력 형식

### 5-Stage 점수표

| Stage | 점수(10) | Grade | 핵심 근거 |
|-------|---------|-------|---------|
| Stage 1 원천기술통제 | X/10 | ? | ... |
| Stage 2 규제통제 | X/10 | ? | ... |
| Stage 3 플랫폼확장 | X/10 | ? | ... |
| Stage 4 반복매출 | X/10 | ? | ... |
| Stage 5 RWW개입 | X/10 | ? | ... |
| **종합** | **X/10** | **?** | **최종 의견** |

**Grade 매핑:** A(9.0+) 강력추천 / B(7.5~8.9) 조건부 / C(5.5~7.4) 추가검증 / D(~5.4) 부적합

각 단계별 2~3문단 상세 분석 작성하세요.

---

## IR 자료

{ir_text[:MAX_INPUT_CHARS]}
"""
    return prompt


def extract_anthropic_text(response) -> str:
    texts = []
    for block in response.content:
        if getattr(block, "type", "") == "text" and getattr(block, "text", ""):
            texts.append(block.text)
    return "\n".join(texts).strip()


def extract_openai_text(response) -> str:
    output_text = getattr(response, "output_text", "")
    if output_text:
        return output_text.strip()

    texts = []
    for item in getattr(response, "output", []) or []:
        for block in getattr(item, "content", []) or []:
            if getattr(block, "type", "") == "output_text" and getattr(block, "text", ""):
                texts.append(block.text)
    return "\n".join(texts).strip()


def call_claude(model: str, system_prompt: str, user_prompt: str, api_key: str) -> str:
    """Anthropic API 호출"""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=MAX_OUTPUT_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return extract_anthropic_text(response)


def call_openai(model: str, system_prompt: str, user_prompt: str, api_key: str) -> str:
    """OpenAI Responses API 호출"""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        instructions=system_prompt,
        input=[{"role": "user", "content": user_prompt}],
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )
    return extract_openai_text(response)


def call_gemini(model: str, system_prompt: str, user_prompt: str, api_key: str) -> str:
    """Gemini API 호출"""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        ),
    )
    return (getattr(response, "text", "") or "").strip()


def call_llm(provider: str, model: str, system_prompt: str, user_prompt: str, progress_callback=None) -> str:
    api_key = get_provider_api_key(provider)
    env_var = PROVIDER_CONFIGS[provider]["env_var"]
    if not api_key:
        raise ValueError(f"{env_var}가 설정되지 않았습니다. Railway 환경변수에 추가하세요.")

    if progress_callback:
        progress_callback(f"{provider} API 호출 중...")

    if provider == "Claude":
        return call_claude(model, system_prompt, user_prompt, api_key)
    if provider == "OpenAI":
        return call_openai(model, system_prompt, user_prompt, api_key)
    if provider == "Gemini":
        return call_gemini(model, system_prompt, user_prompt, api_key)
    raise ValueError(f"지원하지 않는 provider입니다: {provider}")


default_provider = get_default_provider()
default_provider_index = list(PROVIDER_CONFIGS.keys()).index(default_provider)

st.markdown(
    f"""
<div class="llm-panel">
    <div class="llm-title">AI 모델 설정</div>
    <div class="llm-status-row">{format_provider_status_chips()}</div>
    <div class="llm-help">
        기본값은 현재 API Key가 잡혀 있는 provider를 우선 선택합니다. 커스텀 모델 ID를 입력하면 preset 대신 해당 모델을 사용합니다.
    </div>
</div>
""",
    unsafe_allow_html=True,
)

col_llm1, col_llm2 = st.columns(2)
with col_llm1:
    selected_provider = st.selectbox(
        "LLM Provider",
        list(PROVIDER_CONFIGS.keys()),
        index=default_provider_index,
    )
with col_llm2:
    preset_model = st.selectbox(
        "모델",
        PROVIDER_CONFIGS[selected_provider]["models"],
        index=0,
    )

custom_model = st.text_input(
    "커스텀 모델 ID (선택)",
    placeholder="비워두면 위 preset 모델 사용",
)
selected_model = get_selected_model(selected_provider, preset_model, custom_model)
selected_env_var = PROVIDER_CONFIGS[selected_provider]["env_var"]
selected_api_key_ready = bool(get_provider_api_key(selected_provider))

if selected_api_key_ready:
    st.caption(f"{selected_provider} 사용 준비됨 · 환경변수 `{selected_env_var}` 감지됨")
else:
    st.warning(f"{selected_provider}를 사용하려면 환경변수 `{selected_env_var}`를 설정해야 합니다.")


# ─── Step 1: 기업명 ───
st.markdown('<div class="step-label"><div class="step-dot">1</div><div class="step-text">검토 대상 기업명</div></div>', unsafe_allow_html=True)
company_name = st.text_input("기업명", placeholder="예: Surphase, 바이오테크A", label_visibility="collapsed")

# ─── Step 2: IR 자료 ───
st.markdown('<div class="step-label"><div class="step-dot">2</div><div class="step-text">IR 자료 업로드</div></div>', unsafe_allow_html=True)
ir_files = st.file_uploader(
    "IR 데크, 사업계획서 등 (PDF, TXT, DOCX)",
    type=["pdf", "txt", "docx"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)
if ir_files:
    chips = "".join([f'<span class="file-chip">{f.name} ({f.size//1024}KB)</span>' for f in ir_files])
    st.markdown(chips, unsafe_allow_html=True)

# ─── Step 3: VC 의견 ───
st.markdown('<div class="step-label"><div class="step-dot">3</div><div class="step-text">VC 의견 (선택 — Phase 2 재검증용)</div></div>', unsafe_allow_html=True)
vc_opinion = st.text_area(
    "VC 의견",
    placeholder="예: 3D 프린팅 기술의 발전속도가 급속도로 빨라지는 상황에 코팅기반의 무릎 인공관절 시장의 트렌드가 VC내러티브에 맞지 않다고 생각해서 드랍하려고 합니다.\n\n(비워두면 Phase 1만 수행)",
    height=120,
    label_visibility="collapsed",
)

# ─── Step 4: VC 정보 ───
st.markdown('<div class="step-label"><div class="step-dot">4</div><div class="step-text">VC 정보 (선택)</div></div>', unsafe_allow_html=True)
col_vc1, col_vc2 = st.columns(2)
with col_vc1:
    vc_firm = st.text_input("VC/심사역", placeholder="예: 블루포인트 박수용 이사", label_visibility="collapsed")
with col_vc2:
    vc_stage = st.selectbox("투자 단계", ["시드", "프리A", "시리즈A", "시리즈B", "시리즈C+", "기타"], label_visibility="collapsed")

st.markdown("")

# ─── 실행 ───
if "vc_result" not in st.session_state:
    st.session_state.vc_result = None

run_clicked = st.button("검토 시작", type="primary", use_container_width=True)

if run_clicked:
    if not selected_api_key_ready:
        st.error(f"{selected_provider}를 사용하려면 환경변수 `{selected_env_var}`를 먼저 설정하세요")
        st.stop()
    if not company_name:
        st.error("기업명을 입력하세요")
        st.stop()
    if not ir_files:
        st.error("IR 자료를 업로드하세요")
        st.stop()

    # Extract text from uploaded files
    with st.spinner("IR 자료 읽는 중..."):
        all_text = []
        for uf in ir_files:
            lower_name = uf.name.lower()
            if lower_name.endswith(".pdf"):
                text = extract_pdf_text(uf.getvalue())
                all_text.append(f"=== {uf.name} ===\n{text}")
            elif lower_name.endswith(".docx"):
                text = extract_docx_text(uf.getvalue())
                all_text.append(f"=== {uf.name} ===\n{text}")
            else:
                try:
                    text = uf.getvalue().decode("utf-8", errors="replace")
                    all_text.append(f"=== {uf.name} ===\n{text}")
                except Exception:
                    all_text.append(f"=== {uf.name} === (읽기 실패)")

        ir_text = "\n\n".join(all_text)

    # Build structured input_data for backend pipeline
    input_data = {
        "company": {
            "name": company_name,
            "industry": "medtech",  # Default; can be enhanced with user selection
            "stage": vc_stage if vc_stage else "seriesA",
            "founded_year": 2020,  # Default; can be extracted from IR
            "hq_country": "KR",
            "description": ir_text[:200]  # Brief summary
        },
        "analysis_request": {
            "purpose": "ipo_factor_analysis",
            "priority": "high",
            "context": f"VC Review for {company_name}",
            "vc_opinion": vc_opinion if vc_opinion else "",
            "vc_firm": vc_firm if vc_firm else "",
            "previous_analysis_id": None
        },
        "documents": [
            {
                "file_id": f"doc_{i}",
                "filename": uf.name,
                "filetype": uf.name.split(".")[-1].lower(),
                "size_bytes": uf.size,
                "base64_content": __import__('base64').b64encode(uf.getvalue()).decode('utf-8'),
                "doc_type": "ir_deck",
                "confidence": 0.9
            }
            for i, uf in enumerate(ir_files)
        ],
        "quality_flags": {
            "external_validation_done": False,
            "missing_key_info": [],
            "red_flags_already_identified": []
        }
    }

    # Pipeline: Analyzer → Validator (if VC opinion) → Reporter
    try:
        # Phase 1: Analyzer - 5-stage NuBIZ scoring
        with st.spinner("Phase 1: 5-Stage 분석 중..."):
            analyzer = Analyzer()
            analysis_internal = analyzer.analyze(input_data)

        # Phase 2: Validator - assess VC opinion if provided
        if vc_opinion:
            with st.spinner("Phase 2: VC 의견 검증 중..."):
                validator = Validator()
                validation_result = validator.validate(analysis_internal, vc_opinion)
                analysis_internal.update(validation_result)

        # Phase 3: Reporter - generate final report
        with st.spinner("최종 보고서 생성 중..."):
            reporter = Reporter()
            report_result = reporter.generate_report(analysis_internal)

        st.session_state.vc_result = {
            "company": company_name,
            "analysis_internal": analysis_internal,
            "report_final": report_result.get("report_final", {}),
            "markdown": report_result.get("markdown", ""),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "vc_firm": vc_firm,
            "has_phase2": bool(vc_opinion),
            "provider": selected_provider,
            "model": selected_model,
        }
    except Exception as e:
        st.error(f"분석 오류: {str(e)}")
        import traceback
        st.write(traceback.format_exc())

# ─── 결과 표시 ───
if st.session_state.vc_result:
    res = st.session_state.vc_result
    st.markdown("---")

    report_final = res.get("report_final", {})
    analysis_internal = res.get("analysis_internal", {})

    st.markdown(f"### 검토 결과 — {res['company']}")

    if res.get("vc_firm"):
        st.caption(f"VC: {res['vc_firm']} | {res['timestamp']} | {res.get('provider', 'Claude')} · {res.get('model', '')}")
    else:
        st.caption(f"검토일: {res['timestamp']} | {res.get('provider', 'Claude')} · {res.get('model', '')}")

    # Display structured results using tabs
    tabs = ["📊 5-Stage Scorecard", "📋 Executive Summary", "🔧 Framework Status", "📄 Full Report"]
    if res.get("has_phase2"):
        tabs.insert(1, "⚠️ Risk Flags")

    tab_contents = st.tabs(tabs)

    # Tab 1: 5-Stage Scorecard
    with tab_contents[0]:
        scorecard = report_final.get("5stage_scorecard", {})
        if scorecard:
            st.subheader("5-Stage Investment Score")

            # Create scorecard table
            scorecard_data = []
            for stage_key in ["stage_1_원천기술통제", "stage_2_규제통제", "stage_3_플랫폼확장", "stage_4_반복매출", "stage_5_RWW개입"]:
                stage = scorecard.get(stage_key, {})
                score = stage.get("score", 0)
                desc = stage.get("description", "")
                scorecard_data.append({
                    "Stage": stage_key.replace("stage_", "").replace("_", " "),
                    "Score": f"{score}/10",
                    "Description": desc[:60] + "..." if len(desc) > 60 else desc
                })

            df = pd.DataFrame(scorecard_data)
            st.dataframe(df, use_container_width=True)

            overall = scorecard.get("overall_score", 0)
            st.metric("Overall Score", f"{overall}/10")

            # Show evidence for each stage
            with st.expander("📝 Detailed Evidence by Stage"):
                for stage_key in ["stage_1_원천기술통제", "stage_2_규제통제", "stage_3_플랫폼확장", "stage_4_반복매출", "stage_5_RWW개입"]:
                    stage = scorecard.get(stage_key, {})
                    st.write(f"**{stage_key.replace('stage_', '').replace('_', ' ')}**")
                    st.write(f"Score: {stage.get('score', 0)}/10")
                    evidence = stage.get("evidence", [])
                    if evidence:
                        for e in evidence:
                            st.write(f"- {e}")
                    risks = stage.get("risks", [])
                    if risks:
                        st.write("**Risks:**")
                        for r in risks:
                            st.write(f"- {r}")
                    st.divider()

    # Tab 2: Risk Flags (if Phase 2)
    if res.get("has_phase2") and len(tab_contents) > 2:
        tab_idx = 1 if len(tabs) > 3 and tabs[1] == "⚠️ Risk Flags" else 2
        with tab_contents[tab_idx]:
            flags = analysis_internal.get("validator_flags", [])
            if flags:
                st.subheader("Validator Risk Detection")
                for flag in flags:
                    severity = flag.get("severity", "low")
                    severity_icon = {"low": "ℹ️", "medium": "⚠️", "high": "🔴"}
                    st.write(f"{severity_icon.get(severity, '⚠️')} **{flag.get('flag_type', 'Unknown')}** ({severity})")
                    st.write(f"_{flag.get('description', 'No description')}_")
                    if flag.get("must_resolve"):
                        st.warning("Must resolve before proceeding")
            else:
                st.info("No critical flags detected")

    # Tab 3: Executive Summary
    exec_summary_idx = 1 if res.get("has_phase2") else 1
    with tab_contents[exec_summary_idx]:
        exec_summary = report_final.get("executive_summary", {})
        if exec_summary:
            st.subheader(exec_summary.get("headline", company_name))
            st.write(exec_summary.get("investment_case", ""))

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Recommendation", exec_summary.get("key_recommendation", "hold").upper())
            with col2:
                st.metric("Risk Level", exec_summary.get("risk_level", "medium").upper())

            # Engine notice
            if exec_summary.get("engine_notice"):
                st.warning(exec_summary.get("engine_notice"))

    # Tab: Framework Status (v2 Limitations)
    framework_status_idx = None
    for i, tab_name in enumerate(tabs):
        if tab_name == "🔧 Framework Status":
            framework_status_idx = i
            break
    if framework_status_idx is not None:
        with tab_contents[framework_status_idx]:
            st.subheader("Analysis Engine Status (v2)")
            appendix = report_final.get("appendix", {})

            st.write("**Current limitations in v2 framework:**")
            gaps = appendix.get("domain_logic_gaps", [])
            if gaps:
                for gap in gaps:
                    with st.expander(f"ℹ️ {gap.get('item', 'Unknown')}"):
                        st.write(f"**Why:** {gap.get('why', 'N/A')}")
                        st.write(f"**Impact:** {gap.get('impact', 'N/A')}")

            st.info("✅ These limitations are addressed in **v3 (next release)** with full IPO reverse-engineering analysis and Recens Medical pattern integration.")

    # Tab 4: Full Markdown Report
    with tab_contents[-1]:
        st.subheader("Full Analysis Report")
        markdown_report = res.get("markdown", "")
        if markdown_report:
            st.markdown(markdown_report)
        else:
            st.write("Report generation in progress...")

    # Download options
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        markdown_report = res.get("markdown", "")
        st.download_button(
            label="📄 Download Report (Markdown)",
            data=markdown_report,
            file_name=f"{res['company']}_VC검토_{res['timestamp'][:10]}.md",
            mime="text/markdown",
        )

    with col2:
        json_data = json.dumps(analysis_internal, ensure_ascii=False, indent=2)
        st.download_button(
            label="💾 Download Analysis JSON",
            data=json_data,
            file_name=f"{res['company']}_분석데이터_{res['timestamp'][:10]}.json",
            mime="application/json",
        )

# ─── Footer ───
st.markdown("""
<div class="vc-footer">
    NuBI VC Review &mdash; Powered by NUBiPLOT + Multi-LLM API<br>
    &copy; 2026 TeamNubiz
</div>
""", unsafe_allow_html=True)
