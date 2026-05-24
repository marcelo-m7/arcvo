"""
HTTP client for communicating with Ollama API.
Handles health checks, model listing, and text generation.
"""
import json
import logging
from typing import Optional

import requests
from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OllamaClient:
    """
    HTTP client for Ollama API.
    
    Attributes:
        base_url (str): Ollama API base URL (e.g., https://api.ollama.monynha.me)
        model (str): Model name to use (e.g., gemma3:4b)
        timeout (int): Request timeout in seconds
        auth_password (Optional[str]): Password for auth if Ollama requires it
    """

    def __init__(
        self,
        base_url: str,
        model: str = "gemma3:4b",
        timeout: int = 90,
        auth_password: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.auth_password = auth_password

    def health(self) -> bool:
        """
        Check if Ollama API is healthy.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/api/health"
            response = requests.get(url, timeout=5, verify=False)
            return response.status_code == 200
        except Exception as e:
            _logger.warning(f"Ollama health check failed: {e}")
            return False

    def list_models(self) -> list[str]:
        """
        List available models on Ollama.
        
        Returns:
            list[str]: List of available model names
        """
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=self.timeout, verify=False)
            response.raise_for_status()
            data = response.json()
            models_list = data.get("models", [])
            return [m.get("name") for m in models_list if m.get("name")]
        except Exception as e:
            _logger.error(f"Failed to list Ollama models: {e}")
            return []

    def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt (str): Input prompt for the model
            model (str, optional): Model name override. Defaults to self.model
            
        Returns:
            str: Generated text response
            
        Raises:
            UserError: If generation fails or times out
        """
        model = model or self.model
        url = f"{self.base_url}/api/generate"
        
        headers = {}
        if self.auth_password:
            import base64
            # Basic auth if password provided
            auth_str = base64.b64encode(f":{self.auth_password}".encode()).decode()
            headers["Authorization"] = f"Basic {auth_str}"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        
        try:
            _logger.info(f"Calling Ollama generate: model={model}, prompt_len={len(prompt)}")
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
                verify=False,
            )
            response.raise_for_status()
            
            data = response.json()
            generated_text = data.get("response", "").strip()
            
            if not generated_text:
                raise UserError("Ollama returned empty response")
            
            _logger.info(f"Ollama generation succeeded: response_len={len(generated_text)}")
            return generated_text
            
        except requests.Timeout:
            msg = f"Ollama generation timeout after {self.timeout}s"
            _logger.error(msg)
            raise UserError(msg)
        except requests.RequestException as e:
            msg = f"Ollama API error: {e}"
            _logger.error(msg)
            raise UserError(msg)
        except (json.JSONDecodeError, KeyError) as e:
            msg = f"Failed to parse Ollama response: {e}"
            _logger.error(msg)
            raise UserError(msg)

    def extract_json_from_text(self, text: str) -> Optional[dict]:
        """
        Extract JSON object from generated text.
        
        Handles cases where JSON is wrapped in markdown code blocks
        or mixed with explanatory text.
        
        Args:
            text (str): Text potentially containing JSON
            
        Returns:
            Optional[dict]: Parsed JSON object, or None if not found
        """
        # Try direct parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract from markdown code block
        if "```json" in text:
            try:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            except (IndexError, json.JSONDecodeError):
                pass
        
        # Try to extract JSON object pattern
        import re
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
