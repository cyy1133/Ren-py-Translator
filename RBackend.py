import ast
import datetime
import hashlib
import importlib.metadata
import json
import locale
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from io import BytesIO
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from tkinter import Tk, filedialog
from urllib.parse import quote_plus


REQUIRED_PACKAGES = {"flask", "flask-cors", "google-generativeai", "google-genai", "openai", "pillow"}


def ensure_required_packages() -> None:
    installed = {
        (dist.metadata.get("Name") or "").lower()
        for dist in importlib.metadata.distributions()
        if dist.metadata.get("Name")
    }
    missing = sorted(REQUIRED_PACKAGES - installed)
    if not missing:
        return

    print(f"필수 라이브러리를 설치합니다: {', '.join(missing)}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", *missing],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("필수 라이브러리 설치가 완료되었습니다.")
    except subprocess.CalledProcessError as exc:
        print(f"라이브러리 설치 중 오류가 발생했습니다: {exc}")
        print(f"아래 명령으로 수동 설치 후 다시 실행하세요: pip install {' '.join(missing)}")
        input("계속하려면 Enter를 누르세요...")


ensure_required_packages()

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

try:
    import winreg
except ImportError:
    winreg = None

try:
    from google.api_core import exceptions as google_exceptions
except ImportError:
    google_exceptions = None

try:
    from google import genai as google_genai
    from google.genai import types as google_genai_types
except ImportError:
    google_genai = None
    google_genai_types = None

try:
    from google.oauth2 import service_account
except ImportError:
    service_account = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


app = Flask(__name__)
CORS(app)

game_exe_path_from_startup: Optional[str] = None
APP_ROOT = Path(__file__).resolve().parent
CODEX_NPX_WRAPPER = APP_ROOT / "codex_npx.cmd"

DEFAULT_TARGET_LANGUAGE = "ko"
DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-5-mini",
}
SUPPORTED_PROVIDERS = set(DEFAULT_MODELS.keys())
DEFAULT_GEMINI_AUTH_MODE = "api_key"
SUPPORTED_GEMINI_AUTH_MODES = {"api_key", "vertex_ai"}
DEFAULT_OPENAI_AUTH_MODE = "api_key"
SUPPORTED_OPENAI_AUTH_MODES = {"api_key", "oauth_cli"}
DEFAULT_VERTEX_AI_LOCATION = "global"
ACTIVE_TRANSLATION_SESSION_STALE_SECONDS = 180
DEFAULT_CODEX_CLI_COMMAND = f'"{CODEX_NPX_WRAPPER}" {{args}}' if os.name == "nt" else "codex {args}"
AUTO_CODEX_MODEL_ECONOMY = "auto-codex-economy"
AUTO_CODEX_MODEL_BALANCED = "auto-codex-balanced"
DEFAULT_CODEX_OAUTH_MODEL = AUTO_CODEX_MODEL_ECONOMY
DEFAULT_CODEX_REASONING_EFFORT = "high"
SUPPORTED_CODEX_OAUTH_MODELS = {
    AUTO_CODEX_MODEL_ECONOMY,
    AUTO_CODEX_MODEL_BALANCED,
    "gpt-5.1-codex",
    "gpt-5-mini",
    "gpt-5-codex",
}
CHATGPT_UNSUPPORTED_CODEX_MODEL_PREFIXES = ("gpt-5.4",)
CODEX_OAUTH_ITEM_LIMIT = 96
CODEX_OAUTH_CHAR_LIMIT = 28000
CODEX_OAUTH_UI_ITEM_LIMIT = 48
CODEX_OAUTH_UI_CHAR_LIMIT = 24000
CODEX_OAUTH_STORY_ITEM_LIMIT = 16
CODEX_OAUTH_STORY_CHAR_LIMIT = 18000
CODEX_OAUTH_COMPLEX_ITEM_LIMIT = 8
CODEX_OAUTH_COMPLEX_CHAR_LIMIT = 12000
GEMINI_UI_CHAR_LIMIT = 6000
GEMINI_STORY_CHAR_LIMIT = 8400
GEMINI_COMPLEX_CHAR_LIMIT = 7200
TRANSLATION_LOG_DIRNAME = "_translator_logs"
UPLOADED_TRANSLATION_RUN_ROOT = APP_ROOT / "_translator_runs"
TRANSLATION_TEMPERATURE = 0.3
RENPY_CACHE_FILENAMES = {
    "bytecode-27.rpyb",
    "bytecode-39.rpyb",
    "pyanalysis.rpyb",
    "py3analysis.rpyb",
    "screens.rpyb",
}
DEFAULT_BATCH_SIZE_BY_PROVIDER = {
    "gemini": 16,
    "openai": 12,
}
DEFAULT_API_DELAY_BY_PROVIDER = {
    "gemini": 0.2,
    "openai": 0.3,
}
GEMINI_MAX_API_RETRIES = 2
OPENAI_MAX_API_RETRIES = 3
CONTEXT_WINDOW_SIZE = 2
DEFAULT_FALLBACK_PERSONA_KEY = "_default_"
NARRATION_PERSONA_KEY = "_narration_"
NON_CHARACTER_TOKENS = {
    "call",
    "centered",
    "default",
    "define",
    "elif",
    "else",
    "extend",
    "hide",
    "if",
    "image",
    "init",
    "jump",
    "label",
    "menu",
    "new",
    "old",
    "pause",
    "play",
    "python",
    "queue",
    "return",
    "scene",
    "screen",
    "show",
    "stop",
    "style",
    "text",
    "transform",
    "voice",
    "window",
}
NON_CHARACTER_SUFFIXES = (
    "_text",
    "_effect",
    "_label",
    "_screen",
    "_button",
    "_caption",
    "_title",
    "_name",
    "_mobile",
)
NON_CHARACTER_PREFIXES = ("lettertext",)
ADULT_KEYWORDS = (
    "anal",
    "aroused",
    "boob",
    "breast",
    "climax",
    "cock",
    "cum",
    "cunt",
    "dick",
    "ejac",
    "erection",
    "fuck",
    "horny",
    "knot",
    "moan",
    "naked",
    "nippl",
    "orgasm",
    "penis",
    "pussy",
    "sex",
    "shaft",
    "slut",
    "thrust",
    "wetness",
    "whore",
)
TRANSLATE_HEADER_RE = re.compile(
    r"^\s*translate\s+(?P<lang>[A-Za-z0-9_-]+)\s+(?P<label>[A-Za-z0-9_]+|strings)\s*:\s*$"
)
QUOTED_STRING_RE = re.compile(r'^(?P<before>.*?")(?P<text>(?:\\.|[^"])*)"(?P<after>.*)$')
SPEAKER_LINE_RE = re.compile(r'^\s*(?P<speaker>[A-Za-z_][A-Za-z0-9_]*)\s+"(?P<text>(?:\\.|[^"])*)"\s*$')
NARRATION_LINE_RE = re.compile(r'^\s*"(?P<text>(?:\\.|[^"])*)"\s*$')
MENU_LINE_RE = re.compile(r'^\s*"(?P<text>(?:\\.|[^"])*)"\s*:\s*$')
STRING_OLD_RE = re.compile(r'^\s*old\s+"(?P<text>(?:\\.|[^"])*)"\s*$')
STRING_NEW_RE = re.compile(r'^\s*new\s+"(?P<text>(?:\\.|[^"])*)"\s*$')
RENPY_SUBSTITUTION_RE = re.compile(r"(?<!\\)\[[^\[\]\n]+\]")
RENPY_TEXT_TAG_RE = re.compile(r"\{[^{}\n]+\}")
PYTHON_FORMAT_TOKEN_RE = re.compile(
    r"%(?:\([^)]+\))?[#0\- +]?(?:\d+|\*)?(?:\.(?:\d+|\*))?[diouxXeEfFgGcrs]"
)
CHARACTER_DEFINE_RE = re.compile(
    r'^\s*define\s+(?P<speaker>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*Character\(\s*(?P<name>None|_?\(".*?"\)|".*?")'
)
BIOTHUMB_HEADER_RE = re.compile(r"^\s*image\s+biothumb_(?P<name>[A-Za-z0-9_]+)\s*:\s*$")
IMAGE_ASSIGNMENT_RE = re.compile(r"^\s*image\s+(?P<image_name>[A-Za-z_][A-Za-z0-9_]*)\s+.+?=\s*(?P<expr>.+)$")
IMAGE_FILE_RE = re.compile(r'"(?P<path>[^"]+\.(?:png|jpg|jpeg|webp))"')
CROP_RE = re.compile(r"crop\(\s*(?P<x>-?\d+)\s*,\s*(?P<y>-?\d+)\s*,\s*(?P<w>\d+)\s*,\s*(?P<h>\d+)\s*\)")
PROPER_NOUN_RE = re.compile(r"\b([A-Z][A-Za-z']+(?:\s+[A-Z][A-Za-z']+)*)\b")
PROPER_NOUN_STOPWORDS = {
    "he",
    "her",
    "hers",
    "him",
    "his",
    "i",
    "i'd",
    "i'll",
    "i'm",
    "i've",
    "it",
    "it's",
    "she",
    "she'd",
    "she'll",
    "she's",
    "that",
    "the",
    "their",
    "them",
    "they",
    "they'd",
    "they'll",
    "they're",
    "they've",
    "this",
    "we",
    "we'd",
    "we'll",
    "we're",
    "we've",
    "what",
    "when",
    "where",
    "which",
    "who",
    "whom",
    "why",
    "how",
    "you",
    "you'd",
    "you'll",
    "you're",
    "you've",
}
GUI_ASSIGNMENT_RE = re.compile(
    r"^\s*(?:default|define)\s+gui\.(?P<name>[A-Za-z0-9_]+)\s*=\s*(?P<value>.+?)\s*$"
)
TRANSLATE_STYLE_BLOCK_RE = re.compile(
    r"^\s*translate\s+(?P<lang>[A-Za-z0-9_-]+)\s+style\s+(?P<style>[A-Za-z0-9_]+)\s*:\s*$"
)
TRANSLATE_PYTHON_BLOCK_RE = re.compile(
    r"^\s*translate\s+(?P<lang>[A-Za-z0-9_-]+)\s+python\s*:\s*$"
)
STYLE_FONT_RE = re.compile(r'^\s*font\s+"(?P<font>[^"]+)"\s*$')
STYLE_SIZE_RE = re.compile(r"^\s*size\s+(?P<size>-?\d+)\s*$")
FONT_EXTENSIONS = {".ttf", ".otf", ".ttc", ".otc"}
DEFAULT_FONT_PREVIEW_TEXT = "가나다라마바사 ABC 123"
GUI_BASELINE_FONT_KEYS = {
    "dialogue": ("text_font", "default_font"),
    "name": ("name_text_font", "name_font"),
    "options": ("choice_button_text_font", "button_text_font", "interface_text_font", "interface_font"),
    "interface": ("interface_text_font", "interface_font"),
    "system": ("system_font",),
    "glyph": ("glyph_font",),
}
GUI_BASELINE_SIZE_KEYS = {
    "dialogue": ("text_size",),
    "name": ("name_text_size",),
    "options": ("choice_button_text_size", "button_text_size", "text_size"),
    "interface": ("interface_text_size",),
    "label": ("label_text_size", "interface_text_size"),
    "notify": ("notify_text_size", "interface_text_size"),
    "button": ("button_text_size", "interface_text_size"),
    "choice": ("choice_button_text_size", "text_size"),
}
PASSTHROUGH_OLD_MARKER_RE = re.compile(r"^old:\d+(?:\.\d+)?(?:_\d+)?$")
PASSTHROUGH_FILENAME_RE = re.compile(r"^[A-Za-z0-9_.\\/:\-]+\.(?:txt|log|json|png|jpg|jpeg|webp|ogg|mp3|wav|rpy|rpa)$")
ASCII_LETTER_RE = re.compile(r"[A-Za-z]")
TOKENISH_TEXT_RE = re.compile(r"^[A-Za-z0-9_./\\:#@+\-=]+$")
SPRITE_STATE_LINE_RE = re.compile(r"^(?:[A-Za-z]\s+[0-9][A-Za-z0-9_]+(?:,\s*|\s+)?)+$")
PLACEHOLDER_COUNTER_RE = re.compile(r"^\[[^\]]+\](?:/\d+(?:\.\d+)?)?$")
GALLERY_LABEL_RE = re.compile(r"^[A-Z][A-Za-z'’-]+\s+\([A-Za-z0-9_,. ]+\)$")
SENTENCE_HINT_WORDS = {
    "a", "am", "an", "and", "are", "as", "at", "be", "been", "but", "come", "dear", "did", "do", "for",
    "from", "good", "got", "had", "has", "have", "he", "hello", "help", "her", "here", "hey", "him",
    "his", "how", "i", "if", "in", "is", "it", "just", "know", "like", "love", "me", "my", "no", "not",
    "now", "of", "oh", "on", "or", "our", "out", "please", "poor", "right", "she", "so", "sorry", "that",
    "the", "their", "them", "there", "they", "thing", "this", "to", "up", "was", "we", "well", "what",
    "where", "who", "why", "will", "with", "would", "yes", "you", "your",
}
NON_RETRYABLE_TRANSLATION_ERROR_PATTERNS = (
    "insufficient credits",
    "quota",
    "rate limit exceeded",
    "daily limit",
    "monthly limit",
    "billing",
    "unsupported value:",
    '"code": "unsupported_value"',
    "invalid_request_error",
    "invalid api key",
    "missing or invalid access token",
    "missing bearer or basic authentication",
    "authentication",
    "unauthorized",
    "forbidden",
    "access denied",
)
GEMINI_HARD_FAILURE_PATTERNS = (
    "quota",
    "billing",
    "api key not valid",
    "api key expired",
    "permission denied",
    "daily limit",
    "monthly limit",
)
CHARACTER_TONE_PRESETS: Dict[str, Dict[str, str]] = {
    "custom": {
        "name": "직접 입력",
        "tone_instruction": "",
        "note_instruction": "",
        "suggested_tone": "",
        "suggested_notes": "",
    },
    "ui_clean": {
        "name": "UI 간결체",
        "tone_instruction": "짧고 명확한 인터페이스 문체",
        "note_instruction": "불필요한 수식 없이 즉시 이해되는 버튼/시스템 문장 우선",
        "suggested_tone": "짧고 명확한 인터페이스 문체",
        "suggested_notes": "메뉴/버튼/시스템 문자열은 짧고 명확하게 유지",
    },
    "neutral_conversational": {
        "name": "중립 구어체",
        "tone_instruction": "자연스럽고 과장 없는 현대 한국어 구어체",
        "note_instruction": "설명조보다 실제 대화처럼 짧고 자연스럽게 유지",
        "suggested_tone": "자연스럽고 과장 없는 현대 한국어 구어체",
        "suggested_notes": "설명조보다 실제 대화처럼 짧고 자연스럽게 유지",
    },
    "warm_gentle": {
        "name": "다정 부드러운체",
        "tone_instruction": "말끝이 부드럽고 배려심이 느껴지는 다정한 어투",
        "note_instruction": "직설보다 완곡하고 따뜻한 표현을 우선",
        "suggested_tone": "다정하고 부드럽게 상대를 배려하는 말투",
        "suggested_notes": "직설보다 완곡하고 따뜻한 표현을 우선",
    },
    "bright_playful": {
        "name": "발랄 장난기체",
        "tone_instruction": "반 박자 빠르고 생기 있는 장난스러운 어투",
        "note_instruction": "가벼운 농담과 리듬은 살리되 유행어 남용은 피하기",
        "suggested_tone": "발랄하고 장난기 있는 말투",
        "suggested_notes": "가벼운 농담과 리듬은 살리되 유행어 남용은 피하기",
    },
    "formal_period": {
        "name": "격식 시대극체",
        "tone_instruction": "절제된 시대감과 예의를 살린 격식 있는 어투",
        "note_instruction": "현대식 가벼운 표현보다 품위 있고 단정한 문장을 우선",
        "suggested_tone": "절제된 시대극풍의 격식 있는 어투",
        "suggested_notes": "현대식 가벼운 표현보다 품위 있고 단정한 문장을 우선",
    },
    "rustic_plain": {
        "name": "소박 촌락체",
        "tone_instruction": "생활감 있고 소박한 촌락/해안 지역 구어체",
        "note_instruction": "지역색이 보이면 과하게 표준화하지 말고 생활감을 유지",
        "suggested_tone": "소박하고 생활감 있는 촌락풍 구어체",
        "suggested_notes": "지역색이 보이면 과하게 표준화하지 말고 생활감을 유지",
    },
    "cool_blunt": {
        "name": "무심 직설체",
        "tone_instruction": "짧고 단단하며 군더더기 없는 직설적인 어투",
        "note_instruction": "감정 표현을 과장하지 말고 날카로운 리듬 유지",
        "suggested_tone": "짧고 단단한 직설적 말투",
        "suggested_notes": "감정 표현을 과장하지 말고 날카로운 리듬 유지",
    },
    "seductive_teasing": {
        "name": "능글 유혹체",
        "tone_instruction": "여유롭고 유혹적인 여운이 남는 어투",
        "note_instruction": "노골적 직설보다 미묘한 긴장과 능글맞은 리듬을 우선",
        "suggested_tone": "여유롭고 유혹적인 능글맞은 말투",
        "suggested_notes": "노골적 직설보다 미묘한 긴장과 능글맞은 리듬을 우선",
    },
    "literary_narration": {
        "name": "서정 서술체",
        "tone_instruction": "장면 분위기와 감정선을 살리는 서정적인 서술체",
        "note_instruction": "내레이션과 독백은 문장 호흡과 이미지감을 살려 매끄럽게 유지",
        "suggested_tone": "장면 분위기와 감정선을 살리는 서정적인 서술체",
        "suggested_notes": "내레이션과 독백은 문장 호흡과 이미지감을 살려 매끄럽게 유지",
    },
}
UNSUPPORTED_MODEL_ERROR_PATTERNS = (
    "unsupported value",
    "model_not_found",
    "unknown model",
    "invalid model",
    "not available for this account",
)


@dataclass
class TranslationItem:
    item_id: str
    file_relative_path: str
    file_mode: str
    block_id: Optional[str]
    kind: str
    speaker_id: Optional[str]
    speaker_name: Optional[str]
    line_number: int
    target_line_index: int
    source_text: str
    current_text: str
    before: str
    after: str
    adult: bool
    adult_keywords: List[str]
    source_preview: str
    translation_status: str = "untranslated"
    translation_source: str = "source_text"
    connected_translation_text: str = ""
    connected_translation_source: str = ""
    workbench_translation_text: str = ""
    workbench_translation_source: str = ""
    effective_translation_text: str = ""
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "file_relative_path": self.file_relative_path,
            "kind": self.kind,
            "speaker_id": self.speaker_id,
            "speaker_name": self.speaker_name,
            "line_number": self.line_number,
            "source_text": self.source_text,
            "current_text": self.current_text,
            "translation_status": self.translation_status,
            "translation_source": self.translation_source,
            "connected_translation_text": self.connected_translation_text,
            "connected_translation_source": self.connected_translation_source,
            "workbench_translation_text": self.workbench_translation_text,
            "workbench_translation_source": self.workbench_translation_source,
            "effective_translation_text": self.effective_translation_text,
            "adult": self.adult,
            "adult_keywords": self.adult_keywords,
            "source_preview": self.source_preview,
            "context_before": self.context_before,
            "context_after": self.context_after,
        }


@dataclass
class AnalyzedFile:
    absolute_path: Optional[str]
    file_relative_path: str
    output_relative_path: str
    file_name: str
    file_mode: str
    raw_content: str
    items: List[TranslationItem]

    def to_public_dict(self) -> Dict[str, Any]:
        speaker_counts: Dict[str, int] = {}
        adult_count = 0
        untranslated_count = 0
        game_translated_count = 0
        workbench_translated_count = 0
        for item in self.items:
            if item.adult:
                adult_count += 1
            if item.translation_status == "workbench_translated":
                workbench_translated_count += 1
            elif item.translation_status == "game_translated":
                game_translated_count += 1
            else:
                untranslated_count += 1
            speaker_key = item.speaker_id or NARRATION_PERSONA_KEY
            speaker_counts[speaker_key] = speaker_counts.get(speaker_key, 0) + 1

        preview_items = [item.to_public_dict() for item in self.items[:8]]
        return {
            "absolute_path": self.absolute_path,
            "file_relative_path": self.file_relative_path,
            "output_relative_path": self.output_relative_path,
            "file_name": self.file_name,
            "file_mode": self.file_mode,
            "item_count": len(self.items),
            "adult_item_count": adult_count,
            "untranslated_item_count": untranslated_count,
            "game_translated_item_count": game_translated_count,
            "workbench_translated_item_count": workbench_translated_count,
            "speaker_counts": speaker_counts,
            "preview_items": preview_items,
        }


@dataclass
class TranslationSessionRuntime:
    session_id: str
    session_dir: Path
    attempts_dir: Path
    checkpoint_path: Path
    status_path: Path
    metadata_path: Path
    game_dir: Optional[Path]
    analysis_mode: str
    target_language: str


@dataclass
class TranslationOutputContext:
    game_dir_path: Path
    output_root: Path
    analysis_mode: str
    target_language: str
    gui_baseline: Dict[str, Any]
    normalized_publish_settings: Dict[str, Any]
    publish_bundle: Dict[str, Any]
    publish_root: Optional[Path]
    publish_plan: Optional[Dict[str, Any]]


def log_message(message: str, file_name: str = "General") -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}][Backend][{file_name}] {message}", flush=True)


def find_game_directory(start_path: str) -> Optional[str]:
    if not start_path:
        return None

    current_path = Path(start_path).expanduser()
    try:
        current_path = current_path.resolve()
    except OSError:
        current_path = current_path.absolute()

    if current_path.is_file():
        current_path = current_path.parent

    for candidate in (current_path, *current_path.parents):
        if candidate.name.lower() == "game" and candidate.is_dir():
            return str(candidate)
        game_dir = candidate / "game"
        if game_dir.is_dir():
            return str(game_dir)
    return None


def read_text_file(path: Path) -> str:
    encodings = ("utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1")
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def strip_inline_python_comment(value: str) -> str:
    quote_char = ""
    escaped = False
    output: List[str] = []
    for character in value:
        if escaped:
            output.append(character)
            escaped = False
            continue
        if character == "\\":
            output.append(character)
            escaped = True
            continue
        if quote_char:
            output.append(character)
            if character == quote_char:
                quote_char = ""
            continue
        if character in {'"', "'"}:
            output.append(character)
            quote_char = character
            continue
        if character == "#":
            break
        output.append(character)
    return "".join(output).strip()


def resolve_gui_language_default(language_code: str, fallback: Optional[str] = None) -> str:
    normalized = normalize_language_code(language_code)
    if normalized.startswith("ko"):
        return "korean-with-spaces"
    return fallback or "unicode"


def normalize_language_code(value: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "_", (value or "").strip().lower()).strip("_") or DEFAULT_TARGET_LANGUAGE


def default_publish_language_code(target_language: str, analysis_mode: str) -> str:
    normalized = normalize_language_code(target_language)
    if analysis_mode == "translation_layer":
        if normalized.endswith("_workbench"):
            return normalized
        return f"{normalized}_workbench"
    return normalized


def get_workbench_output_base(game_dir_path: Path) -> Path:
    return game_dir_path.parent / "_translator_output"


def get_translation_layer_stage_root(game_dir_path: Path, target_language: str) -> Path:
    normalized = normalize_language_code(target_language)
    return get_workbench_output_base(game_dir_path) / f"{normalized}_translation_layer"


def get_source_stage_root(game_dir_path: Path, target_language: str) -> Path:
    normalized = normalize_language_code(target_language)
    return get_workbench_output_base(game_dir_path) / f"{normalized}_source"


def get_legacy_translation_layer_stage_root(game_dir_path: Path, target_language: str) -> Path:
    normalized = normalize_language_code(target_language)
    return game_dir_path / "tl" / f"{normalized}_ai"


def remove_tree_force(target_path: Path) -> None:
    if not target_path.exists():
        return

    def _handle_remove_readonly(func, path, exc_info):  # type: ignore[no-untyped-def]
        try:
            os.chmod(path, stat.S_IWRITE)
        except OSError:
            pass
        func(path)

    shutil.rmtree(target_path, onerror=_handle_remove_readonly)


def legacy_translation_layer_stage_needs_migration(legacy_root: Path, target_language: str) -> bool:
    normalized_target = normalize_language_code(target_language)
    header_pattern = re.compile(rf"^\s*translate\s+{re.escape(normalized_target)}\b", re.MULTILINE)
    for candidate in legacy_root.rglob("*.rpy"):
        try:
            content = candidate.read_text(encoding="utf-8")
        except OSError:
            continue
        if header_pattern.search(content):
            return True
    return False


def migrate_legacy_translation_layer_stage_root(game_dir_path: Path, target_language: str) -> Dict[str, Any]:
    legacy_root = get_legacy_translation_layer_stage_root(game_dir_path, target_language)
    stage_root = get_translation_layer_stage_root(game_dir_path, target_language)
    if not legacy_root.is_dir():
        return {
            "migrated": False,
            "legacy_root": str(legacy_root),
            "stage_root": str(stage_root),
            "reason": "missing",
        }
    if not legacy_translation_layer_stage_needs_migration(legacy_root, target_language):
        return {
            "migrated": False,
            "legacy_root": str(legacy_root),
            "stage_root": str(stage_root),
            "reason": "already_safe",
        }

    stage_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(legacy_root, stage_root, dirs_exist_ok=True)
    remove_tree_force(legacy_root)
    clear_renpy_cache_files(game_dir_path)
    clear_translation_compiled_files(game_dir_path)
    return {
        "migrated": True,
        "legacy_root": str(legacy_root),
        "stage_root": str(stage_root),
        "reason": "legacy_stage_conflict",
    }


def migrate_embedded_workbench_output_root(game_dir_path: Path) -> Dict[str, Any]:
    embedded_root = game_dir_path / "_translator_output"
    safe_root = get_workbench_output_base(game_dir_path)
    if not embedded_root.is_dir():
        return {
            "migrated": False,
            "embedded_root": str(embedded_root),
            "safe_root": str(safe_root),
            "reason": "missing",
        }

    safe_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(embedded_root, safe_root, dirs_exist_ok=True)
    remove_tree_force(embedded_root)
    clear_renpy_cache_files(game_dir_path)
    clear_translation_compiled_files(game_dir_path)
    return {
        "migrated": True,
        "embedded_root": str(embedded_root),
        "safe_root": str(safe_root),
        "reason": "embedded_stage_conflict",
    }


def migrate_nested_workbench_artifacts(game_dir_path: Path) -> Dict[str, Any]:
    tl_root = game_dir_path / "tl"
    safe_root = get_workbench_output_base(game_dir_path) / "_recovered_nested"
    moved_paths: List[Dict[str, str]] = []

    if not tl_root.is_dir():
        return {
            "migrated": False,
            "safe_root": str(safe_root),
            "moved_paths": moved_paths,
            "reason": "missing_tl",
        }

    nested_dirs = sorted(
        (
            path
            for path in tl_root.rglob("*")
            if path.is_dir() and path.name in WORKBENCH_ARTIFACT_DIRNAMES
        ),
        key=lambda candidate: len(candidate.parts),
    )
    for nested_dir in nested_dirs:
        if not nested_dir.exists():
            continue
        relative_key = "__".join(nested_dir.relative_to(tl_root).parts)
        destination = safe_root / relative_key
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(nested_dir, destination, dirs_exist_ok=True)
        remove_tree_force(nested_dir)
        moved_paths.append(
            {
                "from": str(nested_dir),
                "to": str(destination),
            }
        )

    if moved_paths:
        clear_renpy_cache_files(game_dir_path)
        clear_translation_compiled_files(game_dir_path)

    return {
        "migrated": bool(moved_paths),
        "safe_root": str(safe_root),
        "moved_paths": moved_paths,
        "reason": "nested_artifact_conflict" if moved_paths else "already_safe",
    }


def invalidate_compiled_translation_file(source_path: Path) -> Optional[str]:
    if source_path.suffix.lower() != ".rpy":
        return None
    compiled_path = source_path.with_suffix(source_path.suffix + "c")
    if not compiled_path.exists():
        return None
    try:
        compiled_path.unlink()
    except OSError:
        return None
    return str(compiled_path)


def clear_renpy_cache_files(game_dir_path: Path) -> List[str]:
    cache_dir = game_dir_path / "cache"
    if not cache_dir.is_dir():
        return []

    removed_files: List[str] = []
    for cache_name in sorted(RENPY_CACHE_FILENAMES):
        cache_path = cache_dir / cache_name
        if not cache_path.exists():
            continue
        try:
            cache_path.unlink()
            removed_files.append(str(cache_path))
        except OSError:
            continue
    return removed_files


def clear_translation_compiled_files(game_dir_path: Path) -> List[str]:
    removed_files: List[str] = []
    root_paths = [
        game_dir_path / "tl",
        game_dir_path / "_translator_output",
        get_workbench_output_base(game_dir_path),
    ]
    for root_path in root_paths:
        if not root_path.is_dir():
            continue
        for compiled_path in root_path.rglob("*.rpyc"):
            try:
                compiled_path.unlink()
                removed_files.append(str(compiled_path))
            except OSError:
                continue
    return removed_files


def default_publish_display_name(language_code: str) -> str:
    normalized = normalize_language_code(language_code)
    if normalized.startswith("ko"):
        return "한국어 (AI 번역)"
    return f"{normalized} (AI Translation)"


def normalize_publish_language_code(language_code: str, target_language: str, analysis_mode: str) -> str:
    normalized = normalize_language_code(language_code)
    if analysis_mode != "translation_layer":
        return normalized

    target_normalized = normalize_language_code(target_language)
    if normalized == f"{target_normalized}_ai":
        return default_publish_language_code(target_language, analysis_mode)
    return normalized


def parse_scalar_literal(raw_value: str) -> Any:
    stripped = (raw_value or "").strip()
    if not stripped:
        return None
    try:
        return ast.literal_eval(stripped)
    except (ValueError, SyntaxError):
        return stripped


def resolve_gui_assignment_value(
    raw_assignments: Dict[str, str],
    key: str,
    seen: Optional[set] = None,
) -> Any:
    if key not in raw_assignments:
        return None
    if seen is None:
        seen = set()
    if key in seen:
        return raw_assignments[key].strip()

    seen.add(key)
    raw_value = raw_assignments[key].strip()
    reference_match = re.fullmatch(r"gui\.([A-Za-z0-9_]+)", raw_value)
    if reference_match:
        return resolve_gui_assignment_value(raw_assignments, reference_match.group(1), seen)

    literal = parse_scalar_literal(raw_value)
    if isinstance(literal, (int, float, str)):
        return literal
    return raw_value


def normalize_font_reference(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().strip('"').strip("'")


def try_parse_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    stripped = str(value).strip()
    if not stripped:
        return None
    try:
        return int(round(float(stripped)))
    except ValueError:
        return None


def resolve_font_path(game_dir: Path, font_reference: str) -> Optional[Path]:
    normalized = normalize_font_reference(font_reference)
    if not normalized:
        return None

    font_path = Path(normalized)
    if font_path.is_absolute():
        return font_path if font_path.is_file() else None

    candidates = [
        game_dir / normalized,
        APP_ROOT / normalized,
        game_dir / "gui" / normalized,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    basename = Path(normalized).name.lower()
    matches = sorted(
        candidate
        for candidate in game_dir.rglob("*")
        if candidate.is_file() and candidate.suffix.lower() in FONT_EXTENSIONS and candidate.name.lower() == basename
    )
    return matches[0] if matches else None


def build_public_font_reference(game_dir: Path, font_reference: str) -> str:
    resolved = resolve_font_path(game_dir, font_reference)
    if resolved is None:
        return normalize_font_reference(font_reference)
    try:
        return str(resolved.relative_to(game_dir)).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def build_public_path(game_dir: Path, path_value: Path) -> str:
    normalized = path_value.resolve()
    for base in (game_dir, game_dir.parent):
        try:
            return str(normalized.relative_to(base.resolve())).replace("\\", "/")
        except ValueError:
            continue
    return str(normalized).replace("\\", "/")


def get_windows_font_roots() -> List[Tuple[str, Path]]:
    roots: List[Tuple[str, Path]] = []
    windir = Path(os.environ.get("WINDIR") or "C:/Windows")
    windows_fonts = windir / "Fonts"
    if windows_fonts.is_dir():
        roots.append(("windows", windows_fonts))

    local_font_root = Path(os.environ.get("LOCALAPPDATA") or "") / "Microsoft" / "Windows" / "Fonts"
    if local_font_root.is_dir():
        roots.append(("user", local_font_root))

    return roots


def clean_font_display_name(value: str) -> str:
    cleaned = re.sub(r"\s*\((TrueType|OpenType|All Res)\)\s*$", "", str(value or "").strip(), flags=re.IGNORECASE)
    return cleaned.strip()


def probe_font_name(font_path: Path) -> Tuple[str, str]:
    fallback_name = clean_font_display_name(font_path.stem.replace("_", " "))
    try:
        font = ImageFont.truetype(str(font_path), size=28)
        family_name, style_name = font.getname()
        return clean_font_display_name(family_name or fallback_name), clean_font_display_name(style_name or "Regular")
    except Exception:  # noqa: BLE001
        return fallback_name, "Regular"


def build_system_font_entry(font_path: Path, display_name: str, source: str) -> Dict[str, Any]:
    family_name, style_name = probe_font_name(font_path)
    cleaned_display_name = clean_font_display_name(display_name or family_name or font_path.stem)
    font_id = hashlib.sha1(str(font_path.resolve()).lower().encode("utf-8")).hexdigest()[:16]
    return {
        "font_id": font_id,
        "display_name": cleaned_display_name,
        "family_name": family_name,
        "style_name": style_name,
        "file_name": font_path.name,
        "path": str(font_path.resolve()),
        "source": source,
    }


@lru_cache(maxsize=1)
def discover_system_fonts() -> List[Dict[str, Any]]:
    entries_by_path: Dict[str, Dict[str, Any]] = {}
    font_roots = {label: path for label, path in get_windows_font_roots()}

    def register_font(font_path: Path, display_name: str, source: str) -> None:
        if not font_path.is_file() or font_path.suffix.lower() not in FONT_EXTENSIONS:
            return
        normalized_path = str(font_path.resolve())
        if normalized_path in entries_by_path:
            existing = entries_by_path[normalized_path]
            if display_name and len(display_name) > len(existing.get("display_name") or ""):
                existing["display_name"] = clean_font_display_name(display_name)
            return
        entries_by_path[normalized_path] = build_system_font_entry(font_path, display_name, source)

    if winreg is not None:
        registry_sources = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts", "windows"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts", "user"),
        ]
        for hive, key_path, source_label in registry_sources:
            try:
                with winreg.OpenKey(hive, key_path) as registry_key:
                    value_count = winreg.QueryInfoKey(registry_key)[1]
                    for index in range(value_count):
                        value_name, raw_value, _ = winreg.EnumValue(registry_key, index)
                        font_value = str(raw_value or "").strip()
                        if not font_value:
                            continue
                        font_path = Path(font_value)
                        if not font_path.is_absolute():
                            font_root = font_roots.get(source_label) or font_roots.get("windows")
                            if font_root is None:
                                continue
                            font_path = font_root / font_value
                        register_font(font_path, value_name, source_label)
            except OSError:
                continue

    for source_label, font_root in get_windows_font_roots():
        for suffix in sorted(FONT_EXTENSIONS):
            for font_path in sorted(font_root.glob(f"*{suffix}")):
                register_font(font_path, font_path.stem, source_label)

    return sorted(
        entries_by_path.values(),
        key=lambda entry: (
            str(entry.get("display_name") or "").lower(),
            str(entry.get("style_name") or "").lower(),
            str(entry.get("file_name") or "").lower(),
        ),
    )


def get_system_font_entry(font_id: str) -> Optional[Dict[str, Any]]:
    normalized_id = str(font_id or "").strip()
    if not normalized_id:
        return None
    for entry in discover_system_fonts():
        if entry.get("font_id") == normalized_id:
            return entry
    return None


def resolve_font_preview_path(
    font_id: str = "",
    path_value: str = "",
    font_reference: str = "",
    game_dir: str = "",
) -> Optional[Path]:
    if font_id:
        font_entry = get_system_font_entry(font_id)
        if font_entry:
            font_path = Path(font_entry["path"])
            return font_path if font_path.is_file() else None

    raw_path = normalize_font_reference(path_value)
    if raw_path:
        font_path = Path(raw_path)
        if font_path.is_file() and font_path.suffix.lower() in FONT_EXTENSIONS:
            return font_path

    normalized_reference = normalize_font_reference(font_reference)
    normalized_game_dir = str(game_dir or "").strip()
    if normalized_reference and normalized_game_dir:
        try:
            return resolve_font_path(Path(normalized_game_dir), normalized_reference)
        except Exception:  # noqa: BLE001
            return None
    return None


