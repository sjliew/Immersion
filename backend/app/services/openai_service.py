"""OpenAI Service for conversation generation and language processing"""
import json
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self):
        """Initialize OpenAI client with API key from settings"""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key
        )
        self.model = "gpt-4o-mini"  # Using the efficient model for cost optimization
        
    async def generate_conversation(
        self, 
        topic: str,
        difficulty: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Generate a natural conversation between two people.
        
        Args:
            topic: The conversation scenario/topic
            difficulty: Language difficulty level (easy, intermediate, hard)
            
        Returns:
            Structured conversation with Korean thoughts and English expressions
        """
        
        # Example prompt - will be optimized later
        system_prompt = """You are a language learning conversation designer specializing in Korean-to-English expression.
        
Your task is to create realistic, natural conversations that help Korean speakers express their thoughts in English.

Key principles:
1. Use authentic, colloquial American English (not textbook English)
2. Include natural fillers, contractions, and everyday expressions
3. Make Person A (the learner) need to express complex thoughts/feelings
4. Keep conversations practical and relatable to daily life
5. Each response should be 1-3 sentences maximum

Output format must be valid JSON:
{
    "dialogue": [
        {
            "speaker": "Person B",
            "text": "Neighbor's opening line"
        },
        {
            "speaker": "Person A",
            "korean_thought": "What the learner is thinking in Korean",
            "english_expression": "How to express it naturally in English"
        }
    ]
}"""

        user_prompt = f"""Create a conversation about: {topic}
        
Difficulty: {difficulty}
- Easy: Simple responses, basic vocabulary
- Intermediate: Natural expressions, some idioms
- Hard: Complex thoughts, nuanced expressions

The conversation should have 3-4 exchanges total.
Person B starts the conversation.
Person A needs to respond with something that requires thought and tact.

Remember: Output must be valid JSON matching the format specified."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,  # Some creativity but not too random
                max_tokens=800,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            content = response.choices[0].message.content
            conversation_data = json.loads(content)
            
            # Add metadata
            conversation_data["topic"] = topic
            conversation_data["difficulty"] = difficulty
            conversation_data["model_used"] = self.model
            
            logger.info(f"Generated conversation for topic: {topic}")
            return conversation_data
            
        except Exception as e:
            logger.error(f"Failed to generate conversation: {str(e)}")
            # Return a fallback conversation
            return self._get_fallback_conversation(topic)
    
    async def generate_suggestions(
        self,
        user_input: str,
        context: str,
        korean_thought: str = ""
    ) -> List[str]:
        """
        Generate alternative ways to express the same thought.
        
        Args:
            user_input: What the user tried to say
            context: The conversation context
            korean_thought: The original Korean thought (if available)
            
        Returns:
            List of 3 alternative expressions
        """
        
        prompt = f"""Given this context and attempted expression, provide 3 alternative ways to say the same thing.

Context: {context}
User attempted: "{user_input}"
{f'Original thought in Korean: {korean_thought}' if korean_thought else ''}

Provide 3 alternatives that are:
1. More natural/colloquial
2. More polite/formal
3. More casual/friendly

Output as JSON array of strings."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Handle different possible JSON structures
            if isinstance(result, list):
                return result[:3]
            elif isinstance(result, dict) and "suggestions" in result:
                return result["suggestions"][:3]
            elif isinstance(result, dict) and "alternatives" in result:
                return result["alternatives"][:3]
            else:
                # Try to extract any list from the result
                for value in result.values():
                    if isinstance(value, list):
                        return value[:3]
                        
            return ["Could you repeat that?", "Let me think about it", "That's interesting"]
            
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {str(e)}")
            return [
                "Let me think about that differently",
                "Here's another way to put it",
                "What I mean to say is"
            ]
    
    async def evaluate_response(
        self,
        user_response: str,
        expected_response: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluate how well the user's response matches the expected expression.
        
        Args:
            user_response: What the user said
            expected_response: The target expression
            context: Conversation context
            
        Returns:
            Evaluation with score and feedback
        """
        
        prompt = f"""Evaluate this English expression attempt by a Korean speaker.

Expected expression: "{expected_response}"
User said: "{user_response}"
Context: {context if context else 'General conversation'}

Provide evaluation as JSON:
{{
    "score": 0-100 (how close to natural expression),
    "accuracy": "excellent|good|fair|needs_work",
    "feedback": "Brief, encouraging feedback",
    "corrections": ["specific corrections if needed"],
    "well_done": ["what they did well"]
}}

Be encouraging but honest. Focus on communication effectiveness over perfect grammar."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # More consistent evaluation
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            evaluation = json.loads(content)
            
            # Ensure all required fields
            evaluation.setdefault("score", 70)
            evaluation.setdefault("accuracy", "good")
            evaluation.setdefault("feedback", "Keep practicing!")
            evaluation.setdefault("corrections", [])
            evaluation.setdefault("well_done", ["Clear communication"])
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Failed to evaluate response: {str(e)}")
            return {
                "score": 75,
                "accuracy": "good",
                "feedback": "Good effort! Keep practicing",
                "corrections": [],
                "well_done": ["You communicated your thought clearly"]
            }
    
    def _get_fallback_conversation(self, topic: str) -> Dict[str, Any]:
        """Return a fallback conversation if OpenAI fails"""
        return {
            "topic": topic,
            "difficulty": "intermediate",
            "dialogue": [
                {
                    "speaker": "Person B",
                    "text": "Hey, I wanted to talk to you about something. Do you have a minute?"
                },
                {
                    "speaker": "Person A",
                    "korean_thought": "지금은 좀 바쁜데... 하지만 무슨 일인지 궁금하네. 시간을 내야 할 것 같아.",
                    "english_expression": "I'm actually a bit tied up right now, but sure, what's on your mind?"
                },
                {
                    "speaker": "Person B",
                    "text": "It's about the project deadline. I know we agreed on Friday, but I'm wondering if we could push it back a few days?"
                },
                {
                    "speaker": "Person A",
                    "korean_thought": "금요일까지 끝내기로 했는데... 미루면 내 일정도 꼬이는데. 하지만 이유가 있겠지.",
                    "english_expression": "Well, we did commit to Friday, and pushing it back might throw off my schedule too. What's going on that you need more time?"
                }
            ]
        }


# Singleton instance
openai_service = OpenAIService()