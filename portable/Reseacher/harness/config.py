"""
Master Certification Retrieval & Curation Agent - LLM Client Factory
Multi-provider abstraction supporting Gemini, Anthropic, OpenAI, and Ollama.
"""

import os
import json
from typing import Optional, Dict, Any


class LLMClient:
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()
        self.model = model or os.getenv("LLM_MODEL", "gemini-2.5-flash")

    def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """
        Requests structured JSON completion from configured LLM provider.
        """
        # If no real keys are configured, return deterministic mock structure
        if self._is_mock_env():
            return self._mock_completion(prompt)

        if self.provider == "gemini":
            return self._call_gemini(prompt, system_prompt)
        elif self.provider == "anthropic":
            return self._call_anthropic(prompt, system_prompt)
        elif self.provider == "openai":
            return self._call_openai(prompt, system_prompt)
        elif self.provider == "ollama":
            return self._call_ollama(prompt, system_prompt)
        else:
            return self._mock_completion(prompt)

    def _is_mock_env(self) -> bool:
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if self.provider == "gemini" and (not gemini_key or "your-" in gemini_key):
            return True
        if self.provider == "anthropic" and (not anthropic_key or "your-" in anthropic_key):
            return True
        if self.provider == "openai" and (not openai_key or "your-" in openai_key):
            return True
        return False

    def _call_gemini(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config={"response_mime_type": "application/json"}
            )
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            response = model.generate_content(full_prompt)
            return json.loads(response.text)
        except Exception as e:
            print(f"[WARN] Gemini call failed ({e}). Returning fallback.")
            return self._mock_completion(prompt)

    def _call_anthropic(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            message = client.messages.create(
                model=self.model if "claude" in self.model else "claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = message.content[0].text
            # Extract JSON block
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            return json.loads(raw)
        except Exception as e:
            print(f"[WARN] Anthropic call failed ({e}). Returning fallback.")
            return self._mock_completion(prompt)

    def _call_openai(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model=self.model if "gpt" in self.model else "gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[WARN] OpenAI call failed ({e}). Returning fallback.")
            return self._mock_completion(prompt)

    def _call_ollama(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        import requests
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            resp = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": self.model,
                    "system": system_prompt,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False
                },
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            return json.loads(data.get("response", "{}"))
        except Exception as e:
            print(f"[WARN] Ollama call failed ({e}). Returning fallback.")
            return self._mock_completion(prompt)

    def _mock_completion(self, prompt: str) -> Dict[str, Any]:
        return {
            "name": "Cloud Native eBPF Foundations",
            "issuer": "Isovalent & CNCF",
            "category": "DevSecOps & Kubernetes",
            "url": "https://isovalent.com/learning-path/",
            "cost": "Free",
            "exact_format": "Self-paced Assessment",
            "credly_badge": True,
            "credly_badge_url": "https://www.credly.com/org/isovalent/badge/ebpf-foundations",
            "linkedin_addable": True,
            "linkedin_cert_id_supported": True,
            "why_hidden": "Specialized kernel observability and network security credential rarely indexed on mainstream course aggregators."
        }
