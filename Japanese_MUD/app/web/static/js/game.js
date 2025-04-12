/**
 * Japanese MUD Game - Client-side JavaScript
 * Handles WebSocket communication with the game server.
 */

// Connect to WebSocket server
const socket = io();

// DOM Elements
const gameOutput = document.getElementById('gameOutput');
const commandForm = document.getElementById('commandForm');
const commandInput = document.getElementById('commandInput');
const sendButton = document.getElementById('sendButton');

// Command history
let commandHistory = [];
let commandIndex = -1;

// Connect event
socket.on('connect', () => {
    addMessage('Connected to the game server.', 'success');
});

// Disconnect event
socket.on('disconnect', () => {
    addMessage('Disconnected from the game server.', 'error');
});

// Handle game output (normal text messages)
socket.on('output', (data) => {
    console.log("Received 'output' event:", data.text); // Log normal output
    processGameOutput(data.text);
});

// --- NEW: Handle structured location updates --- 
socket.on('update_location', (data) => {
    console.log("Received 'update_location' event:", data); // Log receiving the event and data
    updateLocationView(data);
});

// --- NEW: Handle location image updates --- 
socket.on('location_image', (data) => {
    const locationImage = document.getElementById('locationImage');
    if (locationImage && data.url) {
        locationImage.src = data.url;
        locationImage.alt = "Current location image"; // Update alt text maybe?
        locationImage.style.display = 'block'; // Ensure it's visible
    } else {
        console.warn("Could not find location image element or URL.");
        if (locationImage) locationImage.style.display = 'none';
    }
});

// Process game output and apply formatting
function processGameOutput(text) {
    // Replace special characters
    text = text.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;');
    
    // Apply formatting for Japanese text
    text = formatJapaneseText(text);
    
    // Apply highlighting for various game elements
    text = formatGameElements(text);
    
    // Add message to output
    addFormattedMessage(text);
}

// Format Japanese text (hiragana, katakana, kanji)
function formatJapaneseText(text) {
    // Match Japanese characters (keeping general class for now)
    const japaneseRegex = /([\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\uFF00-\uFFEF]+)/g;
    text = text.replace(japaneseRegex, (match) => `<span class="japanese">${match}</span>`);
    
    // --- ADDED: Specifically wrap Hiragana within the Japanese spans for distinct styling --- 
    const hiraganaRegex = /[\u3040-\u309F]+/g;
    // Find existing japanese spans and apply hiragana class within them
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = text;
    tempDiv.querySelectorAll('.japanese').forEach(span => {
        span.innerHTML = span.innerHTML.replace(hiraganaRegex, (hiraganaMatch) => `<span class="hiragana">${hiraganaMatch}</span>`);
    });
    return tempDiv.innerHTML;
}

// Format game elements like locations, items, NPCs
function formatGameElements(text) {
    // Highlight location names
    text = text.replace(/Location: ([^(\r\n)]+)/g, 'Location: <span class="location">$1</span>');
    
    // Highlight item names
    text = text.replace(/(taken|dropped|found|see) ([^.,!?\r\n]+)/gi, '$1 <span class="item">$2</span>');
    
    // Highlight NPC names
    text = text.replace(/(talking to|meet) ([^.,!?\r\n]+)/gi, '$1 <span class="npc">$2</span>');
    
    return text;
}

// Add message to game output
function addMessage(text, className = '') {
    const message = document.createElement('div');
    message.className = `message ${className}`;
    message.textContent = text;
    gameOutput.appendChild(message);
    scrollToBottom();
}

// Add formatted message to game output
function addFormattedMessage(html) {
    const message = document.createElement('div');
    message.className = 'message';
    message.innerHTML = html;
    gameOutput.appendChild(message);
    scrollToBottom();
}

// Scroll game output to bottom
function scrollToBottom() {
    gameOutput.scrollTop = gameOutput.scrollHeight;
}

// Send command to server
function sendCommand(command) {
    if (!command.trim()) return;
    
    // Add command to history
    commandHistory.unshift(command);
    if (commandHistory.length > 50) {
        commandHistory.pop();
    }
    commandIndex = -1;
    
    // Display command in output
    addMessage(`> ${command}`, 'command');
    
    // Send command to server
    socket.emit('command', { command });
    
    // Clear input
    commandInput.value = '';
}

// Handle command form submission
commandForm.addEventListener('submit', (e) => {
    e.preventDefault();
    sendCommand(commandInput.value);
});

// Handle command history navigation with up/down arrows
commandInput.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (commandHistory.length > 0) {
            commandIndex = Math.min(commandIndex + 1, commandHistory.length - 1);
            commandInput.value = commandHistory[commandIndex];
            // Move cursor to end of input
            setTimeout(() => {
                commandInput.selectionStart = commandInput.selectionEnd = commandInput.value.length;
            }, 0);
        }
    } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (commandIndex > 0) {
            commandIndex--;
            commandInput.value = commandHistory[commandIndex];
        } else if (commandIndex === 0) {
            commandIndex = -1;
            commandInput.value = '';
        }
    }
});

