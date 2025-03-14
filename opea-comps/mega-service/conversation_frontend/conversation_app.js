/**
 * Japanese Conversation Partner - Frontend Application
 */

// API endpoints
const API_BASE_URL = '';  // Empty for same origin
const API_ENDPOINTS = {
    startConversation: `${API_BASE_URL}/v1/start_conversation`,
    continueConversation: `${API_BASE_URL}/v1/continue_conversation`,
    getFeedback: `${API_BASE_URL}/v1/get_feedback`,
    speechToText: `${API_BASE_URL}/v1/speech_to_text`,
    scenarios: `${API_BASE_URL}/v1/scenarios`,
    textToSpeech: `${API_BASE_URL}/v1/text_to_speech`,
    getSuggestion: `${API_BASE_URL}/v1/get_suggestion`,
};

// Application state
const appState = {
    currentView: 'setup', // 'setup' or 'conversation'
    conversationId: null,
    scenario: 'restaurant',
    proficiency: 'beginner',
    model: 'llama3', // Always use llama3 model
    messages: [],
    recording: false,
    mediaRecorder: null,
    audioChunks: [],
    studentId: localStorage.getItem('studentId') || generateId(),
    translationMode: true,
};

// DOM Elements
const elements = {
    setupView: document.getElementById('setup-view'),
    conversationView: document.getElementById('conversation-view'),
    scenarioTitle: document.getElementById('scenario-title'),
    proficiencyBadge: document.getElementById('proficiency-badge'),
    chatMessages: document.getElementById('chat-messages'),
    userInput: document.getElementById('user-input'),
    sendBtn: document.getElementById('send-btn'),
    speechBtn: document.getElementById('speech-btn'),
    newConversationBtn: document.getElementById('new-conversation-btn'),
    startConversationBtn: document.getElementById('start-conversation-btn'),
    scenarioCards: document.querySelectorAll('.scenario-card'),
    proficiencyButtons: document.querySelectorAll('[data-proficiency]'),
    feedbackContainer: document.getElementById('feedback-container'),
    conversationSummary: document.getElementById('conversation-summary'),
    summaryContent: document.getElementById('summary-content'),
    translationMode: document.getElementById('translation-mode'),
    // Recording modal elements
    recordingModal: new bootstrap.Modal(document.getElementById('recordingModal')),
    recordBtn: document.getElementById('record-btn'),
    recordingStatus: document.getElementById('recording-status'),
    recordingResult: document.getElementById('recording-result'),
    recognizedText: document.getElementById('recognized-text'),
    useRecordingBtn: document.getElementById('use-recording'),
    // Feedback tabs
    grammarTab: document.getElementById('grammar'),
    vocabularyTab: document.getElementById('vocabulary'),
    expressionTab: document.getElementById('expression'),
    overallTab: document.getElementById('overall'),
    // New elements for response suggestions
    helpBtn: document.getElementById('help-btn'),
    responseSuggestion: document.getElementById('response-suggestion'),
    closeSuggestion: document.getElementById('close-suggestion'),
    suggestionJapanese: document.getElementById('suggestion-japanese'),
    suggestionTransliteration: document.getElementById('suggestion-transliteration'),
    suggestionAudioContainer: document.getElementById('suggestion-audio-container'),
    useSuggestion: document.getElementById('use-suggestion')
};

// Initialize the application
function initApp() {
    // Save student ID to localStorage
    localStorage.setItem('studentId', appState.studentId);
    
    // Check if any DOM elements are missing and handle gracefully
    validateDOMElements();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load scenarios from API
    loadScenarios();
}

// Validate DOM elements to ensure we handle missing elements gracefully
function validateDOMElements() {
    // Log warning for any missing critical elements
    const criticalElements = [
        'setupView', 'conversationView', 'scenarioTitle', 'proficiencyBadge',
        'chatMessages', 'userInput', 'sendBtn', 'startConversationBtn'
    ];
    
    for (const elementKey of criticalElements) {
        if (!elements[elementKey]) {
            console.warn(`Critical DOM element missing: ${elementKey}`);
        }
    }
    
    // Model selector is no longer used - ensure it's removed from any code that might reference it
    if (elements.modelSelector) {
        console.warn('Model selector element found but not expected');
    }
}

// Set up event listeners
function setupEventListeners() {
    // Setup view events
    elements.scenarioCards.forEach(card => {
        card.addEventListener('click', () => selectScenario(card.dataset.scenario));
    });
    
    elements.proficiencyButtons.forEach(button => {
        button.addEventListener('click', () => selectProficiency(button.dataset.proficiency));
    });
    
    elements.startConversationBtn.addEventListener('click', startConversation);
    elements.newConversationBtn.addEventListener('click', showSetupView);
    
    // Conversation view events
    elements.userInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendUserMessage();
        }
    });
    
    elements.sendBtn.addEventListener('click', sendUserMessage);
    elements.speechBtn.addEventListener('click', showRecordingModal);
    
    // Recording modal events
    elements.recordBtn.addEventListener('click', toggleRecording);
    elements.useRecordingBtn.addEventListener('click', useRecordedText);
    
    // New event listeners for help button and suggestion UI
    elements.helpBtn.addEventListener('click', getResponseSuggestion);
    elements.closeSuggestion.addEventListener('click', hideSuggestion);
    elements.useSuggestion.addEventListener('click', useResponseSuggestion);
}

