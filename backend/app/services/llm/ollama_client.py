import httpx
from typing import Optional, Dict, Any
import json

from app.config import get_settings


class OllamaClient:
    """Ollama APIクライアント"""
    
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> Optional[str]:
        """
        テキスト生成
        
        Args:
            prompt: プロンプト
            system: システムプロンプト
            temperature: 温度パラメータ
            max_tokens: 最大トークン数
        
        Returns:
            生成されたテキスト
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                return result.get("response", "")
                
        except Exception as e:
            print(f"Ollama generate error: {e}")
            return None
    
    async def chat(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.3,
    ) -> Optional[str]:
        """
        チャット形式で生成
        
        Args:
            messages: [{"role": "user/assistant/system", "content": "..."}]
            temperature: 温度パラメータ
        
        Returns:
            生成されたテキスト
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                return result.get("message", {}).get("content", "")
                
        except Exception as e:
            print(f"Ollama chat error: {e}")
            return None
    
    async def is_available(self) -> bool:
        """Ollamaが利用可能か確認"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False
    
    async def pull_model(self) -> bool:
        """モデルをダウンロード"""
        url = f"{self.base_url}/api/pull"
        
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    url,
                    json={"name": self.model},
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Model pull error: {e}")
            return False
