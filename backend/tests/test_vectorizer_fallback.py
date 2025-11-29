import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai_client.ai_client import AIClient

@pytest.mark.asyncio
async def test_vectorize_image_webapi_fallback():
    # Instantiate AIClient
    # We need to mock the internal clients *after* instantiation or patch the classes *before* instantiation.
    # Since AIClient instantiates them in __init__, patching the classes is better.

    with patch('app.services.ai_client.ai_client.A8VectorizerClient') as MockA8, \
         patch('app.services.ai_client.ai_client.VectorWebAPIClient') as MockWebAPI:
        
        # Setup mocks
        mock_a8_instance = MockA8.return_value
        mock_webapi_instance = MockWebAPI.return_value
        
        # A8 fails
        mock_a8_instance.image_to_vector = AsyncMock(side_effect=Exception("A8 Service Down"))
        
        # WebAPI succeeds
        expected_url = "http://example.com/result.svg"
        mock_webapi_instance.convert_image = AsyncMock(return_value=expected_url)
        
        # Initialize AIClient
        client = AIClient()
        
        # Call the method
        image_bytes = b"fake_image_bytes"
        result = await client.vectorize_image_webapi(image_bytes, options={"vectorFormat": ".svg"})
        
        # Verify results
        assert result == expected_url
        
        # Verify A8 was called
        mock_a8_instance.image_to_vector.assert_called_once()
        
        # Verify WebAPI was called (fallback happened)
        mock_webapi_instance.convert_image.assert_called_once()

@pytest.mark.asyncio
async def test_vectorize_image_webapi_a8_success():
    with patch('app.services.ai_client.ai_client.A8VectorizerClient') as MockA8, \
         patch('app.services.ai_client.ai_client.VectorWebAPIClient') as MockWebAPI:
        
        # Setup mocks
        mock_a8_instance = MockA8.return_value
        mock_webapi_instance = MockWebAPI.return_value
        
        # A8 succeeds
        expected_url = "http://example.com/a8_result.svg"
        mock_a8_instance.image_to_vector = AsyncMock(return_value=expected_url)
        
        # Initialize AIClient
        client = AIClient()
        
        # Call the method
        image_bytes = b"fake_image_bytes"
        result = await client.vectorize_image_webapi(image_bytes, options={"vectorFormat": ".svg"})
        
        # Verify results
        assert result == expected_url
        
        # Verify A8 was called
        mock_a8_instance.image_to_vector.assert_called_once()
        
        # Verify WebAPI was NOT called
        mock_webapi_instance.convert_image.assert_not_called()
