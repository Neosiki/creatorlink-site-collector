# Creatorlink 사이트 구조 메모

2026년 10월 기준으로 `rty0102.creatorlink.net`을 분석해 확인한 내용입니다. 사이트 빌더가 바뀌면 달라질 수 있습니다.

## 페이지
- 홈 화면 링크에 메뉴가 나옵니다. 메뉴 경로는 퍼센트 인코딩된 한글입니다(`/%ED%95%B4%EC%9D%B8%EC%82%AC`). 요청할 때 `urllib.parse.quote(unquote(path), safe='/%')`로 다시 인코딩해야 ASCII 오류가 없습니다.
- 서버가 HTML을 그려서 보내므로 브라우저 없이 HTTP만으로 수집됩니다.
- 메뉴 유형은 세 가지입니다.
  1. 갤러리형: 작품 목록(여러 개 가능)과 소개 섹션이 함께 있음. 목록은 첫 화면에 `view`개(보통 12)만 그려지고 나머지는 '더보기'로 불러옵니다.
  2. 섹션형: 소개 섹션과 슬라이드뿐인 페이지. 이미지는 CSS `background-image`와 `<img>`에 들어 있어 페이지 문자열만 읽으면 전부 나옵니다.
  3. 게시판(forum)형: 글 목록을 관리자만 볼 수 있게 설정된 경우 `data-description`에 안내 문구가 있고 수집할 글이 없습니다.
- 상세 페이지는 `/<메뉴>/view/<작품 seq>`입니다. 삭제됐거나 비공개로 바뀐 작품은 목록에 남아 있어도 404가 돌아오며, 메뉴에 따라 절반 이상이 404였습니다.

## 갤러리 목록 요청(핵심)
페이지 안에 `"list":[ ... ],"view":"12","total":26` 형태의 JSON이 박혀 있습니다. 이 JSON은 첫 화면 몫(`view`개)만 담습니다. 전체는 사이트 JS(`/js/render.*.js`)가 쓰는 아래 요청으로 받습니다.

```
POST /template/gallery/list/pid/<목록ID>/sid/<소유자>/spage/<메뉴slug(인코딩)>/view/<개수>
Content-Type: application/x-www-form-urlencoded
X-Requested-With: XMLHttpRequest
본문: g_mode=gallery&visible=true&sfl=category&stx=&orderby=
```

- `<목록ID>`는 페이지에 박힌 JSON 항목의 `pid`, `<메뉴slug>`는 항목의 `page`입니다. 한 메뉴에 목록이 여러 개 있을 수 있어(도서발간은 3개: 26, 30, 44점) 목록마다 호출합니다.
- `view`를 5000처럼 크게 주면 전체가 한 번에 옵니다. 응답의 `total.list_total`로 개수를 대조합니다.
- 항목 필드: `seq`(작품 id), `sid`, `page`, `pid`, `pos`, `folder`, `title`, `caption`, `content`(HTML 포함 가능), `hashtag`, `category`, `image`(파일명), `alt`, `hit`, `visible`, `datetime`. 응답의 `visible` 값은 모든 항목이 `0`이었고 공개 여부와 무관했습니다.
- 같은 사진이 여러 목록에 겹쳐 들어가므로 작품 수보다 고유 이미지 수가 적을 수 있습니다(風景: 77점, 64종).

## 이미지 주소
- 저장소: `https://storage.googleapis.com/cr-resource/image/<계정해시32자>/<소유자>/[<크기>/]<파일해시32자>.<확장자>`
- 크기 폴더가 없는 주소가 원본이고, `1920/`, `800/`, `700/`, `670/`이 변형입니다. 원본이 변형보다 큰 경우가 대부분이며 메뉴에 따라 최대 가로 6720px까지 나왔습니다(1200px에서 끝나는 메뉴도 있음).
- 목록의 썸네일은 상대 경로(`src="/700/<해시>.jpg"`)로 적혀 있어 계정 해시를 다른 주소에서 가져와 붙여야 합니다.
- 섹션형 페이지의 사진은 `https://lh3.googleusercontent.com/<토큰>=s0`처럼 구글 이미지 서버를 씁니다. `=s0`이 원본 크기 요청입니다. `=w800-h534-n` 같은 꼬리표는 축소본입니다.
- 소유자 폴더가 아닌 주소(예: 다른 계정 폴더)는 템플릿 견본 이미지입니다. 수집에서 제외합니다.
- 홈과 모든 메뉴 상단에 사이트 로고(`<img ... data-attach="true">`)가 있습니다. 작품이 아니므로 공통 폴더에 한 번만 둡니다.
- 일부 항목은 목록에는 있으나 저장소에서 파일이 삭제되어 모든 크기가 404입니다.

## 메타 정보
- 열리는 상세 페이지의 `og:title`, `og:description`, `og:image`에 작품 제목, 캡션, 이미지 해시가 있습니다. 단, `og:image` 주소는 계정 해시가 빠진 깨진 주소(`image//소유자/...`)라서 해시만 읽어야 합니다.
- 상세 페이지가 404여도 같은 정보가 목록 API의 `title`, `caption`, `content`에 있어 캡션을 얻을 수 있습니다.
- 빌더 기본 문구(제목 "제목", 캡션 "텍스트를 변경할 수 있습니다", 라틴어 견본 문장)가 그대로 남은 항목이 있어 걸러냅니다.

## 영상
- YouTube는 `<iframe src="https://www.youtube.com/embed/<id>?wmode=transparent">` 임베드입니다. 파일은 받지 않고 주소와 제목만 기록합니다. 삭제·비공개 영상은 제목 조회(oEmbed)가 404입니다.
