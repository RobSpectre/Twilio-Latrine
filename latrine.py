'''
Twilio Latrine

Written by /rob, 30 August 2011.

My track jacket app - an SMS notification system for the restroom at Twilio.

'''

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
import logging
from xml.etree import ElementTree as etree
from random import choice
from twilio import twiml
# Workaround http://code.google.com/p/googleappengine/issues/detail?id=5064
import sys
sys.modules['ssl'] = None
from twilio import rest
import latrine_models
from local_settings import *
from datetime import datetime

'''
Controllers
'''

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("Sit comfortably with Twilio Latrine.")
        
    def renderTwiML(self, twiml_response_object):
        self.response.headers['Content-Type'] = 'text/xml'
        self.response.out.write(str(twiml_response_object))
        
class SmsHandler(MainPage):
    # Keyword routing
    def post(self):
        body = self.request.get("Body").upper()
        r = ""
        
        if body == "S" or "STATUS" in body:
            r = self.status()
        elif body == "Q" or "QUEUE" in body or "QUE" in body or "GET IN LINE" in body:
            r = self.queue()
        elif body == "IN" or body == "I" or "CHECKIN" in body or "CHECK IN" in body or "CHECK-IN" in body:
            r = self.checkIn()
        elif body == "OUT" or body == "O" or "CHECKOUT" in body or "CHECK OUT" in body or "CHECK-OUT" in body:
            r = self.checkOut()
        elif body == "READ" or body == "R" or "READING" in body:
            r = self.reading()
        elif body == "HELP" or body == "?" or body == "H" or "HELP" in body or "README" in body:
            r = self.help()
        elif body == "D" or "PROTIPS" in body or "DIRECTIONS" in body:
            r = self.directions()
        elif body == "TP" or "TOILET PAPER" in body or "PAPER" in body:
            r = self.toiletPaper()
        elif body == "A" or "ART" in body or "ART QUOTES" in body:
            r = self.art()
        elif "COURTESY" in body or "LID" in body:
            r = self.courtesy()
        elif body == "FPS" or "AIM" in body or "AIMING" in body:
            r = self.aiming()
        elif "FOOD" in body or "EAT" in body or "EATING" in body:
            r = self.eating()
        elif "FEBREEZE" in body or "FEBREZE" in body or "SPRAY" in body or "ODOR" in body:
            r = self.febreze()
        elif body == "WWJD":
            r = self.drawTheOwl()
        elif body == "C" or "CREDITS" in body:
            r = self.credits()
        else:
            r = twiml.Response()
            r.sms("Welcome to Twilio Latrine.  Text HELP for my commands.")
        
        if r:
            self.renderTwiML(r)
        else:
            self.renderTwiML("There was a Twilio Latrine Error.  The Latrine admin has been informed.")
    
    # Dynamic methods
    def status(self):
        r = twiml.Response()
        
        # Check for queue
        results = self.getActiveQueue()
        if results:
            if len(results) == 1:
                r.sms("There is one person in line.  Text Q to claim your spot.")
            else:
                r.sms("There are %i in line.  Text Q to claim your spot." % len(results))
            return r
        
        # Check for capacity checkins
        results = self.getActiveCheckins()
        if len(results) >= LATRINE_CAPACITY:
            r.sms("%i bathrooms are occupied.  Text Q to join the line." % len(results))
            return r
        
        r.sms("No one is in line - the coast is clear!")
        return r
    
    def queue(self):
        r = twiml.Response()
        number = self.request.get("From")
        queue = self.getActiveQueue()
        for position, item in enumerate(queue):
            if item.From == number:
                r.sms("You are %s in line." % self.ordinal(position + 1))
                return r
        
        queued = latrine_models.QueueModel()
        queued.SmsSid = self.request.get("SmsSid")
        queued.AccountSid = self.request.get("AccountSid")
        queued.From = number
        queued.Body = self.request.get("Body")
        queued.City = self.request.get("City")
        queued.State = self.request.get("State")
        queued.Zip = self.request.get("Zip")
        queued.Country = self.request.get("Country")
        queued.put()
        
        r.sms("You have been added to the queue. You are %s in line." % self.ordinal(len(queue) + 1))
        return r
    
    def reading(self):
        r = twiml.Response()
        result = urlfetch.fetch(LATRINE_NEWS)
        if result.status_code == 200:
            tree = etree.fromstring(result.content)
            item = choice(tree.findall("*/item"))
            link = item.find('link').text
            r.sms(link)
        else:
            r.sms("We were unable to find anything to read.  Might I recommend door vandalism?")
        return r
    
    def checkIn(self):
        r = twiml.Response()
        
        # Check if user is already checked in.
        number = self.request.get("From")
        results = self.getActiveCheckins()
        if len(results) >= LATRINE_CAPACITY:
            r.sms("It appears the restrooms are at capacity.  Please do not shit in the plants.")
            return r
        
        for checkin in results:
            if number == checkin.From:
                r.sms("Easy cowboy - you're already checked in. Text O to checkout.")
                return r
        
        # Check if user is in queue and remove.
        queue = self.removeFromQueue(number)
        
        # Check in user
        checkin = latrine_models.CheckinModel()
        checkin.SmsSid = self.request.get("SmsSid")
        checkin.AccountSid = self.request.get("AccountSid")
        checkin.From = self.request.get("From")
        checkin.Body = self.request.get("Body")
        checkin.City = self.request.get("City")
        checkin.State = self.request.get("State")
        checkin.Zip = self.request.get("Zip")
        checkin.Country = self.request.get("Country")
        checkin.put()
        
        r.sms("You are checked in - thank you for your courtesy.")
        return r
    
    def checkOut(self):
        number = self.request.get("From")
        results = self.getActiveCheckins(number)
        
        r = twiml.Response()
        if not results:
            r.sms("You are not checked in, but I appreciate your enthusiasm.  Text I to check in.")
        else:
            for checkin in results:
                checkin.active = False
                checkin.put()
            r.sms("Thank you again - you are now checked out.")
        return r
    
    def removeFromQueue(self, number):
        results = self.getActiveQueue(number)
        if not results:
            # Number is not in the queue
            return False        
        else:
            # Remove from queue
            for queue in results:
                queue.active = False
                queue.put()
                
            # Notify person next in line
            results = self.getActiveQueue()
            if results:
                next_user = results.pop(0)
                self.outgoingSms(next_user.From, "You are next in line for the restroom.  Gods be praised.")
            # User is in the queue and has successfully been removed.    
            return True           
    
    def getActiveCheckins(self, number=False):
        query = db.Query(latrine_models.CheckinModel)
        if number:
            query.filter('active = ', True).filter('From = ', number).order('-date')
        else:
            query.filter('active = ', True).order('-date')
        return query.fetch(limit=5)
        
    def getActiveQueue(self, number=False):
        query = db.Query(latrine_models.QueueModel)
        if number:
            query.filter('active = ', True).filter('From = ', number).order('-date')
        else:
            query.filter('active = ', True).order('-date')
        return query.fetch(limit=5)
    
    
    # Static methods    
    def help(self):
        r = twiml.Response()
        r.sms("Twilio Latrine HELP: Text S to see if there is a line.  Text Q to GET IN LINE. Text I to CHECKIN... (cont'd)")
        r.sms("HELP (pg. 2): Text O to CHECKOUT.  Text R to get something to READ.  Text D for PROTIPS. (done)")
        return r
    
    def directions(self):
        r = twiml.Response()
        r.sms("Need help using the restroom?  Text TP to learn to refill TOILET PAPER.  Text A to get tips on ART (cont'd)")
        r.sms("Text COURTESY for instructions on lid management.  Text FPS for help with AIMING.")
        return r
    
    def toiletPaper(self):
        r = twiml.Response()
        r.sms("1) Remove empty roll from dispenser.  2) Retrieve new roll from shelf.  3) Input new roll into dispenser. (cont'd)")
        r.sms("4) Revel in the warm glow of humanity's appreciation.")
        return r
    
    def art(self):
        art_quotations = []
        art_quotations.append("A man paints with his brains and not with his hands. - Michelangelo")
        art_quotations.append("Lesser artists borrow, great artists steal. - Igor Stravinsky")
        art_quotations.append("Life imitates art far more than art imitates Life. - Oscar Wilde")
        art_quotations.append("I don't do drugs.  I am drugs. - Salvador Dali")
        art_quotations.append("The holy grail is to spend less time making the picture than it takes people to look at it. - Banksy")
        art_quotations.append("Ding a ding dang my dang a long ling long. - Al Jourgensen")
        r = twiml.Response()
        r.sms(choice(art_quotations))
        return r
    
    def courtesy(self):
        r = twiml.Response()
        r.sms("Leave the lid down.  What are you? An ape?")
        return r   
    
    def aiming(self):
        r = twiml.Response()
        r.sms("Play more Team Fortress 2 as the Sniper class.  Pump shotgun in CoD will not help you in here.")
        return r   

    def credits(self):
        r = twiml.Response()
        r.sms("Written by /rob, 30 August 2011.  http://www.brooklynhacker.com")
        return r
    
    def eating(self):
        r = twiml.Response()
        r.sms("Do not shit where you eat, and do not eat where you shit. - Lisa, Sep 2011")
        return r
    
    def febreze(self):
        r = twiml.Response()
        r.sms("If you apply a generous Febrezing to the bathroom, wipe off the seat when you're done.  - Shawn, Sep 2011")
        return r
    
    def drawTheOwl(self):
        r = twiml.Response()
        r.sms("Draw the fucking owl!")
        return r
    
    # Utility Methods 
    def outgoingSms(self, number, body):
        client = rest.TwilioRestClient()
        return client.sms.messages.create(to=number,
                                          from_=TWILIO_CALLER_ID,
                                          body=body)
    
    def handle_exception(self, e, debug):
        logging.exception(e)
        r = twiml.Response()
        r.sms("There was an error processing your request.  The Latrine administrator has been notified.")
        self.renderTwiML(r)
        
    def ordinal(self, n):
        if 10 < n < 14: return '%sth' % n
        if n % 10 == 1: return '%sst' % n
        if n % 10 == 2: return '%snd' % n
        if n % 10 == 3: return '%srd' % n
        return '%sth' % n
        

