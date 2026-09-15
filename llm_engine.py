# ============================================================
# NEXIS 5.13 - OLLAMA LLM ENGINE
# ============================================================
# Connects NEXIS to local Ollama instance for intelligent reasoning
# Mistral model recommended for conversational quality & speed

import requests
import json
import traceback
from typing import Optional, Dict, List


class OllamaEngine:
    """
    Interface to Ollama LLM running locally on localhost:11434
    Handles model inference with graceful fallbacks
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 11434,
        model: str = "mistral",
        timeout: int = 30
    ):
        """
        Initialize Ollama connection.
        
        Args:
            host: Ollama server host (default: localhost)
            port: Ollama server port (default: 11434)
            model: Model name to use (default: mistral)
            timeout: Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.model = model
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.available = False
        self.model_loaded = False
        
        # Test connection on init
        self.test_connection()

    def test_connection(self) -> bool:
        """
        Test if Ollama server is running and accessible.
        
        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                self.available = True
                data = response.json()
                models = data.get("models", [])
                
                # Check if our target model is available
                model_names = [m.get("name", "") for m in models]
                self.model_loaded = any(
                    m.startswith(self.model) for m in model_names
                )
                
                if self.model_loaded:
                    print(
                        f"NEXIS LLM: Ollama connected. "
                        f"Model '{self.model}' ready."
                    )
                else:
                    print(
                        f"NEXIS LLM: Ollama available but "
                        f"'{self.model}' not found. "
                        f"Available: {model_names}"
                    )
                return True
        except requests.ConnectionError:
            print(
                f"NEXIS LLM: Cannot connect to Ollama at "
                f"{self.base_url}. Is it running?"
            )
        except Exception as error:
            print(f"NEXIS LLM: Connection test failed: {error}")
        
        self.available = False
        return False

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 512
    ) -> Optional[str]:
        """
        Generate a response using Ollama.
        
        Args:
            prompt: User message/query
            system: System prompt for context (optional)
            temperature: Creativity level (0.0-1.0)
            top_p: Nucleus sampling parameter
            max_tokens: Maximum response length
        
        Returns:
            Generated text response, or None if failed
        """
        if not self.available or not self.model_loaded:
            print("NEXIS LLM: Ollama not available. Using fallback.")
            return None
        
        try:
            # Build the full prompt with system context if provided
            full_prompt = prompt
            if system:
                full_prompt = f"{system}\n\nUser: {prompt}"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": max_tokens,
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                generated_text = data.get("response", "").strip()
                return generated_text if generated_text else None
            else:
                print(
                    f"NEXIS LLM: Ollama returned status "
                    f"{response.status_code}"
                )
                return None
                
        except requests.Timeout:
            print("NEXIS LLM: Ollama request timed out.")
            return None
        except requests.ConnectionError:
            print("NEXIS LLM: Connection lost to Ollama.")
            self.available = False
            return None
        except Exception as error:
            print(f"NEXIS LLM: Generation error: {error}")
            traceback.print_exc()
            return None

    def generate_streaming(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        callback = None
    ) -> Optional[str]:
        """
        Generate response with streaming (useful for real-time TTS).
        
        Args:
            prompt: User message
            system: System prompt
            temperature: Creativity level
            callback: Function to call with each chunk (token)
        
        Returns:
            Full generated text
        """
        if not self.available or not self.model_loaded:
            return None
        
        try:
            full_prompt = prompt
            if system:
                full_prompt = f"{system}\n\nUser: {prompt}"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": True,
                    "temperature": temperature,
                },
                timeout=self.timeout,
                stream=True
            )
            
            full_text = ""
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        chunk = data.get("response", "")
                        full_text += chunk
                        
                        if callback:
                            callback(chunk)
                    except json.JSONDecodeError:
                        continue
            
            return full_text if full_text else None
            
        except Exception as error:
            print(f"NEXIS LLM: Streaming error: {error}")
            return None

    def pull_model(self, model_name: str = None) -> bool:
        """
        Attempt to download/pull a model from Ollama.
        Note: This runs in the background and takes time.
        
        Args:
            model_name: Model to pull (default: self.model)
        
        Returns:
            True if pull started, False if failed
        """
        if not self.available:
            print("NEXIS LLM: Ollama not available.")
            return False
        
        target = model_name or self.model
        
        try:
            print(f"NEXIS LLM: Pulling model '{target}'...")
            print(f"NEXIS LLM: This may take several minutes.")
            
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": target},
                timeout=600  # 10 minute timeout for download
            )
            
            if response.status_code == 200:
                print(f"NEXIS LLM: Model '{target}' pulled successfully.")
                self.model_loaded = True
                return True
            else:
                print(
                    f"NEXIS LLM: Pull failed with status "
                    f"{response.status_code}"
                )
                return False
                
        except Exception as error:
            print(f"NEXIS LLM: Pull error: {error}")
            return False

    def get_model_info(self) -> Optional[Dict]:
        """
        Get information about the currently loaded model.
        
        Returns:
            Dictionary with model info, or None if failed
        """
        if not self.available:
            return None
        
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": self.model},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as error:
            print(f"NEXIS LLM: Failed to get model info: {error}")
            return None

    def is_ready(self) -> bool:
        """
        Quick check if Ollama is ready to generate.
        
        Returns:
            True if available and model is loaded
        """
        return self.available and self.model_loaded
