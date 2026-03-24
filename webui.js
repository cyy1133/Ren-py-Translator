const BACKEND_URL = "http://127.0.0.1:5000";
const PROGRESS_BACKEND_URL = "http://127.0.0.1:5001";
const MODEL_SUGGESTIONS = {
    gemini: [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.1-pro-preview",
    ],
    openai_api_key: ["gpt-5-mini", "gpt-5", "gpt-4.1-mini"],
    openai_oauth_cli: ["auto-codex-economy", "auto-codex-balanced", "gpt-5.1-codex", "gpt-5-mini", "gpt-5-codex"],
};
const DEFAULT_OPENAI_OAUTH_COMMAND = /windows/i.test(navigator.userAgent)
    ? "codex_npx.cmd {args}"
    : "codex {args}";
const DEFAULT_RUNTIME_SETTINGS = {
    gemini: { batchSize: 16, apiDelay: 0.2 },
    openai_api_key: { batchSize: 12, apiDelay: 0.3 },
    openai_oauth_cli: { batchSize: 12, apiDelay: 0 },
};
const API_KEY_STORAGE_PREFIX = "renpy-workbench-api-key:v1";
const TRANSLATION_PRESETS = [
    {
        id: "gemini_quality",
        name: "추천 품질",
        badge: "Recommended",
        description: "가장 안정적인 번역 품질과 비용 균형. 현재 기본 권장값입니다.",
        provider: "gemini",
        openaiAuthMode: "api_key",
        modelName: "gemini-2.5-flash",
        batchSize: 16,
        apiDelay: 0.2,
    },
    {
        id: "gemini_budget",
        name: "저비용 모드",
        badge: "Budget",
        description: "긴 작업을 더 싸게 돌리는 모드. 속도는 빠르지만 문체 밀도는 조금 낮아집니다.",
        provider: "gemini",
        openaiAuthMode: "api_key",
        modelName: "gemini-2.5-flash-lite",
        batchSize: 16,
        apiDelay: 0.6,
    },
    {
        id: "codex_style_lab",
        name: "문체 실험",
        badge: "Style",
        description: "문장 리듬과 분위기 실험용. 비용과 속도는 더 무겁지만 문체 튜닝용으로 좋습니다.",
        provider: "openai",
        openaiAuthMode: "oauth_cli",
        modelName: "gpt-5.1-codex",
        batchSize: 8,
        apiDelay: 0,
    },
];
const DEFAULT_TRANSLATION_PRESET_ID = "gemini_quality";
const DEFAULT_FONT_BROWSER_SAMPLE_TEXT = "가나다라마바사 ABC 123";
const FONT_BROWSER_PAGE_SIZE = 18;
const CHARACTER_TONE_PRESETS = [
    {
        id: "custom",
        name: "직접 입력",
        description: "드롭다운 자동 지침 없이 tone / notes 내용을 그대로 프롬프트에 넣습니다.",
        suggestedTone: "",
        suggestedNotes: "",
    },
    {
        id: "ui_clean",
        name: "UI / 시스템",
        description: "버튼, 선택지, 시스템 문구를 짧고 명확한 인터페이스 문체로 유지합니다.",
        suggestedTone: "짧고 안정적인 UI 문체, 군더더기 없는 안내형 톤",
        suggestedNotes: "메뉴/버튼/알림 문구는 과장 없이 선명하게 유지",
    },
    {
        id: "neutral_conversational",
        name: "중립 구어체",
        description: "대부분의 일반 캐릭터에 맞는 자연스러운 기본 대화체입니다.",
        suggestedTone: "상황에 맞춘 자연스러운 구어체, 과한 현대 유행어는 자제",
        suggestedNotes: "관계어와 호칭만 일관되게 유지하고 나머지는 문맥에 맞게 부드럽게 조정",
    },
    {
        id: "warm_gentle",
        name: "다정하고 부드럽게",
        description: "배려심 있고 온화한 캐릭터용 말투입니다.",
        suggestedTone: "부드럽고 다정한 구어체, 상대를 배려하는 완곡한 말투",
        suggestedNotes: "정서적 온기를 살리고 공격적인 어휘는 피함",
    },
    {
        id: "bright_playful",
        name: "밝고 경쾌하게",
        description: "활기 있고 감정 표현이 분명한 캐릭터용 톤입니다.",
        suggestedTone: "밝고 리듬감 있는 구어체, 감탄과 반응이 선명한 말투",
        suggestedNotes: "장난기와 추진력이 보이면 살리고 지나친 유치함은 피함",
    },
    {
        id: "formal_period",
        name: "격식 / 시대극",
        description: "약간 고전적이고 예의 바른 시대극 톤에 맞춥니다.",
        suggestedTone: "격식을 갖춘 문어 섞인 대화체, 약간 고전적인 어휘",
        suggestedNotes: "시대감은 유지하되 지나친 한문투나 번역투는 피함",
    },
    {
        id: "rustic_plain",
        name: "소박한 생활 구어",
        description: "촌락, 해안, 생활감 있는 소박한 말투에 맞춥니다.",
        suggestedTone: "생활감 있는 소박한 구어체, 약한 지역색을 품은 말투",
        suggestedNotes: "지역색은 과장하지 말고 담백하게 남김",
    },
    {
        id: "cool_blunt",
        name: "차갑고 직설적",
        description: "무심하거나 딱 잘라 말하는 캐릭터용입니다.",
        suggestedTone: "짧고 직설적인 말투, 감정 표현을 절제한 구어체",
        suggestedNotes: "불필요하게 부드럽게 만들지 말고 선을 긋는 느낌 유지",
    },
    {
        id: "seductive_teasing",
        name: "유혹적 / 장난스럽게",
        description: "로맨스, 유혹, 성인 뉘앙스가 섞인 캐릭터에 맞춥니다.",
        suggestedTone: "유혹적이고 여유 있는 말투, 장난스러운 거리감",
        suggestedNotes: "성적 뉘앙스나 긴장감을 완화하지 말고 자연스럽게 유지",
    },
    {
        id: "literary_narration",
        name: "문학적 내레이션",
        description: "지문과 내레이션을 매끄러운 서술체로 유지합니다.",
        suggestedTone: "묘사 중심의 서술체, 장면 분위기와 감정선을 살리는 문장",
        suggestedNotes: "호흡이 끊기지 않도록 문장을 다듬고 태그/포맷은 그대로 유지",
    },
];

const CHARACTER_TONE_PRESET_COMPARISON_MAP = {
    custom: ["neutral_conversational", "warm_gentle", "formal_period"],
    ui_clean: ["neutral_conversational", "formal_period", "cool_blunt"],
    neutral_conversational: ["warm_gentle", "formal_period", "bright_playful"],
    warm_gentle: ["neutral_conversational", "formal_period", "bright_playful"],
    bright_playful: ["neutral_conversational", "warm_gentle", "cool_blunt"],
    formal_period: ["neutral_conversational", "warm_gentle", "rustic_plain"],
    rustic_plain: ["neutral_conversational", "warm_gentle", "formal_period"],
    cool_blunt: ["neutral_conversational", "formal_period", "bright_playful"],
    seductive_teasing: ["warm_gentle", "neutral_conversational", "formal_period"],
    literary_narration: ["formal_period", "neutral_conversational", "warm_gentle"],
};
const CHARACTER_TONE_PRESET_FALLBACKS = [
    "neutral_conversational",
    "warm_gentle",
    "formal_period",
    "bright_playful",
    "rustic_plain",
    "cool_blunt",
    "seductive_teasing",
];

const state = {
    uploadedFiles: [],
    analysis: null,
    selectedFiles: new Set(),
    fileSelectionCustomized: false,
    fileSelectionAnalysisKey: "",
    characterProfiles: {},
    activeTab: "overview",
    selectedCharacterId: null,
    characterFilter: "",
    oauthStatusPollHandle: null,
    selectedFontPresetId: "",
    selectedTranslationPresetId: DEFAULT_TRANSLATION_PRESET_ID,
    systemFonts: [],
    systemFontsLoaded: false,
    systemFontsLoading: false,
    fontBrowserQuery: "",
    fontBrowserTarget: "dialogue_font",
    fontBrowserPage: 0,
    tonePreviewByCharacter: {},
    tonePreviewLoadingSpeakerId: null,
    selectedIssueCandidateIds: new Set(),
    selectedAdultQueueIds: new Set(),
    issueCandidateSearchQuery: "",
    editorDocument: null,
    editorFilePath: "",
    editorSelectedItemId: null,
    editorStatusFilter: "all",
    editorSearchQuery: "",
    editorDrafts: {},
    translationProgressPollHandle: null,
    translationProgressSession: null,
    translationProgressStatus: null,
    translationProgressRequestActive: false,
    translationProgressBusy: false,
    translationProgressFailureCount: 0,
    translationProgressLastLogKey: "",
};


function buildAnalysisFileSelectionKey(analysis) {
    const filePaths = (analysis?.files || [])
        .map((file) => file.file_relative_path || "")
        .filter(Boolean)
        .sort()
        .join("|");
    return [
        analysis?.analysis_mode || "",
        analysis?.source_label || "",
        analysis?.target_language || "",
        analysis?.game_dir || "",
        filePaths,
    ].join("::");
}


function updateFileSelectionState(availableFilePaths = null) {
    const filePaths = Array.isArray(availableFilePaths)
        ? availableFilePaths
        : (state.analysis?.files || []).map((file) => file.file_relative_path);
    const normalized = filePaths.filter((filePath) => state.selectedFiles.has(filePath));
    state.selectedFiles = new Set(normalized);
    state.fileSelectionCustomized = normalized.length > 0 && normalized.length < filePaths.length;
    return normalized;
}


function applyAnalysisFileSelection(analysis, options = {}) {
    const availableFilePaths = (analysis?.files || []).map((file) => file.file_relative_path);
    const selectionMode = options.selectionMode || "reset";
    if (!availableFilePaths.length) {
        state.selectedFiles = new Set();
        state.fileSelectionCustomized = false;
        state.fileSelectionAnalysisKey = buildAnalysisFileSelectionKey(analysis);
        return availableFilePaths;
    }

    if (selectionMode === "preserve") {
        const preservedSelection = availableFilePaths.filter((filePath) => state.selectedFiles.has(filePath));
        state.selectedFiles = new Set(preservedSelection.length ? preservedSelection : availableFilePaths);
    } else {
        state.selectedFiles = new Set(availableFilePaths);
    }

    updateFileSelectionState(availableFilePaths);
    state.fileSelectionAnalysisKey = buildAnalysisFileSelectionKey(analysis);
    return availableFilePaths;
}

const dom = {
    providerSelect: document.getElementById("providerSelect"),
    geminiAuthField: document.getElementById("geminiAuthField"),
    geminiAuthModeSelect: document.getElementById("geminiAuthModeSelect"),
    openaiAuthField: document.getElementById("openaiAuthField"),
    openaiAuthModeSelect: document.getElementById("openaiAuthModeSelect"),
    apiKeyField: document.getElementById("apiKeyField"),
    apiKeyInput: document.getElementById("apiKeyInput"),
    saveApiKeyButton: document.getElementById("saveApiKeyButton"),
    loadApiKeyButton: document.getElementById("loadApiKeyButton"),
    clearApiKeyButton: document.getElementById("clearApiKeyButton"),
    apiKeyStorageStatus: document.getElementById("apiKeyStorageStatus"),
    geminiVertexPanel: document.getElementById("geminiVertexPanel"),
    vertexProjectIdInput: document.getElementById("vertexProjectIdInput"),
    vertexLocationInput: document.getElementById("vertexLocationInput"),
    vertexCredentialsPathInput: document.getElementById("vertexCredentialsPathInput"),
    loadVertexCredentialsFileButton: document.getElementById("loadVertexCredentialsFileButton"),
    clearVertexCredentialsButton: document.getElementById("clearVertexCredentialsButton"),
    vertexCredentialsFileInput: document.getElementById("vertexCredentialsFileInput"),
    vertexCredentialsJsonInput: document.getElementById("vertexCredentialsJsonInput"),
    vertexCredentialsStatus: document.getElementById("vertexCredentialsStatus"),
    openaiOAuthPanel: document.getElementById("openaiOAuthPanel"),
    openaiOAuthCommandInput: document.getElementById("openaiOAuthCommandInput"),
    setupOpenAIOAuthButton: document.getElementById("setupOpenAIOAuthButton"),
    checkOpenAIOAuthButton: document.getElementById("checkOpenAIOAuthButton"),
    openaiOAuthStatus: document.getElementById("openaiOAuthStatus"),
    modelInput: document.getElementById("modelInput"),
    modelSuggestions: document.getElementById("modelSuggestions"),
    translationPresetGrid: document.getElementById("translationPresetGrid"),
    translationPresetSummary: document.getElementById("translationPresetSummary"),
    targetLanguageInput: document.getElementById("targetLanguageInput"),
    batchSizeInput: document.getElementById("batchSizeInput"),
    apiDelayInput: document.getElementById("apiDelayInput"),
    includeAdultCheckbox: document.getElementById("includeAdultCheckbox"),
    gamePathInput: document.getElementById("gamePathInput"),
    pickExeButton: document.getElementById("pickExeButton"),
    generateTemplateButton: document.getElementById("generateTemplateButton"),
    analyzeGameButton: document.getElementById("analyzeGameButton"),
    repairOutputsButton: document.getElementById("repairOutputsButton"),
    uploadInput: document.getElementById("uploadInput"),
    uploadList: document.getElementById("uploadList"),
    analyzeUploadsButton: document.getElementById("analyzeUploadsButton"),
    clearUploadsButton: document.getElementById("clearUploadsButton"),
    analysisModeLabel: document.getElementById("analysisModeLabel"),
    summaryFiles: document.getElementById("summaryFiles"),
    summaryItems: document.getElementById("summaryItems"),
    summaryCharacters: document.getElementById("summaryCharacters"),
    summaryAdult: document.getElementById("summaryAdult"),
    summaryUntranslated: document.getElementById("summaryUntranslated"),
    summaryGameTranslated: document.getElementById("summaryGameTranslated"),
    summaryWorkbenchTranslated: document.getElementById("summaryWorkbenchTranslated"),
    tabButtons: Array.from(document.querySelectorAll(".tab-button")),
    tabPanels: Array.from(document.querySelectorAll(".tab-panel")),
    worldInferenceText: document.getElementById("worldInferenceText"),
    toneInferenceText: document.getElementById("toneInferenceText"),
    styleInferenceText: document.getElementById("styleInferenceText"),
    dialoguePreviewList: document.getElementById("dialoguePreviewList"),
    fileTable: document.getElementById("fileTable"),
    worldDescriptionInput: document.getElementById("worldDescriptionInput"),
    toneNotesInput: document.getElementById("toneNotesInput"),
    styleRulesInput: document.getElementById("styleRulesInput"),
    protectedTermsInput: document.getElementById("protectedTermsInput"),
    glossaryTable: document.getElementById("glossaryTable"),
    addGlossaryRowButton: document.getElementById("addGlossaryRowButton"),
    publishEnabledCheckbox: document.getElementById("publishEnabledCheckbox"),
    publishLanguageCodeInput: document.getElementById("publishLanguageCodeInput"),
    publishDisplayNameInput: document.getElementById("publishDisplayNameInput"),
    publishGuiLanguageInput: document.getElementById("publishGuiLanguageInput"),
    autoAdjustFontSizesCheckbox: document.getElementById("autoAdjustFontSizesCheckbox"),
    fontPresetSelect: document.getElementById("fontPresetSelect"),
    applyFontPresetButton: document.getElementById("applyFontPresetButton"),
    applyPublishFontsButton: document.getElementById("applyPublishFontsButton"),
    dialogueFontSelect: document.getElementById("dialogueFontSelect"),
    nameFontSelect: document.getElementById("nameFontSelect"),
    optionsFontSelect: document.getElementById("optionsFontSelect"),
    interfaceFontSelect: document.getElementById("interfaceFontSelect"),
    systemFontSelect: document.getElementById("systemFontSelect"),
    glyphFontSelect: document.getElementById("glyphFontSelect"),
    dialogueScaleInput: document.getElementById("dialogueScaleInput"),
    nameScaleInput: document.getElementById("nameScaleInput"),
    optionsScaleInput: document.getElementById("optionsScaleInput"),
    interfaceScaleInput: document.getElementById("interfaceScaleInput"),
    publishBaselineSummary: document.getElementById("publishBaselineSummary"),
    loadSystemFontsButton: document.getElementById("loadSystemFontsButton"),
    fontBrowserTargetSelect: document.getElementById("fontBrowserTargetSelect"),
    fontBrowserSearchInput: document.getElementById("fontBrowserSearchInput"),
    applyFirstFilteredFontButton: document.getElementById("applyFirstFilteredFontButton"),
    fontBrowserSampleTextInput: document.getElementById("fontBrowserSampleTextInput"),
    fontBrowserStatus: document.getElementById("fontBrowserStatus"),
    fontBrowserPageInfo: document.getElementById("fontBrowserPageInfo"),
    fontBrowserPrevButton: document.getElementById("fontBrowserPrevButton"),
    fontBrowserNextButton: document.getElementById("fontBrowserNextButton"),
    currentFontPreviewGrid: document.getElementById("currentFontPreviewGrid"),
    systemFontGallery: document.getElementById("systemFontGallery"),
    styleOverrideTable: document.getElementById("styleOverrideTable"),
    addStyleOverrideRowButton: document.getElementById("addStyleOverrideRowButton"),
    fontSuggestionList: document.getElementById("fontSuggestionList"),
    styleSuggestionList: document.getElementById("styleSuggestionList"),
    issueCandidateSearchInput: document.getElementById("issueCandidateSearchInput"),
    selectVisibleIssueCandidatesButton: document.getElementById("selectVisibleIssueCandidatesButton"),
    clearIssueCandidateSelectionButton: document.getElementById("clearIssueCandidateSelectionButton"),
    retranslateIssueCandidatesButton: document.getElementById("retranslateIssueCandidatesButton"),
    issueCandidateSummary: document.getElementById("issueCandidateSummary"),
    issueCandidateQueue: document.getElementById("issueCandidateQueue"),
    adultQueueSummary: document.getElementById("adultQueueSummary"),
    selectVisibleAdultQueueButton: document.getElementById("selectVisibleAdultQueueButton"),
    clearAdultQueueSelectionButton: document.getElementById("clearAdultQueueSelectionButton"),
    translateAdultQueueButton: document.getElementById("translateAdultQueueButton"),
    adultQueue: document.getElementById("adultQueue"),
    editorFileSelect: document.getElementById("editorFileSelect"),
    editorStatusFilter: document.getElementById("editorStatusFilter"),
    editorSearchInput: document.getElementById("editorSearchInput"),
    loadEditorButton: document.getElementById("loadEditorButton"),
    saveEditorButton: document.getElementById("saveEditorButton"),
    editorSummary: document.getElementById("editorSummary"),
    documentEditor: document.getElementById("documentEditor"),
    characterGrid: document.getElementById("characterGrid"),
    translationRuleSelect: document.getElementById("translationRuleSelect"),
    translateButton: document.getElementById("translateButton"),
    attachProgressButton: document.getElementById("attachProgressButton"),
    translationHint: document.getElementById("translationHint"),
    translationProgressPanel: document.getElementById("translationProgressPanel"),
    resultsPanel: document.getElementById("resultsPanel"),
    logPanel: document.getElementById("logPanel"),
    saveProfileButton: document.getElementById("saveProfileButton"),
    loadProfileButton: document.getElementById("loadProfileButton"),
    profileFileInput: document.getElementById("profileFileInput"),
};


function addLog(message, type = "info") {
    const entry = document.createElement("div");
    entry.className = `log-entry ${type}`;
    const timestamp = new Date().toLocaleTimeString("ko-KR", { hour12: false });
    entry.textContent = `[${timestamp}] ${message}`;
    dom.logPanel.prepend(entry);
}


async function apiGet(path) {
    const response = await fetch(`${BACKEND_URL}${path}`);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data?.error || `서버 오류 (${response.status})`);
    }
    return data;
}