// Focus input field when clicking anywhere in the game area
document.querySelector('.game-wrapper').addEventListener('click', () => {
    commandInput.focus();
});

// Tab completion (just focus on input)
commandInput.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
        e.preventDefault();
        commandInput.focus();
    }
});

// Initialize
window.addEventListener('load', () => {
    commandInput.focus();
});

// --- NEW: Update the entire game view based on structured data --- 
function updateLocationView(data) {
    console.log("Running updateLocationView with data:", data); // Log function entry
    
    // Basic check for expected data structure
    if (!data || typeof data.description !== 'string' || !Array.isArray(data.items) || !Array.isArray(data.npcs)) {
        console.error("Invalid data received in updateLocationView:", data);
        addMessage("[Error: Received invalid location data from server]", "error");
        return;
    }

    // Create a container for this update
    const updateContainer = document.createElement('div');
    updateContainer.className = 'message location-update'; // Add a class for styling
    
    // 1. Display Description (process for formatting)
    const descriptionElement = document.createElement('div');
    descriptionElement.className = 'location-description';
    let baseDescription = data.description.split("\nYou see:")[0].split("\nPeople present:")[0].split("\nExits:")[0].trim(); // Get only the core description part
    let formattedDesc = baseDescription.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    formattedDesc = formatJapaneseText(formattedDesc); // Apply Japanese styling
    formattedDesc = formattedDesc.replace(/\n/g, '<br>'); // Convert newlines
    descriptionElement.innerHTML = formattedDesc; // Use innerHTML as it contains spans
    updateContainer.appendChild(descriptionElement);
    
    // 2. Display Items with Hint functionality
    const itemsElement = document.createElement('div');
    itemsElement.className = 'location-items';
    if (data.items && data.items.length > 0) {
        const itemsTitle = document.createElement('strong');
        itemsTitle.textContent = 'Items: ';
        itemsElement.appendChild(itemsTitle);
        
        const itemsList = document.createElement('ul');
        itemsList.className = 'item-list';
        data.items.forEach((item, index) => {
            const listItem = document.createElement('li');
            listItem.className = 'item-entry';
            
            // Japanese Name
            const nameJp = document.createElement('span');
            nameJp.className = 'item-name-jp japanese'; // Add japanese class
            nameJp.textContent = item.name;
            listItem.appendChild(nameJp);
            
            // Hint span (clickable)
            const hintSpan = document.createElement('span');
            hintSpan.className = 'item-hint';
            hintSpan.textContent = ' [Hint]';
            hintSpan.style.cursor = 'pointer';
            hintSpan.style.color = 'blue'; // Make it look clickable
            hintSpan.setAttribute('data-item-index', index);
            listItem.appendChild(hintSpan);
            
            // Hidden Details span
            const detailsSpan = document.createElement('span');
            detailsSpan.className = 'item-details';
            detailsSpan.style.display = 'none'; // Initially hidden
            detailsSpan.innerHTML = ` (<span class="item-name-en">${item.name_english}</span> / <span class="item-name-romaji">${item.name_romaji || 'N/A'}</span>)`;
            listItem.appendChild(detailsSpan);
            
            // --- NEW: Add contextual action links --- 
            const examineLink = document.createElement('span');
            examineLink.className = 'action-link';
            examineLink.textContent = ' [Examine]';
            examineLink.setAttribute('data-command', 'examine');
            examineLink.setAttribute('data-target', item.name_english || item.name); // Use English name if available
            listItem.appendChild(examineLink);
            
            if (item.can_be_taken) {
                const takeLink = document.createElement('span');
                takeLink.className = 'action-link';
                takeLink.textContent = ' [Take]';
                takeLink.setAttribute('data-command', 'take');
                takeLink.setAttribute('data-target', item.name_english || item.name);
                listItem.appendChild(takeLink);
            }
            // Potential future: [Drop] link if item is in inventory?
            
            itemsList.appendChild(listItem);
        });
        itemsElement.appendChild(itemsList);
    } else {
        itemsElement.textContent = 'Items: None';
    }
    updateContainer.appendChild(itemsElement);
    
    // 3. Display NPCs (can add similar hint logic later if desired)
    const npcsElement = document.createElement('div');
    npcsElement.className = 'location-npcs';
    if (data.npcs && data.npcs.length > 0) {
        const npcsTitle = document.createElement('strong');
        npcsTitle.textContent = 'People: ';
        npcsElement.appendChild(npcsTitle);
        
        const npcsList = document.createElement('ul');
        npcsList.className = 'npc-list';
        data.npcs.forEach(npc => {
            const listItem = document.createElement('li');
            listItem.className = 'npc-entry';
            
            // --- FIX: Format NPC similar to items with a hint --- 
            let npcNameHtml = "";
            if (npc.name) {
                // Apply japanese/hiragana formatting to the Japanese name
                npcNameHtml = `<span class="npc-name-jp japanese">${formatJapaneseText(npc.name)}</span>`; 
            }
            
            // Clickable Hint
            const hintSpan = document.createElement('span');
            hintSpan.className = 'npc-hint'; // Use different class for delegation if needed
            hintSpan.textContent = ' [?]'; // Use different symbol maybe
            hintSpan.style.cursor = 'pointer';
            hintSpan.style.color = 'green'; // Different color for NPC hints
            
            // Hidden Details
            const detailsSpan = document.createElement('span');
            detailsSpan.className = 'npc-details';
            detailsSpan.style.display = 'none';
            let detailsText = " (";
            if (npc.name_english) {
                detailsText += `<span class="npc-name-en">${npc.name_english}</span>`;
            }
            if (npc.name_romaji) {
                detailsText += ` / <span class="npc-name-romaji">${npc.name_romaji}</span>`;
            }
            detailsText += ")";
            if (npc.short_description) {
                 // Escape potential HTML in description
                const escapedDesc = npc.short_description.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                detailsText += ` - <span class="npc-desc">${escapedDesc}</span>`;
            }
            detailsSpan.innerHTML = detailsText;

            // Assemble the list item
            listItem.innerHTML = npcNameHtml; // Start with Japanese name
            listItem.appendChild(hintSpan);
            listItem.appendChild(detailsSpan);
            
            // --- NEW: Add contextual action links --- 
            const talkLink = document.createElement('span');
            talkLink.className = 'action-link';
            talkLink.textContent = ' [Talk]';
            talkLink.setAttribute('data-command', 'talk');
            talkLink.setAttribute('data-target', npc.name_english || npc.name);
            listItem.appendChild(talkLink);
            
            npcsList.appendChild(listItem);
        });
        npcsElement.appendChild(npcsList);
    } else {
        npcsElement.textContent = 'People: None';
    }
    updateContainer.appendChild(npcsElement);
    
    // --- Display Exits --- 
    const exitsElement = document.createElement('div');
    exitsElement.className = 'location-exits';
    // --- FIX: Always show cardinal directions as potential exits --- 
    exitsElement.textContent = "Exits: north, south, east, west";
    // Remove parsing from description string:
    // const exitMatch = data.description.match(/\nExits: (.*)/);
    // exitsElement.textContent = exitMatch ? `Exits: ${exitMatch[1]}` : "Exits: None";
    updateContainer.appendChild(exitsElement);

    // Append the whole update block to the game output
    gameOutput.appendChild(updateContainer);
    console.log("Appended location update container to game output."); // Log successful appending
    scrollToBottom();
}

