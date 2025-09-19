import json
import random
import openai
from typing import List, Dict, Any
from app.config import settings
from app.models import GenerationParams, Conversation, ThoughtChallenge
from .prompt_templates import (
    CONVERSATION_SYSTEM_PROMPT,
    generate_conversation_prompt,
    generate_thought_challenges_prompt,
    evaluate_attempt_prompt
)

# Initialize OpenAI
openai.api_key = settings.openai_api_key


class ConversationGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
    
    async def generate_conversation(self, params: GenerationParams) -> Dict[str, Any]:
        """Generate a realistic conversation using GPT-4"""
        try:
            # Use GPT-4 for high-quality conversation generation
            # Check if we have a custom prompt in context
            if params.context:
                # Use the full custom prompt directly
                json_prompt = params.context + """
                
                Return the conversation in this exact JSON format:
                {
                  "scenario": "brief scenario description",
                  "dialogue": [
                    {
                      "id": 1,
                      "speaker": "neighbor/friend/colleague/stranger/interviewer",
                      "text": "what they say"
                    },
                    {
                      "id": 2,
                      "speaker": "user",
                      "korean_thought": "Korean thought the user wants to express",
                      "english_hint": "Natural English expression"
                    }
                  ]
                }
                
                IMPORTANT: Return ONLY valid JSON, no other text."""
            else:
                # Fall back to template for non-admin usage
                json_prompt = generate_conversation_prompt(
                    scenario=params.scenario or self._get_random_scenario(),
                    difficulty=params.difficulty_level,
                    user_level="intermediate"
                ) + "\n\nIMPORTANT: Return your response as valid JSON only, no other text."
            
            completion = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": CONVERSATION_SYSTEM_PROMPT + "\nAlways return valid JSON."},
                    {
                        "role": "user",
                        "content": json_prompt
                    }
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            # Parse JSON from response
            response_text = completion.choices[0].message.content
            # Clean up response if needed
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            result = json.loads(response_text.strip())
            
            # Generate additional thought challenges
            thoughts = await self.generate_thoughts(params.difficulty_level)
            
            return {
                "id": self._generate_uuid(),
                "user_id": params.user_id,
                "scenario": result.get("scenario"),
                "difficulty_level": params.difficulty_level,
                "dialogue": result.get("dialogue", []),
                "thoughts": thoughts,
                "completed": False
            }
            
        except Exception as e:
            print(f"Error generating conversation: {e}")
            raise Exception("Failed to generate conversation")
    
    async def generate_thoughts(self, difficulty: int) -> List[Dict[str, Any]]:
        """Generate thought challenges using GPT-3.5 for cost optimization"""
        try:
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": CONVERSATION_SYSTEM_PROMPT + "\nAlways return valid JSON."},
                    {"role": "user", "content": generate_thought_challenges_prompt(difficulty) + "\n\nReturn as valid JSON only."}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            response_text = completion.choices[0].message.content
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            result = json.loads(response_text.strip())
            challenges = result.get("challenges", [])
            
            # Add IDs to challenges
            for challenge in challenges:
                challenge["id"] = self._generate_uuid()
            
            return challenges
            
        except Exception as e:
            print(f"Error generating thoughts: {e}")
            return []
    
    async def evaluate_attempt(
        self,
        korean_thought: str,
        expected_english: str,
        user_transcription: str
    ) -> Dict[str, Any]:
        """Evaluate user's attempt at expressing a thought"""
        try:
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an encouraging English teacher."},
                    {
                        "role": "user",
                        "content": evaluate_attempt_prompt(
                            korean_thought,
                            expected_english,
                            user_transcription
                        )
                    }
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(completion.choices[0].message.content)
            
        except Exception as e:
            print(f"Error evaluating attempt: {e}")
            return {
                "score": 70,
                "feedback": "Good effort! Keep practicing.",
                "improvements": []
            }
    
    def _get_random_scenario(self) -> str:
        """Get a random conversation scenario"""
        scenarios = [
            "Complaining to neighbor about noise",
            "Asking colleague for deadline extension",
            "Explaining why you're late to a friend",
            "Negotiating price at a store",
            "Making small talk with stranger at coffee shop",
            "Apologizing for a mistake at work",
            "Giving feedback to a service provider",
            "Declining a social invitation politely",
            "Asking for clarification in a meeting",
            "Expressing disagreement diplomatically"
        ]
        return random.choice(scenarios)
    
    def _generate_uuid(self) -> str:
        """Generate a UUID"""
        import uuid
        return str(uuid.uuid4())


# Create global instance
conversation_generator = ConversationGenerator()