async function apiPostWithBase(baseUrl, path, payload) {
    let response;
    try {
        response = await fetch(`${baseUrl}${path}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
    } catch (error) {
        throw new Error(`백엔드 요청 실패: ${error.message}`);
    }

    const rawText = await response.text();
    let data = {};
    if (rawText) {
        try {
            data = JSON.parse(rawText);
        } catch (error) {
            if (!response.ok) {
                throw new Error(rawText);
            }
            throw error;
        }
    }
    if (!response.ok) {
        const detailParts = [data?.error || `서버 오류 (${response.status})`];
        if (data?.translation_session?.translation_log_dir) {
            detailParts.push(`log=${data.translation_session.translation_log_dir}`);
        }
        if (data?.translation_session?.checkpoint_path) {
            detailParts.push(`checkpoint=${data.translation_session.checkpoint_path}`);
        }
        throw new Error(detailParts.join(" | "));
    }
    return data;
}


async function apiPost(path, payload) {
    return apiPostWithBase(BACKEND_URL, path, payload);
}


async function apiPostProgress(path, payload) {
    try {
        return await apiPostWithBase(PROGRESS_BACKEND_URL, path, payload);
    } catch (error) {
        const message = String(error?.message || "");
        const shouldFallback = message.includes("404")
            || message.includes("Not Found")
            || message.includes("Failed to fetch")
            || message.includes("NetworkError")
            || message.includes("TypeError")
            || message.includes("백엔드 요청 실패");
        if (!shouldFallback) {
            throw error;
        }
        return apiPost(path, payload);
    }
}


function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}


function resetTranslationProgress(options = {}) {
    return resetTranslationProgressUi(options);
}


function formatTranslationStatusTimestamp(value) {
    if (!value) {
        return "-";
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
        return String(value);
    }
    return parsed.toLocaleTimeString("ko-KR", { hour12: false });
}


function renderTranslationProgress(status = state.translationProgressStatus) {
    return renderTranslationProgressUi(status);
}


async function fetchTranslationProgressStatus() {
    return fetchTranslationProgressStatusUi();
}


async function prepareTranslationProgress(payload) {
    return prepareTranslationProgressUi(payload);
}


function resetTranslationProgressUi(options = {}) {
    if (state.translationProgressPollHandle) {
        clearInterval(state.translationProgressPollHandle);
        state.translationProgressPollHandle = null;
    }
    state.translationProgressBusy = false;
    state.translationProgressFailureCount = 0;
    state.translationProgressRequestActive = false;
    if (!options.preserveSession) {
        state.translationProgressSession = null;
        state.translationProgressStatus = null;
        state.translationProgressLastLogKey = "";
    }
    renderTranslationProgressUi();
}


function renderTranslationProgressUi(status = state.translationProgressStatus) {
    if (!dom.translationProgressPanel) {
        return;
    }
    const session = state.translationProgressSession;
    if (!session && !status) {
        dom.translationProgressPanel.className = "results-panel empty-state";
        dom.translationProgressPanel.textContent = "번역 진행도 표시가 아직 없습니다.";
        return;
    }

    const total = Number(status?.total_item_count || 0);
    const completed = Number(status?.completed_item_count || 0);
    const translated = Number(status?.translated_item_count || 0);
    const pending = Number(status?.pending_item_count || 0);
    const failed = Number(status?.failed_item_count || 0);
    const skipped = Number(status?.skipped_adult_count || 0);
    const completedBatches = Number(status?.completed_batch_count || 0);
    const percent = Math.max(0, Math.min(100, Number(status?.progress_percent || 0)));
    const staleSeconds = Number(status?.stale_seconds || 0);
    const isStale = state.translationProgressRequestActive && staleSeconds >= 30;
    const statusLabel = status?.halted ? "중단됨" : (state.translationProgressRequestActive ? "진행 중" : "대기/완료");
    const currentDocument = status?.current_document || session?.current_document || "-";
    const latestAttemptName = status?.latest_attempt_name || "-";
    const latestAttemptPath = status?.latest_attempt?.document_path || "";
    const sessionId = status?.session_id || session?.session_id || "-";
    const updatedAtLabel = formatTranslationStatusTimestamp(status?.updated_at || "");
    const staleLabel = isStale
        ? `<span class="pill warning">갱신 지연 ${escapeHtml(Math.round(staleSeconds))}초</span>`
        : "";

    dom.translationProgressPanel.className = "results-panel translation-progress-panel";
    dom.translationProgressPanel.innerHTML = `
        <div class="result-row">
            <div class="translation-progress-header">
                <div>
                    <strong>실시간 진행도</strong>
                    <div class="helper-text">session=${escapeHtml(sessionId)} · 상태=${escapeHtml(statusLabel)} · 최근 갱신=${escapeHtml(updatedAtLabel)}</div>
                </div>
                <div class="pill-list compact">
                    <span class="pill subtle">${escapeHtml(percent.toFixed(1))}%</span>
                    ${staleLabel}
                </div>
            </div>
            <div class="translation-progress-meter" aria-label="translation progress">
                <div class="translation-progress-fill" style="width:${percent.toFixed(2)}%"></div>
            </div>
            <div class="translation-progress-grid">
                <div class="translation-progress-stat"><strong>${escapeHtml(String(completed))}</strong><span>완료/처리</span></div>
                <div class="translation-progress-stat"><strong>${escapeHtml(String(translated))}</strong><span>번역 완료</span></div>
                <div class="translation-progress-stat"><strong>${escapeHtml(String(pending))}</strong><span>대기</span></div>
                <div class="translation-progress-stat"><strong>${escapeHtml(String(failed))}</strong><span>실패</span></div>
                <div class="translation-progress-stat"><strong>${escapeHtml(String(skipped))}</strong><span>성인 보류</span></div>
                <div class="translation-progress-stat"><strong>${escapeHtml(String(total))}</strong><span>전체 항목</span></div>
            </div>
            <div class="helper-text">현재 문서: ${escapeHtml(currentDocument || "-")}</div>
            <div class="helper-text">최근 attempt: ${escapeHtml(latestAttemptName)}${latestAttemptPath ? ` · ${escapeHtml(latestAttemptPath)}` : ""} · 완료 배치 ${escapeHtml(String(completedBatches))}</div>
            ${status?.last_error ? `<div class="helper-text" style="color: var(--danger);">최근 오류: ${escapeHtml(status.last_error)}</div>` : ""}
            ${status?.halt_reason ? `<div class="helper-text" style="color: var(--warning);">중단 사유: ${escapeHtml(status.halt_reason)}</div>` : ""}
        </div>
    `;
}


function buildTranslationProgressLogKey(status = state.translationProgressStatus) {
    if (!status) {
        return "";
    }
    return [
        status.session_id || "",
        Number(status.translated_item_count || 0),
        Number(status.pending_item_count || 0),
        Number(status.failed_item_count || 0),
        Number(status.completed_batch_count || 0),
        status.current_document || "",
        status.halted ? "halted" : "active",
        status.halt_reason || "",
    ].join("|");
}


function logTranslationProgressUpdate(status = state.translationProgressStatus, options = {}) {
    if (!status) {
        return;
    }
    const logKey = buildTranslationProgressLogKey(status);
    if (!logKey) {
        return;
    }
    if (!options.force && logKey === state.translationProgressLastLogKey) {
        return;
    }
    state.translationProgressLastLogKey = logKey;

    const total = Number(status.total_item_count || 0);
    const translated = Number(status.translated_item_count || 0);
    const pending = Number(status.pending_item_count || 0);
    const completedBatches = Number(status.completed_batch_count || 0);
    const percent = Math.max(0, Math.min(100, Number(status.progress_percent || 0)));
    const currentDocument = status.current_document || "-";
    const lastError = String(status.last_error || "").trim();
    const message = `실시간 진행: ${translated}/${total} (${percent.toFixed(1)}%) · 남음 ${pending} · 배치 ${completedBatches} · 문서 ${currentDocument}`;

    if (status.halted) {
        addLog(`번역 중단: ${status.halt_reason || message}`, "warning");
        return;
    }
    if (lastError) {
        addLog(`${message} · 최근 오류: ${lastError}`, "warning");
        return;
    }
    addLog(message, options.type || "info");
}


function normalizeProgressScope(scope = {}) {
    const payload = scope && typeof scope === "object" ? scope : {};
    const normalized = {};
    for (const [key, value] of Object.entries(payload)) {
        if (Array.isArray(value)) {
            normalized[key] = value.map((item) => String(item ?? "").trim()).filter(Boolean).sort();
        } else if (value == null) {
            normalized[key] = "";
        } else {
            normalized[key] = value;
        }
    }
    return normalized;
}


async function fetchTranslationProgressStatusUi() {
    if (!state.translationProgressSession || state.translationProgressBusy) {
        return;
    }
    state.translationProgressBusy = true;
    try {
        const response = await apiPostProgress("/translation_status", {
            session_id: state.translationProgressSession.session_id,
            analysis_mode: state.translationProgressSession.analysis_mode,
            target_language: state.translationProgressSession.target_language,
            game_exe_path: state.translationProgressSession.game_exe_path || "",
        });
        state.translationProgressFailureCount = 0;
        state.translationProgressStatus = response;
        renderTranslationProgressUi(response);
        logTranslationProgressUpdate(response);
    } catch (error) {
        state.translationProgressFailureCount += 1;
        if (state.translationProgressRequestActive && (state.translationProgressFailureCount === 1 || state.translationProgressFailureCount === 5)) {
            addLog(`진행도 조회 실패: ${error.message}`, "warning");
        }
        if (state.translationProgressFailureCount >= 5) {
            resetTranslationProgressUi({ preserveSession: true });
        }
    } finally {
        state.translationProgressBusy = false;
    }
}


async function prepareTranslationProgressUi(payload) {
    try {
        const response = await apiPostProgress("/resolve_translation_session", payload);
        state.translationProgressSession = {
            session_id: response.session_id,
            analysis_mode: response.analysis_mode,
            target_language: response.target_language,
            game_exe_path: payload.game_exe_path || "",
            status_path: response.status_path || "",
        };
        state.translationProgressStatus = response.status || null;
        state.translationProgressRequestActive = true;
        renderTranslationProgressUi();
        if (response.status) {
            logTranslationProgressUpdate(response.status, { force: true });
        }
        activateTab("results");
        await fetchTranslationProgressStatusUi();
        state.translationProgressPollHandle = window.setInterval(() => {
            fetchTranslationProgressStatusUi().catch(() => {});
        }, 2000);
    } catch (error) {
        addLog(`진행도 세션 준비 실패: ${error.message}`, "warning");
    }
}


function getCharacterInitials(character) {
    const source = String(character?.display_name || character?.speaker_id || "?").trim();
    const parts = source.split(/\s+/).filter(Boolean);
    if (parts.length >= 2) {
        return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return source.slice(0, 2).toUpperCase();
}


function isSystemCharacter(character) {
    return ["_default_", "_narration_"].includes(character?.speaker_id);
}


function buildPortraitUrl(character, size = 160) {
    const portrait = character?.portrait;
    if (!portrait?.asset_path) {
        return "";
    }

    const params = new URLSearchParams({
        path: portrait.asset_path,
        size: String(size),
    });
    if (Array.isArray(portrait.crop) && portrait.crop.length === 4) {
        params.set("crop", portrait.crop.join(","));
    }
    return `${BACKEND_URL}/asset_thumbnail?${params.toString()}`;
}


function buildCharacterAvatarMarkup(character, variant = "small") {
    const avatarClass = `character-avatar ${variant}`;
    const portraitUrl = buildPortraitUrl(character, variant === "large" ? 240 : 112);
    const accessibleName = escapeHtml(character?.display_name || character?.speaker_id || "Character");
    if (portraitUrl) {
        return `<img class="${avatarClass}" src="${portraitUrl}" alt="${accessibleName} portrait" loading="lazy">`;
    }
    return `<div class="${avatarClass} is-fallback" aria-hidden="true">${escapeHtml(getCharacterInitials(character))}</div>`;
}


function getOpenAIAuthMode() {
    return dom.openaiAuthModeSelect?.value || "api_key";
}


function supportsApiKey(provider = dom.providerSelect?.value || "gemini", authMode = getOpenAIAuthMode()) {
    return provider === "gemini" || (provider === "openai" && authMode === "api_key");
}


function getApiKeyStorageScope(provider = dom.providerSelect?.value || "gemini", authMode = getOpenAIAuthMode()) {
    if (provider === "openai") {
        return `openai:${authMode}`;
    }
    return provider || "gemini";
}


function getApiKeyStorageLabel(provider = dom.providerSelect?.value || "gemini", authMode = getOpenAIAuthMode()) {
    if (provider === "openai" && authMode === "api_key") {
        return "OpenAI API 키";
    }
    return "Gemini API 키";
}


function getApiKeyStorageKey(provider = dom.providerSelect?.value || "gemini", authMode = getOpenAIAuthMode()) {
    return `${API_KEY_STORAGE_PREFIX}:${getApiKeyStorageScope(provider, authMode)}`;
}


function getStoredApiKey(provider = dom.providerSelect?.value || "gemini", authMode = getOpenAIAuthMode()) {
    try {
        return window.localStorage.getItem(getApiKeyStorageKey(provider, authMode)) || "";
    } catch (error) {
        return "";
    }
}


function getGeminiAuthMode() {
    return dom.geminiAuthModeSelect?.value || "api_key";
}


function usesGeminiVertex() {
    return (dom.providerSelect?.value || "gemini") === "gemini" && getGeminiAuthMode() === "vertex_ai";
}


function supportsApiKey(
    provider = dom.providerSelect?.value || "gemini",
    openaiAuthMode = getOpenAIAuthMode(),
    geminiAuthMode = getGeminiAuthMode(),
) {
    return (provider === "gemini" && geminiAuthMode !== "vertex_ai")
        || (provider === "openai" && openaiAuthMode === "api_key");
}


function getApiKeyStorageScope(
    provider = dom.providerSelect?.value || "gemini",
    openaiAuthMode = getOpenAIAuthMode(),
    geminiAuthMode = getGeminiAuthMode(),
) {
    if (provider === "openai") {
        return `openai:${openaiAuthMode}`;
    }
    if (provider === "gemini" && geminiAuthMode === "vertex_ai") {
        return "gemini:vertex_ai";
    }
    return provider || "gemini";
}


function getApiKeyStorageLabel(
    provider = dom.providerSelect?.value || "gemini",
    openaiAuthMode = getOpenAIAuthMode(),
    geminiAuthMode = getGeminiAuthMode(),
) {
    if (provider === "openai" && openaiAuthMode === "api_key") {
        return "OpenAI API key";
    }
    if (provider === "gemini" && geminiAuthMode === "vertex_ai") {
        return "Vertex AI";
    }
    return "Gemini API key";
}


function getApiKeyStorageKey(
    provider = dom.providerSelect?.value || "gemini",
    openaiAuthMode = getOpenAIAuthMode(),
    geminiAuthMode = getGeminiAuthMode(),
) {
    return `${API_KEY_STORAGE_PREFIX}:${getApiKeyStorageScope(provider, openaiAuthMode, geminiAuthMode)}`;
}


function getStoredApiKey(
    provider = dom.providerSelect?.value || "gemini",
    openaiAuthMode = getOpenAIAuthMode(),
    geminiAuthMode = getGeminiAuthMode(),
) {
    try {
        return window.localStorage.getItem(getApiKeyStorageKey(provider, openaiAuthMode, geminiAuthMode)) || "";
    } catch (error) {
        return "";
    }
}


function clearFailedTonePreviewCache() {
    let changed = false;
    Object.entries(state.tonePreviewByCharacter || {}).forEach(([speakerId, previewState]) => {
        const hasErrors = Boolean(previewState?.variants?.some((variant) => variant.error));
        if (previewState?.cacheable === false || hasErrors) {
            delete state.tonePreviewByCharacter[speakerId];
            changed = true;
        }
    });
    return changed;
}


function renderApiKeyStorageStatus() {
    if (!dom.apiKeyStorageStatus) {
        return;
    }

    if (!supportsApiKey()) {
        dom.apiKeyStorageStatus.textContent = "Codex OAuth 모드에서는 API 키 저장을 사용하지 않습니다.";
        return;
    }

    const label = getApiKeyStorageLabel();
    const savedKey = getStoredApiKey();
    const currentKey = dom.apiKeyInput.value.trim();
    if (!savedKey) {
        dom.apiKeyStorageStatus.textContent = `${label}가 이 브라우저에 저장되어 있지 않습니다.`;
        return;
    }
    if (!currentKey) {
        dom.apiKeyStorageStatus.textContent = `저장된 ${label}가 있습니다. ‘키 불러오기’를 누르면 입력칸에 채웁니다.`;
        return;
    }
    if (currentKey === savedKey) {
        dom.apiKeyStorageStatus.textContent = `현재 입력값이 저장된 ${label}와 같습니다.`;
        return;
    }
    dom.apiKeyStorageStatus.textContent = `현재 입력값이 저장된 ${label}와 다릅니다. 저장 또는 불러오기를 선택하세요.`;
}


function handleApiKeyMutation({ rerender = true } = {}) {
    const clearedFailedPreview = clearFailedTonePreviewCache();
    renderApiKeyStorageStatus();
    if (rerender && clearedFailedPreview && state.analysis && state.selectedCharacterId) {
        renderSelectedCharacterDetail();
    }
}


function saveCurrentApiKeyToStorage() {
    if (!supportsApiKey()) {
        addLog("현재 인증 방식에서는 API 키 저장을 사용하지 않습니다.", "warning");
        renderApiKeyStorageStatus();
        return;
    }

    const value = dom.apiKeyInput.value.trim();
    if (!value) {
        addLog("저장할 API 키를 먼저 입력하세요.", "warning");
        return;
    }

    try {
        window.localStorage.setItem(getApiKeyStorageKey(), value);
        renderApiKeyStorageStatus();
        addLog(`${getApiKeyStorageLabel()} 저장 완료`, "success");
    } catch (error) {
        addLog(`API 키 저장 실패: ${error.message}`, "error");
    }
}


function loadStoredApiKeyForCurrentScope({ silent = false, rerender = true } = {}) {
    if (!supportsApiKey()) {
        renderApiKeyStorageStatus();
        return false;
    }

    const value = getStoredApiKey();
    if (!value) {
        if (!silent) {
            addLog(`저장된 ${getApiKeyStorageLabel()}가 없습니다.`, "warning");
        }
        renderApiKeyStorageStatus();
        return false;
    }

    dom.apiKeyInput.value = value;
    handleApiKeyMutation({ rerender });
    if (!silent) {
        addLog(`${getApiKeyStorageLabel()} 불러오기 완료`, "success");
    }
    return true;
}


function clearStoredApiKeyForCurrentScope() {
    if (!supportsApiKey()) {
        renderApiKeyStorageStatus();
        return;
    }

    try {
        window.localStorage.removeItem(getApiKeyStorageKey());
        dom.apiKeyInput.value = "";
        handleApiKeyMutation();
        addLog(`${getApiKeyStorageLabel()} 삭제 완료`, "success");
    } catch (error) {
        addLog(`저장된 API 키 삭제 실패: ${error.message}`, "error");
    }
}


function syncStoredApiKeyForCurrentScope() {
    if (!supportsApiKey()) {
        dom.apiKeyInput.value = "";
        renderApiKeyStorageStatus();
        return false;
    }

    dom.apiKeyInput.value = getStoredApiKey();
    handleApiKeyMutation({ rerender: false });
    return Boolean(dom.apiKeyInput.value.trim());
}


function getCharacterTonePresetById(presetId) {
    return CHARACTER_TONE_PRESETS.find((preset) => preset.id === presetId) || CHARACTER_TONE_PRESETS[0];
}


function buildCharacterTonePresetOptions(selectedId) {
    return CHARACTER_TONE_PRESETS.map((preset) => `
        <option value="${escapeHtml(preset.id)}" ${preset.id === selectedId ? "selected" : ""}>${escapeHtml(preset.name)}</option>
    `).join("");
}


function clearTonePreview(speakerId = null) {
    if (!speakerId) {
        state.tonePreviewByCharacter = {};
        state.tonePreviewLoadingSpeakerId = null;
        return;
    }
    delete state.tonePreviewByCharacter[speakerId];
    if (state.tonePreviewLoadingSpeakerId === speakerId) {
        state.tonePreviewLoadingSpeakerId = null;
    }
}


function maybeApplyTonePresetSuggestion(nextPresetId, previousPresetId, currentProfile = {}, fallbackProfile = {}) {
    const nextPreset = getCharacterTonePresetById(nextPresetId);
    const previousPreset = getCharacterTonePresetById(previousPresetId || "custom");
    const nextProfile = { ...currentProfile, tone_preset_id: nextPreset.id };
    const currentTone = (currentProfile.tone || "").trim();
    const currentNotes = (currentProfile.notes || "").trim();
    const previousTone = (previousPreset.suggestedTone || "").trim();
    const previousNotes = (previousPreset.suggestedNotes || "").trim();
    const fallbackTone = (fallbackProfile.tone || "").trim();
    const fallbackNotes = (fallbackProfile.notes || "").trim();
    const nextTone = (nextPreset.suggestedTone || "").trim();
    const nextNotes = (nextPreset.suggestedNotes || "").trim();

    if (nextPreset.id !== "custom") {
        if (!currentTone || currentTone === previousTone || currentTone === fallbackTone) {
            nextProfile.tone = nextTone;
        }
        if (!currentNotes || currentNotes === previousNotes || currentNotes === fallbackNotes) {
            nextProfile.notes = nextNotes;
        }
    }
    return nextProfile;
}


function hasCustomToneMemo(profile = {}, presetId = "custom") {
    const preset = getCharacterTonePresetById(presetId);
    const tone = (profile.tone || "").trim();
    const notes = (profile.notes || "").trim();
    return Boolean(
        (tone && tone !== (preset.suggestedTone || "").trim())
        || (notes && notes !== (preset.suggestedNotes || "").trim())
    );
}


function getCharacterPreviewAlternativePresetIds(currentPresetId, inferredPresetId) {
    const picks = [];
    const pushUnique = (presetId) => {
        if (!presetId || presetId === "custom" || presetId === currentPresetId || picks.includes(presetId)) {
            return;
        }
        picks.push(presetId);
    };

    pushUnique(inferredPresetId);
    (CHARACTER_TONE_PRESET_COMPARISON_MAP[currentPresetId] || []).forEach(pushUnique);
    CHARACTER_TONE_PRESET_FALLBACKS.forEach(pushUnique);
    return picks.slice(0, 2);
}


function buildCharacterPreviewVariants(character) {
    const currentProfile = state.characterProfiles[character.speaker_id] || {};
    const inferredProfile = state.analysis?.default_character_profiles?.[character.speaker_id] || {};
    const currentPresetId = currentProfile.tone_preset_id || inferredProfile.tone_preset_id || "custom";
    const currentPreset = getCharacterTonePresetById(currentPresetId);
    const alternativePresetIds = getCharacterPreviewAlternativePresetIds(currentPresetId, inferredProfile.tone_preset_id || "custom");
    const customMemo = hasCustomToneMemo(currentProfile, currentPresetId);
    const currentDescription = customMemo
        ? `${currentPreset.name} + 현재 커스텀 메모`
        : `${currentPreset.name} 기준 현재 설정`;

    const variants = [
        {
            variantId: "current",
            label: "현재 설정",
            description: currentDescription,
            profile: {
                display_name: currentProfile.display_name || character.display_name || character.speaker_id,
                role: currentProfile.role || inferredProfile.role || "",
                tone_preset_id: currentPresetId,
                tone: currentProfile.tone || "",
                notes: currentProfile.notes || "",
            },
        },
    ];

    alternativePresetIds.forEach((presetId, index) => {
        const preset = getCharacterTonePresetById(presetId);
        variants.push({
            variantId: `alternative_${index + 1}`,
            label: `대안 ${index + 1}`,
            description: preset.name,
            profile: {
                display_name: currentProfile.display_name || character.display_name || character.speaker_id,
                role: currentProfile.role || inferredProfile.role || "",
                tone_preset_id: preset.id,
                tone: preset.suggestedTone || "",
                notes: preset.suggestedNotes || "",
            },
        });
    });

    return variants.slice(0, 3);
}


function buildPreviewCharacterProfilesPayload(speakerId, speakerName, speakerProfile) {
    const defaultProfile = state.characterProfiles._default_
        || state.analysis?.default_character_profiles?._default_
        || {
            display_name: "Default",
            tone_preset_id: "ui_clean",
            role: "UI/선택지/고정 문자열",
            tone: getCharacterTonePresetById("ui_clean").suggestedTone,
            notes: getCharacterTonePresetById("ui_clean").suggestedNotes,
        };

    return {
        _default_: {
            display_name: defaultProfile.display_name || "Default",
            tone_preset_id: defaultProfile.tone_preset_id || "ui_clean",
            role: defaultProfile.role || "UI/선택지/고정 문자열",
            tone: defaultProfile.tone || "",
            notes: defaultProfile.notes || "",
        },
        [speakerId]: {
            display_name: speakerProfile.display_name || speakerName,
            tone_preset_id: speakerProfile.tone_preset_id || "custom",
            role: speakerProfile.role || "",
            tone: speakerProfile.tone || "",
            notes: speakerProfile.notes || "",
        },
    };
}


function buildCharacterPreviewCacheKey(character, variants, sampleLines) {
    const settings = getCurrentTranslationSettings();
    return JSON.stringify({
        speakerId: character.speaker_id,
        provider: settings.provider,
        geminiAuthMode: settings.geminiAuthMode,
        openaiAuthMode: settings.openaiAuthMode,
        modelName: settings.modelName,
        targetLanguage: dom.targetLanguageInput.value.trim() || "ko",
        includeAdult: dom.includeAdultCheckbox.checked,
        worldSettings: collectWorldSettings(),
        vertexSettings: collectVertexSettings(),
        sampleLines,
        variants: variants.map((variant) => ({
            variantId: variant.variantId,
            tonePresetId: variant.profile.tone_preset_id || "custom",
            role: variant.profile.role || "",
            tone: variant.profile.tone || "",
            notes: variant.profile.notes || "",
        })),
    });
}


function usesOpenAIOAuth() {
    return dom.providerSelect.value === "openai" && getOpenAIAuthMode() === "oauth_cli";
}


function normalizeOpenAIOAuthCommand(value) {
    const normalized = String(value || "").trim();
    if (!normalized) {
        return DEFAULT_OPENAI_OAUTH_COMMAND;
    }
    if (DEFAULT_OPENAI_OAUTH_COMMAND === "codex {args}") {
        return normalized;
    }

    const lowered = normalized.toLowerCase();
    const legacyDefaults = new Set([
        "codex",
        "codex {args}",
        "codex.exe",
        "codex.exe {args}",
        '"codex" {args}',
        '"codex.exe" {args}',
    ]);
    return legacyDefaults.has(lowered) ? DEFAULT_OPENAI_OAUTH_COMMAND : normalized;
}


function getModelSuggestionKey() {
    if (dom.providerSelect.value === "openai") {
        return usesOpenAIOAuth() ? "openai_oauth_cli" : "openai_api_key";
    }
    return dom.providerSelect.value;
}


function getDefaultRuntimeSettingKey(provider = dom.providerSelect.value, authMode = getOpenAIAuthMode()) {
    if (provider === "openai") {
        return authMode === "oauth_cli" ? "openai_oauth_cli" : "openai_api_key";
    }
    return provider || "gemini";
}


function getDefaultBatchSizeValue(provider = dom.providerSelect.value, authMode = getOpenAIAuthMode()) {
    const defaults = DEFAULT_RUNTIME_SETTINGS[getDefaultRuntimeSettingKey(provider, authMode)] || DEFAULT_RUNTIME_SETTINGS.gemini;
    return defaults.batchSize;
}


function getDefaultApiDelayValue(provider = dom.providerSelect.value, authMode = getOpenAIAuthMode()) {
    const defaults = DEFAULT_RUNTIME_SETTINGS[getDefaultRuntimeSettingKey(provider, authMode)] || DEFAULT_RUNTIME_SETTINGS.gemini;
    return defaults.apiDelay;
}


function getTranslationPresetById(presetId) {
    return TRANSLATION_PRESETS.find((preset) => preset.id === presetId) || null;
}


function normalizeNumericSetting(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
}


function formatNumericSetting(value) {
    const normalized = normalizeNumericSetting(value, 0);
    return Number.isInteger(normalized) ? String(normalized) : normalized.toFixed(1).replace(/\.0$/, "");
}


function getCurrentTranslationSettings() {
    return {
        provider: dom.providerSelect.value || "gemini",
        geminiAuthMode: getGeminiAuthMode(),
        openaiAuthMode: getOpenAIAuthMode(),
        modelName: dom.modelInput.value.trim(),
        batchSize: normalizeNumericSetting(dom.batchSizeInput.value, getDefaultBatchSizeValue()),
        apiDelay: normalizeNumericSetting(dom.apiDelayInput.value, getDefaultApiDelayValue()),
    };
}


function doesTranslationPresetMatch(preset, settings = getCurrentTranslationSettings()) {
    if (!preset) {
        return false;
    }
    if (preset.provider !== settings.provider) {
        return false;
    }
    if (preset.provider === "openai" && preset.openaiAuthMode !== settings.openaiAuthMode) {
        return false;
    }
    if (preset.modelName !== settings.modelName) {
        return false;
    }
    if (normalizeNumericSetting(preset.batchSize, 12) !== normalizeNumericSetting(settings.batchSize, 12)) {
        return false;
    }
    if (preset.provider === "openai" && preset.openaiAuthMode === "oauth_cli") {
        return true;
    }
    return Math.abs(
        normalizeNumericSetting(preset.apiDelay, 0.3) - normalizeNumericSetting(settings.apiDelay, 0.3),
    ) < 0.001;
}


function inferTranslationPresetId(settings = getCurrentTranslationSettings()) {
    const matchedPreset = TRANSLATION_PRESETS.find((preset) => doesTranslationPresetMatch(preset, settings));
    return matchedPreset?.id || "";
}


function renderTranslationPresetSummary() {
    if (!dom.translationPresetSummary) {
        return;
    }

    const preset = getTranslationPresetById(state.selectedTranslationPresetId);
    if (preset) {
        const runtimeLabel = preset.provider === "gemini"
            ? (usesGeminiVertex() ? "Vertex AI" : "Gemini API")
            : preset.openaiAuthMode === "oauth_cli"
                ? "OpenAI OAuth / Codex CLI"
                : "OpenAI API";
        const delayLabel = preset.provider === "gemini"
            ? ` · delay ${formatNumericSetting(preset.apiDelay)}초 · retry 2`
            : " · Codex가 문서별 청크를 자동 재조정";
        dom.translationPresetSummary.textContent = `${preset.name} · ${runtimeLabel} · ${preset.modelName} · batch ${formatNumericSetting(preset.batchSize)}${delayLabel}`;
        return;
    }

    const current = getCurrentTranslationSettings();
    const runtimeLabel = current.provider === "gemini"
        ? (current.geminiAuthMode === "vertex_ai" ? "Vertex AI" : "Gemini API")
        : current.openaiAuthMode === "oauth_cli"
            ? "OpenAI OAuth / Codex CLI"
            : "OpenAI API";
    const delayLabel = current.provider === "gemini"
        ? ` · delay ${formatNumericSetting(current.apiDelay)}초`
        : "";
    dom.translationPresetSummary.textContent = `커스텀 설정 · ${runtimeLabel} · ${current.modelName || "-"} · batch ${formatNumericSetting(current.batchSize)}${delayLabel}`;
}


function renderTranslationPresetCards() {
    if (!dom.translationPresetGrid) {
        return;
    }

    dom.translationPresetGrid.innerHTML = "";
    TRANSLATION_PRESETS.forEach((preset) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `translation-preset-card${state.selectedTranslationPresetId === preset.id ? " active" : ""}`;
        button.dataset.presetId = preset.id;
        const runtimeLabel = preset.provider === "gemini"
            ? "Gemini API"
            : preset.openaiAuthMode === "oauth_cli"
                ? "OpenAI OAuth"
                : "OpenAI API";
        const delayLabel = preset.provider === "gemini"
            ? ` · delay ${formatNumericSetting(preset.apiDelay)}초`
            : "";
        button.innerHTML = `
            <div class="translation-preset-topline">
                <strong class="translation-preset-name">${escapeHtml(preset.name)}</strong>
                <span class="translation-preset-badge">${escapeHtml(preset.badge)}</span>
            </div>
            <p class="translation-preset-description">${escapeHtml(preset.description)}</p>
            <p class="translation-preset-meta">${escapeHtml(runtimeLabel)} · ${escapeHtml(preset.modelName)} · batch ${escapeHtml(formatNumericSetting(preset.batchSize))}${escapeHtml(delayLabel)}</p>
        `;
        dom.translationPresetGrid.appendChild(button);
    });
    renderTranslationPresetSummary();
}


function syncTranslationPresetSelection() {
    state.selectedTranslationPresetId = inferTranslationPresetId();
    renderTranslationPresetCards();
}


function applyTranslationPreset(presetId, options = {}) {
    const preset = getTranslationPresetById(presetId);
    if (!preset) {
        return;
    }

    dom.providerSelect.value = preset.provider;
    dom.openaiAuthModeSelect.value = preset.openaiAuthMode;
    updateModelSuggestions();
    dom.modelInput.value = preset.modelName;
    dom.batchSizeInput.value = String(preset.batchSize);
    dom.apiDelayInput.value = String(preset.apiDelay);
    state.selectedTranslationPresetId = preset.id;
    updateProviderUI();
    renderTranslationPresetCards();

    if (options.log !== false) {
        addLog(`번역 모드 적용: ${preset.name} (${preset.modelName})`, "success");
    }
}


function handleTranslationPresetClick(event) {
    const button = event.target.closest("[data-preset-id]");
    if (!button) {
        return;
    }
    applyTranslationPreset(button.dataset.presetId);
}


function updateProviderUI() {
    const isOpenAI = dom.providerSelect.value === "openai";
    const useOauth = usesOpenAIOAuth();
    dom.openaiOAuthCommandInput.value = normalizeOpenAIOAuthCommand(dom.openaiOAuthCommandInput.value);
    if (!useOauth) {
        clearOpenAIOAuthPoll();
    }

    dom.openaiAuthField.classList.toggle("hidden", !isOpenAI);
    dom.apiKeyField.classList.toggle("hidden", isOpenAI && useOauth);
    dom.openaiOAuthPanel.classList.toggle("hidden", !isOpenAI || !useOauth);
    dom.apiKeyInput.disabled = isOpenAI && useOauth;
    dom.batchSizeInput.disabled = false;
    dom.apiDelayInput.disabled = useOauth;

    if (useOauth) {
        dom.translationHint.textContent = "OpenAI OAuth 모드에서는 배치 크기를 최대 상한선으로 보고, 문서별로 더 싼 모델과 청크 크기를 자동 선택합니다. 완료된 파일은 즉시 Ren'Py 출력 경로에 반영됩니다.";
        dom.openaiOAuthStatus.textContent = dom.openaiOAuthStatus.textContent || "CLI 점검 전입니다.";
    } else {
        dom.translationHint.textContent = "Gemini/API 모드에서는 배치 상한과 글자수 budget을 함께 보고 긴 대사는 더 작은 청크로 자동 분할합니다.";
    }
    renderApiKeyStorageStatus();
    renderTranslationPresetSummary();
}


function activateTab(tabName) {
    state.activeTab = tabName;
    dom.tabButtons.forEach((button) => {
        button.classList.toggle("active", button.dataset.tab === tabName);
    });
    dom.tabPanels.forEach((panel) => {
        panel.classList.toggle("active", panel.dataset.panel === tabName);
    });
}


function updateModelSuggestions() {
    const suggestions = MODEL_SUGGESTIONS[getModelSuggestionKey()] || [];
    dom.modelSuggestions.innerHTML = "";
    suggestions.forEach((model) => {
        const option = document.createElement("option");
        option.value = model;
        dom.modelSuggestions.appendChild(option);
    });
    if (!dom.modelInput.value || !suggestions.includes(dom.modelInput.value)) {
        dom.modelInput.value = suggestions[0] || "";
    }
    updateProviderUI();
}


function downloadText(content, fileName) {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}


function addGlossaryRow(entry = {}) {
    const row = document.createElement("div");
    row.className = "glossary-row";
    row.innerHTML = `
        <input type="text" data-field="source" placeholder="원문 용어" value="${entry.source || ""}">
        <input type="text" data-field="target" placeholder="번역/음차" value="${entry.target || ""}">
        <input type="text" data-field="note" placeholder="메모" value="${entry.note || ""}">
        <button type="button" class="mini-button" data-action="remove-row">삭제</button>
    `;
    dom.glossaryTable.appendChild(row);
}


function setGlossaryRows(entries = []) {
    dom.glossaryTable.innerHTML = "";
    if (!entries.length) {
        addGlossaryRow();
        return;
    }
    entries.forEach((entry) => addGlossaryRow(entry));
}


function captureGlossaryRows() {
    return Array.from(dom.glossaryTable.querySelectorAll(".glossary-row"))
        .map((row) => ({
            source: row.querySelector("[data-field='source']")?.value.trim() || "",
            target: row.querySelector("[data-field='target']")?.value.trim() || "",
            note: row.querySelector("[data-field='note']")?.value.trim() || "",
        }))
        .filter((entry) => entry.source || entry.target || entry.note);
}


function addStyleOverrideRow(entry = {}) {
    const row = document.createElement("div");
    row.className = "style-override-row";
    row.innerHTML = `
        <input type="text" data-field="style_name" list="styleSuggestionList" placeholder="예: chapterstyle" value="${escapeHtml(entry.style_name || "")}">
        <input type="text" data-field="font_path" list="fontSuggestionList" placeholder="예: fonts/NotoSansKR-Regular.otf" value="${escapeHtml(entry.font_path || "")}">
        <input type="number" data-field="size" placeholder="비우면 기존 크기 유지" min="8" step="1" value="${entry.size ?? ""}">
        <button type="button" class="mini-button" data-action="remove-style-row">삭제</button>
    `;
    dom.styleOverrideTable.appendChild(row);
}


function setStyleOverrideRows(entries = []) {
    dom.styleOverrideTable.innerHTML = "";
    if (!entries.length) {
        addStyleOverrideRow();
        return;
    }
    entries.forEach((entry) => addStyleOverrideRow(entry));
}


function captureStyleOverrideRows() {
    return Array.from(dom.styleOverrideTable.querySelectorAll(".style-override-row"))
        .map((row) => ({
            style_name: row.querySelector("[data-field='style_name']")?.value.trim() || "",
            font_path: row.querySelector("[data-field='font_path']")?.value.trim() || "",
            size: row.querySelector("[data-field='size']")?.value.trim() || "",
        }))
        .filter((entry) => entry.style_name || entry.font_path || entry.size);
}


function normalizeFontOptionEntry(entry) {
    if (entry === undefined || entry === null) {
        return null;
    }
    if (typeof entry === "string") {
        return {
            value: entry,
            label: entry,
            source: "game",
            fontId: "",
        };
    }

    const value = String(entry.value ?? entry.path ?? "").trim();
    if (!value && entry.value !== "") {
        return null;
    }
    return {
        value,
        label: String(entry.label ?? entry.display_name ?? entry.file_name ?? value).trim() || value,
        source: String(entry.source || ""),
        fontId: String(entry.fontId || entry.font_id || ""),
        familyName: String(entry.family_name || ""),
        styleName: String(entry.style_name || ""),
        fileName: String(entry.file_name || ""),
        previewUrl: String(entry.preview_url || ""),
    };
}


function getFontBrowserSampleText() {
    return dom.fontBrowserSampleTextInput?.value.trim() || DEFAULT_FONT_BROWSER_SAMPLE_TEXT;
}


function buildFontPreviewUrl(options = {}) {
    const params = new URLSearchParams();
    params.set("sample", String(options.sampleText || getFontBrowserSampleText()).trim() || DEFAULT_FONT_BROWSER_SAMPLE_TEXT);
    params.set("width", String(options.width || 640));
    params.set("height", String(options.height || 140));
    if (options.fontId) {
        params.set("font_id", String(options.fontId));
    } else if (options.fontReference) {
        params.set("font_reference", String(options.fontReference));
        if (state.analysis?.game_dir) {
            params.set("game_dir", String(state.analysis.game_dir));
        }
    } else if (options.path) {
        params.set("path", String(options.path));
    }
    return `${BACKEND_URL}/font_preview?${params.toString()}`;
}


function buildGameFontOptionEntries() {
    const fontCandidates = state.analysis?.gui_baseline?.font_candidates || [];
    return fontCandidates.map((value) => ({
        value,
        label: value,
        source: "game",
        fontId: "",
        previewUrl: buildFontPreviewUrl({ fontReference: value, width: 420, height: 160 }),
    }));
}


function buildSystemFontOptionEntries() {
    return (state.systemFonts || []).map((font) => ({
        value: font.path,
        label: `${font.display_name}${font.style_name ? ` · ${font.style_name}` : ""} · Windows`,
        source: font.source || "system",
        fontId: font.font_id,
        familyName: font.family_name || "",
        styleName: font.style_name || "",
        fileName: font.file_name || "",
        previewUrl: String(font.preview_url || buildFontPreviewUrl({ fontId: font.font_id, width: 360, height: 160 })),
    }));
}


function getCombinedFontOptionEntries(currentValue = "") {
    const byValue = new Map();
    const pushEntry = (entry) => {
        const normalized = normalizeFontOptionEntry(entry);
        if (!normalized || byValue.has(normalized.value)) {
            return;
        }
        byValue.set(normalized.value, normalized);
    };

    buildGameFontOptionEntries().forEach(pushEntry);
    buildSystemFontOptionEntries().forEach(pushEntry);
    if (currentValue) {
        pushEntry({ value: currentValue, label: currentValue, source: "custom" });
    }
    return Array.from(byValue.values());
}


function getFontEntryByValue(value) {
    const normalizedValue = String(value || "").trim();
    if (!normalizedValue) {
        return null;
    }
    return getCombinedFontOptionEntries(normalizedValue).find((entry) => entry.value === normalizedValue) || null;
}


function buildFontDatalistValues() {
    return getCombinedFontOptionEntries()
        .map((entry) => entry.value)
        .filter(Boolean);
}


function updateSuggestionList(datalistElement, values = []) {
    if (!datalistElement) {
        return;
    }
    datalistElement.innerHTML = "";
    values.forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        datalistElement.appendChild(option);
    });
}


function updateFontSelectOptions(selectElement, values = [], currentValue = "") {
    if (!selectElement) {
        return;
    }
    const normalizedValues = Array.from(new Set(["", ...values, currentValue].filter((value) => value !== undefined && value !== null)))
        .map((value) => String(value));
    selectElement.innerHTML = "";
    normalizedValues.forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value ? value : "기존 유지";
        selectElement.appendChild(option);
    });
    selectElement.value = String(currentValue || "");
}


function updateFontPresetOptions(presets = [], selectedId = "") {
    if (!dom.fontPresetSelect) {
        return;
    }
    dom.fontPresetSelect.innerHTML = "";

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "프리셋 선택";
    dom.fontPresetSelect.appendChild(placeholder);

    presets.forEach((preset) => {
        const option = document.createElement("option");
        option.value = preset.id;
        option.textContent = preset.name;
        dom.fontPresetSelect.appendChild(option);
    });
    dom.fontPresetSelect.value = selectedId || "";
}


function getFontPresetById(presetId) {
    if (!presetId) {
        return null;
    }
    const presets = state.analysis?.gui_baseline?.font_presets || [];
    return presets.find((preset) => preset.id === presetId) || null;
}


function applyFontPreset(presetId) {
    const preset = getFontPresetById(presetId);
    if (!preset) {
        return;
    }
    state.selectedFontPresetId = presetId;
    applyPublishSettings(preset.settings || {}, true);
    renderPublishBaseline();
    addLog(`폰트 프리셋 적용: ${preset.name}`, "success");
}


function collectWorldSettings() {
    return {
        world_description: dom.worldDescriptionInput.value.trim(),
        tone_notes: dom.toneNotesInput.value.trim(),
        style_rules: dom.styleRulesInput.value.trim(),
        protected_terms: dom.protectedTermsInput.value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean),
        glossary: captureGlossaryRows(),
    };
}


function setVertexCredentialsStatus(message) {
    if (dom.vertexCredentialsStatus) {
        dom.vertexCredentialsStatus.textContent = message;
    }
}


function parseVertexCredentialsJson(rawText) {
    const text = String(rawText || "").trim();
    if (!text) {
        return null;
    }
    const parsed = JSON.parse(text);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("서비스 계정 JSON 객체 형식이 아닙니다.");
    }
    return parsed;
}


function applyVertexCredentialsJson(rawText, sourceLabel = "붙여넣기") {
    const text = String(rawText || "").trim();
    if (!text) {
        if (dom.vertexCredentialsJsonInput) {
            dom.vertexCredentialsJsonInput.value = "";
        }
        setVertexCredentialsStatus("서비스 계정 JSON이 비어 있습니다.");
        return false;
    }

    const parsed = parseVertexCredentialsJson(text);
    if (dom.vertexCredentialsJsonInput) {
        dom.vertexCredentialsJsonInput.value = JSON.stringify(parsed, null, 2);
    }
    const inferredProjectId = String(parsed.project_id || parsed.project || "").trim();
    if (inferredProjectId && !(dom.vertexProjectIdInput?.value || "").trim()) {
        dom.vertexProjectIdInput.value = inferredProjectId;
    }
    setVertexCredentialsStatus(`${sourceLabel}에서 서비스 계정 JSON을 불러왔습니다.${inferredProjectId ? ` project_id=${inferredProjectId}` : ""}`);
    return true;
}


function clearVertexCredentialsJson() {
    if (dom.vertexCredentialsJsonInput) {
        dom.vertexCredentialsJsonInput.value = "";
    }
    if (dom.vertexCredentialsFileInput) {
        dom.vertexCredentialsFileInput.value = "";
    }
    setVertexCredentialsStatus("서비스 계정 JSON 입력이 비워졌습니다.");
}


function collectVertexSettings() {
    return {
        project_id: dom.vertexProjectIdInput?.value.trim() || "",
        location: dom.vertexLocationInput?.value.trim() || "global",
        credentials_path: dom.vertexCredentialsPathInput?.value.trim() || "",
        credentials_json: dom.vertexCredentialsJsonInput?.value.trim() || "",
    };
}


function collectPublishSettings() {
    return {
        enabled: dom.publishEnabledCheckbox.checked,
        language_code: dom.publishLanguageCodeInput.value.trim(),
        display_name: dom.publishDisplayNameInput.value.trim(),
        gui_language: dom.publishGuiLanguageInput.value.trim(),
        auto_adjust_sizes: dom.autoAdjustFontSizesCheckbox.checked,
        font_preset_id: state.selectedFontPresetId || "",
        dialogue_font: dom.dialogueFontSelect.value.trim(),
        name_font: dom.nameFontSelect.value.trim(),
        options_font: dom.optionsFontSelect.value.trim(),
        interface_font: dom.interfaceFontSelect.value.trim(),
        system_font: dom.systemFontSelect.value.trim(),
        glyph_font: dom.glyphFontSelect.value.trim(),
        dialogue_scale: Number(dom.dialogueScaleInput.value || 1),
        name_scale: Number(dom.nameScaleInput.value || 1),
        options_scale: Number(dom.optionsScaleInput.value || 1),
        interface_scale: Number(dom.interfaceScaleInput.value || 1),
        extra_style_overrides: captureStyleOverrideRows(),
    };
}


function normalizeProtectedTerms(value) {
    if (Array.isArray(value)) {
        return value.map((entry) => String(entry || "").trim()).filter(Boolean).join("\n");
    }
    if (typeof value === "string") {
        return value
            .split(/\r?\n/)
            .map((line) => line.trim())
            .filter(Boolean)
            .join("\n");
    }
    return "";
}


function sanitizeLegacyPublishSettings(publishSettings = {}, targetLanguage = "") {
    const normalizedTarget = String(targetLanguage || "ko")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9_-]+/g, "_")
        .replace(/^_+|_+$/g, "") || "ko";
    const next = { ...(publishSettings || {}) };
    const languageCode = String(next.language_code || "").trim().toLowerCase();
    if (languageCode === `${normalizedTarget}_ai`) {
        next.language_code = `${normalizedTarget}_workbench`;
    }
    return next;
}


function renderPublishBaseline() {
    const baseline = state.analysis?.gui_baseline;
    if (!baseline || !Object.keys(baseline).length) {
        dom.publishBaselineSummary.className = "publish-summary empty-state";
        dom.publishBaselineSummary.textContent = "게임 분석 후 원본 GUI 폰트, 크기, 언어 스위치 훅 요약을 여기서 보여줍니다.";
        updateSuggestionList(dom.fontSuggestionList, []);
        updateSuggestionList(dom.styleSuggestionList, []);
        [
            dom.dialogueFontSelect,
            dom.nameFontSelect,
            dom.optionsFontSelect,
            dom.interfaceFontSelect,
            dom.systemFontSelect,
            dom.glyphFontSelect,
        ].forEach((element) => updateFontSelectOptions(element, [], ""));
        updateFontPresetOptions([], "");
        return;
    }

    updateSuggestionList(dom.styleSuggestionList, baseline.style_candidates || []);
    const fontCandidates = baseline.font_candidates || [];
    updateSuggestionList(dom.fontSuggestionList, fontCandidates);
    updateFontSelectOptions(dom.dialogueFontSelect, fontCandidates, dom.dialogueFontSelect.value);
    updateFontSelectOptions(dom.nameFontSelect, fontCandidates, dom.nameFontSelect.value);
    updateFontSelectOptions(dom.optionsFontSelect, fontCandidates, dom.optionsFontSelect.value);
    updateFontSelectOptions(dom.interfaceFontSelect, fontCandidates, dom.interfaceFontSelect.value);
    updateFontSelectOptions(dom.systemFontSelect, fontCandidates, dom.systemFontSelect.value);
    updateFontSelectOptions(dom.glyphFontSelect, fontCandidates, dom.glyphFontSelect.value);
    updateFontPresetOptions(baseline.font_presets || [], state.selectedFontPresetId);

    const fontDefaults = baseline.font_defaults || {};
    const sizeDefaults = baseline.size_defaults || {};
    const hookItems = (baseline.language_hook_files || [])
        .map((filePath) => `<li>${escapeHtml(filePath)}</li>`)
        .join("");
    const presetItems = (baseline.font_presets || [])
        .map((preset) => `<li><strong>${escapeHtml(preset.name)}</strong> <span class="helper-text">${escapeHtml(preset.description || "")}</span></li>`)
        .join("");

    dom.publishBaselineSummary.className = "publish-summary";
    dom.publishBaselineSummary.innerHTML = `
        <div class="publish-summary-grid">
            <article class="inference-box">
                <h3>기본 GUI 언어</h3>
                <p class="helper-text">${escapeHtml(baseline.base_gui_language || "unicode")}</p>
            </article>
            <article class="inference-box">
                <h3>기본 폰트</h3>
                <p class="helper-text">대사: ${escapeHtml(fontDefaults.dialogue || "-")}</p>
                <p class="helper-text">이름: ${escapeHtml(fontDefaults.name || "-")}</p>
                <p class="helper-text">옵션: ${escapeHtml(fontDefaults.options || "-")}</p>
                <p class="helper-text">UI: ${escapeHtml(fontDefaults.interface || "-")}</p>
            </article>
            <article class="inference-box">
                <h3>기본 크기</h3>
                <p class="helper-text">대사 ${escapeHtml(sizeDefaults.dialogue ?? "-")} / 이름 ${escapeHtml(sizeDefaults.name ?? "-")} / UI ${escapeHtml(sizeDefaults.interface ?? "-")}</p>
                <p class="helper-text">옵션 ${escapeHtml(sizeDefaults.options ?? "-")} / 라벨 ${escapeHtml(sizeDefaults.label ?? "-")} / 알림 ${escapeHtml(sizeDefaults.notify ?? "-")}</p>
            </article>
        </div>
        <p class="helper-text">
            ${baseline.supports_known_languages_menu
                ? "이 게임은 이미 Language()/known_languages() 흔적이 있어서 새 tl 폴더를 언어 메뉴가 자동 인식할 가능성이 큽니다."
                : "자동 언어 메뉴 훅은 보이지 않습니다. publish 결과와 함께 Language(\"...\") 예시 스니펫을 생성합니다."}
        </p>
        ${presetItems ? `<div class="helper-text"><strong>사용 가능한 폰트 프리셋</strong></div><ul class="sample-list">${presetItems}</ul>` : ""}
        ${hookItems ? `<ul class="sample-list">${hookItems}</ul>` : ""}
    `;
}


function applyPublishSettings(publishSettings = {}, overwrite = false) {
    const defaults = state.analysis?.default_publish_settings || {};
    const nextSettings = { ...defaults, ...(publishSettings || {}) };
    const fontCandidates = state.analysis?.gui_baseline?.font_candidates || [];

    if (overwrite || !dom.publishLanguageCodeInput.value.trim()) {
        dom.publishLanguageCodeInput.value = nextSettings.language_code || "";
    }
    if (overwrite || !dom.publishDisplayNameInput.value.trim()) {
        dom.publishDisplayNameInput.value = nextSettings.display_name || "";
    }
    if (overwrite || !dom.publishGuiLanguageInput.value.trim()) {
        dom.publishGuiLanguageInput.value = nextSettings.gui_language || "";
    }

    dom.publishEnabledCheckbox.checked = nextSettings.enabled !== false;
    dom.autoAdjustFontSizesCheckbox.checked = nextSettings.auto_adjust_sizes !== false;
    state.selectedFontPresetId = nextSettings.font_preset_id || state.selectedFontPresetId || "";
    updateFontPresetOptions(state.analysis?.gui_baseline?.font_presets || [], state.selectedFontPresetId);

    const fontMappings = [
        ["dialogue_font", dom.dialogueFontSelect],
        ["name_font", dom.nameFontSelect],
        ["options_font", dom.optionsFontSelect],
        ["interface_font", dom.interfaceFontSelect],
        ["system_font", dom.systemFontSelect],
        ["glyph_font", dom.glyphFontSelect],
    ];
    fontMappings.forEach(([key, element]) => {
        const nextValue = nextSettings[key] || "";
        updateFontSelectOptions(element, fontCandidates, overwrite ? nextValue : element.value || nextValue);
        if (overwrite || !element.value.trim()) {
            element.value = nextValue;
        }
    });

    const scaleMappings = [
        ["dialogue_scale", dom.dialogueScaleInput],
        ["name_scale", dom.nameScaleInput],
        ["options_scale", dom.optionsScaleInput],
        ["interface_scale", dom.interfaceScaleInput],
    ];
    scaleMappings.forEach(([key, element]) => {
        const htmlDefaultValue = element.defaultValue ?? "";
        if (overwrite || !element.value || element.value === htmlDefaultValue) {
            element.value = nextSettings[key] ?? 1;
        }
    });

    if (overwrite || !captureStyleOverrideRows().some((entry) => entry.style_name || entry.font_path || entry.size)) {
        setStyleOverrideRows(nextSettings.extra_style_overrides || []);
    }
}

function updateFontSelectOptions(selectElement, values = [], currentValue = "") {
    if (!selectElement) {
        return;
    }
    const normalizedEntries = [];
    const seen = new Set();
    const pushEntry = (entry) => {
        const normalized = normalizeFontOptionEntry(entry);
        if (!normalized || seen.has(normalized.value)) {
            return;
        }
        seen.add(normalized.value);
        normalizedEntries.push(normalized);
    };

    pushEntry({ value: "", label: "기존 유지" });
    values.forEach(pushEntry);
    if (currentValue) {
        pushEntry(getFontEntryByValue(currentValue) || { value: currentValue, label: currentValue });
    }

    selectElement.innerHTML = "";
    normalizedEntries.forEach((entry) => {
        const option = document.createElement("option");
        option.value = entry.value;
        option.textContent = entry.label || (entry.value ? entry.value : "기존 유지");
        selectElement.appendChild(option);
    });
    selectElement.value = String(currentValue || "");
}


function setFontBrowserStatus(message, type = "info") {
    if (!dom.fontBrowserStatus) {
        return;
    }
    dom.fontBrowserStatus.textContent = message;
    dom.fontBrowserStatus.dataset.state = type;
}


function getPublishFontFieldMap() {
    return {
        dialogue_font: dom.dialogueFontSelect,
        name_font: dom.nameFontSelect,
        options_font: dom.optionsFontSelect,
        interface_font: dom.interfaceFontSelect,
        system_font: dom.systemFontSelect,
        glyph_font: dom.glyphFontSelect,
    };
}


function getPublishFontLabel(key) {
    return {
        dialogue_font: "대사 폰트",
        name_font: "이름 폰트",
        options_font: "옵션 폰트",
        interface_font: "UI 폰트",
        system_font: "시스템 폰트",
        glyph_font: "Glyph 폰트",
    }[key] || key;
}


function getPublishScaleFieldMap() {
    return {
        dialogue_font: dom.dialogueScaleInput,
        name_font: dom.nameScaleInput,
        options_font: dom.optionsScaleInput,
        interface_font: dom.interfaceScaleInput,
    };
}


function getPublishSizeBaselineMap() {
    const sizeDefaults = state.analysis?.gui_baseline?.size_defaults || {};
    return {
        dialogue_font: Number(sizeDefaults.dialogue || 0),
        name_font: Number(sizeDefaults.name || 0),
        options_font: Number(sizeDefaults.options || 0),
        interface_font: Number(sizeDefaults.interface || 0),
        system_font: Number(sizeDefaults.notify || sizeDefaults.interface || 0),
        glyph_font: Number(sizeDefaults.label || sizeDefaults.interface || 0),
    };
}


function getPublishFontSizeSummary(key) {
    const baselineSize = Number(getPublishSizeBaselineMap()[key] || 0);
    const scaleField = getPublishScaleFieldMap()[key] || null;
    const scale = scaleField ? Number(scaleField.value || 1) || 1 : 1;
    const effectiveSize = baselineSize > 0 ? Number((baselineSize * scale).toFixed(1)) : 0;
    return {
        adjustable: Boolean(scaleField),
        baselineSize,
        scale,
        effectiveSize,
        scaleFieldId: scaleField?.id || "",
    };
}


function getFilteredSystemFonts() {
    const query = state.fontBrowserQuery.trim().toLowerCase();
    return (state.systemFonts || []).filter((font) => {
        if (!query) {
            return true;
        }
        const haystack = [font.display_name, font.family_name, font.style_name, font.file_name]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();
        return haystack.includes(query);
    });
}

function renderCurrentFontPreviewGrid() {
    if (!dom.currentFontPreviewGrid) {
        return;
    }
    dom.currentFontPreviewGrid.innerHTML = "";

    const fieldMap = getPublishFontFieldMap();
    const cards = Object.entries(fieldMap).map(([key, element]) => ({
        key,
        label: getPublishFontLabel(key),
        value: element?.value.trim() || "",
        entry: getFontEntryByValue(element?.value.trim() || ""),
        sizeSummary: getPublishFontSizeSummary(key),
    }));

    if (!cards.some((card) => card.value)) {
        dom.currentFontPreviewGrid.className = "current-font-preview-grid empty-state";
        dom.currentFontPreviewGrid.textContent = "폰트를 선택하면 현재 슬롯별 미리보기가 여기에 표시됩니다.";
        return;
    }

    dom.currentFontPreviewGrid.className = "current-font-preview-grid";
    cards.forEach((card) => {
        const article = document.createElement("article");
        article.className = "font-preview-card";

        const heading = document.createElement("div");
        heading.className = "font-preview-card-head";
        heading.innerHTML = `
            <strong>${escapeHtml(card.label)}</strong>
            <span class="helper-text">${escapeHtml(card.entry?.label || (card.value || "기존 유지"))}</span>
        `;
        article.appendChild(heading);

        const sizeMeta = document.createElement("div");
        sizeMeta.className = "font-size-meta";
        const sizeBits = [];
        if (card.sizeSummary.baselineSize > 0) {
            sizeBits.push(`<span class="font-size-chip">기본 ${escapeHtml(card.sizeSummary.baselineSize)}px</span>`);
        }
        if (card.sizeSummary.adjustable) {
            sizeBits.push(`<span class="font-size-chip">배율 ${escapeHtml(card.sizeSummary.scale.toFixed(2))}</span>`);
        }
        if (card.sizeSummary.effectiveSize > 0) {
            sizeBits.push(`<span class="font-size-chip strong">예상 ${escapeHtml(card.sizeSummary.effectiveSize)}px</span>`);
        }
        sizeMeta.innerHTML = sizeBits.join("");
        article.appendChild(sizeMeta);

        if (card.value) {
            const preview = document.createElement("img");
            preview.className = "font-preview-image";
            preview.alt = `${card.label} preview`;
            preview.loading = "lazy";
            preview.src = card.entry?.previewUrl || buildFontPreviewUrl({ fontReference: card.value, width: 420, height: 160 });
            article.appendChild(preview);
        } else {
            const empty = document.createElement("div");
            empty.className = "font-preview-empty";
            empty.textContent = "기존 폰트를 유지합니다.";
            article.appendChild(empty);
        }

        if (card.sizeSummary.adjustable) {
            const controls = document.createElement("div");
            controls.className = "font-size-controls";
            controls.innerHTML = `
                <label class="font-size-field">
                    <span>배율</span>
                    <input
                        type="number"
                        min="0.6"
                        max="1.8"
                        step="0.02"
                        value="${escapeHtml(card.sizeSummary.scale.toFixed(2))}"
                        data-scale-field-id="${escapeHtml(card.sizeSummary.scaleFieldId)}"
                    >
                </label>
                <div class="font-size-caption">기본 ${escapeHtml(card.sizeSummary.baselineSize || "-")}px 기준으로 publish 시 자동 반영됩니다.</div>
            `;
            article.appendChild(controls);
        }

        dom.currentFontPreviewGrid.appendChild(article);
    });
}


function renderSystemFontGallery() {
    if (!dom.systemFontGallery) {
        return;
    }

    if (state.systemFontsLoading) {
        dom.systemFontGallery.className = "system-font-gallery empty-state";
        dom.systemFontGallery.textContent = "Windows 글꼴을 읽는 중입니다...";
        return;
    }
    if (!state.systemFontsLoaded) {
        dom.systemFontGallery.className = "system-font-gallery empty-state";
        dom.systemFontGallery.textContent = "윈도우 글꼴을 불러오면 여기에 미리보기 카드가 표시됩니다.";
        return;
    }

    const filtered = getFilteredSystemFonts();
    const visibleFonts = filtered.slice(0, query ? 72 : 36);
    setFontBrowserStatus(
        `Windows 글꼴 ${state.systemFonts.length}개 중 ${visibleFonts.length}개 표시 · 적용 슬롯: ${getPublishFontLabel(state.fontBrowserTarget)}`,
        visibleFonts.length ? "ready" : "warning",
    );

    if (!visibleFonts.length) {
        dom.systemFontGallery.className = "system-font-gallery empty-state";
        dom.systemFontGallery.textContent = "검색 조건에 맞는 글꼴이 없습니다.";
        return;
    }

    dom.systemFontGallery.className = "system-font-gallery";
    dom.systemFontGallery.innerHTML = "";
    visibleFonts.forEach((font) => {
        const article = document.createElement("article");
        article.className = "font-browser-card";

        const preview = document.createElement("img");
        preview.className = "font-preview-image";
        preview.alt = `${font.display_name} preview`;
        preview.loading = "lazy";
        preview.src = buildFontPreviewUrl({ fontId: font.font_id, width: 520, height: 112 });
        article.appendChild(preview);

        const meta = document.createElement("div");
        meta.className = "font-browser-meta";
        meta.innerHTML = `
            <strong>${escapeHtml(font.display_name || font.file_name || font.path)}</strong>
            <span class="helper-text">${escapeHtml([font.style_name, font.file_name].filter(Boolean).join(" · "))}</span>
        `;
        article.appendChild(meta);

        const button = document.createElement("button");
        button.type = "button";
        button.className = "secondary-button";
        button.dataset.action = "apply-system-font";
        button.dataset.fontId = font.font_id;
        button.textContent = `${getPublishFontLabel(state.fontBrowserTarget)}에 적용`;
        article.appendChild(button);

        dom.systemFontGallery.appendChild(article);
    });
}

function renderSystemFontGallery() {
    if (!dom.systemFontGallery) {
        return;
    }

    const setPaginationState = (page, totalPages, canGoPrev, canGoNext) => {
        if (dom.fontBrowserPageInfo) {
            dom.fontBrowserPageInfo.textContent = `페이지 ${page} / ${totalPages}`;
        }
        if (dom.fontBrowserPrevButton) {
            dom.fontBrowserPrevButton.disabled = !canGoPrev;
        }
        if (dom.fontBrowserNextButton) {
            dom.fontBrowserNextButton.disabled = !canGoNext;
        }
    };

    if (state.systemFontsLoading) {
        dom.systemFontGallery.className = "system-font-gallery empty-state";
        dom.systemFontGallery.textContent = "Windows 글꼴을 읽는 중입니다...";
        setPaginationState(1, 1, false, false);
        return;
    }
    if (!state.systemFontsLoaded) {
        dom.systemFontGallery.className = "system-font-gallery empty-state";
        dom.systemFontGallery.textContent = "윈도우 글꼴을 불러오면 여기에 미리보기 카드가 표시됩니다.";
        setPaginationState(1, 1, false, false);
        return;
    }

    const query = state.fontBrowserQuery.trim().toLowerCase();
    const filtered = (state.systemFonts || []).filter((font) => {
        if (!query) {
            return true;
        }
        const haystack = [font.display_name, font.family_name, font.style_name, font.file_name]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();
        return haystack.includes(query);
    });
    const totalPages = Math.max(1, Math.ceil(filtered.length / FONT_BROWSER_PAGE_SIZE));
    state.fontBrowserPage = Math.min(Math.max(state.fontBrowserPage || 0, 0), totalPages - 1);
    const startIndex = state.fontBrowserPage * FONT_BROWSER_PAGE_SIZE;
    const endIndex = startIndex + FONT_BROWSER_PAGE_SIZE;
    const visibleFonts = filtered.slice(startIndex, endIndex);
    const pageLabel = filtered.length
        ? `${startIndex + 1}-${Math.min(endIndex, filtered.length)}`
        : "0";
    const targetSizeSummary = getPublishFontSizeSummary(state.fontBrowserTarget);
    const targetSizeLabel = targetSizeSummary.effectiveSize > 0
        ? ` · 예상 크기 ${targetSizeSummary.effectiveSize}px`
        : "";
    setFontBrowserStatus(
        `Windows 글꼴 ${state.systemFonts.length}개 중 ${filtered.length}개 검색 결과 · 현재 ${pageLabel} 표시 · 적용 슬롯: ${getPublishFontLabel(state.fontBrowserTarget)}${targetSizeLabel}`,
        visibleFonts.length ? "ready" : "warning",
    );
    setPaginationState(
        state.fontBrowserPage + 1,
        totalPages,
        state.fontBrowserPage > 0,
        state.fontBrowserPage < totalPages - 1,
    );

    if (!visibleFonts.length) {
        dom.systemFontGallery.className = "system-font-gallery empty-state";
        dom.systemFontGallery.textContent = "검색 조건에 맞는 글꼴이 없습니다.";
        return;
    }

    dom.systemFontGallery.className = "system-font-gallery";
    dom.systemFontGallery.innerHTML = "";
    visibleFonts.forEach((font) => {
        const article = document.createElement("article");
        article.className = "font-browser-card";

        const preview = document.createElement("img");
        preview.className = "font-preview-image";
        preview.alt = `${font.display_name} preview`;
        preview.loading = "lazy";
        preview.src = buildFontPreviewUrl({
            fontId: font.font_id,
            width: 360,
            height: 160,
            sampleText: getFontBrowserSampleText(),
        });
        article.appendChild(preview);

        const meta = document.createElement("div");
        meta.className = "font-browser-meta";
        meta.innerHTML = `
            <strong>${escapeHtml(font.display_name || font.file_name || font.path)}</strong>
            <span class="helper-text">${escapeHtml([font.style_name, font.file_name].filter(Boolean).join(" · "))}</span>
            ${targetSizeSummary.effectiveSize > 0 ? `<span class="helper-text">이 슬롯 적용 예상 크기 ${escapeHtml(targetSizeSummary.effectiveSize)}px</span>` : ""}
        `;
        article.appendChild(meta);

        const button = document.createElement("button");
        button.type = "button";
        button.className = "secondary-button";
        button.dataset.action = "apply-system-font";
        button.dataset.fontId = font.font_id;
        button.textContent = `${getPublishFontLabel(state.fontBrowserTarget)}${targetSizeSummary.effectiveSize > 0 ? ` (${targetSizeSummary.effectiveSize}px)` : ""}에 적용`;
        article.appendChild(button);

        dom.systemFontGallery.appendChild(article);
    });
}


function renderPublishBaseline() {
    const baseline = state.analysis?.gui_baseline;
    const fontOptions = getCombinedFontOptionEntries();

    updateSuggestionList(dom.styleSuggestionList, baseline?.style_candidates || []);
    updateSuggestionList(dom.fontSuggestionList, buildFontDatalistValues());
    [
        dom.dialogueFontSelect,
        dom.nameFontSelect,
        dom.optionsFontSelect,
        dom.interfaceFontSelect,
        dom.systemFontSelect,
        dom.glyphFontSelect,
    ].forEach((element) => updateFontSelectOptions(element, fontOptions, element?.value || ""));
    updateFontPresetOptions(baseline?.font_presets || [], state.selectedFontPresetId);
    renderCurrentFontPreviewGrid();
    renderSystemFontGallery();

    if (!baseline || !Object.keys(baseline).length) {
        dom.publishBaselineSummary.className = "publish-summary empty-state";
        dom.publishBaselineSummary.textContent = "게임 분석 후 기본 GUI 폰트, 크기, 언어 스위치 훅을 여기서 요약합니다.";
        return;
    }

    const fontDefaults = baseline.font_defaults || {};
    const sizeDefaults = baseline.size_defaults || {};
    const hookItems = (baseline.language_hook_files || [])
        .map((filePath) => `<li>${escapeHtml(filePath)}</li>`)
        .join("");
    const presetItems = (baseline.font_presets || [])
        .map((preset) => `<li><strong>${escapeHtml(preset.name)}</strong> <span class="helper-text">${escapeHtml(preset.description || "")}</span></li>`)
        .join("");

    dom.publishBaselineSummary.className = "publish-summary";
    dom.publishBaselineSummary.innerHTML = `
        <div class="publish-summary-grid">
            <article class="inference-box">
                <h3>기본 GUI 언어</h3>
                <p class="helper-text">${escapeHtml(baseline.base_gui_language || "unicode")}</p>
            </article>
            <article class="inference-box">
                <h3>기본 폰트</h3>
                <p class="helper-text">대사 ${escapeHtml(fontDefaults.dialogue || "-")}</p>
                <p class="helper-text">이름 ${escapeHtml(fontDefaults.name || "-")}</p>
                <p class="helper-text">옵션 ${escapeHtml(fontDefaults.options || "-")}</p>
                <p class="helper-text">UI ${escapeHtml(fontDefaults.interface || "-")}</p>
            </article>
            <article class="inference-box">
                <h3>기본 크기</h3>
                <p class="helper-text">대사 ${escapeHtml(sizeDefaults.dialogue ?? "-")} / 이름 ${escapeHtml(sizeDefaults.name ?? "-")} / UI ${escapeHtml(sizeDefaults.interface ?? "-")}</p>
                <p class="helper-text">옵션 ${escapeHtml(sizeDefaults.options ?? "-")} / 라벨 ${escapeHtml(sizeDefaults.label ?? "-")} / 알림 ${escapeHtml(sizeDefaults.notify ?? "-")}</p>
            </article>
        </div>
        <p class="helper-text">
            ${baseline.supports_known_languages_menu
                ? "이 게임은 Language()/known_languages() 흔적이 있어 새 tl 폴더를 언어 메뉴가 자동 인식할 가능성이 높습니다."
                : "자동 언어 메뉴 흔적이 보이지 않습니다. publish 결과와 함께 Language(\"...\") 예시 안내문을 생성합니다."}
        </p>
        ${presetItems ? `<div class="helper-text"><strong>사용 가능한 폰트 프리셋</strong></div><ul class="sample-list">${presetItems}</ul>` : ""}
        ${hookItems ? `<ul class="sample-list">${hookItems}</ul>` : ""}
    `;
}


function applyPublishSettings(publishSettings = {}, overwrite = false) {
    const defaults = state.analysis?.default_publish_settings || {};
    const nextSettings = { ...defaults, ...(publishSettings || {}) };
    const fontOptions = getCombinedFontOptionEntries();

    if (overwrite || !dom.publishLanguageCodeInput.value.trim()) {
        dom.publishLanguageCodeInput.value = nextSettings.language_code || "";
    }
    if (overwrite || !dom.publishDisplayNameInput.value.trim()) {
        dom.publishDisplayNameInput.value = nextSettings.display_name || "";
    }
    if (overwrite || !dom.publishGuiLanguageInput.value.trim()) {
        dom.publishGuiLanguageInput.value = nextSettings.gui_language || "";
    }

    dom.publishEnabledCheckbox.checked = nextSettings.enabled !== false;
    dom.autoAdjustFontSizesCheckbox.checked = nextSettings.auto_adjust_sizes !== false;
    state.selectedFontPresetId = nextSettings.font_preset_id || state.selectedFontPresetId || "";
    updateFontPresetOptions(state.analysis?.gui_baseline?.font_presets || [], state.selectedFontPresetId);

    const fontMappings = [
        ["dialogue_font", dom.dialogueFontSelect],
        ["name_font", dom.nameFontSelect],
        ["options_font", dom.optionsFontSelect],
        ["interface_font", dom.interfaceFontSelect],
        ["system_font", dom.systemFontSelect],
        ["glyph_font", dom.glyphFontSelect],
    ];
    fontMappings.forEach(([key, element]) => {
        const nextValue = nextSettings[key] || "";
        updateFontSelectOptions(element, fontOptions, overwrite ? nextValue : element.value || nextValue);
        if (overwrite || !element.value.trim()) {
            element.value = nextValue;
        }
    });

    const scaleMappings = [
        ["dialogue_scale", dom.dialogueScaleInput],
        ["name_scale", dom.nameScaleInput],
        ["options_scale", dom.optionsScaleInput],
        ["interface_scale", dom.interfaceScaleInput],
    ];
    scaleMappings.forEach(([key, element]) => {
        const htmlDefaultValue = element.defaultValue ?? "";
        if (overwrite || !element.value || element.value === htmlDefaultValue) {
            element.value = nextSettings[key] ?? 1;
        }
    });

    if (overwrite || !captureStyleOverrideRows().some((entry) => entry.style_name || entry.font_path || entry.size)) {
        setStyleOverrideRows(nextSettings.extra_style_overrides || []);
    }
    renderCurrentFontPreviewGrid();
    renderSystemFontGallery();
}


function applyFontValueToTarget(targetKey, fontValue) {
    const fieldMap = getPublishFontFieldMap();
    const targetElement = fieldMap[targetKey];
    if (!targetElement) {
        return;
    }
    updateFontSelectOptions(targetElement, getCombinedFontOptionEntries(fontValue), fontValue);
    targetElement.value = fontValue;
    state.fontBrowserTarget = targetKey;
    if (dom.fontBrowserTargetSelect) {
        dom.fontBrowserTargetSelect.value = targetKey;
    }
    handlePublishControlInput({ target: targetElement });
    renderCurrentFontPreviewGrid();
    renderSystemFontGallery();
}


async function loadSystemFonts(force = false) {
    if (state.systemFontsLoading) {
        return;
    }
    if (state.systemFontsLoaded && !force) {
        renderSystemFontGallery();
        return;
    }

    state.systemFontsLoading = true;
    state.fontBrowserPage = 0;
    setFontBrowserStatus("Windows 글꼴을 읽는 중입니다...", "loading");
    renderSystemFontGallery();
    try {
        const response = await apiGet("/system_fonts");
        state.systemFonts = response.fonts || [];
        state.systemFontsLoaded = true;
        setFontBrowserStatus(`Windows 글꼴 ${state.systemFonts.length}개를 불러왔습니다.`, "ready");
        renderPublishBaseline();
    } catch (error) {
        setFontBrowserStatus(`Windows 글꼴 로드 실패: ${error.message}`, "error");
        addLog(`Windows 글꼴 로드 실패: ${error.message}`, "error");
    } finally {
        state.systemFontsLoading = false;
        renderSystemFontGallery();
    }
}


function handleSystemFontGalleryClick(event) {
    const applyButton = event.target.closest("[data-action='apply-system-font']");
    if (!applyButton) {
        return;
    }
    const fontId = applyButton.dataset.fontId || "";
    const fontEntry = (state.systemFonts || []).find((entry) => entry.font_id === fontId);
    if (!fontEntry) {
        return;
    }
    applyFontValueToTarget(state.fontBrowserTarget, fontEntry.path);
    addLog(`글꼴 적용: ${fontEntry.display_name} -> ${getPublishFontLabel(state.fontBrowserTarget)}`, "success");
}


function applyFirstFilteredSystemFont() {
    if (!state.systemFontsLoaded || state.systemFontsLoading) {
        setFontBrowserStatus("먼저 Windows 글꼴 목록을 불러와 주세요.", "warning");
        return;
    }
    const filtered = getFilteredSystemFonts();
    const fontEntry = filtered[0];
    if (!fontEntry) {
        setFontBrowserStatus("검색 결과가 없어 적용할 글꼴을 찾지 못했습니다.", "warning");
        return;
    }
    state.fontBrowserPage = 0;
    applyFontValueToTarget(state.fontBrowserTarget, fontEntry.path);
    addLog(`검색 결과 첫 글꼴 적용: ${fontEntry.display_name} -> ${getPublishFontLabel(state.fontBrowserTarget)}`, "success");
}

function applyWorldSettings(worldSettings = {}, overwrite = false) {
    if (overwrite || !dom.worldDescriptionInput.value.trim()) {
        dom.worldDescriptionInput.value = worldSettings.world_description || "";
    }
    if (overwrite || !dom.toneNotesInput.value.trim()) {
        dom.toneNotesInput.value = worldSettings.tone_notes || "";
    }
    if (overwrite || !dom.styleRulesInput.value.trim()) {
        dom.styleRulesInput.value = worldSettings.style_rules || "";
    }
    if (overwrite || !dom.protectedTermsInput.value.trim()) {
        dom.protectedTermsInput.value = normalizeProtectedTerms(worldSettings.protected_terms);
    }
    if (overwrite || captureGlossaryRows().length === 0) {
        const glossaryEntries = (worldSettings.glossary && worldSettings.glossary.length)
            ? worldSettings.glossary
            : (state.analysis?.glossary_suggestions || []).slice(0, 10);
        setGlossaryRows(glossaryEntries);
    }
}


function captureCurrentCharacterProfiles() {
    if (!state.selectedCharacterId) {
        return;
    }

    const detailPanel = dom.characterGrid.querySelector("[data-role='character-detail']");
    if (!detailPanel) {
        return;
    }

    const currentProfile = state.characterProfiles[state.selectedCharacterId] || {};
    state.characterProfiles[state.selectedCharacterId] = {
        ...currentProfile,
        tone_preset_id: detailPanel.querySelector("[data-field='tone_preset_id']")?.value || currentProfile.tone_preset_id || "custom",
        display_name: detailPanel.querySelector("[data-field='display_name']")?.value.trim() || "",
        role: detailPanel.querySelector("[data-field='role']")?.value.trim() || "",
        tone: detailPanel.querySelector("[data-field='tone']")?.value.trim() || "",
        notes: detailPanel.querySelector("[data-field='notes']")?.value.trim() || "",
    };
}


function ensureCharacterProfiles() {
    if (!state.analysis) {
        return;
    }
    const defaults = state.analysis.default_character_profiles || {};
    const orderedCharacters = [...(state.analysis.characters || [])]
        .sort((left, right) => {
            if (isSystemCharacter(left) !== isSystemCharacter(right)) {
                return Number(isSystemCharacter(left)) - Number(isSystemCharacter(right));
            }
            return (right.line_count || 0) - (left.line_count || 0);
        });
    state.analysis.characters = orderedCharacters;

    orderedCharacters.forEach((character) => {
        const speakerId = character.speaker_id;
        const existing = state.characterProfiles[speakerId] || {};
        const fallback = defaults[speakerId] || {};
        state.characterProfiles[speakerId] = {
            tone_preset_id: existing.tone_preset_id || fallback.tone_preset_id || "custom",
            display_name: existing.display_name || fallback.display_name || character.display_name || "",
            role: existing.role || fallback.role || "",
            tone: existing.tone || fallback.tone || "",
            notes: existing.notes || fallback.notes || "",
        };
    });

    const hasSelectedCharacter = orderedCharacters.some((character) => character.speaker_id === state.selectedCharacterId);
    if (!hasSelectedCharacter) {
        const firstPlayableCharacter = orderedCharacters.find((character) => !isSystemCharacter(character));
        state.selectedCharacterId = firstPlayableCharacter?.speaker_id || orderedCharacters[0]?.speaker_id || null;
    }
}


function collectCharacterProfiles() {
    captureCurrentCharacterProfiles();
    return state.characterProfiles;
}


function renderSummary() {
    if (!state.analysis) {
        dom.summaryFiles.textContent = "0";
        dom.summaryItems.textContent = "0";
        dom.summaryCharacters.textContent = "0";
        dom.summaryAdult.textContent = "0";
        dom.summaryUntranslated.textContent = "0";
        dom.summaryGameTranslated.textContent = "0";
        dom.summaryWorkbenchTranslated.textContent = "0";
        return;
    }
    dom.summaryFiles.textContent = String(state.analysis.summary.file_count || 0);
    dom.summaryItems.textContent = String(state.analysis.summary.item_count || 0);
    dom.summaryCharacters.textContent = String((state.analysis.characters || []).length);
    dom.summaryAdult.textContent = String(state.analysis.summary.adult_item_count || 0);
    dom.summaryUntranslated.textContent = String(state.analysis.summary.untranslated_item_count || 0);
    dom.summaryGameTranslated.textContent = String(state.analysis.summary.game_translated_item_count || 0);
    dom.summaryWorkbenchTranslated.textContent = String(state.analysis.summary.workbench_translated_item_count || 0);
}


function getTranslationSourceDetail(source) {
    const raw = String(source || "").trim();
    if (!raw.includes(":")) {
        return "";
    }
    return raw.split(":").slice(1).join(":").trim();
}


function hasMeaningfulTranslation(text, sourceText = "") {
    const normalizedText = String(text || "").trim();
    if (!normalizedText) {
        return false;
    }
    return normalizedText !== String(sourceText || "").trim();
}


function buildTranslationPreviewLines(item) {
    const lines = [];
    if (hasMeaningfulTranslation(item.connected_translation_text, item.source_text)) {
        const sourceLabel = item.connected_translation_source ? `게임 연결 (${item.connected_translation_source})` : "게임 연결";
        lines.push(`
            <div class="translation-preview-line">
                <strong>${escapeHtml(sourceLabel)}</strong>
                <span>${escapeHtml(item.connected_translation_text)}</span>
            </div>
        `);
    }
    if (
        hasMeaningfulTranslation(item.workbench_translation_text, item.source_text)
        && item.workbench_translation_text !== item.connected_translation_text
    ) {
        const sourceLabel = item.workbench_translation_source ? `워크벤치 출력 (${item.workbench_translation_source})` : "워크벤치 출력";
        lines.push(`
            <div class="translation-preview-line">
                <strong>${escapeHtml(sourceLabel)}</strong>
                <span>${escapeHtml(item.workbench_translation_text)}</span>
            </div>
        `);
    }
    if (!lines.length) {
        lines.push('<div class="helper-text">현재 연결된 번역이 없습니다.</div>');
    }
    return `<div class="translation-preview-stack">${lines.join("")}</div>`;
}


function renderFileTable() {
    if (!state.analysis || !state.analysis.files?.length) {
        dom.fileTable.className = "file-table empty-state";
        dom.fileTable.textContent = "분석 결과가 아직 없습니다.";
        return;
    }
    dom.fileTable.className = "file-table";
    dom.fileTable.innerHTML = "";
    state.analysis.files.forEach((file) => {
        const checked = state.selectedFiles.has(file.file_relative_path) ? "checked" : "";
        const topPreview = (file.preview_items || []).slice(0, 2)
            .map((item) => `
                <div class="helper-text">
                    ${item.speaker_name || item.speaker_id || item.kind}: ${item.source_preview}
                    <span class="pill subtle">${escapeHtml(getTranslationStatusLabel(item.translation_status))}</span>
                </div>
            `)
            .join("");
        const row = document.createElement("label");
        row.className = "file-row";
        row.innerHTML = `
            <input type="checkbox" data-path="${file.file_relative_path}" ${checked}>
            <div>
                <strong>${file.file_name}</strong>
                <div class="helper-text">${file.file_relative_path}</div>
                ${topPreview}
            </div>
            <div class="pill-list compact">
                <span class="pill">${file.file_mode}</span>
                <span class="pill subtle">미번역 ${file.untranslated_item_count || 0}</span>
                <span class="pill subtle">기존 ${file.game_translated_item_count || 0}</span>
                <span class="pill subtle">워크벤치 ${file.workbench_translated_item_count || 0}</span>
            </div>
            <div><strong>${file.item_count}</strong><div class="helper-text">항목</div></div>
            <div><strong>${file.adult_item_count}</strong><div class="helper-text">성인 큐</div></div>
        `;
        dom.fileTable.appendChild(row);
    });
}


function renderUploadList() {
    if (!state.uploadedFiles.length) {
        dom.uploadList.innerHTML = '<p class="muted">업로드된 파일이 없습니다.</p>';
        return;
    }
    dom.uploadList.innerHTML = "";
    state.uploadedFiles.forEach((file) => {
        const row = document.createElement("div");
        row.className = "dialogue-row";
        row.innerHTML = `
            <div><strong>${file.file_name}</strong></div>
            <div class="helper-text">${(file.file_content || "").length.toLocaleString()} chars</div>
        `;
        dom.uploadList.appendChild(row);
    });
}


function renderWorldInference() {
    const defaults = state.analysis?.default_world_settings;
    if (!defaults) {
        dom.worldInferenceText.textContent = "분석 후 자동으로 채워집니다.";
        dom.toneInferenceText.textContent = "분석 후 자동으로 채워집니다.";
        dom.styleInferenceText.textContent = "분석 후 자동으로 채워집니다.";
        return;
    }
    dom.worldInferenceText.textContent = defaults.world_description || "추정값 없음";
    dom.toneInferenceText.textContent = defaults.tone_notes || "추정값 없음";
    dom.styleInferenceText.textContent = defaults.style_rules || "추정값 없음";
}


function renderDialoguePreview() {
    const previewItems = state.analysis?.dialogue_preview || [];
    if (!previewItems.length) {
        dom.dialoguePreviewList.className = "dialogue-preview empty-state";
        dom.dialoguePreviewList.textContent = "분석 결과가 아직 없습니다.";
        return;
    }
    dom.dialoguePreviewList.className = "dialogue-preview";
    dom.dialoguePreviewList.innerHTML = "";
    previewItems.slice(0, 24).forEach((item) => {
        const row = document.createElement("div");
        row.className = "dialogue-row";
        row.innerHTML = `
            <div><strong>${item.speaker_name || item.speaker_id || "Narration"}</strong> · ${item.file_relative_path}:${item.line_number}</div>
            <div class="helper-text">${item.source_text}</div>
        `;
        dom.dialoguePreviewList.appendChild(row);
    });
}


function renderFileTable() {
    if (!state.analysis || !state.analysis.files?.length) {
        dom.fileTable.className = "file-table empty-state";
        dom.fileTable.textContent = "분석 결과가 아직 없습니다.";
        return;
    }
    dom.fileTable.className = "file-table";
    dom.fileTable.innerHTML = "";
    state.analysis.files.forEach((file) => {
        const checked = state.selectedFiles.has(file.file_relative_path) ? "checked" : "";
        const topPreview = (file.preview_items || []).slice(0, 2)
            .map((item) => `
                <div class="helper-text">
                    ${item.speaker_name || item.speaker_id || item.kind}: ${item.source_preview}
                    <span class="pill subtle">${escapeHtml(getTranslationStatusLabel(item.translation_status, item.translation_source))}</span>
                </div>
            `)
            .join("");
        const row = document.createElement("label");
        row.className = "file-row";
        row.innerHTML = `
            <input type="checkbox" data-path="${file.file_relative_path}" ${checked}>
            <div>
                <strong>${file.file_name}</strong>
                <div class="helper-text">${file.file_relative_path}</div>
                ${topPreview}
            </div>
            <div class="pill-list compact">
                <span class="pill">${file.file_mode}</span>
                <span class="pill subtle">미번역 ${file.untranslated_item_count || 0}</span>
                <span class="pill subtle">연결 ${file.game_translated_item_count || 0}</span>
                <span class="pill subtle">워크벤치 ${file.workbench_translated_item_count || 0}</span>
            </div>
            <div><strong>${file.item_count}</strong><div class="helper-text">항목</div></div>
            <div><strong>${file.adult_item_count}</strong><div class="helper-text">성인 큐</div></div>
        `;
        dom.fileTable.appendChild(row);
    });
}


function renderUploadList() {
    if (!state.uploadedFiles.length) {
        dom.uploadList.innerHTML = '<p class="muted">업로드된 파일이 없습니다.</p>';
        return;
    }
    dom.uploadList.innerHTML = "";
    state.uploadedFiles.forEach((file) => {
        const row = document.createElement("div");
        row.className = "dialogue-row";
        row.innerHTML = `
            <div><strong>${file.file_name}</strong></div>
            <div class="helper-text">${(file.file_content || "").length.toLocaleString()} chars</div>
        `;
        dom.uploadList.appendChild(row);
    });
}


function renderDialoguePreview() {
    const previewItems = state.analysis?.dialogue_preview || [];
    if (!previewItems.length) {
        dom.dialoguePreviewList.className = "dialogue-preview empty-state";
        dom.dialoguePreviewList.textContent = "분석 결과가 아직 없습니다.";
        return;
    }
    dom.dialoguePreviewList.className = "dialogue-preview";
    dom.dialoguePreviewList.innerHTML = "";
    previewItems.slice(0, 24).forEach((item) => {
        const row = document.createElement("div");
        row.className = "dialogue-row";
        const translationBadge = getTranslationStatusLabel(item.translation_status, item.translation_source);
        const translationPreview = buildTranslationPreviewLines(item);
        row.innerHTML = `
            <div class="dialogue-row-header">
                <div><strong>${item.speaker_name || item.speaker_id || "Narration"}</strong> · ${item.file_relative_path}:${item.line_number}</div>
                <div class="pill-list compact"><span class="pill subtle">${escapeHtml(translationBadge)}</span></div>
            </div>
            <div class="helper-text">${item.source_text}</div>
            ${translationPreview}
        `;
        dom.dialoguePreviewList.appendChild(row);
    });
}


function getFilteredCharacters() {
    const characters = state.analysis?.characters || [];
    const query = state.characterFilter.trim().toLowerCase();
    if (!query) {
        return characters;
    }

    return characters.filter((character) => {
        const inferred = state.analysis?.default_character_profiles?.[character.speaker_id] || {};
        const editable = state.characterProfiles[character.speaker_id] || {};
        const haystack = [
            character.display_name,
            character.speaker_id,
            editable.display_name,
            getCharacterTonePresetById(editable.tone_preset_id || inferred.tone_preset_id || "custom").name,
            editable.role,
            editable.tone,
            inferred.role,
            inferred.tone,
            inferred.notes,
        ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();
        return haystack.includes(query);
    });
}


function buildRosterSummary(character) {
    const inferred = state.analysis?.default_character_profiles?.[character.speaker_id] || {};
    const summaryParts = [];
    if (inferred.role) {
        summaryParts.push(inferred.role);
    }
    if (inferred.tone) {
        summaryParts.push(inferred.tone.split(",")[0].trim());
    }
    if (isSystemCharacter(character)) {
        summaryParts.push("system");
    }
    return summaryParts.filter(Boolean).slice(0, 2).join(" / ");
}


function captureCharacterGridViewState(target = null) {
    const rosterList = dom.characterGrid.querySelector(".character-roster-list");
    const filterField = dom.characterGrid.querySelector("[data-role='character-filter']");
    const activeElement = target || document.activeElement;
    const selectedButton = activeElement?.closest?.("[data-select-character]");
    const filterFocused = Boolean(filterField && activeElement === filterField);
    return {
        rosterScrollTop: rosterList?.scrollTop || 0,
        focusMode: filterFocused ? "filter" : (selectedButton?.dataset.selectCharacter ? "character" : null),
        focusSpeakerId: selectedButton?.dataset.selectCharacter || null,
        filterSelectionStart: filterFocused ? (filterField.selectionStart ?? filterField.value.length) : null,
        filterSelectionEnd: filterFocused ? (filterField.selectionEnd ?? filterField.value.length) : null,
    };
}


function restoreCharacterGridViewState(viewState) {
    if (!viewState) {
        return;
    }

    const rosterList = dom.characterGrid.querySelector(".character-roster-list");
    if (rosterList) {
        rosterList.scrollTop = viewState.rosterScrollTop || 0;
    }

    if (viewState.focusMode === "filter") {
        const filterField = dom.characterGrid.querySelector("[data-role='character-filter']");
        if (filterField) {
            filterField.focus({ preventScroll: true });
            if (
                typeof viewState.filterSelectionStart === "number"
                && typeof viewState.filterSelectionEnd === "number"
            ) {
                filterField.setSelectionRange(viewState.filterSelectionStart, viewState.filterSelectionEnd);
            }
        }
        return;
    }

    if (viewState.focusMode === "character" && viewState.focusSpeakerId) {
        const nextButton = Array.from(dom.characterGrid.querySelectorAll("[data-select-character]"))
            .find((candidate) => candidate.dataset.selectCharacter === viewState.focusSpeakerId);
        nextButton?.focus({ preventScroll: true });
    }
}


function getVisibleSelectedCharacter(visibleCharacters) {
    return visibleCharacters.find((character) => character.speaker_id === state.selectedCharacterId)
        || visibleCharacters[0]
        || null;
}


function getCharacterBySpeakerId(speakerId) {
    return (state.analysis?.characters || []).find((entry) => entry.speaker_id === speakerId) || null;
}


function getTranslationRuleValue() {
    return dom.translationRuleSelect?.value || "missing_only";
}


function getTranslationRuleLabel(rule) {
    if (rule === "retranslate_existing") {
        return "기존 번역만 재번역";
    }
    if (rule === "force_all") {
        return "범위 전체 새로 번역";
    }
    return "미번역만 번역";
}


function getTranslationStatusLabel(status, source = "") {
    const sourceDetail = getTranslationSourceDetail(source);
    if (status === "workbench_translated") {
        return sourceDetail ? `워크벤치 출력 · ${sourceDetail}` : "워크벤치 출력";
    }
    if (status === "game_translated") {
        return sourceDetail ? `게임 연결 번역 · ${sourceDetail}` : "게임 연결 번역";
    }
    return "미번역";
}


function getEditableDisplayText(item) {
    if (hasMeaningfulTranslation(item.workbench_translation_text, item.source_text)) {
        return item.workbench_translation_text;
    }
    if (hasMeaningfulTranslation(item.connected_translation_text, item.source_text)) {
        return item.connected_translation_text;
    }
    if (hasMeaningfulTranslation(item.effective_translation_text, item.source_text)) {
        return item.effective_translation_text;
    }
    if (item.translation_status !== "untranslated" && hasMeaningfulTranslation(item.current_text, item.source_text)) {
        return item.current_text;
    }
    return "";
}


function getIssueCandidates() {
    const allCandidates = state.analysis?.issue_candidates || [];
    if (!state.selectedFiles.size) {
        return allCandidates;
    }
    return allCandidates.filter((item) => state.selectedFiles.has(item.file_relative_path));
}


function getAdultQueueItems() {
    const allItems = state.analysis?.adult_queue || [];
    if (!state.selectedFiles.size) {
        return allItems;
    }
    return allItems.filter((item) => state.selectedFiles.has(item.file_relative_path));
}


function syncIssueCandidateSelection(candidates = getIssueCandidates()) {
    const availableIds = new Set((candidates || []).map((item) => item.item_id));
    state.selectedIssueCandidateIds = new Set(
        Array.from(state.selectedIssueCandidateIds).filter((itemId) => availableIds.has(itemId)),
    );
}


function syncAdultQueueSelection(items = getAdultQueueItems()) {
    const availableIds = new Set((items || []).map((item) => item.item_id));
    state.selectedAdultQueueIds = new Set(
        Array.from(state.selectedAdultQueueIds).filter((itemId) => availableIds.has(itemId)),
    );
}


function getVisibleIssueCandidates() {
    const query = (state.issueCandidateSearchQuery || "").trim().toLowerCase();
    const candidates = getIssueCandidates();
    if (!query) {
        return candidates;
    }
    return candidates.filter((item) => {
        const haystack = [
            item.speaker_name,
            item.speaker_id,
            item.file_relative_path,
            item.source_text,
            item.issue_reason,
            item.translation_status,
        ]
            .map((value) => String(value || "").toLowerCase())
            .join(" ");
        return haystack.includes(query);
    });
}


function getIssueReasonLabel(item) {
    return item?.issue_reason || "번역 누락 의심";
}


function buildManualEditPayload(edits) {
    if (!state.analysis) {
        throw new Error("먼저 게임 분석을 실행하세요.");
    }
    const gamePath = dom.gamePathInput.value.trim();
    if (!gamePath) {
        throw new Error("게임 경로 분석 모드에서만 수동 저장을 지원합니다.");
    }
    return {
        game_exe_path: gamePath,
        target_language: dom.targetLanguageInput.value.trim() || "ko",
        publish_settings: collectPublishSettings(),
        edits,
    };
}


function buildCurrentAnalysisPayload({ requireGamePath = false } = {}) {
    if (!state.analysis) {
        throw new Error("먼저 게임 분석을 실행하세요.");
    }

    const payload = {
        target_language: dom.targetLanguageInput.value.trim() || "ko",
    };
    const gamePath = dom.gamePathInput.value.trim();
    if (gamePath) {
        payload.game_exe_path = gamePath;
        return payload;
    }
    if (!requireGamePath && state.uploadedFiles.length) {
        payload.files_data = state.uploadedFiles;
        return payload;
    }
    if (requireGamePath) {
        throw new Error("이 기능은 게임 경로 분석 모드에서만 사용할 수 있습니다.");
    }
    throw new Error("분석 대상 파일을 찾지 못했습니다.");
}


function renderEditorFileOptions() {
    if (!dom.editorFileSelect) {
        return;
    }
    const files = state.analysis?.files || [];
    const currentValue = state.editorFilePath || dom.editorFileSelect.value || "";
    dom.editorFileSelect.innerHTML = '<option value="">파일 선택</option>';
    files.forEach((file) => {
        const option = document.createElement("option");
        option.value = file.file_relative_path;
        option.textContent = `${file.file_name} (${file.item_count})`;
        dom.editorFileSelect.appendChild(option);
    });
    dom.editorFileSelect.value = files.some((file) => file.file_relative_path === currentValue) ? currentValue : "";
}


function getEditorItems() {
    return state.editorDocument?.items || [];
}


function getEditorDraftValue(item) {
    if (!item) {
        return "";
    }
    return state.editorDrafts[item.item_id] ?? item.editable_text ?? getEditableDisplayText(item);
}


function isEditorItemDirty(item) {
    if (!item) {
        return false;
    }
    return getEditorDraftValue(item).trim() !== (item.editable_text || "").trim();
}


function buildEditorSummaryText(documentPayload, visibleCount) {
    const dirtyCount = (documentPayload?.items || []).filter((item) => isEditorItemDirty(item)).length;
    return `${documentPayload.file_relative_path} · 표시 ${visibleCount}/${documentPayload.item_count}줄 · 변경 ${dirtyCount}건 · 저장 시 워크벤치 출력과 publish bundle에 바로 반영됩니다.`;
}


function getVisibleEditorItems() {
    const items = getEditorItems();
    const statusFilter = state.editorStatusFilter || "all";
    const query = (state.editorSearchQuery || "").trim().toLowerCase();
    return items.filter((item) => {
        if (statusFilter === "adult" && !item.adult) {
            return false;
        }
        if (statusFilter !== "all" && statusFilter !== "adult" && item.translation_status !== statusFilter) {
            return false;
        }
        if (!query) {
            return true;
        }
        const draftValue = getEditorDraftValue(item);
        const haystack = [
            item.speaker_name,
            item.speaker_id,
            item.source_text,
            draftValue,
            item.line_number,
            item.file_relative_path,
        ]
            .map((value) => String(value || "").toLowerCase())
            .join(" ");
        return haystack.includes(query);
    });
}


function renderDocumentEditor() {
    if (!dom.documentEditor || !dom.editorSummary) {
        return;
    }
    renderEditorFileOptions();
    if (!state.analysis) {
        dom.editorSummary.textContent = "게임 분석 후 파일을 선택하면 원문/번역문 편집기를 사용할 수 있습니다.";
        dom.documentEditor.className = "document-editor empty-state";
        dom.documentEditor.textContent = "편집할 파일을 먼저 불러오세요.";
        return;
    }

    const documentPayload = state.editorDocument;
    if (!documentPayload) {
        dom.editorSummary.textContent = "파일을 선택하고 ‘파일 열기’를 누르면 원문/번역문을 함께 편집할 수 있습니다.";
        dom.documentEditor.className = "document-editor empty-state";
        dom.documentEditor.textContent = "편집할 파일을 먼저 불러오세요.";
        return;
    }

    const visibleItems = getVisibleEditorItems();
    if (!visibleItems.some((item) => item.item_id === state.editorSelectedItemId)) {
        state.editorSelectedItemId = visibleItems[0]?.item_id || documentPayload.items[0]?.item_id || null;
    }
    const selectedItem = documentPayload.items.find((item) => item.item_id === state.editorSelectedItemId) || visibleItems[0] || null;
    const dirtyCount = documentPayload.items.filter((item) => getEditorDraftValue(item).trim() !== (item.editable_text || "").trim()).length;
    dom.editorSummary.textContent = `${documentPayload.file_relative_path} · ${visibleItems.length}/${documentPayload.item_count}줄 표시 · 변경 ${dirtyCount}건 · 저장 시 워크벤치 출력과 publish bundle에 즉시 반영됩니다.`;

    dom.editorSummary.textContent = buildEditorSummaryText(documentPayload, visibleItems.length);

    const listHtml = visibleItems.length
        ? visibleItems.map((item) => {
            const draftValue = getEditorDraftValue(item);
            const isDirty = draftValue.trim() !== (item.editable_text || "").trim();
            return `
                <button
                    type="button"
                    class="editor-item${item.item_id === selectedItem?.item_id ? " is-selected" : ""}${isDirty ? " is-dirty" : ""}"
                    data-action="select-editor-item"
                    data-item-id="${escapeHtml(item.item_id)}"
                >
                    <div class="editor-item-title">
                        <strong>${escapeHtml(item.speaker_name || item.speaker_id || item.kind || "Narration")}</strong>
                        <span class="pill subtle">${escapeHtml(getTranslationStatusLabel(item.translation_status, item.translation_source))}</span>
                    </div>
                    <div class="helper-text">${escapeHtml(item.file_relative_path)}:${escapeHtml(item.line_number)}</div>
                    <div class="editor-item-snippet">${escapeHtml(item.source_preview || item.source_text)}</div>
                </button>
            `;
        }).join("")
        : '<div class="empty-state">현재 필터에서 표시할 줄이 없습니다.</div>';

    const selectedDraft = selectedItem ? getEditorDraftValue(selectedItem) : "";
    const detailHtml = selectedItem ? `
        <div class="editor-detail-grid">
            <div>
                <p class="section-kicker">Selected Line</p>
                <h3>${escapeHtml(selectedItem.speaker_name || selectedItem.speaker_id || selectedItem.kind || "Narration")}</h3>
                <div class="helper-text">${escapeHtml(selectedItem.file_relative_path)}:${escapeHtml(selectedItem.line_number)} · ${escapeHtml(getTranslationStatusLabel(selectedItem.translation_status, selectedItem.translation_source))}</div>
            </div>
            <div class="editor-source-box">
                <strong>원문</strong>
                <p>${escapeHtml(selectedItem.source_text)}</p>
            </div>
            <div class="translation-preview-stack">
                ${buildTranslationPreviewLines(selectedItem)}
            </div>
            <label class="field">
                <span>편집 번역문</span>
                <textarea data-role="editor-text" data-item-id="${escapeHtml(selectedItem.item_id)}" rows="7" placeholder="직접 번역문을 입력하면 저장 시 바로 게임 출력에 반영됩니다.">${escapeHtml(selectedDraft)}</textarea>
            </label>
            <div class="editor-context-grid">
                <div class="editor-source-box">
                    <strong>이전 문맥</strong>
                    <p>${escapeHtml((selectedItem.context_before || []).join("\n") || "없음")}</p>
                </div>
                <div class="editor-source-box">
                    <strong>다음 문맥</strong>
                    <p>${escapeHtml((selectedItem.context_after || []).join("\n") || "없음")}</p>
                </div>
            </div>
            <div class="editor-detail-actions">
                <button type="button" class="secondary-button" data-action="save-editor-item" data-item-id="${escapeHtml(selectedItem.item_id)}">현재 줄 저장</button>
            </div>
        </div>
    ` : '<div class="empty-state">편집할 줄을 왼쪽 목록에서 선택하세요.</div>';

    dom.documentEditor.className = "document-editor";
    dom.documentEditor.innerHTML = `
        <div class="document-editor-shell">
            <aside class="editor-list-pane">
                <div class="inline-header">
                    <h3>줄 목록</h3>
                    <span class="helper-text">${visibleItems.length}줄</span>
                </div>
                <div class="editor-list">${listHtml}</div>
            </aside>
            <section class="editor-detail">
                ${detailHtml}
            </section>
        </div>
    `;
}


async function loadEditableDocument(
    filePath = dom.editorFileSelect?.value || "",
    {
        silent = false,
        selectedItemId = state.editorSelectedItemId,
    } = {},
) {
    if (!filePath) {
        if (!silent) {
            addLog("편집할 파일을 먼저 선택하세요.", "warning");
        }
        return null;
    }

    dom.loadEditorButton.disabled = true;
    if (dom.editorFileSelect) {
        dom.editorFileSelect.disabled = true;
    }
    try {
        const payload = {
            ...buildCurrentAnalysisPayload(),
            publish_settings: collectPublishSettings(),
            file_relative_path: filePath,
        };
        const response = await apiPost("/load_editable_document", payload);
        state.editorDocument = response.document || null;
        state.editorFilePath = response.document?.file_relative_path || filePath;
        const availableIds = new Set((state.editorDocument?.items || []).map((item) => item.item_id));
        state.editorSelectedItemId = availableIds.has(selectedItemId)
            ? selectedItemId
            : (state.editorDocument?.items?.[0]?.item_id || null);
        renderDocumentEditor();
        if (!silent) {
            addLog(`편집 파일 불러오기 완료: ${state.editorFilePath}`, "success");
        }
        return response;
    } catch (error) {
        state.editorDocument = null;
        state.editorSelectedItemId = null;
        renderDocumentEditor();
        if (!silent) {
            addLog(`편집 파일 불러오기 실패: ${error.message}`, "error");
        }
        throw error;
    } finally {
        dom.loadEditorButton.disabled = false;
        if (dom.editorFileSelect) {
            dom.editorFileSelect.disabled = false;
        }
    }
}


async function refreshAnalysisAfterManualSave({
    reloadEditor = false,
    preferredFilePath = state.editorFilePath,
    selectedItemId = state.editorSelectedItemId,
    activateTabName = state.activeTab,
} = {}) {
    const analysis = await apiPost("/analyze_sources", buildCurrentAnalysisPayload());
            populateFromAnalysis(analysis, "수동 편집 반영", { selectionMode: "preserve" });
    if (reloadEditor && preferredFilePath) {
        try {
            await loadEditableDocument(preferredFilePath, {
                silent: true,
                selectedItemId,
            });
        } catch {
            // The editor falls back to its empty state if the file is unavailable.
        }
    }
    if (activateTabName) {
        activateTab(activateTabName);
    }
    return analysis;
}


async function saveManualEdits(
    edits,
    {
        successMessage = "수동 수정이 저장되었습니다.",
        reloadEditor = false,
        preferredFilePath = state.editorFilePath,
        selectedItemId = state.editorSelectedItemId,
        activateTabName = state.activeTab,
    } = {},
) {
    if (!Array.isArray(edits) || !edits.length) {
        addLog("저장할 변경이 없습니다.", "warning");
        return null;
    }

    const normalizedEdits = edits
        .map((entry) => ({
            file_relative_path: String(entry.file_relative_path || "").trim(),
            item_id: String(entry.item_id || "").trim(),
            text: String(entry.text ?? "").trim(),
        }))
        .filter((entry) => entry.file_relative_path && entry.item_id && entry.text);
    if (!normalizedEdits.length) {
        addLog("비어 있지 않은 번역문만 저장할 수 있습니다.", "warning");
        return null;
    }

    dom.saveEditorButton.disabled = true;
    try {
        const response = await apiPost("/apply_manual_edits", buildManualEditPayload(normalizedEdits));
        normalizedEdits.forEach((entry) => {
            delete state.editorDrafts[entry.item_id];
        });
        renderResults(response);
        addLog(`${successMessage} ${response.applied_item_count || normalizedEdits.length}건`, "success");
        if (response.publish_bundle?.publish_root) {
            addLog(`Ren'Py publish bundle 반영: ${response.publish_bundle.publish_root}`, "success");
        }
        await refreshAnalysisAfterManualSave({
            reloadEditor,
            preferredFilePath,
            selectedItemId,
            activateTabName,
        });
        return response;
    } catch (error) {
        addLog(`수동 수정 저장 실패: ${error.message}`, "error");
        throw error;
    } finally {
        dom.saveEditorButton.disabled = false;
    }
}