// Load scenarios from API
async function loadScenarios() {
    try {
        const response = await axios.get(API_ENDPOINTS.scenarios);
        // We already have static scenarios in HTML, but we could update them here if needed
    } catch (error) {
        console.error('Failed to load scenarios:', error);
    }
}

// Select a scenario
function selectScenario(scenario) {
    appState.scenario = scenario;
    
    // Update UI
    elements.scenarioCards.forEach(card => {
        if (card.dataset.scenario === scenario) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });
}

// Select proficiency level
function selectProficiency(proficiency) {
    appState.proficiency = proficiency;
    
    // Update UI
    elements.proficiencyButtons.forEach(button => {
        if (button.dataset.proficiency === proficiency) {
            button.classList.add('active');
            button.classList.remove('btn-outline-primary');
            button.classList.add('btn-primary');
        } else {
            button.classList.remove('active');
            button.classList.add('btn-outline-primary');
            button.classList.remove('btn-primary');
        }
    });
}

// Start a new conversation
async function startConversation() {
    try {
        // Update UI to show loading state
        elements.startConversationBtn.disabled = true;
        elements.startConversationBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Starting...';
        
        // Log request parameters - always use llama3 as the model regardless of appState
        const requestParams = {
            scenario: appState.scenario,
            proficiency: appState.proficiency,
            student_id: appState.studentId,
            model: 'llama3' // Always use llama3 model, hardcoded here for certainty
        };
        console.log("Starting conversation with params:", requestParams);
        
        // Send request to start conversation
        const response = await axios.post(API_ENDPOINTS.startConversation, requestParams);
        console.log("Server response:", response.data);
        
        // Verify response format
        if (!response.data || !response.data.conversation_id) {
            throw new Error("Invalid server response: missing conversation_id");
        }
        
        // Update state with conversation data
        appState.conversationId = response.data.conversation_id;
        appState.messages = [];
        
        // Handle first message
        if (!response.data.message) {
            console.warn("Server response missing message property");
        } else {
            // Try to display the message
            try {
                addMessage('agent', response.data.message);
            } catch (messageError) {
                console.error("Error adding initial message:", messageError);
                // Fallback to simple display if addMessage fails
                displayFallbackMessage(response.data.message);
            }
        }
        
        // Update UI elements
        elements.scenarioTitle.textContent = getScenarioTitle(appState.scenario);
        elements.proficiencyBadge.textContent = capitalize(appState.proficiency);
        
        // Show conversation view
        showConversationView();
    } catch (error) {
        console.error('Failed to start conversation:', error);
        
        // Generate helpful error message
        let errorMsg = 'Failed to start conversation';
        
        if (error.response) {
            // Server returned error response
            console.error('Response status:', error.response.status);
            console.error('Response data:', error.response.data);
            
            errorMsg += ` (Server error ${error.response.status})`;
            if (error.response.data && error.response.data.error) {
                errorMsg += `: ${error.response.data.error}`;
            }
        } else if (error.request) {
            // Request was made but no response
            console.error('No response received:', error.request);
            errorMsg += ': No response from server. Please check your connection.';
        } else {
            // Error in request setup
            console.error('Request error:', error.message);
            errorMsg += `: ${error.message}`;
        }
        
        // Show error to user
        alert(errorMsg);
    } finally {
        // Reset button state
        elements.startConversationBtn.disabled = false;
        elements.startConversationBtn.innerHTML = '<i class="bi bi-chat-left-text me-2"></i> Start Conversation';
    }
}

