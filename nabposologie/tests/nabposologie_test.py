import json
import unittest

import pytest
from asgiref.sync import async_to_sync

from nabposologie.nabposologie import Nabposologie
from nabd.tests.mock import MockWriter, NabdMockTestCase
from nabd.tests.utils import close_old_async_connections


@pytest.mark.django_db
class TestNabposologie(unittest.TestCase):
    def tearDown(self):
        close_old_async_connections()

    def test_perform(self):
        service = Nabposologie()
        writer = MockWriter()
        service.writer = writer
        async_to_sync(service.perform)()
        self.assertEqual(len(writer.written), 1)
        packet = writer.written[0]
        packet_json = json.loads(packet.decode("utf8"))
        self.assertEqual(packet_json["type"], "message")
        self.assertFalse("signature" in packet_json)
        self.assertTrue("body" in packet_json)


@pytest.mark.django_db
class TestNabposologieRun(NabdMockTestCase):
    def tearDown(self):
        NabdMockTestCase.tearDown(self)
        close_old_async_connections()

    def test_connect(self):
        self.do_test_connect(Nabposologie)
