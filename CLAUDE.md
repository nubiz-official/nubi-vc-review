# NuBI VC Review — CLAUDE.md

## 목표
Gold Standard 수준의 VC 분석 보고서 자동 생성.
기준 문서: `samples/gold_standard_recens.pdf`

## 반드시 읽을 파일
- 구현 계약: `implementation_contract_v2.md`
- 스키마: `schema_design.md`
- 분석 프롬프트: `docs/analysis_prompt.md`
- 완료 조건: `docs/done_criteria.md`

## 핵심 금지 3가지
1. 키워드 매칭으로 점수 산출 금지
2. 템플릿 문자열 보고서 생성 금지
3. 웹 검색 없이 규제/수치 단정 금지

## 배포 경로
이 디렉토리(`services/nubi-vc-review/`)는 **독립 git 저장소**입니다.
- 원격: `https://github.com/nubiz-official/nubi-vc-review.git`
- **커밋/푸시는 반드시 이 디렉토리 안에서만 수행**
- ❌ 금지: `d:\nubiz_project` (main repo)에서 서비스 파일 커밋

## 분석 엔진
- analyzer.py: Claude API + web_search 도구
- reporter.py: Claude API로 보고서 전문 생성
- 모델: claude-opus-4-7 (최신)

## 완료 기준
`docs/done_criteria.md` 4개 항목 전부 YES
