# CLAUDE Development Rules

## Core Principles
1. **NEVER BE LAZY** - Always find root causes and implement proper solutions
2. **SIMPLICITY FIRST** - Every change should be minimal and impact the least code possible
3. **NO TEMPORARY FIXES** - You are a senior developer. Do it right the first time.

## Development Workflow

### 1. Planning Phase
- First, thoroughly read and understand the codebase
- Identify all relevant files that need changes
- Create a detailed plan in `tasks/todo.md` with:
  - Clear, actionable todo items
  - Small, incremental tasks
  - Each task should be independently testable

### 2. Verification Phase
- Present the plan to the user for approval
- Wait for confirmation before proceeding
- Ask clarifying questions if requirements are unclear

### 3. Implementation Phase
- Work through todo items systematically
- Mark items as complete as you go
- After EACH change, provide a high-level explanation
- Keep changes minimal and focused

### 4. Documentation Phase
- Add a review section to todo.md
- Summary of all changes made
- Document any important decisions
- Note any potential future improvements

## Code Quality Standards

### Bug Fixes
- **ALWAYS** find the root cause
- Never apply band-aid solutions
- Test edge cases
- Verify the fix doesn't break other features

### Code Changes
- Each change should be atomic and minimal
- Avoid cascading modifications
- Preserve existing functionality
- Maintain consistent code style
- When creating the code with bash command, not only show the code but what this code is for in our project, and where is this

### Testing
- Manually verify each change works
- Check for regressions
- Test error cases
- Validate user flows end-to-end

## Communication Rules

### Progress Updates
- Provide clear, concise explanations
- Focus on what changed and why
- Mention any risks or considerations
- Be transparent about challenges

### Problem Solving
- If stuck, analyze systematically
- Document the debugging process
- Consider multiple solutions
- Choose the simplest approach


## File Organization

### Todo Management
- Always use `tasks/todo.md` for planning
- Format:
  ```markdown
  # Task: [Description]
  
  ## Todo
  - [ ] Task 1
  - [ ] Task 2
  - [x] Completed task
  
  ## Review
  Summary of changes...
  ```

### Code Structure
- Keep related changes together
- Don't scatter modifications
- Maintain clear separation of concerns
- Follow existing patterns in codebase

## Error Handling

### When Things Go Wrong
1. Stop and analyze the error
2. Read error messages carefully
3. Check logs and stack traces
4. Find the actual source, not symptoms
5. Implement proper error handling

### Never Do
- Apply quick hacks
- Ignore edge cases
- Leave TODO comments without tickets
- Make assumptions about user intent
- Skip validation or error handling

## Performance Considerations

- Optimize only when necessary
- Measure before optimizing
- Keep solutions simple
- Document performance decisions
- Consider mobile constraints

## Security Mindset

- Never expose sensitive data
- Validate all inputs
- Sanitize user data
- Use proper authentication
- Follow security best practices

## Remember
**You are a SENIOR DEVELOPER. Act like one.**
- Take pride in your work
- Write code you'd want to maintain
- Think before you code
- Test what you build
- Document what's not obvious

---
*This file serves as the persistent rulebook for all development work in this project.*

# Express App: Conversation Generation Guidelines

## Core Principle
**Generate conversations that present thoughts Korean speakers naturally have in Korean, but find challenging to express naturally in English.**

## The Learning Mechanism
```
Korean Thought (what they're thinking) → English Expression (how natives would say it)
```
The app teaches users to bridge this specific gap through practice.

## Conversation Requirements

### 1. **Native-Level English Only**
- All English expressions should be 100% native level
- Use natural American English as actually spoken
- Include contractions, fillers, and colloquialisms
- No simplified or learner English

### 2. **Authentic Korean Thoughts**
The Korean thoughts should be:
- **Real thoughts people actually have** in daily life
- **Occasional but recurring** situations
- **Not necessarily complex** - can be simple thoughts that are just hard to express naturally in English

### 3. **The Challenge Gap**
Focus on thoughts that are:
- Easy to express in Korean
- Challenging to express naturally in English
- Common enough to be practical

## What Makes a Thought "Challenging"

