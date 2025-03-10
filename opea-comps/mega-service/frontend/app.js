// Configuration
const API_BASE_URL = 'http://localhost:8082';
const API_ENDPOINTS = {
    basic: '/v1/japanese_tts',
    translate: '/v1/translate_and_speak',
    learning: '/v1/learning_mode',
    examples: '/v1/example_generator'
};

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    // Basic TTS
    const basicText = document.getElementById('basic-text');
    const basicSubmit = document.getElementById('basic-submit');
    const basicLoading = document.getElementById('basic-loading');
    const basicResult = document.getElementById('basic-result');

    // Translate & Speak
    const translateText = document.getElementById('translate-text');
    const translateModel = document.getElementById('translate-model');
    const includeDetails = document.getElementById('include-details');
    const translateSubmit = document.getElementById('translate-submit');
    const translateLoading = document.getElementById('translate-loading');
    const translateResult = document.getElementById('translate-result');

    // Learning Mode
    const learningText = document.getElementById('learning-text');
    const learningModel = document.getElementById('learning-model');
    const isEnglish = document.getElementById('is-english');
    const learningSubmit = document.getElementById('learning-submit');
    const learningLoading = document.getElementById('learning-loading');
    const learningResult = document.getElementById('learning-result');

    // Example Generator
    const keyword = document.getElementById('keyword');
    const examplesModel = document.getElementById('examples-model');
    const exampleCount = document.getElementById('example-count');
    const generateAudio = document.getElementById('generate-audio');
    const examplesSubmit = document.getElementById('examples-submit');
    const examplesLoading = document.getElementById('examples-loading');
    const examplesResult = document.getElementById('examples-result');

    // Event Listeners
    basicSubmit.addEventListener('click', handleBasicTTS);
    translateSubmit.addEventListener('click', handleTranslate);
    learningSubmit.addEventListener('click', handleLearning);
    examplesSubmit.addEventListener('click', handleExamples);

    // Basic TTS Handler
    async function handleBasicTTS() {
        const text = basicText.value.trim();
        if (!text) {
            showError(basicResult, 'Please enter some Japanese text');
            return;
        }

        basicLoading.style.display = 'flex';
        basicResult.innerHTML = '';

        try {
            const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.basic}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                throw new Error(`API returned ${response.status}: ${await response.text()}`);
            }

            const blob = await response.blob();
            displayAudioResult(basicResult, blob, text);
        } catch (error) {
            showError(basicResult, `Error: ${error.message}`);
        } finally {
            basicLoading.style.display = 'none';
        }
    }

    // Translation Handler
    async function handleTranslate() {
        const text = translateText.value.trim();
        if (!text) {
            showError(translateResult, 'Please enter some English text');
            return;
        }

        translateLoading.style.display = 'flex';
        translateResult.innerHTML = '';

        try {
            const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.translate}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text,
                    model: translateModel.value,
                    include_details: includeDetails.checked
                })
            });

            if (!response.ok) {
                throw new Error(`API returned ${response.status}: ${await response.text()}`);
            }

            const blob = await response.blob();
            
            // Check if translation details are provided in headers
            const translationDetails = response.headers.get('X-Translation-Details');
            
            if (translationDetails && includeDetails.checked) {
                const details = JSON.parse(translationDetails);
                displayTranslationResult(translateResult, blob, details);
            } else {
                // If no details, just display the audio
                displayAudioResult(translateResult, blob, 'Translated Japanese');
            }
        } catch (error) {
            showError(translateResult, `Error: ${error.message}`);
        } finally {
            translateLoading.style.display = 'none';
        }
    }

    // Learning Mode Handler
    async function handleLearning() {
        const text = learningText.value.trim();
        if (!text) {
            showError(learningResult, 'Please enter some text');
            return;
        }

        learningLoading.style.display = 'flex';
        learningResult.innerHTML = '';

        try {
            const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.learning}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text,
                    model: learningModel.value,
                    is_english: isEnglish.checked
                })
            });

            if (!response.ok) {
                throw new Error(`API returned ${response.status}: ${await response.text()}`);
            }

            // Get the text details from the X-Text-Details header
            const textDetails = response.headers.get('X-Text-Details');
            const blob = await response.blob();
            
            if (textDetails) {
                const details = JSON.parse(textDetails);
                displayLearningResult(learningResult, blob, details);
            } else {
                displayAudioResult(learningResult, blob, 'Learning Mode Audio');
            }
        } catch (error) {
            showError(learningResult, `Error: ${error.message}`);
        } finally {
            learningLoading.style.display = 'none';
        }
    }

    // Examples Generator Handler
    async function handleExamples() {
        const keywordText = keyword.value.trim();
        if (!keywordText) {
            showError(examplesResult, 'Please enter a Japanese word or phrase');
            return;
        }

        examplesLoading.style.display = 'flex';
        examplesResult.innerHTML = '';

        try {
            const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.examples}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    keyword: keywordText,
                    model: examplesModel.value,
                    count: parseInt(exampleCount.value),
                    generate_audio: generateAudio.checked
                })
            });

            if (!response.ok) {
                throw new Error(`API returned ${response.status}: ${await response.text()}`);
            }

            const data = await response.json();
            displayExamplesResult(examplesResult, data);
        } catch (error) {
            showError(examplesResult, `Error: ${error.message}`);
        } finally {
            examplesLoading.style.display = 'none';
        }
    }

    // Helper Functions
    function showError(element, message) {
        let errorMessage = message;
        element.innerHTML = `<div class="alert alert-danger">${errorMessage}</div>`;
    }

    function displayAudioResult(element, blob, label) {
        const audioUrl = URL.createObjectURL(blob);
        
        element.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">${label}</h5>
                    <audio controls class="audio-player">
                        <source src="${audioUrl}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                    <div class="mt-3">
                        <a href="${audioUrl}" download="japanese_audio.mp3" class="btn btn-sm btn-outline-primary">
                            <i class="bi bi-download"></i> Download Audio
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    function displayTranslationResult(element, blob, details) {
        const audioUrl = URL.createObjectURL(blob);
        
        // Create HTML for furigana if available
        let furiganaHtml = '';
        if (details.furigana && details.furigana.length > 0) {
            furiganaHtml = `
                <h6 class="mt-3">Kanji Readings:</h6>
                <div class="furigana-container">
                    ${details.furigana.map(item => 
                        `<span class="word-item">
                            <span class="word-surface">${item.kanji}</span> → 
                            <span class="word-reading">${item.reading}</span>
                        </span>`
                    ).join('')}
                </div>
            `;
        }
        
        element.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Translation Result</h5>
                    <div class="jp-text mb-2">${details.original}</div>
                    <div class="romaji mb-3">${details.romaji || ''}</div>
                    
                    ${furiganaHtml}
                    
                    <audio controls class="audio-player">
                        <source src="${audioUrl}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                    <div class="mt-3">
                        <a href="${audioUrl}" download="translated_audio.mp3" class="btn btn-sm btn-outline-primary">
                            <i class="bi bi-download"></i> Download Audio
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    function displayLearningResult(element, blob, details) {
        const audioUrl = URL.createObjectURL(blob);
        
        // Create HTML for word breakdown
        let wordsHtml = '';
        if (details.words && details.words.length > 0) {
            wordsHtml = `
                <h6 class="mt-3">Word Breakdown:</h6>
                <div class="furigana-container">
                    ${details.words.map(word => 
                        `<span class="word-item">
                            <span class="word-surface">${word.surface}</span>
                            <span class="word-reading">(${word.reading})</span>
                            <span class="word-pos">${word.pos}</span>
                        </span>`
                    ).join('')}
                </div>
            `;
        }
        
        element.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Learning Materials</h5>
                    <div class="jp-text mb-2">${details.original}</div>
                    <div class="romaji mb-3">${details.romaji || ''}</div>
                    
                    ${wordsHtml}
                    
                    <div class="mt-3 mb-3">
                        <p class="text-muted"><i class="bi bi-info-circle"></i> This audio is played at a slower speed for better learning.</p>
                    </div>
                    
                    <audio controls class="audio-player">
                        <source src="${audioUrl}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                    <div class="mt-3">
                        <a href="${audioUrl}" download="learning_audio.mp3" class="btn btn-sm btn-outline-primary">
                            <i class="bi bi-download"></i> Download Audio
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    function displayExamplesResult(element, data) {
        if (!data.examples) {
            showError(element, 'No examples were generated');
            return;
        }
        
        // Try to parse the examples from the raw text if the API didn't return parsed_examples
        let parsedExamples = data.parsed_examples || [];
        
        if (parsedExamples.length === 0 && data.examples) {
            try {
                // Try to extract JSON objects from the text
                const jsonRegex = /\{[^{}]*\}/g;
                const matches = data.examples.match(jsonRegex);
                
                if (matches) {
                    parsedExamples = matches.map(jsonStr => {
                        try {
                            return JSON.parse(jsonStr);
                        } catch (e) {
                            return null;
                        }
                    }).filter(item => item !== null);
                }
            } catch (error) {
                console.error('Error parsing examples:', error);
            }
        }
        
        // If we still don't have parsed examples, just show the raw text
        if (parsedExamples.length === 0) {
            element.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Generated Examples</h5>
                        <pre class="bg-light p-3 rounded">${data.examples}</pre>
                    </div>
                </div>
            `;
            return;
        }
        
        // If we have parsed examples, display them nicely
        const examplesHtml = parsedExamples.map((example, index) => `
            <div class="example-card">
                <h6>Example ${index + 1}:</h6>
                <div class="jp-text">${example.japanese || ''}</div>
                <div class="romaji my-1">${example.romaji || ''}</div>
                <div class="text-muted">${example.english || ''}</div>
                ${example.has_audio ? `
                    <div class="mt-2">
                        <span class="badge bg-primary">
                            <i class="bi bi-volume-up me-1"></i> Audio Available
                        </span>
                    </div>
                ` : ''}
            </div>
        `).join('');
        
        element.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Generated Examples</h5>
                    <div class="examples-container">
                        ${examplesHtml}
                    </div>
                </div>
            </div>
        `;
    }
}); 