def build_font_preview_image(
    font_path: Path,
    preview_text: str,
    width: int = 640,
    height: int = 140,
) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), (14, 24, 31, 255))
    draw = ImageDraw.Draw(canvas)

    sample_candidates = []
    primary_sample = str(preview_text or DEFAULT_FONT_PREVIEW_TEXT).strip() or DEFAULT_FONT_PREVIEW_TEXT
    for sample in (
        primary_sample[:120],
        "Preview Aa Bb 123",
        "Aa Bb 123",
        Path(font_path).stem[:32] or "Font",
    ):
        if sample and sample not in sample_candidates:
            sample_candidates.append(sample)

    font = None
    bbox = None
    sample_text = sample_candidates[0]
    horizontal_padding = max(12, int(width * 0.045))
    vertical_padding = max(10, int(height * 0.12))
    max_candidate_size = max(28, min(96, int(height * 0.82)))
    min_candidate_size = 20

    for candidate_text in sample_candidates:
        for candidate_size in range(max_candidate_size, min_candidate_size - 1, -2):
            try:
                candidate_font = ImageFont.truetype(str(font_path), size=candidate_size)
                candidate_bbox = candidate_font.getbbox(candidate_text)
                probe_image = Image.new("L", (max(width, 8), max(height, 8)), 0)
                ImageDraw.Draw(probe_image).text((4, 4), candidate_text, font=candidate_font, fill=255)
            except Exception:  # noqa: BLE001
                continue
            text_width = candidate_bbox[2] - candidate_bbox[0]
            text_height = candidate_bbox[3] - candidate_bbox[1]
            if text_width <= width - (horizontal_padding * 2) and text_height <= height - (vertical_padding * 2):
                font = candidate_font
                bbox = candidate_bbox
                sample_text = candidate_text
                break
            font = candidate_font
            bbox = candidate_bbox
            sample_text = candidate_text
        if font is not None and bbox is not None:
            break

    if font is None or bbox is None:
        raise RuntimeError(f"폰트를 렌더링할 수 없습니다: {font_path}")

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = horizontal_padding - bbox[0]
    text_y = max(vertical_padding, int((height - text_height) / 2) - bbox[1])

    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=20, outline=(54, 73, 81, 255), width=1)
    draw.text((text_x, text_y), sample_text, font=font, fill=(244, 246, 248, 255))
    return canvas


def plan_publish_font_reference(
    game_dir_path: Path,
    publish_root: Path,
    font_reference: str,
    planned_assets: Dict[str, str],
) -> str:
    normalized_reference = normalize_font_reference(font_reference)
    if not normalized_reference:
        return ""

    resolved = resolve_font_path(game_dir_path, normalized_reference)
    if resolved is None:
        return normalized_reference

    try:
        return str(resolved.relative_to(game_dir_path)).replace("\\", "/")
    except ValueError:
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", resolved.stem).strip("._") or "font"
        hash_suffix = hashlib.sha1(str(resolved.resolve()).lower().encode("utf-8")).hexdigest()[:8]
        asset_relative_path = f"_workbench_fonts/{safe_stem}_{hash_suffix}{resolved.suffix.lower()}"
        planned_assets[str(resolved.resolve())] = asset_relative_path
        publish_relative_root = str(publish_root.relative_to(game_dir_path)).replace("\\", "/")
        return f"{publish_relative_root}/{asset_relative_path}"


def measure_font_signature(font_path: Optional[Path], font_size: Optional[int]) -> Optional[Tuple[float, float]]:
    if not font_path or not font_size or font_size <= 0 or not font_path.is_file():
        return None

    sample_text = "가나다라마바사아자차카타파하 The quick brown fox 0123456789"
    try:
        font = ImageFont.truetype(str(font_path), size=int(font_size))
        bbox = font.getbbox(sample_text)
    except Exception:  # noqa: BLE001
        return None

    width = max(1.0, float(bbox[2] - bbox[0]))
    height = max(1.0, float(bbox[3] - bbox[1]))
    return width, height


def compute_font_auto_scale(
    game_dir: Path,
    baseline_font_reference: str,
    candidate_font_reference: str,
    baseline_size: Optional[int],
) -> float:
    baseline_path = resolve_font_path(game_dir, baseline_font_reference)
    candidate_path = resolve_font_path(game_dir, candidate_font_reference)
    baseline_signature = measure_font_signature(baseline_path, baseline_size)
    candidate_signature = measure_font_signature(candidate_path, baseline_size)
    if not baseline_signature or not candidate_signature:
        return 1.0

    base_width, base_height = baseline_signature
    cand_width, cand_height = candidate_signature
    if cand_width <= 0 or cand_height <= 0:
        return 1.0

    height_ratio = base_height / cand_height
    width_ratio = base_width / cand_width
    blended_ratio = (height_ratio * 0.7) + (width_ratio * 0.3)
    return max(0.75, min(1.35, blended_ratio))


def extract_translation_font_profiles(
    all_rpy_files: List[Path],
    game_dir: Path,
    size_defaults: Dict[str, Optional[int]],
) -> List[Dict[str, Any]]:
    profile_map: Dict[str, Dict[str, Any]] = {}

    for file_path in all_rpy_files:
        if file_path.name.startswith("zz_workbench_"):
            continue
        lines = read_text_file(file_path).splitlines()
        pointer = 0
        while pointer < len(lines):
            python_match = TRANSLATE_PYTHON_BLOCK_RE.match(lines[pointer])
            style_match = TRANSLATE_STYLE_BLOCK_RE.match(lines[pointer])

            if python_match:
                language_code = normalize_language_code(python_match.group("lang"))
                if language_code.endswith("_workbench"):
                    pointer += 1
                    continue
                profile = profile_map.setdefault(
                    language_code,
                    {
                        "language_code": language_code,
                        "source_files": set(),
                        "gui_assignments": {},
                        "style_overrides": {},
                    },
                )
                profile["source_files"].add(str(file_path.relative_to(game_dir)).replace("\\", "/"))
                pointer += 1
                while pointer < len(lines):
                    line = lines[pointer]
                    if not line.strip():
                        pointer += 1
                        continue
                    if not re.match(r"^\s+", line):
                        break
                    assignment_match = re.match(r"^\s*gui\.(?P<name>[A-Za-z0-9_]+)\s*=\s*(?P<value>.+?)\s*$", line)
                    if assignment_match:
                        profile["gui_assignments"][assignment_match.group("name")] = strip_inline_python_comment(
                            assignment_match.group("value")
                        )
                    pointer += 1
                continue

            if style_match:
                language_code = normalize_language_code(style_match.group("lang"))
                if language_code.endswith("_workbench"):
                    pointer += 1
                    continue
                style_name = style_match.group("style")
                profile = profile_map.setdefault(
                    language_code,
                    {
                        "language_code": language_code,
                        "source_files": set(),
                        "gui_assignments": {},
                        "style_overrides": {},
                    },
                )
                profile["source_files"].add(str(file_path.relative_to(game_dir)).replace("\\", "/"))
                style_entry = profile["style_overrides"].setdefault(style_name, {})
                pointer += 1
                while pointer < len(lines):
                    line = lines[pointer]
                    if not line.strip():
                        pointer += 1
                        continue
                    if not re.match(r"^\s+", line):
                        break
                    font_match = STYLE_FONT_RE.match(line)
                    if font_match:
                        style_entry["font_path"] = normalize_font_reference(font_match.group("font"))
                    size_match = STYLE_SIZE_RE.match(line)
                    if size_match:
                        style_entry["size"] = try_parse_int(size_match.group("size"))
                    pointer += 1
                continue

            pointer += 1

    presets: List[Dict[str, Any]] = []
    for language_code, profile in sorted(profile_map.items()):
        gui_assignments = profile["gui_assignments"]
        if not gui_assignments and not profile["style_overrides"]:
            continue

        font_defaults = {
            key: normalize_font_reference(
                next(
                    (
                        resolve_gui_assignment_value(gui_assignments, candidate)
                        for candidate in candidates
                        if resolve_gui_assignment_value(gui_assignments, candidate) is not None
                    ),
                    "",
                )
            )
            for key, candidates in GUI_BASELINE_FONT_KEYS.items()
        }
        size_values = {
            key: try_parse_int(
                next(
                    (
                        resolve_gui_assignment_value(gui_assignments, candidate)
                        for candidate in candidates
                        if resolve_gui_assignment_value(gui_assignments, candidate) is not None
                    ),
                    None,
                )
            )
            for key, candidates in GUI_BASELINE_SIZE_KEYS.items()
        }

        preset = {
            "id": f"translation_profile_{language_code}",
            "name": f"기존 번역 예시 · {language_code}",
            "description": ", ".join(sorted(profile["source_files"])) or f"{language_code} translation profile",
            "settings": {
                "dialogue_font": font_defaults.get("dialogue") or "",
                "name_font": font_defaults.get("name") or "",
                "options_font": font_defaults.get("options") or "",
                "interface_font": font_defaults.get("interface") or "",
                "system_font": font_defaults.get("system") or "",
                "glyph_font": font_defaults.get("glyph") or "",
                "dialogue_scale": round((size_values.get("dialogue") or size_defaults.get("dialogue") or 1) / max(1, size_defaults.get("dialogue") or 1), 2),
                "name_scale": round((size_values.get("name") or size_defaults.get("name") or 1) / max(1, size_defaults.get("name") or 1), 2),
                "options_scale": round((size_values.get("options") or size_defaults.get("options") or 1) / max(1, size_defaults.get("options") or 1), 2),
                "interface_scale": round((size_values.get("interface") or size_defaults.get("interface") or 1) / max(1, size_defaults.get("interface") or 1), 2),
                "extra_style_overrides": [
                    {
                        "style_name": style_name,
                        "font_path": style_data.get("font_path") or "",
                        "size": style_data.get("size"),
                    }
                    for style_name, style_data in sorted(profile["style_overrides"].items())
                    if style_data.get("font_path") or style_data.get("size") is not None
                ],
            },
        }
        presets.append(preset)

    return presets


def find_preferred_font_candidate(font_candidates: List[str], preferred_names: List[str]) -> str:
    lowered_lookup = {candidate.lower(): candidate for candidate in font_candidates}
    for preferred_name in preferred_names:
        if preferred_name.lower() in lowered_lookup:
            return lowered_lookup[preferred_name.lower()]

    for preferred_name in preferred_names:
        preferred_basename = Path(preferred_name).name.lower()
        for candidate in font_candidates:
            if Path(candidate).name.lower() == preferred_basename:
                return candidate
    return ""


def build_korean_font_presets(font_candidates: List[str]) -> List[Dict[str, Any]]:
    medium_font = find_preferred_font_candidate(
        font_candidates,
        ["GmarketSansTTFMedium.ttf", "fonts/GmarketSansTTFMedium.ttf", "tl/ko/GmarketSansTTFMedium.ttf"],
    )
    bold_font = find_preferred_font_candidate(
        font_candidates,
        ["GmarketSansTTFBold.ttf", "fonts/GmarketSansTTFBold.ttf", "tl/ko/GmarketSansTTFBold.ttf"],
    )
    light_font = find_preferred_font_candidate(
        font_candidates,
        ["GmarketSansTTFLight.ttf", "tl/ko/GmarketSansTTFLight.ttf"],
    )

    if not medium_font and not bold_font and not light_font:
        return []

    medium_or_bold = medium_font or bold_font or light_font
    bold_or_medium = bold_font or medium_font or light_font
    light_or_medium = light_font or medium_font or bold_font

    return [
        {
            "id": "ko_balanced_modern",
            "name": "한글 기본 · 균형형",
            "description": "대사는 Medium, 이름은 Bold, 옵션과 UI는 Medium으로 맞춘 무난한 기본 프리셋입니다.",
            "settings": {
                "font_preset_id": "ko_balanced_modern",
                "dialogue_font": medium_or_bold,
                "name_font": bold_or_medium,
                "options_font": medium_or_bold,
                "interface_font": medium_or_bold,
                "system_font": medium_or_bold,
                "glyph_font": "",
                "dialogue_scale": 1.0,
                "name_scale": 0.96,
                "options_scale": 0.94,
                "interface_scale": 0.94,
                "extra_style_overrides": [],
            },
        },
        {
            "id": "ko_story_soft",
            "name": "한글 기본 · 소설형",
            "description": "대사는 Light 계열로 부드럽게, 이름은 Bold로 살리고 UI는 Medium으로 유지하는 프리셋입니다.",
            "settings": {
                "font_preset_id": "ko_story_soft",
                "dialogue_font": light_or_medium,
                "name_font": bold_or_medium,
                "options_font": medium_or_bold,
                "interface_font": medium_or_bold,
                "system_font": medium_or_bold,
                "glyph_font": "",
                "dialogue_scale": 1.03,
                "name_scale": 0.96,
                "options_scale": 0.95,
                "interface_scale": 0.95,
                "extra_style_overrides": [],
            },
        },
        {
            "id": "ko_choice_strong",
            "name": "한글 기본 · 강조형",
            "description": "선택지와 이름을 더 단단하게 보이게 하고, 대사는 읽기 쉬운 Medium으로 두는 프리셋입니다.",
            "settings": {
                "font_preset_id": "ko_choice_strong",
                "dialogue_font": medium_or_bold,
                "name_font": bold_or_medium,
                "options_font": bold_or_medium,
                "interface_font": medium_or_bold,
                "system_font": medium_or_bold,
                "glyph_font": "",
                "dialogue_scale": 0.98,
                "name_scale": 0.95,
                "options_scale": 0.92,
                "interface_scale": 0.93,
                "extra_style_overrides": [],
            },
        },
    ]


def find_keyword_font_candidate(font_candidates: List[str], keyword_groups: List[List[str]]) -> str:
    normalized_candidates = [(candidate, Path(candidate).name.lower()) for candidate in font_candidates]
    for keywords in keyword_groups:
        normalized_keywords = [keyword.lower() for keyword in keywords if keyword]
        for candidate, basename in normalized_candidates:
            if all(keyword in basename for keyword in normalized_keywords):
                return candidate
    return ""


def build_curated_korean_font_presets(font_candidates: List[str]) -> List[Dict[str, Any]]:
    medium_font = find_preferred_font_candidate(
        font_candidates,
        [
            "Pretendard-Medium.otf",
            "PretendardVariable.ttf",
            "NotoSansKR-Medium.otf",
            "NotoSansCJKkr-Medium.otf",
            "NanumSquareNeo-bRg.ttf",
            "NanumSquareRoundR.ttf",
            "GmarketSansTTFMedium.ttf",
            "fonts/GmarketSansTTFMedium.ttf",
            "tl/ko/GmarketSansTTFMedium.ttf",
            "Malgun.ttf",
        ],
    )
    bold_font = find_preferred_font_candidate(
        font_candidates,
        [
            "Pretendard-Bold.otf",
            "Pretendard-SemiBold.otf",
            "NotoSansKR-Bold.otf",
            "NotoSansCJKkr-Bold.otf",
            "NanumSquareNeo-cBd.ttf",
            "NanumSquareRoundB.ttf",
            "GmarketSansTTFBold.ttf",
            "fonts/GmarketSansTTFBold.ttf",
            "tl/ko/GmarketSansTTFBold.ttf",
            "malgunbd.ttf",
        ],
    )
    light_font = find_preferred_font_candidate(
        font_candidates,
        [
            "Pretendard-Light.otf",
            "NotoSansKR-Light.otf",
            "NotoSansCJKkr-Light.otf",
            "NanumSquareNeo-aLt.ttf",
            "GmarketSansTTFLight.ttf",
            "tl/ko/GmarketSansTTFLight.ttf",
        ],
    )
    story_font = find_preferred_font_candidate(
        font_candidates,
        [
            "RIDIBatang.otf",
            "NanumMyeongjo.ttf",
            "KoPubBatangMedium.ttf",
            "NotoSerifKR-Regular.otf",
            "NotoSerifCJKkr-Regular.otf",
            "SourceHanSerifK-Regular.otf",
        ],
    )

    medium_font = medium_font or find_keyword_font_candidate(
        font_candidates,
        [
            ["pretendard", "medium"],
            ["pretendard"],
            ["noto", "sans", "kr"],
            ["noto", "sans", "cjk", "kr"],
            ["nanumsquare"],
            ["gmarket", "medium"],
            ["malgun"],
        ],
    )
    bold_font = bold_font or find_keyword_font_candidate(
        font_candidates,
        [
            ["pretendard", "bold"],
            ["pretendard", "semi"],
            ["noto", "sans", "bold"],
            ["noto", "kr", "bold"],
            ["nanumsquare", "bold"],
            ["gmarket", "bold"],
            ["malgun", "bd"],
        ],
    )
    light_font = light_font or find_keyword_font_candidate(
        font_candidates,
        [
            ["pretendard", "light"],
            ["noto", "sans", "light"],
            ["nanumsquare", "light"],
            ["gmarket", "light"],
        ],
    )
    story_font = story_font or find_keyword_font_candidate(
        font_candidates,
        [
            ["ridi", "batang"],
            ["nanum", "myeongjo"],
            ["kopub", "batang"],
            ["noto", "serif", "kr"],
            ["noto", "serif", "cjk", "kr"],
            ["sourcehan", "serif"],
        ],
    )

    if not medium_font and not bold_font and not light_font and not story_font:
        return []

    medium_or_bold = medium_font or bold_font or light_font or story_font
    bold_or_medium = bold_font or medium_font or light_font or story_font
    light_or_medium = light_font or medium_font or bold_font or story_font
    story_or_soft = story_font or light_or_medium

    return [
        {
            "id": "ko_balanced_modern",
            "name": "한글 기본 · 균형형",
            "description": "대사는 중간 굵기, 이름은 강조체, 옵션과 UI는 안정적인 산세리프로 맞춘 기본 프리셋입니다.",
            "settings": {
                "font_preset_id": "ko_balanced_modern",
                "dialogue_font": medium_or_bold,
                "name_font": bold_or_medium,
                "options_font": medium_or_bold,
                "interface_font": medium_or_bold,
                "system_font": medium_or_bold,
                "glyph_font": "",
                "dialogue_scale": 1.0,
                "name_scale": 0.96,
                "options_scale": 0.94,
                "interface_scale": 0.94,
                "extra_style_overrides": [],
            },
        },
        {
            "id": "ko_story_soft",
            "name": "한글 기본 · 소설형",
            "description": "본문은 부드럽고 읽기 편하게, 이름과 선택지는 선명하게 보이도록 조합한 스토리 중심 프리셋입니다.",
            "settings": {
                "font_preset_id": "ko_story_soft",
                "dialogue_font": story_or_soft,
                "name_font": bold_or_medium,
                "options_font": medium_or_bold,
                "interface_font": medium_or_bold,
                "system_font": medium_or_bold,
                "glyph_font": "",
                "dialogue_scale": 1.03,
                "name_scale": 0.96,
                "options_scale": 0.95,
                "interface_scale": 0.95,
                "extra_style_overrides": [],
            },
        },
        {
            "id": "ko_choice_strong",
            "name": "한글 기본 · 강조형",
            "description": "선택지와 이름을 또렷하게 살리고, 본문은 과하게 무겁지 않게 유지하는 강조형 프리셋입니다.",
            "settings": {
                "font_preset_id": "ko_choice_strong",
                "dialogue_font": medium_or_bold,
                "name_font": bold_or_medium,
                "options_font": bold_or_medium,
                "interface_font": medium_or_bold,
                "system_font": medium_or_bold,
                "glyph_font": "",
                "dialogue_scale": 0.98,
                "name_scale": 0.95,
                "options_scale": 0.92,
                "interface_scale": 0.93,
                "extra_style_overrides": [],
            },
        },
    ]


def build_font_presets(
    gui_baseline: Dict[str, Any],
    translation_profiles: List[Dict[str, Any]],
    font_candidates: List[str],
) -> List[Dict[str, Any]]:
    base_preset = {
        "id": "preserve_original",
        "name": "원작 기본",
        "description": "원본 게임의 GUI 폰트/크기를 유지합니다.",
        "settings": {
            "dialogue_font": gui_baseline.get("font_defaults", {}).get("dialogue") or "",
            "name_font": gui_baseline.get("font_defaults", {}).get("name") or "",
            "options_font": gui_baseline.get("font_defaults", {}).get("options") or "",
            "interface_font": gui_baseline.get("font_defaults", {}).get("interface") or "",
            "system_font": gui_baseline.get("font_defaults", {}).get("system") or "",
            "glyph_font": gui_baseline.get("font_defaults", {}).get("glyph") or "",
            "dialogue_scale": 1.0,
            "name_scale": 1.0,
            "options_scale": 1.0,
            "interface_scale": 1.0,
            "extra_style_overrides": [],
        },
    }

    presets = [base_preset, *build_curated_korean_font_presets(font_candidates)]
    seen_names = {base_preset["name"]}
    for profile in translation_profiles:
        if profile["name"] in seen_names:
            continue
        presets.append(profile)
        seen_names.add(profile["name"])
    return presets


def build_default_publish_settings(
    target_language: str,
    analysis_mode: str,
    gui_baseline: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    language_code = default_publish_language_code(target_language, analysis_mode)
    baseline_gui_language = (gui_baseline or {}).get("base_gui_language") or "unicode"
    settings = {
        "enabled": analysis_mode == "translation_layer",
        "language_code": language_code,
        "display_name": default_publish_display_name(language_code),
        "gui_language": resolve_gui_language_default(language_code, baseline_gui_language),
        "auto_adjust_sizes": True,
        "font_preset_id": "",
        "dialogue_font": "",
        "name_font": "",
        "options_font": "",
        "interface_font": "",
        "system_font": "",
        "glyph_font": "",
        "dialogue_scale": 1.0,
        "name_scale": 1.0,
        "options_scale": 1.0,
        "interface_scale": 1.0,
        "extra_style_overrides": [],
    }

    if language_code.lower().startswith("ko"):
        for preset in (gui_baseline or {}).get("font_presets") or []:
            if preset.get("id") != "ko_balanced_modern":
                continue
            preset_settings = dict(preset.get("settings") or {})
            for key in (
                "font_preset_id",
                "dialogue_font",
                "name_font",
                "options_font",
                "interface_font",
                "system_font",
                "glyph_font",
                "dialogue_scale",
                "name_scale",
                "options_scale",
                "interface_scale",
                "extra_style_overrides",
            ):
                if key in preset_settings:
                    settings[key] = preset_settings[key]
            break

    return settings


IGNORED_GAME_SCRIPT_PARTS = {"tl", "_translator_output", "_translator_logs"}
WORKBENCH_ARTIFACT_DIRNAMES = {"_translator_output", "_translator_logs"}
NON_TEMPLATE_SOURCE_FILES = {"auto.rpy", "gui.rpy", "label_log.rpy", "set_default_language_at_startup.rpy"}
SYNTHETIC_TEMPLATE_FILES = {"common.rpy"}


def is_primary_game_script(path: Path, game_dir: Path) -> bool:
    try:
        relative_parts = set(path.relative_to(game_dir).parts)
    except ValueError:
        return False
    return not bool(relative_parts & IGNORED_GAME_SCRIPT_PARTS)


def list_game_source_scripts(game_dir: Path) -> List[Path]:
    return [
        path
        for path in sorted(game_dir.rglob("*.rpy"))
        if is_primary_game_script(path, game_dir)
    ]


def list_translation_template_files(translation_root: Path) -> List[Path]:
    if not translation_root.is_dir():
        return []

    template_files: List[Path] = []
    for path in sorted(translation_root.rglob("*.rpy")):
        try:
            rel_parts = set(path.relative_to(translation_root).parts)
        except ValueError:
            continue
        if rel_parts & WORKBENCH_ARTIFACT_DIRNAMES:
            continue
        template_files.append(path)
    return template_files


def remove_workbench_artifact_dirs(root_dir: Path) -> None:
    if not root_dir.is_dir():
        return

    candidate_dirs = sorted(
        (
            path
            for path in root_dir.rglob("*")
            if path.is_dir() and path.name in WORKBENCH_ARTIFACT_DIRNAMES
        ),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in candidate_dirs:
        shutil.rmtree(directory, ignore_errors=True)


def build_template_generation_workspace(game_dir: Path) -> Tuple[Path, Path]:
    temp_root = Path(tempfile.mkdtemp(prefix="renpy_template_workspace_"))
    temp_game_dir = temp_root / "game"
    temp_game_dir.mkdir(parents=True, exist_ok=True)

    for source_path in list_game_source_scripts(game_dir):
        destination_path = temp_game_dir / source_path.relative_to(game_dir)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)

    return temp_root, temp_game_dir


def copy_generated_templates_to_game(
    temp_game_dir: Path,
    game_dir: Path,
    target_language: str,
) -> List[Path]:
    temp_translation_dir = temp_game_dir / "tl" / target_language
    copied_paths: List[Path] = []
    if not temp_translation_dir.is_dir():
        return copied_paths

    target_translation_dir = game_dir / "tl" / target_language
    target_translation_dir.mkdir(parents=True, exist_ok=True)

    for template_path in list_translation_template_files(temp_translation_dir):
        relative_path = template_path.relative_to(temp_translation_dir)
        destination_path = target_translation_dir / relative_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_path, destination_path)
        copied_paths.append(destination_path)

    remove_workbench_artifact_dirs(target_translation_dir)
    return copied_paths


def build_expected_template_relative_paths(game_dir: Path) -> Set[str]:
    expected_paths = {
        str(path.relative_to(game_dir)).replace("\\", "/")
        for path in list_game_source_scripts(game_dir)
        if path.name not in NON_TEMPLATE_SOURCE_FILES
    }
    expected_paths.update(SYNTHETIC_TEMPLATE_FILES)
    return expected_paths


def extract_gui_baseline(game_dir: Path) -> Dict[str, Any]:
    raw_assignments: Dict[str, str] = {}
    language_hook_files = set()
    style_candidates = set()

    source_files = list_game_source_scripts(game_dir)
    all_rpy_files = sorted(game_dir.rglob("*.rpy"))

    for file_path in source_files:
        for line in read_text_file(file_path).splitlines():
            stripped = line.strip()
            match = GUI_ASSIGNMENT_RE.match(stripped)
            if match:
                raw_assignments[match.group("name")] = strip_inline_python_comment(match.group("value"))
            if any(token in stripped for token in ("Language(", "change_language(", "known_languages(")):
                language_hook_files.add(str(file_path.relative_to(game_dir)).replace("\\", "/"))

    for file_path in all_rpy_files:
        for line in read_text_file(file_path).splitlines():
            style_match = TRANSLATE_STYLE_BLOCK_RE.match(line)
            if style_match:
                style_candidates.add(style_match.group("style"))

    font_defaults = {
        key: normalize_font_reference(
            next(
                (
                    resolve_gui_assignment_value(raw_assignments, candidate)
                    for candidate in candidates
                    if resolve_gui_assignment_value(raw_assignments, candidate) is not None
                ),
                "",
            )
        )
        for key, candidates in GUI_BASELINE_FONT_KEYS.items()
    }
    size_defaults = {
        key: try_parse_int(
            next(
                (
                    resolve_gui_assignment_value(raw_assignments, candidate)
                    for candidate in candidates
                    if resolve_gui_assignment_value(raw_assignments, candidate) is not None
                ),
                None,
            )
        )
        for key, candidates in GUI_BASELINE_SIZE_KEYS.items()
    }

    font_candidates = sorted(
        str(path.relative_to(game_dir)).replace("\\", "/")
        for path in game_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in FONT_EXTENSIONS
    )[:200]
    translation_profiles = extract_translation_font_profiles(
        all_rpy_files=all_rpy_files,
        game_dir=game_dir,
        size_defaults=size_defaults,
    )
    font_presets = build_font_presets(
        gui_baseline={"font_defaults": font_defaults, "size_defaults": size_defaults},
        translation_profiles=translation_profiles,
        font_candidates=font_candidates,
    )

    base_gui_language = str(resolve_gui_assignment_value(raw_assignments, "language") or "unicode")
    return {
        "base_gui_language": base_gui_language,
        "font_defaults": font_defaults,
        "size_defaults": size_defaults,
        "font_candidates": font_candidates,
        "font_presets": font_presets,
        "translation_font_profiles": translation_profiles,
        "style_candidates": sorted(style_candidates)[:120],
        "language_hook_files": sorted(language_hook_files),
        "supports_known_languages_menu": bool(language_hook_files),
        "raw_assignments": {
            key: raw_assignments[key]
            for key in sorted(raw_assignments)
            if key in {
                "default_font",
                "text_font",
                "name_font",
                "name_text_font",
                "interface_font",
                "interface_text_font",
                "system_font",
                "glyph_font",
                "text_size",
                "name_text_size",
                "interface_text_size",
                "label_text_size",
                "notify_text_size",
                "button_text_size",
                "choice_button_text_size",
                "language",
            }
        },
    }


def decode_process_output(raw: Optional[bytes]) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw

    preferred_encoding = locale.getpreferredencoding(False) or ""
    filesystem_encoding = sys.getfilesystemencoding() or ""
    candidates: List[str] = []
    for encoding in (
        "utf-8",
        "utf-8-sig",
        preferred_encoding,
        filesystem_encoding,
        "mbcs",
        "cp949",
        "euc-kr",
        "utf-16",
        "utf-16-le",
        "latin-1",
    ):
        normalized = (encoding or "").strip().lower()
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    for encoding in candidates:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue

    return raw.decode("utf-8", errors="replace")


def normalize_display_name(name_token: str) -> Optional[str]:
    if name_token == "None":
        return None
    if name_token.startswith('_("') and name_token.endswith('")'):
        return name_token[3:-2]
    if name_token.startswith('"') and name_token.endswith('"'):
        return name_token[1:-1]
    return name_token


def build_item_id(relative_path: str, line_number: int, kind: str, index: int) -> str:
    raw = f"{relative_path}|{line_number}|{kind}|{index}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"{kind}_{digest}"


def summarize_text(text: str, limit: int = 140) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3]}..."


def split_first_quoted_string(line: str) -> Optional[Dict[str, str]]:
    match = QUOTED_STRING_RE.match(line)
    if not match:
        return None
    return match.groupdict()


def escape_renpy_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\t", "\\t")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
    )


def unescape_renpy_text(text: str) -> str:
    if not text or "\\" not in text:
        return text

    buffer: List[str] = []
    pointer = 0
    while pointer < len(text):
        current = text[pointer]
        if current != "\\" or pointer + 1 >= len(text):
            buffer.append(current)
            pointer += 1
            continue

        next_char = text[pointer + 1]
        if next_char == "n":
            buffer.append("\n")
        elif next_char == "t":
            buffer.append("\t")
        elif next_char == "r":
            buffer.append("\r")
        elif next_char in ('"', "\\"):
            buffer.append(next_char)
        else:
            buffer.append(next_char)
        pointer += 2

    return "".join(buffer)


def decode_renpy_text_literal(text: str, max_depth: int = 2) -> str:
    decoded = text or ""
    for _ in range(max(1, max_depth)):
        next_decoded = unescape_renpy_text(decoded)
        if next_decoded == decoded:
            break
        decoded = next_decoded
    return decoded


def normalize_renpy_string_literal_text(text: str) -> str:
    return escape_renpy_text(decode_renpy_text_literal(text))


def restore_token_sequence(source_text: str, translated_text: str, token_pattern: re.Pattern[str]) -> str:
    source_matches = list(token_pattern.finditer(source_text or ""))
    translated_matches = list(token_pattern.finditer(translated_text or ""))
    if not source_matches or not translated_matches:
        return translated_text

    source_tokens = [match.group(0) for match in source_matches]
    translated_tokens = [match.group(0) for match in translated_matches]
    if source_tokens == translated_tokens:
        return translated_text

    rebuilt_parts: List[str] = []
    cursor = 0
    for index, match in enumerate(translated_matches):
        rebuilt_parts.append(translated_text[cursor:match.start()])
        if index < len(source_tokens):
            rebuilt_parts.append(source_tokens[index])
        else:
            rebuilt_parts.append(match.group(0))
        cursor = match.end()
    rebuilt_parts.append(translated_text[cursor:])
    return "".join(rebuilt_parts)


def restore_renpy_substitutions(source_text: str, translated_text: str) -> str:
    return restore_token_sequence(source_text, translated_text, RENPY_SUBSTITUTION_RE)


def restore_renpy_text_tags(source_text: str, translated_text: str) -> str:
    return restore_token_sequence(source_text, translated_text, RENPY_TEXT_TAG_RE)


def restore_python_format_tokens(source_text: str, translated_text: str) -> str:
    return restore_token_sequence(source_text, translated_text, PYTHON_FORMAT_TOKEN_RE)


def is_token_scaffold_text(text: str) -> bool:
    decoded = decode_renpy_text_literal(text or "")
    cleaned = decoded
    for token_pattern in (RENPY_SUBSTITUTION_RE, RENPY_TEXT_TAG_RE, PYTHON_FORMAT_TOKEN_RE):
        cleaned = token_pattern.sub("", cleaned)
    cleaned = re.sub(r"\s+", "", cleaned)
    cleaned = re.sub(r"[\"'“”‘’`~!@#$^&*()\-_=+|\\/:;,.?<>]+", "", cleaned)
    return not cleaned


def normalize_translated_text_for_item(source_text: str, translated_text: str, block_id: Optional[str] = None) -> str:
    if is_token_scaffold_text(source_text):
        normalized = decode_renpy_text_literal(source_text)
    else:
        normalized = decode_renpy_text_literal(translated_text)
        normalized = restore_renpy_substitutions(source_text, normalized)
        normalized = restore_renpy_text_tags(source_text, normalized)
        normalized = restore_python_format_tokens(source_text, normalized)
    if block_id == "strings":
        return normalize_renpy_string_literal_text(normalized)
    return escape_renpy_text(normalized)


def detect_adult_content(text: str) -> Dict[str, Any]:
    lowered = text.lower()
    hits = sorted({keyword for keyword in ADULT_KEYWORDS if keyword in lowered})
    return {"adult": bool(hits), "keywords": hits}


