#!/usr/bin/env python

#
# developed by Sergey Markelov and Daniel Murphy (2013)
#

from __future__ import absolute_import

import HTMLParser
import getopt
import os
import random
import sys
import time
import urllib2
import socket
import fcntl
import struct
import MySQLdb

from socket import error as SocketError
import errno

sys.path.append(os.path.join(os.path.dirname(__file__), "pkg"))
sys.path.append(os.path.join(os.path.dirname(__file__), "pkg", "queryGenerators"))

from bingAuth import BingAuth, AuthenticationError
from bingRewards import BingRewards
from config import BingRewardsReportItem, Config, ConfigError
from eventsProcessor import EventsProcessor
import db_config as DBConfig
import bingCommon
import bingFlyoutParser as bfp
import helpers
from helpers import BingAccountError 

verbose = False
totalPoints = 0
ip_change = False
ip_address = ""
MachineID = 1

SCRIPT_VERSION = "4.0"
SCRIPT_DATE = "January, 2015"
account_counter = 1

db = DBConfig.db_connection()
cur = db.cursor()

def earnRewards(config, httpHeaders, userAgents, reportItem, password):
    """Earns Bing! reward points and populates reportItem"""
    noException = False
    try:
        if reportItem is None: raise ValueError("reportItem is None")
        if reportItem.accountType is None: raise ValueError("reportItem.accountType is None")
        if reportItem.accountLogin is None: raise ValueError("reportItem.accountLogin is None")
        if password is None: raise ValueError("password is None")

        del reportItem.error
        reportItem.error = None
        reportItem.pointsEarned = 0

        bingRewards = BingRewards(httpHeaders, userAgents, config)
        bingAuth    = BingAuth(httpHeaders, bingRewards.opener)
        bingAuth.authenticate(reportItem.accountType, reportItem.accountLogin, password)
        reportItem.oldPoints = bingRewards.getRewardsPoints()
        rewards = bfp.parseFlyoutPage(bingRewards.requestFlyoutPage(), bingCommon.BING_URL)

        if verbose:
            bingRewards.printRewards(rewards)
        results = bingRewards.process(rewards)

        if verbose:
            print
            print "-" * 80
            print

        bingRewards.printResults(results, verbose)

        reportItem.newPoints = bingRewards.getRewardsPoints()
        reportItem.lifetimeCredits = bingRewards.getLifetimeCredits()
        reportItem.pointsEarned = reportItem.newPoints - reportItem.oldPoints
        reportItem.pointsEarnedRetrying += reportItem.pointsEarned
        print
        print "%s - %s" % (reportItem.accountType, reportItem.accountLogin)
        print
        print "Points before:    %6d" % reportItem.oldPoints
        print "Points after:     %6d" % reportItem.newPoints
        print "Points earned:    %6d" % reportItem.pointsEarned
        print "Lifetime Credits: %6d" % reportItem.lifetimeCredits

        print
        print "-" * 80

        noException = True

    except AuthenticationError, e:
        reportItem.error = e
        print "AuthenticationError:\n%s" % e

    except HTMLParser.HTMLParseError, e:
        reportItem.error = e
        print "HTMLParserError: %s" % e

    except urllib2.HTTPError, e:
        reportItem.error = e
        print "The server couldn't fulfill the request."
        print "Error code: ", e.code

    except urllib2.URLError, e:
        reportItem.error = e
        print "Failed to reach the server."
        print "Reason: ", e.reason

    except SocketError as e:
        if e.errno != errno.ECONNRESET:
            raise

        # see http://stackoverflow.com/a/20568874/2147244
        # for explanation of the problem

        reportItem.error = e
        print "Connection reset by peer."

        except BingAccountError as e:
            reportItem.error = e
            print "BingAccountError: %s" % e
    finally:
        if not noException:
            print
            print "For: %s - %s" % (reportItem.accountType, reportItem.accountLogin)
            print
            print "-" * 80


def usage():
    print "Usage:"
    print "    -h, --help               show this help"
    print
    print "    -f, --configFile=file    use specific config file. Default is config.xml"
    print
    print "    -r, --full-report        force printing complete report at the end. Note: complete report will be"
    print "                             printed anyway if more than one account was processed and cumulative"
    print "                             points earned is more than zero"
    print
    print "    -v, --verbose            print verbose output"
    print
    print "        --version            print version info"

def printVersion():
    print "Bing! Rewards Automation script: <http://sealemar.blogspot.com/2012/12/bing-rewards-automation.html>"
    print "Version: " + SCRIPT_VERSION + " from " + SCRIPT_DATE
    print "See 'version.txt' for the list of changes"
    print "This code is published under LGPL v3 <http://www.gnu.org/licenses/lgpl-3.0.html>"
    print "There is NO WARRANTY, to the extent permitted by law."
    print
    print "Developed by: Sergey Markelov"

def __stringifyAccount(reportItem, strLen):
    if strLen < 15:
        raise ValueError("strLen too small. Must be > " + 15)

    s = ""

    l = strLen - len(s)

    if len(reportItem.accountLogin) < l:
        s += reportItem.accountLogin
    else:
        s += reportItem.accountLogin[:(l - 3)]
        s += "..."

    return s

