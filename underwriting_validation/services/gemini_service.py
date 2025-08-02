"""
Gemini LLM service implementation.

This module provides:
1. Integration with Google's Gemini model via Vertex AI
2. Standard response mode
3. Conversation and prompt handling
4. Error handling and recovery
"""

import logging
import asyncio
import os
from typing import List, Dict, Optional
import time
import random

# Google Generative AI imports
import google.generativeai as genai  # Used when API-key flow is chosen
from google.api_core import exceptions as google_api_exceptions
from google.auth import exceptions as google_auth_exceptions

from google.cloud import aiplatform
from vertexai.preview.generative_models import (
    GenerativeModel,
    SafetySetting,
    HarmCategory,
    HarmBlockThreshold,
)

from underwriting_validation.utils.result import Result, Success, Error
from underwriting_validation.utils.error import LLMError, ErrorCode
from underwriting_validation.config.settings import settings
from underwriting_validation.config.environment import get_env_var_bool

logger = logging.getLogger(__name__)

class GeminiService:
    """
    Service for interacting with Google's Gemini models via Vertex AI.
    
    Provides:
    - Standard response mode
    - Context handling for conversations
    - Error recovery and logging
    """
    
    def __init__(self):
        """Configure Gemini service – heavy model load deferred until first use."""
        # Store configuration from settings
        self.config = settings.gemini
        self.model_name = self.config.model_name
        self.temperature = self.config.temperature
        self.max_output_tokens = self.config.max_output_tokens

        # Generation configuration
        self.generation_config = {
            "temperature": self.temperature, 
            "top_p": 1, 
            "top_k": 32,
            "max_output_tokens": self.max_output_tokens,
        }
        
        # Safety settings in dictionary format (for google-generative-ai client)
        self._safety_settings_dicts = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        # Vertex-AI specific safety settings (created lazily)
        self._safety_settings_vertex: List[SafetySetting] | None = None

        # Model initialization
        self._model = None  # lazy initialization
        self.use_vertex = self.config.uses_service_account  # Determined by credentials
        self.safety_settings = self._safety_settings_dicts  # Default to dict format

        # Option to initialize eagerly
        if get_env_var_bool("GEMINI_EAGER_INIT", False):
            try:
                self._ensure_model()
                logger.info("Gemini model eagerly initialized")
            except Exception as e:
                logger.warning(f"Eager initialization failed: {e}")

    async def analyze_messages(self, messages: List[str], response_format: Optional[str] = None) -> Result[Dict]:
        """
        Analyze a batch of chat messages (or questions) using Gemini with retry logic.
        
        Args:
            messages: List of message strings (last one is the current query)
            response_format: Optional format specification (e.g., "json")
            
        Returns:
            Result containing the LLM's output or error
        """
        if not messages:
            return Error(LLMError(
                code=ErrorCode.PROMPT_TOO_LONG,
                message="No messages provided for analysis",
                user_message="I need a question to answer."
            ))
        
        # Retry logic for network resilience
        max_retries = 3
        base_delay = 0.5
        
        for attempt in range(1, max_retries + 1):
            try:
                # Ensure model is available
                self._ensure_model()

                # Get the last message as the current query
                current_message = messages[-1]
                
                # Get previous messages as history
                history = messages[:-1] if len(messages) > 1 else []
                
                model = self._model

                # Use Vertex AI - simply concatenate history + current message
                prompt = "\n".join(history + [current_message]) if history else current_message
                
                # Prepare generation config (response_format is not supported in Vertex AI)
                generation_config = self.generation_config.copy()
                
                # For Vertex AI, we need to include the response format in the prompt itself
                if response_format and response_format.lower() == "json":
                    prompt = f"{prompt}\n\nPlease provide your response in valid JSON format."
                
                response = await asyncio.to_thread(
                    model.generate_content,
                    prompt,
                    generation_config=generation_config,
                    safety_settings=self.safety_settings,
                )
                response_text = response.text
                
                # Return successful result
                return Success({
                    "response": response_text,
                    "model": self.model_name,
                    "prompt_tokens": getattr(response, "prompt_token_count", 0),
                    "completion_tokens": getattr(response, "candidate_token_count", 0)
                })
                
            except google_auth_exceptions.DefaultCredentialsError as e:
                logger.error(f"Authentication error with Gemini: {str(e)}")
                return Error(LLMError(
                    code=ErrorCode.INVALID_CREDENTIALS,
                    message=f"Authentication error with Gemini: {str(e)}",
                    user_message="There was an issue with AI system authentication."
                ))
            except google_api_exceptions.ResourceExhausted as e:
                logger.error(f"Resource exhaustion error with Gemini: {str(e)}")
                return Error(LLMError(
                    code=ErrorCode.TOKEN_LIMIT_EXCEEDED,
                    message=f"Token limit exceeded with Gemini: {str(e)}",
                    user_message="Your query is too complex for me to process right now."
                ))
            except google_api_exceptions.InvalidArgument as e:
                logger.error(f"Invalid argument error with Gemini: {str(e)}")
                return Error(LLMError(
                    code=ErrorCode.PROMPT_TOO_LONG,
                    message=f"Invalid argument: {str(e)}",
                    user_message="I couldn't process your request due to input constraints."
                ))
            except (google_api_exceptions.ServiceUnavailable,
                    google_api_exceptions.DeadlineExceeded,
                    ConnectionError,
                    OSError) as e:
                # Network-related errors - retry with backoff
                logger.warning(f"Network error on attempt {attempt}/{max_retries}: {str(e)}")
                if attempt < max_retries:
                    delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0.1, 0.3)
                    logger.info(f"Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Network error after {max_retries} attempts: {str(e)}")
                    return Error(LLMError(
                        code=ErrorCode.LLM_UNAVAILABLE,
                        message=f"Network connectivity issues with Gemini: {str(e)}",
                        user_message="I'm having trouble connecting to the AI service right now. Please try again in a moment."
                    ))
            except Exception as e:
                logger.error(f"Error analyzing messages with Gemini on attempt {attempt}: {str(e)}")
                if attempt < max_retries:
                    delay = base_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
                    continue
                else:
                    return Error(LLMError(
                        code=ErrorCode.LLM_UNAVAILABLE,
                        message=f"Error analyzing messages with Gemini: {str(e)}",
                        user_message="I'm having trouble processing your request right now."
                    ))
        
        # This should never be reached due to the loop structure
        return Error(LLMError(
            code=ErrorCode.LLM_UNAVAILABLE,
            message="Unexpected error in retry logic",
            user_message="I'm having trouble processing your request right now."
        ))
    
    async def test_connection(self) -> bool:
        """
        Test the connection to the Gemini API.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try a simple query
            result = await self.analyze_messages(["Hello, are you working?"])
            return result.is_success()
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False 

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _ensure_model(self, retries: int = 5):
        """Initialize the Gemini model with retry logic."""
        if self._model is not None:
            return
            
        if not self.config.has_valid_credentials:
            raise LLMError(
                code=ErrorCode.INVALID_CREDENTIALS,
                message="No valid Google credentials configured",
                user_message="AI service authentication is not properly configured."
            )
        
        delay = 1.0
        last_err: Exception | None = None
        
        for attempt in range(1, retries + 1):
            try:
                if self.config.uses_api_key:
                    self._initialize_with_api_key(attempt)
                    return
                elif self.config.uses_service_account:
                    self._initialize_with_service_account(attempt)
                    return
                else:
                    raise ValueError(f"Unsupported authentication method: {self.config.credentials.auth_method}")
                    
            except (google_auth_exceptions.DefaultCredentialsError, 
                    google_api_exceptions.Unauthenticated) as e:
                # Don't retry auth errors
                logger.error(f"Authentication error on attempt {attempt}: {e}")
                raise LLMError(
                    code=ErrorCode.INVALID_CREDENTIALS,
                    message=f"Authentication failed: {e}",
                    cause=e
                )
            except (google_api_exceptions.ServiceUnavailable,
                    google_api_exceptions.DeadlineExceeded,
                    ConnectionError,
                    OSError) as e:
                last_err = e
                logger.warning(f"Retryable error on attempt {attempt}: {e}")
                if attempt < retries:
                    jitter = random.uniform(0.1, 0.5)
                    sleep_time = delay + jitter
                    logger.info(f"Retrying in {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                    delay *= 1.5  # exponential backoff
                    continue
                else:
                    raise LLMError(
                        code=ErrorCode.SERVICE_UNAVAILABLE,
                        message=f"Service unavailable after {retries} attempts: {e}",
                        cause=e
                    )
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
                raise LLMError(
                    code=ErrorCode.MODEL_INITIALIZATION_FAILED,
                    message=f"Failed to initialize Gemini model: {e}",
                    cause=e
                )
        
        # Should not reach here, but just for safety
        raise LLMError(
            code=ErrorCode.MODEL_INITIALIZATION_FAILED,
            message=f"Failed to initialize Gemini model after {retries} attempts",
            cause=last_err
        )
    
    def _initialize_with_api_key(self, attempt: int):
        """Initialize Gemini model using API key authentication."""
        logger.info(f"Initializing Gemini with API key (attempt {attempt})")
        
        genai.configure(api_key=self.config.credentials.api_key)
        self._model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings=self._safety_settings_dicts,
        )
        self.use_vertex = False
        self.safety_settings = self._safety_settings_dicts
        
        logger.info(f"Gemini model initialized with API key on attempt {attempt}")
    
    def _initialize_with_service_account(self, attempt: int):
        """Initialize Gemini model using service account authentication."""
        project_id = (
            self.config.credentials.project_id or 
            os.environ.get("GOOGLE_CLOUD_PROJECT") or 
            settings.google_cloud.project_id
        )
        location = os.environ.get("GOOGLE_CLOUD_LOCATION") or settings.google_cloud.location
        
        if not project_id:
            raise ValueError("No Google Cloud project ID configured")
        
        # Set up credentials file if needed
        creds_path = self._setup_credentials_file()
        
        logger.info(f"Initializing Vertex AI with project: {project_id}, location: {location} (attempt {attempt})")
        aiplatform.init(project=project_id, location=location)
        self._model = GenerativeModel(model_name=self.model_name)
        self.use_vertex = True
        
        # Build SafetySetting objects once
        if self._safety_settings_vertex is None:
            self._safety_settings_vertex = [
                SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
                SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
                SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
                SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
            ]

        self.safety_settings = self._safety_settings_vertex
        logger.info(f"Gemini model initialized with Vertex AI on attempt {attempt}")
    
    def _setup_credentials_file(self) -> Optional[str]:
        """Set up the credentials file for Google Cloud authentication."""
        # Check if credentials file already exists
        existing_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if existing_path and os.path.exists(existing_path):
            return existing_path
        
        # Create temporary credentials file from settings if needed
        temp_path = self.config.credentials.create_credentials_file()
        if temp_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path
            logger.info("Set up temporary credentials file for Google Cloud authentication")
            return temp_path
        
        return None