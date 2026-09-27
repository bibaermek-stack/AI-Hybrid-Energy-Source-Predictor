"""
The app's offline mode: the last good replies are kept on the phone
(mobile/offline_cache.py) and shown, with their time, when the server
cannot be reached.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from unittest import mock


class OfflineCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {"ECOPREDICT_CACHE_DIR": self.tmp.name})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()


class TestOfflineCache(OfflineCase):
    def test_round_trip_and_bad_files(self):
        from mobile import offline_cache

        self.assertIsNone(offline_cache.get("GET /labs"))
        offline_cache.put("GET /labs", {"labs": [1, 2]})
        value, saved_at = offline_cache.get("GET /labs")
        self.assertEqual(value, {"labs": [1, 2]})
        self.assertGreater(saved_at, 0)
        # a damaged file reads as "nothing saved", not as an error
        path = offline_cache._path("GET /labs")
        path.write_text("{not json", encoding="utf-8")
        self.assertIsNone(offline_cache.get("GET /labs"))
        offline_cache.put("GET /x", {"a": 1})
        offline_cache.clear()
        self.assertIsNone(offline_cache.get("GET /x"))


class TestClientFallsBackToSavedReplies(OfflineCase):
    def setUp(self):
        super().setUp()
        from mobile.state import state

        self.state = state
        self.saved = (state.lang, state.api_base_url)
        state.lang, state.api_base_url = "kk", "https://api.example"

    def tearDown(self):
        self.state.lang, self.state.api_base_url = self.saved
        super().tearDown()

    def test_labs_list_offline_shows_the_saved_list_with_its_time(self):
        from mobile import api_client as mod

        client = mod.APIClient()
        with mock.patch.object(mod, "_http_get_sync", return_value={"labs": [{"id": "a"}]}):
            self.assertEqual(asyncio.run(client.labs_list()), [{"id": "a"}])
        self.assertEqual(client.cache_note("labs"), "")
        with mock.patch.object(mod, "_http_get_sync", return_value=None):
            self.assertEqual(asyncio.run(client.labs_list()), [{"id": "a"}])
        note = client.cache_note("labs")
        self.assertTrue(note.startswith("📴 Желі жоқ"), note)
        # back online: the note goes away
        with mock.patch.object(mod, "_http_get_sync", return_value={"labs": []}):
            asyncio.run(client.labs_list())
        self.assertEqual(client.cache_note("labs"), "")

    def test_nothing_saved_still_reads_as_unavailable(self):
        from mobile import api_client as mod

        client = mod.APIClient()
        with mock.patch.object(mod, "_http_get_sync", return_value=None):
            self.assertIsNone(asyncio.run(client.get_metrics()))
        self.assertEqual(client.cache_note("metrics"), "")

    def test_predictions_are_saved_per_input(self):
        from mobile import api_client as mod

        client = mod.APIClient()
        args = (800, 25, 35, 12, 1, 6, 5, 180, 1000)
        with mock.patch.object(mod, "_http_post_sync", return_value={"solar_power": 42.0}):
            asyncio.run(client.predict(*args))
        with mock.patch.object(mod, "_http_post_sync", return_value=None):
            self.assertEqual(asyncio.run(client.predict(*args)), {"solar_power": 42.0})
            self.assertTrue(client.cache_note("predict"))
            # other inputs were never answered: no stale answer for them
            self.assertIsNone(asyncio.run(client.predict(100, *args[1:])))

    def test_lab_tests_are_saved_per_language(self):
        from mobile import api_client as mod

        client = mod.APIClient()
        with mock.patch.object(mod, "_http_get_sync", return_value={"questions": ["kk"]}):
            asyncio.run(client.lab_test("lab_pv_physics"))
        self.state.lang = "en"
        with mock.patch.object(mod, "_http_get_sync", return_value=None):
            self.assertIsNone(asyncio.run(client.lab_test("lab_pv_physics")))
        self.state.lang = "kk"
        with mock.patch.object(mod, "_http_get_sync", return_value=None):
            self.assertEqual(asyncio.run(client.lab_test("lab_pv_physics")), {"questions": ["kk"]})


if __name__ == "__main__":
    unittest.main()
