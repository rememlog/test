# Horse Racing Intelligence MVP

한국마사회(KRA) 공개데이터를 **실제 호출**해 출전표를 정규화하고, Redis에 캐시한 뒤 Neo4j 관계 그래프로 적재하여 경주 단위 baseline 분석을 만드는 MVP입니다.

## 현재 동작하는 파이프라인

```text
KRA Open API (출전표 상세)
  → FastAPI KRA adapter
  → normalize Horse/Jockey/Trainer/Owner/Race
  → Redis 5분 cache
  → Neo4j relationship upsert
  → deterministic baseline scoring
  → React dashboard
```

### 사용 중인 공식 KRA API

- 출전표 상세정보: `https://apis.data.go.kr/B551015/API26_2/entrySheet_2`
- AI 연구용 경주결과상세: `https://apis.data.go.kr/B551015/API156/raceRsutDtl`

출전표 API에는 경주마, 레이팅, 기수, 조교사, 마주, 통산/최근 1년 성적과 상금 등의 정보가 포함됩니다. 현재 분석은 이 사전 출전정보를 이용합니다.

## 중요: 서비스키

공공데이터포털에서 **한국마사회 출전표 상세정보 API 활용신청** 후 발급받은 키를 `.env`의 `KRA_SERVICE_KEY`에 넣어야 실제 호출됩니다.

```bash
cp .env.example .env
# .env 편집
KRA_SERVICE_KEY=발급받은_디코딩_서비스키
```

`.env`는 `.gitignore`에 포함되어 GitHub에 올라가지 않습니다.

## 실행

```bash
cp .env.example .env
docker compose up --build
```

- Dashboard: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`
- Neo4j Browser: `http://localhost:7474`

## 실제 KRA API

### 연결 상태

```http
GET /api/kra/status
```

### 실제 경주 분석

```http
GET /api/kra/races/analysis?meet=1&rc_date=20260822&rc_no=7
```

- `meet`: 1 서울 / 2 제주 / 3 부산경남 / 4 영천
- `rc_date`: `YYYYMMDD`
- `rc_no`: 경주번호
- `force_refresh=true`: Redis cache 무시하고 KRA 재호출

`rc_date`/`rc_no`를 생략하면 KRA 응답에서 가장 최근 경주를 선택합니다.

### Redis + Neo4j 명시적 동기화

```http
POST /api/kra/sync?meet=1&rc_date=20260822&rc_no=7
```

Neo4j에는 다음 관계가 생성됩니다.

```text
(Owner)-[:OWNS]->(Horse)
(Horse)-[:RIDDEN_BY]->(Jockey)
(Horse)-[:TRAINED_BY]->(Trainer)
(Horse)-[:ENTERS {draw, carried_weight}]->(Race)
(Race)-[:HELD_AT]->(Track)
```

## 분석 점수의 의미

현재 `model_probability`는 학습 완료된 ML 모델의 승률이 아닙니다. 다음 실제 KRA 출전표 feature를 정규화한 **baseline ranking**입니다.

- 최근 1년 3위내 비율
- 통산 3위내 비율
- 최근 1년 승률
- 통산 승률
- 동일 경주 내 상대 레이팅
- 최근/통산 상금 상대값

따라서 데이터 파이프라인/제품 MVP 검증에는 사용할 수 있지만 수익 또는 적중을 보장하는 지표로 사용하면 안 됩니다.

## 다음 개발 단계

1. 과거 `API156/raceRsutDtl` 결과 수집 및 PostgreSQL history 구축
2. Horse × Jockey × Trainer 관계 feature 생성
3. 시계열 분할로 LightGBM/XGBoost 학습
4. Brier score / log loss / calibration 검증
5. 확정 배당 데이터와 사후 value 분석
6. Redis Streams 기반 경기 직전 feature refresh
7. Tesseract OCR로 PDF/이미지 비정형 자료 보조 수집

## 보안

`.env*`, `node_modules`, 인증서/private key, `secrets/credentials`, OCR 원본, 로그, 로컬 DB/볼륨 및 build 산출물은 Git에 포함하지 않습니다. 저장소에는 `.env.example`만 유지합니다.
