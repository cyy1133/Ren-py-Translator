# ===================================================================================
# 자동 라이브러리 설치 및 백엔드 서버
# ===================================================================================

# 0. 스크립트 실행에 필요한 라이브러리를 확인하고 자동으로 설치하는 부분
import sys
import subprocess
import pkg_resources

# 이 스크립트가 필요로 하는 라이브러리 목록을 정의합니다.
required_packages = {'flask', 'flask_cors', 'google-generativeai'}
# 현재 파이썬 환경에 설치된 모든 라이브러리 목록을 가져옵니다.
installed_packages = {pkg.key for pkg in pkg_resources.working_set}
# 필요한 라이브러리 중 설치되지 않은 것을 찾습니다.
missing_packages = required_packages - installed_packages

# 만약 설치되지 않은 라이브러리가 있다면
if missing_packages:
    print(f"필요한 파이썬 라이브러리를 설치합니다: {', '.join(missing_packages)}")
    # 현재 스크립트를 실행하고 있는 파이썬을 사용하여 pip를 실행합니다.
    # 이렇게 하면 가상환경 등에서도 정확한 위치에 라이브러리가 설치됩니다.
    python_executable = sys.executable
    try:
        # subprocess를 사용해 'pip install [패키지명]' 명령어를 실행합니다.
        subprocess.check_call([python_executable, '-m', 'pip', 'install', *missing_packages], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("라이브러리 설치가 완료되었습니다. 서버를 시작합니다.")
    except subprocess.CalledProcessError as e:
        print(f"라이브러리 설치 중 오류가 발생했습니다: {e}")
        print("스크립트를 계속 진행하지만, 'ModuleNotFoundError'가 발생할 수 있습니다.")
        print("터미널(CMD, PowerShell 등)을 열고 아래 명령어를 직접 실행하여 라이브러리를 설치해주세요:")
        print(f"pip install {' '.join(missing_packages)}")
        # 설치 실패 시 잠시 멈춰 사용자가 메시지를 확인할 시간을 줍니다.
        input("계속하려면 Enter 키를 누르세요...")


# 1. 필요한 라이브러리 임포트
from flask import Flask, request, jsonify  # 웹 서버 생성을 위한 Flask 라이브러리
from flask_cors import CORS                # 다른 출처(HTML 파일)에서의 요청을 허용하기 위한 CORS 라이브러리
import google.generativeai as genai        # Google Gemini API 사용을 위한 라이브러리
try:
    # API 호출 시 발생할 수 있는 구체적인 예외들을 처리하기 위함
    from google.api_core import exceptions as google_exceptions
except ImportError:
    # 라이브러리가 설치되지 않았을 경우를 대비한 예외 처리
    google_exceptions = None 
import re                                  # 정규 표현식 사용을 위한 라이브러리
import time                                # API 호출 사이에 지연을 주기 위한 라이브러리
import json                                # JSON 데이터 처리를 위한 라이브러리
import os                                  # 파일 경로 및 이름 처리를 위한 라이브러리
import datetime                            # 로그에 타임스탬프를 남기기 위한 라이브러리
import threading                           # 여러 파일을 동시에 처리(병렬 처리)하기 위한 스레딩 라이브러리

# 2. Flask 앱 초기화 및 설정
app = Flask(__name__) # Flask 애플리케이션 객체 생성
CORS(app)             # 모든 경로에 대해 CORS를 허용하여 로컬 HTML 파일이 API를 호출할 수 있도록 함

# 3. 전역 상수 및 설정 변수 정의
DEFAULT_PERSONA_DESCRIPTION = "표준적이고 중립적인 번역 톤으로, 원문의 의미를 정확하게 전달하는 데 집중합니다. 이 텍스트는 UI 요소이거나 일반적인 설명일 수 있습니다."
CONTEXT_WINDOW_SIZE = 3
DEFAULT_MODEL_NAME = 'gemini-1.5-flash-latest' 
NARRATION_PERSONA_KEY = "_narration_" 
DEFAULT_FALLBACK_PERSONA_KEY = "_default_"


# 4. 헬퍼 함수 정의

def log_message(message, file_name="General"):
    """콘솔에 시간과 파일 이름을 포함한 로그 메시지를 출력하는 함수"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}][Backend][{file_name}] {message}")

def find_game_directory(start_path):
    """주어진 경로에서 Ren'Py 게임의 'game' 폴더를 찾는 함수"""
    current_path = os.path.dirname(start_path)
    for _ in range(3):
        game_dir = os.path.join(current_path, 'game')
        if os.path.isdir(game_dir):
            log_message(f"'game' 폴더를 찾았습니다: {game_dir}")
            return game_dir
        parent_path = os.path.dirname(current_path)
        if parent_path == current_path:
            break
        current_path = parent_path
    log_message(f"'{start_path}' 근처에서 'game' 폴더를 찾지 못했습니다.")
    return None

def extract_translatables_from_rpy(file_path):
    """하나의 .rpy 파일에서 번역 가능한 라인을 추출하여 새 파일 내용을 생성하는 함수"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        log_message(f"'{file_path}' 파일 읽기 오류: {e}")
        return None

    generated_content_lines = ["translate korean:"]
    found_translatable = False

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith(('#', 'define', 'image', 'transform', 'style', 'screen', 'python', 'init', '$', 'label')):
            continue

        dialogue_match = re.match(r'^\s*([a-zA-Z0-9_]+)\s+"(.*)"$', stripped_line)
        narration_match = re.match(r'^\s*"(.*)"$', stripped_line)
        menu_match = re.match(r'^\s*"([^"]+)"\s*:', stripped_line)

        if dialogue_match or (narration_match and not dialogue_match) or (menu_match and not stripped_line.lower().startswith("menu:")):
            generated_content_lines.append(f'\n    # {stripped_line}')
            if dialogue_match:
                char_id = dialogue_match.group(1)
                if char_id.lower() != 'menu':
                    generated_content_lines.append(f'    {char_id} ""')
                else:
                    generated_content_lines.append('    ""')
            elif narration_match or menu_match:
                 generated_content_lines.append('    ""')
            found_translatable = True

    return '\n'.join(generated_content_lines) if found_translatable else None

def configure_gemini_for_thread(api_key, model_name, file_name_for_log="N/A"):
    """스레드별로 Gemini API를 설정하고 모델 객체를 생성하는 함수"""
    try:
        cleaned_api_key = api_key.strip() if api_key else None
        if not cleaned_api_key:
             log_message("ERROR: API 키가 비어 있습니다.", file_name_for_log)
             return None, "API key is empty"
        genai.configure(api_key=cleaned_api_key)
        effective_model_name = model_name if model_name else DEFAULT_MODEL_NAME
        model = genai.GenerativeModel(effective_model_name) 
        return model, None
    except Exception as e:
        log_message(f"ERROR: Gemini API 설정 중 오류 발생: {e}", file_name_for_log)
        return None, f"Gemini configuration error: {e}" 

def construct_batch_prompt_backend(batch_items, context_history, character_personas_map, file_name_for_log="N/A"):
    """한 번의 API 호출에 포함될 프롬프트를 생성하는 함수"""
    prompt = "You are a professional translator for Ren'Py. Translate the following English texts into natural Korean.\n"
    # ... (이하 프롬프트 구성 로직은 생략)
    return prompt

def escape_for_renpy_string(text, file_name_for_log="N/A"):
    """번역된 텍스트를 Ren'Py 문자열에 맞게 이스케이프하는 함수"""
    if not isinstance(text, str): return ""
    return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '    ')

