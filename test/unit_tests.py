'''
Twilio Latrine - Unit Tests

Written by /rob, 30 August 2011
'''

import unittest
from google.appengine.ext import db
from google.appengine.ext import testbed
import latrine_models

class Test_Model(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()

    def tearDown(self):
        self.testbed.deactivate()

class Test_SmsModel(Test_Model):
    def test_insertSms(self):
        latrine_models.SmsModel().put()
        self.assertEqual(1, len(latrine_models.SmsModel().all().fetch(2)))
        
class Test_QueueModel(Test_Model):
    def test_insertQueue(self):
        latrine_models.QueueModel().put()
        self.assertEqual(1, len(latrine_models.QueueModel().all().fetch(2)))

class Test_CheckinModel(Test_Model):
    def test_insertCheckin(self):
        latrine_models.CheckinModel().put()
        self.assertEqual(1, len(latrine_models.CheckinModel().all().fetch(2)))