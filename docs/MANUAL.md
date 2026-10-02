# 사용 매뉴얼

`creatorlink-site-collector`의 명령, 옵션, 결과물, 점검 방법을 정리한 문서입니다. AI 도구에 설치하는 방법은 `docs/INSTALL_AI.md`, 사례와 문제 해결은 `docs/USAGE_EXAMPLES.md`에 있습니다.

## 1. 무엇을 하는 도구인가

Creatorlink(애드블록) 사이트(`*.creatorlink.net`)의 메뉴마다 작품 이미지, 영상 주소, 설명 글을 받아 폴더에 정리합니다. 메뉴 하나를 끝낼 때마다 "무엇을 몇 장 받았고 무엇을 못 받았는지"를 남기도록 만들어, 어느 메뉴까지 끝났는지 늘 알 수 있습니다.

핵심은 갤러리 메뉴가 첫 화면에 작품 12점만 그린다는 점을 해결한 것입니다. 화면에 보이는 이미지만 긁으면 작품이 크게 빠집니다(한 메뉴에서 115점 중 49장만 받은 사례가 있었습니다). 이 도구는 사이트가 '더보기'에 쓰는 목록 요청을 그대로 호출해 전체 작품을 받고, 그 개수와 저장 결과를 맞춰 봅니다. 사이트 구조는 `docs/SITE_STRUCTURE.md`에 있습니다.

## 2. 준비

- Python 3.8 이상. 별도 설치 패키지는 없습니다.
- 선택: Pillow(`pip install pillow`). 있으면 이미지 가로·세로 크기 측정과 열림 검사를 합니다. 없으면 대응표의 가로·세로 칸이 비고, `verify`의 열림 검사는 건너뜁니다(`unreadable`이 `null`로 나옵니다).
- 네트워크: 사이트 도메인, `storage.googleapis.com`, `lh3.googleusercontent.com` 세 곳에 접속할 수 있어야 합니다. 허용 목록을 쓰는 환경에서는 셋 모두 추가하십시오.
- 사용 권한: 사이트 운영자(작가, 매장)가 허락한 용도로만 수집합니다.

## 3. 명령

모든 명령은 `python3 scripts/collect.py <명령> ...` 형태입니다(Windows는 `python`).

### discover: 메뉴와 사이트 정보 확인

```bash
python3 scripts/collect.py discover --base https://○○.creatorlink.net
```

JSON을 출력합니다. `site`에는 소유자 id(`owner`), 저장소 계정 해시(`acct`), 사이트 공통 로고 해시(`logo`)가 있고, `menus`에는 `index`, `name`, `path`가 있습니다. 이 값은 홈 화면에서 자동으로 찾습니다. `owner`가 비어 있으면 홈 화면 형식이 다른 사이트입니다.

### collect: 수집

```bash
# 메뉴 하나(여러 번 지정 가능)
python3 scripts/collect.py collect --base https://○○.creatorlink.net --out ./output --menu 해인사
# 전체 메뉴를 차례로
python3 scripts/collect.py collect --base https://○○.creatorlink.net --out ./output --all
```

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--base` | 필수 | 사이트 주소 |
| `--out` | 필수 | 결과를 둘 폴더 |
| `--menu` | 없음 | 메뉴의 `path`(`discover` 출력의 `path` 값). 메뉴 이름이 아닙니다. 여러 번 지정 가능 |
| `--all` | 꺼짐 | 홈에서 찾은 모든 메뉴를 차례로 수집 |
| `--lang` | `ko` | 폴더와 파일 이름 언어. `en`이면 영문 |
| `--workers` | 12 | 동시 내려받기 수 |
| `--budget` | 140 | 한 번 실행에서 내려받기에 쓸 최대 초. 넘으면 `PARTIAL`로 멈추고 다음 실행에서 이어받음 |
| `--delay` | 0 | 목록 요청 사이 대기(초). 사이트에 부담을 줄이고 싶을 때 올림 |

`--menu`나 `--all` 중 하나는 반드시 지정해야 합니다. 홈 메뉴에 없는 경로를 주면 오류로 멈춥니다.

### verify: 점검

```bash
python3 scripts/collect.py verify --out ./output
```

메뉴 폴더마다 한 줄짜리 JSON을 출력합니다.

| 항목 | 뜻 |
|---|---|
| `rows`, `files` | 대응표 행 수, 이미지 파일 수. 같아야 합니다 |
| `orphans` | 대응표에 없는 파일 |
| `missing` | 대응표에 있으나 파일이 없는 항목 |
| `unreadable` | 열리지 않는 이미지 수. Pillow가 없으면 검사하지 않아 `null` |
| `total_mb` | 이미지 총 용량 |
| `api_items`, `api_unique` | 목록 API가 준 작품 수, 중복을 뺀 이미지 수 |
| `covered_by_content_duplicate` | 다른 주소지만 내용이 같아 한 장으로 합쳐진 수(정상) |
| `source_file_missing` | 목록에는 있으나 사이트 저장소에서 파일이 삭제되어 받을 수 없는 수 |
| `UNCOVERED` | 받아야 하는데 못 받은 이미지. 비어 있어야 합니다 |
| `lists` | `[받은 수, 전체 수]` 쌍의 목록. 한 메뉴에 목록이 여러 개일 수 있습니다 |
| `ok` | 위 문제가 없으면 `true` |

문제가 하나라도 있으면 종료 코드 1입니다.

### master: 전체 대응표

```bash
python3 scripts/collect.py master --out ./output
```

메뉴별 대응표를 `master_파일명대응표.csv`(영문 모드는 `master_mapping.csv`) 한 파일로 합칩니다. 열은 메뉴별 대응표 앞에 `menu`가 붙습니다.

## 4. 결과 폴더

```
output/
  00_공통/                    사이트 공통 로고(작품이 아님)
  01_해브_갤러리/             메뉴 번호 + 이름
    이미지/                   이름_001.jpg, 이름_002.jpg ...
    영상/영상목록.csv         YouTube/Vimeo 주소(영상 파일은 받지 않음)
    상세페이지/               열리는 상세 페이지 HTML
    파일명대응표.csv          작품 한 장당 한 행
    작품설명.txt              페이지 설명 글
    목록데이터.json           목록 API 응답 전체
    원본페이지.html
    status.json               수집 요약
    수집완료.txt              완료 보고(불완전하면 수집미완료.txt)
    _이전파일/                이전 실행에서 남은 파일(있을 때만)
  master_파일명대응표.csv
  .cache/                     이어받기용 캐시
