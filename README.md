# Ren-py-Translator2

Ren'Py 번역 레이어를 우선 분석하고, 캐릭터별 말투/역할, 세계관 설정, 용어집, 성인 콘텐츠 분리 큐를 함께 관리하는 로컬 AI 번역 작업대입니다.

## 현재 구현 범위

- `game/tl/ko/*.rpy` 같은 Ren'Py 번역 파일이 있으면 그 레이어를 우선 분석합니다.
- 번역 레이어가 없으면 원본 `.rpy`를 직접 분석해 소스 치환형 스테이징 출력으로 처리합니다.
- 번역 항목을 파일 통째가 아니라 블록/라인 단위로 구조화해서, 포맷은 앱이 보존하고 모델은 텍스트만 번역하도록 분리했습니다.
- 탭 UI로 `개요 / 대사·파일 / 용어집·세계관 / 캐릭터 / 성인 큐 / 결과·로그`를 분리했습니다.
- `EXE 선택` 버튼으로 실행 파일을 고르면 바로 분석까지 이어집니다.
- 분석 직후 대본을 바탕으로 세계관, 번역 톤, 형식 규칙, 캐릭터별 기본 말투/역할을 자동 추정합니다.
- 가능한 경우 대화 스프라이트에서 캐릭터 썸네일을 자동 추출해서 캐릭터 목록에 붙입니다.
- 캐릭터 탭은 좌측 인물 목록 + 우측 상세 편집 작업대로 재구성되어 `AI 추정 / 사용자 보정 / 샘플 대사`를 나눠 봅니다.
- 캐릭터 탭에서 `어투 프리셋` 드롭다운으로 표준 말투 프롬프트를 고를 수 있고, 현재 값이 AI 기본 추정 그대로라면 새 프리셋 제안값으로 tone/notes를 함께 채웁니다.
- `샘플 미리 번역` 버튼은 현재 프리셋 + tone/notes + 세계관 설정으로 샘플 대사만 먼저 Gemini/OpenAI에 보내 실제 번역 어투를 확인하게 해 줍니다.
- 샘플 미리 번역은 `현재 설정 / 대안 프리셋 2개`를 같은 3~5줄에 대해 나란히 비교하고, 같은 조건이면 프런트엔드 캐시를 재사용해 다시 호출하지 않습니다.
- 캐릭터 상세 패널의 `이 캐릭터만 재번역` 버튼은 현재 체크된 파일 범위에서 해당 화자 대사만 다시 번역하고, 기존 결과 파일은 유지한 채 그 줄만 덮어씁니다.
- 캐릭터 검색은 실시간 반영되더라도 입력 포커스와 커서 위치를 유지하고, 캐릭터 클릭 시 목록 스크롤을 유지합니다.
- 좁은 화면에서는 입력 액션, 탭, 캐릭터 작업대가 재배치되도록 반응형 CSS를 보강했습니다.
- `세계관 설명 / 전반 톤 / 형식 규칙 / 보호 용어 / 용어집`을 프로젝트 프로필 JSON으로 저장/복원할 수 있습니다.
- `배포/폰트` 탭에서 Ren'Py용 publish 언어 코드, `gui.language`, 대사/이름/옵션/UI 폰트, 크기 배율, style별 폰트 오버라이드를 따로 설정할 수 있습니다.
- 게임에서 찾은 폰트 목록과 기존 번역 레이어의 폰트 예시를 바탕으로 `원작 기본`, `기존 번역 예시` 같은 프리셋을 선택해서 한 번에 적용할 수 있습니다.
- 한국어 publish 기본값은 `한글 기본 · 균형형`, `한글 기본 · 소설형`, `한글 기본 · 강조형` 3종을 함께 제안하고, 가능한 경우 `한글 기본 · 균형형`을 기본 선택으로 채웁니다.
- 게임 분석 시 `gui.rpy` 계열에서 기본 폰트/크기와 `Language()/known_languages()` 훅을 추출해 publish 기본값과 폰트 제안 목록으로 보여줍니다.
- 프로필을 불러오면 저장된 게임 경로 기준으로 분석을 다시 실행해 파일 선택과 캐릭터 편집 상태를 최대한 복원합니다.
- 성인 묘사는 휴리스틱으로 별도 큐에 분류되며, 메인 번역에서 제외하면 `adult_review.json`으로 모입니다.
- Gemini와 OpenAI를 같은 UI에서 선택할 수 있습니다.
- 번역 세션마다 체크포인트와 배치 로그를 남겨서, 일부 배치가 실패해도 성공분은 보존되고 같은 조건으로 다시 실행하면 이어서 진행합니다.
- 현재 세션 체크포인트가 비어 있어도, 같은 문서 묶음으로 돌린 이전 OAuth 세션이 있으면 가장 최근 호환 체크포인트를 시드로 이어받습니다.
- Codex OAuth 기본 모델은 `auto-codex-economy`이며, 짧은 UI/고정 문자열은 더 싼 모델 쪽으로 보내고 긴 대사/묘사는 더 강한 모델로 자동 라우팅합니다.
- `old:...`, 파일명 같은 비언어 문자열은 API 호출 없이 그대로 통과시켜 비용을 줄입니다.
- 치명적인 인증/요금/쿼터 오류가 나면 배치를 끝없이 반갈림하지 않고 즉시 세션을 부분 완료 상태로 멈춥니다.
- 전체 파일을 한 번에 시작해도 문서 단위로 순차 처리하고, 문서 하나가 끝날 때마다 즉시 `tl/...`와 publish bundle에 써서 중간 결과를 바로 확인할 수 있습니다.
- 번역 완료 후 `translation_layer` 모드에서는 staging 출력과 함께 실제 Ren'Py가 읽는 `game/tl/<publish_lang>/...` 번들, `zz_workbench_language_config.rpy`, publish manifest/notes 파일을 같이 생성합니다.