function buildTranslationScopeLabel(payload) {
    const scope = payload.translation_scope || {};
    const ruleLabel = getTranslationRuleLabel(scope.translation_rule || payload.translation_rule || getTranslationRuleValue());
    if (scope.mode === "selected_items") {
        return `${ruleLabel} · items=${scope.selected_item_count || scope.selected_item_ids?.length || 0}`;
    }
    if (scope.mode === "selected_speakers") {
        return `${ruleLabel} · speaker=${scope.selected_speaker_names?.join(", ") || scope.selected_speaker_ids?.join(", ") || "-"}`;
    }
    return `${ruleLabel} · all-items`;
}


function buildCharacterDetailPanelHtml(selectedCharacter) {
    const profile = state.characterProfiles[selectedCharacter.speaker_id] || {};
    const inferred = state.analysis.default_character_profiles?.[selectedCharacter.speaker_id] || {};
    const sampleHtml = (selectedCharacter.sample_lines || []).length
        ? selectedCharacter.sample_lines.map((line, index) => `
            <article class="character-sample-card">
                <span class="sample-index">Sample ${index + 1}</span>
                <p>${escapeHtml(line)}</p>
            </article>
        `).join("")
        : '<div class="empty-state">표시할 샘플 대사가 없습니다.</div>';

    return `
        <section class="character-detail-panel" data-role="character-detail">
            <div class="character-detail-hero">
                ${buildCharacterAvatarMarkup(selectedCharacter, "large")}
                <div class="character-detail-heading">
                    <p class="section-kicker">Selected Character</p>
                    <h3>${escapeHtml(selectedCharacter.display_name || selectedCharacter.speaker_id)}</h3>
                    <div class="helper-text">${escapeHtml(selectedCharacter.speaker_id)} · ${escapeHtml(selectedCharacter.defined_in || "generated")}</div>
                    <div class="pill-list">
                        <span class="pill">${selectedCharacter.line_count} lines</span>
                        <span class="pill">${selectedCharacter.adult_line_count} adult</span>
                        <span class="pill subtle">미번역 ${selectedCharacter.untranslated_line_count || 0}</span>
                        <span class="pill subtle">연결 ${selectedCharacter.game_translated_line_count || 0}</span>
                        <span class="pill subtle">워크벤치 ${selectedCharacter.workbench_translated_line_count || 0}</span>
                        ${isSystemCharacter(selectedCharacter) ? '<span class="pill subtle">System speaker</span>' : ""}
                        ${selectedCharacter.portrait?.source_type ? `<span class="pill subtle">${escapeHtml(selectedCharacter.portrait.source_type)}</span>` : ""}
                    </div>
                </div>
            </div>

            <div class="character-inference-grid">
                <article class="character-inference-card">
                    <span class="stat-label">AI 역할 추정</span>
                    <strong>${escapeHtml(inferred.role || "미분류")}</strong>
                </article>
                <article class="character-inference-card">
                    <span class="stat-label">AI 말투 추정</span>
                    <strong>${escapeHtml(inferred.tone || "상황 기반 기본 톤")}</strong>
                </article>
                <article class="character-inference-card wide">
                    <span class="stat-label">번역 메모</span>
                    <p>${escapeHtml(inferred.notes || "샘플 대사 기준으로 추가 보정하세요.")}</p>
                </article>
            </div>

            <div class="character-edit-grid">
                <label class="field">
                    <span>표시명</span>
                    <input type="text" data-field="display_name" value="${escapeHtml(profile.display_name || "")}">
                </label>
                <label class="field">
                    <span>역할</span>
                    <input type="text" data-field="role" value="${escapeHtml(profile.role || "")}" placeholder="예: 주요 등장인물, 조력자, 시스템 메시지">
                </label>
                <label class="field">
                    <span>말투 / 성격</span>
                    <textarea rows="3" data-field="tone" placeholder="예: 다정하지만 경계심이 있고, 상황에 따라 직설적으로 변함">${escapeHtml(profile.tone || "")}</textarea>
                </label>
                <label class="field">
                    <span>번역 메모</span>
                    <textarea rows="5" data-field="notes" placeholder="호칭 규칙, 금지 표현, 관계성 메모">${escapeHtml(profile.notes || "")}</textarea>
                </label>
            </div>

            <div class="character-sample-section">
                <div class="inline-header">
                    <h3>샘플 대사</h3>
                    <span class="helper-text">자동 추정의 근거로 쓰인 대표 문장</span>
                </div>
                <div class="character-sample-list">${sampleHtml}</div>
            </div>
        </section>
    `;
}


