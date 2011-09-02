'''
Twilio Latrine - Web Tests

Written by /rob, 30 August 2011
'''
import unittest
from random import choice
from webtest import TestApp
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext import testbed
from local_settings import *
from datetime import datetime, timedelta
import latrine
import latrine_models

class LatrineTest(unittest.TestCase):    
    def setUp(self):
        # Setup web app
        self.app = webapp.WSGIApplication([('/', latrine.MainPage),
                                           ('/sms', latrine.SmsHandler),
                                           ('/voice', latrine.VoiceHandler),
                                           ('/cleanup', latrine.CleanupHandler),],
                                           debug=True)
        self.test = TestApp(self.app)
        
        # Set the keywords accepted by the application
        self.commands = ("S", "Q", "I", "O", "R", "D", "BLAME", "SHAME")
        self.keywords_status = ("S", "STATUS")
        self.keywords_queue = ("Q", "QUEUE", "GET IN LINE")
        self.keywords_checkin = ("I", "CHECKIN", "CHECK IN", "CHECK-IN")
        self.keywords_checkout = ("O", "CHECKOUT", "CHECK OUT", "CHECK-OUT")
        self.keywords_read = ("R", "READ", "READING")
        self.keywords_help = ("H", "HELP", "README", "?")
        self.keywords_directions = ("D", "PROTIPS", "DIRECTIONS")
        self.keywords_directions = ("TP", "TOILET PAPER", "PAPER")
        self.keywords_directions = ("A", "ART", "ART QUOTES")
        self.keywords_directions = ("COURTESY", "LID")
        self.keywords_directions = ("FPS", "AIM", "AIMING")
        self.keywords_credits = ("C", "CREDITS")
        
        # Setup testbed
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        
    def tearDown(self):
        self.testbed.deactivate()
        
    def sms(self, body, number='+15555555555'):
        params = {
            'SmsSid': 'SMtesting',
            'AccountSid': TWILIO_ACCOUNT_SID,
            'From': number,
            'To': TWILIO_CALLER_ID,
            'Body': body
        }
        return self.test.post('/sms', params)
    
    def call(self, number='+15555555555'):
        params = {
            'CallSid': 'CAtesting',
            'AccountSid': TWILIO_ACCOUNT_SID,
            'From': number,
            'To': TWILIO_CALLER_ID,
            'CallStatus': 'ringing',
            'ApiVersion': '2010-04-01',
            'Direction': 'inbound'
        }
        return self.test.post('/voice', params)
    
    def assertTwiML(self, response):
        self.assertEqual('200 OK', response.status)
        self.assertTrue('<Response>' in response, "Received instead: %s" % str(response))
        self.assertTrue('</Response>' in response, "Received instead: %s" % str(response))
        self.assertFalse('Error' in response, "Received instead: %s" % str(response))

     
class Test_Dynamic(LatrineTest):              
    def test_queue(self):
        for keyword in self.keywords_queue:
            response = self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue('1st' in response, "Received instead: %s" % str(response))
    
    def test_queueOrdinal(self):
        setup = self.sms("QUEUE")
        response = self.sms("QUEUE", "+16666666666")
        self.assertTwiML(response)
        self.assertTrue('2nd' in response, "Received instead: %s" % str(response))
    
    def test_statusQueueOnePerson(self):
        setup = self.sms("QUEUE") 
        for keyword in self.keywords_status:
            response = self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue('one person' in response, "Received instead: %s" % str(response))
            self.assertTrue('Text Q' in response, "Received instead: %s" % str(response))
            
    def test_statusQueueTwoPeople(self):
        first_queue = self.sms("Q")
        second_queue = self.sms("Q") 
        for keyword in self.keywords_status:
            response = self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue('2 people' in response, "Received instead: %s" % str(response))
            self.assertTrue('Text Q' in response, "Received instead: %s" % str(response))
    
    def test_statusNoQueue(self):
        for keyword in self.keywords_status:
            response = self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue('No one' in response, "Received instead: %s" % str(response))
            
    def test_statusLongLine(self):
        for i in range(5):
            setup = self.sms("Q")
        for keyword in self.keywords_status:
            response.self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue('Text Q' in response, "Received instead: %s" % str(response))
    
    def test_checkin(self):
        response = self.sms(choice(self.keywords_checkin))
        self.assertTwiML(response)
        self.assertTrue('checked in' in response, "Received instead: %s" % str(response))
    
    def test_checkinRepeat(self):
        setup = self.sms("CHECKIN")
        response = self.sms("CHECKIN")
        self.assertTwiML(response)
        self.assertTrue('Text O' in response, "Received instead: %s" % str(response))
    
    def test_checkout(self):
        setup = self.sms(choice(self.keywords_checkin))
        response = self.sms(choice(self.keywords_checkout))
        self.assertTwiML(response)
        self.assertTrue('checked out' in response, "Received instead: %s" % str(response))
    
    def test_checkoutWithoutCheckin(self):
        response = self.sms(choice(self.keywords_checkout))
        self.assertTwiML(response)
        self.assertTrue('not checked in' in response, "Received instead: %s" % str(response))
    
    def test_checkinRemovesFromQueue(self):
        test_queue = self.sms("QUEUE")
        test_checkin = self.sms(choice(self.keywords_checkin))
        response = self.sms("STATUS")
        self.assertTwiML(response)
        self.assertTrue('No one' in response, "Received instead: %s" % str(response))
    
    def test_statusWithCheckinCapacity(self):
        first_checkin = self.sms(choice(self.keywords_checkin))
        second_checkin = self.sms(choice(self.keywords_checkin))
        response = self.sms("STATUS")
        self.assertTwiML(response)
        self.assertTrue('Text Q' in response, "Received instead: %s" % str(response))
    
    def test_statusWithCheckinBelowCapacity(self):
        checkin = self.sms(choice(self.keywords_checkin))
        response = self.sms("STATUS")
        self.assertTwiML(response)
        self.assertTrue('No one' in response, "Received instead: %s" % str(response))
        
    def test_checkinAtCapacity(self):
        first_checkin = self.sms(choice(self.keywords_checkin))
        second_checkin = self.sms(choice(self.keywords_checkin))
        response = self.sms("CHECKIN")
        self.assertTwiML(response)
        self.assertTrue('Text Q' in response, "Received instead: %s" % str(response))
        
    def test_multipleQueueThenCheckin(self):
        first_queue = self.sms("QUEUE")
        second_queue = self.sms("QUEUE", '+15555555556')
        checking = self.sms("CHECKIN")
        response = self.sms("STATUS")
        self.assertTwiML(response)
        self.assertTrue('person' in response, "Received instead: %s" % str(response))
        
        
