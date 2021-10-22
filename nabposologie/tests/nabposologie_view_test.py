from django.test import Client, TestCase

from nabposologie.models import Config


class TestView(TestCase):
    def setUp(self):
        Config.load()

    def test_get_settings(self):
        c = Client()
        response = c.get("/nabposologie/settings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "nabposologie/settings.html")
        self.assertTrue("config" in response.context)
        config = Config.load()
        self.assertEqual(response.context["config"], config)
        self.assertEqual(config.enabled, True)

    def test_toggle(self):
        c = Client()
        response = c.post("/nabposologie/settings", {"enabled": "false"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "nabposologie/settings.html")
        self.assertTrue("config" in response.context)
        config = Config.load()
        self.assertEqual(response.context["config"], config)
        self.assertEqual(config.enabled, False)
        response = c.post("/nabposologie/settings", {"enabled": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "nabposologie/settings.html")
        self.assertTrue("config" in response.context)
        config = Config.load()
        self.assertEqual(response.context["config"], config)
        self.assertEqual(config.enabled, True)