function buildCharacterPreviewHtml(selectedCharacter) {
    const previewState = state.tonePreviewByCharacter[selectedCharacter.speaker_id];
    const isLoading = state.tonePreviewLoadingSpeakerId === selectedCharacter.speaker_id;
    if (isLoading) {
        return '<div class="character-preview-empty">샘플 대사를 현재 설정으로 미리 번역하는 중입니다...</div>';
    }
    if (!previewState?.translations?.length) {
        return '<div class="character-preview-empty">프리셋이나 tone/notes를 조정한 뒤 `샘플 미리 번역`을 눌러 실제 번역 어투를 먼저 확인하세요.</div>';
    }

    const metaParts = [
        previewState.tone_preset_name || "직접 입력",
        previewState.provider === "gemini" ? "Gemini" : "OpenAI",
        previewState.model_name || "",
    ].filter(Boolean);
    const cards = previewState.translations.map((entry, index) => `
        <article class="character-preview-card">
            <span class="sample-index">Preview ${index + 1}</span>
            <div class="character-preview-columns">
                <div class="preview-block">
                    <span class="preview-label">원문</span>
                    <p>${escapeHtml(entry.source_text || "")}</p>
                </div>
                <div class="preview-block">
                    <span class="preview-label">미리 번역</span>
                    <p>${escapeHtml(entry.translated_text || "(응답 없음)")}</p>
                </div>
            </div>
        </article>
    `).join("");

    return `
        <div class="helper-text">${escapeHtml(metaParts.join(" · "))}</div>
        <div class="character-preview-list">${cards}</div>
    `;
}


