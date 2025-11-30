from supabase import create_client, Client
from app.config import settings
from typing import Dict, Callable, Optional
import json

class SupabaseRealtimeService:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.channels: Dict[str, any] = {}
    
    def subscribe_to_conversation(
        self, 
        conversation_id: str, 
        callback: Callable,
        event_type: str = "INSERT"
    ):
        """Subscribe to real-time updates for a conversation"""
        channel_name = f"conversation:{conversation_id}"
        
        if channel_name not in self.channels:
            channel = self.client.realtime.channel(channel_name)
            self.channels[channel_name] = channel
        
        channel = self.channels[channel_name]
        
        # Subscribe to message changes
        channel.on(
            "postgres_changes",
            {
                "event": event_type,
                "schema": "public",
                "table": "messages",
                "filter": f"conversation_id=eq.{conversation_id}"
            },
            callback
        )
        
        channel.subscribe()
        return channel
    
    def subscribe_to_reactions(
        self,
        conversation_id: str,
        callback: Callable
    ):
        """Subscribe to reaction updates for messages in a conversation"""
        channel_name = f"conversation:{conversation_id}:reactions"
        
        if channel_name not in self.channels:
            channel = self.client.realtime.channel(channel_name)
            self.channels[channel_name] = channel
        
        channel = self.channels[channel_name]
        
        channel.on(
            "postgres_changes",
            {
                "event": "*",
                "schema": "public",
                "table": "message_reactions",
                "filter": f"message_id=in.(SELECT id FROM messages WHERE conversation_id=eq.{conversation_id})"
            },
            callback
        )
        
        channel.subscribe()
        return channel
    
    def broadcast_typing_indicator(
        self,
        conversation_id: str,
        profile_id: str,
        is_typing: bool
    ):
        """Broadcast typing indicator"""
        channel_name = f"conversation:{conversation_id}"
        
        if channel_name not in self.channels:
            channel = self.client.realtime.channel(channel_name)
            self.channels[channel_name] = channel
            channel.subscribe()
        else:
            channel = self.channels[channel_name]
        
        channel.send({
            "type": "broadcast",
            "event": "typing",
            "payload": {
                "profile_id": profile_id,
                "is_typing": is_typing
            }
        })
    
    def unsubscribe(self, conversation_id: str):
        """Unsubscribe from conversation updates"""
        channel_name = f"conversation:{conversation_id}"
        if channel_name in self.channels:
            self.channels[channel_name].unsubscribe()
            del self.channels[channel_name]
    
    def get_channel(self, conversation_id: str) -> Optional[any]:
        """Get channel for a conversation"""
        channel_name = f"conversation:{conversation_id}"
        return self.channels.get(channel_name)

