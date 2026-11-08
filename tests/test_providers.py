import io
import os
import unittest
import urllib.error
from unittest.mock import patch

from kinoquence.providers import ProviderConfig, ProviderError, _NoRedirectHandler, _request_json, generate_text


class ProviderAdapterTests(unittest.TestCase):
    def test_openai_compatible_response(self):
        config = ProviderConfig(provider="ollama", model="example:latest")
        response = {"choices": [{"message": {"content": "Hello from local model"}}]}
        with patch("kinoquence.providers._request_json", return_value=response) as request:
            with patch.dict(os.environ, {}, clear=True):
                text = generate_text(config, "system", "user")
        self.assertEqual(text, "Hello from local model")
        args, kwargs = request.call_args
        self.assertTrue(args[0].endswith("/chat/completions"))
        self.assertNotIn("Authorization", args[1])

    def test_anthropic_response(self):
        config = ProviderConfig(provider="anthropic", model="claude-test", api_key="test-key")
        response = {"content": [{"type": "text", "text": "A Claude result"}]}
        with patch("kinoquence.providers._request_json", return_value=response) as request:
            text = generate_text(config, "system", "user")
        self.assertEqual(text, "A Claude result")
        self.assertEqual(request.call_args.args[1]["x-api-key"], "test-key")

    def test_gemini_response(self):
        config = ProviderConfig(provider="gemini", model="gemini-test", api_key="test-key")
        response = {"candidates": [{"content": {"parts": [{"text": "A Gemini result"}]}}]}
        with patch("kinoquence.providers._request_json", return_value=response) as request:
            text = generate_text(config, "system", "user")
        self.assertEqual(text, "A Gemini result")
        self.assertIn("generateContent", request.call_args.args[0])

    def test_missing_cloud_key_fails_cleanly(self):
        config = ProviderConfig(provider="anthropic", model="claude-test")
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ProviderError):
                generate_text(config, "system", "user")

    def test_gemini_api_key_is_sent_in_header_not_url(self):
        config = ProviderConfig(provider="gemini", model="gemini-test", api_key="private-test-key")
        response = {"candidates": [{"content": {"parts": [{"text": "A Gemini result"}]}}]}
        with patch("kinoquence.providers._request_json", return_value=response) as request:
            generate_text(config, "system", "user")
        url, headers = request.call_args.args[:2]
        self.assertNotIn("private-test-key", url)
        self.assertEqual(headers["x-goog-api-key"], "private-test-key")

    def test_api_key_is_not_sent_to_remote_plain_http_endpoint(self):
        config = ProviderConfig(
            provider="openai-compatible", model="example", base_url="http://example.com/v1", api_key="secret-value"
        )
        with patch("kinoquence.providers._request_json") as request:
            with self.assertRaises(ProviderError) as raised:
                generate_text(config, "system", "user")
        self.assertNotIn("secret-value", str(raised.exception))
        request.assert_not_called()

    def test_http_error_body_is_not_logged(self):
        marker = "provider-reflected-marker"
        failure = urllib.error.HTTPError(
            "https://provider.example/api", 401, "Unauthorized", {}, io.BytesIO(marker.encode())
        )
        class FakeOpener:
            def open(self, request, timeout):
                raise failure

        with patch("kinoquence.providers.urllib.request.build_opener", return_value=FakeOpener()) as build_opener:
            with self.assertRaises(ProviderError) as raised:
                _request_json("https://provider.example/api", {}, {}, 5)
        self.assertNotIn(marker, str(raised.exception))
        self.assertTrue(any(isinstance(handler, _NoRedirectHandler) for handler in build_opener.call_args.args))

    def test_redirect_handler_refuses_all_redirect_targets(self):
        handler = _NoRedirectHandler()
        self.assertIsNone(handler.redirect_request(None, None, 307, "Temporary Redirect", {}, "https://elsewhere.example"))

    def test_invalid_generation_parameters_are_rejected(self):
        config = ProviderConfig(provider="openai", model="gpt-test", timeout=0)
        with self.assertRaises(ProviderError):
            generate_text(config, "system", "user")

    def test_unknown_provider_is_rejected(self):
        config = ProviderConfig(provider="mystery", model="test")
        with self.assertRaises(ProviderError):
            generate_text(config, "system", "user")


if __name__ == "__main__":
    unittest.main()