// Helper function for fallback message display
function displayFallbackMessage(message) {
    // Extract content from message object if needed
    let content = "";
    if (typeof message === 'string') {
        content = message;
    } else if (message && typeof message === 'object') {
        if (message.content) {
            content = String(message.content);
        } else {
            try {
                content = JSON.stringify(message);
            } catch (e) {
                content = "Message could not be displayed";
            }
        }
    }
    
    // Create simple message element
    const messageEl = document.createElement('div');
    messageEl.className = 'message agent-message';
    
    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    contentEl.textContent = content;
    
    messageEl.appendChild(contentEl);
    elements.chatMessages.appendChild(messageEl);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// Send user message
async function sendUserMessage() {
    const userText = elements.userInput.value.trim();
    if (!userText) return;
    
    // Check if input is in Japanese
    const isJapaneseInput = containsJapaneseCharacters(userText);
    
    try {
        // Add user message to UI
        addMessage('user', userText);
        
        // Clear input
        elements.userInput.value = '';
        
        // Disable input while waiting for response
        elements.userInput.disabled = true;
        elements.sendBtn.disabled = true;
        
        // Create loading message for better user experience
        const loadingEl = document.createElement('div');
        loadingEl.className = 'message agent-message loading-message';
        loadingEl.innerHTML = `
            <div class="message-content">
                <div class="d-flex align-items-center">
                    <div class="spinner-border spinner-border-sm text-secondary me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <span>${isJapaneseInput ? '回答を生成中です...' : 'Generating response...'}</span>
                </div>
            </div>
        `;
        elements.chatMessages.appendChild(loadingEl);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        
        // Prepare request data
        const requestData = {
            conversation_id: appState.conversationId,
            message: userText,
            // Only run analysis if user is explicitly asking for feedback or if this is part of training
            run_analysis: userText.toLowerCase().includes('feedback') || userText.toLowerCase().includes('分析')
        };
        
        // If translation mode is on and input is not in Japanese, add translation hint
        if (elements.translationMode.checked && !isJapaneseInput) {
            requestData.translate_input = true;
        }
        
        console.log("Sending request to continue conversation:", requestData);
        
        // Create AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 20000); // 20 second timeout
        
        try {
            // Send request to continue conversation with timeout handling
            const response = await axios.post(API_ENDPOINTS.continueConversation, requestData, {
                signal: controller.signal
            });
            
            // Clear timeout if request completes successfully
            clearTimeout(timeoutId);
            
            console.log("Received response:", response.data);
            
            // Remove loading message
            elements.chatMessages.removeChild(loadingEl);
            
            // Add agent response to UI
            addMessage('agent', response.data.message);
            
            // Show feedback if available and requested
            if (response.data.feedback && !response.data.feedback.error && !response.data.feedback.analysis_skipped) {
                showFeedback(response.data.feedback);
            }
        } catch (requestError) {
            // Clear timeout
            clearTimeout(timeoutId);
            
            // Remove loading message
            if (loadingEl.parentNode === elements.chatMessages) {
                elements.chatMessages.removeChild(loadingEl);
            }
            
            // If abort error (timeout), show appropriate message
            if (requestError.name === 'AbortError' || requestError.message.includes('timeout')) {
                console.error('Request timed out:', requestError);
                
                // Add a fallback message - for Japanese, provide a standard response
                if (isJapaneseInput) {
                    const fallbackResponses = {
                        'restaurant': 'すみません、少々お待ちください。 (Sumimasen, shoushou omachi kudasai.)',
                        'shopping': 'かしこまりました。少々お待ちください。 (Kashikomarimashita. Shoushou omachi kudasai.)',
                        'directions': 'すみません、もう一度言っていただけますか？ (Sumimasen, mou ichido itte itadakemasu ka?)',
                        'interview': 'なるほど、わかりました。 (Naruhodo, wakarimashita.)'
                    };
                    
                    // Use scenario-appropriate fallback or default
                    const fallbackResponse = fallbackResponses[appState.scenario] || 
                        'すみません、よく理解できませんでした。もう一度言っていただけますか？ (Sumimasen, yoku rikai dekimasen deshita. Mou ichido itte itadakemasu ka?)';
                    
                    addMessage('agent', fallbackResponse);
                } else {
                    // For non-Japanese input, show a generic error message
                    addMessage('agent', 'Sorry, the response took too long. Please try again with a simpler message.');
                }
            } else {
                // For other errors, rethrow to be handled by the outer catch
                throw requestError;
            }
        }
    } catch (error) {
        console.error('Failed to send message:', error);
        if (error.response) {
            console.error('Error response:', error.response.data);
        }
        alert('Failed to send message. Please try again.');
    } finally {
        // Re-enable input
        elements.userInput.disabled = false;
        elements.sendBtn.disabled = false;
        elements.userInput.focus();
    }
}

// Show recording modal
function showRecordingModal() {
    // Reset recording state
    appState.recording = false;
    appState.audioChunks = [];
    elements.recordBtn.textContent = 'Start Recording';
    elements.recordBtn.classList.remove('recording');
    elements.recordingStatus.textContent = 'Click to start recording';
    elements.recordingResult.style.display = 'none';
    elements.useRecordingBtn.disabled = true;
    
    // Show modal
    elements.recordingModal.show();
}

// Toggle recording state
async function toggleRecording() {
    if (appState.recording) {
        // Stop recording
        if (appState.mediaRecorder && appState.mediaRecorder.state !== 'inactive') {
            appState.mediaRecorder.stop();
        }
        elements.recordBtn.textContent = 'Start Recording';
        elements.recordBtn.classList.remove('recording');
        elements.recordingStatus.textContent = 'Processing...';
    } else {
        // Start recording
        try {
            // First, check if the browser supports getUserMedia
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                elements.recordingStatus.textContent = 'Audio recording not supported in this browser. Please try Chrome or Firefox.';
                return;
            }
            
            // Request microphone access with more detailed constraints
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Create audio context to verify audio is being received
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            source.connect(analyser);
            
            // Set up media recorder with explicit MIME type preference
            let options = {};
            // Order matters here - preferring WebM with opus codec which is widely supported
            const mimeTypes = [
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/ogg;codecs=opus',
                'audio/wav',
                'audio/mp4'
            ];
            
            // Find the first supported MIME type
            for (const mimeType of mimeTypes) {
                if (MediaRecorder.isTypeSupported(mimeType)) {
                    options = { mimeType };
                    console.log(`Using supported MIME type: ${mimeType}`);
                    break;
                }
            }
            
            try {
                appState.mediaRecorder = new MediaRecorder(stream, options);
                console.log(`MediaRecorder initialized with options:`, options);
            } catch (e) {
                console.error('MediaRecorder initialization failed:', e);
                appState.mediaRecorder = new MediaRecorder(stream);
                console.log('Using default MediaRecorder settings');
            }
            
            appState.audioChunks = [];
            
            // Update UI to show recording has started
            elements.recordingStatus.textContent = 'Recording... (speak now)';
            elements.recordBtn.textContent = 'Stop Recording';
            elements.recordBtn.classList.add('recording');
            
            // Add visual indicator that microphone is active
            const levelIndicator = document.createElement('div');
            levelIndicator.className = 'level-indicator';
            elements.recordingStatus.appendChild(levelIndicator);
            
            // Event handler for when audio data becomes available
            appState.mediaRecorder.addEventListener('dataavailable', event => {
                if (event.data.size > 0) {
                    appState.audioChunks.push(event.data);
                    console.log('Audio chunk received, size:', event.data.size);
                }
            });
            
            // Event handler for when recording stops
            appState.mediaRecorder.addEventListener('stop', async () => {
                // Remove level indicator
                const indicator = elements.recordingStatus.querySelector('.level-indicator');
                if (indicator) elements.recordingStatus.removeChild(indicator);
                
                elements.recordingStatus.textContent = 'Processing audio...';
                
                // Convert audio chunks to blob
                if (appState.audioChunks.length === 0) {
                    elements.recordingStatus.textContent = 'No audio recorded. Please try again and speak clearly.';
                    return;
                }
                
                const audioBlob = new Blob(appState.audioChunks);
                console.log('Audio blob created, size:', audioBlob.size, 'type:', audioBlob.type);
                
                // If the audio blob is too small, it might not contain any actual speech
                if (audioBlob.size < 1000) {
                    elements.recordingStatus.textContent = 'Recording too short or no audio detected. Please try again and speak clearly.';
                    return;
                }
                
                // Create audio element to verify recording
                const audioURL = URL.createObjectURL(audioBlob);
                const audio = document.createElement('audio');
                audio.controls = true;
                audio.src = audioURL;
                
                // Clear any previous audio preview
                const prevAudio = elements.recordingResult.querySelector('audio');
                if (prevAudio) elements.recordingResult.removeChild(prevAudio);
                
                // Add audio preview
                elements.recordingResult.prepend(audio);
                elements.recordingResult.style.display = 'block';
                
                // Add debug information
                const debugInfo = document.getElementById('debugInfo');
                if (debugInfo) {
                    debugInfo.style.display = 'block';
                    debugInfo.innerHTML = `
                        <p>Audio Blob Type: ${audioBlob.type}</p>
                        <p>Audio Blob Size: ${(audioBlob.size / 1024).toFixed(2)} KB</p>
                    `;
                }
                
                // Send audio to server for speech recognition
                try {
                    const formData = new FormData();
                    
                    // Get the audio type and set appropriate extension
                    const audioType = audioBlob.type || 'audio/webm';
                    console.log(`Audio type for upload: ${audioType}`);
                    
                    let fileExtension = 'webm'; // Default to webm
                    if (audioType.includes('webm')) {
                        fileExtension = 'webm';
                    } else if (audioType.includes('wav')) {
                        fileExtension = 'wav';
                    } else if (audioType.includes('ogg')) {
                        fileExtension = 'ogg';
                    } else if (audioType.includes('mp4') || audioType.includes('mp3')) {
                        fileExtension = 'mp3';
                    }
                    
                    console.log(`Using file extension: ${fileExtension} for audio type: ${audioType}`);
                    
                    // Append browser and platform info to help with debugging
                    if (debugInfo) {
                        debugInfo.innerHTML += `
                            <p>Browser: ${navigator.userAgent}</p>
                            <p>Audio Type: ${audioType}</p>
                            <p>File Extension: ${fileExtension}</p>
                        `;
                    }
                    
                    formData.append('file', audioBlob, `recording.${fileExtension}`);
                    
                    elements.recordingStatus.textContent = 'Transcribing...';
                    console.log('Sending audio to server for transcription...');
                    
                    const response = await axios.post(API_ENDPOINTS.speechToText, formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    });
                    
                    console.log('Server response:', response.data);
                    
                    // Show recognized text
                    if (response.data.text) {
                        elements.recognizedText.textContent = response.data.text;
                        elements.useRecordingBtn.disabled = false;
                        elements.recordingStatus.textContent = 'Recording processed successfully';
                    } else {
                        elements.recordingStatus.textContent = `No speech detected: ${response.data.error || 'Unknown error'}`;
                        if (debugInfo) {
                            debugInfo.innerHTML += `<p>Error: ${response.data.error || 'Unknown error'}</p>
                                                   <p>Status: ${response.data.status || 'Unknown status'}</p>`;
                        }
                    }
                } catch (error) {
                    console.error('Speech recognition error:', error);
                    
                    let errorMessage = 'Failed to process speech. Please try typing instead.';
                    let detailedError = error.message;
                    
                    if (error.response) {
                        // Handle specific error types from the server
                        const serverError = error.response.data.error || 'Unknown server error';
                        const serverStatus = error.response.data.status || 'unknown';
                        console.error(`Server error (${serverStatus}):`, serverError);
                        
                        detailedError = serverError;
                        
                        // Provide more specific user-friendly messages based on the error
                        if (serverStatus === 'conversion_failed') {
                            errorMessage = 'Failed to convert audio format. Please try typing instead.';
                        } else if (serverStatus === 'too_short') {
                            errorMessage = 'Recording too short. Please speak longer and more clearly.';
                        } else if (serverStatus === 'no_speech_detected') {
                            errorMessage = 'No speech detected. Please speak clearly in Japanese.';
                        } else if (serverStatus === 'invalid_format') {
                            errorMessage = 'Audio format not supported. Please try typing instead.';
                        }
                    }
                    
                    elements.recordingStatus.textContent = errorMessage;
                    
                    if (debugInfo) {
                        debugInfo.innerHTML += `
                            <p>Error Message: ${errorMessage}</p>
                            <p>Technical Error: ${detailedError}</p>
                        `;
                        if (error.response) {
                            debugInfo.innerHTML += `<p>Server Response: ${JSON.stringify(error.response.data)}</p>`;
                        }
                    }
                }
                
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            });
            
            // Start recording
            appState.mediaRecorder.start();
            appState.recording = true;
            console.log('Recording started');
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                elements.recordingStatus.textContent = 'Microphone access denied. Please grant permission in your browser.';
            } else {
                elements.recordingStatus.textContent = 'Could not access microphone. Error: ' + error.message;
            }
        }
    }
}

