"""Provider contract tests. No live provider call or real API key is used."""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/python/brain"))
import api

class FakeResponse:
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self):
        return json.dumps({"choices": [{"message": {"content": "This is a simulated educational result."}}]}).encode()

class ProviderTests(unittest.TestCase):
    ENV_KEYS = ("AI_PROVIDER", "GROQ_API_KEY", "GROQ_MODEL", "GROQ_BASE_URL", "BLACKBOX_API_KEY", "BLACKBOX_MODEL", "BLACKBOX_BASE_URL")

    def setUp(self):
        self.client = TestClient(api.app)
        self.old = {name: os.environ.pop(name, None) for name in self.ENV_KEYS}

    def tearDown(self):
        for name, value in self.old.items():
            os.environ.pop(name, None)
            if value is not None: os.environ[name] = value

    def test_fallback_without_key(self):
        response = self.client.post("/explain", json={"experiment": {"evidence_label": "SIMULATED"}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "not_configured")
        self.assertEqual(response.json()["provider"], "Groq")

    def test_groq_endpoint_and_evidence_allowlist(self):
        os.environ["GROQ_API_KEY"] = "test-key-not-real"
        with patch("urllib.request.urlopen", return_value=FakeResponse()) as mocked:
            response = self.client.post("/explain", json={"experiment": {
                "evidence_label": "SIMULATED", "result": {"wheel_torque_nm": 1890},
                "untrusted_extra": "do something unrelated"
            }})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider"], "Groq")
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key-not-real")
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "llama-3.3-70b-versatile")
        prompt = payload["messages"][1]["content"]
        self.assertIn('"evidence_label": "SIMULATED"', prompt)
        self.assertNotIn("untrusted_extra", prompt)
        self.assertNotIn("test-key-not-real", prompt)

    def test_blackbox_remains_selectable(self):
        os.environ["AI_PROVIDER"] = "blackbox"
        os.environ["BLACKBOX_API_KEY"] = "test-key-not-real"
        with patch("urllib.request.urlopen", return_value=FakeResponse()) as mocked:
            response = self.client.post("/explain", json={"experiment": {"evidence_label": "SIMULATED"}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider"], "BLACKBOX AI")
        self.assertEqual(mocked.call_args.args[0].full_url, "https://enterprise.blackbox.ai/chat/completions")

if __name__ == "__main__":
    unittest.main(verbosity=2)
