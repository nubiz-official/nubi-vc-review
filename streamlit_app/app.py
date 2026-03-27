"""
NuBI VC Review — 투자 타당성 검토 플랫폼 (Railway 배포용)
Anthropic API 직접 사용 (Claude CLI 불필요)

2단계 분석:
  Phase 1: 사업성 검토 (시장/솔루션/팀/스케일업)
  Phase 2: VC 의견 재검증 (Phase 1 기반)
"""
import streamlit as st
import os
import json
import pdfplumber
import io
from datetime import datetime

st.set_page_config(
    page_title="NuBI VC Review",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

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
    <div class="vc-badge">INVESTMENT DUE DILIGENCE</div>
    <div class="vc-desc">
        IR 자료를 업로드하면 AI가 투자 타당성을 2단계로 검토합니다<br>
        <b>Phase 1</b>: 사업성 검토 (시장/솔루션/팀/스케일업)<br>
        <b>Phase 2</b>: VC 의견 재검증 (Phase 1 기반 논리 검증)
    </div>
</div>
""", unsafe_allow_html=True)


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


def build_system_prompt():
    return """당신은 NuBI VC Review — TeamNubiz의 투자 타당성 검토 AI입니다.

## 분석 규칙
1. Phase 1을 먼저 완료한 후 Phase 2를 수행하세요
2. 모든 주장에는 근거(데이터, 출처)를 명시하세요
3. 불확실한 항목은 "확인 필요"로 명시하세요
4. 한국어로 작성하세요
5. Markdown 표를 적극 활용하세요"""


def build_user_prompt(company, ir_text, vc_opinion_text, vc_firm_text, vc_stage_text):
    phase1 = f"""## Phase 1: 사업성 검토

기업명: {company}
투자 단계: {vc_stage_text}

아래 IR 자료를 기반으로 4가지 관점에서 투자 타당성을 검토해주세요.
각 항목은 10점 만점으로 평가하고, 근거를 명시하세요.

### 1.1 시장 (Market / Unmet Needs)
- TAM/SAM/SOM 규모와 성장률 (IR 자료 기반 + 당신의 지식으로 검증)
- 언맷니즈의 명확성과 심각도
- 시장 진입 타이밍
- 규제 환경

### 1.2 솔루션 (Solution / 기술 타당성)
- 기술 차별성 (vs 기존 솔루션)
- 기술 실현 가능성 (TRL 수준)
- 특허/IP 해자
- 확장성

### 1.3 팀 (Team / 창업자 역량)
- 창업자 도메인 전문성
- 팀 구성 완전성 (기술/사업/운영)
- 실행 이력 (traction)
- 어드바이저/네트워크

### 1.4 스케일업 (Scale-up / 매출-손익 전망)
- 비즈니스 모델 건전성
- 매출 계획의 현실성
- 유닛 이코노믹스
- 손익분기점 시기

### 출력 형식

각 항목을 아래 표로 정리하세요:

| 항목 | 점수(10) | 핵심 근거 |
|------|---------|---------|
| 시장 | X/10 | ... |
| 솔루션 | X/10 | ... |
| 팀 | X/10 | ... |
| 스케일업 | X/10 | ... |
| **종합** | **X/10** | **등급: A/B/C/D** |

투자 등급: A(8.0+) 적극추천 / B(6.5~7.9) 조건부 / C(5.0~6.4) 추가검증 / D(5.0 미만) 부적합

그리고 각 항목에 대해 2~3문단으로 상세 분석을 작성하세요.

---

## IR 자료 전문

{ir_text[:30000]}
"""

    phase2 = ""
    if vc_opinion_text:
        phase2 = f"""

---

## Phase 2: VC 의견 재검증

{vc_firm_text or 'VC'}가 다음과 같은 의견을 제시했습니다:

> {vc_opinion_text}

Phase 1 분석 결과를 바탕으로 이 의견의 타당성을 검증해주세요.

### 검증 방법
1. VC의 주장을 개별 논점으로 분리
2. 각 논점을 Phase 1 데이터와 대조
3. 타당/부분타당/비타당 판정 + 근거

| VC 논점 | 판정 | 근거 (Phase 1 참조) |
|---------|------|-------------------|

### 최종 권고
VC의 드랍/투자 판단에 대한 종합 의견을 제시하세요.
"""

    return phase1 + phase2


def call_claude(system_prompt: str, user_prompt: str, progress_callback=None) -> str:
    """Anthropic API 직접 호출"""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "오류: ANTHROPIC_API_KEY가 설정되지 않았습니다. Railway 환경변수에 추가하세요."

    client = anthropic.Anthropic(api_key=api_key)

    if progress_callback:
        progress_callback("Claude API 호출 중...")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text


# ─── Step 1: 기업명 ───
st.markdown('<div class="step-label"><div class="step-dot">1</div><div class="step-text">검토 대상 기업명</div></div>', unsafe_allow_html=True)
company_name = st.text_input("기업명", placeholder="예: Surphase, 바이오테크A", label_visibility="collapsed")

# ─── Step 2: IR 자료 ───
st.markdown('<div class="step-label"><div class="step-dot">2</div><div class="step-text">IR 자료 업로드</div></div>', unsafe_allow_html=True)
ir_files = st.file_uploader(
    "IR 데크, 사업계획서 등 (PDF, TXT)",
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
    if not company_name:
        st.error("기업명을 입력하세요")
        st.stop()
    if not ir_files:
        st.error("IR 자료를 업로드하세요")
        st.stop()

    # PDF 텍스트 추출
    with st.spinner("IR 자료 분석 중..."):
        all_text = []
        for uf in ir_files:
            if uf.name.lower().endswith(".pdf"):
                text = extract_pdf_text(uf.getvalue())
                all_text.append(f"=== {uf.name} ===\n{text}")
            else:
                try:
                    text = uf.getvalue().decode("utf-8", errors="replace")
                    all_text.append(f"=== {uf.name} ===\n{text}")
                except Exception:
                    all_text.append(f"=== {uf.name} === (읽기 실패)")

        ir_text = "\n\n".join(all_text)

    # Claude API 호출
    with st.spinner("AI 분석 진행 중... (1~2분 소요)"):
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(company_name, ir_text, vc_opinion, vc_firm, vc_stage)

        try:
            result = call_claude(system_prompt, user_prompt)
            st.session_state.vc_result = {
                "company": company_name,
                "content": result,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "vc_firm": vc_firm,
                "has_phase2": bool(vc_opinion),
            }
        except Exception as e:
            st.error(f"API 오류: {str(e)}")

# ─── 결과 표시 ───
if st.session_state.vc_result:
    res = st.session_state.vc_result
    st.markdown("---")
    st.markdown(f"### 검토 결과 — {res['company']}")

    if res.get("vc_firm"):
        st.caption(f"VC: {res['vc_firm']} | {res['timestamp']}")
    else:
        st.caption(f"검토일: {res['timestamp']}")

    # Phase 표시
    tabs = ["Phase 1: 사업성 검토"]
    if res.get("has_phase2"):
        tabs.append("Phase 2: VC 의견 검증")

    content = res["content"]

    if res.get("has_phase2") and "Phase 2" in content:
        parts = content.split("## Phase 2")
        phase1_content = parts[0]
        phase2_content = "## Phase 2" + parts[1] if len(parts) > 1 else ""

        tab1, tab2 = st.tabs(tabs)
        with tab1:
            st.markdown(phase1_content)
        with tab2:
            st.markdown(phase2_content)
    else:
        st.markdown(content)

    # 다운로드
    st.download_button(
        label="결과 다운로드 (.md)",
        data=content,
        file_name=f"{res['company']}_VC검토_{res['timestamp'][:10]}.md",
        mime="text/markdown",
    )

# ─── Footer ───
st.markdown("""
<div class="vc-footer">
    NuBI VC Review &mdash; Powered by NUBiPLOT + Claude API<br>
    &copy; 2026 TeamNubiz
</div>
""", unsafe_allow_html=True)