function buildCharacterPreviewComparisonHtml(selectedCharacter) {
    const previewState = state.tonePreviewByCharacter[selectedCharacter.speaker_id];
    const isLoading = state.tonePreviewLoadingSpeakerId === selectedCharacter.speaker_id;
    if (isLoading) {
        return '<div class="character-preview-empty">샘플 대사를 현재 설정과 대안 프리셋으로 미리 번역하는 중입니다...</div>';
    }
    if (!previewState?.variants?.length) {
        return '<div class="character-preview-empty">현재 설정, 대안 프리셋 2개를 같은 문장으로 비교합니다. 샘플 미리 번역을 눌러 3안을 먼저 확인하세요.</div>';
    }

    const metaParts = [
        previewState.provider === "gemini" ? "Gemini" : "OpenAI",
        previewState.model_name || "",
        previewState.cacheHit ? "cache hit" : "fresh preview",
    ].filter(Boolean);
    const legendHtml = previewState.variants.map((variant) => `
        <article class="preview-legend-card ${variant.error ? "is-error" : ""}">
            <span class="sample-index">${escapeHtml(variant.label)}</span>
            <strong>${escapeHtml(variant.description || variant.presetName || variant.label)}</strong>
            <p class="helper-text">${escapeHtml(variant.error ? `실패: ${variant.error}` : (variant.presetName || ""))}</p>
        </article>
    `).join("");
    const sampleRows = (previewState.sample_lines || []).map((sourceText, index) => {
        const variantColumns = previewState.variants.map((variant) => {
            const translationEntry = (variant.translations || [])[index] || {};
            return `
                <div class="preview-variant-card ${variant.error ? "is-error" : ""}">
                    <span class="preview-label">${escapeHtml(variant.label)}</span>
                    <strong>${escapeHtml(variant.description || variant.presetName || variant.label)}</strong>
                    <p>${escapeHtml(variant.error ? variant.error : (translationEntry.translated_text || "(응답 없음)"))}</p>
                </div>
            `;
        }).join("");

        return `
            <article class="character-preview-card">
                <span class="sample-index">Sample ${index + 1}</span>
                <div class="character-preview-row-grid">
                    <div class="preview-source-card">
                        <span class="preview-label">원문</span>
                        <p>${escapeHtml(sourceText || "")}</p>
                    </div>
                    <div class="character-preview-columns">
                        ${variantColumns}
                    </div>
                </div>
            </article>
        `;
    }).join("");

    return `
        <div class="helper-text">${escapeHtml(metaParts.join(" · "))}</div>
        <div class="preview-legend-grid">${legendHtml}</div>
        <div class="character-preview-list">${sampleRows}</div>
    `;
}


function buildCharacterDetailPanelHtmlEnhanced(selectedCharacter) {
    const profile = state.characterProfiles[selectedCharacter.speaker_id] || {};
    const inferred = state.analysis.default_character_profiles?.[selectedCharacter.speaker_id] || {};
    const displayName = profile.display_name || selectedCharacter.display_name || selectedCharacter.speaker_id;
    const tonePresetId = profile.tone_preset_id || inferred.tone_preset_id || "custom";
    const tonePreset = getCharacterTonePresetById(tonePresetId);
    const inferredPreset = getCharacterTonePresetById(inferred.tone_preset_id || "custom");
    const sampleHtml = (selectedCharacter.sample_lines || []).length
        ? selectedCharacter.sample_lines.map((line, index) => `
            <article class="character-sample-card">
                <span class="sample-index">Sample ${index + 1}</span>
                <p>${escapeHtml(line)}</p>
            </article>
        `).join("")
        : '<div class="empty-state">표시할 샘플 대사가 없습니다.</div>';
    const previewButtonLabel = state.tonePreviewLoadingSpeakerId === selectedCharacter.speaker_id
        ? "미리 번역 중..."
        : "샘플 3안 미리 번역";

    return `
        <section class="character-detail-panel" data-role="character-detail">
            <div class="character-detail-hero">
                ${buildCharacterAvatarMarkup(selectedCharacter, "large")}
                <div class="character-detail-heading">
                    <p class="section-kicker">Selected Character</p>
                    <h3>${escapeHtml(displayName)}</h3>
                    <div class="helper-text">${escapeHtml(selectedCharacter.speaker_id)} · ${escapeHtml(selectedCharacter.defined_in || "generated")}</div>
                    <div class="pill-list">
                        <span class="pill">${selectedCharacter.line_count} lines</span>
                        <span class="pill">${selectedCharacter.adult_line_count} adult</span>
                        <span class="pill subtle">미번역 ${selectedCharacter.untranslated_line_count || 0}</span>
                        <span class="pill subtle">연결 ${selectedCharacter.game_translated_line_count || 0}</span>
                        <span class="pill subtle">워크벤치 ${selectedCharacter.workbench_translated_line_count || 0}</span>
                        ${isSystemCharacter(selectedCharacter) ? '<span class="pill subtle">System speaker</span>' : ""}
                        ${selectedCharacter.portrait?.source_type ? `<span class="pill subtle">${escapeHtml(selectedCharacter.portrait.source_type)}</span>` : ""}
                    </div>
                </div>
            </div>

            <div class="character-inference-grid">
                <article class="character-inference-card">
                    <span class="stat-label">AI 역할 추정</span>
                    <strong>${escapeHtml(inferred.role || "미분류")}</strong>
                </article>
                <article class="character-inference-card">
                    <span class="stat-label">AI 말투 추정</span>
                    <strong>${escapeHtml(inferred.tone || "상황 기반 기본 톤")}</strong>
                </article>
                <article class="character-inference-card">
                    <span class="stat-label">AI 추천 프리셋</span>
                    <strong>${escapeHtml(inferredPreset.name)}</strong>
                </article>
                <article class="character-inference-card wide">
                    <span class="stat-label">번역 메모</span>
                    <p>${escapeHtml(inferred.notes || "샘플 대사를 보고 추가 보정 권장")}</p>
                </article>
            </div>

            <div class="character-edit-grid">
                <label class="field">
                    <span>표시명</span>
                    <input type="text" data-field="display_name" value="${escapeHtml(profile.display_name || "")}">
                </label>
                <label class="field">
                    <span>역할</span>
                    <input type="text" data-field="role" value="${escapeHtml(profile.role || "")}" placeholder="예: 주요 등장인물, 조력자, 시스템 메시지">
                </label>
                <label class="field">
                    <span>어투 프리셋</span>
                    <select data-field="tone_preset_id">
                        ${buildCharacterTonePresetOptions(tonePresetId)}
                    </select>
                </label>
                <div class="field tone-preset-helper">
                    <span>프리셋 안내</span>
                    <p class="helper-text">
                        현재 선택: <strong>${escapeHtml(tonePreset.name)}</strong>
                        · ${escapeHtml(tonePreset.description)}
                        ${inferredPreset.id !== tonePreset.id ? ` · AI 추천은 ${escapeHtml(inferredPreset.name)}` : ""}
                    </p>
                </div>
                <label class="field full-span">
                    <span>말투 / 성격</span>
                    <textarea rows="3" data-field="tone" placeholder="예: 다정하지만 경계심이 있고, 상황에 따라 직설적으로 변함">${escapeHtml(profile.tone || "")}</textarea>
                </label>
                <label class="field full-span">
                    <span>번역 메모</span>
                    <textarea rows="5" data-field="notes" placeholder="호칭 규칙, 금지 표현, 관계성 메모">${escapeHtml(profile.notes || "")}</textarea>
                </label>
            </div>

            <div class="character-sample-section">
                <div class="inline-header">
                    <div>
                        <h3>샘플 대사</h3>
                        <span class="helper-text">자동 추정의 근거로 쓰인 대표 문장</span>
                    </div>
                    <div class="character-action-row">
                        <button
                            type="button"
                            class="ghost-button mini-button"
                            data-action="retranslate-character"
                            data-speaker-id="${escapeHtml(selectedCharacter.speaker_id)}"
                        >이 캐릭터만 재번역</button>
                        <button
                            type="button"
                            class="secondary-button mini-button"
                            data-action="preview-character-tone"
                            data-speaker-id="${escapeHtml(selectedCharacter.speaker_id)}"
                            ${selectedCharacter.sample_lines?.length ? "" : "disabled"}
                        >${previewButtonLabel}</button>
                    </div>
                </div>
                <p class="helper-text">현재 체크된 파일 범위에서 이 캐릭터 대사만 다시 번역하고, 기존 결과 파일은 유지한 채 해당 줄만 덮어씁니다.</p>
                <div class="character-sample-list">${sampleHtml}</div>
            </div>

            <div class="character-preview-section">
                <div class="inline-header">
                    <div>
                        <h3>프롬프트 미리 번역</h3>
                        <span class="helper-text">현재 설정, 대안 프리셋 2개를 같은 문장으로 먼저 번역해 어투를 비교합니다.</span>
                    </div>
                </div>
                ${buildCharacterPreviewComparisonHtml(selectedCharacter)}
            </div>
        </section>
    `;
}


function syncCharacterRosterSelection() {
    dom.characterGrid.querySelectorAll("[data-select-character]").forEach((button) => {
        button.classList.toggle("selected", button.dataset.selectCharacter === state.selectedCharacterId);
    });
}


function renderSelectedCharacterDetail() {
    if (!state.analysis || !state.analysis.characters?.length) {
        return;
    }

    const visibleCharacters = getFilteredCharacters();
    const selectedCharacter = getVisibleSelectedCharacter(visibleCharacters);
    if (!selectedCharacter) {
        renderCharacterGrid();
        return;
    }

    state.selectedCharacterId = selectedCharacter.speaker_id;
    syncCharacterRosterSelection();

    const detailPanel = dom.characterGrid.querySelector("[data-role='character-detail']");
    if (!detailPanel) {
        renderCharacterGrid();
        return;
    }

    detailPanel.outerHTML = buildCharacterDetailPanelHtmlEnhanced(selectedCharacter);
}


function renderCharacterGrid(viewState = null) {
    if (!state.analysis || !state.analysis.characters?.length) {
        dom.characterGrid.className = "character-grid empty-state";
        dom.characterGrid.textContent = "분석 후 캐릭터 작업 영역이 여기에 생성됩니다.";
        return;
    }

    ensureCharacterProfiles();
    dom.characterGrid.className = "character-grid";
    const visibleCharacters = getFilteredCharacters();
    const selectedCharacter = getVisibleSelectedCharacter(visibleCharacters);

    if (!selectedCharacter) {
        dom.characterGrid.innerHTML = `
            <div class="character-workbench">
                <aside class="character-roster">
                    <div class="character-roster-header">
                        <div>
                            <p class="section-kicker">Roster</p>
                            <h3>캐릭터 목록</h3>
                        </div>
                        <input type="search" value="${escapeHtml(state.characterFilter)}" data-role="character-filter" placeholder="이름, ID, 역할 검색">
                    </div>
                    <div class="character-roster-list empty-state">검색 조건에 맞는 캐릭터가 없습니다.</div>
                </aside>
                <section class="character-detail-panel empty-state">좌측 목록에서 캐릭터를 선택하세요.</section>
            </div>
        `;
        restoreCharacterGridViewState(viewState);
        return;
    }

    state.selectedCharacterId = selectedCharacter.speaker_id;
    const rosterHtml = visibleCharacters.map((character) => {
        const editableProfile = state.characterProfiles[character.speaker_id] || {};
        const selectedClass = character.speaker_id === state.selectedCharacterId ? " selected" : "";
        const summary = buildRosterSummary(character);
        return `
            <button type="button" class="character-list-item${selectedClass}" data-select-character="${escapeHtml(character.speaker_id)}">
                ${buildCharacterAvatarMarkup(character)}
                <div class="character-list-copy">
                    <div class="character-list-title-row">
                        <strong>${escapeHtml(editableProfile.display_name || character.display_name || character.speaker_id)}</strong>
                        ${isSystemCharacter(character) ? '<span class="pill subtle">System</span>' : ""}
                    </div>
                    <div class="helper-text">${escapeHtml(character.speaker_id)}</div>
                    <div class="character-list-summary">${escapeHtml(summary || "샘플 대사 기반 추정 준비됨")}</div>
                    <div class="pill-list compact">
                        <span class="pill">${character.line_count} lines</span>
                        <span class="pill">${character.adult_line_count} adult</span>
                    </div>
                </div>
            </button>
        `;
    }).join("");

    dom.characterGrid.innerHTML = `
        <div class="character-workbench">
            <aside class="character-roster">
                <div class="character-roster-header">
                    <div>
                        <p class="section-kicker">Roster</p>
                        <h3>캐릭터 목록</h3>
                        <div class="helper-text">${visibleCharacters.length} / ${(state.analysis.characters || []).length} 표시 중</div>
                    </div>
                    <input type="search" value="${escapeHtml(state.characterFilter)}" data-role="character-filter" placeholder="이름, ID, 역할 검색">
                </div>
                <div class="character-roster-list">${rosterHtml}</div>
            </aside>
            ${buildCharacterDetailPanelHtmlEnhanced(selectedCharacter)}
        </div>
    `;
    restoreCharacterGridViewState(viewState);
}


function renderIssueCandidates() {
    if (!dom.issueCandidateQueue || !dom.issueCandidateSummary) {
        return;
    }
    if (!state.analysis) {
        dom.issueCandidateSummary.textContent = "게임 분석 후 문제 후보를 여기서 검토할 수 있습니다.";
        dom.issueCandidateQueue.className = "adult-queue empty-state";
        dom.issueCandidateQueue.textContent = "분석 후 문제 후보가 여기에 표시됩니다.";
        dom.selectVisibleIssueCandidatesButton.disabled = true;
        dom.clearIssueCandidateSelectionButton.disabled = true;
        dom.retranslateIssueCandidatesButton.disabled = true;
        return;
    }

    const allCandidates = getIssueCandidates();
    syncIssueCandidateSelection(allCandidates);
    const visibleCandidates = getVisibleIssueCandidates();
    const selectedVisibleCount = visibleCandidates.filter((item) => state.selectedIssueCandidateIds.has(item.item_id)).length;

    dom.issueCandidateSummary.textContent = allCandidates.length
        ? `현재 선택 파일 기준 후보 ${visibleCandidates.length}/${allCandidates.length}줄 · 선택 ${state.selectedIssueCandidateIds.size}줄 · 체크한 줄만 다시 번역할 수 있습니다.`
        : "현재 선택된 파일 범위에서는 미번역 / 원문 유지 의심 후보가 없습니다.";
    dom.selectVisibleIssueCandidatesButton.disabled = !visibleCandidates.length;
    dom.clearIssueCandidateSelectionButton.disabled = !state.selectedIssueCandidateIds.size;
    dom.retranslateIssueCandidatesButton.disabled = !state.selectedIssueCandidateIds.size;

    if (!allCandidates.length) {
        dom.issueCandidateQueue.className = "adult-queue empty-state";
        dom.issueCandidateQueue.textContent = "현재 선택된 파일 범위에서는 문제 후보가 없습니다.";
        return;
    }
    if (!visibleCandidates.length) {
        dom.issueCandidateQueue.className = "adult-queue empty-state";
        dom.issueCandidateQueue.textContent = "검색 조건에 맞는 문제 후보가 없습니다.";
        return;
    }

    dom.issueCandidateQueue.className = "adult-queue";
    dom.issueCandidateQueue.innerHTML = visibleCandidates.map((item) => {
        const checked = state.selectedIssueCandidateIds.has(item.item_id) ? "checked" : "";
        const selectedClass = checked ? " is-selected" : "";
        return `
            <article class="manual-edit-card issue-candidate-card${selectedClass}">
                <div class="dialogue-row-header">
                    <label class="issue-candidate-toggle">
                        <input type="checkbox" data-role="issue-select" data-item-id="${escapeHtml(item.item_id)}" ${checked}>
                        <span>
                            <strong>${escapeHtml(item.speaker_name || item.speaker_id || "Narration")}</strong>
                            <span class="helper-text">${escapeHtml(item.file_relative_path)}:${escapeHtml(item.line_number)}</span>
                        </span>
                    </label>
                    <div class="pill-list compact">
                        <span class="pill subtle">${escapeHtml(getIssueReasonLabel(item))}</span>
                        <span class="pill subtle">score ${escapeHtml(item.issue_score || 0)}</span>
                        <span class="pill subtle">${escapeHtml(getTranslationStatusLabel(item.translation_status, item.translation_source))}</span>
                    </div>
                </div>
                <div class="editor-source-box">
                    <strong>원문</strong>
                    <p>${escapeHtml(item.source_text)}</p>
                </div>
                ${buildTranslationPreviewLines(item)}
                <div class="editor-context-grid">
                    <div class="editor-source-box">
                        <strong>이전 문맥</strong>
                        <p>${escapeHtml((item.context_before || []).join("\n") || "없음")}</p>
                    </div>
                    <div class="editor-source-box">
                        <strong>다음 문맥</strong>
                        <p>${escapeHtml((item.context_after || []).join("\n") || "없음")}</p>
                    </div>
                </div>
                <div class="manual-edit-actions">
                    <button type="button" class="ghost-button mini-button" data-action="open-issue-in-editor" data-file-path="${escapeHtml(item.file_relative_path)}" data-item-id="${escapeHtml(item.item_id)}">편집 탭에서 열기</button>
                    <button type="button" class="secondary-button mini-button" data-action="retranslate-issue-item" data-item-id="${escapeHtml(item.item_id)}">이 줄만 재번역</button>
                </div>
            </article>
        `;
    }).join("");

    if (selectedVisibleCount && !state.selectedIssueCandidateIds.size) {
        dom.retranslateIssueCandidatesButton.disabled = true;
    }
}


