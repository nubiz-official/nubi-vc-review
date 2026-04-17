# 리센스 Rubric 미스매치 분석

**목표:** 원문 Grade A/B → 파이프라인 Grade C 간극 파악 및 rubric 재정의

---

## 1. 원문 강도 분석 (Expected Grade: B+)

### 원문이 강조하는 핵심
| 항목 | 원문 표현 | 강도 |
|------|---------|------|
| **규제 경로** | FDA breakthrough designation + 명확한 510(k) 경로 | A |
| **반복매출** | 소모품 기반 월/분기 반복 테스트 | A |
| **기술** | 3-마커 조합 (94% vs 70% sensitivity) | A- |
| **팀** | CEO: 15yr 진단, Quidel 출신; CTO: PharmD+PhD, 논문 12편 | B+ |
| **Early Indicators** | 3개 명시 (규제실행조직, 원천기술제어, 기기+디스포저블) | A |

**원문 총평:** 규제 명확, 반복매출 강함, 팀 검증됨 → **Expected Grade: B (strong)**

---

## 2. 파이프라인 결과 (Actual Grade: C)

### 현재 생성 결과
| Dimension | Score | Evidence |
|-----------|-------|----------|
| Market | 6.0 | 제네릭 (문서 개수만 고려) |
| Solution | 6.0 | 제네릭 (차별성 미표기) |
| Team | 6.0 | 제네릭 (경험 수년으로만 계산) |
| Scalability | 6.0 | 제네릭 (용량 2-3배면 가능) |
| **Overall** | **6.0** | **Grade C** |

---

## 3. Rubric Mismatch 원인 분석

### 문제 1: Dimension Scoring이 일반 VC형
```
현재: market/solution/team/scalability (4개)
필요: 원천기술/규제/플랫폼/반복매출/RWW (5개 누비즈식)

리센스 사례:
- 규제: A (FDA breakthrough 명시)
- 반복매출: A (소모품 월/분기 반복)
- 원천기술: A- (94% sensitivity 기술 우위)
→ 현재 rubric에서는 이 3개가 4개 generic 항목에 분산 → 점수 평준화
```

### 문제 2: Early Indicators가 제네릭
```
현재: "Product Market Fit Validation", "Regulatory Pathway Clarity" 등
원문: "규제실행조직 선배치", "원천기술 제어 가능성", "기기+디스포저블 설계"

차이: 누비즈 특화 지표 미포함 → 강도 측정 불가
```

### 문제 3: Comparable Companies 미스매치
```
현재: "Similar Company A", "Similar Company B" (제네릭)
원문: Intuitive Surgical, PROCEPT BioRobotics, Shockwave Medical, InMode
      (모두 의료기기+규제+반복매출 구조)

차이: 누비즈식 비교 체계 부재 → IPO 경로 검증 불가
```

### 문제 4: 5-Stage Scorecard 항목명 미정렬
```
설계: 원천기술통제 / 규제통제 / 플랫폼확장 / 반복매출 / RWW개입
현재: stage_1~5 (일반명칭)
매핑 부재 → 누비즈 고유 프레임 활용 불가
```

---

## 4. 수정 방향 (다음 스프린트)

### Step 1: Rubric 재정의
```python
# 변경 전 (analyzer.py)
scores = {
    "market": 6.0,
    "solution": 6.0,
    "team": 6.0,
    "scalability": 6.0
}

# 변경 후 (누비즈 5단계 기반)
scores = {
    "원천기술통제": {
        "evidence": ["FDA breakthrough", "94% sensitivity", "3-marker patent"],
        "score": 8.5
    },
    "규제통제": {
        "evidence": ["510(k) pathway clear", "CPT code pending", "FDA reviewer on board"],
        "score": 8.5
    },
    "플랫폼확장": {
        "evidence": ["CLIA lab 10x scalable", "3 hospital networks LOI"],
        "score": 7.5
    },
    "반복매출": {
        "evidence": ["Monthly/quarterly testing", "<5% churn in pilot"],
        "score": 8.0
    },
    "RWW개입": {
        "evidence": ["CEO: 15yr diagnostics", "Board: FDA reviewer"],
        "score": 7.0
    }
}
overall = (8.5 + 8.5 + 7.5 + 8.0 + 7.0) / 5 = 7.9 → Grade B ✓
```

### Step 2: Early Indicators 누비즈식으로 재정의
```
현재 문제: Generic milestones
필요 사항: 누비즈 프레임과 매핑된 추적 지표

예시 (리센스):
1. 규제실행조직 선배치 → FDA clearance timeline 6-12개월 내 달성
2. 원천기술 제어 가능성 → IP coverage 확인 (특허 3-5건)
3. 기기+디스포저블 설계 → 반복매출 수익화 (연간 $X test volume)
```

### Step 3: Claims Assessment Mapping 재정의
```python
# validator.py 변경 필요
현재: 일반적 verdict (supported/partially_supported/contradicted)
변경: 누비즈 5단계 기준 재평가

VC claim: "규제 경로가 명확하고 reimbursement도 강함"
→ 단순 지원/반지원이 아니라:
   - 규제통제 스코어에 미치는 영향 (8.5/10 근거)
   - 반복매출 신뢰도에 미치는 영향 (reimbursement rate가 매출 70% 결정)
```

### Step 4: Reporter 5-Stage Scorecard 항목명 정렬
```python
# reporter.py
scorecard_5stage = {
    "stage_1_원천기술통제": {...},  # 명시적으로 정렬
    "stage_2_규제통제": {...},
    "stage_3_플랫폼확장": {...},
    "stage_4_반복매출": {...},
    "stage_5_RWW개입": {...}
}
```

---

## 5. 검증 기준 (Calibration 완료 조건)

✓ 리센스 샘플: Grade B 이상 도출
✓ Early Indicators: 원문 3개와 >80% 일치
✓ 5-Stage Scorecard: 원문 항목명과 100% 정렬
✓ Comparable Companies: 리센스 비교사례 3개 이상 포함

---

## 6. 타임라인

- **Day 1-2:** Rubric 재정의 (analyzer.py + validator.py)
- **Day 3:** Reporter 5-stage 항목명 정렬
- **Day 4:** 리센스 재분석 및 Grade 확인
- **Day 5:** Streamlit 통합 준비 (rubric 확정 후)

---

## 부록: 리센스 원문 강도 근거

| 항목 | 원문 구절 | 점수 근거 |
|------|---------|----------|
| 규제 | "FDA breakthrough device designation granted (2024), accelerates approval pathway" | A: 명확 + 가속 경로 |
| 반복매출 | "Disposable test format (similar to glucose monitoring) enables patient home use and recurring orders" | A: 구체적 모델 |
| Early Indicators | "원천기술 제어 가능성", "규제 실행 조직 선배치", "기기+디스포저블 설계" | A: 3개 명시 |
| 팀 | "CEO: 15 years in diagnostics, prior exit (Quidel acquisition 2018)" | B+: 검증된 경험 |

**결론:** 원문이 Grade B+ 수준의 강한 케이스를 제시했으나, 파이프라인이 generic rubric으로 인해 Grade C로 평준화 됨.
