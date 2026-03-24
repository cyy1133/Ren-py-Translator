# 외부 공유 / 게시판 임베드 가이드

Ren'Py Translation Workbench 첫 작업 HTML 튜토리얼을 외부 사이트나 마크다운 게시판에 붙일 때 사용할 수 있는 링크와 예시입니다.

## 1. 외부 공유용 HTML URL

- 직접 열기:
  - <https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/tutorials/first-run-workbench-guide.html>

이 URL은 GitHub 저장소의 최신 `main` 브랜치를 정적 CDN으로 서빙합니다.  
브라우저에서 바로 열 수 있고, 튜토리얼 내부 이미지도 함께 로드됩니다.

## 2. 가장 안전한 마크다운 링크

```md
[Ren'Py Translation Workbench 첫 작업 튜토리얼](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/tutorials/first-run-workbench-guide.html)
```

## 3. 미리보기 이미지 + 링크

게시판이 `iframe`을 막는 경우에는 이미지 링크 방식이 가장 호환성이 좋습니다.

```md
[![튜토리얼 미리보기](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/screenshots/tutorial-03-overview.png)](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/tutorials/first-run-workbench-guide.html)
```

## 4. HTML iframe 임베드 예시

게시판이 raw HTML을 허용하면 아래처럼 바로 임베드할 수 있습니다.

```html
<iframe
  src="https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/tutorials/first-run-workbench-guide.html"
  width="100%"
  height="900"
  style="border:0; border-radius:12px; background:#f5efe4;"
  loading="lazy"
  referrerpolicy="no-referrer"
></iframe>
```

## 5. 게시판이 iframe을 막을 때 대안

- Markdown 링크만 사용
- 미리보기 이미지 + 링크 사용
- 게시글 본문에는 짧은 요약만 넣고 튜토리얼 HTML로 이동시키기

## 6. 함께 붙이면 좋은 보조 링크

- 튜토리얼 HTML:
  - <https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/tutorials/first-run-workbench-guide.html>
- Vertex AI / Google Cloud 무료 크레딧 가이드:
  - <https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/guides/vertex-ai-google-cloud-credits.md>
- Windows 글꼴 브라우저 / 폰트 적용 가이드:
  - <https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/guides/font-browser-and-publish-fonts.md>
