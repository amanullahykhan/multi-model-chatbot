"""
AI Orchestrator - Manages Multiple AI Models and Ensemble Learning
Intelligently routes queries to appropriate models and learns from responses
"""

import os
import json
import requests
import asyncio
import time
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import numpy as np
from datetime import datetime

load_dotenv()

class AIOrchestrator:
    """
    Orchestrates multiple AI models and implements ensemble learning
    """
    
    def __init__(self):
        self.api_keys = {
            "gemini": os.getenv("GEMINI_KEY"),
            "deepseek": os.getenv("DEEPSEEK_KEY"),
            "grok": os.getenv("GROK_KEY"),
            "qwen": os.getenv("QWEN_KEY"),
            "claude": os.getenv("CLAUDE_KEY"),
            "gpt": os.getenv("GPT_KEY"),
            "perplx": os.getenv("PERPLX_KEY"),
            "copilot": os.getenv("COPILOT_KEY"),
        }
        
        self.request_timeout = 30
        self.max_retries = 2
        
        # Model routing intelligence
        self.model_specializations = {
            "gemini": ["general", "creative", "multilingual", "vision"],
            "deepseek": ["coding", "technical", "mathematical", "reasoning"],
            "claude": ["writing", "analysis", "research", "ethical"],
            "gpt": ["general", "conversation", "summarization", "creative"],
            "qwen": ["multilingual", "chinese", "reasoning", "coding"],
            "grok": ["general", "conversation", "current_events"],
            "perplx": ["research", "factual", "current_events", "citations"],
            "copilot": ["coding", "technical", "debugging", "documentation"]
        }
        
        # Query categorization patterns
        self.query_patterns = {
            "coding": ["code", "function", "python", "javascript", "program", "debug", "error", "api"],
            "creative": ["write", "story", "poem", "creative", "imagine", "design"],
            "technical": ["explain", "how does", "technical", "algorithm", "system"],
            "research": ["research", "find", "search", "what is", "information about"],
            "multilingual": ["urdu", "arabic", "chinese", "hindi", "translate"],
            "mathematical": ["calculate", "math", "equation", "solve", "formula"],
            "general": []  # Default category
        }
        
        # Performance tracking for learning
        self.model_performance = {}
        self.load_performance_data()
    
    def load_performance_data(self):
        """Load historical performance data"""
        try:
            if os.path.exists("model_performance.json"):
                with open("model_performance.json", "r") as f:
                    self.model_performance = json.load(f)
        except Exception as e:
            print(f"Could not load performance data: {e}")
            self.model_performance = {model: {"score": 0.5, "count": 0} for model in self.api_keys.keys()}
    
    def save_performance_data(self):
        """Save performance data for learning"""
        try:
            with open("model_performance.json", "w") as f:
                json.dump(self.model_performance, f, indent=2)
        except Exception as e:
            print(f"Could not save performance data: {e}")
    
    def categorize_query(self, prompt: str) -> List[str]:
        """Categorize query to route to best models"""
        prompt_lower = prompt.lower()
        categories = []
        
        for category, keywords in self.query_patterns.items():
            if any(keyword in prompt_lower for keyword in keywords):
                categories.append(category)
        
        return categories if categories else ["general"]
    
    def select_best_models(self, prompt: str, max_models: int = 4) -> List[str]:
        """Intelligently select which models to use based on query"""
        categories = self.categorize_query(prompt)
        
        # Score each model based on specialization match
        model_scores = {}
        for model, specializations in self.model_specializations.items():
            if not self.api_keys.get(model):
                continue
            
            # Base score from specialization match
            spec_score = sum(1 for cat in categories if cat in specializations)
            
            # Add historical performance
            perf_data = self.model_performance.get(model, {"score": 0.5, "count": 0})
            perf_score = perf_data["score"]
            
            # Combine scores (70% specialization, 30% performance)
            model_scores[model] = (spec_score * 0.7) + (perf_score * 0.3)
        
        # Select top models
        sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
        selected = [model for model, score in sorted_models[:max_models]]
        
        # Always include at least one free model
        if not selected:
            selected = ["gemini", "deepseek"][:max_models]
        
        return selected
    
    async def _safe_post(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Any:
        """Safe HTTP POST with retries"""
        for attempt in range(self.max_retries):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.post(url, headers=headers or {}, json=payload, timeout=self.request_timeout)
                )
                
                if response.ok:
                    return response.json()
                else:
                    if response.status_code < 500:
                        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")
                    else:
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        raise RuntimeError(f"Server error {response.status_code}")
                        
            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    raise RuntimeError("Request timed out")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Request failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)
        
        raise RuntimeError("All retry attempts failed")
    
    # =====================================
    # MODEL-SPECIFIC IMPLEMENTATIONS
    # =====================================
    
    async def call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Call Gemini API"""
        key = self.api_keys.get("gemini")
        if not key:
            return {"error": "Gemini API key missing"}
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            start = time.time()
            result = await self._safe_post(url, {}, payload)
            latency = int((time.time() - start) * 1000)
            
            content = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            return {
                "model": "gemini",
                "content": content,
                "latency_ms": latency,
                "confidence": 0.85,
                "raw_response": result
            }
        except Exception as e:
            return {"model": "gemini", "error": str(e)}
    
    async def call_deepseek(self, prompt: str) -> Dict[str, Any]:
        """Call DeepSeek via OpenRouter"""
        key = self.api_keys.get("deepseek")
        if not key:
            return {"error": "DeepSeek API key missing"}
        
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://chatbot.app",
                "X-Title": "Professional Chatbot"
            }
            payload = {
                "model": "deepseek/deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            }
            
            start = time.time()
            result = await self._safe_post(url, headers, payload)
            latency = int((time.time() - start) * 1000)
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            return {
                "model": "deepseek",
                "content": content,
                "latency_ms": latency,
                "confidence": 0.88,
                "raw_response": result
            }
        except Exception as e:
            return {"model": "deepseek", "error": str(e)}
    
    async def call_claude(self, prompt: str) -> Dict[str, Any]:
        """Call Claude via OpenRouter"""
        key = self.api_keys.get("claude")
        if not key:
            return {"error": "Claude API key missing"}
        
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://chatbot.app",
                "X-Title": "Professional Chatbot"
            }
            payload = {
                "model": "anthropic/claude-3.5-haiku",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            }
            
            start = time.time()
            result = await self._safe_post(url, headers, payload)
            latency = int((time.time() - start) * 1000)
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            return {
                "model": "claude",
                "content": content,
                "latency_ms": latency,
                "confidence": 0.90,
                "raw_response": result
            }
        except Exception as e:
            return {"model": "claude", "error": str(e)}
    
    async def call_gpt(self, prompt: str) -> Dict[str, Any]:
        """Call GPT via OpenRouter"""
        key = self.api_keys.get("gpt")
        if not key:
            return {"error": "GPT API key missing"}
        
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://chatbot.app",
                "X-Title": "Professional Chatbot"
            }
            payload = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            }
            
            start = time.time()
            result = await self._safe_post(url, headers, payload)
            latency = int((time.time() - start) * 1000)
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            return {
                "model": "gpt",
                "content": content,
                "latency_ms": latency,
                "confidence": 0.87,
                "raw_response": result
            }
        except Exception as e:
            return {"model": "gpt", "error": str(e)}
    
    async def call_qwen(self, prompt: str) -> Dict[str, Any]:
        """Call Qwen via OpenRouter"""
        key = self.api_keys.get("qwen")
        if not key:
            return {"error": "Qwen API key missing"}
        
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://chatbot.app",
                "X-Title": "Professional Chatbot"
            }
            
            # Try multiple Qwen models
            models = ["qwen/qwen2.5-7b-instruct:free", "qwen/qwen-2.5-72b-instruct"]
            
            for model in models:
                try:
                    payload = {
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 2000
                    }
                    
                    start = time.time()
                    result = await self._safe_post(url, headers, payload)
                    latency = int((time.time() - start) * 1000)
                    
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    return {
                        "model": "qwen",
                        "content": content,
                        "latency_ms": latency,
                        "confidence": 0.86,
                        "raw_response": result
                    }
                except:
                    continue
            
            return {"model": "qwen", "error": "All Qwen models failed"}
        except Exception as e:
            return {"model": "qwen", "error": str(e)}
    
    async def call_perplexity(self, prompt: str) -> Dict[str, Any]:
        """Call Perplexity via OpenRouter"""
        key = self.api_keys.get("perplx")
        if not key:
            return {"error": "Perplexity API key missing"}
        
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://chatbot.app",
                "X-Title": "Professional Chatbot"
            }
            payload = {
                "model": "perplexity/llama-3.1-sonar-small-128k-online",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            }
            
            start = time.time()
            result = await self._safe_post(url, headers, payload)
            latency = int((time.time() - start) * 1000)
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            return {
                "model": "perplexity",
                "content": content,
                "latency_ms": latency,
                "confidence": 0.89,
                "raw_response": result
            }
        except Exception as e:
            return {"model": "perplexity", "error": str(e)}
    
    # =====================================
    # MAIN ORCHESTRATION METHODS
    # =====================================
    
    async def get_all_responses(self, prompt: str, models: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get responses from multiple models in parallel"""
        if models is None:
            models = self.select_best_models(prompt)
        
        model_functions = {
            "gemini": self.call_gemini,
            "deepseek": self.call_deepseek,
            "claude": self.call_claude,
            "gpt": self.call_gpt,
            "qwen": self.call_qwen,
            "perplx": self.call_perplexity,
        }
        
        tasks = []
        model_names = []
        
        for model in models:
            if model in model_functions:
                tasks.append(model_functions[model](prompt))
                model_names.append(model)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        responses = {}
        for model_name, result in zip(model_names, results):
            if isinstance(result, Exception):
                responses[model_name] = {"model": model_name, "error": str(result)}
            else:
                responses[model_name] = result
        
        return responses
    
    def calculate_response_quality(self, response: str, prompt: str) -> float:
        """Calculate quality score for a response"""
        if not response or len(response) < 10:
            return 0.0
        
        score = 0.5  # Base score
        
        # Length appropriateness (not too short, not too long)
        length_score = min(len(response) / 500, 1.0)
        score += length_score * 0.2
        
        # Relevance (simple keyword matching)
        prompt_words = set(prompt.lower().split())
        response_words = set(response.lower().split())
        overlap = len(prompt_words & response_words)
        relevance_score = min(overlap / max(len(prompt_words), 1), 1.0)
        score += relevance_score * 0.3
        
        return min(score, 1.0)
    
    async def get_best_response(self, prompt: str, responses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensemble learning: Select best response from multiple models
        Uses weighted scoring based on:
        - Response quality
        - Model confidence
        - Historical performance
        - Latency
        """
        valid_responses = {
            model: resp for model, resp in responses.items()
            if not resp.get("error") and resp.get("content")
        }
        
        if not valid_responses:
            return {"model": "none", "content": "No valid responses received", "error": "All models failed"}
        
        # Score each response
        scores = {}
        for model, response in valid_responses.items():
            content = response.get("content", "")
            confidence = response.get("confidence", 0.5)
            latency = response.get("latency_ms", 5000)
            
            # Quality score (40%)
            quality = self.calculate_response_quality(content, prompt)
            
            # Confidence score (30%)
            conf_score = confidence
            
            # Performance score (20%)
            perf_data = self.model_performance.get(model, {"score": 0.5})
            perf_score = perf_data.get("score", 0.5)
            
            # Speed score (10%) - faster is better
            speed_score = max(0, 1 - (latency / 10000))
            
            # Combined score
            total_score = (
                quality * 0.4 +
                conf_score * 0.3 +
                perf_score * 0.2 +
                speed_score * 0.1
            )
            
            scores[model] = total_score
        
        # Select best model
        best_model = max(scores, key=scores.get)
        best_response = valid_responses[best_model]
        best_response["ensemble_score"] = scores[best_model]
        best_response["all_scores"] = scores
        
        # Update performance tracking (simple moving average)
        if best_model in self.model_performance:
            current_data = self.model_performance[best_model]
            current_score = current_data.get("score", 0.5)
            count = current_data.get("count", 0)
            
            # Update with exponential moving average
            alpha = 0.1  # Learning rate
            new_score = (1 - alpha) * current_score + alpha * scores[best_model]
            
            self.model_performance[best_model] = {
                "score": new_score,
                "count": count + 1,
                "last_updated": datetime.utcnow().isoformat()
            }
        
        # Save performance data periodically
        if sum(data.get("count", 0) for data in self.model_performance.values()) % 10 == 0:
            self.save_performance_data()
        
        return best_response
    
    def train_from_feedback(self, model: str, feedback_score: float):
        """Update model performance based on user feedback"""
        if model not in self.model_performance:
            self.model_performance[model] = {"score": 0.5, "count": 0}
        
        current_data = self.model_performance[model]
        current_score = current_data.get("score", 0.5)
        
        # Normalize feedback (1-5 stars to 0-1)
        normalized_feedback = feedback_score / 5.0
        
        # Update with higher learning rate for explicit feedback
        alpha = 0.3
        new_score = (1 - alpha) * current_score + alpha * normalized_feedback
        
        self.model_performance[model]["score"] = new_score
        self.model_performance[model]["count"] = current_data.get("count", 0) + 1
        
        self.save_performance_data()