class VoiceHandler(MainPage):
    def post(self):
        r = twiml.Response()
        r.say("Welcome to Twilio Latrine.") 
        
        results = self.getActiveQueue()
        if results:
            if len(results) == 1:
                r.say("There is one person in line.")
            else:
                r.say("There are %i people in line." % len(results))
        else:
            r.say("No one is currently in line.")
     
        r.say("Text HELP to this number for instructions.")
        self.renderTwiML(r)
        
    def getActiveQueue(self, number=False):
        query = db.Query(latrine_models.QueueModel)
        if number:
            query.filter('active = ', True).filter('From = ', number).order('-date')
        else:
            query.filter('active = ', True).order('-date')
        return query.fetch(limit=5)

class CleanupHandler(webapp.RequestHandler):
    def get(self):
        queue = self.getActiveQueue()
        for item in queue:
            if (datetime.now() - item.date).seconds >= LATRINE_AGE_THRESHOLD:
                item.active = False
                item.put()
                
        checkins = self.getActiveCheckins()
        for item in checkins:
            if (datetime.now() - item.date).seconds >= LATRINE_AGE_THRESHOLD:
                item.active = False
                item.put()
                
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("Remaining queue: %s\n Remaining checkins: %s" % (str(self.getActiveQueue()), str(self.getActiveCheckins())))
    
    def getActiveQueue(self):
        query = db.Query(latrine_models.QueueModel)
        query.filter('active = ', True).order('-date')
        return query.fetch(limit=1000)
    
    def getActiveCheckins(self):
        query = db.Query(latrine_models.CheckinModel)
        query.filter('active = ', True).order('-date')
        return query.fetch(limit=1000)   


application = webapp.WSGIApplication([('/', MainPage),
                                      ('/sms', SmsHandler),
                                      ('/voice', VoiceHandler),
                                      ('/cleanup', CleanupHandler)],
                                     debug=True)
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()