def translate_batch_with_gemini_backend(model, prompt_text, batch_id_for_log, file_name_for_log="N/A"):
    """Gemini API를 호출하여 번역을 수행하는 함수"""
    # ... (이하 API 호출 로직은 생략)
    return None, "Error during translation" # Placeholder for brevity

def preprocess_rpy_content(lines, file_name_for_log="N/A"):
    """번역 전 rpy 파일 내용을 사전 처리하는 함수"""
    # ... (이하 사전 처리 로직은 생략)
    return lines

def process_single_file(file_data, api_key, model_name, character_personas_map, batch_size, api_delay, results_list, lock):
    """하나의 파일을 처리하는 스레드의 메인 함수"""
    # ... (이하 파일 처리 로직은 생략)
    return


# 5. Flask 라우트(API 엔드포인트) 정의

@app.route('/generate_files_for_translation', methods=['POST'])
def handle_generate_files():
    """/generate_files_for_translation 경로로 오는 요청을 처리하는 API 엔드포인트"""
    log_message("'/generate_files_for_translation' 요청 수신.")
    data = request.json
    game_exe_path = data.get('game_exe_path')

    if not game_exe_path or not os.path.isfile(game_exe_path):
        return jsonify({"error": "유효한 게임 실행 파일(.exe) 경로가 아닙니다."}), 400

    game_dir = find_game_directory(game_exe_path)
    if not game_dir:
        return jsonify({"error": f"'{game_exe_path}' 경로 근처에서 'game' 폴더를 찾을 수 없습니다."}), 404

    generated_files = []
    for root, _, files in os.walk(game_dir):
        for file in files:
            if file.endswith('.rpy'):
                full_path = os.path.join(root, file)
                log_message(f"rpy 파일 처리 중: {full_path}")
                content = extract_translatables_from_rpy(full_path)
                if content:
                    generated_files.append({
                        "file_name": f"{os.path.splitext(file)[0]}_to_translate.rpy",
                        "file_content": content,
                        "original_rpy_path": os.path.relpath(full_path, game_dir).replace("\\", "/")
                    })
    
    log_message(f"총 {len(generated_files)}개의 번역 대상 파일 생성 완료.")
    return jsonify(generated_files)

@app.route('/translate', methods=['POST'])
def handle_translation_threaded():
    """/translate 경로로 POST 요청이 오면 처리하는 메인 함수"""
    log_message("'/translate' (스레드) 요청 수신 시작.")
    data = request.json
    api_key = data.get('api_key')
    files_data_list = data.get('files_data') 
    model_name = data.get('model_name') 
    personas = data.get('personas', {}) 
    batch_size = data.get('batch_size', 5)
    api_delay = data.get('api_delay', 2.0)

    if not api_key: return jsonify({"error": "API 키가 제공되지 않았습니다."}), 400
    if not files_data_list: return jsonify({"error": "번역할 파일 데이터가 없습니다."}), 400

    threads = []
    results_list = []
    lock = threading.Lock()

    for file_data in files_data_list:
        thread = threading.Thread(target=process_single_file, args=(
            file_data, api_key, model_name, personas, batch_size, api_delay, results_list, lock
        ))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join() 
    
    log_message("모든 파일 처리 스레드 완료. 최종 결과 전송.")
    return jsonify(results_list) 

# 6. 서버 실행
if __name__ == '__main__':
    log_message(f"Flask 서버 시작 중... (http://127.0.0.1:5000)")
    app.run(debug=True, host='0.0.0.0', port=5000)
