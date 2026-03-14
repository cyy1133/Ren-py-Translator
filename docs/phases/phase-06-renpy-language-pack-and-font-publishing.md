# Phase 06 - Ren'Py Language Pack And Font Publishing

## 목표

- 번역 완료본을 staging 출력과 별도로 Ren'Py가 직접 읽는 `game/tl/<lang>/...` 구조로 다시 배치한다.
- `translate <lang> ...` 헤더를 publish 언어 코드로 다시 써서 실제 언어 팩처럼 동작하게 만든다.
- 게임의 기존 GUI 폰트/글자 크기를 추출해, 번역용 폰트가 너무 크거나 작아지지 않도록 자동 보정 경로를 만든다.
- 대사/이름/UI 폰트와 특정 style 폰트를 따로 제어할 수 있게 한다.
- 대사/이름/옵션/UI를 프리셋 단위로 바로 고를 수 있게 한다.

## 조사 결과

- Ren'Py 번역 파일은 `game/tl/<language>/...` 아래에 위치해야 한다.
- 번역 블록 헤더도 `translate <language> ...` 형태로 publish 폴더명과 맞아야 한다.
- 언어별 GUI 조정은 `translate <language> python:` 블록에서 `gui.language`, `gui.text_font`, `gui.name_text_font`, `gui.interface_text_font`, `gui.system_font`, `gui.glyph_font`, `gui.text_size` 등을 덮어쓰는 방식이 자연스럽다.
- `gui.interface_text_font`를 바꾸는 경우 버튼/선택지 텍스트 폰트도 함께 다시 지정하는 편이 안전하다.
- 한국어 기준 기본 `gui.language` 값은 `korean-with-spaces`가 적합하다.

참고 문서:

- [Ren'Py Translation](https://www.renpy.org/doc/html/translation.html)
- [Ren'Py GUI Customization](https://www.renpy.org/doc/html/gui.html)

## 구현 내용

1. 게임 분석 시 `gui.rpy` 계열 `.rpy`를 스캔해서 다음 정보를 추출한다.

- 기본 GUI 언어 (`gui.language`)
- 기본 폰트 후보 (`gui.default_font`, `gui.text_font`, `gui.name_font`, `gui.name_text_font`, `gui.interface_font`, `gui.interface_text_font`, `gui.system_font`, `gui.glyph_font`)
- 기본 크기 (`gui.text_size`, `gui.name_text_size`, `gui.interface_text_size`, `gui.label_text_size`, `gui.notify_text_size`, `gui.button_text_size`, `gui.choice_button_text_size`)
- 게임이 `Language()` 또는 `renpy.known_languages()`를 이미 쓰는지 여부
- 게임 폴더 아래 폰트 파일 후보 목록
- 기존 번역 블록에서 등장한 style 이름 후보

2. 분석 응답에 `gui_baseline`과 `default_publish_settings`를 추가한다.

3. 웹 UI에 `배포/폰트` 탭을 추가한다.

- publish 언어 코드
- 표시 이름
- `gui.language`
- publish bundle on/off
- 폰트 자동 크기 보정 on/off
- `원작 기본`, 기존 번역 예시 기반 폰트 프리셋 선택
- 한국어일 때는 게임 안 폰트 후보를 우선 써서 `한글 기본 · 균형형`, `한글 기본 · 소설형`, `한글 기본 · 강조형` 프리셋을 추가하고, 가능한 경우 균형형을 publish 기본값으로 채운다.
- 대사/이름/옵션/UI/시스템/glyph 폰트 선택
- 대사/이름/옵션/UI 크기 배율
- style별 개별 폰트/크기 오버라이드

4. 디스크 출력 단계에서 기존 staging 출력과 함께 publish bundle을 생성한다.

- `game/tl/<publish_language_code>/...`
- `zz_workbench_language_config.rpy`
- `zz_workbench_publish_manifest.json`
- `zz_workbench_publish_notes.txt`

5. publish config 생성 시 다음 규칙을 사용한다.

- 대사 폰트 입력 시 `gui.default_font`, `gui.text_font`
- 이름 폰트 입력 시 `gui.name_font`, `gui.name_text_font`
- UI 폰트 입력 시 `gui.interface_font`, `gui.interface_text_font`, `gui.label_font`, `gui.button_text_font`, `gui.choice_button_text_font`
- 옵션 폰트 입력 시 `gui.choice_button_text_font`
- 시스템/glyph 폰트는 각각 `gui.system_font`, `gui.glyph_font`
- 크기는 baseline 값에 사용자 배율과 자동 보정 배율을 곱해서 계산
- style override는 `translate <lang> style <style_name>:` 블록으로 생성

6. 프리셋은 두 경로에서 만든다.

- 원본 게임의 현재 GUI 값을 그대로 쓰는 `원작 기본`
- 기존 번역 블록(`translate <lang> python`, `translate <lang> style`)에서 추출한 `기존 번역 예시 · <lang>`

## 자동 크기 보정 방식

- baseline 폰트와 새 폰트를 같은 기준 size로 Pillow에서 렌더링해 bounding box를 측정한다.
- 높이 비율 70%, 너비 비율 30%를 섞어 배율을 만든다.
- 과도한 변화를 막기 위해 `0.75x`~`1.35x`로 clamp한다.
- 사용자가 넣은 수동 배율(`dialogue_scale`, `name_scale`, `interface_scale`)과 곱해서 최종 크기를 계산한다.

## 현재 제약

- 진짜 Ren'Py 언어 팩 자동 생성은 `translation_layer` 모드에서만 지원한다.
- 원본 `.rpy` 직접 치환 모드는 Ren'Py가 요구하는 `translate <lang> <label>` 스켈레톤이 없을 수 있으므로 staging 출력만 만든다.
- style override의 크기는 원본 style 정의를 일반화하기 어렵기 때문에 현재는 직접 숫자를 넣는 방식만 지원한다.

## 검증

- `python -m py_compile RBackend.py`
- `node --check webui.js`
- `ChangelingTale.exe` 분석 응답에서 GUI baseline / publish 기본값 확인
- 실제 `game/tl/ko_workbench/auto.rpy` 생성 후 헤더가 `translate ko_workbench ...`로 바뀌는지 확인
- `zz_workbench_language_config.rpy`, `zz_workbench_publish_manifest.json` 생성 확인