function renderAdultQueue() {
    if (!dom.adultQueue || !dom.adultQueueSummary) {
        return;
    }
    if (!state.analysis) {
        dom.adultQueueSummary.textContent = "현재 선택 파일 범위에서 성인 대사를 확인할 수 있습니다.";
        dom.adultQueue.className = "adult-queue empty-state";
        dom.adultQueue.textContent = "성인 큐가 아직 없습니다.";
        dom.selectVisibleAdultQueueButton.disabled = true;
        dom.clearAdultQueueSelectionButton.disabled = true;
        dom.translateAdultQueueButton.disabled = true;
        return;
    }

    const filteredQueue = getAdultQueueItems();
    syncAdultQueueSelection(filteredQueue);
    dom.adultQueueSummary.textContent = filteredQueue.length
        ? `현재 선택 파일 기준 성인 대사 ${filteredQueue.length}개 중 ${state.selectedAdultQueueIds.size}개 선택됨. 선택 항목만 자동번역할 수 있습니다.`
        : "현재 선택 파일 범위에서 성인 큐 항목이 없습니다.";
    dom.selectVisibleAdultQueueButton.disabled = !filteredQueue.length;
    dom.clearAdultQueueSelectionButton.disabled = !state.selectedAdultQueueIds.size;
    dom.translateAdultQueueButton.disabled = !state.selectedAdultQueueIds.size;

    if (!filteredQueue.length) {
        dom.adultQueue.className = "adult-queue empty-state";
        dom.adultQueue.textContent = "현재 선택 파일 범위에서 성인 큐 항목이 없습니다.";
        return;
    }

    dom.adultQueue.className = "adult-queue";
    dom.adultQueue.innerHTML = filteredQueue.map((item) => {
        const draftValue = getEditorDraftValue(item);
        const isDirty = draftValue.trim() !== getEditableDisplayText(item).trim();
        const checked = state.selectedAdultQueueIds.has(item.item_id) ? "checked" : "";
        const selectedClass = checked ? " is-selected" : "";
        return `
            <article class="manual-edit-card issue-candidate-card${selectedClass}${isDirty ? " is-dirty" : ""}">
                <div class="dialogue-row-header">
                    <label class="issue-candidate-toggle">
                        <input type="checkbox" data-role="adult-select" data-item-id="${escapeHtml(item.item_id)}" ${checked}>
                        <span>
                            <strong>${escapeHtml(item.speaker_name || item.speaker_id || "Narration")}</strong>
                            <span class="helper-text">${escapeHtml(item.file_relative_path)}:${escapeHtml(item.line_number)} · ${escapeHtml(getTranslationStatusLabel(item.translation_status, item.translation_source))}</span>
                        </span>
                    </label>
                    <div class="pill-list compact">
                        <span class="pill subtle">${escapeHtml((item.adult_keywords || []).join(", ") || "adult queue")}</span>
                    </div>
                </div>
                <div class="editor-source-box">
                    <strong>원문</strong>
                    <p>${escapeHtml(item.source_text)}</p>
                </div>
                ${buildTranslationPreviewLines(item)}
                <label class="field">
                    <span>직접 번역</span>
                    <textarea data-role="adult-text" data-item-id="${escapeHtml(item.item_id)}" rows="6" placeholder="이 줄을 직접 번역하면 바로 게임 출력에 반영됩니다.">${escapeHtml(draftValue)}</textarea>
                </label>
                <div class="editor-context-grid">
                    <div class="editor-source-box">
                        <strong>이전 문맥</strong>
                        <p>${escapeHtml((item.context_before || []).join("\n") || "없음")}</p>
                    </div>
                    <div class="editor-source-box">
                        <strong>다음 문맥</strong>
                        <p>${escapeHtml((item.context_after || []).join("\n") || "없음")}</p>
                    </div>
                </div>
                <div class="manual-edit-actions">
                    <button type="button" class="ghost-button mini-button" data-action="open-adult-in-editor" data-file-path="${escapeHtml(item.file_relative_path)}" data-item-id="${escapeHtml(item.item_id)}">편집 탭에서 열기</button>
                    <button type="button" class="secondary-button mini-button" data-action="save-adult-item" data-file-path="${escapeHtml(item.file_relative_path)}" data-item-id="${escapeHtml(item.item_id)}">이 줄 저장</button>
                </div>
            </article>
        `;
    }).join("");
    return;

    const queue = state.analysis?.adult_queue || [];
    if (!queue.length) {
        dom.adultQueue.className = "adult-queue empty-state";
        dom.adultQueue.textContent = "성인 큐가 아직 없습니다.";
        return;
    }
    dom.adultQueue.className = "adult-queue";
    dom.adultQueue.innerHTML = "";
    queue.forEach((item) => {
        const row = document.createElement("div");
        row.className = "adult-row";
        row.innerHTML = `
            <div><strong>${item.speaker_name || item.speaker_id || "Narration"}</strong> · ${item.file_relative_path}:${item.line_number}</div>
            <div class="helper-text">${item.source_text}</div>
            <div class="helper-text">keywords: ${(item.adult_keywords || []).join(", ") || "-"}</div>
        `;
        dom.adultQueue.appendChild(row);
    });
}


function renderResults(payload = { results: [] }) {
    const results = payload.results || [];
    if (!results.length) {
        dom.resultsPanel.className = "results-panel empty-state";
        dom.resultsPanel.textContent = "번역 결과가 아직 없습니다.";
        return;
    }
    dom.resultsPanel.className = "results-panel";
    dom.resultsPanel.innerHTML = "";

    const activePreset = getTranslationPresetById(state.selectedTranslationPresetId);
    if (activePreset) {
        const info = document.createElement("div");
        info.className = "result-row";
        info.innerHTML = `
            <div><strong>번역 모드</strong></div>
            <div class="helper-text">${escapeHtml(activePreset.name)} · ${escapeHtml(activePreset.modelName)} · batch ${escapeHtml(formatNumericSetting(activePreset.batchSize))}${activePreset.provider === "gemini" ? ` · delay ${escapeHtml(formatNumericSetting(activePreset.apiDelay))}초` : ""}</div>
        `;
        dom.resultsPanel.appendChild(info);
    }

    if (payload.provider || payload.model_name) {
        const info = document.createElement("div");
        info.className = "result-row";
        const runtimeLabel = payload.provider === "openai" && payload.openai_auth_mode === "oauth_cli"
            ? "OpenAI OAuth / Codex CLI"
            : `${payload.provider || "provider"} / API`;
        info.innerHTML = `
            <div><strong>실행 방식</strong></div>
            <div class="helper-text">${runtimeLabel} · model=${payload.model_name || "-"}</div>
        `;
        dom.resultsPanel.appendChild(info);
    }

    if (payload.translation_scope) {
        const scope = payload.translation_scope;
        const info = document.createElement("div");
        info.className = "result-row";
        const scopeLabel = scope.mode === "selected_items"
            ? "선택 문제 후보 범위"
            : (scope.mode === "selected_speakers" ? "선택 캐릭터 범위" : "전체 항목 범위");
        const scopeDetail = scope.mode === "selected_items"
            ? `${scope.selected_item_count || scope.selected_item_ids?.length || 0}개 항목`
            : ((scope.selected_speaker_names || scope.selected_speaker_ids || []).join(", ") || "전체 화자");
        info.innerHTML = `
            <div><strong>번역 범위</strong></div>
            <div class="helper-text">${escapeHtml(scopeLabel)} · ${escapeHtml(getTranslationRuleLabel(scope.translation_rule || "missing_only"))}</div>
            <div class="helper-text">${escapeHtml(scopeDetail)}</div>
        `;
        dom.resultsPanel.appendChild(info);
    }

    if (payload.optimization) {
        const optimization = payload.optimization;
        const info = document.createElement("div");
        info.className = "result-row";
        info.innerHTML = `
            <div><strong>자동 최적화</strong></div>
            <div class="helper-text">requested model=${escapeHtml(optimization.requested_model || "-")} · batch cap=${escapeHtml(optimization.batch_size_cap ?? "-")} · effective delay=${escapeHtml(optimization.effective_api_delay ?? "-")}</div>
            <div class="helper-text">document order: ${escapeHtml((optimization.document_order || []).join(", ") || "-")}</div>
        `;
        dom.resultsPanel.appendChild(info);
    }

    if (payload.adult_review_path) {
        const info = document.createElement("div");
        info.className = "result-row";
        info.innerHTML = `
            <div><strong>성인/실패 검토 파일</strong></div>
            <div class="helper-text">${payload.adult_review_path}</div>
        `;
        dom.resultsPanel.appendChild(info);
    }

    if (payload.halted) {
        const info = document.createElement("div");
        info.className = "result-row";
        info.innerHTML = `
            <div><strong>중단 사유</strong></div>
            <div class="helper-text">${escapeHtml(payload.halt_reason || "세션이 중단되었습니다.")}</div>
        `;
        dom.resultsPanel.appendChild(info);
    }

    if (payload.translation_session?.session_id) {
        const session = payload.translation_session;
        const info = document.createElement("div");
        info.className = "result-row";
        info.innerHTML = `
            <div><strong>번역 세션</strong></div>
            <div class="helper-text">session=${session.session_id} · resumed=${session.resumed_item_count || 0} · passthrough=${session.passthrough_item_count || 0} · completed docs=${session.completed_document_count || 0}</div>
            <div class="helper-text">completed batches=${session.completed_batch_count || 0} · failed batches=${session.failed_batch_count || 0} · halted=${session.halted ? "yes" : "no"}</div>
            <div class="helper-text">checkpoint: ${session.checkpoint_path || "-"}</div>
            <div class="helper-text">status: ${session.status_path || "-"}</div>
            <div class="helper-text">codex logs: ${session.translation_log_dir || "-"}</div>
        `;
        dom.resultsPanel.appendChild(info);
    }

    if (payload.publish_bundle?.supported) {
        const publish = payload.publish_bundle;
        const info = document.createElement("div");
        info.className = "result-row";
        info.innerHTML = `
            <div><strong>Ren'Py Publish Bundle</strong></div>
            <div class="helper-text">enabled=${publish.enabled ? "yes" : "no"} · lang=${escapeHtml(publish.language_code || "-")} · display=${escapeHtml(publish.display_name || "-")}</div>
            <div class="helper-text">publish root: ${escapeHtml(publish.publish_root || "-")}</div>
            <div class="helper-text">config: ${escapeHtml(publish.config_path || "-")}</div>
            <div class="helper-text">manifest: ${escapeHtml(publish.manifest_path || "-")}</div>
            <div class="helper-text">notes: ${escapeHtml(publish.notes_path || "-")}</div>
            <div class="helper-text">missing fonts: ${escapeHtml((publish.missing_fonts || []).join(", ") || "-")}</div>
        `;
        dom.resultsPanel.appendChild(info);
    } else if (payload.publish_bundle?.reason) {
        const info = document.createElement("div");
        info.className = "result-row";
        info.innerHTML = `
            <div><strong>Ren'Py Publish Bundle</strong></div>
            <div class="helper-text">${escapeHtml(payload.publish_bundle.reason)}</div>
        `;
        dom.resultsPanel.appendChild(info);
    }

    results.forEach((result) => {
        const row = document.createElement("div");
        row.className = "result-row";
        const details = [
            `상태: ${result.status || "success"}`,
            `번역 ${result.translated_count || 0}`,
            `성인 보류 ${result.skipped_adult_count || 0}`,
            `실패 ${result.failed_item_count || 0}`,
        ].join(" / ");
        row.innerHTML = `
            <div><strong>${result.original_filename}</strong></div>
            <div class="helper-text">${details}</div>
            <div class="helper-text">${escapeHtml(result.output_relative_path || result.translated_filename || "")}</div>
            ${result.publish_relative_path ? `<div class="helper-text">publish: ${escapeHtml(result.publish_relative_path)}</div>` : ""}
            <div class="result-links"></div>
        `;
        const links = row.querySelector(".result-links");
        if (result.translated_content) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "mini-button";
            button.textContent = "결과 다운로드";
            button.addEventListener("click", () => {
                downloadText(
                    result.translated_content,
                    result.translated_filename || result.original_filename || "translated.rpy",
                );
            });
            links.appendChild(button);
        }
        dom.resultsPanel.appendChild(row);
    });

    if ((payload.completed_documents || []).length) {
        const info = document.createElement("div");
        info.className = "result-row";
        const documentRows = (payload.completed_documents || []).map((entry) => `
            <div class="helper-text">${escapeHtml(entry.file_relative_path || "-")} · ${escapeHtml(entry.completion_state || entry.status || "-")} · pending=${escapeHtml(entry.pending_item_count ?? "-")} · stage=${escapeHtml(entry.output_relative_path || "-")}${entry.publish_relative_path ? ` · publish=${escapeHtml(entry.publish_relative_path)}` : ""}</div>
        `).join("");
        info.innerHTML = `
            <div><strong>완료/기록된 파일</strong></div>
            ${documentRows}
        `;
        dom.resultsPanel.appendChild(info);
    }
}


function populateFromAnalysis(analysis, label, options = {}) {
    captureCurrentCharacterProfiles();
    state.analysis = analysis;
    clearTonePreview();
    const availableFilePaths = applyAnalysisFileSelection(analysis, options);
    state.characterProfiles = {
        ...(analysis.default_character_profiles || {}),
        ...state.characterProfiles,
    };
    state.characterFilter = "";
    const nextCharacters = analysis.characters || [];
    const firstPlayableCharacter = nextCharacters.find((character) => !isSystemCharacter(character));
    state.selectedCharacterId = nextCharacters.some((character) => character.speaker_id === state.selectedCharacterId)
        ? state.selectedCharacterId
        : (firstPlayableCharacter?.speaker_id || nextCharacters[0]?.speaker_id || null);

    dom.analysisModeLabel.textContent = `${label} · ${analysis.analysis_mode}`;
    applyWorldSettings(analysis.default_world_settings || {}, false);
    applyPublishSettings(analysis.default_publish_settings || {}, false);
    renderSummary();
    renderWorldInference();
    renderPublishBaseline();
    renderDialoguePreview();
    renderFileTable();
    renderCharacterGrid();
    renderAdultQueue();
}


async function downloadRenpySDK() {
    addLog("Ren'Py SDK(약 150MB) 다운로드를 시작합니다...", "info");
    dom.generateTemplateButton.textContent = "SDK 다운로드 중...";
    try {
        const response = await apiPost("/download_renpy_sdk", {});
        addLog(response.message || "Ren'Py SDK 다운로드 완료", "success");
        return true;
    } catch (error) {
        addLog(`SDK 다운로드 실패: ${error.message}`, "error");
        alert(`❌ SDK 다운로드 중 오류가 발생했습니다.\n${error.message}`);
        return false;
    }
}

async function generateTemplate() {
    const gamePath = dom.gamePathInput.value.trim();
    if (!gamePath) {
        addLog("EXE 경로가 비어 있습니다.", "error");
        return;
    }
    const targetLang = dom.targetLanguageInput.value.trim() || "ko";
    
    dom.generateTemplateButton.disabled = true;
    const originalText = dom.generateTemplateButton.textContent;
    dom.generateTemplateButton.textContent = "뼈대 준비 중...";
    addLog(`템플릿 생성 요청: 언어[${targetLang}]`, "info");
    
    try {
        const response = await apiPost("/generate_template", {
            game_exe_path: gamePath,
            target_language: targetLang,
        });
        
        if (response.status === "cached") {
            addLog(response.message, "success");
            alert(`✅ ${response.message}\n바로 [게임 분석] 버튼을 눌러주세요.`);
        } else if (response.status === "success") {
            addLog(response.message, "success");
            alert(`✅ 템플릿 자동 추출 완료!\n이제 [게임 분석] 버튼을 눌러 번역을 시작하세요.`);
        } else {
            addLog(`알 수 없는 응답: ${JSON.stringify(response)}`, "warning");
        }
    } catch (error) {
        if (error.message.includes("SDK_MISSING")) {
            const wantsDownload = confirm("Ren'Py SDK(약 150MB)가 설치되어 있지 않습니다.\n템플릿(뼈대) 추출을 위해 공식 SDK를 다운로드하시겠습니까?\n(다운로드 중에는 잠시 멈춘 것처럼 보일 수 있습니다.)");
            if (wantsDownload) {
                const downloadSuccess = await downloadRenpySDK();
                if (downloadSuccess) {
                    // 다운로드 성공 시 다시 템플릿 생성 시도
                    dom.generateTemplateButton.disabled = false;
                    dom.generateTemplateButton.textContent = originalText;
                    await generateTemplate();
                    return; // 재귀 호출 완료 후 종료
                }
            } else {
                addLog("사용자가 SDK 다운로드를 취소했습니다.", "warning");
            }
        } else {
            addLog(`템플릿 생성 실패: ${error.message}`, "error");
            alert(`❌ 템플릿 생성 중 오류가 발생했습니다.\n${error.message}`);
        }
    } finally {
        dom.generateTemplateButton.disabled = false;
        dom.generateTemplateButton.textContent = originalText;
    }
}


async function analyzeGame(options = {}) {
    const gamePath = dom.gamePathInput.value.trim();
    if (!gamePath) {
        const error = new Error("게임 경로가 비어 있습니다.");
        addLog(error.message, "error");
        if (options.raiseOnError) {
            throw error;
        }
        return null;
    }
    dom.analyzeGameButton.disabled = true;
    addLog(`게임 분석 요청: ${gamePath}`);
    try {
        const analysis = await apiPost("/analyze_sources", {
            game_exe_path: gamePath,
            target_language: dom.targetLanguageInput.value.trim() || "ko",
        });
        populateFromAnalysis(analysis, "게임 경로 분석", {
            selectionMode: options.selectionMode || "reset",
        });
        addLog(`분석 완료: ${analysis.summary.file_count}개 파일 / ${analysis.summary.item_count}개 항목`, "success");
        addLog(`파일 선택: ${state.selectedFiles.size}/${analysis.summary.file_count}`, "info");
        activateTab("overview");
        return analysis;
    } catch (error) {
        addLog(`게임 분석 실패: ${error.message}`, "error");
        if (options.raiseOnError) {
            throw error;
        }
        return null;
    } finally {
        dom.analyzeGameButton.disabled = false;
    }
}


async function repairTranslationOutputs() {
    const gamePath = dom.gamePathInput.value.trim();
    if (!gamePath) {
        addLog("게임 경로가 비어 있습니다.", "error");
        return;
    }

    dom.repairOutputsButton.disabled = true;
    const originalText = dom.repairOutputsButton.textContent;
    dom.repairOutputsButton.textContent = "복구 중...";
    addLog(`출력 검증/복구 요청: ${gamePath}`, "info");

    try {
        const response = await apiPost("/repair_translation_outputs", {
            game_exe_path: gamePath,
            target_language: dom.targetLanguageInput.value.trim() || "ko",
            publish_settings: collectPublishSettings(),
        });
        const repairedCount = Number(response.repaired_outputs?.changed_paths?.length || 0);
        const cacheCount = Number(response.cache_cleanup_count || 0);
        const compiledCount = Number(response.compiled_cleanup_count || 0);
        addLog(
            `출력 검증/복구 완료: repaired=${repairedCount}, cache=${cacheCount}, compiled=${compiledCount}`,
            repairedCount > 0 ? "success" : "info",
        );
        if (response.nested_artifact_migration?.moved_paths?.length) {
            addLog(`중첩된 워크벤치 산출물 ${response.nested_artifact_migration.moved_paths.length}개를 회수했습니다.`, "warning");
        }
        await analyzeGame({ selectionMode: "preserve" });
    } catch (error) {
        addLog(`출력 검증/복구 실패: ${error.message}`, "error");
    } finally {
        dom.repairOutputsButton.disabled = false;
        dom.repairOutputsButton.textContent = originalText;
    }
}


async function applyPublishFontsOnly() {
    const gamePath = dom.gamePathInput.value.trim();
    if (!gamePath) {
        addLog("게임 경로가 비어 있습니다.", "error");
        return;
    }
    if (!state.analysis) {
        addLog("먼저 게임 분석을 실행한 뒤 폰트를 다시 적용하세요.", "warning");
        return;
    }

    dom.applyPublishFontsButton.disabled = true;
    const originalText = dom.applyPublishFontsButton.textContent;
    dom.applyPublishFontsButton.textContent = "폰트 적용 중..";
    addLog("publish bundle 글꼴/설정만 다시 적용합니다.", "info");

    try {
        const response = await apiPost("/apply_publish_fonts", {
            game_exe_path: gamePath,
            analysis_mode: state.analysis.analysis_mode || "translation_layer",
            target_language: dom.targetLanguageInput.value.trim() || "ko",
            publish_settings: collectPublishSettings(),
        });
        if (response.publish_bundle?.publish_root) {
            addLog(
                `폰트만 재적용 완료: ${response.publish_bundle.publish_root} · copied fonts ${response.font_asset_count || 0}`,
                "success",
            );
            if (response.publish_bundle.config_path) {
                addLog(`언어 설정 파일: ${response.publish_bundle.config_path}`, "info");
            }
        } else if (response.publish_bundle?.reason) {
            addLog(`폰트 재적용 경고: ${response.publish_bundle.reason}`, "warning");
        } else {
            addLog("폰트만 재적용 완료", "success");
        }
        activateTab("results");
    } catch (error) {
        addLog(`폰트만 재적용 실패: ${error.message}`, "error");
    } finally {
        dom.applyPublishFontsButton.disabled = false;
        dom.applyPublishFontsButton.textContent = originalText;
    }
}


async function pickExeAndAnalyze() {
    dom.pickExeButton.disabled = true;
    addLog("EXE 선택창 요청");
    try {
        const response = await apiGet("/pick_game_exe");
        if (!response.path) {
            addLog("EXE 선택이 취소되었습니다.", "warning");
            return;
        }
        dom.gamePathInput.value = response.path;
        addLog(`EXE 선택 완료: ${response.path}`);
        await analyzeGame();
    } catch (error) {
        addLog(`EXE 선택 실패: ${error.message}`, "error");
    } finally {
        dom.pickExeButton.disabled = false;
    }
}


async function analyzeUploads() {
    if (!state.uploadedFiles.length) {
        addLog("업로드된 파일이 없습니다.", "warning");
        return;
    }
    dom.analyzeUploadsButton.disabled = true;
    addLog(`업로드 파일 분석 요청: ${state.uploadedFiles.length}개`);
    try {
        const analysis = await apiPost("/analyze_sources", {
            files_data: state.uploadedFiles,
            target_language: dom.targetLanguageInput.value.trim() || "ko",
        });
        populateFromAnalysis(analysis, "업로드 파일 분석", { selectionMode: "reset" });
        addLog(`업로드 분석 완료: ${analysis.summary.file_count}개 파일 / ${analysis.summary.item_count}개 항목`, "success");
        activateTab("overview");
    } catch (error) {
        addLog(`업로드 분석 실패: ${error.message}`, "error");
    } finally {
        dom.analyzeUploadsButton.disabled = false;
    }
}


async function handleUploadChange(event) {
    const files = Array.from(event.target.files || []);
    if (!files.length) {
        return;
    }
    const loaded = await Promise.all(files.map(async (file) => ({
        file_name: file.name,
        file_content: await file.text(),
    })));
    state.uploadedFiles = loaded;
    renderUploadList();
    addLog(`업로드 완료: ${loaded.length}개 파일`);
    event.target.value = "";
}


function setOpenAIOAuthBusy(isBusy) {
    dom.setupOpenAIOAuthButton.disabled = isBusy;
    dom.checkOpenAIOAuthButton.disabled = isBusy;
}


function clearOpenAIOAuthPoll() {
    if (state.oauthStatusPollHandle) {
        clearTimeout(state.oauthStatusPollHandle);
        state.oauthStatusPollHandle = null;
    }
}


function formatOpenAIOAuthStatus(response) {
    const parts = [];
    if (!response?.npm?.available || !response?.npx?.available) {
        if (!response?.npm?.available) {
            parts.push("npm이 없어 Codex CLI를 설치할 수 없습니다.");
        }
        if (!response?.npx?.available) {
            parts.push("npx가 없어 Codex CLI 래퍼를 실행할 수 없습니다.");
        }
        return parts.join(" · ");
    }

    if (response.install_result?.ok) {
        parts.push(`Codex CLI 설치 완료${response.global_install?.version ? ` (${response.global_install.version})` : ""}`);
    } else if (response.global_install?.installed) {
        parts.push(`Codex CLI 설치됨${response.global_install?.version ? ` (${response.global_install.version})` : ""}`);
    } else {
        parts.push("Codex CLI 전역 설치 없음");
    }

    if (response.login?.logged_in) {
        parts.push(response.login.summary || "ChatGPT 로그인 완료");
    } else if (response.login_launch?.started) {
        parts.push("로그인 창을 열었습니다. 브라우저에서 ChatGPT 인증을 완료하세요.");
    } else {
        parts.push(response.login?.summary || "Codex 로그인 필요");
    }

    if (response.cli?.available) {
        parts.push(`실행 가능: ${response.cli.summary || "codex exec 사용 가능"}`);
    } else {
        parts.push(`실행 불가: ${response.cli?.summary || response.cli?.detail || "CLI 실행 실패"}`);
    }

    return parts.join(" · ");
}


function applyOpenAIOAuthSetupStatus(response, logType = "info") {
    if (response?.command) {
        dom.openaiOAuthCommandInput.value = response.command;
    }
    dom.openaiOAuthStatus.textContent = formatOpenAIOAuthStatus(response);
    if (response?.message) {
        addLog(response.message, logType);
    }
}


async function pollOpenAIOAuthReadiness(remaining = 15) {
    clearOpenAIOAuthPoll();
    if (remaining <= 0 || !usesOpenAIOAuth()) {
        return;
    }

    state.oauthStatusPollHandle = setTimeout(async () => {
        try {
            const response = await apiPost("/openai_oauth_setup", {
                command: normalizeOpenAIOAuthCommand(dom.openaiOAuthCommandInput.value),
                install_if_missing: false,
                launch_login: false,
            });
            applyOpenAIOAuthSetupStatus(response);
            if (!response.ready) {
                await pollOpenAIOAuthReadiness(remaining - 1);
            }
        } catch (error) {
            dom.openaiOAuthStatus.textContent = `OAuth 상태 확인 실패: ${error.message}`;
            addLog(`OpenAI OAuth 상태 확인 실패: ${error.message}`, "error");
        }
    }, 4000);
}


async function checkOpenAIOAuthStatus() {
    clearOpenAIOAuthPoll();
    setOpenAIOAuthBusy(true);
    dom.openaiOAuthStatus.textContent = "Codex CLI 설치/로그인 상태를 확인하는 중입니다...";
    try {
        const response = await apiPost("/openai_oauth_setup", {
            command: normalizeOpenAIOAuthCommand(dom.openaiOAuthCommandInput.value),
            install_if_missing: false,
            launch_login: false,
        });
        applyOpenAIOAuthSetupStatus(response, response.ready ? "success" : "warning");
    } catch (error) {
        dom.openaiOAuthStatus.textContent = `CLI 점검 실패: ${error.message}`;
        addLog(`OpenAI OAuth CLI 점검 실패: ${error.message}`, "error");
    } finally {
        setOpenAIOAuthBusy(false);
    }
}


async function setupOpenAIOAuth() {
    clearOpenAIOAuthPoll();
    setOpenAIOAuthBusy(true);
    dom.openaiOAuthStatus.textContent = "Codex CLI 설치와 ChatGPT OAuth 로그인을 준비하는 중입니다...";
    try {
        const response = await apiPost("/openai_oauth_setup", {
            command: normalizeOpenAIOAuthCommand(dom.openaiOAuthCommandInput.value),
            install_if_missing: true,
            launch_login: true,
        });
        applyOpenAIOAuthSetupStatus(response, response.ready ? "success" : "info");
        if (response.login_launch?.started && !response.ready) {
            addLog("새 터미널 창에서 Codex device-auth 로그인을 진행하세요.", "info");
            await pollOpenAIOAuthReadiness();
        }
    } catch (error) {
        dom.openaiOAuthStatus.textContent = `자동 설치/로그인 실패: ${error.message}`;
        addLog(`OpenAI OAuth 자동 설치/로그인 실패: ${error.message}`, "error");
    } finally {
        setOpenAIOAuthBusy(false);
    }
}


function buildTranslationPayload(options = {}) {
    const apiKey = dom.apiKeyInput.value.trim();
    if (supportsApiKey() && !apiKey) {
        throw new Error("API 키를 입력하세요.");
    }
    if (usesGeminiVertex() && !(dom.vertexProjectIdInput?.value || "").trim()) {
        throw new Error("Vertex AI를 사용하려면 GCP 프로젝트 ID를 입력하세요.");
    }
    if (!state.analysis) {
        throw new Error("먼저 분석을 실행하세요.");
    }
    if (!state.selectedFiles.size) {
        throw new Error("번역할 파일을 하나 이상 선택하세요.");
    }
    const payload = {
        provider: dom.providerSelect.value,
        api_key: apiKey,
        gemini_auth_mode: getGeminiAuthMode(),
        openai_auth_mode: getOpenAIAuthMode(),
        openai_oauth_command: normalizeOpenAIOAuthCommand(dom.openaiOAuthCommandInput.value),
        model_name: dom.modelInput.value.trim(),
        target_language: dom.targetLanguageInput.value.trim() || "ko",
        translation_rule: options.translationRule || getTranslationRuleValue(),
        batch_size: Number(dom.batchSizeInput.value || getDefaultBatchSizeValue()),
        api_delay: Number(dom.apiDelayInput.value || getDefaultApiDelayValue()),
        include_adult_content: options.includeAdultContent ?? dom.includeAdultCheckbox.checked,
        selected_files: Array.from(state.selectedFiles),
        character_profiles: collectCharacterProfiles(),
        world_settings: collectWorldSettings(),
        vertex_settings: collectVertexSettings(),
        publish_settings: collectPublishSettings(),
    };
    const selectedSpeakerIds = Array.isArray(options.selectedSpeakerIds)
        ? options.selectedSpeakerIds.map((value) => String(value || "").trim()).filter(Boolean)
        : [];
    const selectedItemIds = Array.isArray(options.selectedItemIds)
        ? options.selectedItemIds.map((value) => String(value || "").trim()).filter(Boolean)
        : [];
    if (selectedItemIds.length) {
        payload.selected_item_ids = selectedItemIds;
        payload.force_retranslate = options.forceRetranslate !== false;
        payload.translation_scope = {
            mode: "selected_items",
            selected_speaker_ids: [],
            selected_speaker_names: [],
            selected_item_ids: selectedItemIds,
            selected_item_count: selectedItemIds.length,
            translation_rule: payload.translation_rule,
        };
    } else if (selectedSpeakerIds.length) {
        const selectedSpeakerNames = selectedSpeakerIds
            .map((speakerId) => {
                const character = getCharacterBySpeakerId(speakerId);
                const profile = state.characterProfiles[speakerId] || {};
                return profile.display_name || character?.display_name || speakerId;
            })
            .filter(Boolean);
        payload.selected_speaker_ids = selectedSpeakerIds;
        payload.force_retranslate = options.forceRetranslate !== false;
        payload.translation_scope = {
            mode: "selected_speakers",
            selected_speaker_ids: selectedSpeakerIds,
            selected_speaker_names: selectedSpeakerNames,
            translation_rule: payload.translation_rule,
        };
    } else {
        payload.translation_scope = {
            mode: "all_items",
            selected_speaker_ids: [],
            selected_speaker_names: [],
            translation_rule: payload.translation_rule,
        };
    }

    if (dom.gamePathInput.value.trim()) {
        payload.game_exe_path = dom.gamePathInput.value.trim();
    } else if (state.uploadedFiles.length) {
        payload.files_data = state.uploadedFiles;
    } else {
        throw new Error("게임 경로 또는 업로드 파일이 필요합니다.");
    }
    return payload;
}


