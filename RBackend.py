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
    python_executable = sys.executable
    try:
        subprocess.check_call([python_executable, '-m', 'pip', 'install', *missing_packages], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("라이브러리 설치가 완료되었습니다. 서버를 시작합니다.")
    except subprocess.CalledProcessError as e:
        print(f"라이브러리 설치 중 오류가 발생했습니다: {e}")
        print("터미널(CMD, PowerShell 등)을 열고 아래 명령어를 직접 실행하여 라이브러리를 설치해주세요:")
        print(f"pip install {' '.join(missing_packages)}")
        input("계속하려면 Enter 키를 누르세요...")

# 1. 필요한 라이브러리 임포트
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
try:
    from google.api_core import exceptions as google_exceptions
except ImportError:
    google_exceptions = None 
import re
import time
import json
import os
import datetime
import threading

# 2. 전역 변수 및 Flask 앱 초기화
app = Flask(__name__)
CORS(app)
# start.bat에서 드래그 앤 드롭으로 받은 exe 경로를 저장할 변수
game_exe_path_from_startup = None

# 3. 전역 상수 정의
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
    """주어진 .exe 파일 경로에서 상위로 탐색하며 'game' 폴더를 찾는 함수"""
    # ... (함수 내용은 이전과 동일) ...
    current_path = os.path.dirname(start_path)
    for _ in range(3):
        game_dir = os.path.join(current_path, 'game')
        if os.path.isdir(game_dir):
            log_message(f"'game' 폴더를 찾았습니다: {game_dir}")
            return game_dir
        parent_path = os.path.dirname(current_path)
        if parent_path == current_path: break
        current_path = parent_path
    return None

def extract_translatables_from_rpy(file_path):
    """하나의 .rpy 파일에서 번역 가능한 모든 라인을 추출하여 새 파일 내용을 생성하는 함수"""
    # ... (함수 내용은 이전과 동일) ...
    try:
        with open(file_path, 'r', encoding='utf-8') as f: lines = f.readlines()
    except Exception as e:
        log_message(f"'{file_path}' 파일 읽기 오류: {e}"); return None
    generated_content_lines = ["translate korean:"]
    found_translatable = False
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith(('#', 'define', 'image', 'transform', 'style', 'screen', 'python', 'init', '$', 'label')): continue
        dialogue_match = re.match(r'^\s*([a-zA-Z0-9_]+)\s+"(.*)"$', stripped_line)
        narration_match = re.match(r'^\s*"(.*)"$', stripped_line)
        menu_match = re.match(r'^\s*"([^"]+)"\s*:', stripped_line)
        if dialogue_match or (narration_match and not dialogue_match) or (menu_match and not stripped_line.lower().startswith("menu:")):
            generated_content_lines.append(f'\n    # {stripped_line}')
            if dialogue_match:
                char_id = dialogue_match.group(1)
                generated_content_lines.append(f'    {char_id} ""' if char_id.lower() != 'menu' else '    ""')
            else: generated_content_lines.append('    ""')
            found_translatable = True
    return '\n'.join(generated_content_lines) if found_translatable else None

# ... (configure_gemini_for_thread, construct_batch_prompt_backend, escape_for_renpy_string 등 다른 헬퍼 함수들은 생략됨) ...
# (이전 버전의 코드를 그대로 사용하며, 이 예제에서는 간결함을 위해 생략)

def process_single_file(file_data, api_key, model_name, character_personas_map, batch_size, api_delay, results_list, lock, game_exe_path):
    """
    하나의 파일을 번역하고 결과를 'game/tl/ko' 폴더에 저장하는 함수.
    """
    original_file_name = file_data['file_name']
    log_message(f"스레드 시작: '{original_file_name}' 처리 중...", original_file_name)

    # ... (번역 대상 아이템 수집 및 API 호출 로직은 이전과 거의 동일) ...
    
    # 이 함수 마지막 부분에 결과물 처리 로직 변경
    translated_content_full = "..." # 번역 결과물이 여기에 생성되었다고 가정

    # ---- 파일 저장 로직 시작 ----
    saved_path_str = None
    error_str = None
    try:
        # 번역 결과 자동 저장은 '.exe' 경로 기반 파일 생성 시에만 지원
        if 'original_rpy_path' in file_data and game_exe_path:
            game_dir = find_game_directory(game_exe_path)
            if not game_dir:
                raise IOError("'game' 폴더를 찾을 수 없어 파일을 저장할 수 없습니다.")

            original_relative_path = file_data['original_rpy_path']
            # Ren'Py 규칙에 따라 'game/tl/ko/' 경로 구성
            target_dir = os.path.join(game_dir, 'tl', 'ko', os.path.dirname(original_relative_path))
            target_path = os.path.join(target_dir, os.path.basename(original_relative_path))
            
            # 폴더가 없으면 생성
            os.makedirs(target_dir, exist_ok=True)
            
            # 번역된 내용으로 파일 쓰기
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(translated_content_full)
            
            saved_path_str = os.path.relpath(target_path, os.path.dirname(game_dir)).replace("\\", "/")
            log_message(f"번역 파일 저장 완료: {saved_path_str}", original_file_name)
        else:
            raise NotImplementedError("자동 저장은 '경로에서 파일 생성' 기능을 통해서만 지원됩니다.")

    except Exception as e:
        error_str = f"파일 저장 중 오류 발생: {e}"
        log_message(f"ERROR: {error_str}", original_file_name)
    # ---- 파일 저장 로직 끝 ----
    
    # 스레드 간 동기화를 위해 lock을 사용하여 결과 리스트에 추가
    with lock:
        results_list.append({
            "status": "error" if error_str else "success",
            "original_filename": original_file_name,
            "saved_path": saved_path_str,
            "error": error_str
        })

# 5. Flask 라우트(API 엔드포인트) 정의

@app.route('/get_startup_path')
def get_startup_path():
    """앱 시작 시 드래그앤드롭으로 받은 .exe 파일 경로를 프론트엔드에 전달하는 엔드포인트"""
    if game_exe_path_from_startup:
        return jsonify({"path": game_exe_path_from_startup})
    else:
        return jsonify({"path": None})

@app.route('/generate_files_for_translation', methods=['POST'])
def handle_generate_files():
    """/generate_files_for_translation 경로로 오는 요청을 처리하는 API 엔드포인트"""
    # ... (함수 내용은 이전과 동일) ...
    log_message("'/generate_files_for_translation' 요청 수신.")
    data = request.json
    game_exe_path = data.get('game_exe_path')
    if not game_exe_path or not os.path.isfile(game_exe_path): return jsonify({"error": "유효한 게임 실행 파일(.exe) 경로가 아닙니다."}), 400
    game_dir = find_game_directory(game_exe_path)
    if not game_dir: return jsonify({"error": f"'{game_exe_path}' 경로 근처에서 'game' 폴더를 찾을 수 없습니다."}), 404
    generated_files = []
    for root, _, files in os.walk(game_dir):
        for file in files:
            if file.endswith('.rpy'):
                full_path = os.path.join(root, file)
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
    """/translate 경로로 POST 요청이 오면 처리하는 메인 함수. 파일 저장을 위해 game_exe_path를 받음."""
    log_message("'/translate' (스레드) 요청 수신 시작.")
    data = request.json
    # game_exe_path를 요청 본문에서 받아옴
    game_exe_path = data.get('game_exe_path')
    if not game_exe_path:
        return jsonify({"error": "번역 파일 저장을 위해 게임 .exe 경로가 필요합니다."}), 400

    # ... (api_key, files_data_list 등 나머지 파라미터 추출은 이전과 동일) ...
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
        # process_single_file에 game_exe_path 인자 추가
        thread = threading.Thread(target=process_single_file, args=(
            file_data, api_key, model_name, personas, batch_size, api_delay, results_list, lock, game_exe_path
        ))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join() 
    
    log_message("모든 파일 처리 스레드 완료. 최종 결과 전송.")
    return jsonify(results_list) 

# 6. 서버 실행
if __name__ == '__main__':
    # 스크립트 실행 시 전달된 인자(파일 경로)가 있는지 확인
    if len(sys.argv) > 1:
        # 첫 번째 인자를 전역 변수에 저장
        game_exe_path_from_startup = sys.argv[1]
        log_message(f"시작 인자로 게임 경로 수신: {game_exe_path_from_startup}")

    log_message(f"Flask 서버 시작 중... (http://127.0.0.1:5000)")
    app.run(debug=True, host='0.0.0.0', port=5000)