// Use recorded text
function useRecordedText() {
    const text = elements.recognizedText.textContent;
    if (text) {
        elements.userInput.value = text;
        elements.recordingModal.hide();
        elements.userInput.focus();
    }
}

// Add message to chat
function addMessage(role, content) {
    console.log("Adding message with role:", role);
    console.log("Raw content:", content);
    
    // Safety check - extract content string safely
    let contentString = "";
    
    // Handle different types of content
    try {
        if (typeof content === 'string') {
            contentString = content;
        } 
        else if (content && typeof content === 'object') {
            // If content has a 'content' property (server response format)
            if (content.content !== undefined) {
                contentString = String(content.content);
            } else {
                // Fallback to JSON string
                contentString = JSON.stringify(content);
            }
        }
        else {
            // For any other type, convert to string
            contentString = String(content || "");
        }
    } catch (e) {
        console.error("Error extracting content:", e);
        contentString = "Error displaying message";
    }
    
    console.log("Processed content string:", contentString);
    
    // Add to app state
    appState.messages.push({ role, content: contentString, timestamp: new Date() });
    
    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}-message`;
    
    // Create content element
    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    
    // For agent messages with Japanese content
    if (role === 'agent') {
        try {
            // Check if the content is just romaji without Japanese characters
            const hasJapaneseChars = /[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uff00-\uff9f\u4e00-\u9faf]/.test(contentString);
            const hasParentheses = /\([^)]+\)/.test(contentString);
            
            if (hasJapaneseChars && hasParentheses) {
                // Normal case: Japanese with romaji in parentheses
                const parts = contentString.split(/(\([^)]+\))/g);
                
                let formattedContent = '';
                let fullJapaneseText = '';
                let fullTransliteration = '';
                
                for (let i = 0; i < parts.length; i++) {
                    if (parts[i].startsWith('(') && parts[i].endsWith(')')) {
                        // Romaji part
                        const romaji = parts[i].substring(1, parts[i].length - 1);
                        formattedContent += `<div class="romaji">${romaji}</div>`;
                        fullTransliteration += romaji + ' ';
                    } else {
                        // Japanese part
                        formattedContent += parts[i];
                        fullJapaneseText += parts[i];
                    }
                }
                
                // Add formatted content
                contentEl.innerHTML = formattedContent;
                
                // Create audio control for Japanese text
                if (fullJapaneseText.trim()) {
                    const audioContainerEl = document.createElement('div');
                    audioContainerEl.className = 'audio-container';
                    createAudioControl(fullJapaneseText.trim(), audioContainerEl);
                    contentEl.appendChild(audioContainerEl);
                }
            } else if (hasJapaneseChars) {
                // Japanese without romaji
                contentEl.textContent = contentString;
                
                // Create audio control
                const audioContainerEl = document.createElement('div');
                audioContainerEl.className = 'audio-container';
                createAudioControl(contentString.trim(), audioContainerEl);
                contentEl.appendChild(audioContainerEl);
            } else if (!hasJapaneseChars && !hasParentheses && contentString.includes(' ')) {
                // Likely just romaji without proper formatting
                // Try to convert common romaji phrases to Japanese
                const romajiMap = {
                    'Konnichiwa': 'こんにちは',
                    'Irasshaimase': 'いらっしゃいませ',
                    'Hai': 'はい',
                    'Arigatou': 'ありがとう',
                    'Arigatou gozaimasu': 'ありがとうございます',
                    'Sumimasen': 'すみません',
                    'Onegaishimasu': 'お願いします',
                    'Sayounara': 'さようなら',
                    'Mata ne': 'またね'
                };
                
                let formattedContent = '';
                const words = contentString.split(/[.,!?\s]+/);
                
                words.forEach(word => {
                    if (word) {
                        const japaneseWord = romajiMap[word] || '';
                        if (japaneseWord) {
                            formattedContent += `${japaneseWord} (${word}) `;
                        } else {
                            formattedContent += `${word} `;
                        }
                    }
                });
                
                contentEl.innerHTML = formattedContent.trim();
            } else {
                // Fallback for any other format
                contentEl.textContent = contentString;
            }
        } catch (e) {
            console.error("Error formatting agent message:", e);
            contentEl.textContent = contentString;
        }
    } else {
        // User message - simple text
        contentEl.textContent = contentString;
    }
    
    // Add content to message
    messageEl.appendChild(contentEl);
    
    // Add message to chat
    elements.chatMessages.appendChild(messageEl);
    
    // Scroll to bottom
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    
    // Update UI state (ensure buttons and input field are in correct state)
    updateUI();
}

// Update UI state
function updateUI() {
    // Make sure send button is enabled when there's a conversation
    if (appState.conversationId) {
        elements.userInput.disabled = false;
        elements.sendBtn.disabled = false;
        
        // Enable speech button if supported
        if (elements.speechBtn) {
            elements.speechBtn.disabled = false;
        }
        
        // Enable help button
        if (elements.helpBtn) {
            elements.helpBtn.disabled = false;
        }
    } else {
        // No active conversation
        elements.userInput.disabled = true;
        elements.sendBtn.disabled = true;
        
        if (elements.speechBtn) {
            elements.speechBtn.disabled = true;
        }
        
        if (elements.helpBtn) {
            elements.helpBtn.disabled = true;
        }
    }
    
    // Update conversation view elements
    if (elements.scenarioTitle && appState.scenario) {
        elements.scenarioTitle.textContent = getScenarioTitle(appState.scenario);
    }
    
    if (elements.proficiencyBadge && appState.proficiency) {
        elements.proficiencyBadge.textContent = capitalize(appState.proficiency);
    }
}

// Show feedback
function showFeedback(feedback) {
    // Show feedback container
    elements.feedbackContainer.style.display = 'block';
    
    // Clear previous feedback
    elements.grammarTab.innerHTML = '';
    elements.vocabularyTab.innerHTML = '';
    elements.expressionTab.innerHTML = '';
    elements.overallTab.innerHTML = '';
    
    // Grammar feedback
    if (feedback.grammar && feedback.grammar.issues) {
        const grammarList = document.createElement('ul');
        grammarList.className = 'list-group mb-3';
        
        feedback.grammar.issues.forEach(issue => {
            const item = document.createElement('li');
            item.className = 'list-group-item';
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1 text-danger">${issue.error}</h6>
                </div>
                <p class="mb-1 text-success">${issue.correction}</p>
                <small>${issue.explanation}</small>
            `;
            grammarList.appendChild(item);
        });
        
        if (feedback.grammar.issues.length === 0) {
            elements.grammarTab.innerHTML = '<div class="alert alert-success">No grammar issues found!</div>';
        } else {
            elements.grammarTab.appendChild(grammarList);
        }
    }
    
    // Vocabulary feedback
    if (feedback.vocabulary && feedback.vocabulary.suggestions) {
        const vocabList = document.createElement('ul');
        vocabList.className = 'list-group mb-3';
        
        feedback.vocabulary.suggestions.forEach(suggestion => {
            const item = document.createElement('li');
            item.className = 'list-group-item';
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${suggestion.original}</h6>
                </div>
                <p class="mb-1 text-primary">→ ${suggestion.alternative}</p>
                <small>${suggestion.reason}</small>
            `;
            vocabList.appendChild(item);
        });
        
        if (feedback.vocabulary.suggestions.length === 0) {
            elements.vocabularyTab.innerHTML = '<div class="alert alert-success">Good vocabulary usage!</div>';
        } else {
            elements.vocabularyTab.appendChild(vocabList);
        }
    }
    
    // Natural expression feedback
    if (feedback.natural_expression && feedback.natural_expression.improvements) {
        const expressionList = document.createElement('ul');
        expressionList.className = 'list-group mb-3';
        
        feedback.natural_expression.improvements.forEach(improvement => {
            const item = document.createElement('li');
            item.className = 'list-group-item';
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${improvement.original}</h6>
                </div>
                <p class="mb-1 text-primary">→ ${improvement.improved}</p>
            `;
            expressionList.appendChild(item);
        });
        
        if (feedback.natural_expression.improvements.length === 0) {
            elements.expressionTab.innerHTML = '<div class="alert alert-success">Your expressions sound natural!</div>';
        } else {
            elements.expressionTab.appendChild(expressionList);
        }
    }
    
    // Overall feedback
    if (feedback.overall_feedback) {
        elements.overallTab.innerHTML = `<div class="alert alert-info">${feedback.overall_feedback}</div>`;
    }
}

