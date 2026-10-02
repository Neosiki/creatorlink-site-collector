# creatorlink-site-collector

Creatorlink(애드블록) 포트폴리오 사이트의 작품 이미지, 영상 주소, 설명 글을 메뉴 단위로 완결 수집하는 도구입니다. Python 3.8 이상과 표준 라이브러리만 쓰고, 이미지 크기 측정과 열림 검사에만 Pillow를 선택적으로 씁니다.

2026년 10월 카페보리 온라인 도록(작가 류태열 포트폴리오) 자료 수집 작업에서 만들었고, 그 작업에서 겪은 문제를 모두 반영했습니다. 개발 과정 전체는 `docs/DEVELOPMENT_LOG.md`에 있습니다.

## 빠른 사용

```bash
# 1) 메뉴와 사이트 정보 확인
python3 scripts/collect.py discover --base https://example.creatorlink.net

# 2) 메뉴 하나 수집 (여러 번 지정 가능)
python3 scripts/collect.py collect --base https://example.creatorlink.net --out ./output --menu 해인사

# 3) 전체 메뉴를 차례로 수집
python3 scripts/collect.py collect --base https://example.creatorlink.net --out ./output --all

# 4) 점검과 전체 대응표
python3 scripts/collect.py verify --out ./output
python3 scripts/collect.py master --out ./output
```

종료 코드: 0은 완료, 2는 일부만 받았거나(`PARTIAL`) 목록 요청 실패로 불완전, 1은 `verify`에서 문제 발견입니다. `PARTIAL`이면 같은 명령을 다시 실행하면 이어받습니다.

## 만들어지는 폴더

```
output/
  00_공통/                     사이트 공통 로고(작품 아님)
  01_메뉴이름/
    이미지/                    작품 이미지(원본 크기 우선)
    영상/영상목록.csv          YouTube/Vimeo 주소(파일은 받지 않음)
    상세페이지/                열리는 상세 페이지 HTML
    파일명대응표.csv           번호, 파일명, 크기, 용량, 원본 주소, 작품 제목, 캡션
    작품설명.txt               페이지 설명 글
    목록데이터.json            사이트 목록 API 응답 전체(작품 수 대조용)
    원본페이지.html, status.json, 수집완료.txt(불완전하면 수집미완료.txt)
  master_파일명대응표.csv      전체 합본
  .cache/                      이어받기용 캐시(끝나면 지워도 됨)
```

`--lang en`을 주면 폴더와 파일 이름이 영문(`images`, `mapping.csv` 등)이 됩니다.

## 이 도구가 해결하는 문제

| 문제 | 해결 |
|---|---|
| 갤러리 첫 화면에 12점만 나오고 나머지는 '더보기' | 사이트의 목록 요청(`/template/gallery/list/...`)을 호출해 전체 작품을 받음 |
| 같은 사진이 크기별(670·700·800·1920)로 여러 주소 | 해시로 묶고 원본 → 1920 → 800 순으로 가장 큰 것 선택 |
| 템플릿 견본 이미지, 사이트 로고가 섞임 | 소유자 폴더만 인정하고 로고는 자동 감지해 `00_공통`에 한 번만 저장 |
| 상세 페이지가 대량으로 404 | 목록 데이터에서 이미지와 캡션을 받으므로 영향 없음, 개수만 기록 |
| 원본 파일이 사이트에서 삭제됨 | 404를 캐시하고 `source_file_missing`으로 구분해 보고 |
| 같은 사진이 다른 이름으로 중복 업로드 | 내용 해시(SHA-1)로 합침 |
| 빌더 기본 문구("텍스트를 변경할 수 있습니다")가 캡션에 섞임 | 자동 제거 |
| 실행 한도(약 3분)와 백그라운드 종료 | 시간 예산 + 캐시 이어받기 |
| 재실행 때 이전 파일이 남음(삭제 권한 없음) | 지우지 않고 `_이전파일`로 이동 |

## 검증

`tests/`에 단위 테스트 8개가 있습니다(`python3 -m unittest discover -s tests`). 실제 사이트에서는 6개 메뉴(10, 13, 14, 15, 18, 20번)를 수집해 먼저 PC에서 받은 결과와 장수, 용량, 목록 API 작품 수가 모두 일치함을 확인했습니다.

## 주의

- 수집은 사이트 운영자가 허락한 용도로만 쓰세요. 이미지 저작권은 작가에게 있습니다. 이 저장소에는 이미지를 올리지 않습니다(`.gitignore`).
- 호출 간격이 필요하면 `--delay`를 쓰세요. 기본은 사이트가 첫 화면에서 쓰는 수준의 요청만 보냅니다.
- 네트워크 허용 목록이 있는 환경에서는 사이트 도메인, `storage.googleapis.com`, `lh3.googleusercontent.com`을 모두 추가해야 합니다.
