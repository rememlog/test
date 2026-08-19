# Horse Racing Intelligence MVP

한국 경마 공개데이터를 기반으로 **관계 그래프 + 실시간 캐시 + 확률 스코어링**을 제공하는 MVP입니다.

## 핵심 구성

- **FastAPI**: 경주/말/관계/스코어 API
- **Neo4j**: Horse ↔ Jockey ↔ Trainer ↔ Race 관계 저장 및 탐색
- **Redis**: 최신 경주 스코어/캐시/이벤트 큐
- **PostgreSQL**: 원천 경주 결과 및 feature snapshot 저장
- **React + Vite**: 경주 분석 대시보드
- **Tesseract-ready**: 향후 출마표/PDF 이미지의 비정형 정보 보조 수집 확장 지점

## 보안 원칙

실제 비밀값은 저장소에 올리지 않습니다. `.env`, 인증서, 서비스 계정 JSON, OCR 원본, 로컬 DB/볼륨, 로그, `node_modules`와 빌드 산출물은 `.gitignore`에서 제외됩니다. 설정 예시는 `.env.example`만 커밋합니다.

## 실행

```bash
cp .env.example .env
# .env의 비밀번호와 KRA_SERVICE_KEY를 수정

docker compose up --build
```

- Dashboard: http://localhost:5173
- API docs: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

## MVP API

- `GET /health`
- `GET /api/races/demo`
- `GET /api/races/{race_id}/ranking`
- `GET /api/horses/{horse_id}/graph`
- `POST /api/demo/seed`

현재 기본 실행은 외부 API 키 없이도 확인할 수 있도록 deterministic demo dataset을 제공합니다.

## 다음 단계

1. KRA Open API endpoint별 adapter 구현
2. 데이터 정규화 및 정기 ingestion
3. LightGBM/XGBoost 모델 학습 파이프라인
4. calibration/Brier score 기반 모델 검증
5. Tesseract OCR + 문서 parser 연동
6. Neo4j Graph Data Science 기반 pair/community feature
7. Redis Streams 기반 실시간 feature refresh

> 이 프로젝트는 데이터 분석/연구용 MVP이며 수익이나 적중을 보장하지 않습니다.