async function translateSelection(options = {}) {
    let payload;
    try {
        payload = buildTranslationPayload(options);
    } catch (error) {
        addLog(error.message, "error");
        return;
    }

    dom.translateButton.disabled = true;
    resetTranslationProgressUi();
    const runtimeLabel = payload.provider === "openai" && payload.openai_auth_mode === "oauth_cli"
        ? "openai-oauth"
        : payload.provider;
    addLog(`번역 요청 시작: ${payload.selected_files.length}개 파일 / runtime=${runtimeLabel}`);
    if (state.analysis?.files?.length && payload.selected_files.length < state.analysis.files.length) {
        addLog(`부분 번역 범위: 전체 ${state.analysis.files.length}개 중 ${payload.selected_files.length}개 파일만 선택됨`, "warning");
    }
    addLog(`요청 범위: ${buildTranslationScopeLabel(payload)}`);
    try {
        await prepareTranslationProgressUi(payload);
        const response = await apiPost("/translate", payload);
        state.translationProgressRequestActive = false;
        if (response.translation_session?.session_id) {
            state.translationProgressSession = {
                session_id: response.translation_session.session_id,
                analysis_mode: state.analysis?.analysis_mode || "translation_layer",
                target_language: payload.target_language,
                game_exe_path: payload.game_exe_path || "",
                status_path: response.translation_session.status_path || state.translationProgressSession?.status_path || "",
            };
        }
        await fetchTranslationProgressStatusUi();
        renderResults(response);
        const logType = response.halted || response.failed_item_count ? "warning" : "success";
        addLog(
            `번역 ${response.halted ? "부분 완료/중단" : "완료"}: 실패 ${response.failed_item_count || 0}, 성인 보류 ${response.skipped_adult_count || 0}, 완료 파일 ${response.translation_session?.completed_document_count || 0}`,
            logType,
        );
        if (response.translation_session?.resumed_item_count) {
            addLog(`체크포인트 재개: ${response.translation_session.resumed_item_count}개 항목을 이어받았습니다.`);
        }
        if (response.translation_session?.passthrough_item_count) {
            addLog(`패스스루 처리: ${response.translation_session.passthrough_item_count}개 항목은 API 호출 없이 그대로 유지했습니다.`);
        }
        if (response.translation_session?.translation_log_dir) {
            addLog(`Codex 로그 폴더: ${response.translation_session.translation_log_dir}`);
        }
        if (response.translation_session?.checkpoint_path) {
            addLog(`체크포인트 파일: ${response.translation_session.checkpoint_path}`);
        }
        if (response.halted && response.halt_reason) {
            addLog(`세션 중단: ${response.halt_reason}`, "warning");
        }
        if (response.publish_bundle?.publish_root) {
            addLog(`Ren'Py publish bundle: ${response.publish_bundle.publish_root}`, "success");
        } else if (response.publish_bundle?.reason) {
            addLog(`Ren'Py publish bundle: ${response.publish_bundle.reason}`, "warning");
        }
        if (options.refreshAnalysisAfterSuccess && state.analysis) {
            try {
                const analysis = await apiPost("/analyze_sources", buildCurrentAnalysisPayload());
                populateFromAnalysis(analysis, "재번역 반영", { selectionMode: "preserve" });
            } catch (refreshError) {
                addLog(`재분석 실패: ${refreshError.message}`, "warning");
            }
        }
        activateTab(options.activateTabName || "results");
    } catch (error) {
        state.translationProgressRequestActive = false;
        await fetchTranslationProgressStatusUi();
        addLog(`번역 실패: ${error.message}`, "error");
        activateTab("results");
    } finally {
        resetTranslationProgressUi({ preserveSession: true });
        dom.translateButton.disabled = false;
    }
}


async function attachTranslationProgress() {
    let payload;
    try {
        payload = buildTranslationPayload();
    } catch (error) {
        addLog(`진행도 연결 실패: ${error.message}`, "error");
        return;
    }

    resetTranslationProgressUi();
    try {
        const response = await apiPostProgress("/find_active_translation_session", payload);
        state.translationProgressSession = {
            session_id: response.session_id,
            analysis_mode: response.analysis_mode,
            target_language: response.target_language,
            game_exe_path: payload.game_exe_path || "",
            status_path: response.status_path || "",
        };
        state.translationProgressStatus = response.status || null;
        state.translationProgressRequestActive = Boolean(response.active);
        renderTranslationProgressUi();
        if (response.status) {
            logTranslationProgressUpdate(response.status, { force: true, type: response.active ? "info" : "success" });
        }
        activateTab("results");
        await fetchTranslationProgressStatusUi();
        state.translationProgressPollHandle = window.setInterval(() => {
            fetchTranslationProgressStatusUi().catch(() => {});
        }, 2000);

        const requestedScope = normalizeProgressScope(payload.translation_scope || {});
        const matchedScope = normalizeProgressScope(response.translation_scope || {});
        if (!response.active) {
            addLog(`현재 진행 중인 번역 세션은 없습니다. 최근 세션 상태를 표시합니다: session=${response.session_id}`, "warning");
        } else if (JSON.stringify(requestedScope) !== JSON.stringify(matchedScope)) {
            addLog(`현재 설정과 다른 활성 세션에 연결했습니다: session=${response.session_id}`, "warning");
        } else {
            addLog(`진행도 연결: session=${response.session_id}`, "success");
        }
        return;
    } catch (error) {
        addLog(`활성 세션 자동 탐색 실패: ${error.message}`, "warning");
    }

    await prepareTranslationProgressUi(payload);
    if (state.translationProgressSession?.session_id) {
        addLog(`현재 설정 기준 세션에 연결: session=${state.translationProgressSession.session_id}`, "success");
        activateTab("results");
    }
}


async function retranslateSelectedCharacter(speakerId = state.selectedCharacterId) {
    if (!speakerId) {
        addLog("재번역할 캐릭터를 먼저 선택하세요.", "warning");
        return;
    }
    if (dom.translateButton.disabled) {
        addLog("다른 번역 작업이 진행 중입니다.", "warning");
        return;
    }
    const character = getCharacterBySpeakerId(speakerId);
    const displayName = state.characterProfiles[speakerId]?.display_name || character?.display_name || speakerId;
    addLog(`캐릭터 재번역 요청: ${displayName}`, "info");
    await translateSelection({
        selectedSpeakerIds: [speakerId],
        translationRule: "retranslate_existing",
        forceRetranslate: true,
    });
}


async function retranslateIssueCandidates(itemIds = Array.from(state.selectedIssueCandidateIds)) {
    const normalizedIds = itemIds.map((value) => String(value || "").trim()).filter(Boolean);
    if (!normalizedIds.length) {
        addLog("재번역할 문제 후보를 먼저 선택하세요.", "warning");
        return;
    }
    if (dom.translateButton.disabled) {
        addLog("다른 번역 작업이 진행 중입니다.", "warning");
        return;
    }
    addLog(`문제 후보 재번역 요청: ${normalizedIds.length}개 항목`, "info");
    await translateSelection({
        selectedItemIds: normalizedIds,
        translationRule: "force_all",
        forceRetranslate: true,
        refreshAnalysisAfterSuccess: true,
        activateTabName: "issues",
    });
}


async function translateSelectedAdultQueue(itemIds = Array.from(state.selectedAdultQueueIds)) {
    const normalizedIds = itemIds.map((value) => String(value || "").trim()).filter(Boolean);
    if (!normalizedIds.length) {
        addLog("자동번역할 성인 대사를 먼저 선택하세요.", "warning");
        return;
    }
    if (dom.translateButton.disabled) {
        addLog("다른 번역 작업이 진행 중입니다.", "warning");
        return;
    }
    addLog(`성인 큐 자동번역 요청: ${normalizedIds.length}개 항목`, "info");
    await translateSelection({
        selectedItemIds: normalizedIds,
        includeAdultContent: true,
        translationRule: "force_all",
        forceRetranslate: true,
        refreshAnalysisAfterSuccess: true,
        activateTabName: "adult",
    });
}


function buildProfilePayload() {
    const vertexSettings = collectVertexSettings();
    return {
        translation_preset_id: state.selectedTranslationPresetId || inferTranslationPresetId() || "",
        provider: dom.providerSelect.value,
        gemini_auth_mode: getGeminiAuthMode(),
        openai_auth_mode: getOpenAIAuthMode(),
        openai_oauth_command: normalizeOpenAIOAuthCommand(dom.openaiOAuthCommandInput.value),
        model_name: dom.modelInput.value.trim(),
        target_language: dom.targetLanguageInput.value.trim(),
        translation_rule: getTranslationRuleValue(),
        batch_size: Number(dom.batchSizeInput.value || getDefaultBatchSizeValue()),
        api_delay: Number(dom.apiDelayInput.value || getDefaultApiDelayValue()),
        include_adult_content: dom.includeAdultCheckbox.checked,
        game_path: dom.gamePathInput.value.trim(),
        world_settings: collectWorldSettings(),
        vertex_settings: {
            ...vertexSettings,
            credentials_json: "",
        },
        publish_settings: collectPublishSettings(),
        character_profiles: collectCharacterProfiles(),
        selected_files: Array.from(state.selectedFiles),
        analysis: state.analysis,
    };
}


function saveProfile() {
    downloadText(
        JSON.stringify(buildProfilePayload(), null, 2),
        `renpy_translation_profile_${new Date().toISOString().slice(0, 10)}.json`,
    );
    addLog("프로필 JSON 저장 완료", "success");
}


function normalizeLoadedCharacterProfiles(value) {
    if (Array.isArray(value)) {
        return Object.fromEntries(
            value
                .filter((entry) => entry && typeof entry === "object" && entry.speaker_id)
                .map((entry) => [String(entry.speaker_id), { ...entry }]),
        );
    }
    if (value && typeof value === "object") {
        return value;
    }
    return {};
}


function normalizeLoadedProfile(profile = {}) {
    const normalized = (profile && typeof profile === "object") ? { ...profile } : {};
    const targetLanguage = normalized.target_language || normalized.language || "ko";
    return {
        ...normalized,
        provider: normalized.provider || normalized.translation_provider || "gemini",
        gemini_auth_mode: normalized.gemini_auth_mode || normalized.gemini_mode || "api_key",
        openai_auth_mode: normalized.openai_auth_mode || normalized.auth_mode || "api_key",
        openai_oauth_command: normalized.openai_oauth_command || normalized.codex_command || "",
        model_name: normalized.model_name || normalized.model || "",
        target_language: normalized.target_language || normalized.language || "ko",
        translation_rule: normalized.translation_rule || normalized.translation_mode || "missing_only",
        batch_size: normalizeNumericSetting(
            normalized.batch_size ?? normalized.chunk_size,
            getDefaultBatchSizeValue(normalized.provider || normalized.translation_provider || "gemini", normalized.openai_auth_mode || normalized.auth_mode || "api_key"),
        ),
        api_delay: normalizeNumericSetting(
            normalized.api_delay ?? normalized.request_delay,
            getDefaultApiDelayValue(normalized.provider || normalized.translation_provider || "gemini", normalized.openai_auth_mode || normalized.auth_mode || "api_key"),
        ),
        include_adult_content: Boolean(normalized.include_adult_content ?? normalized.include_adult ?? false),
        game_path: normalized.game_path || normalized.game_exe_path || "",
        world_settings: normalized.world_settings || normalized.default_world_settings || {},
        vertex_settings: normalized.vertex_settings || {},
        publish_settings: sanitizeLegacyPublishSettings(
            normalized.publish_settings || normalized.default_publish_settings || {},
            targetLanguage,
        ),
        character_profiles: normalizeLoadedCharacterProfiles(normalized.character_profiles),
        selected_files: Array.isArray(normalized.selected_files)
            ? normalized.selected_files
            : (Array.isArray(normalized.selected_file_paths) ? normalized.selected_file_paths : []),
        analysis: (() => {
            const analysisValue = normalized.analysis || normalized.analysis_snapshot || null;
            return analysisValue && typeof analysisValue === "object" ? analysisValue : null;
        })(),
    };
}


function applyProfile(profile) {
    profile = normalizeLoadedProfile(profile);
    const inferredPresetId = profile.translation_preset_id || inferTranslationPresetId({
        provider: profile.provider || "gemini",
        openaiAuthMode: profile.openai_auth_mode || "api_key",
        modelName: profile.model_name || "",
        batchSize: normalizeNumericSetting(profile.batch_size, getDefaultBatchSizeValue(profile.provider || "gemini", profile.openai_auth_mode || "api_key")),
        apiDelay: normalizeNumericSetting(profile.api_delay, getDefaultApiDelayValue(profile.provider || "gemini", profile.openai_auth_mode || "api_key")),
    });

    if (inferredPresetId) {
        applyTranslationPreset(inferredPresetId, { log: false });
    }

    dom.providerSelect.value = profile.provider || dom.providerSelect.value || "gemini";
    dom.geminiAuthModeSelect.value = profile.gemini_auth_mode || dom.geminiAuthModeSelect.value || "api_key";
    dom.openaiAuthModeSelect.value = profile.openai_auth_mode || dom.openaiAuthModeSelect.value || "api_key";
    dom.openaiOAuthCommandInput.value = normalizeOpenAIOAuthCommand(profile.openai_oauth_command);
    updateModelSuggestions();
    dom.apiKeyInput.value = supportsApiKey(
        profile.provider || dom.providerSelect.value,
        profile.openai_auth_mode || getOpenAIAuthMode(),
        profile.gemini_auth_mode || getGeminiAuthMode(),
    ) ? (profile.api_key || "") : "";
    if (!dom.apiKeyInput.value) {
        syncStoredApiKeyForCurrentScope();
    } else {
        handleApiKeyMutation({ rerender: false });
    }
    dom.modelInput.value = profile.model_name || dom.modelInput.value;
    dom.targetLanguageInput.value = profile.target_language || "ko";
    if (dom.translationRuleSelect) {
        dom.translationRuleSelect.value = profile.translation_rule || "missing_only";
    }
    dom.batchSizeInput.value = profile.batch_size || getDefaultBatchSizeValue(profile.provider || dom.providerSelect.value, profile.openai_auth_mode || getOpenAIAuthMode());
    dom.apiDelayInput.value = profile.api_delay ?? getDefaultApiDelayValue(profile.provider || dom.providerSelect.value, profile.openai_auth_mode || getOpenAIAuthMode());
    dom.includeAdultCheckbox.checked = Boolean(profile.include_adult_content);
    dom.gamePathInput.value = profile.game_path || "";
    dom.vertexProjectIdInput.value = profile.vertex_settings?.project_id || "";
    dom.vertexLocationInput.value = profile.vertex_settings?.location || dom.vertexLocationInput.value || "global";
    dom.vertexCredentialsPathInput.value = profile.vertex_settings?.credentials_path || "";
    dom.vertexCredentialsJsonInput.value = profile.vertex_settings?.credentials_json || "";
    setVertexCredentialsStatus(dom.vertexCredentialsJsonInput.value.trim()
        ? "프로필에 저장된 서비스 계정 JSON을 복원했습니다."
        : "경로, JSON 파일 로드, JSON 붙여넣기 중 하나만 사용해도 됩니다. JSON에 project_id가 있으면 프로젝트 ID를 자동으로 채웁니다.");
    applyWorldSettings(profile.world_settings || {}, true);
    applyPublishSettings(profile.publish_settings || {}, true);
    state.characterProfiles = profile.character_profiles || {};
    clearTonePreview();
    state.selectedFiles = Array.isArray(profile.selected_files)
        ? new Set(profile.selected_files)
        : new Set();
    updateFileSelectionState();
    syncTranslationPresetSelection();
    renderTranslationHint();
    if (state.analysis) {
        renderFileTable();
        renderCharacterGrid();
    }
}


async function handleProfileLoad(event) {
    const file = event.target.files?.[0];
    if (!file) {
        return;
    }
    try {
        const rawText = await file.text();
        const profile = normalizeLoadedProfile(JSON.parse(rawText || "{}"));
        applyProfile(profile);
        addLog("프로필 JSON 불러오기 완료", "success");

        if (profile.game_path) {
            addLog("프로필의 게임 경로를 기준으로 분석을 다시 실행합니다.");
            try {
                await analyzeGame({ raiseOnError: true, selectionMode: "preserve" });
            } catch (analysisError) {
                if (profile.analysis) {
                    populateFromAnalysis(profile.analysis, "프로필 내장 분석 복원", { selectionMode: "preserve" });
                    addLog(`분석 재실행 실패로 저장된 분석 데이터를 복원했습니다: ${analysisError.message}`, "warning");
                } else {
                    throw analysisError;
                }
            }
        } else if (profile.analysis) {
            populateFromAnalysis(profile.analysis, "프로필 내장 분석 복원", { selectionMode: "preserve" });
            addLog("프로필에 포함된 분석 데이터를 복원했습니다.", "success");
        } else if (!state.analysis) {
            addLog("프로필은 불러왔지만 복원할 분석 데이터가 없어서 설정만 적용했습니다.", "warning");
        }
    } catch (error) {
        addLog(`프로필 불러오기 실패: ${error.message}`, "error");
    } finally {
        event.target.value = "";
    }
}


function handleGlossaryClick(event) {
    if (event.target.dataset.action === "remove-row") {
        event.target.closest(".glossary-row")?.remove();
        if (!dom.glossaryTable.children.length) {
            addGlossaryRow();
        }
    }
}


function handleStyleOverrideClick(event) {
    if (event.target.dataset.action === "remove-style-row") {
        event.target.closest(".style-override-row")?.remove();
        if (!dom.styleOverrideTable.children.length) {
            addStyleOverrideRow();
        }
    }
}


function handleFontPresetApply() {
    const presetId = dom.fontPresetSelect.value;
    if (!presetId) {
        addLog("적용할 폰트 프리셋을 먼저 선택하세요.", "warning");
        return;
    }
    applyFontPreset(presetId);
}


function handlePublishControlInput(event) {
    const target = event.target;
    if (!target) {
        return;
    }
    const fontControlIds = new Set([
        "dialogueFontSelect",
        "nameFontSelect",
        "optionsFontSelect",
        "interfaceFontSelect",
        "systemFontSelect",
        "glyphFontSelect",
        "dialogueScaleInput",
        "nameScaleInput",
        "optionsScaleInput",
        "interfaceScaleInput",
    ]);
    if (fontControlIds.has(target.id) && target.id !== "fontPresetSelect") {
        state.selectedFontPresetId = "";
        updateFontPresetOptions(state.analysis?.gui_baseline?.font_presets || [], "");
    }
    if (fontControlIds.has(target.id)) {
        renderCurrentFontPreviewGrid();
        renderSystemFontGallery();
    }
}


function handleCurrentFontPreviewGridInput(event) {
    const scaleFieldId = event.target?.dataset?.scaleFieldId || "";
    if (!scaleFieldId) {
        return;
    }
    const linkedField = document.getElementById(scaleFieldId);
    if (!linkedField) {
        return;
    }
    linkedField.value = event.target.value;
    handlePublishControlInput({ target: linkedField });
}


function handleFileSelection(event) {
    if (event.target.type !== "checkbox") {
        return;
    }
    const filePath = event.target.dataset.path;
    if (!filePath) {
        return;
    }
    if (event.target.checked) {
        state.selectedFiles.add(filePath);
    } else {
        state.selectedFiles.delete(filePath);
    }
    updateFileSelectionState();
    renderTranslationHint();
    renderIssueCandidates();
    renderAdultQueue();
}


async function previewCharacterTone(speakerId = state.selectedCharacterId) {
    if (!speakerId || !state.analysis) {
        return;
    }

    captureCurrentCharacterProfiles();
    const character = (state.analysis.characters || []).find((entry) => entry.speaker_id === speakerId);
    if (!character || !(character.sample_lines || []).length) {
        addLog("샘플 미리 번역에 사용할 대사가 없습니다.", "warning");
        return;
    }

    const provider = dom.providerSelect.value || "gemini";
    const geminiAuthMode = getGeminiAuthMode();
    const openaiAuthMode = getOpenAIAuthMode();
    const profile = state.characterProfiles[speakerId] || {};
    const payload = {
        provider,
        gemini_auth_mode: geminiAuthMode,
        openai_auth_mode: openaiAuthMode,
        openai_oauth_command: normalizeOpenAIOAuthCommand(dom.openaiOAuthCommandInput.value),
        model_name: dom.modelInput.value.trim(),
        target_language: dom.targetLanguageInput.value.trim() || "ko",
        include_adult_content: dom.includeAdultCheckbox.checked,
        world_settings: collectWorldSettings(),
        vertex_settings: collectVertexSettings(),
        character_profiles: collectCharacterProfiles(),
        speaker_id: character.speaker_id,
        speaker_name: profile.display_name || character.display_name || character.speaker_id,
        sample_lines: (character.sample_lines || []).slice(0, 4),
    };

    if (supportsApiKey(provider, openaiAuthMode, geminiAuthMode)) {
        payload.api_key = dom.apiKeyInput.value.trim();
    }

    state.tonePreviewLoadingSpeakerId = speakerId;
    renderSelectedCharacterDetail();
    try {
        const response = await apiPost("/preview_character_tone", payload);
        state.tonePreviewByCharacter[speakerId] = { ...response, cacheable: true, cacheHit: false };
        addLog(`샘플 미리 번역 완료: ${character.display_name || character.speaker_id} · ${response.tone_preset_name || "직접 입력"}`, "success");
    } catch (error) {
        addLog(`샘플 미리 번역 실패: ${error.message}`, "error");
    } finally {
        if (state.tonePreviewLoadingSpeakerId === speakerId) {
            state.tonePreviewLoadingSpeakerId = null;
        }
        renderSelectedCharacterDetail();
    }
}


async function previewCharacterToneComparison(speakerId = state.selectedCharacterId) {
    if (!speakerId || !state.analysis) {
        return;
    }

    captureCurrentCharacterProfiles();
    const character = (state.analysis.characters || []).find((entry) => entry.speaker_id === speakerId);
    if (!character || !(character.sample_lines || []).length) {
        addLog("샘플 미리 번역에 사용할 대사가 없습니다.", "warning");
        return;
    }

    const provider = dom.providerSelect.value || "gemini";
    const geminiAuthMode = getGeminiAuthMode();
    const openaiAuthMode = getOpenAIAuthMode();
    const profile = state.characterProfiles[speakerId] || {};
    const sampleLines = (character.sample_lines || []).slice(0, 5);
    const previewVariants = buildCharacterPreviewVariants(character);
    const cacheKey = buildCharacterPreviewCacheKey(character, previewVariants, sampleLines);
    const cachedPreview = state.tonePreviewByCharacter[speakerId];
    const canReuseCachedPreview = cachedPreview?.cacheKey === cacheKey
        && cachedPreview?.cacheable !== false
        && !cachedPreview?.variants?.some((variant) => variant.error);
    if (canReuseCachedPreview) {
        state.tonePreviewByCharacter[speakerId] = {
            ...cachedPreview,
            cacheHit: true,
        };
        addLog(`샘플 미리 번역 캐시 재사용: ${character.display_name || character.speaker_id}`, "info");
        renderSelectedCharacterDetail();
        return;
    }

    const commonPayload = {
        provider,
        gemini_auth_mode: geminiAuthMode,
        openai_auth_mode: openaiAuthMode,
        openai_oauth_command: normalizeOpenAIOAuthCommand(dom.openaiOAuthCommandInput.value),
        model_name: dom.modelInput.value.trim(),
        target_language: dom.targetLanguageInput.value.trim() || "ko",
        include_adult_content: dom.includeAdultCheckbox.checked,
        world_settings: collectWorldSettings(),
        vertex_settings: collectVertexSettings(),
        speaker_id: character.speaker_id,
        speaker_name: profile.display_name || character.display_name || character.speaker_id,
        sample_lines: sampleLines,
    };

    state.tonePreviewLoadingSpeakerId = speakerId;
    renderSelectedCharacterDetail();
    try {
        const previewResults = await Promise.allSettled(previewVariants.map(async (variant) => {
            const payload = {
                ...commonPayload,
                character_profiles: buildPreviewCharacterProfilesPayload(
                    speakerId,
                    commonPayload.speaker_name,
                    variant.profile,
                ),
            };
            if (supportsApiKey(provider, openaiAuthMode, geminiAuthMode)) {
                payload.api_key = dom.apiKeyInput.value.trim();
            }

            const response = await apiPost("/preview_character_tone", payload);
            return {
                variantId: variant.variantId,
                label: variant.label,
                description: variant.description,
                presetId: response.tone_preset_id || variant.profile.tone_preset_id || "custom",
                presetName: response.tone_preset_name || getCharacterTonePresetById(variant.profile.tone_preset_id || "custom").name,
                translations: response.translations || [],
                error: "",
            };
        }));

        const normalizedVariants = previewResults.map((result, index) => {
            if (result.status === "fulfilled") {
                return result.value;
            }
            const variant = previewVariants[index];
            return {
                variantId: variant.variantId,
                label: variant.label,
                description: variant.description,
                presetId: variant.profile.tone_preset_id || "custom",
                presetName: getCharacterTonePresetById(variant.profile.tone_preset_id || "custom").name,
                translations: [],
                error: result.reason?.message || "미리 번역 실패",
            };
        });
        const failedCount = normalizedVariants.filter((variant) => variant.error).length;

        state.tonePreviewByCharacter[speakerId] = {
            cacheKey,
            cacheable: failedCount === 0,
            cacheHit: false,
            provider,
            model_name: commonPayload.model_name,
            sample_lines: sampleLines,
            variants: normalizedVariants,
        };
        addLog(
            `샘플 미리 번역 완료: ${character.display_name || character.speaker_id} · ${normalizedVariants.length - failedCount}/${normalizedVariants.length}안 성공`,
            failedCount ? "warning" : "success",
        );
    } catch (error) {
        addLog(`샘플 미리 번역 실패: ${error.message}`, "error");
    } finally {
        if (state.tonePreviewLoadingSpeakerId === speakerId) {
            state.tonePreviewLoadingSpeakerId = null;
        }
        renderSelectedCharacterDetail();
    }
}


function handleCharacterGridClick(event) {
    const retranslateTrigger = event.target.closest("[data-action='retranslate-character']");
    if (retranslateTrigger) {
        retranslateSelectedCharacter(retranslateTrigger.dataset.speakerId || state.selectedCharacterId);
        return;
    }

    const previewTrigger = event.target.closest("[data-action='preview-character-tone']");
    if (previewTrigger) {
        previewCharacterToneComparison(previewTrigger.dataset.speakerId || state.selectedCharacterId);
        return;
    }

    const target = event.target.closest("[data-select-character]");
    if (!target) {
        return;
    }

    const speakerId = target.dataset.selectCharacter;
    if (!speakerId || speakerId === state.selectedCharacterId) {
        return;
    }

    captureCurrentCharacterProfiles();
    state.selectedCharacterId = speakerId;
    renderSelectedCharacterDetail();
    target.focus({ preventScroll: true });
}


function handleCharacterGridInput(event) {
    const filterField = event.target.closest("[data-role='character-filter']");
    if (filterField) {
        const viewState = captureCharacterGridViewState(filterField);
        state.characterFilter = filterField.value;
        renderCharacterGrid(viewState);
        return;
    }

    const fieldName = event.target.dataset.field;
    if (!fieldName || !state.selectedCharacterId) {
        return;
    }

    const currentProfile = state.characterProfiles[state.selectedCharacterId] || {};
    if (fieldName === "tone_preset_id") {
        const fallbackProfile = state.analysis?.default_character_profiles?.[state.selectedCharacterId] || {};
        state.characterProfiles[state.selectedCharacterId] = maybeApplyTonePresetSuggestion(
            event.target.value,
            currentProfile.tone_preset_id || "custom",
            currentProfile,
            fallbackProfile,
        );
        clearTonePreview(state.selectedCharacterId);
        renderSelectedCharacterDetail();
        return;
    }

    state.characterProfiles[state.selectedCharacterId] = {
        ...currentProfile,
        [fieldName]: event.target.value,
    };
    if (["tone", "notes", "role", "display_name"].includes(fieldName)) {
        clearTonePreview(state.selectedCharacterId);
    }
}


function handleCharacterGridChange(event) {
    const fieldName = event.target.dataset.field;
    if (!fieldName || !state.selectedCharacterId) {
        return;
    }
    if (fieldName === "tone_preset_id") {
        const currentProfile = state.characterProfiles[state.selectedCharacterId] || {};
        const fallbackProfile = state.analysis?.default_character_profiles?.[state.selectedCharacterId] || {};
        state.characterProfiles[state.selectedCharacterId] = maybeApplyTonePresetSuggestion(
            event.target.value,
            currentProfile.tone_preset_id || "custom",
            currentProfile,
            fallbackProfile,
        );
        clearTonePreview(state.selectedCharacterId);
        renderSelectedCharacterDetail();
        return;
    }
    captureCurrentCharacterProfiles();
}


async function prefillStartupPath() {
    try {
        const data = await apiGet("/get_startup_path");
        if (data.path) {
            dom.gamePathInput.value = data.path;
            addLog(`시작 인자로 받은 게임 경로를 불러왔습니다: ${data.path}`);
            await analyzeGame();
        }
    } catch {
        addLog("백엔드 시작 경로 자동 불러오기는 생략되었습니다.", "warning");
    }
}


