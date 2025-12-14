import os
import sys
import asyncio
from openai import AzureOpenAI

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base_worker import BaseWorker, StepMetrics

# Azure OpenAI Config
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://my-resource.openai.azure.com/")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
API_VERSION = "2024-02-15-preview"

client_ai = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT, 
    api_key=AZURE_OPENAI_KEY,  
    api_version=API_VERSION
)


class AzureAIWorker(BaseWorker):
    """Worker for Azure OpenAI tasks: translation and summarization with token tracking"""
    
    def __init__(self):
        queue_name = os.getenv("AZURE_AI_QUEUE_NAME", "azure-ai-jobs")
        super().__init__(queue_name=queue_name, step_name="AZURE_AI")
    
    def summarize_text(self, text: str, metrics: StepMetrics) -> str:
        """Summarize text using GPT-4 with token tracking"""
        response = client_ai.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text concisely. Include key points as a bulleted list at the end."},
                {"role": "user", "content": f"Summarize the following text:\n\n{text}"}
            ]
        )
        
        # Track token usage
        if response.usage:
            metrics.prompt_tokens = response.usage.prompt_tokens
            metrics.completion_tokens = response.usage.completion_tokens
            metrics.total_tokens = response.usage.total_tokens
            metrics.api_cost_usd = self._calculate_api_cost(
                metrics.prompt_tokens, 
                metrics.completion_tokens
            )
        
        return response.choices[0].message.content
    
    def translate_text(self, text: str, target_lang: str, metrics: StepMetrics) -> str:
        """Translate text using GPT-4 with token tracking"""
        response = client_ai.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": f"You are a translator. Translate the following text to {target_lang}. Preserve the original meaning and tone."},
                {"role": "user", "content": text}
            ]
        )
        
        # Track token usage
        if response.usage:
            metrics.prompt_tokens = response.usage.prompt_tokens
            metrics.completion_tokens = response.usage.completion_tokens
            metrics.total_tokens = response.usage.total_tokens
            metrics.api_cost_usd = self._calculate_api_cost(
                metrics.prompt_tokens, 
                metrics.completion_tokens
            )
        
        return response.choices[0].message.content
    
    async def process(self, job_id: str, payload: dict, metrics: StepMetrics, sb_client) -> dict:
        """Process Azure AI task (summarize or translate) with metrics collection"""
        task = payload.get("task")  # 'summarize', 'translate'
        input_text = payload.get("text", "")
        
        # Record model info
        metrics.model_name = DEPLOYMENT_NAME
        metrics.model_version = API_VERSION
        
        if not input_text:
            metrics.error_code = "MISSING_INPUT"
            raise ValueError("No input text provided")
        
        result_data = {}
        
        if task == "summarize":
            self.step_name = "SUMMARIZE"  # Override for correct event reporting
            summary = self.summarize_text(input_text, metrics)
            result_data = {
                "summary": summary,
                "input_char_count": len(input_text),
                "output_char_count": len(summary),
                "tokens_used": metrics.total_tokens,
                "cost_usd": metrics.api_cost_usd
            }
            print(f"[AZURE] Summarization complete. Tokens: {metrics.total_tokens}, Cost: ${metrics.api_cost_usd:.4f}")
            
        elif task == "translate":
            self.step_name = "TRANSLATE"
            target_lang = payload.get("target_lang", "en")
            translation = self.translate_text(input_text, target_lang, metrics)
            result_data = {
                "translation": translation,
                "source_language": payload.get("source_lang", "unknown"),
                "target_language": target_lang,
                "input_char_count": len(input_text),
                "output_char_count": len(translation),
                "tokens_used": metrics.total_tokens,
                "cost_usd": metrics.api_cost_usd
            }
            print(f"[AZURE] Translation complete. Tokens: {metrics.total_tokens}, Cost: ${metrics.api_cost_usd:.4f}")
        
        else:
            metrics.error_code = "UNKNOWN_TASK"
            raise ValueError(f"Unknown task: {task}")
        
        # Upload result
        blob_path = self.upload_result(job_id, task, result_data)
        
        return {
            "blob_path": blob_path,
            "preview": str(result_data)[:100],
            "tokens_used": metrics.total_tokens,
            "cost_usd": metrics.api_cost_usd
        }


if __name__ == "__main__":
    worker = AzureAIWorker()
    asyncio.run(worker.run())
