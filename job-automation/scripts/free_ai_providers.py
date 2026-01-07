"""
🆓 FREE AI PROVIDERS - Zero-Cost AI for Job Automation

Supports multiple FREE AI providers with automatic fallback:
1. Groq (FREE - Llama 3, Mixtral, Gemma) - FASTEST
2. Google Gemini (FREE tier - 15 requests/min)
3. HuggingFace Inference (FREE - many models)
4. Together.ai (FREE $25 credits)
5. Cohere (FREE tier - 100 calls/min)
6. Mistral AI (FREE tier available)
7. Ollama (FREE - local, no internet needed)
8. OpenRouter (FREE tier with many models)

NO API KEYS NEEDED for some providers!

Author: AutoApply Automation
"""

import os
import sys
import json
import logging
import re
import time
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class FreeAIProvider(ABC):
    """Base class for free AI providers."""
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass


class GroqProvider(FreeAIProvider):
    """
    🚀 Groq - FASTEST FREE AI
    - Free tier: Very generous
    - Models: Llama 3 70B, Mixtral, Gemma
    - Speed: ~500 tokens/sec (10x faster than GPT-4)
    
    Get free key: https://console.groq.com/keys
    """
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY', '')
        self.model = 'llama-3.3-70b-versatile'  # Best free model
        
    @property
    def name(self) -> str:
        return "Groq (Llama 3.3 70B)"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        try:
            import requests
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self.model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': max_tokens,
                    'temperature': 0.7
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            logging.warning(f"Groq error: {response.status_code}")
        except Exception as e:
            logging.warning(f"Groq failed: {e}")
        return None


class GeminiProvider(FreeAIProvider):
    """
    🌟 Google Gemini - FREE tier
    - Free: 15 requests/minute, 1500/day
    - Models: gemini-1.5-flash (fast), gemini-1.5-pro
    
    Get free key: https://makersuite.google.com/app/apikey
    """
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY', '')
        self.model = 'gemini-1.5-flash'
        
    @property
    def name(self) -> str:
        return "Google Gemini 1.5 Flash"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            return response.text
        except ImportError:
            # Fallback to REST API
            try:
                import requests
                response = requests.post(
                    f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent',
                    params={'key': self.api_key},
                    json={'contents': [{'parts': [{'text': prompt}]}]},
                    timeout=30
                )
                if response.status_code == 200:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
            except:
                pass
        except Exception as e:
            logging.warning(f"Gemini failed: {e}")
        return None


