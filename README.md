# Ren-py-Translator
Renpy Translator for Script. 

이 프로그램은 Ren'py 게임을 AI를 통해 (Gemini API) 한글로 번역하는데 도움을 받을 수 있는 툴입니다. 

Gemini API 키 생성 및 사용법 :
==============================================
https://aistudio.google.com/app/apikey?hl=ko
구글에 회원가입 및 로그인을 진행해주세요.

화면 중앙에 있는 Google AI Sudio에 로그인 을 클릭해주세요.

좌측 메뉴에서 Get API Key 메뉴를 클릭해주세요.

API Key 생성하기 버튼을 클릭해주세요.


사용법 : 
====================================================================
1. Start.bat 파일을 실행합니다 (Python3.9 (3.12 권장) 설치가 되어있어야 합니다.)
2. Gemini API key를 넣고 모델을 고릅니다. (2.0 flash 추천)
3. rpy 파일을 직접 넣거나 게임의 exe 파일이 저장된 주소를 입력하고 버튼을 누르세요.
4. 백엔드 스크립트가 알아서 rpy 스크립트에 들어있는 화자 코드 (캐릭터 코드) 를 분석하여 아래 설명을 추가할 수 있도록 칸을 추가합니다
5. 캐릭터에 맞는 서술 방식을 추가합니다.
6. 번역 버튼을 누릅니다.
7. ** 참고 귀찮지 않도록 화자 정보를 Json으로 저장해서 다시 사용할 수 있습니다. **
8. ![image](https://github.com/user-attachments/assets/c4e2117f-7452-42a6-9894-fec1a2ed471c)
9. ![image](https://github.com/user-attachments/assets/bc9df750-6826-4d9b-8deb-794cae5617db)

![Sample](https://github.com/user-attachments/assets/9c6e70b1-523d-434e-92e6-32587d5a11df)