```

대응표 열: 번호, 파일명, 가로px, 세로px, 바이트, 해시, 페이지요소, 출처페이지, 원본URL, 작품제목, 작품캡션. CSV는 UTF-8(BOM 포함)이라 엑셀에서 한글이 바로 보입니다.

`status.json`의 주요 값은 `candidates`(후보 이미지 수), `saved`(저장), `duplicates`(내용 중복으로 합침), `download_failed`, `videos`, `api_lists`/`api_total`/`api_failed`(목록 요청 수, 작품 수, 실패 수), `detail_ok`/`detail_dead`(열린 상세 페이지, 404 수), `stale_moved`, `state`(`complete` 또는 `incomplete`)입니다.

## 5. 종료 코드와 이어받기

| 명령 | 종료 코드 | 뜻 |
|---|---|---|
| `collect` | 0 | 요청한 메뉴가 모두 완료 |
| `collect` | 2 | 시간 예산을 넘겨 일부만 받았거나(`PARTIAL`), 목록 요청이 실패해 불완전 |
| `verify` | 1 | 점검에서 문제 발견 |

`PARTIAL`이면 같은 명령을 그대로 다시 실행합니다. 받은 이미지는 `.cache`에 있어 이어서 받습니다. 목록 요청 실패로 불완전(`수집미완료.txt`)이면 다시 실행해 `수집완료.txt`로 바뀌는지 확인합니다. 일시 오류는 다음 실행에서 다시 시도하고, 404는 "원본 삭제"로 기록해 다시 시도하지 않습니다.

실행 시간이 짧게 제한된 환경(한 번에 약 3분)에서는 기본 `--budget 140`을 그대로 쓰고 같은 명령을 반복하십시오. 백그라운드 실행은 호출이 끝나면 종료되는 환경이 있어 쓰지 않습니다.

## 6. 완결을 판단하는 법

"전부 받았다"고 말하려면 메뉴마다 세 가지를 봅니다.

1. `verify`의 `UNCOVERED`가 비어 있다.
2. `lists`의 각 쌍에서 받은 수와 전체 수가 같다.
3. `rows`와 `files`가 같고 `orphans`, `missing`이 비어 있다.

`source_file_missing`은 실패가 아니라 "사이트에서 이미 삭제된 파일"입니다. 개수를 보고에 적습니다. 상세 페이지 404가 많아도(`detail_dead`) 작품이 빠진 것이 아닙니다. 사진과 캡션은 목록 데이터로 확보됩니다.

## 7. 알려진 한계

- 해상도는 사이트 저장소가 가진 최대 크기까지입니다. 메뉴에 따라 800~1200px뿐이기도 합니다. 인쇄용 원본은 작가에게 받아야 합니다.
- 영상 파일은 받지 않고 주소만 기록합니다.
- 갤러리 목록 요청 형식이 바뀌면 `목록데이터.json`이 비고 `api_failed`가 올라갑니다. 그때는 `docs/SITE_STRUCTURE.md`의 요청 형식과 사이트의 `render.js`를 대조하십시오.
- Windows 기본 터미널에서 직접 검증하지 않았습니다. 한글이 깨지면 `$env:PYTHONUTF8=1`을 먼저 실행하십시오.
- Creatorlink 외의 사이트 빌더에는 쓸 수 없습니다.

## 8. 저작권과 개인정보

이미지 저작권은 작가에게 있습니다. 허락받은 용도(도록 제작, 포트폴리오 이전, 백업)로만 수집하고, 저장소에는 수집한 이미지를 올리지 않습니다(`.gitignore`에 `output/`). 캡션에 가격, 에디션, 작가 연락처가 들어 있는 작품이 있으니, 도록 등 외부에 옮기기 전에 공개 범위를 확인하십시오.
