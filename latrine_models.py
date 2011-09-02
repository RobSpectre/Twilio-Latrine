'''
Models
'''

from google.appengine.ext import db

class SmsModel(db.Model):
    SmsSid = db.StringProperty()
    AccountSid = db.StringProperty()
    From = db.StringProperty()
    Body = db.StringProperty()
    City = db.StringProperty()
    State = db.StringProperty()
    Zip = db.StringProperty()
    Country = db.StringProperty()
    active = db.BooleanProperty(default=True)
    date = db.DateTimeProperty(auto_now_add=True)
    
class QueueModel(SmsModel):
    notified = db.BooleanProperty(default=False)
    
class CheckinModel(SmsModel):
    knocks = db.IntegerProperty(default=0)