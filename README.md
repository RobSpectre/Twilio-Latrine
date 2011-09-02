Twilio Latrine - A Twilio-powered SMS app for managing restroom courtesy.
================================

Latrine is an SMS interface for maintaining a courteous restroom environment in the workplace. It features a queue for getting
in line for the restroom without leaving your desk, checkin/checkout for notifying others when the restroom is full (anonymously, 
of course), directions for those who might be confused, and a bunch of other fun easter eggs.

Text HELP to (415) 237-2388 to see it in action.


Usage
-------------------------

Latrine is operated via SMS by a team sharing the same limited restroom resources.  It accepts the following commands:

* STATUS 	- Text S to check if the restrooms are occupied.
* QUEUE 	- Text Q to get in line for the restroom.
* CHECKIN 	- Text I to signal you are entering the restroom.
* CHECKOUT 	- Text O to signal you are exiting the restroom.
* READ 		- Text R to get something to read while you're in there.
* PROTIPS	- Text D if you need assistance using the facilities.

Each command is thoroughly aliased in order to be forgiving - most commands are only one or two characters.
There are a bunch more commands that aren't listed here - see if you can find them all.

Also all queue / checkin events expire after 15 minutes - you do not need to always remember to check in and check out every
single time.  This maintains a pragmatic state of your restroom situation as the day goes on.


Installing
-------------------------

Latrine runs on Google App Engine.  To install, follow these steps:

1. Install the [Google App Engine SDK for Python](http://code.google.com/appengine/downloads.html#Google_App_Engine_SDK_for_Python)
1. Clone [this repository](git@github.com:RobSpectre/Twilio-Latrine.git).
1. Change the value of application in app.yaml.
1. Add your Twilio credentials and restroom configuration to local_settings.py
1. Deploy to Google App Engine

<pre>
    appcfg.py update twiliolatrine/
</pre>


Testing
-------------------------

Latrine uses [GAEUnit](http://code.google.com/p/gaeunit/).  To run the tests, launch the dev server and visit the 
[/test endpoint](http://localhost:8080/test)in your browser.

<pre>
	dev_appserver.py twiliolatrine
	wget http://localhost:8080/test
</pre> 


About
-------------------------
This work is licensed under GPLv3.  Created by Rob Spectre.  Crafted for my first demonstration to Twilio, Inc.
Thanks for the track jacket - let's draw some fucking owls.
