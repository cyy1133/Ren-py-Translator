# Phase 02 - Extraction And Normalization

## 목표

- Ren'Py 스크립트를 번역 가능한 최소 단위로 정규화한다.
- 번역 가능한 항목과 파일 포맷 보존 책임을 분리한다.

## 현재 파이프라인

분석 모드 1: `translation_layer`

- 경로: `game/tl/<target_language>/**/*.rpy`
- 대상:
  - `translate ko <block_id>:` 블록
  - `translate ko strings:` 블록
- 추출 항목:
  - `dialogue`
  - `narration`
  - `string`
- 번역 후 저장 경로:
  - `game/tl/<target_language>_ai/...`

분석 모드 2: `source_files`

- 경로: `game/**/*.rpy` 중 `tl` 제외
- 대상:
  - `speaker "..."` 대사
  - `"..."` 내레이션
  - `"..." :` 메뉴 문구
  - `old/new` 문자열 쌍
- 번역 후 저장 경로:
  - `game/_translator_output/<target_language>_source/...`

업로드 모드: `uploaded_files`

- 디스크 저장 없이 결과만 반환

## 정규화 모델

각 번역 항목은 아래 메타데이터를 갖는다.

- `item_id`
- `file_relative_path`
- `kind`
- `speaker_id`
- `speaker_name`
- `line_number`
- `source_text`
- `current_text`
- `adult`
- `adult_keywords`
- `context_before`
- `context_after`

핵심 포인트:

- Ren'Py 줄 전체를 모델이 다루지 않는다.
- 실제 줄 치환은 `before + translated_text + after` 방식으로 앱이 수행한다.
- 즉, 인덴트/화자 토큰/주석/문장 외 포맷은 모델 출력에 의존하지 않는다.

## 테스트 게임 기준 확인

`Changiling tales`는 `translation_layer` 모드로 잡힌다.

- `tl/ko/script_grace.rpy` 같은 파일을 우선 대상으로 선택한다.
- 원본 `game/script_grace.rpy`는 캐릭터 정의/참조용으로만 활용한다.

## 한계

- Ren'Py의 모든 특수 구문을 100% 커버하지는 않는다.
- 특히 `.rpyc`만 있는 게임은 현재 자동 추출 대상이 아니다.