// Show setup view
function showSetupView() {
    // Update state
    appState.currentView = 'setup';
    
    // Update UI
    elements.setupView.style.display = 'block';
    elements.conversationView.style.display = 'none';
    elements.feedbackContainer.style.display = 'none';
    elements.conversationSummary.style.display = 'none';
}

// Show conversation view
function showConversationView() {
    // Update state
    appState.currentView = 'conversation';
    
    // Update UI
    elements.setupView.style.display = 'none';
    elements.conversationView.style.display = 'block';
    elements.chatMessages.innerHTML = '';
    
    // Add messages from state
    appState.messages.forEach(msg => {
        addMessage(msg.role, msg.content);
    });
    
    // Focus input
    elements.userInput.focus();
}

// Utility Functions

// Generate a random ID
function generateId() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

// Capitalize a string
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Get scenario title
function getScenarioTitle(scenario) {
    const titles = {
        restaurant: 'Restaurant Conversation',
        shopping: 'Shopping Conversation',
        directions: 'Asking for Directions',
        interview: 'Job Interview'
    };
    
    return titles[scenario] || 'Conversation';
}

// Check if a string contains Japanese characters
function containsJapaneseCharacters(str) {
    return /[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uff00-\uff9f\u4e00-\u9faf\u3400-\u4dbf]/.test(str);
}

