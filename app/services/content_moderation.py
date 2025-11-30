import os
from typing import Dict, Optional
from app.config import settings
import httpx

class ContentModerationService:
    """Service for automated content moderation"""
    
    def __init__(self):
        self.enabled = settings.ENABLE_MODERATION
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.moderation_provider = os.getenv("MODERATION_PROVIDER", "openai")  # openai, perspective
    
    async def moderate_text(self, text: str) -> Dict:
        """
        Moderate text content for inappropriate content
        
        Returns:
            {
                "is_safe": bool,
                "confidence": float,
                "categories": dict,
                "flagged": bool,
                "reason": str
            }
        """
        if not self.enabled:
            return {
                "is_safe": True,
                "confidence": 1.0,
                "categories": {},
                "flagged": False,
                "reason": None
            }
        
        if self.moderation_provider == "openai" and self.openai_api_key:
            return await self._moderate_openai(text)
        elif self.moderation_provider == "perspective":
            return await self._moderate_perspective(text)
        else:
            # Basic keyword filtering as fallback
            return self._basic_keyword_filter(text)
    
    async def moderate_image(self, image_url: str) -> Dict:
        """
        Moderate image content
        
        Returns:
            {
                "is_safe": bool,
                "confidence": float,
                "flagged": bool,
                "reason": str
            }
        """
        if not self.enabled:
            return {
                "is_safe": True,
                "confidence": 1.0,
                "flagged": False,
                "reason": None
            }
        
        # For now, return safe (you'd integrate with image moderation API)
        # Options: AWS Rekognition, Google Cloud Vision API, etc.
        return {
            "is_safe": True,
            "confidence": 1.0,
            "flagged": False,
            "reason": None
        }
    
    async def moderate_video(self, video_url: str) -> Dict:
        """
        Moderate video content
        
        Returns:
            {
                "is_safe": bool,
                "confidence": float,
                "flagged": bool,
                "reason": str
            }
        """
        if not self.enabled:
            return {
                "is_safe": True,
                "confidence": 1.0,
                "flagged": False,
                "reason": None
            }
        
        # For now, return safe (you'd integrate with video moderation API)
        # Options: AWS Rekognition Video, Google Cloud Video Intelligence, etc.
        return {
            "is_safe": True,
            "confidence": 1.0,
            "flagged": False,
            "reason": None
        }
    
    async def _moderate_openai(self, text: str) -> Dict:
        """Use OpenAI moderation API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/moderations",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"input": text},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    moderation = result["results"][0]
                    
                    is_flagged = moderation["flagged"]
                    categories = moderation["category_scores"]
                    
                    # Check if any category is above threshold
                    threshold = 0.5
                    flagged_categories = [
                        cat for cat, score in categories.items()
                        if score > threshold
                    ]
                    
                    return {
                        "is_safe": not is_flagged,
                        "confidence": 1.0 - max(categories.values()) if categories else 1.0,
                        "categories": categories,
                        "flagged": is_flagged,
                        "reason": ", ".join(flagged_categories) if flagged_categories else None
                    }
        except Exception as e:
            print(f"OpenAI moderation error: {e}")
        
        return self._basic_keyword_filter(text)
    
    async def _moderate_perspective(self, text: str) -> Dict:
        """Use Google Perspective API"""
        perspective_api_key = os.getenv("PERSPECTIVE_API_KEY")
        if not perspective_api_key:
            return self._basic_keyword_filter(text)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={perspective_api_key}",
                    json={
                        "comment": {"text": text},
                        "languages": ["en"],
                        "requestedAttributes": {
                            "TOXICITY": {},
                            "SEVERE_TOXICITY": {},
                            "IDENTITY_ATTACK": {},
                            "INSULT": {},
                            "PROFANITY": {},
                            "THREAT": {}
                        }
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    scores = result.get("attributeScores", {})
                    
                    # Get max toxicity score
                    max_score = 0.0
                    flagged_categories = []
                    
                    for attr, data in scores.items():
                        score = data["summaryScore"]["value"]
                        if score > 0.5:  # Threshold
                            flagged_categories.append(attr.lower())
                        max_score = max(max_score, score)
                    
                    return {
                        "is_safe": max_score < 0.5,
                        "confidence": 1.0 - max_score,
                        "categories": {k: v["summaryScore"]["value"] for k, v in scores.items()},
                        "flagged": max_score >= 0.5,
                        "reason": ", ".join(flagged_categories) if flagged_categories else None
                    }
        except Exception as e:
            print(f"Perspective API error: {e}")
        
        return self._basic_keyword_filter(text)
    
    def _basic_keyword_filter(self, text: str) -> Dict:
        """Basic keyword-based filtering as fallback"""
        # List of inappropriate keywords (simplified - you'd have a more comprehensive list)
        inappropriate_keywords = [
            # Add your list of inappropriate keywords here
            # This is a basic example
        ]
        
        text_lower = text.lower()
        found_keywords = [kw for kw in inappropriate_keywords if kw in text_lower]
        
        return {
            "is_safe": len(found_keywords) == 0,
            "confidence": 0.7 if len(found_keywords) == 0 else 0.3,
            "categories": {},
            "flagged": len(found_keywords) > 0,
            "reason": f"Inappropriate keywords: {', '.join(found_keywords)}" if found_keywords else None
        }

