from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from app.config.supabase import supabase
from app.middleware.auth import get_current_user
from app.services.supabase_service import supabase_service

router = APIRouter()


class JournalEntry(BaseModel):
    day_number: int
    character_name: str
    character_emoji: str
    character_location: str
    entry_text: str
    time_of_day: str


def get_journal_entry_text(day_number: int, location: str, time_of_day: str, character_name: str, age_group: str, gender: str) -> str:
    """Generate journal entry based on character attributes and progression"""
    
    city = 'New York' if location == 'new-york' else 'LA'
    
    # Customize entries based on character attributes
    # Early days (1-7): Overwhelmed and nervous
    if day_number <= 7:
        if time_of_day == 'morning':
            if age_group == '18-24':
                return f"Day {day_number} in {city}\n\nWoke up in my tiny apartment. Still can't believe I'm actually here. The city sounds are overwhelming - sirens, cars, people. Everyone seems to know exactly where they're going except me.\n\nNeed to grab coffee before my first day at the internship. Hope I can find that place the HR person mentioned..."
            else:  # 25-34
                return f"Day {day_number} in {city}\n\nAnother restless night. This city never sleeps and apparently neither do I now. The pressure of this new job is real. They expect so much and my English feels so... inadequate.\n\nTeam meeting at 9am. Time to pretend I understand everything they're saying..."
        
        elif time_of_day == 'afternoon':
            if gender == 'female':
                return f"Day {day_number} in {city}\n\nLunch alone again. Watching groups of coworkers laughing together. They invited me but I'm scared I won't understand their jokes or know what to say.\n\nWait, someone's approaching my table. It's Sarah from the design team..."
            else:
                return f"Day {day_number} in {city}\n\nThe morning meeting was brutal. So many technical terms, so much crosstalk. I nodded and took notes but honestly caught maybe 60% of it.\n\nNow at lunch and someone from accounting is walking over. Deep breath..."
        
        else:  # evening
            return f"Day {day_number} in {city}\n\nExhausted doesn't even begin to describe it. Every conversation feels like running a mental marathon. But I made it through another day.\n\nMy roommate just knocked. Probably wants to chat about apartment stuff..."
    
    # Finding footing (8-30)
    elif day_number <= 30:
        if time_of_day == 'morning':
            return f"Day {day_number} in {city}\n\nStarting to find my rhythm. The barista at the corner cafe knows my order now - small victory! The morning commute doesn't feel as intimidating.\n\nBig presentation today. I actually have ideas to contribute. Here goes nothing..."
        
        elif time_of_day == 'afternoon':
            return f"Day {day_number} in {city}\n\nToday's team lunch wasn't scary. Actually made a joke that landed! Sure, I practiced it in my head first, but progress is progress.\n\nThe new project manager wants to discuss something. Walking over now..."
        
        else:  # evening
            return f"Day {day_number} in {city}\n\nThree weeks in {city}. The words come easier now. Not easy, but easier. Even called to order takeout without rehearsing first.\n\nNeighbors are having a small gathering. They invited me. Maybe I should go..."
    
    # Building confidence (31-60)
    elif day_number <= 60:
        if time_of_day == 'morning':
            return f"Day {day_number} in {city}, {character_name}'s story\n\n{city} mornings hit different now. I have my spots, my people, my routine. The anxiety is still there but quieter.\n\nLeading today's standup meeting. Six weeks ago this would've terrified me. Now? Just another Tuesday..."
        
        elif time_of_day == 'afternoon':
            return f"Day {day_number}, {character_name} in {city}\n\nClient lunch went great! Explained our proposal without freezing up. They chose us! My accent is still there but who cares? They understood.\n\nTeam's celebrating. David's coming over with coffee..."
        
        else:  # evening
            return f"Day {day_number} in {city}\n\nTwo months here. Got invited to trivia night with the crew. Last month I would've made excuses. Tonight I said yes immediately.\n\nThey're here to pick me up. Time to see if all this practice pays off..."
    
    # Feeling at home (60+)
    else:
        return f"Day {day_number} - {character_name} in {city}\n\n{city} is home now. That's wild to write but it's true. The intimidating skyline is just my morning view. The fast talkers are my friends.\n\nToday someone asked ME for directions. Gave them the full local treatment - 'turn left at the bodega, can't miss it.' Felt like a real {city} {'girl' if gender == 'female' else 'guy'}.\n\nMeeting starting soon. Time to live, not just practice living..."