// Function to get a response suggestion
async function getResponseSuggestion() {
    // Only allow suggestions when a conversation is active
    if (!appState.conversationId) {
        alert('Please start a conversation first');
        return;
    }
    
    try {
        // Show suggestion area with loading state
        elements.responseSuggestion.style.display = 'block';
        elements.suggestionJapanese.innerHTML = '<div class="suggestion-loading"><div class="spinner-border suggestion-loading-spinner text-info" role="status"></div></div>';
        elements.suggestionTransliteration.textContent = 'Generating suggestion...';
        elements.suggestionAudioContainer.innerHTML = '';
        elements.useSuggestion.style.display = 'none';
        
        // Add context explanation if recent messages exist
        const contextHint = document.createElement('div');
        contextHint.className = 'text-muted small mb-3';
        contextHint.innerHTML = '<i class="bi bi-info-circle"></i> Generating a helpful response based on the current conversation...';
        elements.suggestionJapanese.parentNode.insertBefore(contextHint, elements.suggestionJapanese);
        
        // Scroll to make the suggestion visible
        elements.responseSuggestion.scrollIntoView({ behavior: 'smooth' });
        
        // Request suggestion from backend
        const response = await axios.post(API_ENDPOINTS.getSuggestion, {
            conversation_id: appState.conversationId
        });
        
        console.log('Suggestion response:', response.data);
        
        // Remove context hint after loading
        if (contextHint.parentNode) {
            contextHint.parentNode.removeChild(contextHint);
        }
        
        // Display suggestion
        if (response.data && (response.data.japanese_text || response.data.suggestion)) {
            // Get the Japanese text either from japanese_text field or extract from suggestion
            let japaneseText = response.data.japanese_text || '';
            let romajiText = response.data.romaji_text || '';
            
            // If we have a full suggestion but not parsed parts, extract them
            if (!japaneseText && response.data.suggestion) {
                const suggestion = response.data.suggestion;
                // Try to extract Japanese and romaji from the formatted suggestion
                const match = suggestion.match(/([^(]+)(\([^)]+\))/);
                if (match) {
                    japaneseText = match[1].trim();
                    romajiText = match[2].replace(/[()]/g, '').trim();
                } else {
                    japaneseText = suggestion;
                }
            }
            
            // Add a context explanation for the suggestion
            const helpContext = document.createElement('div');
            helpContext.className = 'alert alert-info mb-3';
            
            // Customize message based on recent agent message
            const recentAgentMsg = getRecentAgentMessage();
            if (recentAgentMsg && recentAgentMsg.includes('何名様')) {
                helpContext.innerHTML = '<strong>Context:</strong> The server is asking how many people are in your party. The suggested response tells them your party size.';
            } else if (recentAgentMsg && recentAgentMsg.includes('エラー')) {
                helpContext.innerHTML = '<strong>Context:</strong> There was an error. The suggested response clarifies your party size.';
            } else {
                helpContext.innerHTML = '<strong>Context:</strong> This is an appropriate response based on the conversation.';
            }
            
            elements.suggestionJapanese.parentNode.insertBefore(helpContext, elements.suggestionJapanese);
            
            // Display Japanese text
            elements.suggestionJapanese.textContent = japaneseText;
            
            // Display transliteration
            elements.suggestionTransliteration.textContent = 'Transliteration: ' + romajiText;
            
            // Create audio control
            createAudioControl(japaneseText, elements.suggestionAudioContainer);
            
            // Show the use suggestion button
            elements.useSuggestion.style.display = 'inline-block';
            
            // Highlight the suggestion briefly
            elements.responseSuggestion.classList.add('pulse-animation');
            setTimeout(() => {
                elements.responseSuggestion.classList.remove('pulse-animation');
            }, 2000);
        } else {
            // Handle case where no proper suggestion was returned
            elements.suggestionJapanese.textContent = 'Sorry, could not generate a suggestion.';
            elements.suggestionTransliteration.textContent = '';
            elements.suggestionAudioContainer.innerHTML = '';
        }
    } catch (error) {
        console.error('Error getting suggestion:', error);
        elements.suggestionJapanese.textContent = 'Error getting suggestion.';
        elements.suggestionTransliteration.textContent = 'Please try again.';
        elements.suggestionAudioContainer.innerHTML = '';
    }
}