## 테스트 기준선

테스트 대상:

- `F:\R18Games\Changiling tales\changelingtale-fullbuildwindows\ChangelingTale.exe`

2026-03-12 기준 분석 결과:

- 분석 모드: `translation_layer`
- 파일 수: `19`
- 전체 항목 수: `27,474`
- 대사: `7,294`
- 내레이션: `7,384`
- 문자열 블록: `12,796`
- 성인 큐: `259`

상세 수치는 [docs/testing/changeling-tales-baseline.md](/A:/MyProjects/Ren-py-Translator2/docs/testing/changeling-tales-baseline.md)에 정리했습니다.

## 실행

1. `Start.bat` 실행
2. `WebUI.HTML`에서 게임 `.exe` 경로를 넣고 `게임 분석`
3. 또는 `EXE 선택`으로 실행 파일을 고르면 즉시 분석
4. `대사/파일` 탭에서 샘플 대사와 파일 목록 확인
5. `용어집/세계관`, `배포/폰트`, `캐릭터` 탭에서 자동 추정값을 보정
6. 공급자와 모델 선택 후 `선택 파일 번역`

직접 파일 모드도 지원합니다.

- `.rpy` / `.txt` 업로드
- `업로드 파일 분석`
- 같은 UI에서 설정 후 번역

## 출력 경로

게임 경로 기반 번역:

- 번역 레이어 모드: `game/tl/ko_ai/...`
- Ren'Py publish bundle: `game/tl/<publish_language_code>/...`
- publish 설정/폰트 적용 파일: `game/tl/<publish_language_code>/zz_workbench_language_config.rpy`
- publish manifest/메모: `game/tl/<publish_language_code>/zz_workbench_publish_manifest.json`, `zz_workbench_publish_notes.txt`
- 원본 소스 모드: `game/_translator_output/ko_source/...`
- 성인/실패 검토: `adult_review.json`
- 배치 로그/체크포인트: `game/_translator_logs/{analysis_mode}/{lang}/{session_id}/...`

주의:

- 진짜 Ren'Py 언어 팩 생성은 `translation_layer` 모드에서만 자동 지원합니다.
- 원본 `.rpy` 직접 치환 모드에서는 스테이징 출력만 만들고, publish bundle은 경고만 반환합니다.
- 옵션 폰트는 Ren'Py의 `gui.choice_button_text_font` / `gui.choice_button_text_size`로 따로 매핑합니다.

업로드 파일 번역:

- 디스크 자동 저장 없이 브라우저에서 결과 다운로드
- 세션 로그/체크포인트는 작업 폴더 아래 `_translator_runs/...`에 저장

## Provider 메모

Gemini:

