"""Translation/AI adapter to support both Azure OpenAI and local HuggingFace models.

This module provides a unified interface for AI operations that works with:
- Azure OpenAI (using DefaultAzureCredential or API key)
- HuggingFace Transformers (for local development)
"""

import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class AIModelAdapter(ABC):
    """Abstract base class for AI model adapters."""
    
    @abstractmethod
    def summarize_text(self, text: str) -> Dict[str, Any]:
        """Summarize text.
        
        Args:
            text: Text to summarize
        
        Returns:
            Dict with keys: 'summary', 'prompt_tokens', 'completion_tokens', 
            'total_tokens', 'cost_usd'
        """
        pass
    
    @abstractmethod
    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (optional)
        
        Returns:
            Dict with keys: 'translation', 'prompt_tokens', 'completion_tokens',
            'total_tokens', 'cost_usd'
        """
        pass


class AzureOpenAIAdapter(AIModelAdapter):
    """Azure OpenAI implementation using DefaultAzureCredential or API key."""
    
    def __init__(
        self,
        endpoint: str,
        deployment: str,
        api_key: Optional[str] = None,
        use_azure_ad: bool = True,
        api_version: str = "2024-02-15-preview"
    ):
        """Initialize Azure OpenAI adapter.
        
        Args:
            endpoint: Azure OpenAI endpoint URL
            deployment: Deployment/model name
            api_key: API key (optional, for backward compatibility)
            use_azure_ad: Whether to use DefaultAzureCredential (True) or API key (False)
            api_version: API version
        """
        from openai import AzureOpenAI
        
        self.endpoint = endpoint
        self.deployment = deployment
        self.api_version = api_version
        self.use_azure_ad = use_azure_ad
        
        if use_azure_ad and not api_key:
            # Use DefaultAzureCredential (production)
            from azure.identity import DefaultAzureCredential
            from azure.core.credentials import AccessToken
            
            # Create token provider for OpenAI SDK
            credential = DefaultAzureCredential()
            
            # Get token for Azure Cognitive Services
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            
            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                azure_ad_token=token.token,
                api_version=api_version
            )
            self.credential = credential
        else:
            # Use API key (legacy or local testing)
            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )
            self.credential = None
        
        # Cost per 1000 tokens
        self.cost_per_1k_input = float(os.getenv("AZURE_OPENAI_INPUT_COST", "0.01"))
        self.cost_per_1k_output = float(os.getenv("AZURE_OPENAI_OUTPUT_COST", "0.03"))
    
    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate API cost.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Cost in USD
        """
        input_cost = (prompt_tokens / 1000) * self.cost_per_1k_input
        output_cost = (completion_tokens / 1000) * self.cost_per_1k_output
        return round(input_cost + output_cost, 6)
    
    def _refresh_token_if_needed(self) -> None:
        """Refresh Azure AD token if using DefaultAzureCredential."""
        if self.use_azure_ad and self.credential:
            token = self.credential.get_token("https://cognitiveservices.azure.com/.default")
            # Update client with new token
            self.client._azure_ad_token = token.token
    
    def summarize_text(self, text: str) -> Dict[str, Any]:
        """Summarize text using Azure OpenAI."""
        self._refresh_token_if_needed()
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes text concisely. "
                              "Include key points as a bulleted list at the end."
                },
                {"role": "user", "content": f"Summarize the following text:\n\n{text}"}
            ]
        )
        
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        total_tokens = response.usage.total_tokens if response.usage else 0
        
        return {
            "summary": response.choices[0].message.content,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": self._calculate_cost(prompt_tokens, completion_tokens)
        }
    
    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text using Azure OpenAI."""
        self._refresh_token_if_needed()
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a translator. Translate the following text to "
                              f"{target_language}. Preserve the original meaning and tone."
                },
                {"role": "user", "content": text}
            ]
        )
        
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        total_tokens = response.usage.total_tokens if response.usage else 0
        
        return {
            "translation": response.choices[0].message.content,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": self._calculate_cost(prompt_tokens, completion_tokens)
        }


class HuggingFaceAdapter(AIModelAdapter):
    """HuggingFace local models implementation for development."""
    
    def __init__(self):
        """Initialize HuggingFace adapter with local models."""
        # Use lightweight models suitable for local development
        self.summarization_model_name = os.getenv(
            "HF_SUMMARIZATION_MODEL",
            "facebook/bart-large-cnn"  # Good quality summarization model
        )
        self.translation_model_name = os.getenv(
            "HF_TRANSLATION_MODEL",
            "Helsinki-NLP/opus-mt-{src}-{tgt}"  # Template for translation models
        )
        
        self._summarization_pipeline = None
        self._translation_pipelines = {}  # Cache translation models
    
    def _get_summarization_pipeline(self):
        """Lazy load summarization pipeline."""
        if self._summarization_pipeline is None:
            from transformers import pipeline
            print(f"Loading summarization model: {self.summarization_model_name}")
            self._summarization_pipeline = pipeline(
                "summarization", 
                model=self.summarization_model_name,
                device=-1  # CPU
            )
        return self._summarization_pipeline
    
    def _get_translation_pipeline(self, source_lang: str, target_lang: str):
        """Lazy load translation pipeline for specific language pair"""
        key = f"{source_lang}-{target_lang}"
        
        if key not in self._translation_pipelines:
            from transformers import pipeline
            
            # Build model name from template
            if "{src}" in self.translation_model_name:
                model_name = self.translation_model_name.format(src=source_lang, tgt=target_lang)
            else:
                model_name = self.translation_model_name
            
            print(f"Loading translation model: {model_name}")
            try:
                self._translation_pipelines[key] = pipeline(
                    "translation",
                    model=model_name,
                    device=-1  # CPU
                )
            except Exception as e:
                print(f"Error loading translation model {model_name}: {e}")
                # Fallback to a generic multilingual model
                print("Falling back to NLLB-200 model")
                model_name = "facebook/nllb-200-distilled-600M"
                self._translation_pipelines[key] = pipeline(
                    "translation",
                    model=model_name,
                    device=-1
                )
        
        return self._translation_pipelines[key]
    
    def summarize_text(self, text: str) -> Dict[str, Any]:
        """Summarize text using HuggingFace model"""
        pipeline = self._get_summarization_pipeline()
        
        # BART model has a max length of 1024 tokens
        # Truncate input if too long
        max_input_length = 1024
        if len(text.split()) > max_input_length:
            text = ' '.join(text.split()[:max_input_length])
        
        result = pipeline(
            text,
            max_length=150,
            min_length=40,
            do_sample=False
        )
        
        summary = result[0]['summary_text']
        
        # Estimate token counts (rough approximation)
        prompt_tokens = len(text.split())
        completion_tokens = len(summary.split())
        total_tokens = prompt_tokens + completion_tokens
        
        return {
            "summary": summary,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": 0.0  # Local models are free
        }
    
    def translate_text(self, text: str, target_language: str, source_language: Optional[str] = None) -> Dict[str, Any]:
        """Translate text using HuggingFace model"""
        # Map common language codes
        lang_map = {
            "en": "eng",
            "es": "spa",
            "fr": "fra",
            "de": "deu",
            "zh": "zho",
            "ja": "jpn",
            "ko": "kor",
        }
        
        src_lang = lang_map.get(source_language, source_language or "eng")
        tgt_lang = lang_map.get(target_language, target_language)
        
        try:
            pipeline = self._get_translation_pipeline(src_lang, tgt_lang)
            result = pipeline(text)
            translation = result[0]['translation_text']
        except Exception as e:
            print(f"Translation error: {e}")
            # Fallback: return original text with note
            translation = f"[Translation unavailable: {e}] {text}"
        
        # Estimate token counts
        prompt_tokens = len(text.split())
        completion_tokens = len(translation.split())
        total_tokens = prompt_tokens + completion_tokens
        
        return {
            "translation": translation,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": 0.0  # Local models are free
        }


def get_ai_adapter(
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
    deployment: Optional[str] = None,
    use_azure_ad: Optional[bool] = None
) -> AIModelAdapter:
    """Factory function to get the appropriate AI adapter.
    
    Args:
        endpoint: Azure OpenAI endpoint (optional, read from env if None)
        api_key: Azure OpenAI API key (optional, for legacy support)
        deployment: Azure OpenAI deployment name (optional, read from env if None)
        use_azure_ad: Whether to use DefaultAzureCredential (None = auto-detect)
    
    Returns:
        AIModelAdapter instance (either Azure OpenAI or HuggingFace)
    """
    environment = os.getenv("ENVIRONMENT", "AZURE").upper()
    
    if environment == "LOCAL":
        # Use HuggingFace models for local development
        return HuggingFaceAdapter()
    else:
        # Use Azure OpenAI
        if endpoint is None:
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://my-resource.openai.azure.com/")
        if deployment is None:
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        
        # Auto-detect whether to use Azure AD or API key
        if use_azure_ad is None:
            if api_key is None:
                api_key = os.getenv("AZURE_OPENAI_KEY", "")
            # Use Azure AD if no API key is provided
            use_azure_ad = not bool(api_key)
        
        return AzureOpenAIAdapter(
            endpoint=endpoint,
            deployment=deployment,
            api_key=api_key if not use_azure_ad else None,
            use_azure_ad=use_azure_ad
        )

