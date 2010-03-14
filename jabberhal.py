#!/usr/bin/python
# JabberHAL - A simple Jabber chatbot using MegaHAL

# Credits:
# MegaHAL -> http://megahal.alioth.debian.org
# Howie -> http://howie.sourceforge.net

import sys
import getpass
import random
import time
import os

import xmpp
import simplehal

class JabberBot():
    def __init__(self, username=""):
        try:
            account = username
            if account == "": raise KeyError
        except KeyError: account = raw_input("account: ")
        try:
            password = ""
            if password == "": raise KeyError
        except KeyError: password = getpass.getpass("password for %s: " % account)
        
        # Read max delay
        try: self._maxdelay = 3
        except KeyError: self._maxdelay = 0

    	self._jid = xmpp.JID(account)
    	username,server = self._jid.getNode(),self._jid.getDomain()

        # Connect to server through SSL
        self._con = xmpp.Client(server,debug=None)
        if not self._con.connect():#server=(server,port)):
            sys.stderr.write("JABBER: Couldn't connect to %s: network error\n" % server)
            return

        # Register event handlers
        self._con.RegisterHandler('message',self._messageCB)
        self._con.RegisterHandler('presence',self._presenceCB)
        self._con.RegisterHandler('iq',self._iqCB)
        
        # Log in
        if self._con.auth(username,password):#,resource):
            pass
        else:
            print "JABBER ERROR: login failed:", self._con.lastErr, self._con.lastErrCode
            return

        # Request roster
        self._con.sendInitPresence()

        # start megahal
        self._hal = simplehal.SimpleHAL()
        if os.path.exists('jabberhal.db'):
            self._hal.load('jabberhal.db')

        print "Bot started!"

        
    def run_forever(self):
        while True:
            time.sleep(1)
            self._con.Process(1)
            # If connection is broken, restore it
            if not self._con.isConnected(): self._con.reconnectAndReauth()


    def display(self, output, user):
        # "user" must be a legitimate JID (user@server)
        msg = xmpp.Message(user, output.strip())
        msg.setType('chat')
        self._con.send(msg)

    def _messageCB(self, con, msg):
        """Called when a message is recieved"""
        if not msg.getBody(): # Dont process blank messages
            return
        # Jabber IDs contain a slash between the server name and the
        # resource name.  This presents a problem, since Alice uses
        # the session name as the filename for the log/session files.
        # So the session name for Jabber sessions is just
        # "username@server".
        source = str(msg.getFrom()).split("/")[0]
        # message body is Unicode, and Alice currently doesn't like
        # Unicode.  Convert it to ASCII with str() before submitting.
        #response = self.submit(str(msg.getBody()), source+"@JABBER")
 
        try:
            q = str(msg.getBody())
            response = self._hal.respond(q)
        except UnicodeEncodeError:
            response = "I don't understand your language! Do you speak English?"

        time.sleep( random.random() * self._maxdelay )
        self.display(response, source)

    def _presenceCB(self, con, prs):
        """Called when a presence is recieved"""
        who = str(prs.getFrom())
        type = prs.getType()
        if type == None: type = 'available'

        # subscription request: 
        # - accept their subscription
        # - send request for subscription to their presence
        if type == 'subscribe':
            #print u"subscribe request from %s" % (who)
            con.send(xmpp.Presence(to=who, typ='subscribed'))
            con.send(xmpp.Presence(to=who, typ='subscribe'))

        # unsubscription request: 
        # - accept their unsubscription
        # - send request for unsubscription to their presence
        elif type == 'unsubscribe':
            #print u"unsubscribe request from %s" % (who)
            con.send(xmpp.Presence(to=who, typ='unsubscribed'))
            con.send(xmpp.Presence(to=who, typ='unsubscribe'))

        #elif type == 'subscribed':
        #    print u"we are now subscribed to %s" % (who)

        #elif type == 'unsubscribed':
        #    print u"we are now unsubscribed to %s"  % (who)

        #elif type == 'available':
        #    print u"%s is available (%s / %s)" % (who, prs.getShow(), prs.getStatus())
        #elif type == 'unavailable':
        #    print u"%s is unavailable (%s / %s)" % (who, prs.getShow(), prs.getStatus())

    def _iqCB(self, con,iq):
        """Called when an iq is recieved, we just let the library handle it at the moment"""
        pass

# the main function
def main():
    if len(sys.argv)<2:
        print "Usage: %s username@server.com" % sys.argv[0]
        return 0

    try:
        bot = JabberBot(sys.argv[1])
        bot.run_forever()        
    except KeyboardInterrupt: 
        print     
    finally:  
        bot._hal.save('jabberhal.db')

# if this file is run directly, call main.
if __name__ == "__main__":
    main()

