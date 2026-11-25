# KOVO Pro Analyst Studio — 자동 연동 데이터

KOVO(한국배구연맹) 공식 API에서 **실측 수집한** V-리그·KOVO컵·퓨처스 챔프전 데이터입니다.
`KOVO_PRO_ANALYST_STUDIO.html` 앱이 열릴 때 이 저장소의 `data/manifest.json`을 먼저 읽고,
sha256이 바뀐 청크만 내려받아 자기 데이터를 갱신합니다.

- 가상·추정·합성 데이터 0건. 공식 API에 없는 값은 `—` 또는 `미공시`로 표기합니다.
- 개인정보는 담지 않습니다(선수 이름·소속·기록 등 공개 경기 기록만).

## 1. 데이터 청크 (`data/manifest.json`)

| 청크 | 담긴 데이터 | 크기 |
|---|---|---|
| `data/core.json` | 시즌 목록 · 구단 마스터 · 남녀 순위표 · 팀 기록 · 선수 시즌 기록 · 부문 랭킹 · 수상/주요기록 | 약 0.9MB |
| `data/games.json` | 7시즌 경기 일정(정규·준PO·PO·챔결) · 박스스코어 308경기 · KOVO컵 · 퓨처스 챔프전 | 약 2.1MB |
| `data/season.json` | 선수 449명 프로필·이력·수상·시즌별 추이 | 약 0.8MB |
| `data/news.json` | KOVO 뉴스·보도자료·공지 120건 + 외부 배구 뉴스 271건 | 약 0.23MB |
| `data/live_patch.json` | 실시간 경기 응답(KOVO `/stat/real-time`) | 약 4KB |

각 청크는 `<id>.json`(정본)과 같은 바이트를 `window.KOVO_RECEIVE(...)`로 감싼 `<id>.js` 두 형태로 올라갑니다.
- `.json` — `raw.githubusercontent.com` (fetch, CORS `*`)
- `.js` — `raw.githack.com` · `cdn.jsdelivr.net` (앱을 `file://`로 열어 fetch가 막힐 때 script 로더용)

앱은 받은 값을 제자리(in-place)로 덮어씁니다. `data/manifest.json`의 `checked_at`이 앱에 저장된
마지막 확인 시각보다 이전이면 반영하지 않습니다(역행 차단).

## 2. 수집 범위 (KOVO 공식 API `user-api.kovo.co.kr`)

| 구분 | 범위 |
|---|---|
| V-리그 시즌 | `023`(2026-27) ~ `017`(2020-21) 7개 시즌, 남자부·여자부 |
| 팀 기록 | 순위표·팀 누적 기록(공격·블로킹·서브·디그·세트·리시브·범실) |
| 선수 기록 | 시즌별 전 선수(미규정 포함) 누적 기록 + 부문별 랭킹 13종 |
| 경기 | 7시즌 정규리그·준플레이오프·플레이오프·챔피언결정전 일정/결과 |
| 박스스코어 | 2026-27·2025-26 308경기 선수별 상세 기록 |
| 로스터 | 14개 구단 등록 선수(2026-27·2025-26), 선수 상세·이력·수상·시즌 기록 |
| KOVO컵 | 2025 여수·NH농협컵(823), 2026 여수·NH농협컵(824) — 조별리그·준결승·결승 |
| 퓨처스 챔프전 | 2025(601)·2026(602) 단양대회 — 실업팀 포함 일정·결과·팀/선수 기록(2026 남자부) |
| 수상 | 라운드 MVP · 트리플크라운 · 달성기록 |
| 뉴스 | KOVO 뉴스·보도자료·공지 각 40건(제목·요약) |

### 수집하지 못한 것 (정직 표기)
- **FIVB / VolleyballWorld(VNL)** — 자바스크립트 렌더링으로 공식 API 접근 불가(차단 520).
- **네이버 스포츠 배구 API** — 응답 시간 초과.
- **2025 퓨처스 챔프전 팀·선수 누적 기록** — 공식 API에 없음(일정·결과만 제공).

## 3. 수집·검증 스크립트 (`tools/`)

| 파일 | 역할 |
|---|---|
| `tools/fetch_kovo_all.py` | V-리그 7시즌·KOVO컵·박스스코어·선수 상세·뉴스 전수 수집 → `data/kovo_raw.json` |
| `tools/fetch_futures.py` | 퓨처스 챔프전(gcode 009) 수집 → `data/kovo_raw.json` 병합 |
| `tools/fetch_external.py` | 구글뉴스 RSS 배구 뉴스 + 접근 차단 소스 기록 → `data/external.json` |
| `tools/verify_kovo.py` | QtWebEngine 실기 검증(탭·모달·오버플로·폰트 굵기·명암비·JS 오류) |

`build_kovo.py`가 `kovo_raw.json`을 앱용 압축 데이터로 변환해 청크와 단일 HTML을 만듭니다.
`KOVO_DATA` 필드 약어는 `build_kovo.py`의 `PR`/`BI` 인덱스 정의를 참고하세요.

## 4. 데이터 출처

- KOVO 공식 API: `https://user-api.kovo.co.kr` (Accept-Language: ko-KR, Origin: https://kovo.co.kr)
- 구단 엠블럼·선수 사진: `https://cdn.kovo.co.kr`
- 외부 뉴스: Google News RSS(프로배구·V-리그·배구대표팀)

수집 시각은 `data/manifest.json`의 `updated_at`·`checked_at`에 기록됩니다.
