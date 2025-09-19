# Task: Core Functionality Implementation

## Objective
Implement all core functionality for Express app: authentication, conversation generation, audio recording/playback, speech-to-text, text-to-speech, and expression management. Use basic prompts that work, leaving room for optimization later.

## Todo

### Phase 1: Supabase Authentication
- [ ] Update backend auth middleware to use Supabase
- [ ] Create frontend Supabase service
- [ ] Update AuthScreen for Supabase login
- [ ] Pass auth tokens in API calls

### Phase 2: Connect Frontend to Backend
- [ ] Update frontend API client with auth headers
- [ ] Wire up conversation generation
- [ ] Connect user progress tracking
- [ ] Replace all mock data

### Phase 3: Audio Recording
- [ ] Install audio recording libraries
- [ ] Implement recording service
- [ ] Add hold-to-record functionality
- [ ] Upload audio to Supabase Storage

### Phase 4: Speech Processing
- [ ] Connect Whisper transcription
- [ ] Generate TTS for conversations
- [ ] Implement audio playback
- [ ] Store audio URLs

### Phase 5: Expression Management
- [ ] Implement save expression flow
- [ ] Connect saved expressions screen
- [ ] Add search/filter functionality
- [ ] Enable audio playback for saved expressions

### Phase 6: Progress Tracking
- [ ] Track practice metrics
- [ ] Update progress displays
- [ ] Connect streak tracking
- [ ] Display real statistics

## Implementation Notes
- Using basic prompts for now - optimize later
- All prompts centralized in prompt_templates.py
- Focus on functionality over optimization
- Leave room for future prompt engineering

## Review
(To be completed)

## Status
🚧 In Progress

---
*Created: 2025-01-06*