CONVERSATION_SYSTEM_PROMPT = """You are an expert at creating hyper-realistic English conversations for Korean speakers learning to express complex thoughts naturally. Your conversations should sound EXACTLY like real native speakers - with fillers, interruptions, natural flow, and authentic expressions.

CRITICAL RULES:
1. Conversations must sound like you're overhearing real people talk - NOT textbook English
2. Include natural fillers: "um", "like", "you know", "I mean", "actually", "basically"
3. Use contractions, incomplete sentences, and natural speech patterns
4. Include emotional and social complexity
5. Characters should interrupt, overlap, or trail off naturally
6. Avoid formal or educational tone at all costs"""


def generate_conversation_prompt(scenario: str, difficulty: int, user_level: str) -> str:
    return f"""Create a realistic conversation for the scenario: "{scenario}"
Difficulty level: {difficulty}/10
User level: {user_level}

The conversation should:
1. Have 4-6 natural turns between speakers
2. Include 2-3 moments where the user needs to express complex thoughts
3. Sound like a real conversation you'd overhear in daily life
4. Include cultural context and natural idioms
5. Have realistic endings (not forced closures)

For each user turn, provide:
- korean_thought: The complex thought in Korean that the user wants to express
- english_hint: The natural way a native speaker would express this thought

Format as JSON:
{{
  "scenario": "scenario description",
  "dialogue": [
    {{
      "id": 1,
      "speaker": "neighbor/friend/colleague",
      "text": "what they say"
    }},
    {{
      "id": 2,
      "speaker": "user",
      "korean_thought": "Korean thought",
      "english_hint": "Natural English expression"
    }}
  ]
}}"""


def generate_thought_challenges_prompt(difficulty: int) -> str:
    return f"""Generate 3 thought challenges for intermediate Korean speakers trying to express themselves naturally in English.

Difficulty: {difficulty}/10

Each challenge should:
1. Be a thought that's easy to think but hard to express naturally
2. Require understanding of cultural/emotional nuance
3. Have multiple valid ways to express it
4. Be immediately useful in real life

Format:
{{
  "challenges": [
    {{
      "korean_thought": "Korean thought",
      "english_expression": "Most natural English expression",
      "difficulty_points": ["why this is challenging"],
      "context": "when you'd use this"
    }}
  ]
}}"""


def evaluate_attempt_prompt(korean_thought: str, expected_english: str, user_transcription: str) -> str:
    return f"""Evaluate how well the user expressed this thought:

Korean thought: "{korean_thought}"
Expected natural expression: "{expected_english}"
User said: "{user_transcription}"

Score from 0-100 based on:
1. Did they convey the core meaning? (40%)
2. How natural does it sound? (30%)
3. Grammar and vocabulary accuracy (20%)
4. Cultural appropriateness (10%)

Return:
{{
  "score": number,
  "feedback": "brief encouraging feedback",
  "improvements": ["specific suggestions"]
}}"""