function renderTranslationHint() {
    const rule = getTranslationRuleValue();
    const ruleLabel = getTranslationRuleLabel(rule);
    const totalFileCount = state.analysis?.files?.length || 0;
    const selectedFileCount = state.selectedFiles.size;
    const selectionHint = totalFileCount
        ? `선택 파일 ${selectedFileCount}/${totalFileCount}. `
        : "";
    if (dom.translateButton) {
        if (rule === "retranslate_existing") {
            dom.translateButton.textContent = "선택 파일 재번역";
        } else if (rule === "force_all") {
            dom.translateButton.textContent = "선택 파일 새로 통번역";
        } else {
            dom.translateButton.textContent = "선택 파일 미번역 번역";
        }
    }

    let ruleHint = "현재 범위에서 미번역 줄만 새로 번역합니다. 이미 게임에 연결된 번역과 워크벤치 출력은 유지합니다.";
    if (rule === "retranslate_existing") {
        ruleHint = "현재 범위에서 이미 번역된 줄만 다시 번역합니다. 캐릭터 재번역도 이 규칙으로 동작합니다.";
    } else if (rule === "force_all") {
        ruleHint = "현재 범위의 줄을 전부 새 번역 대상으로 잡습니다. 기존 번역도 다시 씁니다.";
    }
    if (usesOpenAIOAuth()) {
        dom.translationHint.textContent = `현재 규칙: ${ruleLabel}. ${selectionHint}${ruleHint} OpenAI OAuth 모드에서는 배치 상한을 기준으로 더 싼 모델과 청크 크기를 자동 선택하고, 완료된 파일은 즉시 Ren'Py 출력 경로에 반영합니다.`;
        return;
    }
    dom.translationHint.textContent = `현재 규칙: ${ruleLabel}. ${selectionHint}${ruleHint} Gemini/API 모드에서는 배치 상한과 글자수 budget을 함께 보고 긴 대사를 더 작은 청크로 자동 분할합니다.`;
}


function updateProviderUI() {
    const isOpenAI = dom.providerSelect.value === "openai";
    const useOauth = usesOpenAIOAuth();
    dom.openaiOAuthCommandInput.value = normalizeOpenAIOAuthCommand(dom.openaiOAuthCommandInput.value);
    if (!useOauth) {
        clearOpenAIOAuthPoll();
    }

    dom.openaiAuthField.classList.toggle("hidden", !isOpenAI);
    dom.apiKeyField.classList.toggle("hidden", isOpenAI && useOauth);
    dom.openaiOAuthPanel.classList.toggle("hidden", !isOpenAI || !useOauth);
    dom.apiKeyInput.disabled = isOpenAI && useOauth;
    dom.batchSizeInput.disabled = false;
    dom.apiDelayInput.disabled = useOauth;
    renderTranslationHint();

    if (useOauth) {
        dom.openaiOAuthStatus.textContent = dom.openaiOAuthStatus.textContent || "CLI 점검 대기 중입니다.";
    }
    renderTranslationPresetSummary();
}


function renderAdultQueue() {
    const queue = state.analysis?.adult_queue || [];
    if (!queue.length) {
        dom.adultQueue.className = "adult-queue empty-state";
        dom.adultQueue.textContent = "성인 큐가 아직 없습니다.";
        return;
    }

    dom.adultQueue.className = "adult-queue";
    dom.adultQueue.innerHTML = queue.map((item) => {
        const draftValue = getEditorDraftValue(item);
        const isDirty = draftValue.trim() !== getEditableDisplayText(item).trim();
        return `
            <article class="manual-edit-card${isDirty ? " is-dirty" : ""}">
                <div class="dialogue-row-header">
                    <div>
                        <strong>${escapeHtml(item.speaker_name || item.speaker_id || "Narration")}</strong>
                        <div class="helper-text">${escapeHtml(item.file_relative_path)}:${escapeHtml(item.line_number)} · ${escapeHtml(getTranslationStatusLabel(item.translation_status, item.translation_source))}</div>
                    </div>
                    <div class="pill-list compact">
                        <span class="pill subtle">${escapeHtml((item.adult_keywords || []).join(", ") || "adult queue")}</span>
                    </div>
                </div>
                <div class="editor-source-box">
                    <strong>원문</strong>
                    <p>${escapeHtml(item.source_text)}</p>
                </div>
                ${buildTranslationPreviewLines(item)}
                <label class="field">
                    <span>직접 번역</span>
                    <textarea data-role="adult-text" data-item-id="${escapeHtml(item.item_id)}" rows="6" placeholder="이 줄은 직접 번역해 바로 게임 출력에 반영할 수 있습니다.">${escapeHtml(draftValue)}</textarea>
                </label>
                <div class="editor-context-grid">
                    <div class="editor-source-box">
                        <strong>이전 문맥</strong>
                        <p>${escapeHtml((item.context_before || []).join("\n") || "없음")}</p>
                    </div>
                    <div class="editor-source-box">
                        <strong>다음 문맥</strong>
                        <p>${escapeHtml((item.context_after || []).join("\n") || "없음")}</p>
                    </div>
                </div>
                <div class="manual-edit-actions">
                    <button type="button" class="ghost-button mini-button" data-action="open-adult-in-editor" data-file-path="${escapeHtml(item.file_relative_path)}" data-item-id="${escapeHtml(item.item_id)}">편집 탭에서 열기</button>
                    <button type="button" class="secondary-button mini-button" data-action="save-adult-item" data-file-path="${escapeHtml(item.file_relative_path)}" data-item-id="${escapeHtml(item.item_id)}">이 줄 저장</button>
                </div>
            </article>
        `;
    }).join("");
}


function populateFromAnalysis(analysis, label, options = {}) {
    captureCurrentCharacterProfiles();
    state.analysis = analysis;
    clearTonePreview();
    const availableFilePaths = applyAnalysisFileSelection(analysis, options);
    state.characterProfiles = {
        ...(analysis.default_character_profiles || {}),
        ...state.characterProfiles,
    };
    state.characterFilter = "";
    const nextCharacters = analysis.characters || [];
    const firstPlayableCharacter = nextCharacters.find((character) => !isSystemCharacter(character));
    state.selectedCharacterId = nextCharacters.some((character) => character.speaker_id === state.selectedCharacterId)
        ? state.selectedCharacterId
        : (firstPlayableCharacter?.speaker_id || nextCharacters[0]?.speaker_id || null);
    syncIssueCandidateSelection(analysis.issue_candidates || []);
    syncAdultQueueSelection(analysis.adult_queue || []);
    state.editorDocument = null;
    state.editorSelectedItemId = null;
    if (!availableFilePaths.includes(state.editorFilePath)) {
        state.editorFilePath = "";
    }

    dom.analysisModeLabel.textContent = `${label} · ${analysis.analysis_mode}`;
    applyWorldSettings(analysis.default_world_settings || {}, false);
    applyPublishSettings(analysis.default_publish_settings || {}, false);
    renderSummary();
    renderWorldInference();
    renderPublishBaseline();
    renderDialoguePreview();
    renderFileTable();
    renderCharacterGrid();
    renderIssueCandidates();
    renderAdultQueue();
    renderDocumentEditor();
    renderTranslationHint();
}


function updateEditorDraftState(itemId) {
    if (!state.editorDocument) {
        return;
    }
    const item = getEditorItems().find((entry) => entry.item_id === itemId);
    const listButton = Array.from(dom.documentEditor.querySelectorAll("[data-action='select-editor-item']"))
        .find((entry) => entry.dataset.itemId === itemId);
    if (listButton && item) {
        listButton.classList.toggle("is-dirty", isEditorItemDirty(item));
    }
    dom.editorSummary.textContent = buildEditorSummaryText(state.editorDocument, getVisibleEditorItems().length);
}


function handleDocumentEditorInput(event) {
    const textField = event.target.closest("[data-role='editor-text']");
    if (!textField) {
        return;
    }
    const itemId = textField.dataset.itemId;
    const item = getEditorItems().find((entry) => entry.item_id === itemId);
    if (!item) {
        return;
    }
    if (textField.value === (item.editable_text || "")) {
        delete state.editorDrafts[itemId];
    } else {
        state.editorDrafts[itemId] = textField.value;
    }
    updateEditorDraftState(itemId);
}


async function handleDocumentEditorClick(event) {
    const selectButton = event.target.closest("[data-action='select-editor-item']");
    if (selectButton) {
        const scrollTop = dom.documentEditor.querySelector(".editor-list")?.scrollTop || 0;
        state.editorSelectedItemId = selectButton.dataset.itemId || null;
        renderDocumentEditor();
        const nextList = dom.documentEditor.querySelector(".editor-list");
        if (nextList) {
            nextList.scrollTop = scrollTop;
        }
        return;
    }

    const saveButton = event.target.closest("[data-action='save-editor-item']");
    if (!saveButton || !state.editorDocument) {
        return;
    }
    const itemId = saveButton.dataset.itemId || "";
    const item = getEditorItems().find((entry) => entry.item_id === itemId);
    if (!item) {
        return;
    }
    const text = getEditorDraftValue(item).trim();
    if (!text) {
        addLog("비어 있지 않은 번역문만 저장할 수 있습니다.", "warning");
        return;
    }
    await saveManualEdits(
        [
            {
                file_relative_path: item.file_relative_path,
                item_id: item.item_id,
                text,
            },
        ],
        {
            successMessage: "현재 줄 저장 완료:",
            reloadEditor: true,
            preferredFilePath: state.editorFilePath,
            selectedItemId: item.item_id,
            activateTabName: "editor",
        },
    );
}


async function saveLoadedEditorDocument() {
    if (!state.editorDocument) {
        addLog("먼저 편집할 파일을 불러오세요.", "warning");
        return;
    }
    const edits = getEditorItems()
        .filter((item) => isEditorItemDirty(item))
        .map((item) => ({
            file_relative_path: item.file_relative_path,
            item_id: item.item_id,
            text: getEditorDraftValue(item),
        }));
    if (!edits.length) {
        addLog("저장할 변경이 없습니다.", "warning");
        return;
    }
    await saveManualEdits(edits, {
        successMessage: `${state.editorFilePath} 저장 완료:`,
        reloadEditor: true,
        preferredFilePath: state.editorFilePath,
        selectedItemId: state.editorSelectedItemId,
        activateTabName: "editor",
    });
}


function handleAdultQueueInput(event) {
    const textField = event.target.closest("[data-role='adult-text']");
    if (!textField) {
        return;
    }
    const itemId = textField.dataset.itemId || "";
    const item = (state.analysis?.adult_queue || []).find((entry) => entry.item_id === itemId);
    if (!item) {
        return;
    }
    if (textField.value === getEditableDisplayText(item)) {
        delete state.editorDrafts[itemId];
    } else {
        state.editorDrafts[itemId] = textField.value;
    }
    textField.closest(".manual-edit-card")?.classList.toggle(
        "is-dirty",
        textField.value.trim() !== getEditableDisplayText(item).trim(),
    );
}


function handleAdultQueueChange(event) {
    const checkbox = event.target.closest("[data-role='adult-select']");
    if (!checkbox) {
        return;
    }
    const itemId = checkbox.dataset.itemId || "";
    if (!itemId) {
        return;
    }
    if (checkbox.checked) {
        state.selectedAdultQueueIds.add(itemId);
    } else {
        state.selectedAdultQueueIds.delete(itemId);
    }
    renderAdultQueue();
}


async function handleAdultQueueClick(event) {
    const openButton = event.target.closest("[data-action='open-adult-in-editor']");
    if (openButton) {
        const filePath = openButton.dataset.filePath || "";
        const itemId = openButton.dataset.itemId || "";
        if (!filePath) {
            return;
        }
        state.editorFilePath = filePath;
        if (dom.editorFileSelect) {
            dom.editorFileSelect.value = filePath;
        }
        activateTab("editor");
        await loadEditableDocument(filePath, {
            selectedItemId: itemId || state.editorSelectedItemId,
        });
        return;
    }

    const saveButton = event.target.closest("[data-action='save-adult-item']");
    if (!saveButton) {
        return;
    }
    const itemId = saveButton.dataset.itemId || "";
    const filePath = saveButton.dataset.filePath || "";
    const item = (state.analysis?.adult_queue || []).find((entry) => entry.item_id === itemId);
    if (!item || !filePath) {
        return;
    }
    const text = getEditorDraftValue(item).trim();
    if (!text) {
        addLog("비어 있지 않은 번역문만 저장할 수 있습니다.", "warning");
        return;
    }
    await saveManualEdits(
        [
            {
                file_relative_path: filePath,
                item_id: itemId,
                text,
            },
        ],
        {
            successMessage: "성인 큐 저장 완료:",
            reloadEditor: state.editorFilePath === filePath,
            preferredFilePath: state.editorFilePath || filePath,
            selectedItemId: state.editorFilePath === filePath ? itemId : state.editorSelectedItemId,
            activateTabName: "adult",
        },
    );
}


function handleIssueCandidateSearchInput() {
    state.issueCandidateSearchQuery = dom.issueCandidateSearchInput?.value || "";
    renderIssueCandidates();
}


function handleIssueCandidateQueueChange(event) {
    const checkbox = event.target.closest("[data-role='issue-select']");
    if (!checkbox) {
        return;
    }
    const itemId = checkbox.dataset.itemId || "";
    if (!itemId) {
        return;
    }
    if (checkbox.checked) {
        state.selectedIssueCandidateIds.add(itemId);
    } else {
        state.selectedIssueCandidateIds.delete(itemId);
    }
    renderIssueCandidates();
}


async function handleIssueCandidateQueueClick(event) {
    const openButton = event.target.closest("[data-action='open-issue-in-editor']");
    if (openButton) {
        const filePath = openButton.dataset.filePath || "";
        const itemId = openButton.dataset.itemId || "";
        if (!filePath) {
            return;
        }
        state.editorFilePath = filePath;
        if (dom.editorFileSelect) {
            dom.editorFileSelect.value = filePath;
        }
        activateTab("editor");
        await loadEditableDocument(filePath, {
            selectedItemId: itemId || state.editorSelectedItemId,
        });
        return;
    }

    const retranslateButton = event.target.closest("[data-action='retranslate-issue-item']");
    if (!retranslateButton) {
        return;
    }
    const itemId = retranslateButton.dataset.itemId || "";
    if (!itemId) {
        return;
    }
    await retranslateIssueCandidates([itemId]);
}


async function handleVertexCredentialsFileChange(event) {
    const file = event.target.files?.[0];
    if (!file) {
        return;
    }
    try {
        const rawText = await file.text();
        applyVertexCredentialsJson(rawText, `${file.name} 파일`);
        addLog(`Vertex 서비스 계정 JSON 로드 완료: ${file.name}`, "success");
    } catch (error) {
        setVertexCredentialsStatus(`서비스 계정 JSON 로드 실패: ${error.message}`);
        addLog(`Vertex 서비스 계정 JSON 로드 실패: ${error.message}`, "error");
    }
}


function renderApiKeyStorageStatus() {
    if (!dom.apiKeyStorageStatus) {
        return;
    }
    if (usesGeminiVertex()) {
        dom.apiKeyStorageStatus.textContent = "Vertex AI mode uses your GCP project plus ADC or a service account JSON instead of an API key.";
        return;
    }
    if (!supportsApiKey()) {
        dom.apiKeyStorageStatus.textContent = "Codex OAuth mode does not use API key storage.";
        return;
    }

    const label = getApiKeyStorageLabel();
    const savedKey = getStoredApiKey();
    const currentKey = dom.apiKeyInput.value.trim();
    if (!savedKey) {
        dom.apiKeyStorageStatus.textContent = `No saved ${label} for the current scope.`;
        return;
    }
    if (!currentKey) {
        dom.apiKeyStorageStatus.textContent = `A saved ${label} is available. Click load to restore it into the input field.`;
        return;
    }
    if (savedKey === currentKey) {
        dom.apiKeyStorageStatus.textContent = `The current ${label} matches the saved value for this scope.`;
        return;
    }
    dom.apiKeyStorageStatus.textContent = `The current ${label} differs from the saved value for this scope.`;
}


function updateProviderUI() {
    const isOpenAI = dom.providerSelect.value === "openai";
    const isGemini = dom.providerSelect.value === "gemini";
    const useOauth = usesOpenAIOAuth();
    const useVertex = usesGeminiVertex();
    const apiKeySupported = supportsApiKey(dom.providerSelect.value, getOpenAIAuthMode(), getGeminiAuthMode());
    dom.openaiOAuthCommandInput.value = normalizeOpenAIOAuthCommand(dom.openaiOAuthCommandInput.value);
    if (!useOauth) {
        clearOpenAIOAuthPoll();
    }

    dom.geminiAuthField?.classList.toggle("hidden", !isGemini);
    dom.openaiAuthField.classList.toggle("hidden", !isOpenAI);
    dom.apiKeyField.classList.toggle("hidden", !apiKeySupported);
    dom.geminiVertexPanel?.classList.toggle("hidden", !isGemini || !useVertex);
    dom.openaiOAuthPanel.classList.toggle("hidden", !isOpenAI || !useOauth);
    dom.apiKeyInput.disabled = !apiKeySupported;
    dom.batchSizeInput.disabled = false;
    dom.apiDelayInput.disabled = useOauth;
    renderApiKeyStorageStatus();
    renderTranslationHint();

    if (useOauth) {
        dom.openaiOAuthStatus.textContent = dom.openaiOAuthStatus.textContent || "CLI status check pending.";
    }
    renderTranslationPresetSummary();
}


function init() {
    applyTranslationPreset(DEFAULT_TRANSLATION_PRESET_ID, { log: false });
    syncStoredApiKeyForCurrentScope();
    setVertexCredentialsStatus("경로, JSON 파일 로드, JSON 붙여넣기 중 하나만 사용해도 됩니다. JSON에 project_id가 있으면 프로젝트 ID를 자동으로 채웁니다.");
    setGlossaryRows([]);
    setStyleOverrideRows([]);
    renderSummary();
    renderUploadList();
    renderWorldInference();
    renderPublishBaseline();
    renderDialoguePreview();
    renderFileTable();
    renderCharacterGrid();
    renderIssueCandidates();
    renderAdultQueue();
    renderResults();
    activateTab("overview");

    dom.translationPresetGrid?.addEventListener("click", handleTranslationPresetClick);
    dom.providerSelect.addEventListener("change", () => {
        updateModelSuggestions();
        syncStoredApiKeyForCurrentScope();
        syncTranslationPresetSelection();
    });
    dom.geminiAuthModeSelect?.addEventListener("change", () => {
        updateModelSuggestions();
        syncStoredApiKeyForCurrentScope();
        syncTranslationPresetSelection();
    });
    dom.loadVertexCredentialsFileButton?.addEventListener("click", () => dom.vertexCredentialsFileInput?.click());
    dom.clearVertexCredentialsButton?.addEventListener("click", clearVertexCredentialsJson);
    dom.vertexCredentialsFileInput?.addEventListener("change", (event) => {
        handleVertexCredentialsFileChange(event).catch(() => {});
    });
    dom.vertexCredentialsJsonInput?.addEventListener("change", () => {
        const rawText = dom.vertexCredentialsJsonInput.value.trim();
        if (!rawText) {
            setVertexCredentialsStatus("서비스 계정 JSON 입력이 비어 있습니다.");
            return;
        }
        try {
            applyVertexCredentialsJson(rawText, "붙여넣기");
        } catch (error) {
            setVertexCredentialsStatus(`서비스 계정 JSON 파싱 실패: ${error.message}`);
            addLog(`Vertex 서비스 계정 JSON 파싱 실패: ${error.message}`, "error");
        }
    });
    dom.openaiAuthModeSelect.addEventListener("change", () => {
        updateModelSuggestions();
        syncStoredApiKeyForCurrentScope();
        syncTranslationPresetSelection();
    });
    dom.apiKeyInput.addEventListener("input", () => handleApiKeyMutation({ rerender: true }));
    dom.saveApiKeyButton?.addEventListener("click", saveCurrentApiKeyToStorage);
    dom.loadApiKeyButton?.addEventListener("click", () => loadStoredApiKeyForCurrentScope({ rerender: true }));
    dom.clearApiKeyButton?.addEventListener("click", clearStoredApiKeyForCurrentScope);
    [dom.modelInput, dom.batchSizeInput, dom.apiDelayInput].forEach((element) => {
        element.addEventListener("input", syncTranslationPresetSelection);
        element.addEventListener("change", syncTranslationPresetSelection);
    });
    dom.translationRuleSelect?.addEventListener("change", renderTranslationHint);
    dom.setupOpenAIOAuthButton.addEventListener("click", setupOpenAIOAuth);
    dom.checkOpenAIOAuthButton.addEventListener("click", checkOpenAIOAuthStatus);
    dom.pickExeButton.addEventListener("click", pickExeAndAnalyze);
    dom.generateTemplateButton.addEventListener("click", generateTemplate);
    dom.analyzeGameButton.addEventListener("click", analyzeGame);
    dom.repairOutputsButton?.addEventListener("click", repairTranslationOutputs);
    dom.uploadInput.addEventListener("change", handleUploadChange);
    dom.analyzeUploadsButton.addEventListener("click", analyzeUploads);
    dom.clearUploadsButton.addEventListener("click", () => {
        state.uploadedFiles = [];
        renderUploadList();
        addLog("업로드 목록 초기화");
    });
    dom.addGlossaryRowButton.addEventListener("click", () => addGlossaryRow());
    dom.glossaryTable.addEventListener("click", handleGlossaryClick);
    dom.addStyleOverrideRowButton.addEventListener("click", () => addStyleOverrideRow());
    dom.styleOverrideTable.addEventListener("click", handleStyleOverrideClick);
    dom.applyFontPresetButton.addEventListener("click", handleFontPresetApply);
    dom.applyPublishFontsButton?.addEventListener("click", () => {
        applyPublishFontsOnly().catch(() => {});
    });
    [
        dom.dialogueFontSelect,
        dom.nameFontSelect,
        dom.optionsFontSelect,
        dom.interfaceFontSelect,
        dom.systemFontSelect,
        dom.glyphFontSelect,
        dom.dialogueScaleInput,
        dom.nameScaleInput,
        dom.optionsScaleInput,
        dom.interfaceScaleInput,
    ].forEach((element) => {
        element.addEventListener("input", handlePublishControlInput);
        element.addEventListener("change", handlePublishControlInput);
    });
    dom.fileTable.addEventListener("change", handleFileSelection);
    dom.characterGrid.addEventListener("click", handleCharacterGridClick);
    dom.characterGrid.addEventListener("input", handleCharacterGridInput);
    dom.characterGrid.addEventListener("change", handleCharacterGridChange);
    dom.translateButton.addEventListener("click", translateSelection);
    dom.attachProgressButton?.addEventListener("click", attachTranslationProgress);
    dom.issueCandidateSearchInput?.addEventListener("input", handleIssueCandidateSearchInput);
    dom.selectVisibleIssueCandidatesButton?.addEventListener("click", () => {
        getVisibleIssueCandidates().forEach((item) => state.selectedIssueCandidateIds.add(item.item_id));
        renderIssueCandidates();
    });
    dom.clearIssueCandidateSelectionButton?.addEventListener("click", () => {
        state.selectedIssueCandidateIds.clear();
        renderIssueCandidates();
    });
    dom.retranslateIssueCandidatesButton?.addEventListener("click", () => {
        retranslateIssueCandidates().catch(() => {});
    });
    dom.selectVisibleAdultQueueButton?.addEventListener("click", () => {
        getAdultQueueItems().forEach((item) => state.selectedAdultQueueIds.add(item.item_id));
        renderAdultQueue();
    });
    dom.clearAdultQueueSelectionButton?.addEventListener("click", () => {
        state.selectedAdultQueueIds.clear();
        renderAdultQueue();
    });
    dom.translateAdultQueueButton?.addEventListener("click", () => {
        translateSelectedAdultQueue().catch(() => {});
    });
    dom.saveProfileButton.addEventListener("click", saveProfile);
    dom.loadProfileButton.addEventListener("click", () => dom.profileFileInput.click());
    dom.profileFileInput.addEventListener("change", handleProfileLoad);
    dom.tabButtons.forEach((button) => {
        button.addEventListener("click", () => activateTab(button.dataset.tab));
    });

    prefillStartupPath();
}


init();

if (dom.fontBrowserSampleTextInput && !dom.fontBrowserSampleTextInput.value.trim()) {
    dom.fontBrowserSampleTextInput.value = DEFAULT_FONT_BROWSER_SAMPLE_TEXT;
}
if (dom.fontBrowserTargetSelect?.value) {
    state.fontBrowserTarget = dom.fontBrowserTargetSelect.value;
}
dom.loadSystemFontsButton?.addEventListener("click", () => {
    loadSystemFonts(true).catch(() => {});
});
dom.fontBrowserTargetSelect?.addEventListener("change", () => {
    state.fontBrowserTarget = dom.fontBrowserTargetSelect.value || "dialogue_font";
    state.fontBrowserPage = 0;
    renderSystemFontGallery();
});
dom.fontBrowserSearchInput?.addEventListener("input", () => {
    state.fontBrowserQuery = dom.fontBrowserSearchInput.value.trim();
    state.fontBrowserPage = 0;
    renderSystemFontGallery();
});
dom.fontBrowserSearchInput?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") {
        return;
    }
    event.preventDefault();
    state.fontBrowserQuery = dom.fontBrowserSearchInput.value.trim();
    applyFirstFilteredSystemFont();
});
dom.applyFirstFilteredFontButton?.addEventListener("click", () => {
    state.fontBrowserQuery = dom.fontBrowserSearchInput?.value.trim() || "";
    applyFirstFilteredSystemFont();
});
dom.fontBrowserSampleTextInput?.addEventListener("input", () => {
    state.fontBrowserPage = 0;
    renderCurrentFontPreviewGrid();
    renderSystemFontGallery();
});
dom.fontBrowserPrevButton?.addEventListener("click", () => {
    state.fontBrowserPage = Math.max(0, (state.fontBrowserPage || 0) - 1);
    renderSystemFontGallery();
});
dom.fontBrowserNextButton?.addEventListener("click", () => {
    state.fontBrowserPage = Math.max(0, (state.fontBrowserPage || 0) + 1);
    renderSystemFontGallery();
});
dom.currentFontPreviewGrid?.addEventListener("input", handleCurrentFontPreviewGridInput);
dom.currentFontPreviewGrid?.addEventListener("change", handleCurrentFontPreviewGridInput);
dom.systemFontGallery?.addEventListener("click", handleSystemFontGalleryClick);
loadSystemFonts(false).catch(() => {});

dom.editorFileSelect?.addEventListener("change", () => {
    state.editorFilePath = dom.editorFileSelect.value || "";
});
dom.editorStatusFilter?.addEventListener("change", () => {
    state.editorStatusFilter = dom.editorStatusFilter.value || "all";
    renderDocumentEditor();
});
dom.editorSearchInput?.addEventListener("input", () => {
    state.editorSearchQuery = dom.editorSearchInput.value || "";
    renderDocumentEditor();
});
dom.loadEditorButton?.addEventListener("click", async () => {
    activateTab("editor");
    try {
        await loadEditableDocument();
    } catch {
        // loadEditableDocument already reports the failure.
    }
});
dom.saveEditorButton?.addEventListener("click", () => {
    saveLoadedEditorDocument().catch(() => {});
});
dom.documentEditor?.addEventListener("input", handleDocumentEditorInput);
dom.documentEditor?.addEventListener("click", (event) => {
    handleDocumentEditorClick(event).catch(() => {});
});
dom.adultQueue?.addEventListener("input", handleAdultQueueInput);
dom.adultQueue?.addEventListener("change", handleAdultQueueChange);
dom.adultQueue?.addEventListener("click", (event) => {
    handleAdultQueueClick(event).catch(() => {});
});
dom.issueCandidateQueue?.addEventListener("change", handleIssueCandidateQueueChange);
dom.issueCandidateQueue?.addEventListener("click", (event) => {
    handleIssueCandidateQueueClick(event).catch(() => {});
});
renderDocumentEditor();


// ─── 대사 검색 기능 ────────────────────────────────────────────────
async function runDialogueSearch() {
    const query = document.getElementById("dialogueSearchInput")?.value?.trim();
    const limitEl = document.getElementById("dialogueSearchLimit");
    const maxResults = parseInt(limitEl?.value || "50", 10);
    const statusEl = document.getElementById("dialogueSearchStatus");
    const resultsEl = document.getElementById("dialogueSearchResults");
    const gamePath = dom.gamePathInput?.value?.trim();

    if (!query) {
        if (statusEl) { statusEl.textContent = "검색어를 입력하세요."; }
        return;
    }
    if (!gamePath) {
        if (statusEl) { statusEl.textContent = "먼저 게임 EXE 경로를 입력하고 분석을 실행하세요."; }
        return;
    }

    if (statusEl) { statusEl.textContent = "검색 중..."; }
    if (resultsEl) {
        resultsEl.className = "document-editor empty-state";
        resultsEl.textContent = "검색 중...";
    }

    try {
        const data = await apiPost("/search_dialogue", {
            query,
            game_exe_path: gamePath,
            max_results: maxResults,
        });

        if (statusEl) {
            statusEl.textContent = `결과 ${data.result_count}건 (파일 ${data.searched_files}개 검색됨)`;
        }

        if (!data.results || data.results.length === 0) {
            if (resultsEl) {
                resultsEl.className = "document-editor empty-state";
                resultsEl.textContent = `"${query}"에 해당하는 번역 대사를 찾지 못했습니다.`;
            }
            return;
        }

        const rows = data.results.map((item) => `
            <tr>
                <td class="search-result-file">${escapeHtml(item.file)}</td>
                <td class="search-result-lang"><span class="pill subtle">${escapeHtml(item.lang)}</span></td>
                <td class="search-result-line">${escapeHtml(String(item.line))}</td>
                <td class="search-result-en">${escapeHtml(item.en)}</td>
                <td class="search-result-ko">${escapeHtml(item.ko || "(번역 없음)")}</td>
            </tr>
        `).join("");

        if (resultsEl) {
            resultsEl.className = "document-editor";
            resultsEl.innerHTML = `
                <div style="overflow-x:auto">
                    <table class="search-result-table">
                        <thead>
                            <tr>
                                <th>파일</th>
                                <th>언어팩</th>
                                <th>줄</th>
                                <th>영어 원문</th>
                                <th>한국어 번역</th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>
            `;
        }
    } catch (error) {
        if (statusEl) { statusEl.textContent = `검색 실패: ${error.message}`; }
        if (resultsEl) {
            resultsEl.className = "document-editor empty-state";
            resultsEl.textContent = `검색 중 오류가 발생했습니다: ${error.message}`;
        }
    }
}

document.getElementById("dialogueSearchButton")?.addEventListener("click", () => {
    runDialogueSearch().catch(() => {});
});
document.getElementById("dialogueSearchInput")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        runDialogueSearch().catch(() => {});
    }
});