def normalize_identifier_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def is_markup_only_text(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    cleaned = re.sub(r"\{[^{}]+\}", "", stripped)
    cleaned = cleaned.replace("\\n", "").replace("\n", "").strip()
    cleaned = re.sub(r"['\".,:;!?…·\-–—()\[\]/\\]+", "", cleaned).strip()
    return not cleaned


def is_low_signal_sample(text: str) -> bool:
    stripped = re.sub(r"\s+", " ", (text or "").strip())
    if not stripped:
        return True

    lowered = stripped.lower()
    if lowered in {"test", "language"}:
        return True
    if re.fullmatch(r"old:\d+(?:\.\d+)?(?:_\d+)?", lowered):
        return True
    if re.fullmatch(r"[\w./-]+\.(txt|otf|ttf|png|jpg|jpeg|mp3|ogg|wav|rpy|rpyc)", lowered):
        return True
    return False


def resolve_character_alias(
    speaker_id: str,
    character_registry: Dict[str, Dict[str, Any]],
) -> Optional[str]:
    candidate = normalize_identifier_token(speaker_id)
    if not candidate:
        return None

    for prefix in NON_CHARACTER_PREFIXES:
        if candidate.startswith(prefix):
            candidate = candidate[len(prefix) :]
            break

    for suffix in ("text", "mobile", "effect", "label", "screen", "button", "caption", "title", "name"):
        if candidate.endswith(suffix):
            candidate = candidate[: -len(suffix)]
            break

    candidate = re.sub(r"\d+$", "", candidate)
    if not candidate:
        return None

    matches: List[str] = []
    for key, value in character_registry.items():
        if key in {DEFAULT_FALLBACK_PERSONA_KEY, NARRATION_PERSONA_KEY}:
            continue
        key_token = normalize_identifier_token(key)
        display_token = normalize_identifier_token(value.get("display_name") or "")
        if candidate in {key_token, display_token}:
            matches.append(key)

    return matches[0] if len(matches) == 1 else None


def looks_like_non_character_speaker(
    speaker_id: str,
    character_registry: Dict[str, Dict[str, Any]],
) -> bool:
    if not speaker_id:
        return False

    lowered = speaker_id.lower()
    if lowered in NON_CHARACTER_TOKENS:
        return True
    if lowered.startswith(NON_CHARACTER_PREFIXES):
        return True
    if any(lowered.endswith(suffix) for suffix in NON_CHARACTER_SUFFIXES):
        return True
    return False


def classify_speaker_reference(
    speaker_id: Optional[str],
    source_text: str,
    character_registry: Dict[str, Dict[str, Any]],
    previous_item: Optional["TranslationItem"] = None,
) -> Dict[str, Optional[str]]:
    if not speaker_id:
        return {"kind": "narration", "speaker_id": None}

    lowered = speaker_id.lower()
    if lowered == "extend":
        if previous_item and previous_item.kind in {"dialogue", "narration"}:
            return {"kind": previous_item.kind, "speaker_id": previous_item.speaker_id}
        return {"kind": "narration", "speaker_id": None}

    if speaker_id not in character_registry:
        alias_key = resolve_character_alias(speaker_id, character_registry)
        if alias_key:
            return {"kind": "narration", "speaker_id": alias_key}

    if looks_like_non_character_speaker(speaker_id, character_registry) or is_markup_only_text(source_text):
        return {"kind": "string", "speaker_id": DEFAULT_FALLBACK_PERSONA_KEY}

    if speaker_id in character_registry:
        return {"kind": "dialogue", "speaker_id": speaker_id}

    return {"kind": "dialogue", "speaker_id": speaker_id}


def resolve_item_speaker_name(
    kind: str,
    speaker_id: Optional[str],
    character_registry: Dict[str, Dict[str, Any]],
) -> Optional[str]:
    if kind in {"string", "menu"}:
        lookup_key = DEFAULT_FALLBACK_PERSONA_KEY
    elif speaker_id:
        lookup_key = speaker_id
    else:
        lookup_key = NARRATION_PERSONA_KEY
    return character_registry.get(lookup_key, {}).get("display_name")


def collect_character_definitions(script_paths: List[Path]) -> Dict[str, Dict[str, Any]]:
    registry: Dict[str, Dict[str, Any]] = {}
    for script_path in script_paths:
        content = read_text_file(script_path)
        relative_path = script_path.name
        for line_number, line in enumerate(content.splitlines(), start=1):
            match = CHARACTER_DEFINE_RE.match(line)
            if not match:
                continue
            speaker_id = match.group("speaker")
            display_name = normalize_display_name(match.group("name"))
            entry = registry.setdefault(
                speaker_id,
                {
                    "speaker_id": speaker_id,
                    "display_name": display_name,
                    "defined_in": relative_path,
                },
            )
            if display_name and not entry.get("display_name"):
                entry["display_name"] = display_name
    registry.setdefault(
        NARRATION_PERSONA_KEY,
        {
            "speaker_id": NARRATION_PERSONA_KEY,
            "display_name": "Narration",
            "defined_in": "generated",
        },
    )
    registry.setdefault(
        DEFAULT_FALLBACK_PERSONA_KEY,
        {
            "speaker_id": DEFAULT_FALLBACK_PERSONA_KEY,
            "display_name": "Default",
            "defined_in": "generated",
        },
    )
    return registry


def normalize_portrait_key(raw_value: Optional[str]) -> str:
    if not raw_value:
        return ""

    cleaned = re.sub(r"[^a-z0-9]+", "", str(raw_value).lower())
    suffixes = ("portrait", "thumb", "human", "sprite", "default", "neutral", "calm", "idle")
    trimmed = True
    while trimmed and cleaned:
        trimmed = False
        for suffix in suffixes:
            if cleaned.endswith(suffix) and len(cleaned) > len(suffix) + 1:
                cleaned = cleaned[: -len(suffix)]
                trimmed = True
                break
    return cleaned


def build_portrait_aliases(character_entry: Dict[str, Any]) -> List[str]:
    aliases: List[str] = []
    seen = set()

    for raw_value in (character_entry.get("speaker_id"), character_entry.get("display_name")):
        if not raw_value:
            continue

        normalized = normalize_portrait_key(raw_value)
        if normalized and normalized not in seen:
            aliases.append(normalized)
            seen.add(normalized)

        for token in re.split(r"[\s/_-]+", str(raw_value)):
            token_normalized = normalize_portrait_key(token)
            if token_normalized and token_normalized not in seen:
                aliases.append(token_normalized)
                seen.add(token_normalized)

    return aliases


def resolve_asset_path(game_dir: Path, relative_asset_path: str) -> Optional[Path]:
    cleaned = relative_asset_path.replace("\\", "/").strip().lstrip("./")
    if not cleaned:
        return None

    game_root = game_dir.resolve()
    candidate_paths = [game_dir / cleaned]
    if not cleaned.startswith("images/"):
        candidate_paths.append(game_dir / "images" / cleaned)

    for candidate in candidate_paths:
        resolved = candidate.resolve()
        try:
            resolved.relative_to(game_root)
        except ValueError:
            continue
        if resolved.is_file():
            return resolved
    return None


def portrait_score(candidate: Dict[str, Any], aliases: List[str]) -> int:
    candidate_keys = candidate.get("keys") or []
    best_alias_score = 0

    for alias in aliases:
        if not alias:
            continue
        for candidate_key in candidate_keys:
            if not candidate_key:
                continue
            if alias == candidate_key:
                best_alias_score = max(best_alias_score, 140 if len(alias) > 1 else 120)
            elif len(alias) >= 3 and candidate_key.startswith(alias):
                best_alias_score = max(best_alias_score, 112)
            elif len(alias) >= 3 and alias.startswith(candidate_key) and len(candidate_key) >= 3:
                best_alias_score = max(best_alias_score, 102)
            elif len(alias) >= 3 and alias in candidate_key:
                best_alias_score = max(best_alias_score, 92)
            elif len(candidate_key) >= 3 and candidate_key in alias:
                best_alias_score = max(best_alias_score, 86)

    return int(candidate.get("base_score") or 0) + best_alias_score


def extract_portrait_candidate_from_block(
    game_dir: Path,
    block_text: str,
    *,
    source_type: str,
    image_name: Optional[str] = None,
    portrait_label: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    file_match = IMAGE_FILE_RE.search(block_text)
    if not file_match:
        return None

    asset_path = resolve_asset_path(game_dir, file_match.group("path"))
    if not asset_path:
        return None

    crop_match = CROP_RE.search(block_text)
    crop = None
    if crop_match:
        crop = [
            int(crop_match.group("x")),
            int(crop_match.group("y")),
            int(crop_match.group("w")),
            int(crop_match.group("h")),
        ]

    key_parts = {
        normalize_portrait_key(portrait_label),
        normalize_portrait_key(image_name),
        normalize_portrait_key(asset_path.stem),
        normalize_portrait_key(asset_path.parent.name),
        normalize_portrait_key(asset_path.parent.parent.name if asset_path.parent.parent != asset_path.parent else ""),
    }
    key_parts = {part for part in key_parts if part}

    path_lower = asset_path.as_posix().lower()
    base_score = 36
    if source_type == "biothumb":
        base_score += 60
    if crop:
        base_score += 22
    if any(token in path_lower for token in ("calm", "neutral", "default", "idle")):
        base_score += 18
    if any(token in path_lower for token in ("happy", "smile", "soft")):
        base_score += 8
    if any(token in path_lower for token in ("angry", "sad", "cry", "shout", "mad", "scared", "hurt", "pain")):
        base_score -= 8
    if any(token in path_lower for token in ("nude", "naked", "sex", "cum", "orgasm", "fuck", "bed")):
        base_score -= 70

    return {
        "asset_path": str(asset_path),
        "asset_relative_path": str(asset_path.relative_to(game_dir)).replace("\\", "/"),
        "crop": crop,
        "source_type": source_type,
        "keys": sorted(key_parts),
        "base_score": base_score,
    }


def collect_character_portraits(
    game_dir: Path,
    script_paths: List[Path],
    character_registry: Dict[str, Dict[str, Any]],
) -> None:
    candidates: List[Dict[str, Any]] = []

    for script_path in script_paths:
        content = read_text_file(script_path)
        lines = content.splitlines()
        index = 0
        while index < len(lines):
            line = lines[index]
            biothumb_match = BIOTHUMB_HEADER_RE.match(line)
            if biothumb_match:
                block_lines = [line]
                index += 1
                while index < len(lines):
                    next_line = lines[index]
                    if next_line.strip() and not next_line[:1].isspace():
                        break
                    block_lines.append(next_line)
                    index += 1
                candidate = extract_portrait_candidate_from_block(
                    game_dir,
                    "\n".join(block_lines),
                    source_type="biothumb",
                    portrait_label=biothumb_match.group("name"),
                )
                if candidate:
                    candidates.append(candidate)
                continue

            assignment_match = IMAGE_ASSIGNMENT_RE.match(line)
            if assignment_match:
                candidate = extract_portrait_candidate_from_block(
                    game_dir,
                    assignment_match.group("expr"),
                    source_type="image",
                    image_name=assignment_match.group("image_name"),
                    portrait_label=assignment_match.group("image_name"),
                )
                if candidate:
                    candidates.append(candidate)
            index += 1

    deduplicated: Dict[Any, Dict[str, Any]] = {}
    for candidate in candidates:
        signature = (
            candidate.get("asset_path"),
            tuple(candidate.get("crop") or []),
            candidate.get("source_type"),
            tuple(candidate.get("keys") or []),
        )
        existing = deduplicated.get(signature)
        if not existing or int(candidate.get("base_score") or 0) > int(existing.get("base_score") or 0):
            deduplicated[signature] = candidate

    unique_candidates = list(deduplicated.values())
    for speaker_id, character_entry in character_registry.items():
        if speaker_id in {NARRATION_PERSONA_KEY, DEFAULT_FALLBACK_PERSONA_KEY}:
            continue

        aliases = build_portrait_aliases(character_entry)
        if not aliases:
            continue

        best_candidate = None
        best_score = 0
        for candidate in unique_candidates:
            score = portrait_score(candidate, aliases)
            if score > best_score:
                best_candidate = candidate
                best_score = score

        if best_candidate and best_score >= 120:
            character_entry["portrait"] = {
                "asset_path": best_candidate["asset_path"],
                "asset_relative_path": best_candidate["asset_relative_path"],
                "crop": best_candidate.get("crop"),
                "source_type": best_candidate.get("source_type"),
            }


def choose_scan_mode(game_dir: Path, target_language: str) -> Dict[str, Any]:
    # 순환 번역 방지: _ai 또는 _workbench 언어는 소스로 사용할 수 없음
    if target_language.endswith(("_ai", "_workbench")):
        return {
            "mode": "source_files",
            "files": list_game_source_scripts(game_dir),
            "language": target_language,
        }

    translation_dir = game_dir / "tl" / target_language
    if translation_dir.is_dir():
        # tl 폴더 내부에서도 _translator_output 등 잘못 생성된 하위 폴더 제외
        all_candidates = sorted(translation_dir.rglob("*.rpy"))
        filtered_files = []
        for path in all_candidates:
            try:
                # game/tl/ko/ 하위 경로에서 금지된 키워드 확인
                rel_parts = set(path.relative_to(translation_dir).parts)
                if not (rel_parts & WORKBENCH_ARTIFACT_DIRNAMES):
                    filtered_files.append(path)
            except ValueError:
                continue

        if filtered_files:
            return {
                "mode": "translation_layer",
                "files": filtered_files,
                "language": target_language,
            }

    source_files = list_game_source_scripts(game_dir)
    return {
        "mode": "source_files",
        "files": source_files,
        "language": target_language,
    }


def parse_crop_query(crop_value: str) -> Optional[List[int]]:
    if not crop_value:
        return None

    parts = [part.strip() for part in crop_value.split(",")]
    if len(parts) != 4:
        return None

    try:
        return [int(part) for part in parts]
    except ValueError:
        return None


def build_thumbnail_image(image: Image.Image, crop: Optional[List[int]], size: int) -> Image.Image:
    width, height = image.size

    if crop and len(crop) == 4:
        crop_x, crop_y, crop_w, crop_h = crop
        left = max(0, min(width - 1, crop_x))
        top = max(0, min(height - 1, crop_y))
        right = max(left + 1, min(width, crop_x + crop_w))
        bottom = max(top + 1, min(height, crop_y + crop_h))
        image = image.crop((left, top, right, bottom))
    elif height > width:
        square = min(width, height)
        top = max(0, min((height - square) // 5, height - square))
        image = image.crop((0, top, square, top + square))
    elif width > height:
        square = min(width, height)
        left = max(0, (width - square) // 2)
        image = image.crop((left, 0, left + square, square))

    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    return image.resize((size, size), resampling)


def parse_comment_source_line(
    line: str,
    character_registry: Dict[str, Dict[str, Any]],
    previous_item: Optional["TranslationItem"] = None,
) -> Dict[str, Any]:
    stripped = re.sub(r"^\s*#\s*", "", line).strip()
    speaker_match = SPEAKER_LINE_RE.match(stripped)
    if speaker_match:
        classification = classify_speaker_reference(
            speaker_id=speaker_match.group("speaker"),
            source_text=speaker_match.group("text"),
            character_registry=character_registry,
            previous_item=previous_item,
        )
        return {
            "kind": classification["kind"],
            "speaker_id": classification["speaker_id"],
            "source_text": speaker_match.group("text"),
        }
    narration_match = NARRATION_LINE_RE.match(stripped)
    if narration_match:
        return {
            "kind": "narration",
            "speaker_id": None,
            "source_text": narration_match.group("text"),
        }
    return {"kind": None, "speaker_id": None, "source_text": ""}


def assign_item_context(items: List[TranslationItem]) -> None:
    for index, item in enumerate(items):
        before_items = items[max(0, index - CONTEXT_WINDOW_SIZE) : index]
        after_items = items[index + 1 : index + 1 + CONTEXT_WINDOW_SIZE]
        item.context_before = [context_item.source_preview for context_item in before_items]
        item.context_after = [context_item.source_preview for context_item in after_items]


def parse_translation_file(
    absolute_path: Path,
    relative_path: str,
    output_relative_path: str,
    character_registry: Dict[str, Dict[str, Any]],
) -> AnalyzedFile:
    raw_content = read_text_file(absolute_path)
    lines = raw_content.splitlines()
    items: List[TranslationItem] = []
    item_index = 0
    pointer = 0

    while pointer < len(lines):
        header_match = TRANSLATE_HEADER_RE.match(lines[pointer])
        if not header_match:
            pointer += 1
            continue

        block_label = header_match.group("label")
        block_start = pointer
        pointer += 1

        while pointer < len(lines) and not TRANSLATE_HEADER_RE.match(lines[pointer]):
            pointer += 1

        block_lines = lines[block_start:pointer]
        if block_label == "strings":
            old_text = None
            for offset, line in enumerate(block_lines, start=0):
                old_match = STRING_OLD_RE.match(line)
                if old_match:
                    old_text = decode_renpy_text_literal(old_match.group("text"))
                    continue
                new_match = STRING_NEW_RE.match(line)
                if new_match and old_text is not None:
                    line_index = block_start + offset
                    pieces = split_first_quoted_string(line)
                    if not pieces:
                        continue
                    adult_info = detect_adult_content(old_text)
                    item = TranslationItem(
                        item_id=build_item_id(relative_path, line_index + 1, "string", item_index),
                        file_relative_path=relative_path,
                        file_mode="translation_layer",
                        block_id="strings",
                        kind="string",
                        speaker_id=DEFAULT_FALLBACK_PERSONA_KEY,
                        speaker_name=character_registry.get(DEFAULT_FALLBACK_PERSONA_KEY, {}).get("display_name"),
                        line_number=line_index + 1,
                        target_line_index=line_index,
                        source_text=old_text,
                        current_text=new_match.group("text"),
                        before=pieces["before"],
                        after=pieces["after"],
                        adult=adult_info["adult"],
                        adult_keywords=adult_info["keywords"],
                        source_preview=summarize_text(old_text),
                    )
                    items.append(item)
                    item_index += 1
                    old_text = None
            continue

        comment_source = None
        target_line_index = None
        target_line = None
        for offset, line in enumerate(block_lines):
            if line.strip().startswith("#") and comment_source is None:
                parsed = parse_comment_source_line(
                    line=line,
                    character_registry=character_registry,
                    previous_item=items[-1] if items else None,
                )
                if parsed["kind"]:
                    comment_source = parsed
            elif line.strip() and not line.strip().startswith("#") and '"' in line:
                target_line_index = block_start + offset
                target_line = line
                break

        if not comment_source or target_line_index is None or not target_line:
            continue

        pieces = split_first_quoted_string(target_line)
        if not pieces:
            continue

        speaker_id = comment_source["speaker_id"]
        adult_info = detect_adult_content(comment_source["source_text"])
        item = TranslationItem(
            item_id=build_item_id(relative_path, target_line_index + 1, comment_source["kind"], item_index),
            file_relative_path=relative_path,
            file_mode="translation_layer",
            block_id=block_label,
            kind=comment_source["kind"],
            speaker_id=speaker_id,
            speaker_name=resolve_item_speaker_name(comment_source["kind"], speaker_id, character_registry),
            line_number=target_line_index + 1,
            target_line_index=target_line_index,
            source_text=comment_source["source_text"],
            current_text=pieces["text"],
            before=pieces["before"],
            after=pieces["after"],
            adult=adult_info["adult"],
            adult_keywords=adult_info["keywords"],
            source_preview=summarize_text(comment_source["source_text"]),
        )
        items.append(item)
        item_index += 1

    assign_item_context(items)
    return AnalyzedFile(
        absolute_path=str(absolute_path),
        file_relative_path=relative_path,
        output_relative_path=output_relative_path,
        file_name=Path(relative_path).name,
        file_mode="translation_layer",
        raw_content=raw_content,
        items=items,
    )


def parse_source_file(
    absolute_path: Path,
    relative_path: str,
    output_relative_path: str,
    character_registry: Dict[str, Dict[str, Any]],
) -> AnalyzedFile:
    raw_content = read_text_file(absolute_path)
    lines = raw_content.splitlines()
    items: List[TranslationItem] = []
    item_index = 0
    pending_old_text: Optional[str] = None

    for line_index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        old_match = STRING_OLD_RE.match(line)
        if old_match:
            pending_old_text = decode_renpy_text_literal(old_match.group("text"))
            continue

        new_match = STRING_NEW_RE.match(line)
        if new_match and pending_old_text is not None:
            pieces = split_first_quoted_string(line)
            if pieces:
                adult_info = detect_adult_content(pending_old_text)
                items.append(
                    TranslationItem(
                        item_id=build_item_id(relative_path, line_index + 1, "string", item_index),
                        file_relative_path=relative_path,
                        file_mode="source_files",
                        block_id=None,
                        kind="string",
                        speaker_id=DEFAULT_FALLBACK_PERSONA_KEY,
                        speaker_name=character_registry.get(DEFAULT_FALLBACK_PERSONA_KEY, {}).get("display_name"),
                        line_number=line_index + 1,
                        target_line_index=line_index,
                        source_text=pending_old_text,
                        current_text=decode_renpy_text_literal(new_match.group("text")),
                        before=pieces["before"],
                        after=pieces["after"],
                        adult=adult_info["adult"],
                        adult_keywords=adult_info["keywords"],
                        source_preview=summarize_text(pending_old_text),
                    )
                )
                item_index += 1
            pending_old_text = None
            continue

        speaker_match = SPEAKER_LINE_RE.match(stripped)
        if speaker_match:
            speaker_id = speaker_match.group("speaker")
            pieces = split_first_quoted_string(line)
            if not pieces:
                continue
            source_text = speaker_match.group("text")
            classification = classify_speaker_reference(
                speaker_id=speaker_id,
                source_text=source_text,
                character_registry=character_registry,
                previous_item=items[-1] if items else None,
            )
            adult_info = detect_adult_content(source_text)
            items.append(
                TranslationItem(
                    item_id=build_item_id(relative_path, line_index + 1, classification["kind"], item_index),
                    file_relative_path=relative_path,
                    file_mode="source_files",
                    block_id=None,
                    kind=classification["kind"],
                    speaker_id=classification["speaker_id"],
                    speaker_name=resolve_item_speaker_name(
                        classification["kind"],
                        classification["speaker_id"],
                        character_registry,
                    ),
                    line_number=line_index + 1,
                    target_line_index=line_index,
                    source_text=source_text,
                    current_text=speaker_match.group("text"),
                    before=pieces["before"],
                    after=pieces["after"],
                    adult=adult_info["adult"],
                    adult_keywords=adult_info["keywords"],
                    source_preview=summarize_text(source_text),
                )
            )
            item_index += 1
            continue

        narration_match = NARRATION_LINE_RE.match(stripped)
        if narration_match:
            previous_non_empty = ""
            for back_index in range(line_index - 1, -1, -1):
                previous_non_empty = lines[back_index].strip()
                if previous_non_empty:
                    break
            if previous_non_empty.startswith("menu:"):
                continue
            pieces = split_first_quoted_string(line)
            if not pieces:
                continue
            source_text = narration_match.group("text")
            adult_info = detect_adult_content(source_text)
            items.append(
                TranslationItem(
                    item_id=build_item_id(relative_path, line_index + 1, "narration", item_index),
                    file_relative_path=relative_path,
                    file_mode="source_files",
                    block_id=None,
                    kind="narration",
                    speaker_id=None,
                    speaker_name=character_registry.get(NARRATION_PERSONA_KEY, {}).get("display_name"),
                    line_number=line_index + 1,
                    target_line_index=line_index,
                    source_text=source_text,
                    current_text=narration_match.group("text"),
                    before=pieces["before"],
                    after=pieces["after"],
                    adult=adult_info["adult"],
                    adult_keywords=adult_info["keywords"],
                    source_preview=summarize_text(source_text),
                )
            )
            item_index += 1
            continue

        menu_match = MENU_LINE_RE.match(stripped)
        if menu_match:
            pieces = split_first_quoted_string(line)
            if not pieces:
                continue
            source_text = menu_match.group("text")
            adult_info = detect_adult_content(source_text)
            items.append(
                TranslationItem(
                    item_id=build_item_id(relative_path, line_index + 1, "menu", item_index),
                    file_relative_path=relative_path,
                    file_mode="source_files",
                    block_id=None,
                    kind="menu",
                    speaker_id=DEFAULT_FALLBACK_PERSONA_KEY,
                    speaker_name=character_registry.get(DEFAULT_FALLBACK_PERSONA_KEY, {}).get("display_name"),
                    line_number=line_index + 1,
                    target_line_index=line_index,
                    source_text=source_text,
                    current_text=menu_match.group("text"),
                    before=pieces["before"],
                    after=pieces["after"],
                    adult=adult_info["adult"],
                    adult_keywords=adult_info["keywords"],
                    source_preview=summarize_text(source_text),
                )
            )
            item_index += 1

    assign_item_context(items)
    return AnalyzedFile(
        absolute_path=str(absolute_path),
        file_relative_path=relative_path,
        output_relative_path=output_relative_path,
        file_name=Path(relative_path).name,
        file_mode="source_files",
        raw_content=raw_content,
        items=items,
    )


def parse_translation_file_from_content(
    file_name: str,
    relative_path: str,
    output_relative_path: str,
    raw_content: str,
    character_registry: Dict[str, Dict[str, Any]],
) -> AnalyzedFile:
    lines = raw_content.splitlines()
    items: List[TranslationItem] = []
    item_index = 0
    pointer = 0

    while pointer < len(lines):
        header_match = TRANSLATE_HEADER_RE.match(lines[pointer])
        if not header_match:
            pointer += 1
            continue

        block_label = header_match.group("label")
        block_start = pointer
        pointer += 1
        while pointer < len(lines) and not TRANSLATE_HEADER_RE.match(lines[pointer]):
            pointer += 1

        block_lines = lines[block_start:pointer]
        if block_label == "strings":
            old_text = None
            for offset, line in enumerate(block_lines, start=0):
                old_match = STRING_OLD_RE.match(line)
                if old_match:
                    old_text = decode_renpy_text_literal(old_match.group("text"))
                    continue
                new_match = STRING_NEW_RE.match(line)
                if new_match and old_text is not None:
                    line_index = block_start + offset
                    pieces = split_first_quoted_string(line)
                    if not pieces:
                        continue
                    adult_info = detect_adult_content(old_text)
                    items.append(
                        TranslationItem(
                            item_id=build_item_id(relative_path, line_index + 1, "string", item_index),
                            file_relative_path=relative_path,
                            file_mode="uploaded_files",
                            block_id="strings",
                            kind="string",
                            speaker_id=DEFAULT_FALLBACK_PERSONA_KEY,
                            speaker_name=character_registry.get(DEFAULT_FALLBACK_PERSONA_KEY, {}).get("display_name"),
                            line_number=line_index + 1,
                            target_line_index=line_index,
                            source_text=old_text,
                            current_text=decode_renpy_text_literal(new_match.group("text")),
                            before=pieces["before"],
                            after=pieces["after"],
                            adult=adult_info["adult"],
                            adult_keywords=adult_info["keywords"],
                            source_preview=summarize_text(old_text),
                        )
                    )
                    item_index += 1
                    old_text = None
            continue

        comment_source = None
        target_line_index = None
        target_line = None
        for offset, line in enumerate(block_lines):
            if line.strip().startswith("#") and comment_source is None:
                parsed = parse_comment_source_line(
                    line=line,
                    character_registry=character_registry,
                    previous_item=items[-1] if items else None,
                )
                if parsed["kind"]:
                    comment_source = parsed
            elif line.strip() and not line.strip().startswith("#") and '"' in line:
                target_line_index = block_start + offset
                target_line = line
                break

        if not comment_source or target_line_index is None or not target_line:
            continue

        pieces = split_first_quoted_string(target_line)
        if not pieces:
            continue
        adult_info = detect_adult_content(comment_source["source_text"])
        speaker_id = comment_source["speaker_id"]
        items.append(
            TranslationItem(
                item_id=build_item_id(relative_path, target_line_index + 1, comment_source["kind"], item_index),
                file_relative_path=relative_path,
                file_mode="uploaded_files",
                block_id=block_label,
                kind=comment_source["kind"],
                speaker_id=speaker_id,
                speaker_name=resolve_item_speaker_name(comment_source["kind"], speaker_id, character_registry),
                line_number=target_line_index + 1,
                target_line_index=target_line_index,
                source_text=comment_source["source_text"],
                current_text=pieces["text"],
                before=pieces["before"],
                after=pieces["after"],
                adult=adult_info["adult"],
                adult_keywords=adult_info["keywords"],
                source_preview=summarize_text(comment_source["source_text"]),
            )
        )
        item_index += 1

    assign_item_context(items)
    return AnalyzedFile(
        absolute_path=None,
        file_relative_path=relative_path,
        output_relative_path=output_relative_path,
        file_name=file_name,
        file_mode="uploaded_files",
        raw_content=raw_content,
        items=items,
    )


def parse_source_file_from_content(
    file_name: str,
    relative_path: str,
    output_relative_path: str,
    raw_content: str,
    character_registry: Dict[str, Dict[str, Any]],
) -> AnalyzedFile:
    lines = raw_content.splitlines()
    items: List[TranslationItem] = []
    item_index = 0
    pending_old_text: Optional[str] = None

    for line_index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        old_match = STRING_OLD_RE.match(line)
        if old_match:
            pending_old_text = unescape_renpy_text(old_match.group("text"))
            continue

        new_match = STRING_NEW_RE.match(line)
        if new_match and pending_old_text is not None:
            pieces = split_first_quoted_string(line)
            if pieces:
                adult_info = detect_adult_content(pending_old_text)
                items.append(
                    TranslationItem(
                        item_id=build_item_id(relative_path, line_index + 1, "string", item_index),
                        file_relative_path=relative_path,
                        file_mode="uploaded_files",
                        block_id=None,
                        kind="string",
                        speaker_id=DEFAULT_FALLBACK_PERSONA_KEY,
                        speaker_name=character_registry.get(DEFAULT_FALLBACK_PERSONA_KEY, {}).get("display_name"),
                        line_number=line_index + 1,
                        target_line_index=line_index,
                        source_text=pending_old_text,
                            current_text=decode_renpy_text_literal(new_match.group("text")),
                        before=pieces["before"],
                        after=pieces["after"],
                        adult=adult_info["adult"],
                        adult_keywords=adult_info["keywords"],
                        source_preview=summarize_text(pending_old_text),
                    )
                )
                item_index += 1
            pending_old_text = None
            continue

        speaker_match = SPEAKER_LINE_RE.match(stripped)
        if speaker_match:
            speaker_id = speaker_match.group("speaker")
            pieces = split_first_quoted_string(line)
            if not pieces:
                continue
            source_text = speaker_match.group("text")
            classification = classify_speaker_reference(
                speaker_id=speaker_id,
                source_text=source_text,
                character_registry=character_registry,
                previous_item=items[-1] if items else None,
            )
            adult_info = detect_adult_content(source_text)
            items.append(
                TranslationItem(
                    item_id=build_item_id(relative_path, line_index + 1, classification["kind"], item_index),
                    file_relative_path=relative_path,
                    file_mode="uploaded_files",
                    block_id=None,
                    kind=classification["kind"],
                    speaker_id=classification["speaker_id"],
                    speaker_name=resolve_item_speaker_name(
                        classification["kind"],
                        classification["speaker_id"],
                        character_registry,
                    ),
                    line_number=line_index + 1,
                    target_line_index=line_index,
                    source_text=source_text,
                    current_text=speaker_match.group("text"),
                    before=pieces["before"],
                    after=pieces["after"],
                    adult=adult_info["adult"],
                    adult_keywords=adult_info["keywords"],
                    source_preview=summarize_text(source_text),
                )
            )
            item_index += 1
            continue

        narration_match = NARRATION_LINE_RE.match(stripped)
        if narration_match:
            previous_non_empty = ""
            for back_index in range(line_index - 1, -1, -1):
                previous_non_empty = lines[back_index].strip()
                if previous_non_empty:
                    break
            if previous_non_empty.startswith("menu:"):
                continue
            pieces = split_first_quoted_string(line)
            if not pieces:
                continue
            source_text = narration_match.group("text")
            adult_info = detect_adult_content(source_text)
            items.append(
                TranslationItem(
                    item_id=build_item_id(relative_path, line_index + 1, "narration", item_index),
                    file_relative_path=relative_path,
                    file_mode="uploaded_files",
                    block_id=None,
                    kind="narration",
                    speaker_id=None,
                    speaker_name=character_registry.get(NARRATION_PERSONA_KEY, {}).get("display_name"),
                    line_number=line_index + 1,
                    target_line_index=line_index,
                    source_text=source_text,
                    current_text=narration_match.group("text"),
                    before=pieces["before"],
                    after=pieces["after"],
                    adult=adult_info["adult"],
                    adult_keywords=adult_info["keywords"],
                    source_preview=summarize_text(source_text),
                )
            )
            item_index += 1
            continue

        menu_match = MENU_LINE_RE.match(stripped)
        if menu_match:
            pieces = split_first_quoted_string(line)
            if not pieces:
                continue
            source_text = menu_match.group("text")
            adult_info = detect_adult_content(source_text)
            items.append(
                TranslationItem(
                    item_id=build_item_id(relative_path, line_index + 1, "menu", item_index),
                    file_relative_path=relative_path,
                    file_mode="uploaded_files",
                    block_id=None,
                    kind="menu",
                    speaker_id=DEFAULT_FALLBACK_PERSONA_KEY,
                    speaker_name=character_registry.get(DEFAULT_FALLBACK_PERSONA_KEY, {}).get("display_name"),
                    line_number=line_index + 1,
                    target_line_index=line_index,
                    source_text=source_text,
                    current_text=menu_match.group("text"),
                    before=pieces["before"],
                    after=pieces["after"],
                    adult=adult_info["adult"],
                    adult_keywords=adult_info["keywords"],
                    source_preview=summarize_text(source_text),
                )
            )
            item_index += 1

    assign_item_context(items)
    return AnalyzedFile(
        absolute_path=None,
        file_relative_path=relative_path,
        output_relative_path=output_relative_path,
        file_name=file_name,
        file_mode="uploaded_files",
        raw_content=raw_content,
        items=items,
    )


def parse_uploaded_file(
    file_name: str,
    file_content: str,
    original_rpy_path: Optional[str],
    character_registry: Dict[str, Dict[str, Any]],
) -> AnalyzedFile:
    relative_path = original_rpy_path or file_name
    output_relative_path = file_name
    if TRANSLATE_HEADER_RE.search(file_content):
        return parse_translation_file_from_content(
            file_name=file_name,
            relative_path=relative_path,
            output_relative_path=output_relative_path,
            raw_content=file_content,
            character_registry=character_registry,
        )
    return parse_source_file_from_content(
        file_name=file_name,
        relative_path=relative_path,
        output_relative_path=output_relative_path,
        raw_content=file_content,
        character_registry=character_registry,
    )


def collect_analysis_corpus(analyzed_files: List[AnalyzedFile], limit: int = 120000) -> str:
    fragments: List[str] = []
    total_length = 0
    for analyzed_file in analyzed_files:
        for item in analyzed_file.items:
            text = item.source_text.strip()
            if not text:
                continue
            fragments.append(text)
            total_length += len(text)
            if total_length >= limit:
                return "\n".join(fragments)
    return "\n".join(fragments)


def infer_world_defaults(
    analyzed_files: List[AnalyzedFile],
    term_counts: Dict[str, int],
    adult_count: int,
) -> Dict[str, Any]:
    corpus = collect_analysis_corpus(analyzed_files).lower()
    glossary_terms = [term for term, _ in sorted(term_counts.items(), key=lambda pair: (-pair[1], pair[0]))[:8]]

    fantasy_terms = ("fae", "magic", "spirit", "dryad", "nymph", "werewolf", "changeling", "kingdom", "deity")
    coastal_terms = ("sea", "shore", "boat", "ocean", "harbor", "tide", "wave", "shark", "fishing")
    rural_terms = ("farm", "herd", "sheepdog", "village", "pastor", "cattle", "barn", "field")
    period_terms = ("gran", "pub", "lavvy", "whist", "maidens", "parlor", "tea", "carriage")
    modern_terms = ("phone", "laptop", "texted", "apartment", "car", "internet", "elevator")
    romance_terms = ("kiss", "love", "flirt", "heart", "blush", "darling", "desire")

    def keyword_score(keyword_group: tuple[str, ...]) -> int:
        return sum(corpus.count(term) for term in keyword_group)

    fantasy_score = keyword_score(fantasy_terms)
    coastal_score = keyword_score(coastal_terms)
    rural_score = keyword_score(rural_terms)
    period_score = keyword_score(period_terms)
    modern_score = keyword_score(modern_terms)
    romance_score = keyword_score(romance_terms)

    era_label = "현대물"
    if period_score > modern_score:
        era_label = "근대풍 시대극"
    elif fantasy_score > 0 and modern_score == 0:
        era_label = "시대감이 흐릿한 판타지극"

    setting_parts: List[str] = [era_label]
    if coastal_score > 0 and rural_score > 0:
        setting_parts.append("해안 농촌/소도시 분위기")
    elif coastal_score > 0:
        setting_parts.append("해안/항구 배경")
    elif rural_score > 0:
        setting_parts.append("농촌/마을 배경")

    if fantasy_score > 0:
        setting_parts.append("민속/페이 계열 판타지")
    if romance_score > 0:
        setting_parts.append("로맨스 감정선 비중이 큼")
    if adult_count > 0:
        setting_parts.append("성인 묘사가 섞여 있음")

    world_description = " / ".join(setting_parts)
    tone_notes_parts = [
        "대사 톤은 캐릭터별 말투 차이를 크게 유지",
        "고유명사는 음차와 의미 번역을 혼용하되 용어집 우선 적용",
    ]
    if period_score > modern_score:
        tone_notes_parts.append("현대식 직역보다 약간 고전적이고 생활감 있는 표현을 우선")
    if fantasy_score > 0:
        tone_notes_parts.append("민속/환상 요소는 가볍게 풀지 말고 신화적 분위기를 유지")
    if coastal_score > 0 or rural_score > 0:
        tone_notes_parts.append("촌락/해안 지역 특유의 소박한 생활감을 살림")
    if adult_count > 0:
        tone_notes_parts.append("성인 장면은 수위를 완화하지 말고 문맥상 감정선과 신체 묘사를 유지")

    style_rules_parts = [
        "Ren'Py 태그, 변수, 줄바꿈, 플레이스홀더는 그대로 유지",
        "화자별 호칭과 관계어는 일관되게 유지",
        "UI 문자열과 대사는 문체를 분리",
    ]
    if period_score > modern_score:
        style_rules_parts.append(
            "시대감 있는 어휘는 자연스럽게 활용하되, "
            "대사 말투는 격식 종결어미(-습니다/-겠습니다 등 하오체/합쇼체)를 쓰지 말고 "
            "각 캐릭터 guidance에 명시된 구어체를 유지할 것"
        )

    protected_terms = []
    for term in glossary_terms[:6]:
        if len(term) >= 3:
            protected_terms.append(term)

    rationale = {
        "fantasy_score": fantasy_score,
        "coastal_score": coastal_score,
        "rural_score": rural_score,
        "period_score": period_score,
        "modern_score": modern_score,
        "romance_score": romance_score,
    }

    return {
        "world_description": world_description,
        "tone_notes": "\n".join(tone_notes_parts),
        "style_rules": "\n".join(style_rules_parts),
        "protected_terms": protected_terms,
        "glossary": [{"source": term, "target": "", "note": "자동 추천 용어"} for term in protected_terms[:4]],
        "rationale": rationale,
    }


def infer_character_defaults(character_stat: Dict[str, Any]) -> Dict[str, str]:
    speaker_id = character_stat["speaker_id"]
    display_name = character_stat.get("display_name") or speaker_id
    line_count = character_stat.get("line_count", 0)
    adult_line_count = character_stat.get("adult_line_count", 0)
    samples = " ".join(character_stat.get("sample_lines") or []).lower()

    if speaker_id == DEFAULT_FALLBACK_PERSONA_KEY:
        return {
            "display_name": display_name,
            "tone_preset_id": "ui_clean",
            "role": "UI/선택지/고정 문자열",
            "tone": "간결하고 안정적인 인터페이스 문체",
            "notes": "메뉴/버튼/시스템 문자열은 짧고 명확하게 유지",
        }
    if speaker_id == NARRATION_PERSONA_KEY:
        return {
            "display_name": display_name,
            "tone_preset_id": "literary_narration",
            "role": "내레이션/지문",
            "tone": "묘사 중심의 서술체",
            "notes": "장면 분위기와 감정선이 살아 있도록 서술 문장을 매끄럽게 유지",
        }

    role = "단역 또는 상황형 캐릭터"
    if line_count >= 1500:
        role = "주연급 캐릭터"
    elif line_count >= 400:
        role = "반복 등장 조연"
    elif line_count >= 120:
        role = "중간 비중 조연"

    tone_markers: List[str] = []
    notes_markers: List[str] = []
    tone_preset_id = "neutral_conversational"

    if any(token in samples for token in ("gran", "yer", "lass", "eh", "aye", "lickety")):
        tone_markers.append("생활감 있는 구어체")
        notes_markers.append("지역색/사투리 느낌이 보이면 과하게 표준화하지 않기")
        tone_preset_id = "rustic_plain"
    if any(token in samples for token in ("well", "um", "sorry", "please", "i don't know")):
        tone_markers.append("조심스럽고 부드러운 말투")
        if tone_preset_id == "neutral_conversational":
            tone_preset_id = "warm_gentle"
    if any(token in samples for token in ("!", "of course", "absolutely", "come", "listen", "no!")):
        tone_markers.append("감정 표현이 비교적 선명함")
        if tone_preset_id == "neutral_conversational":
            tone_preset_id = "bright_playful"
    if any(token in samples for token in ("kiss", "beautiful", "love", "dear", "lust", "bed", "flirt")) or adult_line_count > 0:
        tone_markers.append("로맨틱/관능적 뉘앙스 가능")
        tone_preset_id = "seductive_teasing"
    if any(token in samples for token in ("help", "tea", "home", "gentle", "sweet")):
        tone_markers.append("다정하고 돌보는 느낌")
        if tone_preset_id == "neutral_conversational":
            tone_preset_id = "warm_gentle"

    if not tone_markers:
        if line_count >= 400:
            tone_markers.append("캐릭터성이 뚜렷한 자연스러운 구어체")
        else:
            tone_markers.append("상황에 맞춘 기본 구어체")

    if adult_line_count > 0:
        notes_markers.append("성인 장면에서 수위를 임의로 낮추지 않기")
    if line_count >= 1500:
        notes_markers.append("주요 서사 축에 속할 가능성이 높으므로 호칭/말투 일관성 우선")
    elif line_count < 40:
        notes_markers.append("짧은 등장분량이라도 말버릇이 있으면 유지")

    # 어떤 비-UI 캐릭터든 격식체(하오체) 방지 안내를 notes 맨 앞에 추가
    notes_markers.insert(0, "격식 종결어미(-습니다/-겠습니다/-입니다 등 하오체/합쇼체) 사용 금지, 구어체 유지")

    return {
        "display_name": display_name,
        "tone_preset_id": tone_preset_id,
        "role": role,
        "tone": ", ".join(dict.fromkeys(tone_markers)),
        "notes": " / ".join(dict.fromkeys(notes_markers)) if notes_markers else "샘플 대사를 보고 추가 보정 권장",
    }


def normalize_translation_compare_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def build_translation_match_key(
    file_relative_path: str,
    kind: str,
    speaker_id: Optional[str],
    source_text: str,
) -> str:
    return "|".join(
        [
            str(file_relative_path or "").strip().lower(),
            str(kind or "").strip().lower(),
            normalize_identifier_token(speaker_id or ""),
            normalize_translation_compare_text(source_text),
        ]
    )


def is_meaningfully_translated(source_text: str, translated_text: str) -> bool:
    translated = normalize_translation_compare_text(translated_text)
    if not translated:
        return False
    return translated != normalize_translation_compare_text(source_text)


def get_existing_live_translation_text(item: TranslationItem) -> str:
    for candidate in (
        item.workbench_translation_text,
        item.connected_translation_text,
        item.current_text,
    ):
        if normalize_translation_compare_text(candidate):
            return candidate
    return ""


def build_issue_candidate_reason(item: TranslationItem) -> Tuple[str, str]:
    source_text = normalize_translation_compare_text(item.source_text)
    if normalize_translation_compare_text(item.workbench_translation_text) == source_text:
        return ("workbench_same_as_source", "워크벤치 출력이 원문 그대로 남아 있음")
    if normalize_translation_compare_text(item.connected_translation_text) == source_text:
        return ("connected_same_as_source", "게임 연결 번역이 원문 그대로 남아 있음")
    if normalize_translation_compare_text(item.current_text) == source_text:
        return ("current_layer_same_as_source", "현재 번역 레이어가 원문 그대로 남아 있음")
    return ("missing_translation", "번역문이 아직 연결되지 않았거나 비어 있음")


def should_skip_issue_candidate(item: TranslationItem) -> bool:
    source_text = (item.source_text or "").strip()
    if not source_text:
        return True
    if item.kind not in {"dialogue", "narration", "string"}:
        return True
    if is_passthrough_translation_item(item):
        return True
    if is_markup_only_text(source_text) or is_low_signal_sample(source_text):
        return True
    if "{#donottranslate" in source_text.lower():
        return True

    cleaned = re.sub(r"\{[^{}]+\}", "", source_text)
    cleaned = cleaned.replace("\\n", " ").replace("\n", " ").strip()
    if not cleaned or not ASCII_LETTER_RE.search(cleaned):
        return True
    if PLACEHOLDER_COUNTER_RE.fullmatch(cleaned):
        return True
    if GALLERY_LABEL_RE.fullmatch(cleaned):
        return True
    if SPRITE_STATE_LINE_RE.fullmatch(cleaned):
        return True
    token_parts = re.findall(r"[A-Za-z0-9_]+", cleaned)
    if token_parts:
        single_letter_alpha_count = sum(1 for part in token_parts if len(part) == 1 and part.isalpha())
        if single_letter_alpha_count >= 2:
            return True
        if (
            len(token_parts[0]) == 1
            and token_parts[0].isalpha()
            and any(any(character.isdigit() for character in part) for part in token_parts[1:])
        ):
            return True
    word_parts = [part.lower() for part in re.findall(r"[A-Za-z']+", cleaned)]
    has_sentence_hint = any(part in SENTENCE_HINT_WORDS for part in word_parts)
    has_sentence_punctuation = any(token in cleaned for token in ("?", "!", "...", "…", ".", ";", ":"))
    if word_parts and len(word_parts) <= 4 and not has_sentence_hint and not has_sentence_punctuation:
        return True
    if TOKENISH_TEXT_RE.fullmatch(cleaned) and " " not in cleaned and len(cleaned) <= 24:
        return True
    return False


def build_issue_candidate_payload(item: TranslationItem) -> Optional[Dict[str, Any]]:
    if item.translation_status != "untranslated":
        return None
    if should_skip_issue_candidate(item):
        return None

    cleaned = re.sub(r"\s+", " ", re.sub(r"\{[^{}]+\}", "", (item.source_text or "").replace("\\n", " ")).strip())
    reason_code, reason_text = build_issue_candidate_reason(item)
    score = 0
    if item.kind in {"dialogue", "narration"}:
        score += 2
    if " " in cleaned:
        score += 3
    if len(cleaned) >= 20:
        score += 2
    if len(cleaned) >= 60:
        score += 1
    if any(token in cleaned for token in ("?", "!", ",", ";", ":")):
        score += 1
    if item.adult:
        score += 1

    payload = item.to_public_dict()
    payload.update(
        {
            "issue_reason_code": reason_code,
            "issue_reason": reason_text,
            "issue_score": score,
            "issue_live_text": get_existing_live_translation_text(item),
        }
    )
    return payload


def load_existing_translation_lookup(
    analyzed_files: List[AnalyzedFile],
    character_registry: Dict[str, Dict[str, Any]],
    analysis_mode: str,
    overlay_root: Optional[Path],
    source_label: Optional[str] = None,
) -> Dict[str, Any]:
    if overlay_root is None or not overlay_root.is_dir():
        return {"by_item_id": {}, "by_match_key": {}}

    translated_lookup: Dict[str, Dict[str, str]] = {}
    match_lookup: Dict[str, List[Dict[str, str]]] = {}
    for document in analyzed_files:
        overlay_path = overlay_root / Path(document.output_relative_path)
        if not overlay_path.is_file():
            continue
        raw_content = read_text_file(overlay_path)
        if analysis_mode == "translation_layer":
            overlay_document = parse_translation_file_from_content(
                file_name=document.file_name,
                relative_path=document.file_relative_path,
                output_relative_path=document.output_relative_path,
                raw_content=raw_content,
                character_registry=character_registry,
            )
        else:
            overlay_document = parse_source_file_from_content(
                file_name=document.file_name,
                relative_path=document.file_relative_path,
                output_relative_path=document.output_relative_path,
                raw_content=raw_content,
                character_registry=character_registry,
            )
        for item in overlay_document.items:
            payload = {
                "text": item.current_text,
                "source": source_label or overlay_root.name,
            }
            translated_lookup[item.item_id] = payload
            match_key = build_translation_match_key(
                file_relative_path=item.file_relative_path,
                kind=item.kind,
                speaker_id=item.speaker_id,
                source_text=item.source_text,
            )
            match_lookup.setdefault(match_key, []).append(payload)
    return {"by_item_id": translated_lookup, "by_match_key": match_lookup}


def collect_connected_translation_overlays(
    game_dir_path: Path,
    target_language: str,
) -> List[Dict[str, Any]]:
    tl_root = game_dir_path / "tl"
    if not tl_root.is_dir():
        return []

    normalized_target = normalize_language_code(target_language)
    overlays: List[Dict[str, Any]] = []
    for child in tl_root.iterdir():
        if not child.is_dir():
            continue
        folder_name = str(child.name or "").strip()
        if not folder_name or folder_name.lower() == "none":
            continue
        normalized_name = normalize_language_code(folder_name)
        if not normalized_name.startswith(normalized_target):
            continue

        suffix = normalized_name[len(normalized_target):].lstrip("_")
        if not suffix:
            priority = 0
        elif suffix == "workbench":
            priority = 1
        elif suffix.startswith("workbench"):
            priority = 2
        elif suffix == "ai":
            priority = 4
        else:
            priority = 3
        overlays.append(
            {
                "label": folder_name,
                "path": child,
                "priority": priority,
            }
        )

    overlays.sort(key=lambda item: (item["priority"], item["label"].lower()))
    return overlays


def take_overlay_translation_entry(
    item: TranslationItem,
    overlay_lookup: Dict[str, Any],
    allow_direct: bool = True,
) -> Dict[str, str]:
    if allow_direct:
        direct_lookup = overlay_lookup.get("by_item_id") or {}
        if item.item_id in direct_lookup:
            return direct_lookup[item.item_id]

    if is_low_signal_sample(item.source_text) or is_markup_only_text(item.source_text):
        return {}

    match_lookup = overlay_lookup.get("by_match_key") or {}
    match_key = build_translation_match_key(
        file_relative_path=item.file_relative_path,
        kind=item.kind,
        speaker_id=item.speaker_id,
        source_text=item.source_text,
    )
    candidates = match_lookup.get(match_key) or []
    if not candidates:
        return {}
    payload = candidates.pop(0)
    if not candidates:
        match_lookup.pop(match_key, None)
    return payload


def annotate_existing_translation_state(
    analyzed_files: List[AnalyzedFile],
    character_registry: Dict[str, Dict[str, Any]],
    analysis_mode: str,
    target_language: str,
    game_dir: Optional[str],
) -> None:
    workbench_root: Optional[Path] = None
    connected_lookup: Dict[str, Any] = {"by_item_id": {}, "by_match_key": {}}
    if game_dir:
        game_dir_path = Path(game_dir)
        repair_summary = repair_workbench_outputs_for_game(
            game_dir_path,
            target_language,
            force_cache_cleanup=False,
        )
        embedded_output_migration = repair_summary["embedded_output_migration"]
        nested_artifact_migration = repair_summary["nested_artifact_migration"]
        repaired_outputs = repair_summary["repaired_outputs"]
        if embedded_output_migration.get("migrated"):
            log_message(
                f"embedded workbench output moved outside game dir: {embedded_output_migration['embedded_root']} -> {embedded_output_migration['safe_root']}",
                "Translation",
            )
        if nested_artifact_migration.get("migrated"):
            log_message(
                f"nested workbench artifacts recovered from tl folders: {len(nested_artifact_migration['moved_paths'])} path(s)",
                "Translation",
            )
        if repaired_outputs.get("repaired"):
            log_message(
                f"repaired malformed workbench translation blocks: {len(repaired_outputs['changed_paths'])} file(s)",
                "Translation",
            )
        for overlay in collect_connected_translation_overlays(game_dir_path, target_language):
            overlay_lookup = load_existing_translation_lookup(
                analyzed_files=analyzed_files,
                character_registry=character_registry,
                analysis_mode="translation_layer",
                overlay_root=overlay["path"],
                source_label=overlay["label"],
            )
            for item_id, payload in (overlay_lookup.get("by_item_id") or {}).items():
                connected_lookup["by_item_id"].setdefault(item_id, payload)
            for match_key, payloads in (overlay_lookup.get("by_match_key") or {}).items():
                connected_lookup["by_match_key"].setdefault(match_key, []).extend(payloads)
        if analysis_mode == "translation_layer":
            workbench_root = get_translation_layer_stage_root(game_dir_path, target_language)
        elif analysis_mode == "source_files":
            workbench_root = get_source_stage_root(game_dir_path, target_language)

    workbench_lookup = load_existing_translation_lookup(
        analyzed_files=analyzed_files,
        character_registry=character_registry,
        analysis_mode=analysis_mode,
        overlay_root=workbench_root,
    )

    for document in analyzed_files:
        for item in document.items:
            connected_text = ""
            connected_source = ""
            if analysis_mode == "translation_layer" and is_meaningfully_translated(item.source_text, item.current_text):
                connected_text = item.current_text
                connected_source = target_language
            else:
                connected_entry = take_overlay_translation_entry(item, connected_lookup, allow_direct=analysis_mode == "translation_layer")
                if is_meaningfully_translated(item.source_text, connected_entry.get("text", "")):
                    connected_text = connected_entry.get("text", "")
                    connected_source = connected_entry.get("source", "")

            workbench_entry = take_overlay_translation_entry(item, workbench_lookup, allow_direct=True)
            workbench_text = workbench_entry.get("text", "")
            workbench_source = workbench_entry.get("source", "")
            item.connected_translation_text = connected_text
            item.connected_translation_source = connected_source
            item.workbench_translation_text = workbench_text
            item.workbench_translation_source = workbench_source

            if is_meaningfully_translated(item.source_text, workbench_text):
                item.translation_status = "workbench_translated"
                item.translation_source = f"workbench_output:{workbench_source or 'staging'}"
                item.effective_translation_text = workbench_text
            elif is_meaningfully_translated(item.source_text, connected_text):
                item.translation_status = "game_translated"
                item.translation_source = f"game_translation:{connected_source or target_language}"
                item.effective_translation_text = connected_text
            else:
                item.translation_status = "untranslated"
                item.translation_source = "source_text"
                item.effective_translation_text = ""


def build_analysis_response(
    analyzed_files: List[AnalyzedFile],
    character_registry: Dict[str, Dict[str, Any]],
    analysis_mode: str,
    source_label: str,
    target_language: str,
    game_dir: Optional[str] = None,
    gui_baseline: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    annotate_existing_translation_state(
        analyzed_files=analyzed_files,
        character_registry=character_registry,
        analysis_mode=analysis_mode,
        target_language=target_language,
        game_dir=game_dir,
    )
    character_stats: Dict[str, Dict[str, Any]] = {
        key: {
            "speaker_id": value["speaker_id"],
            "display_name": value.get("display_name"),
            "defined_in": value.get("defined_in"),
            "portrait": value.get("portrait"),
            "line_count": 0,
            "adult_line_count": 0,
            "untranslated_line_count": 0,
            "game_translated_line_count": 0,
            "workbench_translated_line_count": 0,
            "sample_lines": [],
        }
        for key, value in character_registry.items()
    }
    adult_queue: List[Dict[str, Any]] = []
    issue_candidates: List[Dict[str, Any]] = []
    term_counts: Dict[str, int] = {}
    dialogue_preview: List[Dict[str, Any]] = []
    dialogue_preview_limits = {
        "untranslated": 32,
        "game_translated": 24,
        "workbench_translated": 24,
    }
    dialogue_preview_counts = {key: 0 for key in dialogue_preview_limits}

    total_items = 0
    dialogue_count = 0
    narration_count = 0
    string_count = 0
    adult_count = 0
    untranslated_count = 0
    game_translated_count = 0
    workbench_translated_count = 0

    for analyzed_file in analyzed_files:
        for item in analyzed_file.items:
            total_items += 1
            if item.translation_status == "workbench_translated":
                workbench_translated_count += 1
            elif item.translation_status == "game_translated":
                game_translated_count += 1
            else:
                untranslated_count += 1
            if item.kind == "dialogue":
                dialogue_count += 1
            elif item.kind == "narration":
                narration_count += 1
            elif item.kind == "string":
                string_count += 1

            stats_key = item.speaker_id or NARRATION_PERSONA_KEY
            if stats_key not in character_stats:
                character_stats[stats_key] = {
                    "speaker_id": stats_key,
                    "display_name": item.speaker_name,
                    "defined_in": analyzed_file.file_name,
                    "portrait": character_registry.get(stats_key, {}).get("portrait"),
                    "line_count": 0,
                    "adult_line_count": 0,
                    "untranslated_line_count": 0,
                    "game_translated_line_count": 0,
                    "workbench_translated_line_count": 0,
                    "sample_lines": [],
                }
            character_stats[stats_key]["line_count"] += 1
            if item.translation_status == "workbench_translated":
                character_stats[stats_key]["workbench_translated_line_count"] += 1
            elif item.translation_status == "game_translated":
                character_stats[stats_key]["game_translated_line_count"] += 1
            else:
                character_stats[stats_key]["untranslated_line_count"] += 1
            if not is_low_signal_sample(item.source_preview) and len(character_stats[stats_key]["sample_lines"]) < 3:
                character_stats[stats_key]["sample_lines"].append(item.source_preview)
            preview_limit = dialogue_preview_limits.get(item.translation_status, 16)
            if (
                item.kind in {"dialogue", "narration"}
                and len(dialogue_preview) < 80
                and dialogue_preview_counts.get(item.translation_status, 0) < preview_limit
            ):
                dialogue_preview.append(
                    {
                        "item_id": item.item_id,
                        "file_relative_path": item.file_relative_path,
                        "speaker_id": item.speaker_id,
                        "speaker_name": item.speaker_name,
                        "kind": item.kind,
                        "line_number": item.line_number,
                        "source_text": item.source_text,
                        "current_text": item.current_text,
                        "translation_status": item.translation_status,
                        "translation_source": item.translation_source,
                        "connected_translation_text": item.connected_translation_text,
                        "connected_translation_source": item.connected_translation_source,
                        "workbench_translation_text": item.workbench_translation_text,
                        "workbench_translation_source": item.workbench_translation_source,
                        "effective_translation_text": item.effective_translation_text,
                    }
                )
                dialogue_preview_counts[item.translation_status] = dialogue_preview_counts.get(item.translation_status, 0) + 1

            if item.adult:
                adult_count += 1
                character_stats[stats_key]["adult_line_count"] += 1
                if len(adult_queue) < 60:
                    adult_queue.append(
                        {
                            "item_id": item.item_id,
                            "file_relative_path": item.file_relative_path,
                            "speaker_id": item.speaker_id,
                            "speaker_name": item.speaker_name,
                            "kind": item.kind,
                            "line_number": item.line_number,
                            "source_text": item.source_text,
                            "current_text": item.current_text,
                            "translation_status": item.translation_status,
                            "translation_source": item.translation_source,
                            "connected_translation_text": item.connected_translation_text,
                            "connected_translation_source": item.connected_translation_source,
                            "workbench_translation_text": item.workbench_translation_text,
                            "workbench_translation_source": item.workbench_translation_source,
                            "effective_translation_text": item.effective_translation_text,
                            "context_before": item.context_before,
                            "context_after": item.context_after,
                            "adult_keywords": item.adult_keywords,
                        }
                    )

            issue_candidate = build_issue_candidate_payload(item)
            if issue_candidate is not None:
                issue_candidates.append(issue_candidate)

            for term in PROPER_NOUN_RE.findall(item.source_text):
                lowered = term.lower()
                if len(term) < 3 or lowered in PROPER_NOUN_STOPWORDS or lowered in {"and", "but"}:
                    continue
                term_counts[term] = term_counts.get(term, 0) + 1

    issue_candidates.sort(
        key=lambda entry: (
            -int(entry.get("issue_score") or 0),
            str(entry.get("file_relative_path") or ""),
            int(entry.get("line_number") or 0),
            str(entry.get("item_id") or ""),
        )
    )

    glossary_suggestions = []
    for term, count in sorted(term_counts.items(), key=lambda pair: (-pair[1], pair[0]))[:20]:
        glossary_suggestions.append({"source": term, "target": "", "note": f"반복 등장 {count}회"})

    files_payload = [analyzed_file.to_public_dict() for analyzed_file in analyzed_files]
    character_payload = sorted(
        [
            item
            for item in character_stats.values()
            if item["line_count"] > 0 or item["speaker_id"] in {DEFAULT_FALLBACK_PERSONA_KEY, NARRATION_PERSONA_KEY}
        ],
        key=lambda item: (
            item["speaker_id"] in {DEFAULT_FALLBACK_PERSONA_KEY, NARRATION_PERSONA_KEY},
            -item["line_count"],
            item["speaker_id"],
        ),
    )
    default_character_profiles = {
        item["speaker_id"]: infer_character_defaults(item)
        for item in character_payload
    }
    default_world_settings = infer_world_defaults(analyzed_files, term_counts, adult_count)
    baseline_payload = gui_baseline or {}
    default_publish_settings = build_default_publish_settings(
        target_language=target_language,
        analysis_mode=analysis_mode,
        gui_baseline=baseline_payload,
    )

    return {
        "analysis_mode": analysis_mode,
        "source_label": source_label,
        "target_language": target_language,
        "game_dir": game_dir,
        "files": files_payload,
        "characters": character_payload,
        "dialogue_preview": dialogue_preview,
        "adult_queue": adult_queue,
        "issue_candidates": issue_candidates,
        "summary": {
            "file_count": len(analyzed_files),
            "item_count": total_items,
            "dialogue_count": dialogue_count,
            "narration_count": narration_count,
            "string_count": string_count,
            "adult_item_count": adult_count,
            "issue_candidate_count": len(issue_candidates),
            "untranslated_item_count": untranslated_count,
            "game_translated_item_count": game_translated_count,
            "workbench_translated_item_count": workbench_translated_count,
        },
        "glossary_suggestions": glossary_suggestions,
        "default_character_profiles": default_character_profiles,
        "default_world_settings": default_world_settings,
        "gui_baseline": baseline_payload,
        "default_publish_settings": default_publish_settings,
    }


def analyze_game_path(game_exe_path: str, target_language: str) -> Dict[str, Any]:
    game_dir_str = find_game_directory(game_exe_path)
    if not game_dir_str:
        raise FileNotFoundError("'game' 폴더를 찾지 못했습니다.")

    game_dir = Path(game_dir_str)
    migrate_legacy_translation_layer_stage_root(game_dir, target_language)
    source_files = list_game_source_scripts(game_dir)
    character_registry = collect_character_definitions(source_files)
    collect_character_portraits(game_dir, source_files, character_registry)
    gui_baseline = extract_gui_baseline(game_dir)
    scan_decision = choose_scan_mode(game_dir, target_language)

    analyzed_files: List[AnalyzedFile] = []
    if scan_decision["mode"] == "translation_layer":
        for absolute_path in scan_decision["files"]:
            relative_path = str(absolute_path.relative_to(game_dir)).replace("\\", "/")
            output_relative_path = str(absolute_path.relative_to(game_dir / "tl" / target_language)).replace("\\", "/")
            analyzed_file = parse_translation_file(absolute_path, relative_path, output_relative_path, character_registry)
            if analyzed_file.items:
                analyzed_files.append(analyzed_file)
    else:
        for absolute_path in scan_decision["files"]:
            relative_path = str(absolute_path.relative_to(game_dir)).replace("\\", "/")
            analyzed_file = parse_source_file(absolute_path, relative_path, relative_path, character_registry)
            if analyzed_file.items:
                analyzed_files.append(analyzed_file)

    return build_analysis_response(
        analyzed_files=analyzed_files,
        character_registry=character_registry,
        analysis_mode=scan_decision["mode"],
        source_label="game_exe_path",
        target_language=target_language,
        game_dir=game_dir_str,
        gui_baseline=gui_baseline,
    )


def analyze_uploaded_files(files_data: List[Dict[str, Any]], target_language: str) -> Dict[str, Any]:
    character_registry = {
        NARRATION_PERSONA_KEY: {
            "speaker_id": NARRATION_PERSONA_KEY,
            "display_name": "Narration",
            "defined_in": "uploaded",
        },
        DEFAULT_FALLBACK_PERSONA_KEY: {
            "speaker_id": DEFAULT_FALLBACK_PERSONA_KEY,
            "display_name": "Default",
            "defined_in": "uploaded",
        },
    }
    analyzed_files = []
    for file_data in files_data:
        file_name = file_data.get("file_name") or "uploaded.rpy"
        file_content = file_data.get("file_content") or ""
        original_rpy_path = file_data.get("original_rpy_path")
        analyzed_file = parse_uploaded_file(file_name, file_content, original_rpy_path, character_registry)
        if analyzed_file.items:
            analyzed_files.append(analyzed_file)
    return build_analysis_response(
        analyzed_files=analyzed_files,
        character_registry=character_registry,
        analysis_mode="uploaded_files",
        source_label="files_data",
        target_language=target_language,
        game_dir=None,
        gui_baseline={},
    )


def normalize_selected_speaker_ids(payload: Dict[str, Any]) -> Set[str]:
    normalized_ids: Set[str] = set()
    for entry in payload.get("selected_speaker_ids") or []:
        candidate = str(entry or "").strip()
        if candidate:
            normalized_ids.add(candidate)
    return normalized_ids


def normalize_selected_item_ids(payload: Dict[str, Any]) -> Set[str]:
    normalized_ids: Set[str] = set()
    for entry in payload.get("selected_item_ids") or []:
        candidate = str(entry or "").strip()
        if candidate:
            normalized_ids.add(candidate)
    return normalized_ids


def filter_documents_by_speaker_ids(
    documents: List[AnalyzedFile],
    selected_speaker_ids: Set[str],
) -> List[AnalyzedFile]:
    if not selected_speaker_ids:
        return documents

    filtered_documents: List[AnalyzedFile] = []
    for document in documents:
        filtered_items = [
            item
            for item in document.items
            if (item.speaker_id or NARRATION_PERSONA_KEY) in selected_speaker_ids
        ]
        if not filtered_items:
            continue
        filtered_documents.append(
            AnalyzedFile(
                absolute_path=document.absolute_path,
                file_relative_path=document.file_relative_path,
                output_relative_path=document.output_relative_path,
                file_name=document.file_name,
                file_mode=document.file_mode,
                raw_content=document.raw_content,
                items=filtered_items,
            )
        )
    return filtered_documents


def filter_documents_by_item_ids(
    documents: List[AnalyzedFile],
    selected_item_ids: Set[str],
) -> List[AnalyzedFile]:
    if not selected_item_ids:
        return documents

    filtered_documents: List[AnalyzedFile] = []
    for document in documents:
        filtered_items = [
            item
            for item in document.items
            if item.item_id in selected_item_ids
        ]
        if not filtered_items:
            continue
        filtered_documents.append(
            AnalyzedFile(
                absolute_path=document.absolute_path,
                file_relative_path=document.file_relative_path,
                output_relative_path=document.output_relative_path,
                file_name=document.file_name,
                file_mode=document.file_mode,
                raw_content=document.raw_content,
                items=filtered_items,
            )
        )
    return filtered_documents


def normalize_translation_rule(payload: Dict[str, Any]) -> str:
    rule = str(payload.get("translation_rule") or "missing_only").strip().lower()
    if rule not in {"missing_only", "retranslate_existing", "force_all"}:
        return "missing_only"
    return rule


def should_include_item_for_translation_rule(item: TranslationItem, translation_rule: str) -> bool:
    if translation_rule == "force_all":
        return True
    if translation_rule == "retranslate_existing":
        return item.translation_status in {"game_translated", "workbench_translated"}
    return item.translation_status == "untranslated"


def filter_documents_by_translation_rule(
    documents: List[AnalyzedFile],
    translation_rule: str,
) -> List[AnalyzedFile]:
    if translation_rule == "force_all":
        return documents

    filtered_documents: List[AnalyzedFile] = []
    for document in documents:
        filtered_items = [
            item
            for item in document.items
            if should_include_item_for_translation_rule(item, translation_rule)
        ]
        if not filtered_items:
            continue
        filtered_documents.append(
            AnalyzedFile(
                absolute_path=document.absolute_path,
                file_relative_path=document.file_relative_path,
                output_relative_path=document.output_relative_path,
                file_name=document.file_name,
                file_mode=document.file_mode,
                raw_content=document.raw_content,
                items=filtered_items,
            )
        )
    return filtered_documents


def get_documents_for_translation(payload: Dict[str, Any]) -> Dict[str, Any]:
    target_language = payload.get("target_language") or DEFAULT_TARGET_LANGUAGE
    selected_files = set(payload.get("selected_files") or [])
    selected_speaker_ids = normalize_selected_speaker_ids(payload)
    selected_item_ids = normalize_selected_item_ids(payload)
    translation_rule = normalize_translation_rule(payload)
    incoming_scope = payload.get("translation_scope") or {}
    selected_speaker_names = [
        str(value or "").strip()
        for value in (incoming_scope.get("selected_speaker_names") or [])
        if str(value or "").strip()
    ]

    if payload.get("game_exe_path"):
        game_dir_str = find_game_directory(payload["game_exe_path"])
        if not game_dir_str:
            raise FileNotFoundError("'game' 폴더를 찾지 못했습니다.")
        game_dir = Path(game_dir_str)
        source_files = list_game_source_scripts(game_dir)
        character_registry = collect_character_definitions(source_files)
        collect_character_portraits(game_dir, source_files, character_registry)
        scan_decision = choose_scan_mode(game_dir, target_language)
        analyzed_files: List[AnalyzedFile] = []
        if scan_decision["mode"] == "translation_layer":
            for absolute_path in scan_decision["files"]:
                relative_path = str(absolute_path.relative_to(game_dir)).replace("\\", "/")
                if selected_files and relative_path not in selected_files:
                    continue
                output_relative_path = str(absolute_path.relative_to(game_dir / "tl" / target_language)).replace("\\", "/")
                analyzed_file = parse_translation_file(absolute_path, relative_path, output_relative_path, character_registry)
                if analyzed_file.items:
                    analyzed_files.append(analyzed_file)
        else:
            for absolute_path in scan_decision["files"]:
                relative_path = str(absolute_path.relative_to(game_dir)).replace("\\", "/")
                if selected_files and relative_path not in selected_files:
                    continue
                analyzed_file = parse_source_file(absolute_path, relative_path, relative_path, character_registry)
                if analyzed_file.items:
                    analyzed_files.append(analyzed_file)

        annotate_existing_translation_state(
            analyzed_files=analyzed_files,
            character_registry=character_registry,
            analysis_mode=scan_decision["mode"],
            target_language=target_language,
            game_dir=game_dir_str,
        )
        filtered_documents = filter_documents_by_speaker_ids(analyzed_files, selected_speaker_ids)
        filtered_documents = filter_documents_by_translation_rule(filtered_documents, translation_rule)
        filtered_documents = filter_documents_by_item_ids(filtered_documents, selected_item_ids)
        scope_mode = "selected_items" if selected_item_ids else ("selected_speakers" if selected_speaker_ids else "all_items")

        return {
            "documents": filtered_documents,
            "character_registry": character_registry,
            "analysis_mode": scan_decision["mode"],
            "target_language": target_language,
            "game_dir": game_dir_str,
            "translation_scope": {
                "mode": scope_mode,
                "selected_speaker_ids": sorted(selected_speaker_ids),
                "selected_speaker_names": selected_speaker_names,
                "selected_item_ids": sorted(selected_item_ids),
                "selected_item_count": len(selected_item_ids),
                "translation_rule": translation_rule,
                "force_retranslate": bool(payload.get("force_retranslate")) or translation_rule != "missing_only",
            },
        }

    files_data = payload.get("files_data") or []
    if not files_data:
        raise ValueError("번역할 파일 데이터가 없습니다.")

    character_registry = {
        NARRATION_PERSONA_KEY: {
            "speaker_id": NARRATION_PERSONA_KEY,
            "display_name": "Narration",
            "defined_in": "uploaded",
        },
        DEFAULT_FALLBACK_PERSONA_KEY: {
            "speaker_id": DEFAULT_FALLBACK_PERSONA_KEY,
            "display_name": "Default",
            "defined_in": "uploaded",
        },
    }
    analyzed_files = []
    for file_data in files_data:
        file_name = file_data.get("file_name") or "uploaded.rpy"
        relative_path = file_data.get("original_rpy_path") or file_name
        if selected_files and relative_path not in selected_files and file_name not in selected_files:
            continue
        analyzed_file = parse_uploaded_file(
            file_name=file_name,
            file_content=file_data.get("file_content") or "",
            original_rpy_path=file_data.get("original_rpy_path"),
            character_registry=character_registry,
        )
        if analyzed_file.items:
            analyzed_files.append(analyzed_file)

    annotate_existing_translation_state(
        analyzed_files=analyzed_files,
        character_registry=character_registry,
        analysis_mode="uploaded_files",
        target_language=target_language,
        game_dir=None,
    )
    filtered_documents = filter_documents_by_speaker_ids(analyzed_files, selected_speaker_ids)
    filtered_documents = filter_documents_by_translation_rule(filtered_documents, translation_rule)
    filtered_documents = filter_documents_by_item_ids(filtered_documents, selected_item_ids)
    scope_mode = "selected_items" if selected_item_ids else ("selected_speakers" if selected_speaker_ids else "all_items")

    return {
        "documents": filtered_documents,
        "character_registry": character_registry,
        "analysis_mode": "uploaded_files",
        "target_language": target_language,
        "game_dir": None,
        "translation_scope": {
            "mode": scope_mode,
            "selected_speaker_ids": sorted(selected_speaker_ids),
            "selected_speaker_names": selected_speaker_names,
            "selected_item_ids": sorted(selected_item_ids),
            "selected_item_count": len(selected_item_ids),
            "translation_rule": translation_rule,
            "force_retranslate": bool(payload.get("force_retranslate")) or translation_rule != "missing_only",
        },
    }


def normalize_glossary_entries(world_settings: Dict[str, Any]) -> List[Dict[str, str]]:
    glossary_entries = []
    for entry in world_settings.get("glossary", []) or []:
        source = (entry.get("source") or "").strip()
        target = (entry.get("target") or "").strip()
        note = (entry.get("note") or "").strip()
        if source:
            glossary_entries.append({"source": source, "target": target, "note": note})
    return glossary_entries


def build_character_guidance(
    item_batch: List[TranslationItem],
    character_profiles: Dict[str, Any],
    character_registry: Dict[str, Dict[str, Any]],
) -> List[str]:
    used_keys = {item.speaker_id or NARRATION_PERSONA_KEY for item in item_batch}
    used_keys.add(DEFAULT_FALLBACK_PERSONA_KEY)
    guidance_lines = []

    for key in sorted(used_keys):
        profile = character_profiles.get(key, {})
        registry_entry = character_registry.get(key, {})
        display_name = profile.get("display_name") or registry_entry.get("display_name") or key
        role = (profile.get("role") or "").strip()
        tone = (profile.get("tone") or "").strip()
        notes = (profile.get("notes") or "").strip()
        tone_preset_id = (profile.get("tone_preset_id") or "").strip()
        tone_preset = CHARACTER_TONE_PRESETS.get(tone_preset_id)
        combined_tone = " / ".join(part for part in [
            tone_preset.get("tone_instruction", "") if tone_preset else "",
            tone,
        ] if part)
        combined_notes = " / ".join(part for part in [
            tone_preset.get("note_instruction", "") if tone_preset else "",
            notes,
        ] if part)

        parts = [display_name]
        if role:
            parts.append(f"role={role}")
        if tone_preset and tone_preset_id != "custom":
            parts.append(f"preset={tone_preset['name']}")
        if combined_tone:
            parts.append(f"tone={combined_tone}")
        if combined_notes:
            parts.append(f"notes={combined_notes}")
        guidance_lines.append(f"- {key}: {' | '.join(parts)}")
    return guidance_lines


def build_batch_prompts(
    item_batch: List[TranslationItem],
    world_settings: Dict[str, Any],
    character_profiles: Dict[str, Any],
    character_registry: Dict[str, Dict[str, Any]],
    include_adult_content: bool,
) -> Dict[str, str]:
    world_description = (world_settings.get("world_description") or "").strip()
    tone_notes = (world_settings.get("tone_notes") or "").strip()
    style_rules = (world_settings.get("style_rules") or "").strip()
    protected_terms = [term.strip() for term in world_settings.get("protected_terms", []) or [] if term.strip()]
    glossary_entries = normalize_glossary_entries(world_settings)
    character_guidance = build_character_guidance(item_batch, character_profiles, character_registry)

    glossary_lines = []
    for entry in glossary_entries:
        if entry["target"]:
            glossary_line = f"- {entry['source']} => {entry['target']}"
            if entry["note"]:
                glossary_line += f" ({entry['note']})"
            glossary_lines.append(glossary_line)
    protected_term_lines = [f"- {term}" for term in protected_terms]

    system_prompt = (
        "You are a specialist translator for Ren'Py visual novel scripts.\n"
        "Translate source strings into natural Korean.\n"
        "Return JSON only in the format {\"translations\":[{\"i\":\"0\",\"t\":\"...\"}]}.\n"
        "The 'i' field is the index provided in the request. The 't' field is the translated text.\n"
        "Preserve Ren'Py tags, variables, placeholders, escaped characters, tone, and speaker intent.\n"
        "Do not explain your reasoning. Do not omit any item."
    )

    payload_items = []
    for index, item in enumerate(item_batch):
        payload_items.append(
            {
                "i": str(index),
                "k": item.kind,
                "sid": item.speaker_id,
                "sn": item.speaker_name,
                "s": item.source_text,
                "adult": item.adult,
                "cb": item.context_before,
                "ca": item.context_after,
            }
        )

    user_sections = [
        "Task: Translate every item into Korean. Keep the same 'i' index for each item.",
        f"Adult content in this batch is {'allowed' if include_adult_content else 'not expected'}.",
    ]
    if world_description:
        user_sections.append(f"World setting:\n{world_description}")
    if tone_notes:
        user_sections.append(f"Global tone notes:\n{tone_notes}")
    if style_rules:
        user_sections.append(f"Formatting/style rules:\n{style_rules}")
    if protected_term_lines:
        user_sections.append("Terms to keep as-is:\n" + "\n".join(protected_term_lines))
    if glossary_lines:
        user_sections.append("Glossary:\n" + "\n".join(glossary_lines))
    if character_guidance:
        user_sections.append("Character guidance:\n" + "\n".join(character_guidance))
    user_sections.append("Items:\n" + json.dumps(payload_items, ensure_ascii=False))

    return {
        "system_prompt": system_prompt,
        "user_prompt": "\n\n".join(user_sections),
    }


def build_preview_translation_items(
    speaker_id: str,
    speaker_name: str,
    sample_lines: List[str],
) -> List[TranslationItem]:
    cleaned_lines = [line.strip() for line in sample_lines if (line or "").strip()]
    items: List[TranslationItem] = []
    for index, line in enumerate(cleaned_lines[:5]):
        adult_info = detect_adult_content(line)
        items.append(
            TranslationItem(
                item_id=f"preview_{speaker_id}_{index + 1}",
                file_relative_path="preview/character_tone.rpy",
                file_mode="preview",
                block_id=None,
                kind="dialogue",
                speaker_id=speaker_id,
                speaker_name=speaker_name,
                line_number=index + 1,
                target_line_index=index,
                source_text=line,
                current_text="",
                before="",
                after="",
                adult=adult_info["adult"],
                adult_keywords=adult_info["keywords"],
                source_preview=summarize_text(line),
                context_before=cleaned_lines[max(0, index - 2) : index],
                context_after=cleaned_lines[index + 1 : index + 3],
            )
        )
    return items


def extract_text_from_gemini_response(response: Any) -> str:
    if response is None:
        return ""
    direct_text = getattr(response, "text", None)
    if direct_text:
        return direct_text
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        if not content:
            continue
        parts = getattr(content, "parts", None) or []
        collected = [getattr(part, "text", "") for part in parts if getattr(part, "text", None)]
        text = "".join(collected).strip()
        if text:
            return text
    return ""


def extract_json_from_text(text: str) -> Dict[str, Any]:
    text = text.strip()
    if not text:
        raise ValueError("응답이 비어 있습니다.")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced_match:
        return json.loads(fenced_match.group(1))

    json_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))

    raise ValueError("JSON 응답을 파싱하지 못했습니다.")


def normalize_gemini_auth_mode(provider: str, auth_mode: Optional[str]) -> str:
    if provider != "gemini":
        return DEFAULT_GEMINI_AUTH_MODE
    if auth_mode in SUPPORTED_GEMINI_AUTH_MODES:
        return str(auth_mode)
    return DEFAULT_GEMINI_AUTH_MODE


def normalize_openai_auth_mode(provider: str, auth_mode: Optional[str]) -> str:
    if provider != "openai":
        return "api_key"
    if auth_mode in SUPPORTED_OPENAI_AUTH_MODES:
        return str(auth_mode)
    return DEFAULT_OPENAI_AUTH_MODE


def normalize_vertex_settings(value: Optional[Dict[str, Any]]) -> Dict[str, str]:
    payload = value if isinstance(value, dict) else {}
    credentials_json_value = payload.get("credentials_json") or payload.get("service_account_json") or ""
    if isinstance(credentials_json_value, dict):
        credentials_json = json.dumps(credentials_json_value, ensure_ascii=False)
    else:
        credentials_json = str(credentials_json_value or "").strip()
    project_id = str(payload.get("project_id") or payload.get("project") or "").strip()
    if not project_id and credentials_json:
        try:
            parsed_credentials = json.loads(credentials_json)
            if isinstance(parsed_credentials, dict):
                project_id = str(parsed_credentials.get("project_id") or parsed_credentials.get("project") or "").strip()
        except json.JSONDecodeError:
            pass
    return {
        "project_id": project_id,
        "location": str(payload.get("location") or DEFAULT_VERTEX_AI_LOCATION).strip() or DEFAULT_VERTEX_AI_LOCATION,
        "credentials_path": str(payload.get("credentials_path") or "").strip(),
        "credentials_json": credentials_json,
    }


def build_vertex_session_descriptor(vertex_settings: Optional[Dict[str, Any]]) -> Dict[str, str]:
    normalized = normalize_vertex_settings(vertex_settings)
    return {
        "project_id": normalized.get("project_id", ""),
        "location": normalized.get("location", DEFAULT_VERTEX_AI_LOCATION),
        "credentials_mode": (
            "json" if normalized.get("credentials_json")
            else ("path" if normalized.get("credentials_path") else "adc")
        ),
    }


def normalize_codex_command_template(command_template: Optional[str]) -> str:
    normalized = (command_template or "").strip()
    if not normalized:
        return DEFAULT_CODEX_CLI_COMMAND
    if os.name != "nt":
        return normalized

    lowered = normalized.lower()
    legacy_defaults = {
        "codex",
        "codex {args}",
        "codex.exe",
        "codex.exe {args}",
        '"codex" {args}',
        '"codex.exe" {args}',
    }
    if lowered in legacy_defaults:
        return DEFAULT_CODEX_CLI_COMMAND
    return normalized


def get_cli_command_name(base_name: str) -> str:
    if os.name == "nt":
        return f"{base_name}.cmd"
    return base_name


def check_command_version(command: str, workdir: str) -> Dict[str, Any]:
    result = run_shell_command(f"{command} --version", workdir)
    summary = (result.stdout or result.stderr or "").strip().splitlines()
    return {
        "available": result.returncode == 0,
        "command": command,
        "summary": summary[0] if summary else "",
        "detail": (result.stderr or result.stdout or "").strip(),
        "returncode": result.returncode,
    }


def inspect_global_codex_install(workdir: str) -> Dict[str, Any]:
    npm_command = get_cli_command_name("npm")
    npm_status = check_command_version(npm_command, workdir)
    if not npm_status["available"]:
        return {
            "installed": False,
            "version": "",
            "command": npm_command,
            "summary": npm_status["summary"] or "npm is not available",
            "detail": npm_status["detail"],
        }

    result = run_shell_command(f"{npm_command} list -g @openai/codex --depth=0 --json", workdir)
    payload: Dict[str, Any] = {}
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        payload = {}

    dependency = (payload.get("dependencies") or {}).get("@openai/codex") or {}
    installed = bool(dependency)
    version = str(dependency.get("version") or "")
    detail = (result.stderr or result.stdout or "").strip()
    return {
        "installed": installed,
        "version": version,
        "command": npm_command,
        "summary": version or ("@openai/codex is not installed globally"),
        "detail": detail,
    }


def install_global_codex_cli(workdir: str) -> Dict[str, Any]:
    npm_command = get_cli_command_name("npm")
    result = run_shell_command(f"{npm_command} install -g @openai/codex@latest", workdir)
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    summary = stdout.splitlines()[-1] if stdout else (stderr.splitlines()[-1] if stderr else "")
    return {
        "ok": result.returncode == 0,
        "command": npm_command,
        "summary": summary or ("Installed @openai/codex globally" if result.returncode == 0 else "npm install failed"),
        "detail": stderr or stdout,
        "returncode": result.returncode,
    }


def run_shell_command(command: str, workdir: str, input_text: Optional[str] = None) -> subprocess.CompletedProcess:
    result = subprocess.run(
        command,
        input=input_text.encode("utf-8") if input_text is not None else None,
        capture_output=True,
        shell=True,
        cwd=workdir,
    )
    return subprocess.CompletedProcess(
        args=result.args,
        returncode=result.returncode,
        stdout=decode_process_output(result.stdout),
        stderr=decode_process_output(result.stderr),
    )


def build_codex_shell_command(command_template: str, args_text: str) -> str:
    normalized_template = normalize_codex_command_template(command_template)
    if "{args}" in normalized_template:
        return normalized_template.replace("{args}", args_text)
    return f"{normalized_template} {args_text}".strip()


def check_codex_cli(command: str, workdir: str) -> Dict[str, Any]:
    normalized_command = normalize_codex_command_template(command)
    result = run_shell_command(build_codex_shell_command(normalized_command, "exec --help"), workdir)
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    available = result.returncode == 0
    summary = stdout.splitlines()[0] if stdout else (stderr.splitlines()[0] if stderr else "")
    return {
        "available": available,
        "command": normalized_command,
        "summary": summary or ("codex exec 사용 가능" if available else "codex exec 호출 실패"),
        "detail": stderr or stdout,
        "returncode": result.returncode,
    }


def check_codex_login(command: str, workdir: str) -> Dict[str, Any]:
    normalized_command = normalize_codex_command_template(command)
    result = run_shell_command(build_codex_shell_command(normalized_command, "login status"), workdir)
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    summary = stdout.splitlines()[0] if stdout else (stderr.splitlines()[0] if stderr else "")
    lowered = f"{stdout}\n{stderr}".lower()
    logged_in = result.returncode == 0 and "logged in" in lowered and "not logged" not in lowered
    return {
        "logged_in": logged_in,
        "command": normalized_command,
        "summary": summary or ("Logged in" if logged_in else "Login required"),
        "detail": stderr or stdout,
        "returncode": result.returncode,
    }


def launch_codex_login(command: str, workdir: str) -> Dict[str, Any]:
    normalized_command = normalize_codex_command_template(command)
    login_command = build_codex_shell_command(normalized_command, "login --device-auth")
    creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if os.name == "nt" else 0
    process = subprocess.Popen(
        login_command,
        shell=True,
        cwd=workdir,
        creationflags=creationflags,
    )
    return {
        "started": True,
        "command": normalized_command,
        "pid": process.pid,
        "summary": "Started Codex device-auth login flow",
    }


def inspect_openai_oauth_environment(command: str, workdir: str) -> Dict[str, Any]:
    normalized_command = normalize_codex_command_template(command)
    npm_status = check_command_version(get_cli_command_name("npm"), workdir)
    npx_status = check_command_version(get_cli_command_name("npx"), workdir)
    global_install = inspect_global_codex_install(workdir)
    cli_status = check_codex_cli(normalized_command, workdir) if npx_status["available"] else {
        "available": False,
        "command": normalized_command,
        "summary": "npx is not available",
        "detail": npx_status["detail"],
        "returncode": npx_status["returncode"],
    }
    login_status = check_codex_login(normalized_command, workdir) if cli_status["available"] else {
        "logged_in": False,
        "command": normalized_command,
        "summary": "Codex CLI is not ready",
        "detail": cli_status["detail"],
        "returncode": cli_status["returncode"],
    }
    return {
        "command": normalized_command,
        "npm": npm_status,
        "npx": npx_status,
        "global_install": global_install,
        "cli": cli_status,
        "login": login_status,
        "ready": bool(cli_status["available"] and login_status["logged_in"]),
    }


def ensure_openai_oauth_ready(command: str, workdir: str, install_if_missing: bool, launch_login_flow: bool) -> Dict[str, Any]:
    status = inspect_openai_oauth_environment(command, workdir)
    install_result: Optional[Dict[str, Any]] = None
    login_launch: Optional[Dict[str, Any]] = None

    if install_if_missing and status["npm"]["available"] and not status["global_install"]["installed"]:
        install_result = install_global_codex_cli(workdir)
        if install_result["ok"]:
            status = inspect_openai_oauth_environment(command, workdir)
        else:
            status["install_result"] = install_result
            status["message"] = install_result["summary"]
            return status

    if launch_login_flow and status["cli"]["available"] and not status["login"]["logged_in"]:
        login_launch = launch_codex_login(command, workdir)
        status["login"] = {
            **status["login"],
            "summary": "Device-auth login window opened",
        }

    status["install_result"] = install_result
    status["login_launch"] = login_launch
    status["ready"] = bool(status["cli"]["available"] and status["login"]["logged_in"])
    if status["ready"]:
        status["message"] = "Codex CLI is installed, logged in, and ready."
    elif login_launch:
        status["message"] = "Codex login window opened. Complete ChatGPT OAuth in the new terminal."
    elif install_result and install_result["ok"]:
        status["message"] = "Codex CLI installation completed."
    else:
        status["message"] = status["login"]["summary"] or status["cli"]["summary"]
    return status


def summarize_codex_cli_failure(detail: str) -> str:
    lines = [line.strip() for line in (detail or "").splitlines() if line.strip()]
    if not lines:
        return "Codex CLI execution failed."

    for pattern in ("Unsupported value:", '"code": "unsupported_value"', "invalid_request_error", "ERROR:"):
        for line in reversed(lines):
            if pattern in line:
                return line

    for line in reversed(lines):
        lowered = line.lower()
        if not lowered.startswith("warn ") and "mcp:" not in lowered:
            return line
    return lines[-1]


def write_text_artifact(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content or "", encoding="utf-8")


def write_json_artifact(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json_artifact(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def build_translation_session_id(
    documents: List[AnalyzedFile],
    provider: str,
    gemini_auth_mode: str,
    vertex_descriptor: Dict[str, str],
    openai_auth_mode: str,
    model_name: str,
    analysis_mode: str,
    target_language: str,
    include_adult_content: bool,
    world_settings: Dict[str, Any],
    character_profiles: Dict[str, Any],
    translation_scope: Optional[Dict[str, Any]] = None,
) -> str:
    descriptor = {
        "provider": provider,
        "gemini_auth_mode": gemini_auth_mode,
        "vertex_descriptor": vertex_descriptor,
        "openai_auth_mode": openai_auth_mode,
        "model_name": model_name,
        "analysis_mode": analysis_mode,
        "target_language": target_language,
        "include_adult_content": include_adult_content,
        "world_settings": world_settings,
        "character_profiles": character_profiles,
        "translation_scope": translation_scope or {"mode": "all_items", "selected_speaker_ids": []},
        "files": [
            {
                "file_relative_path": document.file_relative_path,
                "item_count": len(document.items),
                "first_item_id": document.items[0].item_id if document.items else None,
                "last_item_id": document.items[-1].item_id if document.items else None,
            }
            for document in documents
        ],
    }
    raw = json.dumps(descriptor, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def build_translation_session_runtime(
    documents: List[AnalyzedFile],
    provider: str,
    gemini_auth_mode: str,
    vertex_settings: Dict[str, str],
    openai_auth_mode: str,
    model_name: str,
    analysis_mode: str,
    target_language: str,
    include_adult_content: bool,
    world_settings: Dict[str, Any],
    character_profiles: Dict[str, Any],
    game_dir: Optional[str],
    translation_scope: Optional[Dict[str, Any]] = None,
) -> TranslationSessionRuntime:
    session_id = build_translation_session_id(
        documents=documents,
        provider=provider,
        gemini_auth_mode=gemini_auth_mode,
        vertex_descriptor=build_vertex_session_descriptor(vertex_settings),
        openai_auth_mode=openai_auth_mode,
        model_name=model_name,
        analysis_mode=analysis_mode,
        target_language=target_language,
        include_adult_content=include_adult_content,
        world_settings=world_settings,
        character_profiles=character_profiles,
        translation_scope=translation_scope,
    )
    if game_dir:
        session_dir = Path(game_dir) / TRANSLATION_LOG_DIRNAME / analysis_mode / target_language / session_id
        runtime_game_dir = Path(game_dir)
    else:
        session_dir = UPLOADED_TRANSLATION_RUN_ROOT / analysis_mode / target_language / session_id
        runtime_game_dir = None
    attempts_dir = session_dir / "attempts"
    attempts_dir.mkdir(parents=True, exist_ok=True)
    return TranslationSessionRuntime(
        session_id=session_id,
        session_dir=session_dir,
        attempts_dir=attempts_dir,
        checkpoint_path=session_dir / "checkpoint.json",
        status_path=session_dir / "status.json",
        metadata_path=session_dir / "session.json",
        game_dir=runtime_game_dir,
        analysis_mode=analysis_mode,
        target_language=target_language,
    )


def load_translation_checkpoint(runtime: TranslationSessionRuntime) -> Dict[str, str]:
    if not runtime.checkpoint_path.is_file():
        return {}
    try:
        payload = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    translated_lookup = payload.get("translated_lookup")
    if not isinstance(translated_lookup, dict):
        return {}
    return {
        str(item_id): text
        for item_id, text in translated_lookup.items()
        if isinstance(item_id, str) and isinstance(text, str)
    }


def load_compatible_translation_checkpoint(
    runtime: TranslationSessionRuntime,
    documents: List[AnalyzedFile],
    provider: str,
    gemini_auth_mode: str,
    vertex_descriptor: Dict[str, str],
    openai_auth_mode: str,
) -> Dict[str, str]:
    direct_checkpoint = load_translation_checkpoint(runtime)
    if direct_checkpoint:
        return direct_checkpoint

    parent_dir = runtime.session_dir.parent
    if not parent_dir.is_dir():
        return {}

    expected_documents = sorted(document.file_relative_path for document in documents)
    best_lookup: Dict[str, str] = {}
    best_score: Tuple[int, str] = (0, "")

    for candidate_dir in parent_dir.iterdir():
        if not candidate_dir.is_dir() or candidate_dir == runtime.session_dir:
            continue
        session_path = candidate_dir / "session.json"
        checkpoint_path = candidate_dir / "checkpoint.json"
        if not session_path.is_file() or not checkpoint_path.is_file():
            continue
        try:
            session_payload = json.loads(session_path.read_text(encoding="utf-8"))
            checkpoint_payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue

        if session_payload.get("provider") != provider:
            continue
        if session_payload.get("gemini_auth_mode") != gemini_auth_mode:
            continue
        if (session_payload.get("vertex_descriptor") or {}) != vertex_descriptor:
            continue
        if session_payload.get("openai_auth_mode") != openai_auth_mode:
            continue
        if session_payload.get("analysis_mode") != runtime.analysis_mode:
            continue
        if session_payload.get("target_language") != runtime.target_language:
            continue
        if sorted(session_payload.get("documents") or []) != expected_documents:
            continue

        translated_lookup = checkpoint_payload.get("translated_lookup")
        if not isinstance(translated_lookup, dict):
            continue
        normalized_lookup = {
            str(item_id): text
            for item_id, text in translated_lookup.items()
            if isinstance(item_id, str) and isinstance(text, str)
        }
        updated_at = str(checkpoint_payload.get("updated_at") or session_payload.get("updated_at") or "")
        score = (len(normalized_lookup), updated_at)
        if score > best_score:
            best_lookup = normalized_lookup
            best_score = score

    return best_lookup


def persist_translation_session_state(
    runtime: TranslationSessionRuntime,
    *,
    translated_lookup: Dict[str, str],
    total_items: int,
    skipped_adult_items: List[Dict[str, Any]],
    failed_items: List[Dict[str, Any]],
    completed_batches: List[Dict[str, Any]],
    failed_batches: List[Dict[str, Any]],
    resumed_item_count: int,
    last_error: str = "",
    completed_documents: Optional[List[Dict[str, Any]]] = None,
    current_document: str = "",
    halted: bool = False,
    halt_reason: str = "",
    passthrough_item_count: int = 0,
    optimization: Optional[Dict[str, Any]] = None,
) -> None:
    failed_item_ids = {
        item.get("item_id")
        for item in failed_items
        if isinstance(item, dict) and item.get("item_id")
    }
    status_payload = {
        "session_id": runtime.session_id,
        "updated_at": datetime.datetime.now().isoformat(),
        "total_item_count": total_items,
        "translated_item_count": len(translated_lookup),
        "resumed_item_count": resumed_item_count,
        "failed_item_count": len(failed_items),
        "failed_batch_count": len(failed_batches),
        "completed_batch_count": len(completed_batches),
        "skipped_adult_count": len(skipped_adult_items),
        "passthrough_item_count": passthrough_item_count,
        "pending_item_count": max(
            0,
            total_items - len(translated_lookup) - len(skipped_adult_items) - len(failed_item_ids),
        ),
        "checkpoint_path": str(runtime.checkpoint_path),
        "attempt_log_dir": str(runtime.attempts_dir),
        "last_error": last_error,
        "halted": halted,
        "halt_reason": halt_reason,
        "current_document": current_document,
        "completed_documents": completed_documents or [],
        "optimization": optimization or {},
        "completed_batches": completed_batches,
        "failed_batches": failed_batches,
    }
    checkpoint_payload = {
        "session_id": runtime.session_id,
        "updated_at": status_payload["updated_at"],
        "translated_lookup": translated_lookup,
        "status": status_payload,
    }
    write_json_artifact(runtime.checkpoint_path, checkpoint_payload)
    write_json_artifact(runtime.status_path, status_payload)


def build_translation_status_payload(runtime: TranslationSessionRuntime) -> Dict[str, Any]:
    session_payload = read_json_artifact(runtime.metadata_path)
    status_payload = read_json_artifact(runtime.status_path)

    total_item_count = try_parse_int(status_payload.get("total_item_count"))
    if total_item_count is None:
        total_item_count = try_parse_int(session_payload.get("total_items")) or 0

    translated_item_count = try_parse_int(status_payload.get("translated_item_count")) or 0
    failed_item_count = try_parse_int(status_payload.get("failed_item_count")) or 0
    skipped_adult_count = try_parse_int(status_payload.get("skipped_adult_count")) or 0
    pending_item_count = try_parse_int(status_payload.get("pending_item_count"))
    if pending_item_count is None:
        pending_item_count = max(
            0,
            total_item_count - translated_item_count - failed_item_count - skipped_adult_count,
        )
    completed_item_count = max(
        0,
        min(total_item_count, translated_item_count + failed_item_count + skipped_adult_count),
    )
    progress_percent = round((completed_item_count / total_item_count) * 100, 2) if total_item_count > 0 else 0.0

    updated_at = str(status_payload.get("updated_at") or session_payload.get("updated_at") or "")
    stale_seconds = None
    if updated_at:
        try:
            updated_dt = datetime.datetime.fromisoformat(updated_at)
            stale_seconds = max(0.0, (datetime.datetime.now() - updated_dt).total_seconds())
        except ValueError:
            stale_seconds = None

    latest_attempt = {}
    latest_attempt_name = ""
    completed_batches = status_payload.get("completed_batches") or []
    if isinstance(completed_batches, list) and completed_batches:
        latest_batch = completed_batches[-1]
        if isinstance(latest_batch, dict):
            latest_attempt = latest_batch
            latest_attempt_name = str(latest_batch.get("log_dir") or "").replace("\\", "/").rstrip("/").split("/")[-1]
    if not latest_attempt and runtime.attempts_dir.is_dir():
        attempt_dirs = sorted(
            [child for child in runtime.attempts_dir.iterdir() if child.is_dir() and child.name.startswith("attempt_")],
            key=lambda child: child.name,
        )
        if attempt_dirs:
            latest_attempt_dir = attempt_dirs[-1]
            latest_attempt = read_json_artifact(latest_attempt_dir / "meta.json")
            latest_attempt_name = latest_attempt_dir.name

    current_document = str(status_payload.get("current_document") or "")
    completed_document_count = len(status_payload.get("completed_documents") or [])
    halted = bool(status_payload.get("halted"))
    last_error = str(status_payload.get("last_error") or "")
    if latest_attempt.get("document_path") and not current_document:
        current_document = str(latest_attempt.get("document_path") or "")

    return {
        "session_id": runtime.session_id,
        "status_path": str(runtime.status_path),
        "checkpoint_path": str(runtime.checkpoint_path),
        "attempt_log_dir": str(runtime.attempts_dir),
        "metadata_path": str(runtime.metadata_path),
        "analysis_mode": runtime.analysis_mode,
        "target_language": runtime.target_language,
        "updated_at": updated_at,
        "stale_seconds": stale_seconds,
        "halted": halted,
        "halt_reason": str(status_payload.get("halt_reason") or ""),
        "last_error": last_error,
        "current_document": current_document,
        "total_item_count": total_item_count,
        "translated_item_count": translated_item_count,
        "failed_item_count": failed_item_count,
        "skipped_adult_count": skipped_adult_count,
        "pending_item_count": pending_item_count,
        "completed_item_count": completed_item_count,
        "completed_batch_count": try_parse_int(status_payload.get("completed_batch_count")) or 0,
        "failed_batch_count": try_parse_int(status_payload.get("failed_batch_count")) or 0,
        "completed_document_count": completed_document_count,
        "resumed_item_count": try_parse_int(status_payload.get("resumed_item_count")) or 0,
        "passthrough_item_count": try_parse_int(status_payload.get("passthrough_item_count")) or 0,
        "progress_percent": progress_percent,
        "latest_attempt_name": latest_attempt_name,
        "latest_attempt": latest_attempt,
        "optimization": status_payload.get("optimization") or session_payload.get("optimization") or {},
        "has_status": runtime.status_path.is_file(),
    }


def begin_translation_attempt_log(
    runtime: TranslationSessionRuntime,
    attempt_index: int,
    metadata: Dict[str, Any],
    system_prompt: str,
    user_prompt: str,
) -> Path:
    attempt_dir = runtime.attempts_dir / f"attempt_{attempt_index:04d}"
    attempt_dir.mkdir(parents=True, exist_ok=True)
    write_json_artifact(attempt_dir / "meta.json", metadata)
    if system_prompt:
        write_text_artifact(attempt_dir / "system_prompt.txt", system_prompt)
    if user_prompt:
        write_text_artifact(attempt_dir / "user_prompt.txt", user_prompt)
    return attempt_dir


def finalize_translation_attempt_log(
    attempt_dir: Path,
    *,
    metadata: Optional[Dict[str, Any]] = None,
    response_payload: Optional[Dict[str, Any]] = None,
    error_text: str = "",
) -> None:
    if metadata is not None:
        write_json_artifact(attempt_dir / "meta.json", metadata)
    if response_payload is not None:
        write_json_artifact(attempt_dir / "response_payload.json", response_payload)
    if error_text:
        write_text_artifact(attempt_dir / "error.txt", error_text)


def split_translation_batch(batch: List[TranslationItem]) -> List[List[TranslationItem]]:
    if len(batch) <= 1:
        return [batch]
    midpoint = max(1, len(batch) // 2)
    return [batch[:midpoint], batch[midpoint:]]


def translate_with_codex_cli(
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    cli_command: str,
    workdir: str,
    debug_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    schema = {
        "type": "object",
        "properties": {
            "translations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "i": {"type": "string"},
                        "t": {"type": "string"},
                    },
                    "required": ["i", "t"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["translations"],
        "additionalProperties": False,
    }
    prompt = (
        "You are running inside Codex CLI in non-interactive mode.\n"
        "Follow the system instructions and return only a JSON object that matches the schema.\n\n"
        f"[SYSTEM]\n{system_prompt}\n\n"
        f"[USER]\n{user_prompt}\n"
    )

    with tempfile.TemporaryDirectory(prefix="codex_oauth_translate_") as temp_dir:
        temp_path = Path(temp_dir)
        schema_path = temp_path / "schema.json"
        output_path = temp_path / "response.json"
        schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

        normalized_command = normalize_codex_command_template(cli_command)
        effective_model = model_name or DEFAULT_CODEX_OAUTH_MODEL
        command = build_codex_shell_command(
            normalized_command,
            (
                'exec --skip-git-repo-check --sandbox workspace-write '
                f'-c model_reasoning_effort="{DEFAULT_CODEX_REASONING_EFFORT}" '
                f'--model "{effective_model}" --output-schema "{schema_path}" -o "{output_path}" -'
            ),
        )
        if debug_dir:
            write_text_artifact(debug_dir / "codex_command.txt", command)
            write_json_artifact(
                debug_dir / "codex_meta.json",
                {
                    "model": effective_model,
                    "command_template": normalized_command,
                    "workdir": workdir,
                    "schema_path": str(schema_path),
                    "output_path": str(output_path),
                },
            )
        result = run_shell_command(command, workdir, input_text=prompt)
        if debug_dir:
            write_text_artifact(debug_dir / "codex_stdout.txt", result.stdout or "")
            write_text_artifact(debug_dir / "codex_stderr.txt", result.stderr or "")
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            summary = summarize_codex_cli_failure(detail) or f"Codex CLI execution failed (exit={result.returncode})"
            if debug_dir:
                write_text_artifact(debug_dir / "codex_error.txt", detail)
            raise RuntimeError(f"{summary} [log: {debug_dir}]" if debug_dir else summary)

        raw_text = output_path.read_text(encoding="utf-8") if output_path.is_file() else ""
        if not raw_text.strip():
            raw_text = (result.stdout or "").strip()
        if debug_dir:
            write_text_artifact(debug_dir / "codex_raw_response.txt", raw_text)
        parsed = extract_json_from_text(raw_text)
        if debug_dir:
            write_json_artifact(debug_dir / "codex_parsed_response.json", parsed)
        return parsed


def translate_with_gemini(api_key: str, model_name: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=model_name)
    last_error = None
    for attempt in range(1, GEMINI_MAX_API_RETRIES + 1):
        try:
            response = model.generate_content(
                [system_prompt, user_prompt],
                generation_config={"temperature": TRANSLATION_TEMPERATURE},
            )
            return extract_json_from_text(extract_text_from_gemini_response(response))
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            error_text = str(exc)
            if any(pattern in error_text.lower() for pattern in GEMINI_HARD_FAILURE_PATTERNS):
                raise
            if google_exceptions and isinstance(exc, google_exceptions.ResourceExhausted):
                if attempt >= GEMINI_MAX_API_RETRIES:
                    raise
                time.sleep(1.5 * attempt)
                continue
            if attempt >= GEMINI_MAX_API_RETRIES:
                raise
            time.sleep(0.8 * attempt)
    raise last_error  # pragma: no cover


def extract_text_from_google_genai_sdk_response(response: Any) -> str:
    text = getattr(response, "text", None)
    if text:
        return text

    fragments: List[str] = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                fragments.append(part_text)
    return "".join(fragments)


def translate_with_vertex_gemini(
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    vertex_settings: Dict[str, str],
) -> Dict[str, Any]:
    if google_genai is None or google_genai_types is None:
        raise RuntimeError("google-genai 라이브러리를 사용할 수 없습니다.")

    project_id = (vertex_settings.get("project_id") or "").strip()
    location = (vertex_settings.get("location") or DEFAULT_VERTEX_AI_LOCATION).strip() or DEFAULT_VERTEX_AI_LOCATION
    credentials_path = (vertex_settings.get("credentials_path") or "").strip()
    credentials_json = (vertex_settings.get("credentials_json") or "").strip()
    if not project_id:
        raise RuntimeError("Vertex AI를 사용하려면 GCP 프로젝트 ID가 필요합니다.")

    client_kwargs: Dict[str, Any] = {
        "vertexai": True,
        "project": project_id,
        "location": location,
        "http_options": google_genai_types.HttpOptions(api_version="v1"),
    }
    if credentials_json:
        if service_account is None:
            raise RuntimeError("google-auth 서비스 계정 라이브러리를 사용할 수 없습니다.")
        try:
            credentials_info = json.loads(credentials_json)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Vertex AI 서비스 계정 JSON을 해석할 수 없습니다: {error}") from error
        if not isinstance(credentials_info, dict):
            raise RuntimeError("Vertex AI 서비스 계정 JSON은 객체 형식이어야 합니다.")
        client_kwargs["credentials"] = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
    elif credentials_path:
        if service_account is None:
            raise RuntimeError("google-auth 서비스 계정 라이브러리를 사용할 수 없습니다.")
        credentials_file = Path(credentials_path)
        if not credentials_file.is_file():
            raise RuntimeError(f"Vertex AI 서비스 계정 JSON을 찾을 수 없습니다: {credentials_path}")
        client_kwargs["credentials"] = service_account.Credentials.from_service_account_file(
            str(credentials_file),
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

    client = google_genai.Client(**client_kwargs)
    response = client.models.generate_content(
        model=model_name,
        contents=[system_prompt, user_prompt],
        config=google_genai_types.GenerateContentConfig(
            temperature=TRANSLATION_TEMPERATURE,
        ),
    )
    return extract_json_from_text(extract_text_from_google_genai_sdk_response(response))


def translate_with_openai(api_key: str, model_name: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    if OpenAI is None:
        raise RuntimeError("openai 라이브러리를 사용할 수 없습니다.")
    client = OpenAI(api_key=api_key)
    last_error = None
    for attempt in range(1, OPENAI_MAX_API_RETRIES + 1):
        try:
            response = client.responses.create(
                model=model_name,
                input=[
                    {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                    {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
                ],
                temperature=TRANSLATION_TEMPERATURE,
            )
            text = getattr(response, "output_text", None)
            if not text:
                fragments = []
                for item in getattr(response, "output", []) or []:
                    for content in getattr(item, "content", []) or []:
                        content_text = getattr(content, "text", None)
                        if content_text:
                            fragments.append(content_text)
                text = "".join(fragments)
            return extract_json_from_text(text or "")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= OPENAI_MAX_API_RETRIES:
                raise
            time.sleep(1.0 * attempt)
    raise last_error  # pragma: no cover


def perform_translation(
    provider: str,
    api_key: str,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    gemini_auth_mode: str = DEFAULT_GEMINI_AUTH_MODE,
    vertex_settings: Optional[Dict[str, str]] = None,
    openai_auth_mode: str = DEFAULT_OPENAI_AUTH_MODE,
    openai_oauth_command: str = DEFAULT_CODEX_CLI_COMMAND,
    workdir: Optional[str] = None,
    debug_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    if provider == "gemini":
        if gemini_auth_mode == "vertex_ai":
            return translate_with_vertex_gemini(
                model_name=model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                vertex_settings=normalize_vertex_settings(vertex_settings),
            )
        return translate_with_gemini(api_key, model_name, system_prompt, user_prompt)
    if provider == "openai":
        if openai_auth_mode == "oauth_cli":
            return translate_with_codex_cli(
                model_name=model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                cli_command=openai_oauth_command,
                workdir=workdir or os.getcwd(),
                debug_dir=debug_dir,
            )
        return translate_with_openai(api_key, model_name, system_prompt, user_prompt)
    raise ValueError(f"지원하지 않는 공급자입니다: {provider}")


def build_translation_lookup_from_response(
    response_payload: Optional[Dict[str, Any]],
    item_batch: List[TranslationItem],
) -> Dict[str, str]:
    translations = (response_payload or {}).get("translations")
    if not isinstance(translations, list):
        return {}

    id_map = {str(index): item.item_id for index, item in enumerate(item_batch)}
    lookup: Dict[str, str] = {}
    for entry in translations:
        if not isinstance(entry, dict):
            continue

        item_id = entry.get("id")
        text = entry.get("text")
        if isinstance(item_id, str) and isinstance(text, str) and item_id:
            lookup[item_id] = text
            continue

        raw_index = entry.get("i")
        indexed_text = entry.get("t")
        if raw_index is None or not isinstance(indexed_text, str):
            continue

        resolved_item_id = id_map.get(str(raw_index))
        if resolved_item_id:
            lookup[resolved_item_id] = indexed_text
    return lookup


def chunk_items(items: List[TranslationItem], batch_size: int) -> List[List[TranslationItem]]:
    size = max(1, int(batch_size or 1))
    return [items[index : index + size] for index in range(0, len(items), size)]


def estimate_translation_item_budget(item: TranslationItem) -> int:
    context_before = "".join(item.context_before or [])
    context_after = "".join(item.context_after or [])
    return len(item.source_text or "") + len(context_before) + len(context_after) + 48


def chunk_items_by_budget(items: List[TranslationItem], item_limit: int, char_limit: int) -> List[List[TranslationItem]]:
    if not items:
        return []

    effective_item_limit = max(1, int(item_limit or 1))
    effective_char_limit = max(2000, int(char_limit or 2000))
    batches: List[List[TranslationItem]] = []
    current_batch: List[TranslationItem] = []
    current_chars = 0

    for item in items:
        item_size = estimate_translation_item_budget(item)
        should_flush = (
            current_batch
            and (
                len(current_batch) >= effective_item_limit
                or current_chars + item_size > effective_char_limit
                or current_batch[-1].file_relative_path != item.file_relative_path
            )
        )
        if should_flush:
            batches.append(current_batch)
            current_batch = []
            current_chars = 0

        current_batch.append(item)
        current_chars += item_size

    if current_batch:
        batches.append(current_batch)
    return batches


def classify_translation_batch(item_batch: List[TranslationItem]) -> Dict[str, Any]:
    if not item_batch:
        return {
            "avg_chars": 0,
            "max_chars": 0,
            "speaker_count": 0,
            "kind_counts": {},
            "story_heavy": False,
            "ui_heavy": True,
            "complex": False,
        }

    char_lengths = [len((item.source_text or "").strip()) for item in item_batch]
    avg_chars = sum(char_lengths) / max(1, len(char_lengths))
    max_chars = max(char_lengths) if char_lengths else 0
    speaker_ids = {item.speaker_id or DEFAULT_FALLBACK_PERSONA_KEY for item in item_batch}
    kind_counts: Dict[str, int] = {}
    for item in item_batch:
        kind = item.kind or "string"
        kind_counts[kind] = kind_counts.get(kind, 0) + 1

    story_heavy = any(
        item.kind in {"dialogue", "narration", "menu"} or (item.speaker_id not in {None, DEFAULT_FALLBACK_PERSONA_KEY})
        for item in item_batch
    )
    ui_heavy = (
        not story_heavy
        and all((item.kind or "string") == "string" for item in item_batch)
        and avg_chars <= 52
        and max_chars <= 120
    )
    complex_batch = bool(
        max_chars >= 220
        or avg_chars >= 120
        or len(speaker_ids) >= 3
        or any(item.adult for item in item_batch)
        or kind_counts.get("narration", 0) >= max(2, len(item_batch) // 2)
    )
    return {
        "avg_chars": round(avg_chars, 2),
        "max_chars": max_chars,
        "speaker_count": len(speaker_ids),
        "kind_counts": kind_counts,
        "story_heavy": story_heavy,
        "ui_heavy": ui_heavy,
        "complex": complex_batch,
    }


def is_passthrough_translation_item(item: TranslationItem) -> bool:
    source_text = (item.source_text or "").strip()
    if not source_text:
        return True
    if PASSTHROUGH_OLD_MARKER_RE.fullmatch(source_text):
        return True
    if PASSTHROUGH_FILENAME_RE.fullmatch(source_text) and " " not in source_text:
        return True
    return False


def is_non_retryable_translation_error(error_text: str) -> bool:
    lowered = (error_text or "").lower()
    return any(pattern in lowered for pattern in NON_RETRYABLE_TRANSLATION_ERROR_PATTERNS)


def is_unsupported_model_error(error_text: str) -> bool:
    lowered = (error_text or "").lower()
    return any(pattern in lowered for pattern in UNSUPPORTED_MODEL_ERROR_PATTERNS)


def normalize_codex_oauth_requested_model(model_name: str) -> Tuple[str, str]:
    normalized_model = (model_name or DEFAULT_CODEX_OAUTH_MODEL).strip() or DEFAULT_CODEX_OAUTH_MODEL
    if normalized_model in SUPPORTED_CODEX_OAUTH_MODELS:
        return normalized_model, ""

    lowered = normalized_model.lower()
    if lowered.startswith(CHATGPT_UNSUPPORTED_CODEX_MODEL_PREFIXES):
        fallback_model = "gpt-5.1-codex"
        warning = (
            f"The '{normalized_model}' model is not supported when using Codex with a ChatGPT account. "
            f"Falling back to '{fallback_model}'."
        )
        return fallback_model, warning

    warning = (
        f"The '{normalized_model}' model is not supported by Codex OAuth in this app. "
        f"Falling back to '{DEFAULT_CODEX_OAUTH_MODEL}'."
    )
    return DEFAULT_CODEX_OAUTH_MODEL, warning


def choose_codex_oauth_model(
    requested_model: str,
    item_batch: List[TranslationItem],
    depth: int,
    unsupported_models: Set[str],
) -> Tuple[str, str]:
    normalized_model, _ = normalize_codex_oauth_requested_model(requested_model)
    batch_profile = classify_translation_batch(item_batch)
    if normalized_model not in {AUTO_CODEX_MODEL_ECONOMY, AUTO_CODEX_MODEL_BALANCED}:
        return normalized_model, "manual"

    simple_candidate = "gpt-5-mini"
    strong_candidate = "gpt-5.1-codex"
    if depth > 0 or batch_profile["complex"]:
        preferred = strong_candidate
        strategy = "auto-strong"
    elif normalized_model == AUTO_CODEX_MODEL_BALANCED:
        preferred = strong_candidate if batch_profile["story_heavy"] else simple_candidate
        strategy = "auto-balanced"
    else:
        preferred = simple_candidate
        strategy = "auto-economy"

    if preferred in unsupported_models:
        preferred = strong_candidate
        strategy += "-fallback"
    return preferred, strategy


def build_oauth_chunk_plan(items: List[TranslationItem], batch_size_cap: int) -> Dict[str, Any]:
    effective_cap = max(1, int(batch_size_cap or 1))
    profile = classify_translation_batch(items)
    if profile["ui_heavy"]:
        item_limit = min(CODEX_OAUTH_ITEM_LIMIT, max(effective_cap, 24), CODEX_OAUTH_UI_ITEM_LIMIT)
        char_limit = CODEX_OAUTH_UI_CHAR_LIMIT
        strategy = "ui-large"
    elif profile["complex"]:
        item_limit = min(CODEX_OAUTH_ITEM_LIMIT, min(effective_cap, CODEX_OAUTH_COMPLEX_ITEM_LIMIT))
        char_limit = CODEX_OAUTH_COMPLEX_CHAR_LIMIT
        strategy = "story-tight"
    else:
        item_limit = min(CODEX_OAUTH_ITEM_LIMIT, max(min(effective_cap, CODEX_OAUTH_STORY_ITEM_LIMIT), 10))
        char_limit = CODEX_OAUTH_STORY_CHAR_LIMIT
        strategy = "story-balanced"

    return {
        "item_limit": max(1, item_limit),
        "char_limit": min(CODEX_OAUTH_CHAR_LIMIT, max(2000, char_limit)),
        "strategy": strategy,
        "profile": profile,
    }


def build_gemini_chunk_plan(items: List[TranslationItem], batch_size_cap: int) -> Dict[str, Any]:
    effective_cap = max(1, int(batch_size_cap or 1))
    profile = classify_translation_batch(items)
    if profile["ui_heavy"]:
        strategy = "char-ui"
        base_char_limit = GEMINI_UI_CHAR_LIMIT
    elif profile["complex"]:
        strategy = "char-tight"
        base_char_limit = GEMINI_COMPLEX_CHAR_LIMIT
    else:
        strategy = "char-balanced"
        base_char_limit = GEMINI_STORY_CHAR_LIMIT
    char_scale = max(0.55, min(1.35, effective_cap / 16))
    char_limit = int(base_char_limit * char_scale)

    return {
        "item_limit": effective_cap,
        "char_limit": max(2000, char_limit),
        "strategy": strategy,
        "profile": profile,
    }


def get_document_pending_items(
    document: AnalyzedFile,
    translated_lookup: Dict[str, str],
    include_adult_content: bool,
) -> List[TranslationItem]:
    pending_items: List[TranslationItem] = []
    for item in document.items:
        if item.item_id in translated_lookup:
            continue
        if item.adult and not include_adult_content:
            continue
        pending_items.append(item)
    return pending_items


def is_document_translation_complete(
    document: AnalyzedFile,
    translated_lookup: Dict[str, str],
    include_adult_content: bool,
) -> bool:
    return not get_document_pending_items(document, translated_lookup, include_adult_content)


def order_documents_for_translation(
    documents: List[AnalyzedFile],
    translated_lookup: Dict[str, str],
    include_adult_content: bool,
) -> List[AnalyzedFile]:
    def document_sort_key(document: AnalyzedFile) -> Tuple[int, int, str]:
        pending_items = get_document_pending_items(document, translated_lookup, include_adult_content)
        if not pending_items:
            return (0, 0, document.file_relative_path)
        profile = classify_translation_batch(pending_items[: min(len(pending_items), 24)])
        priority = 0 if profile["ui_heavy"] else 1
        char_weight = sum(len((item.source_text or "").strip()) for item in pending_items)
        return (priority, len(pending_items) * 1000 + char_weight, document.file_relative_path)

    return sorted(documents, key=document_sort_key)


def translate_documents(
    documents: List[AnalyzedFile],
    provider: str,
    api_key: str,
    model_name: str,
    gemini_auth_mode: str,
    vertex_settings: Dict[str, str],
    character_profiles: Dict[str, Any],
    world_settings: Dict[str, Any],
    character_registry: Dict[str, Dict[str, Any]],
    batch_size: int,
    api_delay: float,
    include_adult_content: bool,
    openai_auth_mode: str = DEFAULT_OPENAI_AUTH_MODE,
    openai_oauth_command: str = DEFAULT_CODEX_CLI_COMMAND,
    workdir: Optional[str] = None,
    runtime: Optional[TranslationSessionRuntime] = None,
    document_write_callback: Optional[Callable[[AnalyzedFile, Dict[str, str], List[Dict[str, Any]], List[Dict[str, Any]]], Dict[str, Any]]] = None,
    translation_scope: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    translated_lookup: Dict[str, str] = (
        load_compatible_translation_checkpoint(
            runtime,
            documents,
            provider,
            gemini_auth_mode,
            build_vertex_session_descriptor(vertex_settings),
            openai_auth_mode,
        )
        if runtime
        else {}
    )
    translation_scope = translation_scope or {"mode": "all_items", "selected_speaker_ids": []}
    if translation_scope.get("force_retranslate"):
        target_item_ids = {
            item.item_id
            for document in documents
            for item in document.items
        }
        for item_id in target_item_ids:
            translated_lookup.pop(item_id, None)
    resumed_item_count = len(translated_lookup)
    skipped_adult_items: List[Dict[str, Any]] = []
    failed_items: List[Dict[str, Any]] = []
    completed_batches: List[Dict[str, Any]] = []
    failed_batches: List[Dict[str, Any]] = []
    completed_document_lookup: Dict[str, Dict[str, Any]] = {}
    unsupported_oauth_models: Set[str] = set()
    halted = False
    halt_reason = ""
    current_document = ""
    passthrough_item_count = 0

    translatable_items = []
    for document in documents:
        for item in document.items:
            if item.adult and not include_adult_content:
                skipped_adult_items.append(item.to_public_dict())
                continue
            translatable_items.append(item)
            if is_passthrough_translation_item(item):
                if translated_lookup.get(item.item_id) != item.source_text:
                    translated_lookup[item.item_id] = item.source_text
                    passthrough_item_count += 1
                continue

    total_items = len(translatable_items)
    ordered_documents = order_documents_for_translation(documents, translated_lookup, include_adult_content)
    optimization_summary = {
        "requested_model": model_name,
        "provider": provider,
        "openai_auth_mode": openai_auth_mode,
        "batch_size_cap": max(1, int(batch_size or 1)),
        "effective_api_delay": 0 if provider == "openai" and openai_auth_mode == "oauth_cli" else api_delay,
        "document_order": [document.file_relative_path for document in ordered_documents],
        "document_plans": [],
    }
    for document in ordered_documents:
        pending_items = get_document_pending_items(document, translated_lookup, include_adult_content)
        if provider == "openai" and openai_auth_mode == "oauth_cli":
            chunk_plan = build_oauth_chunk_plan(pending_items or document.items, batch_size)
        elif provider == "gemini":
            chunk_plan = build_gemini_chunk_plan(pending_items or document.items, batch_size)
        else:
            chunk_plan = {
                "item_limit": max(1, int(batch_size or 1)),
                "char_limit": 0,
                "strategy": "fixed",
                "profile": classify_translation_batch(pending_items or document.items),
            }
        optimization_summary["document_plans"].append(
            {
                "file_relative_path": document.file_relative_path,
                "pending_item_count": len(pending_items),
                "item_limit": chunk_plan["item_limit"],
                "char_limit": chunk_plan["char_limit"],
                "strategy": chunk_plan["strategy"],
                "profile": chunk_plan["profile"],
            }
        )

    if runtime:
        write_json_artifact(
            runtime.metadata_path,
            {
                "session_id": runtime.session_id,
                "provider": provider,
                "gemini_auth_mode": gemini_auth_mode,
                "vertex_descriptor": build_vertex_session_descriptor(vertex_settings),
                "openai_auth_mode": openai_auth_mode,
                "model_name": model_name,
                "analysis_mode": runtime.analysis_mode,
                "target_language": runtime.target_language,
                "documents": [document.file_relative_path for document in documents],
                "ordered_documents": [document.file_relative_path for document in ordered_documents],
                "total_items": total_items,
                "resumed_item_count": resumed_item_count,
                "translation_scope": translation_scope,
                "checkpoint_path": str(runtime.checkpoint_path),
                "attempt_log_dir": str(runtime.attempts_dir),
                "optimization": optimization_summary,
            },
        )

    attempt_index = 0

    def completed_documents() -> List[Dict[str, Any]]:
        ordered_paths = [document.file_relative_path for document in ordered_documents]
        return [completed_document_lookup[path] for path in ordered_paths if path in completed_document_lookup]

    def persist_state(last_error: str = "") -> None:
        if not runtime:
            return
        persist_translation_session_state(
            runtime,
            translated_lookup=translated_lookup,
            total_items=total_items,
            skipped_adult_items=skipped_adult_items,
            failed_items=failed_items,
            completed_batches=completed_batches,
            failed_batches=failed_batches,
            resumed_item_count=resumed_item_count,
            last_error=last_error,
            completed_documents=completed_documents(),
            current_document=current_document,
            halted=halted,
            halt_reason=halt_reason,
            passthrough_item_count=passthrough_item_count,
            optimization=optimization_summary,
        )

    def sync_written_document(document: AnalyzedFile) -> None:
        if not document_write_callback:
            return
        result = document_write_callback(document, translated_lookup, skipped_adult_items, failed_items)
        if not isinstance(result, dict):
            return
        result_payload = dict(result)
        result_payload["completion_state"] = "complete" if is_document_translation_complete(document, translated_lookup, include_adult_content) else "partial"
        result_payload["pending_item_count"] = len(get_document_pending_items(document, translated_lookup, include_adult_content))
        result_payload["written_at"] = datetime.datetime.now().isoformat()
        completed_document_lookup[document.file_relative_path] = result_payload

    for document in ordered_documents:
        if is_document_translation_complete(document, translated_lookup, include_adult_content):
            sync_written_document(document)
    persist_state()

    def process_batch(
        batch: List[TranslationItem],
        document: AnalyzedFile,
        chunk_strategy: str,
        depth: int = 0,
        parent_label: str = "root",
    ) -> None:
        nonlocal attempt_index, halted, halt_reason
        if halted:
            return
        working_batch = [item for item in batch if item.item_id not in translated_lookup]
        if not working_batch:
            return

        actual_model_name = model_name
        model_strategy = "fixed"
        batch_profile = classify_translation_batch(working_batch)
        attempt_index += 1
        attempt_meta = {
            "attempt_index": attempt_index,
            "parent_label": parent_label,
            "depth": depth,
            "provider": provider,
            "openai_auth_mode": openai_auth_mode,
            "requested_model_name": model_name,
            "model_name": actual_model_name,
            "model_strategy": model_strategy,
            "chunk_strategy": chunk_strategy,
            "document_path": document.file_relative_path,
            "item_count": len(working_batch),
            "file_paths": sorted({item.file_relative_path for item in working_batch}),
            "item_ids": [item.item_id for item in working_batch],
            "batch_profile": batch_profile,
            "started_at": datetime.datetime.now().isoformat(),
        }
        attempt_dir = begin_translation_attempt_log(runtime, attempt_index, attempt_meta, "", "") if runtime else None

        log_message(
            f"[{provider}] 배치 번역 시작: {len(working_batch)}개 항목 (model={actual_model_name}, depth={depth}, file={document.file_relative_path})",
            working_batch[0].file_relative_path if working_batch else "batch",
        )

        try:
            prompts = build_batch_prompts(
                item_batch=working_batch,
                world_settings=world_settings,
                character_profiles=character_profiles,
                character_registry=character_registry,
                include_adult_content=include_adult_content,
            )
            if provider == "openai" and openai_auth_mode == "oauth_cli":
                actual_model_name, model_strategy = choose_codex_oauth_model(
                    requested_model=model_name,
                    item_batch=working_batch,
                    depth=depth,
                    unsupported_models=unsupported_oauth_models,
                )
                attempt_meta["model_name"] = actual_model_name
                attempt_meta["model_strategy"] = model_strategy
            if attempt_dir:
                write_json_artifact(attempt_dir / "meta.json", attempt_meta)
                write_text_artifact(attempt_dir / "system_prompt.txt", prompts["system_prompt"])
                write_text_artifact(attempt_dir / "user_prompt.txt", prompts["user_prompt"])

            log_message(
                f"[{provider}] 諛곗튂 踰덉뿭 ?쒖옉: {len(working_batch)}媛???ぉ (model={actual_model_name}, depth={depth}, file={document.file_relative_path})",
                working_batch[0].file_relative_path if working_batch else "batch",
            )
            response_payload = perform_translation(
                provider=provider,
                api_key=api_key,
                model_name=actual_model_name,
                system_prompt=prompts["system_prompt"],
                user_prompt=prompts["user_prompt"],
                gemini_auth_mode=gemini_auth_mode,
                vertex_settings=vertex_settings,
                openai_auth_mode=openai_auth_mode,
                openai_oauth_command=openai_oauth_command,
                workdir=workdir,
                debug_dir=attempt_dir,
            )
            translations = response_payload.get("translations")
            if not isinstance(translations, list):
                raise ValueError("번역 응답에 'translations' 리스트가 없습니다.")

            # 인덱스(i)를 원래의 item_id로 복원하기 위한 맵 생성
            id_map = {str(idx): item.item_id for idx, item in enumerate(working_batch)}
            batch_map: Dict[str, str] = {}
            for entry in translations:
                if not isinstance(entry, dict):
                    continue
                # 새로운 키 'i' (index)와 't' (text) 사용
                raw_idx = entry.get("i")
                text = entry.get("t")
                if raw_idx is not None and isinstance(text, str):
                    real_id = id_map.get(str(raw_idx))
                    if real_id:
                        batch_map[real_id] = text

            missing_items: List[TranslationItem] = []
            translated_count = 0
            for item in working_batch:
                translated_text = batch_map.get(item.item_id)
                if translated_text is None:
                    missing_items.append(item)
                    continue
                translated_lookup[item.item_id] = translated_text.strip()
                translated_count += 1

            completion_record = {
                **attempt_meta,
                "finished_at": datetime.datetime.now().isoformat(),
                "status": "success" if not missing_items else "partial_missing",
                "translated_count": translated_count,
                "missing_count": len(missing_items),
                "log_dir": str(attempt_dir) if attempt_dir else "",
            }
            completed_batches.append(completion_record)
            if attempt_dir:
                finalize_translation_attempt_log(
                    attempt_dir,
                    metadata=completion_record,
                    response_payload=response_payload,
                )
            persist_state()

            if missing_items:
                missing_record = {
                    **completion_record,
                    "status": "partial_missing",
                    "missing_item_ids": [item.item_id for item in missing_items],
                }
                failed_batches.append(missing_record)
                
                # depth가 낮고(아직 너무 많이 쪼개지지 않음) 누락된 항목이 있으면 다시 시도
                if depth < 3:
                    log_message(
                        f"누락된 항목 {len(missing_items)}개에 대해 재시도를 시작합니다. (depth={depth+1})",
                        working_batch[0].file_relative_path if working_batch else "batch",
                    )
                    for sub_batch in split_translation_batch(missing_items):
                        process_batch(sub_batch, document, chunk_strategy, depth + 1, f"missing_{attempt_index:04d}")
                else:
                    # 더 이상 재시도할 수 없는 경우 실패 목록에 저장
                    for m_item in missing_items:
                        failed_items.append(
                            {
                                **m_item.to_public_dict(),
                                "error": "최대 재시도 횟수 초과 또는 번역 응답 누락",
                                "log_dir": str(attempt_dir) if attempt_dir else "",
                            }
                        )
                    persist_state(f"일부 항목({len(missing_items)}개)이 번역되지 않았습니다.")
                return

            if api_delay and api_delay > 0 and not (provider == "openai" and openai_auth_mode == "oauth_cli"):
                time.sleep(api_delay)
        except Exception as exc:  # noqa: BLE001
            error_text = str(exc)
            failure_record = {
                **attempt_meta,
                "finished_at": datetime.datetime.now().isoformat(),
                "status": "retry_split" if len(working_batch) > 1 else "failed",
                "error": error_text,
                "log_dir": str(attempt_dir) if attempt_dir else "",
            }
            failed_batches.append(failure_record)
            if attempt_dir:
                finalize_translation_attempt_log(
                    attempt_dir,
                    metadata=failure_record,
                    error_text=error_text,
                )

            if provider == "openai" and openai_auth_mode == "oauth_cli" and is_unsupported_model_error(error_text):
                unsupported_oauth_models.add(actual_model_name)
                if actual_model_name != "gpt-5.1-codex":
                    persist_state(error_text)
                    process_batch(working_batch, document, chunk_strategy, depth, f"model_retry_{attempt_index:04d}")
                    return

            if is_non_retryable_translation_error(error_text):
                halted = True
                halt_reason = error_text
                persist_state(error_text)
                return

            if len(working_batch) > 1:
                persist_state(error_text)
                for sub_batch in split_translation_batch(working_batch):
                    process_batch(sub_batch, document, chunk_strategy, depth + 1, f"split_{attempt_index:04d}")
                return

            failed_items.append(
                {
                    **working_batch[0].to_public_dict(),
                    "error": error_text,
                    "log_dir": str(attempt_dir) if attempt_dir else "",
                }
            )
            persist_state(error_text)

    for document in ordered_documents:
        current_document = document.file_relative_path
        pending_items = get_document_pending_items(document, translated_lookup, include_adult_content)
        if not pending_items:
            persist_state()
            continue

        if provider == "openai" and openai_auth_mode == "oauth_cli":
            chunk_plan = build_oauth_chunk_plan(pending_items, batch_size)
            batches = chunk_items_by_budget(
                pending_items,
                item_limit=chunk_plan["item_limit"],
                char_limit=chunk_plan["char_limit"],
            )
        elif provider == "gemini":
            chunk_plan = build_gemini_chunk_plan(pending_items, batch_size)
            batches = chunk_items_by_budget(
                pending_items,
                item_limit=chunk_plan["item_limit"],
                char_limit=chunk_plan["char_limit"],
            )
        else:
            chunk_plan = {
                "item_limit": max(1, int(batch_size or 1)),
                "char_limit": 0,
                "strategy": "fixed",
                "profile": classify_translation_batch(pending_items),
            }
            batches = chunk_items(pending_items, batch_size)

        persist_state()
        for batch_index, batch in enumerate(batches, start=1):
            if halted:
                break
            process_batch(
                batch,
                document=document,
                chunk_strategy=chunk_plan["strategy"],
                depth=0,
                parent_label=f"{Path(document.file_name).stem}_{batch_index:04d}",
            )

        sync_written_document(document)
        persist_state(halt_reason if halted else "")
        if halted:
            break

    persist_state()

    return {
        "translated_lookup": translated_lookup,
        "skipped_adult_items": skipped_adult_items,
        "failed_items": failed_items,
        "completed_batches": completed_batches,
        "failed_batches": failed_batches,
        "completed_documents": completed_documents(),
        "halted": halted,
        "halt_reason": halt_reason,
        "optimization": optimization_summary,
        "translation_scope": translation_scope,
        "session": {
            "session_id": runtime.session_id if runtime else "",
            "checkpoint_path": str(runtime.checkpoint_path) if runtime else "",
            "translation_log_dir": str(runtime.attempts_dir) if runtime else "",
            "status_path": str(runtime.status_path) if runtime else "",
            "resumed_item_count": resumed_item_count,
            "passthrough_item_count": passthrough_item_count,
            "completed_batch_count": len(completed_batches),
            "failed_batch_count": len(failed_batches),
            "completed_document_count": len(completed_documents()),
            "halted": halted,
            "halt_reason": halt_reason,
        },
    }


def normalize_style_overrides(entries: Any) -> List[Dict[str, Any]]:
    if not isinstance(entries, list):
        return []

    normalized_entries: List[Dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        style_name = re.sub(r"[^A-Za-z0-9_]+", "", str(entry.get("style_name") or "").strip())
        font_path = normalize_font_reference(entry.get("font_path") or entry.get("font") or "")
        size_value = try_parse_int(entry.get("size"))
        if not style_name or (not font_path and size_value is None):
            continue
        normalized_entries.append(
            {
                "style_name": style_name,
                "font_path": font_path,
                "size": size_value,
            }
        )
    return normalized_entries


def normalize_publish_settings_payload(
    publish_settings: Optional[Dict[str, Any]],
    target_language: str,
    analysis_mode: str,
    gui_baseline: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    normalized = build_default_publish_settings(target_language, analysis_mode, gui_baseline or {})
    incoming = publish_settings or {}

    enabled = incoming.get("enabled")
    if enabled is not None:
        normalized["enabled"] = bool(enabled)

    language_code = normalize_publish_language_code(
        incoming.get("language_code") or normalized["language_code"],
        target_language=target_language,
        analysis_mode=analysis_mode,
    )
    normalized["language_code"] = language_code
    normalized["display_name"] = str(incoming.get("display_name") or normalized["display_name"] or "").strip() or default_publish_display_name(language_code)
    normalized["gui_language"] = str(incoming.get("gui_language") or normalized["gui_language"] or "").strip() or resolve_gui_language_default(
        language_code,
        (gui_baseline or {}).get("base_gui_language"),
    )
    normalized["auto_adjust_sizes"] = bool(incoming.get("auto_adjust_sizes", normalized["auto_adjust_sizes"]))
    normalized["font_preset_id"] = str(incoming.get("font_preset_id") or normalized.get("font_preset_id") or "").strip()

    for key in ("dialogue_font", "name_font", "options_font", "interface_font", "system_font", "glyph_font"):
        normalized[key] = normalize_font_reference(incoming.get(key) or normalized.get(key) or "")

    for key in ("dialogue_scale", "name_scale", "options_scale", "interface_scale"):
        raw_value = incoming.get(key, normalized[key])
        try:
            normalized[key] = max(0.5, min(1.75, float(raw_value)))
        except (TypeError, ValueError):
            normalized[key] = 1.0

    normalized["extra_style_overrides"] = normalize_style_overrides(incoming.get("extra_style_overrides"))
    return normalized


def build_translated_document_lines(
    document: AnalyzedFile,
    translated_lookup: Dict[str, str],
    publish_language_code: Optional[str] = None,
    base_content: Optional[str] = None,
) -> Dict[str, Any]:
    source_lines = document.raw_content.splitlines()
    output_lines = (base_content if isinstance(base_content, str) else document.raw_content).splitlines()
    local_failures: List[Dict[str, Any]] = []
    translated_count = 0
    skipped_count = 0

    for item in document.items:
        if item.item_id not in translated_lookup:
            if item.adult:
                skipped_count += 1
            else:
                local_failures.append(item.to_public_dict())
            continue
        replacement_source = translated_lookup[item.item_id]
        replacement = normalize_translated_text_for_item(
            source_text=item.source_text,
            translated_text=replacement_source,
            block_id=item.block_id,
        )
        output_lines[item.target_line_index] = f'{item.before}{replacement}"{item.after}'
        translated_count += 1

    if publish_language_code and document.file_mode == "translation_layer":
        for index, line in enumerate(output_lines):
            header_match = TRANSLATE_HEADER_RE.match(line)
            if not header_match:
                continue
            indentation = re.match(r"^\s*", line).group(0)
            output_lines[index] = f"{indentation}translate {publish_language_code} {header_match.group('label')}:"

        for item in document.items:
            if item.block_id == "strings" and item.item_id in translated_lookup:
                old_idx = item.target_line_index - 1
                if 0 <= old_idx < len(output_lines) and old_idx < len(source_lines):
                    # Keep the original tl/<lang> old-line exactly as Ren'Py extracted it.
                    # Re-escaping item.source_text here would double-escape sequences like
                    # \" and \n, which breaks publish bundle matching in-game.
                    output_lines[old_idx] = source_lines[old_idx]

    return {
        "output_lines": output_lines,
        "translated_count": translated_count,
        "skipped_count": skipped_count,
        "local_failures": local_failures,
    }


def collect_translate_blocks(lines: List[str]) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    label_counts: Dict[str, int] = {}
    pointer = 0
    while pointer < len(lines):
        header_match = TRANSLATE_HEADER_RE.match(lines[pointer])
        if not header_match:
            pointer += 1
            continue

        label = header_match.group("label")
        start = pointer
        pointer += 1
        while pointer < len(lines) and not TRANSLATE_HEADER_RE.match(lines[pointer]):
            pointer += 1

        occurrence = label_counts.get(label, 0)
        label_counts[label] = occurrence + 1
        blocks.append(
            {
                "key": (label, occurrence),
                "label": label,
                "start": start,
                "end": pointer,
                "lines": lines[start:pointer],
            }
        )
    return blocks


def is_live_translation_output_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False
    if STRING_OLD_RE.match(line) or STRING_NEW_RE.match(line):
        return False
    return '"' in line


def extract_primary_translation_line(block_lines: List[str]) -> Optional[str]:
    for line in block_lines:
        if is_live_translation_output_line(line):
            return line
    return None


def normalize_live_translation_line(source_line: str, translated_line: str) -> str:
    source_pieces = split_first_quoted_string(source_line)
    translated_pieces = split_first_quoted_string(translated_line)
    if not source_pieces or not translated_pieces:
        return translated_line
    normalized_text = normalize_translated_text_for_item(
        source_text=decode_renpy_text_literal(source_pieces["text"]),
        translated_text=translated_pieces["text"],
        block_id=None,
    )
    return f'{source_pieces["before"]}{normalized_text}"{source_pieces["after"]}'


def repair_string_translation_block_lines(
    source_block_lines: List[str],
    output_block_lines: List[str],
) -> Optional[List[str]]:
    if len(source_block_lines) != len(output_block_lines):
        return None

    repaired_lines = [output_block_lines[0]]
    changed = False
    pending_old_text = ""

    for source_line, output_line in zip(source_block_lines[1:], output_block_lines[1:]):
        source_old_match = STRING_OLD_RE.match(source_line)
        if source_old_match:
            pending_old_text = decode_renpy_text_literal(source_old_match.group("text"))

        if STRING_NEW_RE.match(output_line):
            output_match = STRING_NEW_RE.match(output_line)
            indentation = re.match(r"^\s*", output_line).group(0)
            normalized_output_line = f'{indentation}new "{normalize_translated_text_for_item(pending_old_text, output_match.group("text"), "strings")}"'
            repaired_lines.append(normalized_output_line)
            if normalized_output_line != output_line:
                changed = True
            continue
        repaired_lines.append(source_line)
        if source_line != output_line:
            changed = True

    if not changed:
        return None
    return repaired_lines


def repair_translation_layer_output_file(source_path: Path, output_path: Path) -> bool:
    if not source_path.is_file() or not output_path.is_file():
        return False

    try:
        source_lines = source_path.read_text(encoding="utf-8").splitlines()
        output_lines = output_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False

    source_blocks = collect_translate_blocks(source_lines)
    output_blocks = collect_translate_blocks(output_lines)
    output_block_lookup = {block["key"]: block for block in output_blocks}
    repaired_lines = list(output_lines)
    changed = False

    for source_block in reversed(source_blocks):
        output_block = output_block_lookup.get(source_block["key"])
        if not output_block:
            continue

        if source_block["label"] == "strings":
            repaired_block_lines = repair_string_translation_block_lines(
                source_block["lines"],
                output_block["lines"],
            )
            if repaired_block_lines is not None:
                repaired_lines[output_block["start"] : output_block["end"]] = repaired_block_lines
                changed = True
            continue

        translated_line = extract_primary_translation_line(output_block["lines"][1:])
        if not translated_line:
            continue

        new_block_lines = [output_block["lines"][0]]
        replaced_translation = False
        for source_line in source_block["lines"][1:]:
            if not replaced_translation and is_live_translation_output_line(source_line):
                new_block_lines.append(normalize_live_translation_line(source_line, translated_line))
                replaced_translation = True
            else:
                new_block_lines.append(source_line)

        if replaced_translation and new_block_lines != output_block["lines"]:
            repaired_lines[output_block["start"] : output_block["end"]] = new_block_lines
            changed = True

    if not changed:
        return False

    output_path.write_text("\n".join(repaired_lines) + "\n", encoding="utf-8")
    invalidate_compiled_translation_file(output_path)
    return True


def repair_existing_translation_layer_outputs(
    game_dir_path: Path,
    target_language: str,
    publish_language_code: Optional[str] = None,
) -> Dict[str, Any]:
    source_root = game_dir_path / "tl" / normalize_language_code(target_language)
    if not source_root.is_dir():
        return {"repaired": False, "changed_paths": [], "reason": "missing_source_root"}

    candidate_roots: List[Path] = []
    stage_root = get_translation_layer_stage_root(game_dir_path, target_language)
    if stage_root.is_dir():
        candidate_roots.append(stage_root)

    publish_codes = {default_publish_language_code(target_language, "translation_layer")}
    if publish_language_code:
        publish_codes.add(normalize_language_code(publish_language_code))

    tl_root = game_dir_path / "tl"
    if tl_root.is_dir():
        for manifest_path in tl_root.glob("*/zz_workbench_publish_manifest.json"):
            publish_codes.add(manifest_path.parent.name)

    for language_code in sorted(publish_codes):
        publish_root = tl_root / language_code
        if publish_root.is_dir():
            candidate_roots.append(publish_root)

    changed_paths: List[str] = []
    seen_roots: Set[Path] = set()
    for root_path in candidate_roots:
        if root_path in seen_roots:
            continue
        seen_roots.add(root_path)
        for source_path in source_root.rglob("*.rpy"):
            relative_path = source_path.relative_to(source_root)
            output_path = root_path / relative_path
            if repair_translation_layer_output_file(source_path, output_path):
                changed_paths.append(str(output_path))

    if changed_paths:
        clear_renpy_cache_files(game_dir_path)
        clear_translation_compiled_files(game_dir_path)

    return {
        "repaired": bool(changed_paths),
        "changed_paths": changed_paths,
        "reason": "repaired" if changed_paths else "already_clean",
    }


def repair_workbench_outputs_for_game(
    game_dir_path: Path,
    target_language: str,
    publish_language_code: Optional[str] = None,
    force_cache_cleanup: bool = True,
) -> Dict[str, Any]:
    embedded_output_migration = migrate_embedded_workbench_output_root(game_dir_path)
    nested_artifact_migration = migrate_nested_workbench_artifacts(game_dir_path)
    repaired_outputs = repair_existing_translation_layer_outputs(
        game_dir_path,
        target_language,
        publish_language_code=publish_language_code,
    )

    cache_cleanup_files: List[str] = []
    compiled_cleanup_files: List[str] = []
    if force_cache_cleanup:
        cache_cleanup_files = clear_renpy_cache_files(game_dir_path)
        compiled_cleanup_files = clear_translation_compiled_files(game_dir_path)

    return {
        "embedded_output_migration": embedded_output_migration,
        "nested_artifact_migration": nested_artifact_migration,
        "repaired_outputs": repaired_outputs,
        "cache_cleanup_files": cache_cleanup_files,
        "compiled_cleanup_files": compiled_cleanup_files,
    }


def build_publish_font_plan(
    game_dir_path: Path,
    gui_baseline: Dict[str, Any],
    publish_settings: Dict[str, Any],
    publish_root: Path,
) -> Dict[str, Any]:
    font_defaults = gui_baseline.get("font_defaults") or {}
    size_defaults = gui_baseline.get("size_defaults") or {}
    planned_font_assets: Dict[str, str] = {}
    plan = {
        "language_code": publish_settings["language_code"],
        "display_name": publish_settings["display_name"],
        "gui_language": publish_settings["gui_language"],
        "auto_adjust_sizes": publish_settings["auto_adjust_sizes"],
        "fonts": {},
        "font_assets": [],
        "sizes": {},
        "style_overrides": [],
        "missing_fonts": [],
    }

    category_key_map = {
        "dialogue": "dialogue_font",
        "name": "name_font",
        "options": "options_font",
        "interface": "interface_font",
        "system": "system_font",
        "glyph": "glyph_font",
    }
    scale_key_map = {
        "dialogue": "dialogue_scale",
        "name": "name_scale",
        "options": "options_scale",
        "interface": "interface_scale",
    }

    effective_scale_map: Dict[str, float] = {}
    for category, setting_key in category_key_map.items():
        baseline_reference = normalize_font_reference(font_defaults.get(category) or "")
        selected_reference = normalize_font_reference(publish_settings.get(setting_key) or "")
        plan["fonts"][category] = (
            plan_publish_font_reference(
                game_dir_path=game_dir_path,
                publish_root=publish_root,
                font_reference=selected_reference,
                planned_assets=planned_font_assets,
            )
            if selected_reference
            else ""
        )
        if selected_reference and resolve_font_path(game_dir_path, selected_reference) is None:
            plan["missing_fonts"].append(selected_reference)

        manual_scale = float(publish_settings.get(scale_key_map.get(category), 1.0) or 1.0)
        auto_scale = 1.0
        if publish_settings["auto_adjust_sizes"] and category in scale_key_map and baseline_reference and selected_reference:
            auto_scale = compute_font_auto_scale(
                game_dir=game_dir_path,
                baseline_font_reference=baseline_reference,
                candidate_font_reference=selected_reference,
                baseline_size=size_defaults.get(category),
            )
        effective_scale_map[category] = max(0.5, min(1.75, manual_scale * auto_scale))

    size_category_mapping = {
        "dialogue": "dialogue",
        "name": "name",
        "options": "options",
        "interface": "interface",
        "label": "interface",
        "notify": "interface",
        "button": "interface",
        "choice": "options",
    }
    for size_name, baseline_size in size_defaults.items():
        base_value = try_parse_int(baseline_size)
        if base_value is None:
            continue
        scale_category = size_category_mapping.get(size_name, "interface")
        effective_scale = effective_scale_map.get(scale_category, 1.0)
        plan["sizes"][size_name] = max(8, int(round(base_value * effective_scale)))

    for entry in publish_settings["extra_style_overrides"]:
        style_override = {
            "style_name": entry["style_name"],
            "font_path": (
                plan_publish_font_reference(
                    game_dir_path=game_dir_path,
                    publish_root=publish_root,
                    font_reference=entry["font_path"],
                    planned_assets=planned_font_assets,
                )
                if entry.get("font_path")
                else ""
            ),
            "size": try_parse_int(entry.get("size")),
        }
        if entry.get("font_path") and resolve_font_path(game_dir_path, entry["font_path"]) is None:
            plan["missing_fonts"].append(entry["font_path"])
        plan["style_overrides"].append(style_override)

    plan["font_assets"] = [
        {
            "source_path": source_path,
            "relative_path": relative_path,
        }
        for source_path, relative_path in sorted(planned_font_assets.items())
    ]
    plan["missing_fonts"] = sorted(dict.fromkeys(plan["missing_fonts"]))
    return plan


def build_publish_config_content(plan: Dict[str, Any]) -> str:
    language_code = plan["language_code"]
    fonts = plan["fonts"]
    sizes = plan["sizes"]
    lines = [
        "# Generated by Ren'Py Translation Workbench.",
        f"translate {language_code} python:",
        f'    gui.language = "{plan["gui_language"]}"',
    ]

    if fonts.get("dialogue"):
        lines.extend(
            [
                f'    gui.default_font = "{fonts["dialogue"]}"',
                f'    gui.text_font = "{fonts["dialogue"]}"',
            ]
        )
    if fonts.get("name"):
        lines.extend(
            [
                f'    gui.name_font = "{fonts["name"]}"',
                f'    gui.name_text_font = "{fonts["name"]}"',
            ]
        )
    if fonts.get("interface"):
        lines.extend(
            [
                f'    gui.interface_font = "{fonts["interface"]}"',
                f'    gui.interface_text_font = "{fonts["interface"]}"',
                f'    gui.label_font = "{fonts["interface"]}"',
                f'    gui.button_text_font = "{fonts["interface"]}"',
            ]
        )
    if fonts.get("options"):
        lines.append(f'    gui.choice_button_text_font = "{fonts["options"]}"')
    elif fonts.get("interface"):
        lines.append(f'    gui.choice_button_text_font = "{fonts["interface"]}"')
    if fonts.get("system"):
        lines.append(f'    gui.system_font = "{fonts["system"]}"')
    if fonts.get("glyph"):
        lines.append(f'    gui.glyph_font = "{fonts["glyph"]}"')

    size_assignment_map = {
        "dialogue": "gui.text_size",
        "name": "gui.name_text_size",
        "interface": "gui.interface_text_size",
        "label": "gui.label_text_size",
        "notify": "gui.notify_text_size",
        "button": "gui.button_text_size",
        "choice": "gui.choice_button_text_size",
    }
    for size_name, variable_name in size_assignment_map.items():
        size_value = sizes.get(size_name)
        if size_value is not None:
            lines.append(f"    {variable_name} = {size_value}")

    for style_override in plan["style_overrides"]:
        lines.append("")
        lines.append(f"translate {language_code} style {style_override['style_name']}:")
        if style_override.get("font_path"):
            lines.append(f'    font "{style_override["font_path"]}"')
        if style_override.get("size") is not None:
            lines.append(f"    size {style_override['size']}")

    return "\n".join(lines).rstrip() + "\n"


def build_publish_notes(
    game_dir_path: Path,
    gui_baseline: Dict[str, Any],
    publish_root: Path,
    plan: Dict[str, Any],
) -> str:
    relative_publish_root = str(publish_root.relative_to(game_dir_path)).replace("\\", "/")
    lines = [
        "Ren'Py publish bundle generated by Ren'Py Translation Workbench.",
        "",
        f"Language code: {plan['language_code']}",
        f"Display name: {plan['display_name']}",
        f"Publish folder: {relative_publish_root}",
        "Main config file: zz_workbench_language_config.rpy",
        "",
    ]

    if gui_baseline.get("supports_known_languages_menu"):
        lines.append("This game already references Language()/known_languages() in these files:")
        for path in gui_baseline.get("language_hook_files") or []:
            lines.append(f"- {path}")
        lines.append("")
        lines.append("If the language selector uses renpy.known_languages(), this new tl folder can appear without extra code.")
    else:
        lines.append("This game does not appear to expose a language switch automatically.")
        lines.append("Add a button such as:")
        lines.append(f'    textbutton "{plan["display_name"]}" action Language("{plan["language_code"]}")')

    if plan.get("missing_fonts"):
        lines.append("")
        lines.append("Fonts not found at generation time:")
        for font_path in plan["missing_fonts"]:
            lines.append(f"- {font_path}")

    lines.append("")
    lines.append("If you want to overwrite an existing language pack, set the publish language code to that exact tl folder name and translate again.")
    return "\n".join(lines).rstrip() + "\n"


def prepare_translation_output_context(
    game_dir: str,
    analysis_mode: str,
    target_language: str,
    publish_settings: Optional[Dict[str, Any]] = None,
) -> TranslationOutputContext:
    game_dir_path = Path(game_dir)
    gui_baseline = extract_gui_baseline(game_dir_path) if analysis_mode == "translation_layer" else {}
    normalized_publish_settings = normalize_publish_settings_payload(
        publish_settings=publish_settings,
        target_language=target_language,
        analysis_mode=analysis_mode,
        gui_baseline=gui_baseline,
    )
    repair_summary = repair_workbench_outputs_for_game(
        game_dir_path,
        target_language,
        publish_language_code=normalized_publish_settings.get("language_code"),
        force_cache_cleanup=False,
    )
    embedded_output_migration = repair_summary["embedded_output_migration"]
    if embedded_output_migration.get("migrated"):
        log_message(
            f"embedded workbench output moved outside game dir: {embedded_output_migration['embedded_root']} -> {embedded_output_migration['safe_root']}",
            "Translation",
        )
    nested_artifact_migration = repair_summary["nested_artifact_migration"]
    if nested_artifact_migration.get("migrated"):
        log_message(
            f"nested workbench artifacts recovered from tl folders: {len(nested_artifact_migration['moved_paths'])} path(s)",
            "Translation",
        )
    repaired_outputs = repair_summary["repaired_outputs"]
    if repaired_outputs.get("repaired"):
        log_message(
            f"repaired malformed workbench translation blocks: {len(repaired_outputs['changed_paths'])} file(s)",
            "Translation",
        )
    if analysis_mode == "translation_layer":
        migration_result = migrate_legacy_translation_layer_stage_root(game_dir_path, target_language)
        if migration_result.get("migrated"):
            log_message(
                f"legacy tl staging moved to safe output root: {migration_result['legacy_root']} -> {migration_result['stage_root']}",
                "Translation",
            )
        output_root = get_translation_layer_stage_root(game_dir_path, target_language)
    else:
        output_root = get_source_stage_root(game_dir_path, target_language)

    output_root.mkdir(parents=True, exist_ok=True)
    publish_bundle = {
        "enabled": False,
        "supported": analysis_mode == "translation_layer",
        "language_code": normalized_publish_settings["language_code"],
        "display_name": normalized_publish_settings["display_name"],
        "publish_root": "",
        "config_path": "",
        "manifest_path": "",
        "notes_path": "",
        "missing_fonts": [],
        "size_plan": {},
        "font_plan": {},
        "font_assets": [],
    }
    publish_root: Optional[Path] = None
    publish_plan: Optional[Dict[str, Any]] = None

    if analysis_mode == "translation_layer" and normalized_publish_settings.get("enabled"):
        publish_root = game_dir_path / "tl" / normalized_publish_settings["language_code"]
        publish_root.mkdir(parents=True, exist_ok=True)
        publish_plan = build_publish_font_plan(
            game_dir_path=game_dir_path,
            gui_baseline=gui_baseline,
            publish_settings=normalized_publish_settings,
            publish_root=publish_root,
        )
        publish_bundle.update(
            {
                "enabled": True,
                "publish_root": str(publish_root.relative_to(game_dir_path)).replace("\\", "/"),
                "missing_fonts": publish_plan["missing_fonts"],
                "size_plan": publish_plan["sizes"],
                "font_plan": publish_plan["fonts"],
                "font_assets": publish_plan.get("font_assets") or [],
            }
        )
    elif analysis_mode != "translation_layer":
        publish_bundle["reason"] = "source_files/uploaded_files 모드는 Ren'Py tl 언어 팩을 자동 생성할 수 없습니다."
    else:
        publish_bundle["reason"] = "publish bundle 생성이 비활성화되어 있습니다."

    return TranslationOutputContext(
        game_dir_path=game_dir_path,
        output_root=output_root,
        analysis_mode=analysis_mode,
        target_language=target_language,
        gui_baseline=gui_baseline,
        normalized_publish_settings=normalized_publish_settings,
        publish_bundle=publish_bundle,
        publish_root=publish_root,
        publish_plan=publish_plan,
    )


def write_document_result_to_disk(
    document: AnalyzedFile,
    translated_lookup: Dict[str, str],
    output_context: TranslationOutputContext,
) -> Dict[str, Any]:
    output_path = output_context.output_root / Path(document.output_relative_path)
    stage_base_content = None
    if output_path.is_file():
        existing_content = output_path.read_text(encoding="utf-8")
        if len(existing_content.splitlines()) == len(document.raw_content.splitlines()):
            stage_base_content = existing_content
    stage_output = build_translated_document_lines(
        document=document,
        translated_lookup=translated_lookup,
        base_content=stage_base_content,
    )
    output_lines = stage_output["output_lines"]
    local_failures = stage_output["local_failures"]
    translated_count = stage_output["translated_count"]
    skipped_count = stage_output["skipped_count"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    invalidate_compiled_translation_file(output_path)

    publish_relative_path = ""
    if output_context.publish_root is not None:
        publish_path = output_context.publish_root / Path(document.output_relative_path)
        publish_base_content = None
        if publish_path.is_file():
            existing_publish_content = publish_path.read_text(encoding="utf-8")
            if len(existing_publish_content.splitlines()) == len(document.raw_content.splitlines()):
                publish_base_content = existing_publish_content
        publish_output = build_translated_document_lines(
            document=document,
            translated_lookup=translated_lookup,
            publish_language_code=output_context.normalized_publish_settings["language_code"],
            base_content=publish_base_content,
        )
        publish_path.parent.mkdir(parents=True, exist_ok=True)
        publish_path.write_text("\n".join(publish_output["output_lines"]) + "\n", encoding="utf-8")
        invalidate_compiled_translation_file(publish_path)
        publish_relative_path = build_public_path(output_context.game_dir_path, publish_path)

    return {
        "original_filename": document.file_name,
        "file_relative_path": document.file_relative_path,
        "output_relative_path": build_public_path(output_context.game_dir_path, output_path),
        "publish_relative_path": publish_relative_path,
        "translated_content": "\n".join(output_lines) + "\n",
        "translated_count": translated_count,
        "skipped_adult_count": skipped_count,
        "failed_item_count": len(local_failures),
        "status": "success" if not local_failures else "partial",
    }


def sync_translation_support_files(
    documents: List[AnalyzedFile],
    skipped_adult_items: List[Dict[str, Any]],
    failed_items: List[Dict[str, Any]],
    output_context: TranslationOutputContext,
) -> Dict[str, Any]:
    adult_review_payload = {
        "skipped_adult_items": skipped_adult_items,
        "failed_items": failed_items,
        "generated_at": datetime.datetime.now().isoformat(),
    }
    adult_review_path = output_context.output_root / "adult_review.json"
    adult_review_path.write_text(json.dumps(adult_review_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    publish_bundle = dict(output_context.publish_bundle)
    if output_context.publish_root is not None and output_context.publish_plan is not None:
        copied_font_assets: List[str] = []
        for asset in output_context.publish_plan.get("font_assets") or []:
            source_path = Path(asset.get("source_path") or "")
            relative_path = str(asset.get("relative_path") or "").strip()
            if not source_path.is_file() or not relative_path:
                continue
            destination_path = output_context.publish_root / relative_path
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)
            copied_font_assets.append(relative_path.replace("\\", "/"))

        config_path = output_context.publish_root / "zz_workbench_language_config.rpy"
        config_path.write_text(build_publish_config_content(output_context.publish_plan), encoding="utf-8")
        invalidate_compiled_translation_file(config_path)

        manifest_path = output_context.publish_root / "zz_workbench_publish_manifest.json"
        manifest_payload = {
            "generated_at": datetime.datetime.now().isoformat(),
            "publish_settings": output_context.normalized_publish_settings,
            "publish_plan": output_context.publish_plan,
            "gui_baseline": output_context.gui_baseline,
            "analysis_mode": output_context.analysis_mode,
            "target_language": output_context.target_language,
            "document_count": len(documents),
        }
        manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        notes_path = output_context.publish_root / "zz_workbench_publish_notes.txt"
        notes_path.write_text(
            build_publish_notes(
                game_dir_path=output_context.game_dir_path,
                gui_baseline=output_context.gui_baseline,
                publish_root=output_context.publish_root,
                plan=output_context.publish_plan,
            ),
            encoding="utf-8",
        )
        publish_bundle.update(
            {
                "config_path": build_public_path(output_context.game_dir_path, config_path),
                "manifest_path": build_public_path(output_context.game_dir_path, manifest_path),
                "notes_path": build_public_path(output_context.game_dir_path, notes_path),
                "font_assets": copied_font_assets,
            }
        )

    cache_cleanup_files: List[str] = []
    compiled_cleanup_files: List[str] = []
    if output_context.analysis_mode == "translation_layer":
        cache_cleanup_files = clear_renpy_cache_files(output_context.game_dir_path)
        compiled_cleanup_files = clear_translation_compiled_files(output_context.game_dir_path)
    if cache_cleanup_files:
        publish_bundle["cache_cleanup_files"] = [
            build_public_path(output_context.game_dir_path, Path(cache_path))
            for cache_path in cache_cleanup_files
        ]
    if compiled_cleanup_files:
        publish_bundle["compiled_cleanup_files"] = [
            build_public_path(output_context.game_dir_path, Path(cache_path))
            for cache_path in compiled_cleanup_files
        ]

    return {
        "adult_review_path": build_public_path(output_context.game_dir_path, adult_review_path),
        "publish_bundle": publish_bundle,
    }


def write_results_to_disk(
    documents: List[AnalyzedFile],
    translated_lookup: Dict[str, str],
    game_dir: str,
    analysis_mode: str,
    target_language: str,
    skipped_adult_items: List[Dict[str, Any]],
    failed_items: List[Dict[str, Any]],
    publish_settings: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    output_context = prepare_translation_output_context(
        game_dir=game_dir,
        analysis_mode=analysis_mode,
        target_language=target_language,
        publish_settings=publish_settings,
    )
    results = [write_document_result_to_disk(document, translated_lookup, output_context) for document in documents]
    sync_payload = sync_translation_support_files(
        documents=documents,
        skipped_adult_items=skipped_adult_items,
        failed_items=failed_items,
        output_context=output_context,
    )

    return {
        "results": results,
        "adult_review_path": sync_payload["adult_review_path"],
        "publish_bundle": sync_payload["publish_bundle"],
    }


def build_effective_translation_lookup(document: AnalyzedFile) -> Dict[str, str]:
    effective_lookup: Dict[str, str] = {}
    for item in document.items:
        if is_meaningfully_translated(item.source_text, item.workbench_translation_text):
            effective_lookup[item.item_id] = item.workbench_translation_text
        elif is_meaningfully_translated(item.source_text, item.connected_translation_text):
            effective_lookup[item.item_id] = item.connected_translation_text
        elif is_meaningfully_translated(item.source_text, item.current_text):
            effective_lookup[item.item_id] = item.current_text
    return effective_lookup


def build_editable_translation_text(item: TranslationItem) -> Tuple[str, str]:
    if is_meaningfully_translated(item.source_text, item.workbench_translation_text):
        return item.workbench_translation_text, item.workbench_translation_source or "workbench_output"
    if is_meaningfully_translated(item.source_text, item.connected_translation_text):
        return item.connected_translation_text, item.connected_translation_source or "game_translation"
    if is_meaningfully_translated(item.source_text, item.current_text):
        return item.current_text, "current_file"
    return "", ""


def build_document_editor_payload(
    document: AnalyzedFile,
    output_context: Optional[TranslationOutputContext] = None,
) -> Dict[str, Any]:
    output_relative_path = ""
    publish_relative_path = ""
    if output_context is not None:
        output_relative_path = build_public_path(
            output_context.game_dir_path,
            output_context.output_root / Path(document.output_relative_path),
        )
        if output_context.publish_root is not None:
            publish_relative_path = build_public_path(
                output_context.game_dir_path,
                output_context.publish_root / Path(document.output_relative_path),
            )

    items_payload: List[Dict[str, Any]] = []
    for item in document.items:
        editable_text, editable_source = build_editable_translation_text(item)
        item_payload = item.to_public_dict()
        item_payload.update(
            {
                "editable_text": editable_text,
                "editable_source": editable_source,
            }
        )
        items_payload.append(item_payload)

    return {
        "file_name": document.file_name,
        "file_relative_path": document.file_relative_path,
        "file_mode": document.file_mode,
        "output_relative_path": output_relative_path,
        "publish_relative_path": publish_relative_path,
        "item_count": len(document.items),
        "adult_item_count": sum(1 for item in document.items if item.adult),
        "items": items_payload,
    }


def build_generate_files_response(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    documents_info = get_documents_for_translation(payload)
    generated_files = []
    for document in documents_info["documents"]:
        generated_files.append(
            {
                "file_name": document.file_name,
                "file_content": document.raw_content,
                "original_rpy_path": document.file_relative_path,
                "file_mode": document.file_mode,
            }
        )
    return generated_files


@app.route("/health")
def health_check() -> Dict[str, str]:
    return jsonify({"status": "ok"})


@app.route("/system_fonts")
def list_system_fonts() -> Any:
    fonts = discover_system_fonts()
    preview_text = (request.args.get("sample") or "").strip() or DEFAULT_FONT_PREVIEW_TEXT
    payload = []
    for entry in fonts:
        payload.append(
            {
                **entry,
                "preview_url": f"/font_preview?font_id={entry['font_id']}&sample={quote_plus(preview_text)}",
            }
        )
    return jsonify({"font_count": len(payload), "fonts": payload})


@app.route("/font_preview")
def font_preview() -> Any:
    font_id = (request.args.get("font_id") or "").strip()
    path_value = (request.args.get("path") or "").strip()
    font_reference = (request.args.get("font_reference") or "").strip()
    game_dir = (request.args.get("game_dir") or "").strip()
    preview_text = (request.args.get("sample") or "").strip() or DEFAULT_FONT_PREVIEW_TEXT

    font_path = resolve_font_preview_path(
        font_id=font_id,
        path_value=path_value,
        font_reference=font_reference,
        game_dir=game_dir,
    )
    if font_path is None:
        return jsonify({"error": "폰트 파일을 찾을 수 없습니다."}), 404

    try:
        width = int(request.args.get("width") or 640)
    except ValueError:
        width = 640
    try:
        height = int(request.args.get("height") or 140)
    except ValueError:
        height = 140

    width = max(280, min(width, 1024))
    height = max(84, min(height, 320))

    try:
        preview_image = build_font_preview_image(font_path, preview_text=preview_text, width=width, height=height)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"폰트 미리보기 생성 실패: {exc}"}), 500

    image_buffer = BytesIO()
    preview_image.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    return send_file(image_buffer, mimetype="image/png", max_age=3600)


@app.route("/asset_thumbnail")
def asset_thumbnail() -> Any:
    raw_path = (request.args.get("path") or "").strip()
    if not raw_path:
        return jsonify({"error": "이미지 경로가 비어 있습니다."}), 400

    asset_path = Path(raw_path)
    if asset_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"} or not asset_path.is_file():
        return jsonify({"error": "유효한 이미지 파일을 찾지 못했습니다."}), 404

    try:
        size = int(request.args.get("size") or 160)
    except ValueError:
        size = 160
    size = max(64, min(size, 512))
    crop = parse_crop_query((request.args.get("crop") or "").strip())

    try:
        with Image.open(asset_path) as image:
            thumbnail = build_thumbnail_image(image.convert("RGBA"), crop, size)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"썸네일 생성 실패: {exc}"}), 500

    image_buffer = BytesIO()
    thumbnail.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    return send_file(image_buffer, mimetype="image/png", max_age=3600)


@app.route("/get_startup_path")
def get_startup_path() -> Dict[str, Any]:
    return jsonify({"path": game_exe_path_from_startup})


@app.route("/pick_game_exe")
def pick_game_exe() -> Any:
    try:
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected_path = filedialog.askopenfilename(
            title="Ren'Py 게임 실행 파일 선택",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        )
        root.destroy()
        return jsonify({"path": selected_path or None})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500

@app.route("/generate_template", methods=["POST"])
def generate_template() -> Any:
    log_message("'/generate_template' 요청 받음")
    payload = request.get_json(force=True) or {}

    game_exe_path = payload.get("game_exe_path")
    target_language = payload.get("target_language")

    if not game_exe_path or not target_language:
        return jsonify({"error": "game_exe_path와 target_language가 필요합니다."}), 400

    game_dir_str = find_game_directory(game_exe_path)
    if not game_dir_str:
        return jsonify({"error": "'game' 폴더를 찾을 수 없습니다."}), 400

    game_dir = Path(game_dir_str)
    # SDK가 설치되어 있는지 확인
    sdk_dir = APP_ROOT / "renpy_sdk"
    sdk_exe_paths = list(sdk_dir.glob("renpy-*-sdk/renpy.exe"))
    
    if not sdk_dir.is_dir() or not sdk_exe_paths:
        log_message("Ren'Py SDK가 설치되지 않아 템플릿 생성을 진행할 수 없습니다.")
        return jsonify({"error": "SDK_MISSING", "message": "Ren'Py SDK가 필요합니다. 다운로드를 진행하시겠습니까?"}), 400
        
    sdk_exe = str(sdk_exe_paths[0])
    
    tl_dir = game_dir / "tl" / target_language
    remove_workbench_artifact_dirs(tl_dir)
    existing_template_files = list_translation_template_files(tl_dir)
    expected_template_paths = build_expected_template_relative_paths(game_dir)
    existing_template_paths = (
        {
            str(path.relative_to(tl_dir)).replace("\\", "/")
            for path in existing_template_files
        }
        if tl_dir.is_dir()
        else set()
    )
    missing_template_paths = expected_template_paths - existing_template_paths

    # 캐시 확인: 이미 템플릿 파일(.rpy)이 하나라도 있다면 추출 생략
    if existing_template_files and not missing_template_paths:
        log_message(f"[{target_language}] 언어 폴더에 이미 번역 템플릿 파일이 존재합니다 (캐시 활용).")
        return jsonify({"status": "cached", "message": "이미 번역 템플릿이 존재하여 추출을 건너뛰었습니다."}), 200
    if missing_template_paths:
        log_message(f"[{target_language}] 템플릿 누락 {len(missing_template_paths)}개를 감지하여 재생성합니다.")

    log_message(f"[{target_language}] 번역 템플릿 생성을 시작합니다...")
    temp_root: Optional[Path] = None
    temp_game_dir: Optional[Path] = None
    
    try:
        temp_root, temp_game_dir = build_template_generation_workspace(game_dir)
        cmd = [sdk_exe, str(temp_game_dir), "translate", target_language]
        # 백그라운드 서버 블로킹 방지를 위해 적절한 타임아웃(예: 300초) 설정 및 인코딩 방어
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        copied_files = copy_generated_templates_to_game(temp_game_dir, game_dir, target_language)
        
        # 엔진 출력에 따른 리턴코드가 1이어도 실제 파일은 정상 생성되는 경우가 있으므로 파일 우선 확인
        if copied_files:
            log_message(f"[{target_language}] 번역 템플릿 생성 완료.")
            return jsonify({"status": "success", "message": "번역 템플릿 추출이 완료되었습니다."}), 200
        else:
            if result.returncode == 0:
                log_message("명령어는 성공했으나 파일이 생성되지 않음.")
                return jsonify({"error": "명령은 성공했지만 템플릿 파일이 보이지 않습니다."}), 500
            else:
                # 에러 메시지를 로깅할 때, 비표준 문자로 인해 터미널 로거가 터지는 현상 방지: ascii.encode
                err_text = ""
                if result.stderr: err_text += result.stderr + "\n"
                if result.stdout: err_text += result.stdout
                
                safe_err = err_text.encode('ascii', 'replace').decode('ascii') if err_text else "Unknown error (No stdout/stderr)"
                log_message(f"템플릿 추출 실패:\n{safe_err}")
                return jsonify({"error": f"엔진 추출 중 파일이 생성되지 않았으며 오류가 발생했습니다:\n{safe_err}"}), 500
    except subprocess.TimeoutExpired:
        # 시간 초과 시에도 파일이 일부/전부 생성되었을 수 있으므로 확인
        if temp_game_dir is not None:
            copy_generated_templates_to_game(temp_game_dir, game_dir, target_language)
        if list_translation_template_files(tl_dir):
            log_message(f"[{target_language}] 타임아웃이 발생했으나 템플릿 파일은 생성되어 무시합니다.")
            return jsonify({"status": "success", "message": "과정이 오래 걸렸으나 번역 템플릿 추출은 일부/전부 완료되었습니다."}), 200
        else:    
            log_message("템플릿 추출 시간 초과.")
            return jsonify({"error": "템플릿 추출 시간이 초과되었습니다 (5분). 수동으로 진행해주세요."}), 504
    except Exception as e:
        safe_e = str(e).encode('ascii', 'replace').decode('ascii')
        log_message(f"템플릿 추출 중 예외 발생: {safe_e}")
        return jsonify({"error": f"템플릿 추출 중 오류: {safe_e}"}), 500
    finally:
        if temp_root is not None:
            shutil.rmtree(temp_root, ignore_errors=True)


@app.route("/download_renpy_sdk", methods=["POST"])
def download_renpy_sdk():
    """
    Ren'Py SDK 8.3.4를 워크벤치/renpy_sdk 내부에 다운로드 및 압축 해제
    """
    import urllib.request
    import zipfile
    import tempfile
    import shutil

    sdk_dir = APP_ROOT / "renpy_sdk"
    sdk_url = "https://www.renpy.org/dl/8.3.4/renpy-8.3.4-sdk.zip"
    
    # 이미 설치되어 있는지 확인
    if sdk_dir.is_dir() and any(sdk_dir.glob("renpy-*-sdk/renpy.exe")):
        return jsonify({"status": "success", "message": "Ren'Py SDK가 이미 설치되어 있습니다."}), 200

    try:
        log_message("Ren'Py SDK 다운로드 시작 (약 150MB)...")
        # 임시 파일로 다운로드
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            temp_path = tmp_file.name
            
        urllib.request.urlretrieve(sdk_url, temp_path)
        log_message("Ren'Py SDK 다운로드 완료. 압축 해제 중...")
        
        # 압축 해제
        sdk_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(temp_path, 'r') as zip_ref:
            zip_ref.extractall(sdk_dir)
            
        # 임시 파일 삭제
        try:
            os.remove(temp_path)
        except:
            pass
            
        log_message("Ren'Py SDK 설치 완료.")
        return jsonify({"status": "success", "message": "Ren'Py SDK를 성공적으로 다운로드했습니다."}), 200
        
    except Exception as e:
        safe_e = str(e).encode('ascii', 'replace').decode('ascii')
        log_message(f"Ren'Py SDK 설치 중 오류: {safe_e}")
        return jsonify({"error": f"SDK 다운로드 중 오류 발생: {safe_e}"}), 500

@app.route("/analyze_sources", methods=["POST"])
def analyze_sources() -> Any:
    log_message("'/analyze_sources' 요청 수신")
    data = request.get_json(force=True) or {}
    target_language = data.get("target_language") or DEFAULT_TARGET_LANGUAGE

    if data.get("game_exe_path"):
        game_exe_path = data["game_exe_path"]
        if not os.path.isfile(game_exe_path):
            return jsonify({"error": "유효한 게임 실행 파일(.exe) 경로가 아닙니다."}), 400
        try:
            response = analyze_game_path(game_exe_path, target_language)
            return jsonify(response)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": str(exc)}), 500

    files_data = data.get("files_data") or []
    if files_data:
        try:
            response = analyze_uploaded_files(files_data, target_language)
            return jsonify(response)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": str(exc)}), 500

    return jsonify({"error": "분석할 게임 경로 또는 파일 데이터가 없습니다."}), 400


@app.route("/repair_translation_outputs", methods=["POST"])
def repair_translation_outputs() -> Any:
    data = request.get_json(force=True) or {}
    game_exe_path = data.get("game_exe_path") or game_exe_path_from_startup
    target_language = data.get("target_language") or DEFAULT_TARGET_LANGUAGE
    publish_settings = data.get("publish_settings") or {}

    if not game_exe_path:
        return jsonify({"error": "game_exe_path媛 ?꾩슂?⑸땲??"}), 400

    game_dir_str = find_game_directory(game_exe_path)
    if not game_dir_str:
        return jsonify({"error": "'game' ?대뜑瑜?李얠쓣 ???놁뒿?덈떎."}), 400

    game_dir_path = Path(game_dir_str)
    normalized_publish_settings = normalize_publish_settings_payload(
        publish_settings=publish_settings,
        target_language=target_language,
        analysis_mode="translation_layer",
        gui_baseline=extract_gui_baseline(game_dir_path),
    )
    repair_summary = repair_workbench_outputs_for_game(
        game_dir_path,
        target_language,
        publish_language_code=normalized_publish_settings.get("language_code"),
        force_cache_cleanup=True,
    )
    repaired_outputs = repair_summary["repaired_outputs"]
    return jsonify(
        {
            "status": "success",
            "game_dir": str(game_dir_path),
            "target_language": normalize_language_code(target_language),
            "publish_language_code": normalized_publish_settings.get("language_code"),
            "embedded_output_migration": repair_summary["embedded_output_migration"],
            "nested_artifact_migration": repair_summary["nested_artifact_migration"],
            "repaired_outputs": repaired_outputs,
            "cache_cleanup_count": len(repair_summary["cache_cleanup_files"]),
            "compiled_cleanup_count": len(repair_summary["compiled_cleanup_files"]),
            "cache_cleanup_files": repair_summary["cache_cleanup_files"],
            "compiled_cleanup_files": repair_summary["compiled_cleanup_files"],
        }
    )


@app.route("/apply_publish_fonts", methods=["POST"])
def apply_publish_fonts() -> Any:
    data = request.get_json(force=True) or {}
    game_exe_path = data.get("game_exe_path") or game_exe_path_from_startup
    target_language = data.get("target_language") or DEFAULT_TARGET_LANGUAGE
    analysis_mode = str(data.get("analysis_mode") or "translation_layer").strip() or "translation_layer"
    publish_settings = data.get("publish_settings") or {}

    if not game_exe_path:
        return jsonify({"error": "game_exe_path가 비어 있습니다."}), 400

    game_dir_str = find_game_directory(game_exe_path)
    if not game_dir_str:
        return jsonify({"error": "선택한 경로에서 'game' 폴더를 찾지 못했습니다."}), 400

    if analysis_mode != "translation_layer":
        return jsonify({"error": "폰트만 재적용은 Ren'Py game/tl publish bundle 모드에서만 지원됩니다."}), 400

    output_context = prepare_translation_output_context(
        game_dir=game_dir_str,
        analysis_mode=analysis_mode,
        target_language=target_language,
        publish_settings=publish_settings,
    )
    sync_payload = sync_translation_support_files(
        documents=[],
        skipped_adult_items=[],
        failed_items=[],
        output_context=output_context,
    )
    publish_bundle = sync_payload["publish_bundle"]
    return jsonify(
        {
            "status": "success",
            "analysis_mode": analysis_mode,
            "target_language": normalize_language_code(target_language),
            "game_dir": game_dir_str,
            "adult_review_path": sync_payload["adult_review_path"],
            "publish_bundle": publish_bundle,
            "font_asset_count": len(publish_bundle.get("font_assets") or []),
        }
    )


def build_session_runtime_from_id(
    *,
    session_id: str,
    analysis_mode: str,
    target_language: str,
    game_dir: Optional[str] = None,
) -> TranslationSessionRuntime:
    normalized_analysis_mode = str(analysis_mode or "translation_layer").strip() or "translation_layer"
    normalized_target_language = normalize_language_code(target_language or DEFAULT_TARGET_LANGUAGE)
    if game_dir:
        session_dir = Path(game_dir) / TRANSLATION_LOG_DIRNAME / normalized_analysis_mode / normalized_target_language / session_id
        runtime_game_dir = Path(game_dir)
    else:
        session_dir = UPLOADED_TRANSLATION_RUN_ROOT / normalized_analysis_mode / normalized_target_language / session_id
        runtime_game_dir = None
    return TranslationSessionRuntime(
        session_id=session_id,
        session_dir=session_dir,
        attempts_dir=session_dir / "attempts",
        checkpoint_path=session_dir / "checkpoint.json",
        status_path=session_dir / "status.json",
        metadata_path=session_dir / "session.json",
        game_dir=runtime_game_dir,
        analysis_mode=normalized_analysis_mode,
        target_language=normalized_target_language,
    )


def normalize_translation_scope_for_matching(scope: Any) -> Dict[str, Any]:
    payload = dict(scope) if isinstance(scope, dict) else {}
    normalized: Dict[str, Any] = {}
    for key, value in payload.items():
        if key in {"selected_speaker_ids", "selected_speaker_names", "selected_item_ids", "selected_files", "documents"}:
            if isinstance(value, list):
                normalized[key] = sorted(str(item) for item in value if str(item or "").strip())
            else:
                normalized[key] = []
        elif isinstance(value, bool):
            normalized[key] = value
        elif value is None:
            normalized[key] = ""
        else:
            normalized[key] = str(value) if isinstance(value, (int, float)) else value
    return normalized


def parse_iso_datetime(value: Any) -> datetime.datetime:
    try:
        return datetime.datetime.fromisoformat(str(value or "").strip())
    except Exception:  # noqa: BLE001
        return datetime.datetime.min


def score_translation_session_match(
    session_payload: Dict[str, Any],
    *,
    provider: str,
    gemini_auth_mode: str,
    vertex_descriptor: Dict[str, str],
    openai_auth_mode: str,
    model_name: str,
    requested_scope: Dict[str, Any],
    requested_documents: Set[str],
) -> int:
    score = 0
    if session_payload.get("provider") == provider:
        score += 30
    if session_payload.get("gemini_auth_mode") == gemini_auth_mode:
        score += 10
    if (session_payload.get("vertex_descriptor") or {}) == vertex_descriptor:
        score += 10
    if session_payload.get("openai_auth_mode") == openai_auth_mode:
        score += 10
    if session_payload.get("model_name") == model_name:
        score += 25

    session_scope = normalize_translation_scope_for_matching(session_payload.get("translation_scope") or {})
    if session_scope == requested_scope:
        score += 40
    elif session_scope.get("mode") == requested_scope.get("mode"):
        score += 10

    session_documents = {
        str(path or "").strip()
        for path in (session_payload.get("documents") or [])
        if str(path or "").strip()
    }
    if requested_documents and session_documents:
        if session_documents == requested_documents:
            score += 30
        else:
            overlap = len(session_documents & requested_documents)
            score += min(20, overlap * 2)
    return score


def find_best_translation_session(
    *,
    game_dir: Path,
    analysis_mode: str,
    target_language: str,
    provider: str,
    gemini_auth_mode: str,
    vertex_settings: Dict[str, str],
    openai_auth_mode: str,
    model_name: str,
    requested_scope: Dict[str, Any],
    requested_documents: Set[str],
) -> Optional[Dict[str, Any]]:
    session_root = game_dir / TRANSLATION_LOG_DIRNAME / analysis_mode / target_language
    if not session_root.is_dir():
        return None

    normalized_scope = normalize_translation_scope_for_matching(requested_scope)
    vertex_descriptor = build_vertex_session_descriptor(vertex_settings)
    candidates: List[Tuple[Tuple[int, datetime.datetime, int], Dict[str, Any]]] = []
    now = datetime.datetime.now()

    for session_dir in session_root.iterdir():
        if not session_dir.is_dir():
            continue
        metadata_path = session_dir / "session.json"
        status_path = session_dir / "status.json"
        if not metadata_path.is_file() or not status_path.is_file():
            continue

        session_payload = read_json_artifact(metadata_path)
        status_payload = read_json_artifact(status_path)
        if not session_payload or not status_payload:
            continue

        pending_item_count = try_parse_int(status_payload.get("pending_item_count")) or 0
        halted = bool(status_payload.get("halted"))
        active = pending_item_count > 0 and not halted
        updated_at = parse_iso_datetime(status_payload.get("updated_at"))
        if updated_at is datetime.datetime.min:
            active = False
        elif active and (now - updated_at).total_seconds() > ACTIVE_TRANSLATION_SESSION_STALE_SECONDS:
            active = False
        match_score = score_translation_session_match(
            session_payload,
            provider=provider,
            gemini_auth_mode=gemini_auth_mode,
            vertex_descriptor=vertex_descriptor,
            openai_auth_mode=openai_auth_mode,
            model_name=model_name,
            requested_scope=normalized_scope,
            requested_documents=requested_documents,
        )
        candidates.append(
            (
                (1 if active else 0, updated_at, match_score),
                {
                    "session_id": session_dir.name,
                    "session_payload": session_payload,
                    "status_payload": status_payload,
                    "active": active,
                    "match_score": match_score,
                },
            )
        )

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


@app.route("/resolve_translation_session", methods=["POST"])
def resolve_translation_session() -> Any:
    data = request.get_json(force=True) or {}
    provider = (data.get("provider") or "gemini").lower()
    gemini_auth_mode = normalize_gemini_auth_mode(provider, data.get("gemini_auth_mode"))
    vertex_settings = normalize_vertex_settings(data.get("vertex_settings"))
    openai_auth_mode = normalize_openai_auth_mode(provider, data.get("openai_auth_mode"))
    model_name = data.get("model_name") or (
        DEFAULT_CODEX_OAUTH_MODEL if provider == "openai" and openai_auth_mode == "oauth_cli" else DEFAULT_MODELS[provider]
    )
    if provider == "openai" and openai_auth_mode == "oauth_cli":
        model_name, _ = normalize_codex_oauth_requested_model(model_name)

    try:
        translation_inputs = get_documents_for_translation(data)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 400

    documents = translation_inputs.get("documents") or []
    if not documents:
        return jsonify(
            {
                "error": "踰덉뿭 ???뚯씪??媛 議댁옱?섏? ?딆뒿?덈떎.",
                "translation_scope": translation_inputs.get("translation_scope") or {},
            }
        ), 400

    runtime = build_translation_session_runtime(
        documents=documents,
        provider=provider,
        gemini_auth_mode=gemini_auth_mode,
        vertex_settings=vertex_settings,
        openai_auth_mode=openai_auth_mode,
        model_name=model_name,
        analysis_mode=translation_inputs["analysis_mode"],
        target_language=translation_inputs["target_language"],
        include_adult_content=bool(data.get("include_adult_content")),
        world_settings=data.get("world_settings") or {},
        character_profiles=data.get("character_profiles") or {},
        game_dir=translation_inputs.get("game_dir"),
        translation_scope=translation_inputs.get("translation_scope"),
    )
    status_payload = build_translation_status_payload(runtime)
    return jsonify(
        {
            "session_id": runtime.session_id,
            "analysis_mode": runtime.analysis_mode,
            "target_language": runtime.target_language,
            "status_path": str(runtime.status_path),
            "checkpoint_path": str(runtime.checkpoint_path),
            "translation_log_dir": str(runtime.attempts_dir),
            "document_count": len(documents),
            "translation_scope": translation_inputs.get("translation_scope") or {},
            "status": status_payload,
        }
    )


@app.route("/find_active_translation_session", methods=["POST"])
def find_active_translation_session() -> Any:
    data = request.get_json(force=True) or {}
    game_exe_path = str(data.get("game_exe_path") or "").strip()
    if not game_exe_path:
        return jsonify({"error": "game_exe_path가 필요합니다."}), 400

    game_dir_str = find_game_directory(game_exe_path)
    if not game_dir_str:
        return jsonify({"error": "'game' 폴더를 찾지 못했습니다."}), 400

    provider = (data.get("provider") or "gemini").lower()
    gemini_auth_mode = normalize_gemini_auth_mode(provider, data.get("gemini_auth_mode"))
    vertex_settings = normalize_vertex_settings(data.get("vertex_settings"))
    openai_auth_mode = normalize_openai_auth_mode(provider, data.get("openai_auth_mode"))
    model_name = data.get("model_name") or (
        DEFAULT_CODEX_OAUTH_MODEL if provider == "openai" and openai_auth_mode == "oauth_cli" else DEFAULT_MODELS[provider]
    )
    if provider == "openai" and openai_auth_mode == "oauth_cli":
        model_name, _ = normalize_codex_oauth_requested_model(model_name)

    analysis_mode = str(data.get("analysis_mode") or "translation_layer").strip() or "translation_layer"
    target_language = normalize_language_code(data.get("target_language") or DEFAULT_TARGET_LANGUAGE)
    requested_scope = data.get("translation_scope") or {}
    requested_documents = {
        str(path or "").strip()
        for path in (data.get("selected_files") or [])
        if str(path or "").strip()
    }

    best_match = find_best_translation_session(
        game_dir=Path(game_dir_str),
        analysis_mode=analysis_mode,
        target_language=target_language,
        provider=provider,
        gemini_auth_mode=gemini_auth_mode,
        vertex_settings=vertex_settings,
        openai_auth_mode=openai_auth_mode,
        model_name=model_name,
        requested_scope=requested_scope,
        requested_documents=requested_documents,
    )
    if not best_match:
        return jsonify({"error": "진행 중이거나 최근에 갱신된 번역 세션을 찾지 못했습니다."}), 404

    runtime = build_session_runtime_from_id(
        session_id=best_match["session_id"],
        analysis_mode=analysis_mode,
        target_language=target_language,
        game_dir=game_dir_str,
    )
    status_payload = build_translation_status_payload(runtime)
    return jsonify(
        {
            "session_id": runtime.session_id,
            "analysis_mode": runtime.analysis_mode,
            "target_language": runtime.target_language,
            "status_path": str(runtime.status_path),
            "checkpoint_path": str(runtime.checkpoint_path),
            "translation_log_dir": str(runtime.attempts_dir),
            "translation_scope": best_match["session_payload"].get("translation_scope") or {},
            "status": status_payload,
            "active": bool(best_match.get("active")),
            "match_score": int(best_match.get("match_score") or 0),
            "matched_documents": best_match["session_payload"].get("documents") or [],
        }
    )


@app.route("/translation_status", methods=["POST"])
def translation_status() -> Any:
    data = request.get_json(force=True) or {}
    session_id = str(data.get("session_id") or "").strip()
    if not session_id:
        return jsonify({"error": "session_id媛 ?꾩슂?⑸땲??"}), 400

    analysis_mode = str(data.get("analysis_mode") or "translation_layer").strip() or "translation_layer"
    target_language = normalize_language_code(data.get("target_language") or DEFAULT_TARGET_LANGUAGE)
    game_dir: Optional[str] = None
    game_exe_path = str(data.get("game_exe_path") or "").strip()
    if game_exe_path:
        game_dir = find_game_directory(game_exe_path)
        if not game_dir:
            return jsonify({"error": "'game' ?대뜑瑜?李얠? 紐삵뻽?듬땲??"}), 400

    runtime = build_session_runtime_from_id(
        session_id=session_id,
        analysis_mode=analysis_mode,
        target_language=target_language,
        game_dir=game_dir,
    )
    return jsonify(build_translation_status_payload(runtime))


@app.route("/generate_files_for_translation", methods=["POST"])
def handle_generate_files() -> Any:
    log_message("'/generate_files_for_translation' 요청 수신")
    data = request.get_json(force=True) or {}
    try:
        generated_files = build_generate_files_response(data)
        return jsonify(generated_files)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


@app.route("/openai_oauth_status", methods=["POST"])
def openai_oauth_status() -> Any:
    data = request.get_json(force=True) or {}
    command = (data.get("command") or DEFAULT_CODEX_CLI_COMMAND).strip()
    try:
        status = check_codex_cli(command=command, workdir=os.getcwd())
        return jsonify(status)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


@app.route("/openai_oauth_setup", methods=["POST"])
def openai_oauth_setup() -> Any:
    data = request.get_json(force=True) or {}
    command = (data.get("command") or DEFAULT_CODEX_CLI_COMMAND).strip()
    install_if_missing = bool(data.get("install_if_missing"))
    launch_login_flow = bool(data.get("launch_login"))
    try:
        status = ensure_openai_oauth_ready(
            command=command,
            workdir=os.getcwd(),
            install_if_missing=install_if_missing,
            launch_login_flow=launch_login_flow,
        )
        return jsonify(status)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


@app.route("/preview_character_tone", methods=["POST"])
def preview_character_tone() -> Any:
    log_message("'/preview_character_tone' ?? ??")
    data = request.get_json(force=True) or {}
    provider = (data.get("provider") or "gemini").lower()
    gemini_auth_mode = normalize_gemini_auth_mode(provider, data.get("gemini_auth_mode"))
    vertex_settings = normalize_vertex_settings(data.get("vertex_settings"))
    openai_auth_mode = normalize_openai_auth_mode(provider, data.get("openai_auth_mode"))
    openai_oauth_command = (data.get("openai_oauth_command") or DEFAULT_CODEX_CLI_COMMAND).strip()
    if provider not in SUPPORTED_PROVIDERS:
        return jsonify({"error": f"???? ?? ??????: {provider}"}), 400
    if provider == "openai" and openai_auth_mode == "api_key" and OpenAI is None:
        return jsonify({"error": "OpenAI ?????? ???? ?????."}), 500
    if provider == "gemini" and gemini_auth_mode == "api_key" and genai is None:
        return jsonify({"error": "Google Generative AI ?????? ???? ?????."}), 500
    if provider == "gemini" and gemini_auth_mode == "vertex_ai" and google_genai is None:
        return jsonify({"error": "google-genai ?????? ???? ?????."}), 500

    api_key = (data.get("api_key") or os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY") or "").strip()
    if provider == "gemini" and gemini_auth_mode == "api_key" and not api_key:
        return jsonify({"error": "API ?? ???? ?????."}), 400
    if provider == "gemini" and gemini_auth_mode == "vertex_ai" and not vertex_settings.get("project_id"):
        return jsonify({"error": "Vertex AI? ????? GCP ???? ID? ?????."}), 400
    if provider == "openai" and openai_auth_mode == "api_key" and not api_key:
        return jsonify({"error": "API ?? ???? ?????."}), 400

    speaker_id = (data.get("speaker_id") or "").strip()
    speaker_name = (data.get("speaker_name") or speaker_id or "Character").strip()
    sample_lines = [line for line in (data.get("sample_lines") or []) if (line or "").strip()]
    if not speaker_id or not sample_lines:
        return jsonify({"error": "?? ???? ??? ?? ?? ?? ??? ????."}), 400

    model_name = data.get("model_name") or (
        DEFAULT_CODEX_OAUTH_MODEL if provider == "openai" and openai_auth_mode == "oauth_cli" else DEFAULT_MODELS[provider]
    )
    model_warning = ""
    if provider == "openai" and openai_auth_mode == "oauth_cli":
        model_name, model_warning = normalize_codex_oauth_requested_model(model_name)
        if model_warning:
            log_message(f"Codex OAuth model normalized: {model_warning}")
    world_settings = data.get("world_settings") or {}
    character_profiles = data.get("character_profiles") or {}

    profile = character_profiles.get(speaker_id) or {
        "display_name": speaker_name,
    }
    character_profiles = {
        DEFAULT_FALLBACK_PERSONA_KEY: character_profiles.get(DEFAULT_FALLBACK_PERSONA_KEY) or {
            "display_name": "Default",
            "role": "UI/???/?? ???",
            "tone_preset_id": "ui_clean",
            "tone": CHARACTER_TONE_PRESETS["ui_clean"]["suggested_tone"],
            "notes": CHARACTER_TONE_PRESETS["ui_clean"]["suggested_notes"],
        },
        speaker_id: {
            "display_name": profile.get("display_name") or speaker_name,
            "tone_preset_id": profile.get("tone_preset_id") or "custom",
            "role": profile.get("role") or "",
            "tone": profile.get("tone") or "",
            "notes": profile.get("notes") or "",
        },
    }
    character_registry = {
        DEFAULT_FALLBACK_PERSONA_KEY: {"display_name": "Default"},
        speaker_id: {"display_name": profile.get("display_name") or speaker_name},
    }
    preview_items = build_preview_translation_items(speaker_id, speaker_name, sample_lines)
    prompts = build_batch_prompts(
        preview_items,
        world_settings,
        character_profiles,
        character_registry,
        include_adult_content=bool(data.get("include_adult_content")),
    )

    try:
        translated = perform_translation(
            provider=provider,
            api_key=api_key,
            model_name=model_name,
            system_prompt=prompts["system_prompt"],
            user_prompt=prompts["user_prompt"],
            gemini_auth_mode=gemini_auth_mode,
            vertex_settings=vertex_settings,
            openai_auth_mode=openai_auth_mode,
            openai_oauth_command=openai_oauth_command,
            workdir=os.getcwd(),
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500

    translated_lookup = build_translation_lookup_from_response(translated, preview_items)
    translated_count = sum(1 for item in preview_items if (translated_lookup.get(item.item_id) or "").strip())
    if translated_count == 0:
        return jsonify({"error": "샘플 미리 번역 응답에서 번역 텍스트를 읽지 못했습니다."}), 502

    preset_id = (profile.get("tone_preset_id") or "custom").strip() or "custom"
    preset = CHARACTER_TONE_PRESETS.get(preset_id, CHARACTER_TONE_PRESETS["custom"])
    return jsonify(
        {
            "speaker_id": speaker_id,
            "speaker_name": speaker_name,
            "provider": provider,
            "gemini_auth_mode": gemini_auth_mode,
            "openai_auth_mode": openai_auth_mode,
            "model_name": model_name,
            "model_warning": model_warning,
            "translated_count": translated_count,
            "tone_preset_id": preset_id,
            "tone_preset_name": preset.get("name") or "?? ??",
            "translations": [
                {
                    "source_text": item.source_text,
                    "translated_text": translated_lookup.get(item.item_id, ""),
                }
                for item in preview_items
            ],
        }
    )

@app.route("/load_editable_document", methods=["POST"])
def load_editable_document() -> Any:
    data = request.get_json(force=True) or {}
    file_relative_path = str(data.get("file_relative_path") or "").strip()
    if not file_relative_path:
        return jsonify({"error": "불러올 파일 경로가 비어 있습니다."}), 400

    payload = dict(data)
    payload["selected_files"] = [file_relative_path]
    payload["translation_rule"] = "force_all"

    try:
        translation_inputs = get_documents_for_translation(payload)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 400

    documents = translation_inputs.get("documents") or []
    if not documents:
        return jsonify({"error": "편집할 파일을 찾지 못했습니다."}), 404

    document = documents[0]
    output_context = None
    if translation_inputs.get("game_dir"):
        output_context = prepare_translation_output_context(
            game_dir=translation_inputs["game_dir"],
            analysis_mode=translation_inputs["analysis_mode"],
            target_language=translation_inputs["target_language"],
            publish_settings=data.get("publish_settings"),
        )

    return jsonify(
        {
            "analysis_mode": translation_inputs["analysis_mode"],
            "target_language": translation_inputs["target_language"],
            "document": build_document_editor_payload(document, output_context),
        }
    )


@app.route("/apply_manual_edits", methods=["POST"])
def apply_manual_edits() -> Any:
    data = request.get_json(force=True) or {}
    manual_edits = data.get("edits") or []
    if not isinstance(manual_edits, list) or not manual_edits:
        return jsonify({"error": "저장할 수동 수정 항목이 없습니다."}), 400

    selected_files = sorted(
        {
            str(entry.get("file_relative_path") or "").strip()
            for entry in manual_edits
            if str(entry.get("file_relative_path") or "").strip()
        }
    )
    if not selected_files:
        return jsonify({"error": "수동 수정 대상 파일을 식별하지 못했습니다."}), 400

    payload = dict(data)
    payload["selected_files"] = selected_files
    payload["translation_rule"] = "force_all"

    try:
        translation_inputs = get_documents_for_translation(payload)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 400

    if not translation_inputs.get("game_dir"):
        return jsonify({"error": "수동 편집 저장은 게임 경로 분석 모드에서만 지원합니다."}), 400

    output_context = prepare_translation_output_context(
        game_dir=translation_inputs["game_dir"],
        analysis_mode=translation_inputs["analysis_mode"],
        target_language=translation_inputs["target_language"],
        publish_settings=data.get("publish_settings"),
    )
    edit_map: Dict[str, Dict[str, str]] = {}
    for entry in manual_edits:
        file_relative_path = str(entry.get("file_relative_path") or "").strip()
        item_id = str(entry.get("item_id") or "").strip()
        translated_text = str(entry.get("text") or "").strip()
        if not file_relative_path or not item_id or not translated_text:
            continue
        edit_map.setdefault(file_relative_path, {})[item_id] = translated_text

    if not edit_map:
        return jsonify({"error": "비어 있지 않은 번역문이 필요합니다."}), 400

    results: List[Dict[str, Any]] = []
    saved_items: List[Dict[str, Any]] = []
    selected_documents = [
        document
        for document in (translation_inputs.get("documents") or [])
        if document.file_relative_path in edit_map
    ]
    if not selected_documents:
        return jsonify({"error": "수동 수정 대상 문서를 찾지 못했습니다."}), 404

    for document in selected_documents:
        document_edits = edit_map.get(document.file_relative_path) or {}
        translated_lookup = build_effective_translation_lookup(document)
        applied_count = 0
        for item in document.items:
            next_text = document_edits.get(item.item_id)
            if not next_text:
                continue
            translated_lookup[item.item_id] = next_text
            saved_items.append(
                {
                    "item_id": item.item_id,
                    "file_relative_path": item.file_relative_path,
                    "speaker_id": item.speaker_id,
                    "speaker_name": item.speaker_name,
                    "line_number": item.line_number,
                    "text": next_text,
                    "previous_status": item.translation_status,
                    "new_status": "workbench_translated",
                }
            )
            applied_count += 1

        if applied_count == 0:
            continue
        results.append(write_document_result_to_disk(document, translated_lookup, output_context))

    if not results:
        return jsonify({"error": "적용할 수동 수정 항목이 없습니다."}), 400

    sync_payload = sync_translation_support_files(
        documents=selected_documents,
        skipped_adult_items=[],
        failed_items=[],
        output_context=output_context,
    )
    return jsonify(
        {
            "analysis_mode": translation_inputs["analysis_mode"],
            "target_language": translation_inputs["target_language"],
            "applied_item_count": len(saved_items),
            "saved_items": saved_items,
            "results": results,
            "adult_review_path": sync_payload["adult_review_path"],
            "publish_bundle": sync_payload["publish_bundle"],
        }
    )


@app.route("/translate", methods=["POST"])
def handle_translation() -> Any:
    log_message("'/translate' ?? ??")
    data = request.get_json(force=True) or {}
    provider = (data.get("provider") or "gemini").lower()
    gemini_auth_mode = normalize_gemini_auth_mode(provider, data.get("gemini_auth_mode"))
    vertex_settings = normalize_vertex_settings(data.get("vertex_settings"))
    openai_auth_mode = normalize_openai_auth_mode(provider, data.get("openai_auth_mode"))
    openai_oauth_command = (data.get("openai_oauth_command") or DEFAULT_CODEX_CLI_COMMAND).strip()
    if provider not in SUPPORTED_PROVIDERS:
        return jsonify({"error": f"???? ?? ??????: {provider}"}), 400
    if provider == "openai" and openai_auth_mode == "api_key" and OpenAI is None:
        return jsonify({"error": "OpenAI ?????? ???? ?????."}), 500
    if provider == "gemini" and gemini_auth_mode == "api_key" and genai is None:
        return jsonify({"error": "Google Generative AI ?????? ???? ?????."}), 500
    if provider == "gemini" and gemini_auth_mode == "vertex_ai" and google_genai is None:
        return jsonify({"error": "google-genai ?????? ???? ?????."}), 500

    api_key = (data.get("api_key") or os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY") or "").strip()
    if provider == "gemini" and gemini_auth_mode == "api_key" and not api_key:
        return jsonify({"error": "API ?? ???? ?????."}), 400
    if provider == "gemini" and gemini_auth_mode == "vertex_ai" and not vertex_settings.get("project_id"):
        return jsonify({"error": "Vertex AI? ????? GCP ???? ID? ?????."}), 400
    if provider == "openai" and openai_auth_mode == "api_key" and not api_key:
        return jsonify({"error": "API ?? ???? ?????."}), 400

    model_name = data.get("model_name") or (
        DEFAULT_CODEX_OAUTH_MODEL if provider == "openai" and openai_auth_mode == "oauth_cli" else DEFAULT_MODELS[provider]
    )
    model_warning = ""
    if provider == "openai" and openai_auth_mode == "oauth_cli":
        model_name, model_warning = normalize_codex_oauth_requested_model(model_name)
        if model_warning:
            log_message(f"Codex OAuth model normalized: {model_warning}")
    batch_size = int(data.get("batch_size") or DEFAULT_BATCH_SIZE_BY_PROVIDER.get(provider, 12))
    api_delay = float(data.get("api_delay") if data.get("api_delay") not in (None, "") else DEFAULT_API_DELAY_BY_PROVIDER.get(provider, 0.3))
    if provider == "openai" and openai_auth_mode == "oauth_cli":
        api_delay = 0.0
    include_adult_content = bool(data.get("include_adult_content"))
    character_profiles = data.get("character_profiles") or {}
    world_settings = data.get("world_settings") or {}
    publish_settings = data.get("publish_settings") or {}
    session_runtime: Optional[TranslationSessionRuntime] = None
    output_context: Optional[TranslationOutputContext] = None

    try:
        translation_inputs = get_documents_for_translation(data)
        documents = translation_inputs["documents"]
        if not documents:
            scope = translation_inputs.get("translation_scope") or {}
            translation_rule = (translation_inputs.get("translation_scope") or {}).get("translation_rule") or "missing_only"
            if scope.get("mode") == "selected_items":
                message = "?? ???? ?? ??? ?? ?? ??? ????."
            elif translation_rule == "retranslate_existing":
                message = "?? ???? ???? ?? ?? ??? ????."
            elif translation_rule == "missing_only":
                message = "?? ???? ??? ??? ????."
            else:
                message = "?? ??? ??? ?? ?????."
            return jsonify({"error": message, "translation_scope": translation_inputs.get("translation_scope") or {}}), 400

        document_write_callback = None
        if translation_inputs["game_dir"]:
            output_context = prepare_translation_output_context(
                game_dir=translation_inputs["game_dir"],
                analysis_mode=translation_inputs["analysis_mode"],
                target_language=translation_inputs["target_language"],
                publish_settings=publish_settings,
            )
            sync_translation_support_files(
                documents=documents,
                skipped_adult_items=[],
                failed_items=[],
                output_context=output_context,
            )

            def document_write_callback(
                document: AnalyzedFile,
                translated_lookup: Dict[str, str],
                skipped_adult_items: List[Dict[str, Any]],
                failed_items: List[Dict[str, Any]],
            ) -> Dict[str, Any]:
                result = write_document_result_to_disk(document, translated_lookup, output_context)
                sync_translation_support_files(
                    documents=documents,
                    skipped_adult_items=skipped_adult_items,
                    failed_items=failed_items,
                    output_context=output_context,
                )
                return result

        session_runtime = build_translation_session_runtime(
            documents=documents,
            provider=provider,
            gemini_auth_mode=gemini_auth_mode,
            vertex_settings=vertex_settings,
            openai_auth_mode=openai_auth_mode,
            model_name=model_name,
            analysis_mode=translation_inputs["analysis_mode"],
            target_language=translation_inputs["target_language"],
            include_adult_content=include_adult_content,
            world_settings=world_settings,
            character_profiles=character_profiles,
            game_dir=translation_inputs["game_dir"],
            translation_scope=translation_inputs.get("translation_scope"),
        )

        translation_payload = translate_documents(
            documents=documents,
            provider=provider,
            api_key=api_key,
            model_name=model_name,
            gemini_auth_mode=gemini_auth_mode,
            vertex_settings=vertex_settings,
            character_profiles=character_profiles,
            world_settings=world_settings,
            character_registry=translation_inputs["character_registry"],
            batch_size=batch_size,
            api_delay=api_delay,
            include_adult_content=include_adult_content,
            openai_auth_mode=openai_auth_mode,
            openai_oauth_command=openai_oauth_command,
            workdir=os.getcwd(),
            runtime=session_runtime,
            document_write_callback=document_write_callback,
            translation_scope=translation_inputs.get("translation_scope"),
        )

        if translation_inputs["game_dir"]:
            write_result = write_results_to_disk(
                documents=documents,
                translated_lookup=translation_payload["translated_lookup"],
                game_dir=translation_inputs["game_dir"],
                analysis_mode=translation_inputs["analysis_mode"],
                target_language=translation_inputs["target_language"],
                skipped_adult_items=translation_payload["skipped_adult_items"],
                failed_items=translation_payload["failed_items"],
                publish_settings=publish_settings,
            )
            return jsonify(
                {
                    "provider": provider,
                    "gemini_auth_mode": gemini_auth_mode,
                    "openai_auth_mode": openai_auth_mode,
                    "model_name": model_name,
                    "model_warning": model_warning,
                    "analysis_mode": translation_inputs["analysis_mode"],
                    "adult_review_path": write_result["adult_review_path"],
                    "skipped_adult_count": len(translation_payload["skipped_adult_items"]),
                    "failed_item_count": len(translation_payload["failed_items"]),
                    "translation_session": translation_payload["session"],
                    "publish_bundle": write_result["publish_bundle"],
                    "results": write_result["results"],
                    "completed_documents": translation_payload["completed_documents"],
                    "optimization": translation_payload["optimization"],
                    "translation_scope": translation_payload["translation_scope"],
                    "halted": translation_payload["halted"],
                    "halt_reason": translation_payload["halt_reason"],
                }
            )

        results = []
        for document in documents:
            output_lines = document.raw_content.splitlines()
            translated_count = 0
            skipped_count = 0
            failed_count = 0
            for item in document.items:
                if item.item_id not in translation_payload["translated_lookup"]:
                    if item.adult:
                        skipped_count += 1
                    else:
                        failed_count += 1
                    continue
                replacement_source = translation_payload["translated_lookup"][item.item_id]
                replacement = normalize_translated_text_for_item(
                    source_text=item.source_text,
                    translated_text=replacement_source,
                    block_id=item.block_id,
                )
                output_lines[item.target_line_index] = f'{item.before}{replacement}"{item.after}'
                translated_count += 1

            results.append(
                {
                    "original_filename": document.file_name,
                    "file_relative_path": document.file_relative_path,
                    "translated_filename": f"{Path(document.file_name).stem}_translated{Path(document.file_name).suffix}",
                    "translated_content": "\n".join(output_lines) + "\n",
                    "translated_count": translated_count,
                    "skipped_adult_count": skipped_count,
                    "failed_item_count": failed_count,
                    "status": "success" if failed_count == 0 else "partial",
                }
            )

        return jsonify(
            {
                "provider": provider,
                "gemini_auth_mode": gemini_auth_mode,
                "openai_auth_mode": openai_auth_mode,
                "model_name": model_name,
                "model_warning": model_warning,
                "analysis_mode": translation_inputs["analysis_mode"],
                "skipped_adult_count": len(translation_payload["skipped_adult_items"]),
                "failed_item_count": len(translation_payload["failed_items"]),
                "translation_session": translation_payload["session"],
                "results": results,
                "completed_documents": translation_payload["completed_documents"],
                "optimization": translation_payload["optimization"],
                "translation_scope": translation_payload["translation_scope"],
                "halted": translation_payload["halted"],
                "halt_reason": translation_payload["halt_reason"],
                "adult_review": {
                    "skipped_adult_items": translation_payload["skipped_adult_items"],
                    "failed_items": translation_payload["failed_items"],
                },
            }
        )
    except Exception as exc:  # noqa: BLE001
        log_message(f"ERROR: {exc}")
        payload = {"error": str(exc)}
        if session_runtime:
            payload["translation_session"] = {
                "session_id": session_runtime.session_id,
                "checkpoint_path": str(session_runtime.checkpoint_path),
                "translation_log_dir": str(session_runtime.attempts_dir),
                "status_path": str(session_runtime.status_path),
            }
        return jsonify(payload), 500

@app.route("/search_dialogue", methods=["POST"])
def search_dialogue():
    """번역 파일에서 영어/한국어 대사를 검색합니다."""
    try:
        payload = request.get_json(force=True) or {}
        query = (payload.get("query") or "").strip()
        game_exe_path = payload.get("game_exe_path") or game_exe_path_from_startup
        max_results = min(int(payload.get("max_results") or 50), 200)

        if not query:
            return jsonify({"error": "query가 필요합니다."}), 400
        if not game_exe_path:
            return jsonify({"error": "game_exe_path가 필요합니다."}), 400

        game_dir_str = find_game_directory(game_exe_path)
        if not game_dir_str:
            return jsonify({"error": "game 폴더를 찾지 못했습니다."}), 400

        game_dir = Path(game_dir_str)
        tl_root = game_dir / "tl"
        source_root = get_source_stage_root(game_dir, "ko")

        query_lower = query.lower()
        results = []

        # translate 블록 파싱: comment 라인(영어) + 번역 라인(한국어)
        BLOCK_LABEL_RE = re.compile(r"^\s*translate\s+\S+\s+(\S+)\s*:\s*$")
        COMMENT_RE = re.compile(r'^\s*#\s*(?:[a-zA-Z_]\w*\s+)?"(.*)"')
        TRANS_LINE_RE_SEARCH = re.compile(r'^\s*(?:([a-zA-Z_]\w*)\s+)?"(.*)"')

        def search_tl_file(rpy_path: Path, lang_folder: str) -> None:
            try:
                lines = rpy_path.read_text(encoding="utf-8", errors="replace").splitlines()
            except Exception:
                return
            i = 0
            while i < len(lines):
                if BLOCK_LABEL_RE.match(lines[i]):
                    block_start = i
                    en_text = ""
                    ko_text = ""
                    j = i + 1
                    while j < len(lines):
                        if BLOCK_LABEL_RE.match(lines[j]):
                            break
                        cm = COMMENT_RE.match(lines[j])
                        if cm and not en_text:
                            en_text = cm.group(1)
                        elif lines[j].strip() and not lines[j].strip().startswith("#") and not ko_text:
                            tm = TRANS_LINE_RE_SEARCH.match(lines[j])
                            if tm:
                                ko_text = tm.group(2)
                        j += 1
                    if en_text and (query_lower in en_text.lower() or query_lower in ko_text.lower()):
                        results.append({
                            "file": rpy_path.name,
                            "lang": lang_folder,
                            "line": block_start + 1,
                            "en": en_text,
                            "ko": ko_text,
                        })
                        if len(results) >= max_results:
                            return
                    i = j
                else:
                    # strings 형식 (old/new)
                    if lines[i].strip().startswith('old "'):
                        old_text = lines[i].strip()[5:-1]
                        new_text = ""
                        if i + 1 < len(lines) and lines[i + 1].strip().startswith('new "'):
                            new_text = lines[i + 1].strip()[5:-1]
                        if query_lower in old_text.lower() or query_lower in new_text.lower():
                            results.append({
                                "file": rpy_path.name,
                                "lang": lang_folder,
                                "line": i + 1,
                                "en": old_text,
                                "ko": new_text,
                            })
                            if len(results) >= max_results:
                                return
                    i += 1

        # tl 폴더 내 언어 폴더들을 검색
        searched_files = 0
        if tl_root.is_dir():
            for lang_dir in sorted(tl_root.iterdir()):
                if not lang_dir.is_dir():
                    continue
                for rpy_file in sorted(lang_dir.glob("*.rpy")):
                    search_tl_file(rpy_file, lang_dir.name)
                    searched_files += 1
                    if len(results) >= max_results:
                        break
                if len(results) >= max_results:
                    break

        return jsonify({
            "query": query,
            "result_count": len(results),
            "searched_files": searched_files,
            "results": results,
        })
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    if len(sys.argv) > 1:
        game_exe_path_from_startup = sys.argv[1]
        log_message(f"시작 인자로 게임 경로 수신: {game_exe_path_from_startup}")

    try:
        backend_port = int(str(os.environ.get("RENPY_TRANSLATOR_PORT", "5000")).strip() or "5000")
    except (TypeError, ValueError):
        backend_port = 5000
    log_message(f"Flask 서버 시작 중... (http://127.0.0.1:{backend_port})")
    debug_mode = str(os.environ.get("RENPY_TRANSLATOR_DEBUG", "")).strip().lower() in {"1", "true", "yes", "on"}
    app.run(
        debug=debug_mode,
        use_reloader=debug_mode,
        threaded=True,
        host="0.0.0.0",
        port=backend_port,
    )