#def get_ip_address(ifname):
#    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#    return socket.inet_ntoa(fcntl.ioctl(
#        s.fileno(),
#        0x8915,  # SIOCGIFADDR
#        struct.pack('256s', ifname[:15])
#    )[20:24])

def __processAccount(config, httpHeaders, userAgents, reportItem, accountPassword):
    global totalPoints
    global account_counter
    global ip_address
    global ip_change
    eventsProcessor = EventsProcessor(config, reportItem)

#    while (account_counter > 3 and ip_change==True):
# 
#        if ip_address != str(get_ip_address('eth0')):
#            account_counter = 1
#        else:
#            print "Waiting for IP Address to change before proceeding"
#            time.sleep(10)

#    ip_address = str(get_ip_address('eth0'))
#    print "IP ADDRESS: %s" % (ip_address)
#    reportItem.ip_address = str(ip_address)

    while True:
        reportItem.retries += 1

        if reportItem.retries > 1:
            print "retry #" + str(reportItem.retries)

        earnRewards(config, httpHeaders, userAgents, reportItem, accountPassword)
        totalPoints += reportItem.pointsEarned

        result, extra = eventsProcessor.processReportItem()
        if result == EventsProcessor.OK:
            break
        elif result == EventsProcessor.RETRY:
            time.sleep(extra)
        else:
            # TODO: implement as Utils.warn() or something
            print "Unexpected result from eventsProcessor.processReportItem() = ( %s, %s )" % (result, extra)
            break

    account_counter += 1
    
    #Get old points from server
    oldPoints = 0
    cur.execute("SELECT Points FROM Accounts WHERE Email='%s'" % reportItem.accountLogin)
    for row in cur.fetchall() :
        oldPoints = row[0]

    #Set account as completed
    pointsEarned = reportItem.newPoints - oldPoints
    if pointsEarned < 0:
        if reportItem.lifetimeCredits < 1000:
            pointsEarned += 525
        else:
            pointsEarned += 475
    cur.execute("UPDATE Accounts SET RanToday='YES', Points=%d, PointsEarned=%d, LifetimePoints=%d WHERE Email='%s'" % (reportItem.newPoints, pointsEarned, reportItem.lifetimeCredits, reportItem.accountLogin))


def __processAccountUserAgent(config, account_name, account_pass, userAgents, doSleep):
# sleep between two accounts logins
    if doSleep:
        extra = config.general.betweenAccountsInterval + random.uniform(0, config.general.betweenAccountsSalt)
        time.sleep(extra)

    reportItem = BingRewardsReportItem()
    reportItem.accountType  = "Live"
    reportItem.accountLogin = account_name

    agents = bingCommon.UserAgents.generate()

    httpHeaders = bingCommon.HEADERS
    httpHeaders["User-Agent"] = userAgents[ random.randint(0, len(userAgents) - 1) ]
    __processAccount(config, httpHeaders, agents, reportItem, account_pass)

    return reportItem

def __run(config):

    global MachineID
#    global ip_address

    report = list()

    doSleep = False

#    ip_address = str(get_ip_address('eth0'))
    
    num_accounts = 0
    cur.execute("SELECT Email,Password FROM Accounts WHERE RanToday='NO' AND Banned='NO' AND MachineID=%d ORDER BY RAND()" % (MachineID))
    for row in cur.fetchall() :
        
        account_name = row[0]
        account_pass = row[1]
        reportItem = __processAccountUserAgent(config, account_name, account_pass, bingCommon.USER_AGENTS_PC, doSleep)
        report.append(reportItem)
        doSleep = True
        num_accounts += 1
    
    sentEmail = "-"
    cur.execute("SELECT SentEmail FROM Settings")
    for row in cur.fetchall() :
        sentEmail = row[0]
    
    if num_accounts > 0:
        cur.execute("SELECT COUNT(*) FROM Accounts WHERE RanToday='NO' AND Banned='NO'")
        for row in cur.fetchall() :
            if row[0]==0 and sentEmail=="NO":
                EventsProcessor.onScriptComplete(config)

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:rv", ["help", "configFile=", "full-report", "verbose", "version"])
    except getopt.GetoptError, e:
        print "getopt.GetoptError: %s" % e
        usage()
        sys.exit(1)

    configFile = os.path.join(os.path.dirname(__file__), "config.xml")
    showFullReport = False
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-f", "--configFile"):
            configFile = a
        elif o in ("-r", "--full-report"):
            showFullReport = True
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o == "--version":
            printVersion()
            sys.exit()
        else:
            raise NotImplementedError("option '" + o + "' is not implemented")

    print "%s - script started" % helpers.getLoggingTime()
    print "-" * 80
    print

    helpers.createResultsDir(__file__)

    config = Config()

    try:
        config.parseFromFile(configFile)
    except IOError, e:
        print "IOError: %s" % e
        sys.exit(2)
    except ConfigError, e:
        print "ConfigError: %s" % e
        sys.exit(2)

    try:
        __run(config)
    except BaseException, e:
        EventsProcessor.onScriptFailure(config, e)