Not about complexity, but about:
- **Cultural expression differences** (Korean indirectness vs American directness)
- **Idiomatic gaps** (expressions that don't translate literally)
- **Contextual appropriateness** (knowing what natives would actually say)
- **Natural flow** (how to start, transition, or end statements naturally)

## OpenAI Prompt Template

```python
"""Generate conversations for Korean speakers practicing natural English expression.

Requirements:
1. Person A receives Korean thoughts they commonly have
2. These thoughts should be challenging to express naturally in English
3. All English must be 100% native-level American English
4. Focus on the gap between how Koreans think and how Americans express

The korean_thought should be:
- Authentic thoughts Koreans actually have
- Common enough to be practical
- Challenging to express naturally in English (not about vocabulary)

The english_expression should be:
- Exactly how native Americans would say it
- Natural with appropriate fillers and casual language
- Context-appropriate (work, social, service situations)

Output JSON format:
{
    "dialogue": [
        {
            "speaker": "Person B",
            "text": "[Native English that sets up situation]"
        },
        {
            "speaker": "Person A", 
            "korean_thought": "[Authentic Korean thought]",
            "english_expression": "[How natives would actually say it]"
        }
    ]
}"""
```

## Key Focus Areas

1. **Starting conversations** - How to naturally begin
2. **Soft disagreement** - Pushing back politely  
3. **Changing topics** - Smooth transitions
4. **Showing uncertainty** - Hedging and softening
5. **Reacting naturally** - Authentic responses
6. **Ending conversations** - Natural closings

## What to Avoid

❌ **Don't generate:**
- Overly complex philosophical thoughts
- Rare situations users won't encounter
- Textbook/formal English
- Direct word-for-word translations
- Thoughts that are easy to express in both languages

✅ **Do generate:**
- Daily life situations
- Common but tricky expressions
- Natural spoken English
- Culturally appropriate responses
- Thoughts with no direct English equivalent

## Success Metric

A conversation is successful when:
1. Korean users think "Yes, I have this thought often"
2. The English expression makes them go "Oh, so that's how you say it!"
3. They can immediately use it in real life

---

# Project Requirements Document: Express

## 1. Executive Summary
Express (ConvoFlow) is a mobile-first language learning application designed for intermediate/advanced Korean speakers who need to practice articulating complex thoughts in English. Unlike traditional language apps that focus on vocabulary or grammar, Express presents users with contextually relevant thoughts they must express in English during AI-powered conversations.

**Core Value Proposition**: Help users build neural pathways for expressing sophisticated thoughts they already have in Korean but struggle to articulate naturally in English.

## 2. User Personas & Use Cases

### Primary Personas:

#### 1. Inseok (Recent Arrival)
- Just moved to US for tech job
- Can read/understand English perfectly
- Freezes when expressing opinions in meetings
- **Needs**: Professional communication confidence

#### 2. Seonmi (Working Professional)
- 2-3 years in US tech company
- Handles basic work communication
- Struggles with nuanced expression and persuasion
- **Needs**: Advanced articulation skills

#### 3. Jihee (Job Seeker)
- In US, seeking employment
- Strong technical English
- Lacks conversational fluency for interviews
- **Needs**: Interview and networking practice

### Core User Flow:
1. User opens app → sees Home Tab with conversation stats
2. Starts new conversation with AI partner
3. Receives contextually relevant "thought prompts" to express
4. Practices articulating these thoughts via voice
5. Saves challenging phrases/expressions for later review
6. Tracks progress through articulation quality metrics

## 3. Functional Requirements

### 3.1 Home Tab (Practice Screen)
**Stats Dashboard:**
- Total conversations completed
- Minutes practiced this week
- Thoughts successfully articulated
- Current streak

**Start Conversation (Primary CTA):**
- One-tap to begin
- Shows today's conversation topic/context
- Indicates difficulty level

**Recent Progress:**
- Last 3 conversations summary
- Improvement indicators

### 3.2 Conversation Engine (Core Feature)

**Pre-Conversation Setup:**
- Context selection (work meeting, casual chat, interview, etc.)
- Difficulty calibration
- Optional: "What's on your mind today?"

**During Conversation:**
- AI partner provides contextual setup
- User receives thought prompt (the key innovation)
- Voice recording with visual feedback
- Real-time transcription
- Option to retry articulation
- Save phrase/expression feature

**Thought Prompt Requirements:**
- Contextually relevant to conversation
- Slightly above user's current level
- Emotionally resonant
- Requires idiomatic/professional expression

**Post-Conversation:**
- Performance summary
- Phrases successfully used
- Areas for improvement
- Option to rate thought relevance

### 3.3 Saved Expressions Tab
**Organization:**
- By conversation date
- By category (professional, emotional, cultural)
- By mastery level

**Review Features:**
- Native speaker pronunciation
- Alternative expressions
- Usage examples
- Personal notes

### 3.4 Profile Tab
**User Information:**
- Basic profile
- Language goals
- Professional context

**Progress Tracking:**
- Overall statistics
- Improvement graphs
- Achievement milestones

**Settings:**
- Notification preferences
- Difficulty preferences
- Voice settings

## 4. Technical Requirements

### 4.1 Core Technologies
- **Frontend**: React Native (iOS/Android)
- **Backend**: Python FastAPI
- **Database**: Supabase (PostgreSQL + Auth)
- **AI/ML**: OpenAI GPT-4 API for conversation generation
- **Speech**: OpenAI Whisper for Speech-to-Text
- **TTS**: OpenAI TTS for audio generation
- **Storage**: Supabase Storage for audio recordings
- **Authentication**: Supabase Auth

### 4.2 AI Integration Architecture
```
User Profile + Context → Thought Generation Engine → Difficulty Calibrator → Conversation Flow
                              ↑                           ↑
                     Performance Feedback ←──────── Speech Analysis
```

### 4.3 Current Implementation Status
- ✅ Backend API structure (FastAPI)
- ✅ Frontend navigation structure (React Native/Expo)
- ✅ Basic UI components
- 🚧 Supabase authentication integration
- 🚧 Conversation generation with OpenAI
- ⏳ Audio recording and speech processing
- ⏳ Progress tracking and analytics
- ⏳ Expression management system