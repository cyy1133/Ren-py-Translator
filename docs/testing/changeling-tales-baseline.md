# Changiling Tales Baseline

기준 시각:

- 2026-03-12

기준 경로:

- `F:\R18Games\Changiling tales\changelingtale-fullbuildwindows\ChangelingTale.exe`

## 분석 결과

- 분석 모드: `translation_layer`
- 파일 수: `19`
- 전체 항목 수: `27,474`
- 대사: `7,294`
- 내레이션: `7,384`
- 문자열 블록: `12,796`
- 성인 큐: `259`
- 화자 카드 수: `44`
- 캐릭터 썸네일 매칭: `42 / 44`
- 비화자 토큰 처리: `extend`, `butterfly_effect`, `lettertext*` 같은 스타일/연장 토큰은 화자 목록에서 분리 또는 병합

## 항목 수 상위 파일

- `tl/ko/script_grace.rpy` : `15,770` / 성인 `128`
- `tl/ko/script_marion.rpy` : `5,504` / 성인 `46`
- `tl/ko/script_chapter1_human.rpy` : `2,933` / 성인 `21`
- `tl/ko/script_boat.rpy` : `798` / 성인 `4`
- `tl/ko/screens.rpy` : `690` / 성인 `30`
- `tl/ko/screens_bonus_scenes.rpy` : `635` / 성인 `20`
- `tl/ko/common.rpy` : `281` / 성인 `1`
- `tl/ko/screens_bairds.rpy` : `205` / 성인 `6`

## 화자 상위 집계

- `_default_ / Default` : `12,796` / 성인 `133`
- `_narration_ / Narration` : `7,318` / 성인 `91`
- `c / Malcolm` : `2,861` / 성인 `5`
- `g / Grace` : `1,648` / 성인 `9`
- `m / Marion` : `1,133` / 성인 `6`
- `s / Agnes` : `437` / 성인 `3`
- `b / Balgair` : `307` / 성인 `10`
- `a / Alana` : `263` / 성인 `1`
- `j / Jessie` : `246` / 성인 `1`
- `d / Douglas` : `146` / 성인 `0`

## 검증 방식

- `python -m py_compile RBackend.py`
- `node --check webui.js`
- Flask `test_client()`로 `/analyze_sources` 호출
- 직접 `analyze_game_path()` 호출로 요약 수치 확인
- `/asset_thumbnail` 이미지 응답 확인

## 현재 미검증 범위

- 실제 API 키를 사용한 실번역
- 성인 큐가 켜진 상태의 provider별 거절/재시도 흐름
- `.rpyc` 전용 게임
