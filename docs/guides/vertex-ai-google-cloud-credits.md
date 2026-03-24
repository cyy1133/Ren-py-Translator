# Vertex AI / Google Cloud 무료 크레딧 가이드

Ren'Py Translation Workbench에서 `Google Gemini -> Vertex AI` 모드를 사용할 때, Google Cloud 프로젝트 청구와 무료 크레딧 확인 흐름을 정리한 가이드입니다.  
*This guide explains how to use `Google Gemini -> Vertex AI` mode in Ren'Py Translation Workbench, with a focus on Google Cloud billing and free-credit verification.*

## 1. 왜 Vertex AI를 쓰는가

- `Gemini Developer API key` 경로는 Google AI Studio / Developer API 청구 흐름입니다. / *The `Gemini Developer API key` path uses the Google AI Studio / Developer API billing flow.*
- `Vertex AI` 경로는 Google Cloud 프로젝트 기준으로 청구됩니다. / *The `Vertex AI` path is billed against a Google Cloud project.*
- Google Cloud 무료 체험이나 프로모션 크레딧, 예산 경고, 비용 리포트를 함께 쓰려면 Vertex AI가 더 명확합니다. / *Vertex AI is the clearer choice when you want to use Google Cloud free-trial/promotional credits, budgets, and billing reports.*

이 앱의 Vertex 모드는 현재 `서비스 계정 JSON` 또는 `Application Default Credentials (ADC)` 기준으로 동작합니다.  
*The current Vertex mode in this app works with either a service account JSON or Application Default Credentials (ADC).*

## 2. Google 공식 문서 기준으로 먼저 알아둘 점

- Google Cloud Free Trial은 보통 `90일 / $300 welcome credit` 구조입니다. / *Google Cloud Free Trial is typically a `90-day / $300 welcome credit` program.*
- Free Trial 중에는 사용량이 `Google Cloud Billing` 안에서 집계됩니다. / *Usage during the Free Trial is tracked under Google Cloud Billing.*
- Vertex AI는 Google Cloud 제품군이므로, 실제로 어느 청구 계정과 프로젝트에 연결되어 있는지가 중요합니다. / *Vertex AI is part of Google Cloud, so the attached billing account and project matter.*
- Vertex AI에서는 AI Studio 키를 그대로 쓰지 않습니다. 서비스 계정 JSON, ADC, 또는 Google Cloud 방식 인증을 써야 합니다. / *Vertex AI does not use AI Studio keys directly; use service-account JSON, ADC, or another Google Cloud authentication path.*