class HuggingFaceProvider(FreeAIProvider):
    """
    🤗 HuggingFace Inference API - FREE
    - Free tier: Rate limited but usable
    - Models: Mistral, Llama, Zephyr, many more
    
    Get free token: https://huggingface.co/settings/tokens
    """
    
    def __init__(self):
        self.api_key = os.getenv('HUGGINGFACE_API_KEY') or os.getenv('HF_TOKEN', '')
        # Free models that work well
        self.models = [
            'mistralai/Mistral-7B-Instruct-v0.2',
            'HuggingFaceH4/zephyr-7b-beta',
            'microsoft/Phi-3-mini-4k-instruct'
        ]
        
    @property
    def name(self) -> str:
        return "HuggingFace (Mistral/Zephyr)"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        try:
            import requests
            
            for model in self.models:
                try:
                    response = requests.post(
                        f'https://api-inference.huggingface.co/models/{model}',
                        headers={'Authorization': f'Bearer {self.api_key}'},
                        json={
                            'inputs': prompt,
                            'parameters': {'max_new_tokens': max_tokens, 'temperature': 0.7}
                        },
                        timeout=60
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if isinstance(result, list) and result:
                            return result[0].get('generated_text', '')
                        return str(result)
                except:
                    continue
        except Exception as e:
            logging.warning(f"HuggingFace failed: {e}")
        return None


class TogetherProvider(FreeAIProvider):
    """
    🤝 Together.ai - $25 FREE credits
    - Free: $25 credits on signup (lasts months)
    - Models: Llama 3, Mixtral, Qwen, many more
    
    Get free credits: https://api.together.xyz/
    """
    
    def __init__(self):
        self.api_key = os.getenv('TOGETHER_API_KEY', '')
        self.model = 'meta-llama/Llama-3.3-70B-Instruct-Turbo'
        
    @property
    def name(self) -> str:
        return "Together.ai (Llama 3.3)"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        try:
            import requests
            response = requests.post(
                'https://api.together.xyz/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self.model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': max_tokens,
                    'temperature': 0.7
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logging.warning(f"Together.ai failed: {e}")
        return None


class CohereProvider(FreeAIProvider):
    """
    💎 Cohere - FREE tier
    - Free: 100 API calls/minute
    - Models: Command-R (great for analysis)
    
    Get free key: https://dashboard.cohere.ai/api-keys
    """
    
    def __init__(self):
        self.api_key = os.getenv('COHERE_API_KEY', '')
        
    @property
    def name(self) -> str:
        return "Cohere Command-R"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        try:
            import requests
            response = requests.post(
                'https://api.cohere.ai/v1/generate',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'command',
                    'prompt': prompt,
                    'max_tokens': max_tokens,
                    'temperature': 0.7
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['generations'][0]['text']
        except Exception as e:
            logging.warning(f"Cohere failed: {e}")
        return None


class OpenRouterProvider(FreeAIProvider):
    """
    🔀 OpenRouter - FREE tier with many models
    - Free: Some models are completely free
    - Access to: Claude, GPT, Llama, Mistral via single API
    
    Get free key: https://openrouter.ai/keys
    """
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY', '')
        # Free models on OpenRouter
        self.model = 'meta-llama/llama-3.2-3b-instruct:free'
        
    @property
    def name(self) -> str:
        return "OpenRouter (Free Llama)"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        try:
            import requests
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://github.com/autoapply',
                    'X-Title': 'AutoApply Job Automation'
                },
                json={
                    'model': self.model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': max_tokens
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logging.warning(f"OpenRouter failed: {e}")
        return None


class OllamaProvider(FreeAIProvider):
    """
    🏠 Ollama - 100% FREE local AI
    - Free: Runs on your computer
    - Models: Llama 3, Mistral, Phi, Gemma
    - No internet needed!
    
    Install: https://ollama.ai/download
    """
    
    def __init__(self):
        self.host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'llama3.2')
        
    @property
    def name(self) -> str:
        return f"Ollama ({self.model})"
    
    def is_available(self) -> bool:
        try:
            import requests
            response = requests.get(f'{self.host}/api/tags', timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def generate(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        try:
            import requests
            response = requests.post(
                f'{self.host}/api/generate',
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False,
                    'options': {'num_predict': max_tokens}
                },
                timeout=120
            )
            if response.status_code == 200:
                return response.json().get('response', '')
        except Exception as e:
            logging.warning(f"Ollama failed: {e}")
        return None


class FreeAIManager:
    """
    🤖 Smart AI Manager - Auto-selects best FREE provider
    
    Priority order:
    1. Groq (fastest, best quality)
    2. Google Gemini (reliable)
    3. Together.ai (good free credits)
    4. HuggingFace (always works)
    5. Cohere (good for text)
    6. OpenRouter (many models)
    7. Ollama (local fallback)
    """
    
    def __init__(self):
        self.providers: List[FreeAIProvider] = [
            GroqProvider(),
            GeminiProvider(),
            TogetherProvider(),
            HuggingFaceProvider(),
            CohereProvider(),
            OpenRouterProvider(),
            OllamaProvider(),
        ]
        
        self.available_providers = [p for p in self.providers if p.is_available()]
        
        if self.available_providers:
            logging.info(f"✅ Available FREE AI providers: {[p.name for p in self.available_providers]}")
        else:
            logging.warning("⚠️ No AI providers available. Add API keys to secrets.")
            self._print_setup_guide()
    
    def _print_setup_guide(self):
        """Print guide for getting free API keys."""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║          🆓 FREE AI API KEYS - GET THEM IN 2 MINUTES!            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  🚀 GROQ (Recommended - FASTEST)                                 ║
║     https://console.groq.com/keys                                ║
║     → Sign up → Create API Key → Copy                            ║
║     Add secret: GROQ_API_KEY                                     ║
║                                                                  ║
║  🌟 GOOGLE GEMINI (Easy, Reliable)                               ║
║     https://makersuite.google.com/app/apikey                     ║
║     → Click "Create API Key" → Copy                              ║
║     Add secret: GEMINI_API_KEY                                   ║
║                                                                  ║
║  🤗 HUGGINGFACE (Always Free)                                    ║
║     https://huggingface.co/settings/tokens                       ║
║     → New Token → Copy                                           ║
║     Add secret: HUGGINGFACE_API_KEY                              ║
║                                                                  ║
║  🤝 TOGETHER.AI ($25 Free Credits)                               ║
║     https://api.together.xyz/                                    ║
║     → Sign up → API Keys → Copy                                  ║
║     Add secret: TOGETHER_API_KEY                                 ║
║                                                                  ║
║  💎 COHERE (100 calls/min free)                                  ║
║     https://dashboard.cohere.ai/api-keys                         ║
║     → Create Trial Key → Copy                                    ║
║     Add secret: COHERE_API_KEY                                   ║
║                                                                  ║
║  🔀 OPENROUTER (Multiple models)                                 ║
║     https://openrouter.ai/keys                                   ║
║     → Create Key → Copy                                          ║
║     Add secret: OPENROUTER_API_KEY                               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """)
    
    def generate(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Generate using best available provider."""
        for provider in self.available_providers:
            try:
                result = provider.generate(prompt, max_tokens)
                if result:
                    logging.debug(f"Generated using {provider.name}")
                    return result
            except Exception as e:
                logging.warning(f"{provider.name} failed: {e}")
                continue
        
        logging.error("All AI providers failed")
        return None
    
    def generate_with_fallback(self, prompt: str, fallback: str = '', max_tokens: int = 500) -> str:
        """Generate with fallback value if all providers fail."""
        result = self.generate(prompt, max_tokens)
        return result if result else fallback
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all providers."""
        return {p.name: p.is_available() for p in self.providers}


# Singleton instance
_ai_manager: Optional[FreeAIManager] = None

def get_ai() -> FreeAIManager:
    """Get the AI manager singleton."""
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = FreeAIManager()
    return _ai_manager


def main():
    """Test free AI providers."""
    print("\n🤖 FREE AI PROVIDER TEST\n")
    print("="*50)
    
    ai = get_ai()
    
    # Show status
    print("\n📊 Provider Status:")
    for name, available in ai.get_provider_status().items():
        status = "✅ Available" if available else "❌ Not configured"
        print(f"  {name}: {status}")
    
    if ai.available_providers:
        # Test generation
        print(f"\n🧪 Testing with: {ai.available_providers[0].name}")
        
        result = ai.generate(
            "In one sentence, what is the most important skill for a Data Analyst in 2025?",
            max_tokens=100
        )
        
        if result:
            print(f"\n✅ Response: {result[:200]}...")
        else:
            print("\n❌ Generation failed")
    else:
        print("\n⚠️ No providers available. See setup guide above.")


if __name__ == '__main__':
    main()