- API 키를 직접 입력합니다.
- 상단 `빠른 번역 모드`는 `추천 품질 (gemini-2.5-flash)`, `저비용 모드 (gemini-2.5-flash-lite)`, `문체 실험 (gpt-5.1-codex)` 프리셋을 제공합니다.
- 기본으로는 `추천 품질` 프리셋이 적용되고, 공급자/인증 방식/모델/배치/딜레이를 한 번에 맞춥니다.
- 2026-03-14 실측 기준 `gemini-2.5-flash`는 `batch 16 / delay 0.2 / retry 2`를 기본값으로 사용합니다. 샘플 3종에서 `8 / 12 / 16`개 청크를 비교했을 때 모두 성공했고, 항목당 평균 시간은 `1.44s / 1.22s / 1.08s`였습니다.
- Gemini는 이제 `배치 상한 + 글자수 budget`을 같이 사용합니다. 짧은 UI 문자열은 16개까지 묶되, 긴 서사/내레이션 블록은 같은 상한을 유지하면서도 글자 수가 커지면 자동으로 더 작은 청크로 나눕니다.
- 실측 원본은 [output/gemini_flash_chunk_eval_20260314.json](/A:/MyProjects/Ren-py-Translator2/output/gemini_flash_chunk_eval_20260314.json)에 저장했습니다.
- 2026-03-13 기준 UI 추천 목록은 `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`, `gemini-3-flash-preview`, `gemini-3.1-flash-lite-preview`, `gemini-3.1-pro-preview`입니다.
- 기본값은 번역 속도/비용 균형을 위해 `gemini-2.5-flash`로 유지합니다.
- 모델명은 공식 Gemini 모델 문서 기준으로 직접 바꿀 수 있습니다.

OpenAI:

- `OpenAI API key`와 `Codex OAuth (CLI)` 두 방식을 UI에서 전환할 수 있습니다.
- API 키 모드는 OpenAI `Responses API` 호출 방식을 사용합니다.
- OAuth 모드는 `codex exec` 기반 로컬 실행이며, API 키 입력 없이 더 큰 문맥 청크로 번역합니다.
- OAuth 모드의 `배치 크기` 입력은 이제 고정 크기가 아니라 상한선으로 사용됩니다.
- `auto-codex-economy`는 짧은 UI/고정 문자열은 더 싼 모델로, 긴 대사/서사 블록은 더 강한 모델로 자동 라우팅하고, 실패 시에만 더 강한 모델/더 작은 청크로 내려갑니다.
- `문체 실험` 프리셋은 OpenAI OAuth + `gpt-5.1-codex`를 바로 맞춰서 분위기/문체 튜닝용으로 빠르게 전환할 수 있게 합니다.
- OAuth 배치는 문서별로 `ui-large / story-balanced / story-tight` 전략을 자동 선택해 청크 크기를 조정합니다.
- 인증/요금/쿼터 오류는 즉시 세션을 중단하고, 이미 끝난 파일은 그대로 유지한 채 체크포인트와 로그 경로를 반환합니다.
- Windows에서는 저장소의 `codex_npx.cmd {args}`를 기본값으로 사용해 WindowsApps `codex.exe` 접근 거부를 우회합니다.
- 예전 프로필에 `codex {args}`가 저장되어 있어도, 현재 빌드에서는 Windows에서 자동으로 `codex_npx.cmd {args}`로 치환합니다.
- OAuth 패널의 `자동 설치/로그인` 버튼은 Codex CLI가 없으면 npm 전역 설치를 시도하고, 로그인되지 않은 경우 `codex login --device-auth` 창을 자동으로 엽니다.
- OAuth 번역 실행은 `gpt-5.1-codex` 계열과 충돌하는 전역 `model_reasoning_effort = "xhigh"` 설정을 피하기 위해, 실행 시 CLI reasoning effort를 `high`로 고정합니다.
- 각 OAuth 배치마다 프롬프트, Codex 명령, stdout/stderr, 원시 응답, 파싱된 JSON을 세션 로그 폴더에 저장합니다.
- 세션 `status.json`에는 현재 문서, 완료된 파일, 중단 여부, 최적화 전략 요약이 함께 기록됩니다.

Codex OAuth:

- 2026-03-12 기준 Codex CLI는 `Sign in with ChatGPT` 인증과 `codex exec` 비대화형 실행을 지원합니다.
- 이 저장소는 로컬 토큰을 직접 읽어 재사용하지 않고, 사용자가 이미 로그인한 Codex CLI를 subprocess로 호출하는 방식만 사용합니다.
- 따라서 API 키 없이도 OpenAI OAuth 번역 경로를 선택할 수 있지만, 로컬에서 `codex exec`가 실제로 호출 가능해야 합니다.

관련 링크:

- OpenAI Responses API: [platform.openai.com/docs/api-reference/responses](https://platform.openai.com/docs/api-reference/responses)
- OpenAI API keys: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Codex CLI getting started: [help.openai.com/en/articles/11096431-openai-codex-cli-getting-started](https://help.openai.com/en/articles/11096431-openai-codex-cli-getting-started)
- Gemini models: [ai.google.dev/gemini-api/docs/models](https://ai.google.dev/gemini-api/docs/models)

## 문서

- 단계 문서 인덱스: [docs/phases/README.md](/A:/MyProjects/Ren-py-Translator2/docs/phases/README.md)
- 테스트 기준선: [docs/testing/changeling-tales-baseline.md](/A:/MyProjects/Ren-py-Translator2/docs/testing/changeling-tales-baseline.md)
