import os
from typing import Optional, List
from app.config import settings
import httpx

class AIIcebreakerService:
    """Service for generating AI-powered icebreaker messages"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.provider = os.getenv("AI_PROVIDER", "openai")  # openai, gemini, deepseek
    
    async def generate_icebreaker(
        self,
        user_profile: dict,
        match_profile: dict,
        context: Optional[str] = None
    ) -> List[str]:
        """
        Generate AI-powered icebreaker messages based on user profiles
        
        Args:
            user_profile: Current user's profile data
            match_profile: Match's profile data
            context: Optional context (e.g., mutual interests)
        
        Returns:
            List of icebreaker message suggestions
        """
        if self.provider == "openai" and self.openai_api_key:
            return await self._generate_openai_icebreaker(user_profile, match_profile, context)
        elif self.provider == "gemini" and self.gemini_api_key:
            return await self._generate_gemini_icebreaker(user_profile, match_profile, context)
        elif self.provider == "deepseek" and self.deepseek_api_key:
            return await self._generate_deepseek_icebreaker(user_profile, match_profile, context)
        else:
            return self._generate_fallback_icebreakers(user_profile, match_profile)
    
    async def _generate_openai_icebreaker(
        self,
        user_profile: dict,
        match_profile: dict,
        context: Optional[str]
    ) -> List[str]:
        """Generate icebreaker using OpenAI"""
        try:
            prompt = self._build_prompt(user_profile, match_profile, context)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful assistant that generates friendly, engaging icebreaker messages for a dating app. Generate 3-5 creative, personalized icebreaker messages that are appropriate and respectful."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.8,
                        "max_tokens": 300
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    # Parse the response to extract icebreaker messages
                    icebreakers = self._parse_icebreakers(content)
                    return icebreakers[:5]  # Return up to 5
        except Exception as e:
            print(f"OpenAI API error: {e}")
        
        return self._generate_fallback_icebreakers(user_profile, match_profile)
    
    async def _generate_gemini_icebreaker(
        self,
        user_profile: dict,
        match_profile: dict,
        context: Optional[str]
    ) -> List[str]:
        """Generate icebreaker using Google Gemini"""
        try:
            prompt = self._build_prompt(user_profile, match_profile, context)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_api_key}",
                    json={
                        "contents": [{
                            "parts": [{
                                "text": f"You are a helpful assistant that generates friendly, engaging icebreaker messages for a dating app. Generate 3-5 creative, personalized icebreaker messages that are appropriate and respectful.\n\n{prompt}"
                            }]
                        }]
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    icebreakers = self._parse_icebreakers(content)
                    return icebreakers[:5]
        except Exception as e:
            print(f"Gemini API error: {e}")
        
        return self._generate_fallback_icebreakers(user_profile, match_profile)
    
    async def _generate_deepseek_icebreaker(
        self,
        user_profile: dict,
        match_profile: dict,
        context: Optional[str]
    ) -> List[str]:
        """Generate icebreaker using DeepSeek"""
        try:
            prompt = self._build_prompt(user_profile, match_profile, context)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.deepseek_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful assistant that generates friendly, engaging icebreaker messages for a dating app. Generate 3-5 creative, personalized icebreaker messages that are appropriate and respectful."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.8,
                        "max_tokens": 300
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    icebreakers = self._parse_icebreakers(content)
                    return icebreakers[:5]
        except Exception as e:
            print(f"DeepSeek API error: {e}")
        
        return self._generate_fallback_icebreakers(user_profile, match_profile)
    
    def _build_prompt(
        self,
        user_profile: dict,
        match_profile: dict,
        context: Optional[str]
    ) -> str:
        """Build prompt for AI generation"""
        prompt = f"""Generate icebreaker messages for a dating app conversation.

User's profile:
- Name: {user_profile.get('name', 'User')}
- Interests: {', '.join(user_profile.get('hobbies', [])[:5])}
- Bio: {user_profile.get('bio', 'No bio')[:100]}

Match's profile:
- Name: {match_profile.get('name', 'Match')}
- Interests: {', '.join(match_profile.get('hobbies', [])[:5])}
- Bio: {match_profile.get('bio', 'No bio')[:100]}

"""
        if context:
            prompt += f"Context: {context}\n\n"
        
        # Find mutual interests
        user_interests = set(user_profile.get('hobbies', []))
        match_interests = set(match_profile.get('hobbies', []))
        mutual = user_interests & match_interests
        if mutual:
            prompt += f"Mutual interests: {', '.join(list(mutual)[:3])}\n\n"
        
        prompt += "Generate 3-5 creative, personalized icebreaker messages. Make them friendly, engaging, and reference their interests or profile when possible. Format each message on a new line."
        
        return prompt
    
    def _parse_icebreakers(self, content: str) -> List[str]:
        """Parse AI response to extract icebreaker messages"""
        lines = content.split('\n')
        icebreakers = []
        
        for line in lines:
            line = line.strip()
            # Remove numbering (1., 2., etc.)
            if line and (line[0].isdigit() or line.startswith('-')):
                line = line.split('.', 1)[-1].strip()
                line = line.lstrip('- ').strip()
            if line and len(line) > 10 and len(line) < 200:
                icebreakers.append(line)
        
        return icebreakers if icebreakers else self._generate_fallback_icebreakers({}, {})
    
    def _generate_fallback_icebreakers(
        self,
        user_profile: dict,
        match_profile: dict
    ) -> List[str]:
        """Generate fallback icebreakers when AI is unavailable"""
        icebreakers = [
            f"Hey {match_profile.get('name', 'there')}! I noticed we have some things in common. Would love to chat!",
            f"Hi! Your profile caught my attention. How's your day going?",
            f"Hey! I see you're into {', '.join(match_profile.get('hobbies', ['life'])[:2])}. That's awesome!",
            f"Hi {match_profile.get('name', 'there')}! What's the best part of your week been so far?",
            f"Hey! I'd love to get to know you better. What are you passionate about?"
        ]
        
        # Try to personalize based on mutual interests
        user_interests = set(user_profile.get('hobbies', []))
        match_interests = set(match_profile.get('hobbies', []))
        mutual = user_interests & match_interests
        
        if mutual:
            interest = list(mutual)[0]
            icebreakers.insert(0, f"Hey! I see we're both into {interest}. That's cool! What got you into it?")
        
        return icebreakers[:5]