@router.get("/entry")
async def get_journal_entry(current_user: dict = Depends(get_current_user)):
    """Get personalized journal entry for the current user"""
    try:
        # Get user and character data
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's character_id and character_start_date
        user_result = supabase.client.table('users').select(
            'character_id, character_start_date'
        ).eq('id', user['id']).single().execute()
        
        if not user_result.data or not user_result.data.get('character_id'):
            return {
                "status": "error",
                "message": "No character selected",
                "data": None
            }
        
        # Get character data from characters table
        character_result = supabase.client.table('characters').select(
            'id, name, emoji, location, age_group, gender'
        ).eq('id', user_result.data['character_id']).single().execute()
        
        if not character_result.data:
            return {
                "status": "error",
                "message": "Character not found",
                "data": None
            }
        
        # Combine the data
        character_data = {
            'character_name': character_result.data['name'],
            'character_emoji': character_result.data.get('emoji', '👤'),
            'character_location': character_result.data.get('location', 'new-york'),
            'character_age_group': character_result.data.get('age_group', '25-34'),
            'character_gender': character_result.data.get('gender', 'neutral'),
            'character_start_date': user_result.data.get('character_start_date')
        }
        
        # Calculate day number
        day_number = 1
        if character_data.get('character_start_date'):
            start_date = datetime.fromisoformat(character_data['character_start_date'].replace('Z', '+00:00'))
            day_number = (datetime.now() - start_date).days + 1
        
        # Determine time of day
        current_hour = datetime.now().hour
        if current_hour < 12:
            time_of_day = 'morning'
        elif current_hour < 18:
            time_of_day = 'afternoon'
        else:
            time_of_day = 'evening'
        
        # Generate journal entry
        entry_text = get_journal_entry_text(
            day_number=day_number,
            location=character_data['character_location'],
            time_of_day=time_of_day,
            character_name=character_data['character_name'],
            age_group=character_data['character_age_group'],
            gender=character_data['character_gender']
        )
        
        journal_entry = JournalEntry(
            day_number=day_number,
            character_name=character_data['character_name'],
            character_emoji=character_data['character_emoji'],
            character_location=character_data['character_location'],
            entry_text=entry_text,
            time_of_day=time_of_day
        )
        
        return {
            "status": "success",
            "data": journal_entry.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation-context")
async def get_conversation_context(current_user: dict = Depends(get_current_user)):
    """Get context for the next conversation based on character and progression"""
    try:
        # Get user and character data
        user = await supabase_service.get_user_by_auth_id(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's character_id and character_start_date
        user_result = supabase.client.table('users').select(
            'character_id, character_start_date'
        ).eq('id', user['id']).single().execute()
        
        if not user_result.data or not user_result.data.get('character_id'):
            return {
                "status": "error",
                "message": "No character selected",
                "data": None
            }
        
        # Get character data from characters table
        character_result = supabase.client.table('characters').select(
            'id, name'
        ).eq('id', user_result.data['character_id']).single().execute()
        
        if not character_result.data:
            return {
                "status": "error",
                "message": "Character not found",
                "data": None
            }
        
        character = {
            'character_name': character_result.data['name'],
            'character_location': character_result.data.get('location', 'new-york'),
            'character_age_group': character_result.data.get('age_group', '25-34'),
            'character_gender': character_result.data.get('gender', 'neutral'),
            'character_start_date': user_result.data.get('character_start_date')
        }
        
        # Calculate day number for context
        day_number = 1
        if character.get('character_start_date'):
            start_date = datetime.fromisoformat(character['character_start_date'].replace('Z', '+00:00'))
            day_number = (datetime.now() - start_date).days + 1
        
        # Generate context based on progression
        if day_number <= 7:
            conversation_context = {
                "difficulty": "beginner",
                "scenario": "casual_introduction",
                "emotion": "nervous",
                "topics": ["introductions", "basic_questions", "directions"],
                "character_mood": "overwhelmed but trying"
            }
        elif day_number <= 30:
            conversation_context = {
                "difficulty": "intermediate",
                "scenario": "workplace_interaction",
                "emotion": "cautiously_confident",
                "topics": ["work_projects", "weekend_plans", "recommendations"],
                "character_mood": "finding their footing"
            }
        elif day_number <= 60:
            conversation_context = {
                "difficulty": "advanced",
                "scenario": "social_engagement",
                "emotion": "confident",
                "topics": ["opinions", "storytelling", "humor"],
                "character_mood": "comfortable and engaged"
            }
        else:
            conversation_context = {
                "difficulty": "fluent",
                "scenario": "leadership",
                "emotion": "natural",
                "topics": ["complex_discussions", "mentoring", "cultural_exchange"],
                "character_mood": "at home and thriving"
            }
        
        # Add character-specific context
        conversation_context["character"] = {
            "name": character['character_name'],
            "location": character['character_location'],
            "age_group": character['character_age_group'],
            "gender": character['character_gender'],
            "day_number": day_number
        }
        
        return {
            "status": "success",
            "data": conversation_context
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))