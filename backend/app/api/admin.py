from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
import openai
from app.config import settings
from app.config.supabase import supabase
from app.services.ai.conversation_generator import ConversationGenerator
from app.models import GenerationParams


class GenerateConversationRequest(BaseModel):
    prompt: str
    scenario: Optional[str] = None
    difficulty_level: int = 5


router = APIRouter()

# Initialize OpenAI
client = openai.OpenAI(api_key=settings.openai_api_key)

# Store for current conversation
current_conversation = {}


@router.get("/", response_class=HTMLResponse)
async def admin_interface():
    """Serve the ChatGPT-style admin interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Express Admin - Conversation Studio</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                min-height: 100vh;
            }
            
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .header h1 {
                text-align: center;
                font-size: 2em;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .prompt-section {
                background: white;
                border-radius: 12px;
                padding: 25px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .prompt-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .prompt-title {
                font-size: 1.2em;
                font-weight: 600;
                color: #333;
            }
            
            
            .prompt-input {
                width: 100%;
                min-height: 100px;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                resize: vertical;
                transition: border-color 0.3s;
            }
            
            .prompt-input:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .controls {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }
            
            button {
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .btn-generate {
                background: #667eea;
                color: white;
                flex: 1;
            }
            
            .btn-generate:hover {
                background: #5a67d8;
                transform: translateY(-1px);
            }
            
            .btn-clear {
                background: #e0e0e0;
                color: #666;
            }
            
            .btn-approve {
                background: #48bb78;
                color: white;
            }
            
            .btn-save {
                background: #38a169;
                color: white;
            }
            
            .conversation-section {
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                display: none;
            }
            
            .conversation-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid #f0f0f0;
            }
            
            .conversation-title {
                font-size: 1.3em;
                font-weight: 600;
                color: #333;
            }
            
            .scenario-badge {
                background: #667eea;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 12px;
            }
            
            .dialogue-container {
                max-height: 600px;
                overflow-y: auto;
                padding-right: 10px;
            }
            
            .dialogue-turn {
                margin-bottom: 20px;
            }
            
            .speaker-label {
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                margin-bottom: 8px;
            }
            
            .ai-speaker {
                color: #667eea;
            }
            
            .user-speaker {
                color: #48bb78;
            }
            
            .dialogue-text {
                padding: 15px;
                border-radius: 8px;
                line-height: 1.6;
            }
            
            .ai-text {
                background: #f0f4ff;
                margin-right: 50px;
            }
            
            .user-text {
                background: #f0fff4;
                margin-left: 50px;
            }
            
            .thought-prompt {
                background: #fffbeb;
                border-left: 4px solid #f59e0b;
                padding: 15px;
                margin: 10px 0;
                margin-left: 50px;
                border-radius: 0 8px 8px 0;
            }
            
            .thought-label {
                font-weight: 600;
                color: #92400e;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .korean-thought {
                font-size: 16px;
                color: #451a03;
                margin-bottom: 10px;
                line-height: 1.5;
            }
            
            .english-hint {
                font-size: 14px;
                color: #78716c;
                font-style: italic;
            }
            
            .action-buttons {
                display: flex;
                gap: 10px;
                margin-top: 20px;
                padding-top: 20px;
                border-top: 2px solid #f0f0f0;
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: #666;
            }
            
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .status-message {
                background: #e6fffa;
                border-left: 4px solid #38b2ac;
                padding: 15px;
                margin: 20px 0;
                border-radius: 0 8px 8px 0;
                display: none;
            }
            
            .error-message {
                background: #fff5f5;
                border-left: 4px solid #fc8181;
                color: #c53030;
            }
            
            .success-message {
                background: #f0fff4;
                border-left: 4px solid #48bb78;
                color: #22543d;
            }
            
            .placeholder-text {
                color: #a0aec0;
                font-style: italic;
            }
            
            .audio-indicator {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                padding: 2px 8px;
                background: #edf2f7;
                border-radius: 12px;
                font-size: 11px;
                color: #4a5568;
            }
            
            .audio-ready {
                background: #c6f6d5;
                color: #22543d;
            }
            
            .prompt-history {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-top: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .history-title {
                font-weight: 600;
                margin-bottom: 15px;
                color: #333;
            }
            
            .history-item {
                padding: 10px;
                margin-bottom: 8px;
                background: #f7f7f7;
                border-radius: 6px;
                cursor: pointer;
                transition: background 0.2s;
            }
            
            .history-item:hover {
                background: #e0e0e0;
            }
            
            .history-prompt {
                font-size: 13px;
                color: #333;
                margin-bottom: 4px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            
            .history-meta {
                font-size: 11px;
                color: #888;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 Express Conversation Studio</h1>
        </div>
        
        <div class="container">
            <!-- Prompt Input Section -->
            <div class="prompt-section">
                <div class="prompt-header">
                    <div class="prompt-title">Create Conversation</div>
                </div>
                
                <textarea 
                    id="promptInput" 
                    class="prompt-input" 
                    placeholder="Describe the conversation scenario and specific Korean thoughts to practice...&#10;&#10;Example: Create a job interview conversation where the user needs to express thoughts about work-life balance, career goals, and why they left their previous job. Include natural Korean thoughts that are challenging to express professionally in English."
                ></textarea>
                
                <div class="controls">
                    <button class="btn-generate" onclick="generateConversation()">
                        🚀 Generate Conversation
                    </button>
                    <button class="btn-clear" onclick="clearConversation()">
                        🔄 Clear
                    </button>
                </div>
            </div>
            
            <!-- Status Messages -->
            <div id="statusMessage" class="status-message"></div>
            
            <!-- Prompt History -->
            <div class="prompt-history" id="promptHistorySection" style="display: none;">
                <div class="history-title">📝 Recent Prompts</div>
                <div id="historyList"></div>
            </div>
            
            <!-- Conversation Display Section -->
            <div id="conversationSection" class="conversation-section">
                <div class="conversation-header">
                    <div class="conversation-title">Generated Conversation</div>
                    <div id="scenarioBadge" class="scenario-badge"></div>
                </div>
                
                <div id="dialogueContainer" class="dialogue-container"></div>
                
                <div class="action-buttons">
                    <button class="btn-generate" onclick="regenerate()">
                        🔄 Regenerate
                    </button>
                    <button class="btn-approve" onclick="approveConversation()">
                        ✅ Approve Conversation
                    </button>
                    <button class="btn-save" onclick="saveToSupabase()" style="display: none;" id="saveBtn">
                        💾 Generate Audio & Save to Supabase
                    </button>
                </div>
            </div>
        </div>
        
        <script>
            let currentConversation = null;
            let isApproved = false;
            let promptHistory = [];
            
            async function generateConversation() {
                const prompt = document.getElementById('promptInput').value;
                
                if (!prompt.trim()) {
                    showStatus('Please enter a prompt to generate a conversation.', 'error');
                    return;
                }
                
                // Show loading
                document.getElementById('conversationSection').style.display = 'none';
                showStatus('Generating conversation...', 'info');
                
                try {
                    const response = await fetch('/api/admin/generate-single', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            prompt: prompt,
                            difficulty_level: 5  // Fixed intermediate level
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        currentConversation = data.conversation;
                        isApproved = false;
                        displayConversation(data.conversation);
                        showStatus('Conversation generated successfully!', 'success');
                        document.getElementById('saveBtn').style.display = 'none';
                        
                        // Save to local prompt history
                        promptHistory.unshift({
                            prompt: prompt,
                            scenario: data.conversation.scenario,
                            timestamp: new Date().toLocaleString()
                        });
                        // Keep only last 10 prompts
                        promptHistory = promptHistory.slice(0, 10);
                        localStorage.setItem('promptHistory', JSON.stringify(promptHistory));
                        updatePromptHistory();
                    } else {
                        showStatus('Error: ' + (data.detail || 'Failed to generate'), 'error');
                    }
                } catch (error) {
                    showStatus('Error: ' + error.message, 'error');
                }
            }
            
            function displayConversation(conversation) {
                const container = document.getElementById('dialogueContainer');
                const section = document.getElementById('conversationSection');
                
                // Set scenario badge
                document.getElementById('scenarioBadge').textContent = conversation.scenario || 'General';
                
                // Clear and build dialogue
                container.innerHTML = '';
                
                conversation.dialogue.forEach((turn, index) => {
                    const turnDiv = document.createElement('div');
                    turnDiv.className = 'dialogue-turn';
                    
                    if (turn.speaker === 'user') {
                        // User turn with thought prompt
                        turnDiv.innerHTML = `
                            <div class="speaker-label user-speaker">👤 USER</div>
                            ${turn.korean_thought ? `
                                <div class="thought-prompt">
                                    <div class="thought-label">
                                        💭 Express this thought in English:
                                    </div>
                                    <div class="korean-thought">${turn.korean_thought}</div>
                                    ${turn.english_hint ? `
                                        <div class="english-hint">💡 Hint: ${turn.english_hint}</div>
                                    ` : ''}
                                </div>
                            ` : `
                                <div class="dialogue-text user-text">
                                    <span class="placeholder-text">[User responds naturally to the conversation]</span>
                                </div>
                            `}
                        `;
                    } else {
                        // AI partner turn
                        const speakerEmoji = {
                            'neighbor': '🏠',
                            'colleague': '💼', 
                            'friend': '👋',
                            'stranger': '🚶',
                            'interviewer': '👔'
                        }[turn.speaker] || '🤖';
                        
                        turnDiv.innerHTML = `
                            <div class="speaker-label ai-speaker">
                                ${speakerEmoji} ${turn.speaker.toUpperCase()}
                                ${turn.audio_url ? '<span class="audio-indicator audio-ready">🔊 Audio</span>' : ''}
                            </div>
                            <div class="dialogue-text ai-text">
                                ${turn.text || '<em>No dialogue</em>'}
                            </div>
                        `;
                    }
                    
                    container.appendChild(turnDiv);
                });
                
                // Show conversation section
                section.style.display = 'block';
            }
            
            function regenerate() {
                generateConversation();
            }
            
            function clearConversation() {
                document.getElementById('promptInput').value = '';
                document.getElementById('conversationSection').style.display = 'none';
                currentConversation = null;
                isApproved = false;
                hideStatus();
            }
            
            function approveConversation() {
                if (!currentConversation) {
                    showStatus('No conversation to approve.', 'error');
                    return;
                }
                
                isApproved = true;
                document.getElementById('saveBtn').style.display = 'inline-block';
                showStatus('Conversation approved! You can now generate audio and save to Supabase.', 'success');
            }
            
            async function saveToSupabase() {
                if (!currentConversation || !isApproved) {
                    showStatus('Please approve the conversation first.', 'error');
                    return;
                }
                
                showStatus('Generating audio and saving to Supabase...', 'info');
                
                try {
                    const response = await fetch('/api/admin/save-single', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            conversation: currentConversation
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        showStatus(`Successfully saved! Generated ${data.audio_count} audio files.`, 'success');
                        // Update display with audio indicators
                        if (data.conversation) {
                            currentConversation = data.conversation;
                            displayConversation(data.conversation);
                        }
                    } else {
                        showStatus('Error: ' + (data.detail || 'Failed to save'), 'error');
                    }
                } catch (error) {
                    showStatus('Error: ' + error.message, 'error');
                }
            }
            
            function showStatus(message, type = 'info') {
                const statusDiv = document.getElementById('statusMessage');
                statusDiv.textContent = message;
                statusDiv.className = 'status-message';
                
                if (type === 'error') {
                    statusDiv.className += ' error-message';
                } else if (type === 'success') {
                    statusDiv.className += ' success-message';
                }
                
                statusDiv.style.display = 'block';
                
                if (type === 'success') {
                    setTimeout(hideStatus, 5000);
                }
            }
            
            function hideStatus() {
                document.getElementById('statusMessage').style.display = 'none';
            }
            
            // Allow Enter key to generate (with Ctrl/Cmd)
            document.getElementById('promptInput').addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    generateConversation();
                }
            });
            
            // Load prompt history from localStorage
            function loadPromptHistory() {
                const saved = localStorage.getItem('promptHistory');
                if (saved) {
                    promptHistory = JSON.parse(saved);
                    updatePromptHistory();
                }
            }
            
            // Update prompt history display
            function updatePromptHistory() {
                const historyList = document.getElementById('historyList');
                const historySection = document.getElementById('promptHistorySection');
                
                if (promptHistory.length === 0) {
                    historySection.style.display = 'none';
                    return;
                }
                
                historySection.style.display = 'block';
                historyList.innerHTML = promptHistory.map((item, index) => `
                    <div class="history-item" onclick="reusePrompt(${index})">
                        <div class="history-prompt">${item.prompt}</div>
                        <div class="history-meta">${item.scenario} • ${item.timestamp}</div>
                    </div>
                `).join('');
            }
            
            // Reuse a prompt from history
            function reusePrompt(index) {
                const item = promptHistory[index];
                document.getElementById('promptInput').value = item.prompt;
                showStatus('Prompt loaded from history. Click Generate to create a new conversation.', 'info');
            }
            
            // Initialize on load
            loadPromptHistory();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.post("/generate-single")
async def generate_single_conversation(request: GenerateConversationRequest):
    """Generate a single conversation based on prompt"""
    try:
        generator = ConversationGenerator()
        
        # Create params from request
        params = GenerationParams(
            user_id=f"admin_{uuid.uuid4()}",
            scenario=request.scenario or request.prompt[:50],  # Use first 50 chars as scenario
            difficulty_level=request.difficulty_level,
            context=request.prompt  # Full prompt as context
        )
        
        # Generate conversation
        conversation = await generator.generate_conversation(params)
        
        # Add the prompt to the conversation for tracking
        conversation['prompt_used'] = request.prompt
        conversation['generated_at'] = datetime.utcnow().isoformat()
        
        return {
            "status": "success",
            "conversation": conversation
        }
        
    except Exception as e:
        print(f"Error in generate_single: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-single")
async def save_single_conversation(conversation: Dict[str, Any]):
    """Save a single conversation with audio generation"""
    try:
        audio_count = 0
        
        # Ensure storage buckets exist
        await ensure_audio_buckets()
        
        # Generate audio for AI responses
        for turn in conversation['dialogue']:
            if turn.get('speaker') != 'user' and turn.get('text'):
                if not turn.get('audio_url'):
                    # Generate TTS audio
                    audio_url = await generate_and_store_audio(
                        text=turn['text'],
                        voice=get_voice_for_speaker(turn['speaker']),
                        turn_id=turn.get('id', str(uuid.uuid4()))
                    )
                    turn['audio_url'] = audio_url
                    audio_count += 1
        
        # Store in database
        stored = await store_conversation_to_db(conversation)
        
        return {
            "status": "success",
            "saved": stored,
            "audio_count": audio_count,
            "conversation": conversation  # Return updated conversation with audio URLs
        }
        
    except Exception as e:
        print(f"Error in save_single: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def ensure_audio_buckets():
    """Create Supabase storage buckets if they don't exist"""
    try:
        # This is a simplified version - in production you'd check if buckets exist
        # For now, we'll assume they exist or handle the error gracefully
        pass
    except Exception as e:
        print(f"Error ensuring buckets: {e}")


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
        
        # Store in Supabase (create bucket if needed)
        file_name = f"conversations/{turn_id}_{datetime.utcnow().timestamp()}.mp3"
        
        try:
            # Try to upload to Supabase storage
            result = supabase.storage.from_('audio-library').upload(
                file_name,
                response.content,
                file_options={"content-type": "audio/mpeg"}
            )
        except Exception as e:
            # If bucket doesn't exist, create it
            try:
                supabase.storage.create_bucket('audio-library', public=True)
                result = supabase.storage.from_('audio-library').upload(
                    file_name,
                    response.content,
                    file_options={"content-type": "audio/mpeg"}
                )
            except:
                # Bucket might already exist or other error
                pass
        
        # Get public URL
        url = supabase.storage.from_('audio-library').get_public_url(file_name)
        
        return url
        
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None


def get_voice_for_speaker(speaker: str) -> str:
    """Map speaker type to OpenAI voice"""
    voice_map = {
        "neighbor": "echo",
        "colleague": "alloy", 
        "friend": "nova",
        "stranger": "fable",
        "interviewer": "onyx"
    }
    return voice_map.get(speaker, "nova")


async def store_conversation_to_db(conversation: Dict[str, Any]) -> bool:
    """Store conversation in Supabase database"""
    try:
        # Store in conversations table with prompt
        result = supabase.client.table('conversations').insert({
            'id': conversation.get('id', str(uuid.uuid4())),
            'scenario': conversation.get('scenario', 'General'),
            'difficulty_level': conversation.get('difficulty_level', 5),
            'dialogue': json.dumps(conversation['dialogue']),
            'thoughts': json.dumps(conversation.get('thoughts', [])),
            'prompt_used': conversation.get('prompt_used', ''),  # Store the prompt
            'created_at': datetime.utcnow().isoformat(),
            'is_library': True  # Mark as library content
        }).execute()
        
        return True
        
    except Exception as e:
        print(f"Error storing conversation: {e}")
        # Table might not exist yet
        return False