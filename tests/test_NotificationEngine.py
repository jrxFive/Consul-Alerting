#!/usr/bin/env python
import unittest
import json as json
import consulalerting.settings as settings
import consulalerting.utilities as utilities
from consulalerting import NotificationEngine
from consulalerting import ConsulHealthStruct


KV_ALERTING_AVAILABLE_PLUGINS = ["hipchat", "slack", "mailgun"]

ALERT_LIST = [{"Node": "consul-agent",
               "CheckID": "serfHealth",
               "Name": "Serf Health Status",
               "Tags": ["devops", "consul", "mailgun", "hipchat"],
               "ServiceName": "",
               "Notes": "",
               "Status": "critical",
               "ServiceID": "",
               "Output": "Agent not live or unreachable"},
              {"Node": "consul-agent",
               "CheckID": "service:redis",
               "Name": "Service 'redis' check",
               "Tags": ["devops", "redis", "techops", "dev", "slack"],
               "ServiceName": "redis",
               "Notes": "",
               "Status": "critical",
               "ServiceID": "redis",
               "Output": "Usage: check_redis.py [options]\n\ncheck_redis.py: error: Warning level required\n"},
              {"Node": "consul",
               "CheckID": "serfHealth",
               "Name": "Serf Health Status",
               "Tags": ["dev", "consul"],
               "ServiceName": "",
               "Notes": "",
               "Status": "passing",
               "ServiceID": "",
               "Output": "Agent alive and reachable"},
              {"Node": "consul",
               "CheckID": "service:redis",
               "Name": "Service 'redis' check",
               "Tags": ["qa", "redis-slave"],
               "ServiceName": "redis",
               "Notes": "",
               "Status": "critical",
               "ServiceID": "redis",
               "Output": "Usage: check_redis.py [options]\n\ncheck_redis.py: error: Warning level required\n"}]



CONSUL_HEALTH_STRUCT_ALERT_LIST = [
    ConsulHealthStruct.ConsulHealthStruct(**obj) for obj in ALERT_LIST]


class NotificationEngineTests(unittest.TestCase):


    def setUp(self):
        self.ne = NotificationEngine.NotificationEngine(
            CONSUL_HEALTH_STRUCT_ALERT_LIST, settings.consul)
        self.ne.available_plugins = KV_ALERTING_AVAILABLE_PLUGINS
        self.ne.unique_tags = set(["hipchat", "mailgun"])

    def test_uniqueTags(self):
        unique_tags = self.ne.get_unique_tags_keys()
        self.assertEqual(len(unique_tags), len(set(
            ["devops", "consul", "mailgun", "hipchat", "redis", "techops", "dev", "slack", "qa", "redis-slave"])))

    def test_loadPluginsFromTags(self):
        hipchat, slack, mailgun, email, pagerduty, influxdb = self.ne.load_plugins_from_tags()
        self.assertFalse(email)
        self.assertTrue(hipchat)
        self.assertFalse(slack)
        self.assertTrue(mailgun)
        self.assertFalse(pagerduty)
        self.assertFalse(influxdb)


if __name__ == '__main__':
    unittest.main()
