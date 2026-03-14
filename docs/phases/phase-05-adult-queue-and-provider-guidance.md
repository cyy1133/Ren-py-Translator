# Phase 05 - Adult Queue And Provider Guidance

## 목표

- 성인 묘사 때문에 전체 파일 번역이 멈추지 않게 한다.
- 공급자별 사용 경계를 분명히 문서화한다.

## 성인 큐

현재 방식은 휴리스틱 키워드 기반 분류다.

예시 키워드:

- `sex`
- `cock`
- `cum`
- `breast`
- `orgasm`
- `thrust`

동작:

- `성인 콘텐츠도 메인 번역에 포함`이 꺼져 있으면 해당 항목은 메인 배치에서 빠진다.
- 빠진 항목은 UI의 `Adult Queue`에 남는다.
- 게임 경로 모드에서는 `adult_review.json`으로 저장된다.

의도:

- 공급자가 특정 표현만 거절해도 전체 파일이 망가지지 않게 하기
- 사용자가 별도 검수/재번역 영역을 확보하게 하기

## 공급자 가이드

Gemini 자동 번역:

- Google AI Studio 또는 Gemini API 키 사용
- 모델명은 사용자가 직접 교체 가능

OpenAI 자동 번역:

- OpenAI API 키 사용
- 백엔드는 `Responses API` 기반
- 참고: [platform.openai.com/docs/api-reference/responses](https://platform.openai.com/docs/api-reference/responses)

Codex OAuth / ChatGPT 로그인:

- 2026-03-12 기준 공식 Codex CLI 문서는 ChatGPT 로그인 또는 API 키 로그인 방식을 설명한다.
- 참고: [help.openai.com/en/articles/11096431-openai-codex-cli-getting-started](https://help.openai.com/en/articles/11096431-openai-codex-cli-getting-started)
- 이 로그인은 Codex 클라이언트용 로컬 인증 흐름으로 봐야 하며, 이 저장소가 그 자격증명을 일반 REST API 키처럼 직접 읽어 쓰도록 만들지는 않았다.

현재 결론:

- 자동 번역 파이프라인은 `Gemini API key` 또는 `OpenAI API key` 기반으로 유지
- Codex는 수동 검수/보조 번역 워크플로우로 연결

## 다음 페이즈 후보

- 성인 큐 전용 재시도 버튼
- 성인 큐만 따로 내보내는 prompt bundle
- 항목별 승인/확정 상태