// Helper function to get the most recent agent message
function getRecentAgentMessage() {
    if (!appState.messages || appState.messages.length === 0) {
        return '';
    }
    
    // Look for the most recent agent message
    for (let i = appState.messages.length - 1; i >= 0; i--) {
        if (appState.messages[i].role === 'agent') {
            return appState.messages[i].content;
        }
    }
    
    return '';
}

// Helper function to create audio control
function createAudioControl(text, container) {
    container.innerHTML = '';
    
    const audioControl = document.createElement('div');
    audioControl.className = 'audio-control';
    
    const playButton = document.createElement('button');
    playButton.className = 'btn btn-sm btn-outline-primary';
    playButton.innerHTML = '<i class="bi bi-volume-up"></i> Listen';
    playButton.dataset.japaneseText = text;
    
    // Add click handler for audio
    playButton.addEventListener('click', function() {
        this.disabled = true;
        this.innerHTML = '<i class="bi bi-hourglass-split"></i> Loading...';
        
        const text = this.dataset.japaneseText;
        let audioContainer = this.parentNode.querySelector('.audio-container');
        
        if (!audioContainer) {
            audioContainer = document.createElement('div');
            audioContainer.className = 'audio-container mt-2';
            this.parentNode.appendChild(audioContainer);
        }
        
        // Call TTS API
        fetch(API_ENDPOINTS.textToSpeech, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        })
        .then(response => {
            if (!response.ok) throw new Error('TTS request failed');
            return response.blob();
        })
        .then(blob => {
            const audioUrl = URL.createObjectURL(blob);
            
            let audioElement = audioContainer.querySelector('audio');
            if (!audioElement) {
                audioElement = document.createElement('audio');
                audioElement.controls = true;
                audioElement.className = 'w-100';
                audioContainer.appendChild(audioElement);
            }
            
            audioElement.src = audioUrl;
            audioElement.play();
            
            // Reset button
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-volume-up"></i> Listen';
        })
        .catch(error => {
            console.error('Audio error:', error);
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-volume-up"></i> Try Again';
            
            if (!audioContainer.querySelector('.error-message')) {
                const errorMsg = document.createElement('div');
                errorMsg.className = 'error-message text-danger small mt-1';
                errorMsg.textContent = 'Audio generation failed. Please try again.';
                audioContainer.appendChild(errorMsg);
            }
        });
    });
    
    audioControl.appendChild(playButton);
    container.appendChild(audioControl);
}

// Function to hide the suggestion area
function hideSuggestion() {
    elements.responseSuggestion.style.display = 'none';
}

// Function to use the suggested response
function useResponseSuggestion() {
    // Get the Japanese text from the suggestion
    const suggestedText = elements.suggestionJapanese.textContent;
    
    // Set it as the input value
    elements.userInput.value = suggestedText;
    
    // Hide the suggestion
    hideSuggestion();
    
    // Focus on the input field
    elements.userInput.focus();
}

// Initialize the app when the document is loaded
document.addEventListener('DOMContentLoaded', initApp); 