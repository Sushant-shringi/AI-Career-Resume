from unittest.mock import patch, MagicMock
import pytest
from backend.app.services.llm.base import LLMProvider
from backend.app.services.llm.gemini_provider import GeminiProvider
from backend.app.services.llm.ollama_provider import OllamaProvider
from backend.app.services.llm import get_llm_provider
from backend.app.services.rag_service import rag_service

def test_gemini_provider_inherits_llm_provider():
    provider = GeminiProvider(api_key="test-key", model="gemini-3.1-flash-lite")
    assert isinstance(provider, LLMProvider)
    assert "Google Gemini (gemini-3.1-flash-lite)" in provider.provider_name

def test_gemini_provider_missing_api_key():
    provider = GeminiProvider(api_key="", model="gemini-3.1-flash-lite")
    is_avail, msg = provider.is_available()
    assert is_avail is False
    assert "Gemini API key is not configured" in msg
    
    # generate without key
    result = provider.generate("Test prompt")
    assert "Gemini API key is not configured" in result
    assert "Add GEMINI_API_KEY to the backend environment" in result

def test_provider_factory_selection():
    gemini_prov = get_llm_provider("gemini")
    assert isinstance(gemini_prov, GeminiProvider)
    
    ollama_prov = get_llm_provider("ollama")
    assert isinstance(ollama_prov, OllamaProvider)

@patch("google.genai.Client")
def test_gemini_provider_successful_generate(mock_client_cls):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is a grounded answer based on your resume."
    mock_client.models.generate_content.return_value = mock_response
    mock_client_cls.return_value = mock_client

    provider = GeminiProvider(api_key="valid-mock-key", model="gemini-3.1-flash-lite")
    response = provider.generate(
        prompt="What AWS services did I use?",
        system_prompt="You are a factual resume assistant."
    )

    assert response == "This is a grounded answer based on your resume."
    mock_client.models.generate_content.assert_called_once()
    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-3.1-flash-lite"
    assert call_kwargs["contents"] == "What AWS services did I use?"
    assert call_kwargs["config"].system_instruction == "You are a factual resume assistant."
    assert call_kwargs["config"].temperature == 0.2

@patch("google.genai.Client")
def test_gemini_provider_error_handling(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API key not valid. Please pass a valid API key.")
    mock_client_cls.return_value = mock_client

    provider = GeminiProvider(api_key="invalid-key", model="gemini-3.1-flash-lite")
    response = provider.generate(prompt="Test prompt")

    assert "Error: The provided GEMINI_API_KEY is invalid" in response
    # Verify no traceback is leaked
    assert "Traceback" not in response
    assert "invalid-key" not in response

@patch("backend.app.services.llm.gemini_provider.GeminiProvider.generate")
def test_rag_service_with_gemini_provider(mock_gemini_generate):
    mock_gemini_generate.return_value = "Candidate used AWS Lambda and S3 in the ETL pipeline."
    
    with patch("backend.app.config.settings.LLM_PROVIDER", "gemini"):
        with patch("backend.app.config.settings.GEMINI_API_KEY", "mock-key"):
            answer, chunks, provider_name = rag_service.answer_question(
                resume_id=1,
                question="What AWS services were used?"
            )
            assert "Google Gemini" in provider_name
