# Ren'Py Translation Workbench 첫 작업 튜토리얼

이 문서는 **마크다운 게시판에 그대로 붙여도 깨지지 않게 만든 버전**입니다.  
HTML 전체 문서를 게시판에 붙이면 소스 코드가 그대로 노출되는 경우가 많아서, 게시판용으로는 이 문서를 쓰는 편이 맞습니다.

- HTML 튜토리얼 열기: <https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/tutorials/first-run-workbench-guide.html>
- GitHub 마크다운 버전: <https://github.com/cyy1133/Ren-py-Translator/blob/main/docs/tutorials/first-run-workbench-guide-board.md>
- 원문 마크다운(CDN): <https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/tutorials/first-run-workbench-guide-board.md>

## 1. 시작 전에 준비할 것

- 번역할 프로젝트의 실행 파일 경로
- 번역 공급자
  - Gemini API key
  - Vertex AI 서비스 계정 JSON
  - OpenAI / Codex CLI
- 전체 통번역 전에 분석, 용어집, 캐릭터 샘플 말투 확인을 먼저 끝낼 계획

## 2. 첫 화면

첫 화면은 크게 두 부분입니다.

- 위쪽: 공급자, 인증 방식, 모델, 빠른 번역 모드
- 아래쪽: 실행 파일 경로, 게임 분석, 템플릿 준비, 출력 검증/복구

![첫 화면](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/screenshots/tutorial-01-api-setup.png)

## 3. Vertex AI 설정

Gemini 인증 방식을 `Vertex AI`로 바꾸면 API key 대신 아래를 넣습니다.

- GCP 프로젝트 ID
- Vertex 리전
- 서비스 계정 JSON 경로, 파일 로드, 또는 JSON 붙여넣기

![Vertex AI 설정](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/screenshots/tutorial-02-vertex-ai.png)

공식 참고 문서:

- [Google Cloud Free Program / Free Trial](https://cloud.google.com/free/docs/free-cloud-features)
- [Vertex AI quickstart](https://cloud.google.com/vertex-ai/generative-ai/docs/start/quickstarts/quickstart-multimodal)
- [Create and delete service account keys](https://cloud.google.com/iam/docs/keys-create-delete)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc)
- [Vertex AI pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)

더 긴 설명:

- [Vertex AI / Google Cloud 무료 크레딧 가이드](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/guides/vertex-ai-google-cloud-credits.md)

## 4. 실행 파일 분석과 개요

실행 파일을 넣고 `게임 분석`을 누르면 프로젝트 전체 규모를 먼저 확인할 수 있습니다.

- 파일 수
- 번역 항목 수
- 화자 수
- 성인 큐 수
- 미번역 / 기존 번역 / 워크벤치 출력 수

![개요 탭](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/screenshots/tutorial-03-overview.png)

## 5. 대사/파일 탭

이 탭에서는 어떤 파일만 먼저 시험 번역할지 정리합니다.

- 파일별 줄 수 확인
- 기존 번역 / 워크벤치 출력 / 미번역 상태 확인
- 대사 미리보기 확인

![대사/파일 탭](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/screenshots/tutorial-04-dialogue-files.png)

## 6. 용어집/세계관 탭

전체 프로젝트에 공통으로 적용할 규칙을 넣는 곳입니다.

- 세계관 설명
- 형식 보존 규칙
- 보호 용어
- 용어집 매핑

![용어집/세계관 탭](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/screenshots/tutorial-05-glossary-world.png)

## 7. 캐릭터 탭

전체 번역 전에 캐릭터 샘플 3~5줄을 먼저 확인하는 흐름이 가장 효율적입니다.

- 캐릭터 선택
- 현재 프리셋 / 대안 프리셋 비교
- 샘플 미리 번역
- 말투 확정 후 본번역

![캐릭터 탭](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/screenshots/tutorial-06-characters.png)

## 8. 배포/폰트 탭

번역문이 게임 안에서 어떤 글꼴과 크기로 보일지 정합니다.

- 대사 / 이름 / 옵션 / UI / 시스템 / Glyph 슬롯 분리
- 기본 크기, 배율, 예상 적용 크기 확인
- 번역 후 `폰트만 다시 적용` 가능

![배포/폰트 탭](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/screenshots/tutorial-07-publish-fonts.png)

## 9. Windows 글꼴 브라우저

설치된 Windows 글꼴을 카드형으로 보고 적용할 수 있습니다.

- 글꼴 검색
- 첫 검색 결과 적용
- 페이지 이동
- 슬롯별 예상 크기 확인

![Windows 글꼴 브라우저](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/screenshots/tutorial-08-font-browser.png)

더 긴 설명:

- [Windows 글꼴 브라우저 / 폰트 적용 가이드](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/guides/font-browser-and-publish-fonts.md)

## 10. 성인 큐

민감한 줄을 메인 배치와 분리해 검수하거나 따로 자동번역할 수 있습니다.

![성인 큐](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/screenshots/tutorial-09-adult-queue.png)

## 11. 편집/검수 탭

원문, 기존 연결 번역, 워크벤치 번역, 편집용 번역문을 한 번에 비교하고 수정합니다.

![편집/검수 탭](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/screenshots/tutorial-10-editor.png)

## 12. 번역 시작 & 로그

실제 작업을 시작하는 마지막 탭입니다.

- 미번역만 번역
- 기존 번역만 재번역
- 범위 전체 새로 번역
- 진행도 연결
- 실시간 로그 확인

![번역 시작 & 로그 탭](https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/screenshots/tutorial-11-results-log.png)

## 13. 가장 안전한 첫 작업 순서

1. 실행 파일 분석
2. 용어집/세계관 정리
3. 핵심 캐릭터 샘플 말투 확인
4. 메인 파일 1~2개 시험 번역
5. 폰트와 검수 확인
6. 그 다음 전체 범위 확장

## 14. 관련 링크

- HTML 튜토리얼: <https://cdn.jsdelivr.net/gh/cyy1133/Ren-py-Translator@main/docs/tutorials/first-run-workbench-guide.html>
- 마크다운 임베드/공유 가이드: <https://github.com/cyy1133/Ren-py-Translator/blob/main/docs/tutorials/first-run-workbench-guide-embed.md>
- README: <https://github.com/cyy1133/Ren-py-Translator/blob/main/README.md>