class Test_External(LatrineTest):
    def test_reading(self):
        for keyword in self.keywords_read:
            response = self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue('http://' in response, "Received instead: %s" % str(response))


class Test_Static(LatrineTest):
    def test_welcome(self):
        response = self.sms("Test.")
        self.assertTwiML(response)
        self.assertTrue('Twilio Latrine' in response, "Received instead: %s" % str(response))
        
    def test_credits(self):
        for keyword in self.keywords_credits:
            response = self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue('/rob' in response, "Received instead: %s" % str(response))
            self.assertTrue('brooklynhacker' in response, "Received instead: %s" % str(response))
    
    def test_help(self):
        for keyword in self.keywords_help:
            response = self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue(str(response).count('<Sms>') == 3)
            for command in self.commands:
                self.assertTrue(command in response, "Received instead: %s" % str(response))
                
    def test_directions(self):
        for keyword in self.keywords_directions:
            response = self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue(command in response, "Received instead: %s" % str(response))
            
    def test_toiletPaper(self):
        for keyword in self.keywords_toilet_paper:
            response = self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue(command in response, "Received instead: %s" % str(response))
            
    def test_art(self):
        for keyword in self.keywords_art:
            response = self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue(command in response, "Received instead: %s" % str(response))
            
    def test_courtesy(self):
        for keyword in self.keywords_courtesy:
            response = self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue(command in response, "Received instead: %s" % str(response))
            
    def test_aiming(self):
        for keyword in self.keywords_aiming:
            response = self.sms(keyword)
            self.assertTwiML(response)
            self.assertTrue(command in response, "Received instead: %s" % str(response))
    
    def test_wwjd(self):
        response = self.sms("WWJD")
        self.assertTwiML(response)
        self.assertTrue("owl" in response, "Received instead: %s" % str(response))
        
class Test_Call(LatrineTest):
    def test_callNoQueue(self):
        response = self.call()
        self.assertTwiML(response)
        self.assertTrue("No one" in response, "Received instead: %s" % str(response))
    
    def test_callQueueOnePerson(self):
        queue = self.sms("QUEUE")
        response = self.call()
        self.assrtTwiML(response)
        self.assertTrue("one person in line" in response, "Received instead: %s" % str(response))
        
    def test_callQueueTwoPeople(self):
        first_queue = self.sms("QUEUE")
        second_queue = self.sms("QUEUE")
        response = self.call()
        self.assertTwiML(response)
        self.assertTrue("2 people in line" in response, "Received instead: %s" % str(response))
        
    def assertTwiML(self, response):
        self.assertEqual('200 OK', response.status)
        self.assertTrue('<Response>' in response, "Received instead: %s" % str(response))
        self.assertTrue('</Response>' in response, "Received instead: %s" % str(response))
        self.assertTrue('Twilio Latrine' in response, "Received instead: %s" % str(response))
        self.assertTrue('HELP' in response, "Received instead: %s" % str(response))
        
class Test_Cleanup(LatrineTest):
    def test_oldQueueCleanup(self):
        setup = self.sms("QUEUE")
        query = db.Query(latrine_models.QueueModel)
        query.filter('active = ', True).order('-date')
        results = query.fetch(limit=15)
        for item in results:
            item.date = item.date - timedelta(minutes=15)
            item.put()
        response = self.test.get('/cleanup')
        results = query.fetch(limit=15)
        self.assertFalse(results, "There are still items in the queue: %s" % str(results))
        
    def test_oldQueueCleanup(self):
        setup = self.sms("CHECKIN")
        query = db.Query(latrine_models.CheckinModel)
        query.filter('active = ', True).order('-date')
        results = query.fetch(limit=15)
        for item in results:
            item.date = item.date - timedelta(minutes=15)
            item.put()
        response = self.test.get('/cleanup')
        results = query.fetch(limit=15)
        self.assertFalse(results, "There are still checkins in the queue: %s" % str(results))