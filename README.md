# KOVO Pro Analyst Studio — 자동 연동 데이터

KOVO(한국배구연맹) 공식 API에서 **실측 수집한** V-리그·KOVO컵·퓨처스 챔프전 데이터입니다.
`KOVO_PRO_ANALYST_STUDIO.html` 앱이 열릴 때 이 저장소의 `data/manifest.json`을 먼저 읽고,
sha256이 바뀐 청크만 내려받아 자기 데이터를 갱신합니다.

- 가상·추정·합성 데이터 0건. 공식 API에 없는 값은 `—` 또는 `미공시`로 표기합니다.
- 개인정보는 담지 않습니다(선수 이름·소속·기록 등 공개 경기 기록만).

## 1. 데이터 범위

| 구분 | 범위 | 건수 |
|---|---|---|
| V-리그 | `seasonListV` 전 시즌(`001`~`023`, 2005~2026-27) | 23시즌 × 남녀 |
| V-리그 기록 | 시즌별 팀 순위·팀 기록·선수 기록·일정(정규·준PO·PO·챔결)·부문 랭킹·수상/트리플크라운/기준기록 | 5,002경기 |
| KOVO컵 | `seasonListCup` 전 대회(`803`~`824`) 일정·순위·선수 기록 | 22개 대회 |
| 퓨처스 챔프전 | `futures seasons`(`601`,`602`) 경기·기록 | 2개 대회 |
| 박스스코어 | 경기별 선수 박스스코어(공식 세부 기록) | 5,443경기 |
| 선수 | 프로필·이력(`history`)·수상(`honor`)·트리플크라운·기준기록·시즌 기록 | 1,366명 |
| 로스터 | 2026-2027 등록(REGISTER) 로스터 | 288명 |
| 국제·특별전 | 한일 Top Match·최강전·라이벌매치·한중일·한태 올스타·글로벌 슈퍼매치 | 16개 대회 |
| 뉴스 | KOVO 뉴스·보도자료·공지 + 외부 배구 뉴스(구글뉴스 RSS·연합뉴스) | 360 + 600건 |

## 2. 데이터 청크 (`data/manifest.json`)

| 청크 | 담긴 데이터 | 크기 |
|---|---|---|
| `data/core.json` | 시즌 목록·최근 3개년·구단 마스터·남녀 순위표·팀 기록·선수 시즌 기록·부문 랭킹·수상 | 약 2.5MB |
| `data/games.json` | 23시즌 경기 일정(정규·준PO·PO·챔결)·KOVO컵·퓨처스·최근 3시즌 박스스코어 | 약 4.2MB |
| `data/season.json` | 선수 1,366명 프로필·이력·신분·수상·시즌별 추이 | 약 2.4MB |
| `data/news.json` | KOVO 뉴스·보도자료·공지 + 외부 배구 뉴스 | 약 0.6MB |
| `data/live_patch.json` | 최신 시즌 일정·오늘 경기·다음 경기 스냅샷 | 약 0.2MB |
| `data/box_<시즌>.json` | 시즌별 박스스코어(필요할 때만 내려받는 lazy 청크, `box_001`~`box_824`) | 0.05~1.0MB |

각 청크는 `<id>.json`(정본)과 같은 바이트를 `window.KOVO_RECEIVE(...)`로 감싼 `<id>.js` 두 형태로 올라갑니다.
- `.json` — `raw.githubusercontent.com` (fetch, CORS `*`)
- `.js` — `cdn.jsdelivr.net` (fetch가 막힐 때 script 로더용)

앱은 받은 값을 제자리(in-place)로 덮어쓰며, `manifest.updated_at`이 앱 내장 데이터보다 **이전이면 반영하지 않습니다**(역행 차단).
박스스코어 청크는 경기 모달을 열 때만 내려받습니다.

## 3. 수집·검증 도구

| 도구 | 역할 |
|---|---|
| `tools/collect.py` | KOVO 공식 API 전수 수집(캐시 기반 재개 가능). `seasons/cup/futures/players/boxes/merge` |
| `tools/build_kovo.py` | 원본 → 앱 데이터·청크·단일 HTML 빌드 |
| `tools/fetch_external.py` | 외부 뉴스(구글뉴스 RSS·연합뉴스) 수집 |
| `tools/update_news.py` | 뉴스 청크만 최신으로 갱신(manifest `checked_at` 포함) |
| `tools/verify_manifest.py` | 청크 sha256·bytes·`.js` 래퍼 검증, `--fix`로 재생성 |

## 4. 갱신 절차

```bash
python3 tools/collect.py seasons      # V-리그 전 시즌
python3 tools/collect.py cup futures  # KOVO컵·퓨처스
python3 tools/collect.py players boxes
python3 tools/collect.py merge
python3 tools/fetch_external.py
python3 tools/build_kovo.py
python3 tools/update_news.py          # 뉴스만 자주 갱신할 때
python3 tools/verify_manifest.py --fix
```

## 5. 신분·이력 기준

선수 신분은 KOVO 공식 `/players/{pcode}/history`(등록·계약·FA·이적·임대·자유신분·임의해지·은퇴)와
최신 시즌 등록 로스터(`/teams/{code}/players?seasonCode=023`, `status=REGISTER`)로만 판정합니다.

- 현역 등록 / 군복무·상무 / 자유신분·방출 / 은퇴 / 과거 소속
- FA·트레이드 이력은 이력 문자열의 `FA`, `이적`, `트레이드` 이벤트로 별도 표기
- 동명이인은 이름이 아니라 `playerCode`로 구분하고, 화면에는 생년·구단·등번호를 함께 표시

코칭스태프는 KOVO 공식 API가 제공하지 않아 **미공시**로 표기하며 추정해 넣지 않습니다.
구단 주소·연락처·홈페이지·소개는 KOVO `/teams` 공식 값입니다.