// --- NEW: Event listener for Hint clicks (using event delegation) --- 
gameOutput.addEventListener('click', function(event) {
    // Handle Item Hints
    if (event.target.classList.contains('item-hint')) {
        const hintSpan = event.target;
        const listItem = hintSpan.closest('.item-entry');
        if (listItem) {
            const detailsSpan = listItem.querySelector('.item-details');
            if (detailsSpan) {
                hintSpan.style.display = 'none'; // Hide the hint link
                detailsSpan.style.display = 'inline'; // Show the details
            }
        }
    }
    // --- ADDED: Handle NPC Hints --- 
    else if (event.target.classList.contains('npc-hint')) {
        const hintSpan = event.target;
        const listItem = hintSpan.closest('.npc-entry'); // Target NPC list item
        if (listItem) {
            const detailsSpan = listItem.querySelector('.npc-details'); // Target NPC details span
            if (detailsSpan) {
                hintSpan.style.display = 'none'; // Hide the hint link
                detailsSpan.style.display = 'inline'; // Show the details
            }
        }
    }
    // --- ADDED: Handle Contextual Action Links --- 
    else if (event.target.classList.contains('action-link')) {
        const actionLink = event.target;
        const command = actionLink.getAttribute('data-command');
        const target = actionLink.getAttribute('data-target');
        
        if (command && target) {
            // Construct command, quoting target name might be safer
            const fullCommand = `${command} ${target}`; 
            sendCommand(fullCommand);
        } else {
            console.error("Action link missing command or target:", actionLink);
        }
    }
});

// --- NEW: Add listeners for Static Command Buttons --- 
document.addEventListener('DOMContentLoaded', () => {
    const staticCommandButtons = document.querySelectorAll('.static-commands .cmd-btn');
    staticCommandButtons.forEach(button => {
        button.addEventListener('click', () => {
            const command = button.getAttribute('data-command');
            if (command) {
                sendCommand(command);
            }
        });
    });
    
    // Initial focus
    if (commandInput) {
        commandInput.focus();
    }
}); 