공식 참고:
- [Google Cloud Free Trial / Free Program](https://cloud.google.com/free/docs/free-cloud-features)
- [Vertex AI pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [Vertex AI quickstart](https://cloud.google.com/vertex-ai/generative-ai/docs/start/quickstarts/quickstart-multimodal)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc)
- [Create and delete service account keys](https://cloud.google.com/iam/docs/keys-create-delete)

## 3. 준비물

다음 네 가지가 준비되어 있으면 됩니다.  
*You only need four things ready before using the app with Vertex AI.*

1. Google Cloud 프로젝트
2. 해당 프로젝트에 연결된 Billing 계정
3. 활성화된 Vertex AI API
4. 서비스 계정 JSON 또는 ADC

권장 방식은 `서비스 계정 JSON 파일을 로컬에 따로 두고, 앱 UI에서 런타임에만 불러오는 것`입니다.  
*The recommended approach is to keep the service-account JSON outside the app folder and load it only at runtime through the UI.*

## 4. Google Cloud 쪽 준비 절차

### 4-1. 프로젝트 선택 또는 생성

- Google Cloud 콘솔에서 새 프로젝트를 만들거나 기존 프로젝트를 선택합니다. / *Create a new project or select an existing one in Google Cloud Console.*
- 이 앱에서는 나중에 `GCP 프로젝트 ID`가 필요하므로, 콘솔에 표시되는 실제 `project_id`를 확인해 둡니다. / *You will need the exact `project_id` later in the app.*

### 4-2. Billing 연결

- 프로젝트에 Billing 계정을 연결합니다. / *Attach a billing account to the project.*
- Free Trial 또는 프로모션 크레딧이 있다면, 이 프로젝트가 그 Billing 계정 아래에 있어야 합니다. / *If you have Free Trial or promotional credits, the project must be attached to the billing account that owns those credits.*

### 4-3. Vertex AI API 활성화

- `Vertex AI API`를 켭니다. / *Enable the `Vertex AI API`.*
- Google 공식 quickstart도 Billing과 Vertex AI API 활성화를 선행 조건으로 적고 있습니다. / *Google’s official quickstart also lists billing and Vertex AI API enablement as prerequisites.*

### 4-4. 서비스 계정 준비

- 번역 전용 서비스 계정을 하나 만드는 편이 관리가 쉽습니다. / *A dedicated translation service account is easier to manage.*
- JSON 키를 만든 뒤, 앱 폴더 밖 경로에 둡니다. 예: `Downloads`, `Documents`, 회사 보안 저장소. / *Create a JSON key and store it outside the app folder, such as `Downloads`, `Documents`, or a secure company location.*
- 배포 ZIP 안에 JSON을 넣지 마세요. / *Do not place the JSON inside the release ZIP.*

## 5. Workbench UI에서 Vertex AI 설정하기

### 5-1. 공급자와 인증 방식 선택

1. `공급자`를 `Google Gemini`로 둡니다.
2. `Gemini 인증 방식`을 `Vertex AI`로 바꿉니다.

이때 UI에 Vertex 전용 패널이 열립니다. / *A Vertex-specific panel appears in the UI.*

### 5-2. 입력해야 하는 항목

- `GCP 프로젝트 ID`
- `Vertex 리전`
- 인증 정보 한 가지
  - `서비스 계정 JSON 경로`
  - `JSON 파일 불러오기`
  - `서비스 계정 JSON 붙여넣기`

권장 기본값:
- 리전: `global`
- 프로젝트 ID: 서비스 계정 JSON 안의 `project_id`와 동일하게

### 5-3. JSON 파일 로드 방식

이 앱은 세 가지 방식 중 하나만 써도 됩니다.  
*You only need one of these three credential-loading paths.*

1. `서비스 계정 JSON 경로`에 직접 경로 입력
2. `JSON 파일 불러오기`로 파일 선택
3. `서비스 계정 JSON 붙여넣기`에 JSON 원문 붙여넣기

JSON 안에 `project_id`가 있으면 UI가 `GCP 프로젝트 ID`를 자동으로 채웁니다.  
*If the JSON contains `project_id`, the UI auto-fills the project field.*

## 6. 보안상 중요한 점

이 앱은 서비스 계정 JSON을 다음 위치에 자동 저장하지 않습니다.  
*The app intentionally does not persist the raw service-account JSON in the following places.*

- release ZIP
- Git 저장소
- `프로필 저장` JSON 파일

즉, 배포물에는 JSON이 들어가지 않고, 사용자는 실행 후 직접 로드해야 합니다.  
*The release package does not include the JSON; users load it manually after startup.*

권장 보안 습관:
- JSON을 프로젝트 폴더 안에 복사하지 않기
- Git에 추가하지 않기
- 업무용/개인용 프로젝트를 분리하기
- 필요 없어진 키는 Google Cloud IAM에서 삭제하기

## 7. 무료 크레딧이 실제로 적용되는지 확인하는 방법

실제 API를 사용한 뒤에는 Google Cloud Billing 보고서에서 확인하는 게 가장 정확합니다.  
*After you make a real API call, the most reliable verification path is the Google Cloud Billing report.*

확인 순서:

1. Google Cloud 콘솔에서 `Billing -> Reports`로 이동
2. Billing 계정을 현재 Vertex 프로젝트가 사용하는 계정으로 맞춤
3. `Projects` 필터에서 현재 프로젝트만 선택
4. `Services` 또는 `SKUs` 기준으로 `Vertex AI` 관련 사용량 확인
5. `Promotions / Credits` 항목이 같이 빠지는지 확인

체크 포인트:
- 사용량은 보이는데 크레딧 차감이 안 보이면, 보고서 반영 지연일 수 있습니다.
- 사용량이 아예 다른 프로젝트로 들어가면 `project_id`를 잘못 쓴 것입니다.
- Vertex가 아니라 Gemini Developer API로 갔다면 `Gemini 인증 방식`이 잘못된 것입니다.

## 8. 이 앱에서 특히 조심할 오해

### 오해 1. Vertex AI인데 AI Studio API key를 넣으면 된다

아닙니다. 이 앱의 Vertex 모드는 서비스 계정 JSON 또는 ADC 흐름입니다.  
*No. The app’s Vertex mode expects service-account JSON or ADC.*

### 오해 2. JSON을 프로필 저장하면 다음에도 자동으로 계속 쓸 수 있다

보안 때문에 raw JSON은 프로필로 내보내지 않습니다.  
*For security reasons, the raw JSON is not exported with profiles.*

### 오해 3. release ZIP 안에 JSON을 같이 넣어도 된다

권장하지 않습니다. 이 앱도 기본적으로 그걸 막는 방향으로 설계돼 있습니다.  
*Not recommended. The app is intentionally designed to avoid bundling it.*

## 9. 추천 운영 방식

번역 실무에서는 다음 조합이 가장 안전합니다.  
*This is the safest operating pattern for real translation work.*

1. release ZIP은 그대로 배포
2. 서비스 계정 JSON은 각 사용자 로컬 경로에서만 관리
3. 앱 실행 후 UI에서 JSON 파일 로드
4. 테스트 번역 1회 수행
5. Google Cloud Billing 보고서에서 `Vertex AI`와 크레딧 적용 여부 확인
6. 이상 없으면 전체 번역 진행

## 10. 관련 UI와 함께 보면 좋은 문서

- [README.md](../../README.md)
- [Windows 글꼴 브라우저 / 폰트 적용 가이드](font-browser-and-publish-fonts.md)

## 11. 공식 참고 링크

- [Google Cloud Free Program / Free Trial](https://cloud.google.com/free/docs/free-cloud-features)
- [Vertex AI pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [Vertex AI quickstart](https://cloud.google.com/vertex-ai/generative-ai/docs/start/quickstarts/quickstart-multimodal)
- [ADC authentication](https://cloud.google.com/docs/authentication/provide-credentials-adc)
- [Service account keys](https://cloud.google.com/iam/docs/keys-create-delete)
