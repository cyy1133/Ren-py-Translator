# Phase 04 - Translation Pipeline And Prompt Contract

## 목표

- 모델이 파일 포맷을 건드리지 않고 텍스트만 번역하게 만든다.
- 캐릭터/세계관/용어집 정보를 번역 프롬프트에 안정적으로 주입한다.

## 현재 번역 흐름

1. 분석된 파일에서 번역 항목만 추린다.
2. 성인 큐 제외 여부를 먼저 판정한다.
3. 항목을 배치 단위로 자른다.
4. 각 배치마다 다음 정보로 프롬프트를 만든다.

- 세계관 설명
- 글로벌 톤 메모
- 형식/보존 규칙
- 보호 용어
- 용어집
- 해당 배치에 실제로 등장하는 화자 카드 정보
- 각 항목의 앞/뒤 문맥

5. 모델 응답은 JSON만 허용한다.
6. 앱이 번역 문자열을 원본 줄에 다시 주입한다.
7. 배치 성공분은 체크포인트에 즉시 기록해 같은 조건으로 재실행하면 재개한다.
8. OAuth CLI 배치가 실패하거나 일부 `id`를 누락하면 더 작은 배치로 자동 분할 재시도한다.
9. 각 배치의 프롬프트/응답/오류는 세션 로그 폴더에 남긴다.
10. 문서는 한 번에 모두 flatten하지 않고, 파일 단위로 순차 처리한다.
11. 파일 하나가 끝날 때마다 바로 `tl/...` staging 출력과 publish bundle을 다시 써서 Ren'Py에서 중간 결과를 확인할 수 있게 한다.
12. `old:...`, 파일명 같은 비언어 문자열은 API에 보내지 않고 그대로 통과시킨다.
13. 인증/요금/쿼터 오류는 더 작은 배치로 무한 분할하지 않고 세션을 부분 완료 상태로 중단한다.

## 응답 계약

모델에게 요구하는 형식:

```json
{
  "translations": [
    { "id": "dialogue_xxxxx", "text": "..." }
  ]
}
```

앱이 검증하는 것:

- `translations` 키 존재
- 각 `id`가 요청 배치의 항목과 매칭되는지
- `text`가 문자열인지

## 포맷 보존 규칙

- 따옴표 바깥 구조는 앱이 유지
- 태그, 변수, 이스케이프는 프롬프트에서 보존 지시
- 실제 쓰기 전 `escape_renpy_text()`로 다시 한 번 안전하게 정규화

## Provider 처리

Gemini:

- `generate_content()` 호출
- JSON 텍스트 파싱

OpenAI:

- `Responses API` 호출
- `output_text` 우선, 없으면 조각을 합쳐 JSON 파싱
- `Codex OAuth (CLI)` 경로에서는 기본값 `auto-codex-economy`를 통해 UI/고정 문자열은 더 싼 모델, 서사/대사는 더 강한 모델로 자동 라우팅한다.
- OAuth 배치 크기는 고정값이 아니라 상한선으로 해석하고, 문서 성격에 따라 `ui-large / story-balanced / story-tight` 전략으로 청크를 자동 조정한다.
- `model_reasoning_effort="high"`를 강제한다.
- Codex CLI 경로는 `checkpoint.json`, `status.json`, `attempts/attempt_xxxx/*` 로그를 함께 남긴다.

## 남은 개선점

- 품질 점수/검수 상태 필드 추가
- 체크포인트 정리/삭제 UI
