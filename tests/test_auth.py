"""Tests for credential helpers."""

import pytest
from unittest.mock import patch, MagicMock


def test_get_maap_secret_with_401_error():
    """Test that dict error response from MAAP is properly caught and raised."""
    error_response = {
        "message": "No valid authentication credentials provided or processed.",
        "code": 401,
    }
    with patch("maap_data_downloaders.auth.MAAP") as mock_maap_class:
        mock_instance = MagicMock()
        mock_maap_class.return_value = mock_instance
        mock_instance.secrets.get_secret.return_value = error_response

        from maap_data_downloaders.auth import get_maap_secret

        with pytest.raises(RuntimeError) as exc_info:
            get_maap_secret("TEST_SECRET")

        assert "could not be retrieved" in str(exc_info.value)
        assert "HTTP 401" in str(exc_info.value)
        assert "No valid authentication credentials" in str(exc_info.value)


def test_get_maap_secret_with_valid_response():
    """Test that valid secret string is returned unchanged."""
    with patch("maap_data_downloaders.auth.MAAP") as mock_maap_class:
        mock_instance = MagicMock()
        mock_maap_class.return_value = mock_instance
        mock_instance.secrets.get_secret.return_value = "my-secret-value"

        from maap_data_downloaders.auth import get_maap_secret

        result = get_maap_secret("TEST_SECRET")
        assert result == "my-secret-value"


def test_get_maap_secret_with_empty_response():
    """Test that empty/None response raises RuntimeError."""
    with patch("maap_data_downloaders.auth.MAAP") as mock_maap_class:
        mock_instance = MagicMock()
        mock_maap_class.return_value = mock_instance
        mock_instance.secrets.get_secret.return_value = None

        from maap_data_downloaders.auth import get_maap_secret

        with pytest.raises(RuntimeError) as exc_info:
            get_maap_secret("TEST_SECRET")

        assert "empty or not found" in str(exc_info.value)


def test_get_earthdata_credentials():
    """Test that get_earthdata_credentials calls get_maap_secret twice."""
    with patch("maap_data_downloaders.auth.get_maap_secret") as mock_get_secret:
        mock_get_secret.side_effect = ["test-user", "test-pass"]

        from maap_data_downloaders.auth import get_earthdata_credentials

        username, password = get_earthdata_credentials()
        assert username == "test-user"
        assert password == "test-pass"


def test_get_earthdata_token():
    """Test that get_earthdata_token calls get_maap_secret with EARTHDATA_TOKEN."""
    with patch("maap_data_downloaders.auth.get_maap_secret") as mock_get_secret:
        mock_get_secret.return_value = "test-token-value"

        from maap_data_downloaders.auth import get_earthdata_token

        token = get_earthdata_token()
        assert token == "test-token-value"
        mock_get_secret.assert_called_once_with("EARTHDATA_TOKEN")
