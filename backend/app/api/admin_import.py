from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
import re
import openai
import logging
from app.config import settings
from app.config.supabase import supabase
from app.config.infrastructure import infrastructure
from supabase import create_client
import asyncio
import random

router = APIRouter()

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize OpenAI
client = openai.OpenAI(api_key=settings.openai_api_key)

# Initialize Supabase client directly with service key for admin operations
supabase_client = create_client(settings.supabase_url, settings.supabase_service_key)


class ConversationImportRequest(BaseModel):
    text: str
    title: Optional[str] = None


@router.get("/", response_class=HTMLResponse)
async def import_interface():
    """Serve the conversation import interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Express - Conversation Import</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            h1 {
                color: white;
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            
            .main-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            
            @media (max-width: 968px) {
                .main-grid {
                    grid-template-columns: 1fr;
                }
            }
            
            .card {
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }
            
            .card-title {
                font-size: 1.3em;
                font-weight: 600;
                margin-bottom: 20px;
                color: #333;
            }
            
            .import-textarea {
                width: 100%;
                min-height: 400px;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-family: 'Monaco', 'Courier New', monospace;
                font-size: 13px;
                resize: vertical;
                transition: border-color 0.3s;
            }
            
            .import-textarea:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .format-hint {
                background: #f0f4ff;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                font-size: 13px;
                color: #4a5568;
                line-height: 1.6;
            }
            
            .format-example {
                background: #2d3748;
                color: #e2e8f0;
                padding: 12px;
                border-radius: 6px;
                font-family: 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                margin-top: 10px;
                overflow-x: auto;
            }
            
            button {
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .btn-parse {
                background: #667eea;
                color: white;
                width: 100%;
                margin-top: 15px;
            }
            
            .btn-parse:hover {
                background: #5a67d8;
                transform: translateY(-1px);
            }
            
            .btn-save {
                background: #48bb78;
                color: white;
            }
            
            .btn-clear {
                background: #e0e0e0;
                color: #666;
            }
            
            .preview-section {
                max-height: 500px;
                overflow-y: auto;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
            
            .conversation-preview {
                margin-bottom: 20px;
                padding-bottom: 20px;
                border-bottom: 2px solid #f0f0f0;
            }
            
            .conversation-preview:last-child {
                border-bottom: none;
            }
            
            .preview-title {
                font-weight: 600;
                color: #667eea;
                margin-bottom: 10px;
            }
            
            .dialogue-turn {
                margin: 10px 0;
                padding: 10px;
                border-radius: 6px;
            }
            
            .ai-turn {
                background: #f0f4ff;
                border-left: 3px solid #667eea;
            }
            
            .user-turn {
                background: #f0fff4;
                border-left: 3px solid #48bb78;
            }
            
            .speaker-name {
                font-weight: 600;
                color: #333;
                margin-bottom: 5px;
                font-size: 12px;
                text-transform: uppercase;
            }
            
            .dialogue-text {
                color: #4a5568;
                line-height: 1.5;
            }
            
            .thought-section {
                margin-top: 8px;
                padding: 8px;
                background: #fffbeb;
                border-radius: 4px;
            }
            
            .korean-thought {
                color: #92400e;
                font-weight: 500;
                margin-bottom: 4px;
            }
            
            .english-expression {
                color: #78716c;
                font-style: italic;
                font-size: 13px;
            }
            
            .action-buttons {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            
            .action-buttons button {
                flex: 1;
            }
            
            .status-message {
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
                display: none;
            }
            
            .status-success {
                background: #c6f6d5;
                color: #22543d;
                border-left: 4px solid #48bb78;
            }
            
            .status-error {
                background: #fed7d7;
                color: #742a2a;
                border-left: 4px solid #fc8181;
            }
            
            .status-info {
                background: #bee3f8;
                color: #2c5282;
                border-left: 4px solid #4299e1;
            }
            
            .stats {
                display: flex;
                gap: 15px;
                margin-top: 15px;
            }
            
            .stat {
                flex: 1;
                text-align: center;
                padding: 10px;
                background: #f7fafc;
                border-radius: 6px;
            }
            
            .stat-value {
                font-size: 1.5em;
                font-weight: bold;
                color: #667eea;
            }
            
            .stat-label {
                font-size: 11px;
                color: #718096;
                text-transform: uppercase;
                margin-top: 4px;
            }
            
            .audio-badge {
                display: inline-block;
                padding: 2px 8px;
                background: #edf2f7;
                border-radius: 12px;
                font-size: 11px;
                color: #4a5568;
                margin-left: 8px;
            }
            
            .audio-pending {
                background: #fef5e7;
                color: #f39c12;
            }
            
            .audio-ready {
                background: #d5f4e6;
                color: #27ae60;
            }
            
            .voice-selector-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                border: 2px solid #667eea;
            }
            
            .voice-selector-card h3 {
                margin: 0 0 15px 0;
                color: #667eea;
                font-size: 1.1em;
            }
            
            .voice-controls {
                display: flex;
                gap: 15px;
                align-items: center;
                flex-wrap: wrap;
            }
            
            .voice-select {
                padding: 8px 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                cursor: pointer;
                transition: border-color 0.3s;
            }
            
            .voice-select:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .btn-preview {
                background: #667eea;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                cursor: pointer;
                transition: background 0.3s;
            }
            
            .btn-preview:hover {
                background: #5a67d8;
            }
            
            .btn-preview:disabled {
                background: #cbd5e0;
                cursor: not-allowed;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📝 Express Conversation Import</h1>
            
            <!-- Character Selection -->
            <div class="card" style="margin-bottom: 20px;">
                <h2 class="card-title">Select Character</h2>
                <p style="margin-bottom: 12px; color: #666;">Choose which character will be practicing these conversations</p>
                <select id="characterSelect" class="character-select" onchange="window.onCharacterChange()" style="width: 100%; padding: 12px; border: 2px solid #e3e4e6; border-radius: 8px; font-size: 15px;">
                    <option value="">-- Select a Character --</option>
                    <option value="alex" data-location="new-york" data-age="18-24" data-gender="male">Alex (New York, 21, College Student)</option>
                    <option value="emma" data-location="new-york" data-age="18-24" data-gender="female">Emma (New York, 22, Intern)</option>
                    <option value="marcus" data-location="new-york" data-age="25-34" data-gender="male">Marcus (New York, 28, Software Engineer)</option>
                    <option value="sofia" data-location="new-york" data-age="25-34" data-gender="female">Sofia (New York, 27, Marketing Manager)</option>
                    <option value="ryan" data-location="los-angeles" data-age="18-24" data-gender="male">Ryan (Los Angeles, 20, Film Student)</option>
                    <option value="mia" data-location="los-angeles" data-age="18-24" data-gender="female">Mia (Los Angeles, 21, Actor)</option>
                    <option value="jake" data-location="los-angeles" data-age="25-34" data-gender="male">Jake (Los Angeles, 29, Musician)</option>
                    <option value="luna" data-location="los-angeles" data-age="25-34" data-gender="female">Luna (Los Angeles, 26, Designer)</option>
                </select>
                <div id="characterInfo" style="margin-top: 10px; display: none;">
                    <span id="characterInfoText" style="display: inline-block; padding: 6px 12px; background: #e8f5e9; color: #2e7d32; border-radius: 20px; font-size: 13px;"></span>
                </div>
            </div>
            
            <div class="main-grid">
                <!-- Left: Input Section -->
                <div class="card">
                    <h2 class="card-title">Import Conversations</h2>
                    
                    <div class="format-hint">
                        <strong>Format:</strong> First select a character above, then paste your conversations below. Use speaker names with colons, 
                        and wrap Korean thoughts and English expressions in brackets.
                        <div id="characterHint" style="color: #667eea; font-weight: bold; display: none; margin-top: 10px;">
                            💡 Replace "User" with: <span id="selectedCharacterName"></span>
                        </div>
                        <div class="format-example">[Day: 15]
[Time: Monday 2:30pm]
[Location: Coffee shop]
[Journal Context: Exhausted, desperately need caffeine]

Barista: What can I get you today?
Alex: I'll have a large iced americano

Barista: Rough day? We have a strong dark roast.
Alex: [Practice] [Korean: 트리플 샷 라떼가 좋겠네요. 프로젝트 마감이라서]
      [English: Triple shot sounds perfect. Got a deadline]

Barista: Coming right up! Name for the order?
Alex: It's Alex

---

[Day: 30]
[Time: Friday 6:00pm]
[Location: Gym]
[Journal Context: Finally finished the project, feeling accomplished]

Friend: Hey! Haven't seen you all week!
Alex: Yeah, been swamped with work

Friend: Want to grab drinks after this?
Alex: [Practice] [Korean: 좋아요! 한 시간만 운동하고 갈게요]
      [English: Sounds good! Let me finish my workout first]</div>
                    </div>
                    
                    <textarea 
                        id="importText" 
                        class="import-textarea" 
                        placeholder="Paste your conversations here...

Format:
[Day: 1]
[Time: Monday 9:00am]
[Location: Coffee shop near work]
[Journal Context: First day in the city, nervous about ordering]

User: [Korean: 커피 주문하고 싶어요] [English: I'd like to order coffee]
Barista: What can I get for you today?

---

Multiple conversations separated by '---' (three dashes)"
                    ></textarea>
                    
                    <button class="btn-parse" onclick="window.parseConversations()">
                        🔍 Parse & Preview
                    </button>
                    
                    <div id="inputStatus" class="status-message"></div>
                </div>
                
                <!-- Right: Preview Section -->
                <div class="card">
                    <h2 class="card-title">Preview & Save</h2>
                    
                    <div class="stats" id="stats" style="display: none;">
                        <div class="stat">
                            <div class="stat-value" id="convCount">0</div>
                            <div class="stat-label">Conversations</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="turnCount">0</div>
                            <div class="stat-label">Total Turns</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="audioCount">0</div>
                            <div class="stat-label">Audio Files</div>
                        </div>
                    </div>
                    
                    <div class="preview-section" id="previewSection">
                        <p style="color: #a0aec0; text-align: center; padding: 40px;">
                            Parse conversations to see preview...
                        </p>
                    </div>
                    
                    <div class="action-buttons" id="actionButtons" style="display: none;">
                        <button class="btn-clear" onclick="window.clearAll()">
                            🔄 Clear
                        </button>
                        <button class="btn-save" onclick="window.saveToSupabase()">
                            💾 Generate Audio & Save
                        </button>
                    </div>
                    
                    <div id="saveStatus" class="status-message"></div>
                </div>
            </div>
        </div>
        
        <script>
            console.log('Script starting to load...');
            let parsedConversations = [];
            let voiceSamples = {};
            let selectedVoice = 'random';
            let selectedCharacter = null;
            
            // Character change handler
            window.onCharacterChange = function() {
                const select = document.getElementById('characterSelect');
                const selectedOption = select.options[select.selectedIndex];
                const infoDiv = document.getElementById('characterInfo');
                const infoText = document.getElementById('characterInfoText');
                
                if (selectedOption.value) {
                    selectedCharacter = {
                        name: selectedOption.text.split(' ')[0], // Extract first name
                        value: selectedOption.value,
                        location: selectedOption.dataset.location,
                        ageGroup: selectedOption.dataset.age,
                        gender: selectedOption.dataset.gender
                    };
                    
                    infoDiv.style.display = 'block';
                    infoText.textContent = `Selected: ${selectedCharacter.name} (${selectedCharacter.location === 'new-york' ? 'New York' : 'Los Angeles'})`;
                    
                    // Update the UI hint
                    const hint = document.getElementById('characterHint');
                    const nameSpan = document.getElementById('selectedCharacterName');
                    if (hint && nameSpan) {
                        hint.style.display = 'block';
                        nameSpan.textContent = selectedCharacter.name;
                    }
                    
                    // Re-parse if there's existing text
                    const inputText = document.getElementById('importText').value;
                    if (inputText.trim()) {
                        window.parseConversations();
                    }
                } else {
                    selectedCharacter = null;
                    infoDiv.style.display = 'none';
                    
                    // Hide the hint
                    const hint = document.getElementById('characterHint');
                    if (hint) {
                        hint.style.display = 'none';
                    }
                }
            }
            
            // Load voice samples on page load
            window.addEventListener('load', async () => {
                try {
                    const response = await fetch('/api/voices/samples');
                    const data = await response.json();
                    if (data.status === 'success') {
                        voiceSamples = data.samples;
                        console.log('Voice samples loaded:', voiceSamples);
                    }
                } catch (error) {
                    console.error('Failed to load voice samples:', error);
                }
            });
            
            console.log('Defining parseConversations...');
            // Helper function to check if speaker matches selected character
            window.isSelectedCharacter = function(speakerName) {
                if (!selectedCharacter) return false;
                return speakerName.toLowerCase() === selectedCharacter.name.toLowerCase();
            }
            
            window.parseConversations = function() {
                console.log('parseConversations called!');
                
                // Check if character is selected
                if (!selectedCharacter) {
                    window.showStatus('inputStatus', 'Please select a character first', 'error');
                    return;
                }
                
                const text = document.getElementById('importText').value.trim();
                
                if (!text) {
                    window.showStatus('inputStatus', 'Please paste conversations to parse', 'error');
                    return;
                }
                
                try {
                    // Split by --- to separate multiple conversations  
                    const conversationTexts = text.split('\\n---').filter(c => c.trim());
                    parsedConversations = [];
                    
                    conversationTexts.forEach((convText, index) => {
                        const lines = convText.trim().split('\\n');
                        const dialogue = [];
                        let currentSpeaker = null;
                        let currentText = '';
                        let koreanThought = '';
                        let englishExpression = '';
                        let turnId = 1;
                        
                        // Extract metadata
                        let dayNumber = null;
                        let timeOfDay = null;
                        let location = null;
                        let journalContext = null;
                        
                        lines.forEach(line => {
                            line = line.trim();
                            
                            // Check for metadata
                            const dayMatch = line.match(/\[Day:\s*(\d+)\]/);
                            if (dayMatch) {
                                dayNumber = parseInt(dayMatch[1]);
                                return;
                            }
                            
                            const timeMatch = line.match(/\[Time:\s*(.+?)\]/);
                            if (timeMatch) {
                                timeOfDay = timeMatch[1].trim();
                                return;
                            }
                            
                            const locationMatch = line.match(/\[Location:\s*(.+?)\]/);
                            if (locationMatch) {
                                location = locationMatch[1].trim();
                                return;
                            }
                            
                            const contextMatch = line.match(/\[Journal Context:\s*(.+?)\]/);
                            if (contextMatch) {
                                journalContext = contextMatch[1].trim();
                                return;
                            }
                            
                            // Check for Korean thought (for multi-line format)
                            const koreanMatch = line.match(/\\[Korean:\\s*(.+?)\\]/);
                            if (koreanMatch && !line.match(/^[A-Za-z]+:/)) {
                                koreanThought = koreanMatch[1].trim();
                                return;
                            }
                            
                            // Check for English expression (for multi-line format)
                            const englishMatch = line.match(/\\[English:\\s*(.+?)\\]/);
                            if (englishMatch && !line.match(/^[A-Za-z]+:/)) {
                                englishExpression = englishMatch[1].trim();
                                return;
                            }
                            
                            // Check for speaker line
                            const speakerMatch = line.match(/^([A-Za-z]+):\\s*(.+)/);
                            console.log('Line:', line, 'Speaker match:', speakerMatch);
                            if (speakerMatch) {
                                // Save previous turn if exists
                                if (currentSpeaker) {
                                    // Determine if this is a practice moment (has Korean and English)
                                    const isPractice = !!(koreanThought && englishExpression);
                                    
                                    const turn = {
                                        id: turnId++,
                                        speaker: currentSpeaker.toLowerCase(),
                                        is_practice: isPractice
                                    };
                                    
                                    if (isPractice) {
                                        // Practice moment - has Korean/English, no audio
                                        turn.korean_thought = koreanThought;
                                        turn.english_hint = englishExpression;
                                        turn.text = null;
                                        turn.audio_url = null;
                                    } else {
                                        // Regular dialogue - has text, needs audio
                                        turn.text = currentText;
                                        turn.korean_thought = null;
                                        turn.english_hint = null;
                                        turn.audio_url = null; // Will be filled during audio generation
                                    }
                                    
                                    dialogue.push(turn);
                                    console.log('Saved turn:', turn);
                                }
                                
                                // Reset for new speaker
                                koreanThought = '';
                                englishExpression = '';
                                currentSpeaker = speakerMatch[1];
                                currentText = speakerMatch[2];
                                
                                // Check if this line has [Practice] marker
                                const hasPracticeMarker = currentText.includes('[Practice]');
                                
                                if (hasPracticeMarker) {
                                    console.log('Found [Practice] marker for', currentSpeaker);
                                    // Remove [Practice] marker from text
                                    currentText = currentText.replace('[Practice]', '').trim();
                                    
                                    // Extract Korean and English from the line
                                    const lineKoreanMatch = currentText.match(/\\[Korean:\\s*(.+?)\\]/);
                                    const lineEnglishMatch = currentText.match(/\\[English:\\s*(.+?)\\]/);
                                    
                                    if (lineKoreanMatch) {
                                        koreanThought = lineKoreanMatch[1].trim();
                                        console.log('Extracted Korean:', koreanThought);
                                        currentText = ''; // Clear text since this is a practice moment
                                    }
                                    if (lineEnglishMatch) {
                                        englishExpression = lineEnglishMatch[1].trim();
                                        console.log('Extracted English:', englishExpression);
                                        currentText = ''; // Clear text since this is a practice moment
                                    }
                                } else {
                                    // Regular dialogue - keep the text as is for audio generation
                                    console.log('Regular dialogue for', currentSpeaker, ':', currentText);
                                }
                            } else if (line && currentSpeaker) {
                                // Continuation of previous speaker's text
                                currentText += ' ' + line;
                            }
                        });
                        
                        // Don't forget the last turn
                        if (currentSpeaker) {
                            const isPractice = !!(koreanThought && englishExpression);
                            const turn = {
                                id: turnId++,
                                speaker: currentSpeaker.toLowerCase(),
                                is_practice: isPractice
                            };
                            
                            if (isPractice) {
                                turn.korean_thought = koreanThought;
                                turn.english_hint = englishExpression;
                                turn.text = null;
                                turn.audio_url = null;
                            } else {
                                turn.text = currentText;
                                turn.korean_thought = null;
                                turn.english_hint = null;
                                turn.audio_url = null;
                            }
                            
                            dialogue.push(turn);
                        }
                        
                        if (dialogue.length > 0) {
                            // Use metadata or defaults
                            const conversationTitle = location ? `Day ${dayNumber || 1}: ${location}` : `Day ${dayNumber || 1}: Conversation ${index + 1}`;
                            const conversationScenario = journalContext || (dialogue[0].text ? dialogue[0].text.substring(0, 50) + '...' : 'Conversation');
                            
                            parsedConversations.push({
                                id: window.generateUUID(),
                                title: conversationTitle,
                                scenario: conversationScenario,
                                day_number: dayNumber || 1,
                                time_of_day: timeOfDay || 'Monday 2:30pm',
                                location: location || 'Casual encounter',
                                journal_context: journalContext || conversationScenario,
                                dialogue: dialogue,
                                is_library: true,
                                // Add character reference
                                character_name: selectedCharacter.name
                            });
                        }
                    });
                    
                    if (parsedConversations.length > 0) {
                        // Log parsing summary
                        parsedConversations.forEach(conv => {
                            const characterTurns = conv.dialogue.filter(t => window.isSelectedCharacter(t.speaker)).length;
                            const otherTurns = conv.dialogue.filter(t => !window.isSelectedCharacter(t.speaker)).length;
                            console.log(`Conversation has ${conv.dialogue.length} total turns: ${characterTurns} ${selectedCharacter?.name || 'character'}, ${otherTurns} other`);
                        });
                        
                        window.displayPreview();
                        window.updateStats();
                        window.showVoiceSelector();
                        window.showStatus('inputStatus', `Successfully parsed ${parsedConversations.length} conversation(s)`, 'success');
                    } else {
                        window.showStatus('inputStatus', 'No valid conversations found. Check format.', 'error');
                    }
                    
                } catch (error) {
                    window.showStatus('inputStatus', 'Error parsing conversations: ' + error.message, 'error');
                }
            }
            
            window.showVoiceSelector = function() {
                const previewSection = document.getElementById('previewSection');
                
                // Collect unique speakers who need voices (non-practice dialogue)
                const speakersNeedingVoices = new Set();
                parsedConversations.forEach(conv => {
                    conv.dialogue.forEach(turn => {
                        if (!turn.is_practice && turn.text) {
                            speakersNeedingVoices.add(turn.speaker);
                        }
                    });
                });
                
                // Create voice selector for each speaker
                let voiceSelectorsHtml = Array.from(speakersNeedingVoices).map(speaker => {
                    const isCharacter = window.isSelectedCharacter(speaker);
                    const displayName = isCharacter ? `${speaker} (character voice)` : speaker;
                    
                    return `
                        <div class="speaker-voice-selector" style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: 600; color: #2d3748;">
                                ${displayName}:
                            </label>
                            <select id="voice-${speaker}" class="voice-select" data-speaker="${speaker}">
                                <option value="random">Random Voice</option>
                                <option value="alloy">Alloy (Neutral)</option>
                                <option value="echo" ${isCharacter && selectedCharacter?.gender === 'male' ? 'selected' : ''}>Echo (Male)</option>
                                <option value="fable">Fable (British Male)</option>
                                <option value="onyx">Onyx (Deep Male)</option>
                                <option value="nova" ${isCharacter && selectedCharacter?.gender === 'female' ? 'selected' : ''}>Nova (Female)</option>
                                <option value="shimmer">Shimmer (Female)</option>
                            </select>
                        </div>
                    `;
                }).join('');
                
                const voiceSelectorHtml = `
                    <div class="voice-selector-card">
                        <h3>Select Voices for Each Speaker</h3>
                        <p style="color: #718096; font-size: 13px; margin-bottom: 15px;">
                            Choose a voice for each speaker. Practice moments don't need voices.
                        </p>
                        <div class="voice-controls">
                            ${voiceSelectorsHtml}
                        </div>
                    </div>
                `;
                
                // Remove existing voice selector if any
                const existingSelector = document.querySelector('.voice-selector-card');
                if (existingSelector) {
                    existingSelector.remove();
                }
                
                // Insert new voice selector before the preview
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = voiceSelectorHtml;
                previewSection.parentNode.insertBefore(tempDiv.firstElementChild, previewSection);
            }
            
            window.onVoiceChange = function() {
                const select = document.getElementById('conversationVoice');
                selectedVoice = select.value;
                const previewBtn = document.getElementById('previewBtn');
                previewBtn.disabled = (selectedVoice === 'random');
            }
            
            window.playVoiceSample = function() {
                const voice = document.getElementById('conversationVoice').value;
                if (voice === 'random') {
                    window.showStatus('saveStatus', 'Please select a specific voice to preview', 'info');
                    return;
                }
                
                const sampleUrl = voiceSamples[voice];
                if (sampleUrl) {
                    const audio = new Audio(sampleUrl);
                    audio.play().catch(error => {
                        console.error('Failed to play audio:', error);
                        window.showStatus('saveStatus', 'Failed to play audio sample', 'error');
                    });
                } else {
                    window.showStatus('saveStatus', 'Sample audio not available for this voice', 'error');
                }
            }
            
            window.displayPreview = function() {
                const preview = document.getElementById('previewSection');
                const actionButtons = document.getElementById('actionButtons');
                
                preview.innerHTML = parsedConversations.map((conv, idx) => `
                    <div class="conversation-preview">
                        <div class="preview-title">📚 ${conv.title}</div>
                        ${conv.day_number || conv.time_of_day || conv.location || conv.journal_context ? `
                            <div style="background: #f7fafc; padding: 10px; border-radius: 6px; margin: 10px 0;">
                                ${conv.day_number ? `<div style="color: #667eea; font-size: 14px; font-weight: bold;">📅 <strong>Day ${conv.day_number}</strong></div>` : ''}
                                ${conv.time_of_day ? `<div style="color: #4a5568; font-size: 13px; margin-top: 4px;">⏰ <strong>Time:</strong> ${conv.time_of_day}</div>` : ''}
                                ${conv.location ? `<div style="color: #4a5568; font-size: 13px; margin-top: 4px;">📍 <strong>Location:</strong> ${conv.location}</div>` : ''}
                                ${conv.journal_context ? `<div style="color: #718096; font-size: 13px; margin-top: 6px; font-style: italic;">📖 <strong>Context:</strong> ${conv.journal_context}</div>` : ''}
                            </div>
                        ` : ''}
                        ${conv.dialogue.map(turn => `
                            <div class="dialogue-turn ${window.isSelectedCharacter(turn.speaker) ? 'user-turn' : 'ai-turn'}">
                                <div class="speaker-name">
                                    ${turn.speaker}
                                    ${!window.isSelectedCharacter(turn.speaker) ? '<span class="audio-badge audio-pending">🔊 Audio pending</span>' : ''}
                                </div>
                                ${turn.text ? `<div class="dialogue-text">${turn.text}</div>` : ''}
                                ${turn.korean_thought ? `
                                    <div class="thought-section">
                                        <div class="korean-thought">💭 ${turn.korean_thought}</div>
                                        ${turn.english_hint ? `<div class="english-expression">→ ${turn.english_hint}</div>` : ''}
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                `).join('');
                
                actionButtons.style.display = 'flex';
            }
            
            window.updateStats = function() {
                const stats = document.getElementById('stats');
                const convCount = document.getElementById('convCount');
                const turnCount = document.getElementById('turnCount');
                const audioCount = document.getElementById('audioCount');
                
                let totalTurns = 0;
                let totalAudio = 0;
                
                parsedConversations.forEach(conv => {
                    totalTurns += conv.dialogue.length;
                    conv.dialogue.forEach(turn => {
                        // Count audio for all speakers with regular dialogue (not practice moments)
                        if (!turn.is_practice && turn.text) {
                            totalAudio++;
                        }
                    });
                });
                
                convCount.textContent = parsedConversations.length;
                turnCount.textContent = totalTurns;
                audioCount.textContent = totalAudio;
                
                stats.style.display = 'flex';
            }
            
            window.saveToSupabase = async function() {
                if (parsedConversations.length === 0) {
                    window.showStatus('saveStatus', 'No conversations to save', 'error');
                    return;
                }
                
                // Collect selected voices for each speaker
                const speakerVoices = {};
                const voiceSelectors = document.querySelectorAll('[id^="voice-"]');
                voiceSelectors.forEach(selector => {
                    const speaker = selector.dataset.speaker;
                    speakerVoices[speaker] = selector.value;
                });
                
                window.showStatus('saveStatus', 'Generating audio and saving...', 'info');
                
                try {
                    // Include speaker voices in the request
                    const requestData = {
                        conversations: parsedConversations,
                        speaker_voices: speakerVoices
                    };
                    
                    const response = await fetch('/api/import/save-batch', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(requestData)
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        window.showStatus('saveStatus', 
                            `✅ Saved ${data.saved_count} conversations with ${data.audio_count} audio files!`, 
                            'success'
                        );
                        
                        // Update preview to show audio is ready
                        document.querySelectorAll('.audio-pending').forEach(badge => {
                            badge.className = 'audio-badge audio-ready';
                            badge.textContent = '🔊 Audio ready';
                        });
                    } else {
                        window.showStatus('saveStatus', 'Error: ' + (data.detail || 'Failed to save'), 'error');
                    }
                } catch (error) {
                    window.showStatus('saveStatus', 'Error: ' + error.message, 'error');
                }
            }
            
            window.clearAll = function() {
                document.getElementById('importText').value = '';
                document.getElementById('previewSection').innerHTML = `
                    <p style="color: #a0aec0; text-align: center; padding: 40px;">
                        Parse conversations to see preview...
                    </p>
                `;
                document.getElementById('actionButtons').style.display = 'none';
                document.getElementById('stats').style.display = 'none';
                parsedConversations = [];
                selectedVoice = 'random';
                // Remove voice selector if it exists
                const voiceSelector = document.querySelector('.voice-selector-card');
                if (voiceSelector) {
                    voiceSelector.remove();
                }
                window.hideStatus('inputStatus');
                window.hideStatus('saveStatus');
            }
            
            window.showStatus = function(elementId, message, type) {
                const element = document.getElementById(elementId);
                element.textContent = message;
                element.className = 'status-message status-' + type;
                element.style.display = 'block';
                
                if (type === 'success') {
                    setTimeout(() => window.hideStatus(elementId), 5000);
                }
            }
            
            window.hideStatus = function(elementId) {
                document.getElementById(elementId).style.display = 'none';
            }
            
            window.generateUUID = function() {
                // Generate a proper UUID v4
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    var r = Math.random() * 16 | 0,
                        v = c == 'x' ? r : (r & 0x3 | 0x8);
                    return v.toString(16);
                });
            }
            
            // Allow Ctrl/Cmd+Enter to parse
            document.getElementById('importText').addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    window.parseConversations();
                }
            });
            
            console.log('Script fully loaded!');
            console.log('window.parseConversations type:', typeof window.parseConversations);
            console.log('window.saveToSupabase type:', typeof window.saveToSupabase);
            console.log('window.clearAll type:', typeof window.clearAll);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


class SaveBatchRequest(BaseModel):
    conversations: List[Dict[str, Any]]
    speaker_voices: Optional[Dict[str, str]] = None  # Maps speaker names to voice selections

@router.post("/save-batch")
async def save_batch_conversations(request: SaveBatchRequest):
    """Save multiple imported conversations with audio generation"""
    try:
        # Ensure infrastructure exists (safe to call multiple times)
        await infrastructure.initialize_infrastructure()
        
        saved_count = 0
        audio_count = 0
        speaker_voices = request.speaker_voices or {}
        
        for conv in request.conversations:
            # Generate audio for all non-practice dialogue turns
            for turn in conv['dialogue']:
                # Check if this is a practice moment (no audio needed)
                if turn.get('is_practice', False):
                    continue
                    
                # Generate audio for regular dialogue
                if turn.get('text'):
                    speaker = turn.get('speaker', '')
                    # Get the voice for this speaker, or use random
                    voice = speaker_voices.get(speaker, 'random')
                    
                    if voice == 'random':
                        # Pick a random voice appropriate for the speaker
                        voice = get_random_voice_for_speaker(speaker)
                    
                    audio_url = await generate_and_store_audio(
                        text=turn['text'],
                        voice=voice,
                        turn_id=f"{conv['id']}_{turn['id']}"
                    )
                    if audio_url:
                        turn['audio_url'] = audio_url
                        turn['voice'] = voice  # Store which voice was used
                        audio_count += 1
            
            # Store conversation in database
            stored = await store_conversation_to_db(conv)
            if stored:
                saved_count += 1
        
        return {
            "status": "success",
            "saved_count": saved_count,
            "audio_count": audio_count
        }
        
    except Exception as e:
        print(f"Error in save_batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_and_store_audio(text: str, voice: str, turn_id: str) -> str:
    """Generate TTS audio and store in Supabase"""
    try:
        # Generate audio using OpenAI TTS
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=1.0
        )
        
        # Store in Supabase
        file_name = f"conversations/{turn_id}_{datetime.utcnow().timestamp()}.mp3"
        
        try:
            # Try to upload to Supabase storage
            result = supabase_client.storage.from_('audio-library').upload(
                file_name,
                response.content,
                file_options={"content-type": "audio/mpeg"}
            )
        except Exception as e:
            # If bucket doesn't exist, create it
            try:
                # Bucket creation is handled by infrastructure.initialize_infrastructure()
                await infrastructure.create_storage_buckets()
                result = supabase_client.storage.from_('audio-library').upload(
                    file_name,
                    response.content,
                    file_options={"content-type": "audio/mpeg"}
                )
            except:
                pass
        
        # Get public URL
        url = supabase_client.storage.from_('audio-library').get_public_url(file_name)
        return url
        
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None


def get_voice_for_speaker(speaker: str, gender: str = None) -> str:
    """Select voice based on gender preference or randomly"""
    import random
    
    # Voice pools by gender
    male_voices = ["echo", "fable", "onyx"]
    female_voices = ["nova", "shimmer"]
    neutral_voices = ["alloy"]
    
    if gender == "male":
        return random.choice(male_voices)
    elif gender == "female":
        return random.choice(female_voices)
    else:
        # Random selection from all voices if no gender specified
        all_voices = male_voices + female_voices + neutral_voices
        return random.choice(all_voices)


async def store_conversation_to_db(conversation: Dict[str, Any]) -> bool:
    """Store conversation in Supabase database"""
    try:
        # Always generate a new ID to avoid duplicates
        conversation_id = str(uuid.uuid4())
        character_name = conversation.get('character_name', '')
        
        # Query the characters table to get the actual character ID
        character_id = None
        if character_name:
            logger.info(f"Looking up character: {character_name}")
            # Query characters table for matching name
            character_result = supabase_client.table('characters').select('id').eq('name', character_name).execute()
            
            if character_result.data and len(character_result.data) > 0:
                character_id = character_result.data[0]['id']
                logger.info(f"Found character ID: {character_id} for {character_name}")
            else:
                logger.warning(f"No character found with name: {character_name}")
                # Try with lowercase as fallback
                character_result = supabase_client.table('characters').select('id').ilike('name', character_name).execute()
                if character_result.data and len(character_result.data) > 0:
                    character_id = character_result.data[0]['id']
                    logger.info(f"Found character ID with case-insensitive search: {character_id}")
                else:
                    logger.error(f"Character not found in database: {character_name}")
                    return False
        
        insert_data = {
            'id': conversation_id,
            'scenario': conversation.get('scenario', 'Imported Conversation'),
            'dialogue': json.dumps(conversation['dialogue']),
            'thoughts': json.dumps([]),  # Empty for imported conversations
            'day_number': conversation.get('day_number', 1),
            'time_of_day': conversation.get('time_of_day'),
            'location': conversation.get('location'),
            'journal_context': conversation.get('journal_context', ''),
            'created_at': datetime.utcnow().isoformat(),
            'is_library': True,  # Mark as library content
            'imported': True,  # Mark as imported
            'character_id': character_id  # Store character ID
        }
        
        # Log the data being inserted
        print(f"Attempting to insert conversation:")
        print(f"  ID: {conversation_id}")
        print(f"  Character Name: {character_name}")
        print(f"  Character ID: {character_id}")
        print(f"  Day: {insert_data['day_number']}")
        print(f"  Time: {insert_data['time_of_day']}")
        print(f"  Location: {insert_data['location']}")
        print(f"  Dialogue count: {len(conversation['dialogue'])}")
        print(f"  Journal context: {insert_data['journal_context'][:50]}..." if insert_data['journal_context'] else "  Journal context: None")
        
        # Store in conversations table with metadata - use upsert to handle conflicts
        result = supabase_client.table('conversations').upsert(
            insert_data,
            on_conflict='id'  # If ID exists, update instead of error
        ).execute()
        
        if result and result.data:
            print(f"✅ Successfully stored conversation {conversation_id}")
            return True
        else:
            print(f"❌ Insert returned no data for conversation {conversation_id}")
            if result:
                print(f"   Result: {result}")
            return False
        
    except Exception as e:
        print(f"❌ Error storing conversation: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False