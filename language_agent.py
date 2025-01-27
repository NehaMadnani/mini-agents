from anthropic import Anthropic
import os
from typing import Dict
from datetime import datetime, timezone
import time
from dotenv import load_dotenv

class LanguageAgent:
    def __init__(self):
        load_dotenv(override=True)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            raise ValueError("Missing required API key")
            
        self.client = Anthropic(api_key=self.anthropic_api_key)
        self.rate_limit = {
            "limit": 100000,
            "remaining": 100000,
            "reset_at": int(time.time()) + 3600
        }
        # Define token limits
        self.MIN_INPUT_TOKENS = 1
        self.MAX_OUTPUT_TOKENS = 512
        self.MAX_TOTAL_TOKENS = 200000

    def estimate_tokens(self, text: str) -> int:
        # Rough approximation: 1 token ≈ 4 characters
        return max(1, len(text) // 4)

    def validate_input_length(self, text: str) -> bool:
        estimated_tokens = self.estimate_tokens(text)
        return estimated_tokens >= self.MIN_INPUT_TOKENS and estimated_tokens <= self.MAX_TOTAL_TOKENS

    def update_rate_limit(self) -> Dict:
        self.rate_limit["remaining"] -= 1
        if self.rate_limit["remaining"] <= 0:
            if time.time() >= self.rate_limit["reset_at"]:
                self.rate_limit["remaining"] = self.rate_limit["limit"]
                self.rate_limit["reset_at"] = int(time.time()) + 3600
        return self.rate_limit

    def calculate_token_usage(self, claude_response) -> Dict:
        try:
            input_tokens = claude_response.usage.input_tokens
            output_tokens = claude_response.usage.output_tokens
            
            return {
                "total_tokens": input_tokens + output_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "billable_tokens": input_tokens + output_tokens
            }
        except (AttributeError, TypeError):
            estimated_tokens = self.estimate_tokens(str(claude_response.content))
            return {
                "total_tokens": estimated_tokens,
                "input_tokens": None,
                "output_tokens": None,
                "billable_tokens": estimated_tokens,
                "estimation_method": "word_count_approximation"
            }

    def process_query(self, user_input: str, language: str = "en") -> Dict:
        start_time = time.time()
        
        try:
            # Validate input length
            if not self.validate_input_length(user_input):
                return {
                    "error": f"Input text must be between {self.MIN_INPUT_TOKENS} and {self.MAX_TOTAL_TOKENS} tokens",
                    "meta": {
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }

            # Get Claude's response with language instruction
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=self.MAX_OUTPUT_TOKENS,
                system=f"You are a helpful language assistant. Respond in {language} language only.",
                messages=[{"role": "user", "content": user_input}]
            )
            
            # Calculate metrics
            total_response_time = int((time.time() - start_time) * 1000)
            token_usage = self.calculate_token_usage(message)
            rate_limit = self.update_rate_limit()
            
            # Extract response text
            response_text = message.content[0].text if hasattr(message.content[0], 'text') else str(message.content)
            
            return {
                "meta": {
                    "request_id": f"req_{int(time.time())}_{hash(user_input) % 10000}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "response_time_ms": total_response_time,
                    "version": "1.0.0",
                    "token_limits": {
                        "min_input": self.MIN_INPUT_TOKENS,
                        "max_output": self.MAX_OUTPUT_TOKENS
                    }
                },
                "rate_limit": {
                    "limit": rate_limit["limit"],
                    "remaining": rate_limit["remaining"],
                    "reset_at": datetime.fromtimestamp(rate_limit["reset_at"], timezone.utc).isoformat()
                },
                "response": {
                    "text": response_text,
                    "type": "language_response",
                    "language": language
                },
                "usage": token_usage,
                "query": {
                    "text": user_input,
                    "target_language": language
                }
            }
        except Exception as e:
            return {
                "error": str(e),
                "meta": {
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
