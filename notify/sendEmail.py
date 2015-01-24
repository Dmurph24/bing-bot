#!/usr/bin/env python

import MySQLdb
import time
import smtplib
import sys
import math
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ..pkg import db_config as DBConfig

db = DBConfig.db_connection()
cur = db.cursor()

def sendEmail(to,message):
    #Currently supports only gmail accounts
    #Feel free to modify this for any email account
    email = "youremail@gmail.com"
    password = "myemailpass"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Bing Bot"
    msg['From'] = email
    msg['To'] = to
    
    part1 = MIMEText(message, 'html')
    msg.attach(part1)
    
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(email,password)
    problems = server.sendmail(email,to,msg.as_string())
    server.quit()

#Start Email
msg = ""
to = "youremail@domain.com"

msg = "<!doctype html><html><head><link rel='stylesheet' type='text/css' href='http://www.netglowgames.com/old/Assets/LightFairCSS.css'>"
msg += "<meta charset='UTF-8'></head><body bgcolor='#EDEDED'><table class='tabletemplate' width=750px><tr class='tableHeader'>"
msg += "<td width=250px align=center><span>?&@</span></td>"
msg += "<td><br><table width=500px border=0px><tr class=tableHeader style='background-color:rgb(188,188,188); color:rgb(102,102,102);'><td>Account</td><td>New Points</td><td>Earned</td><td>Lifetime Credits</td></tr>"
    
class_str = "tableRow1"
totalPoints = 0
lifetimeTotalDollars = 0.0
moneyMade = 0.0
bannedFutureMoney = 0.0

cur.execute("SELECT Email, Points, PointsEarned, LifetimePoints, Banned FROM Accounts")
for row in cur.fetchall() :
    
    totalPoints += row[2]
    
    if row[3] > 525:
        lifetimeTotalDollars += 5.0 + (((row[3]-525.0)/475.0)*5.0)
        moneyMade += (math.floor((row[3]-525) / 475)*5) + 5.0
    else:
        lifetimeTotalDollars += ((row[3]/525.0)*5.0)

    if row[4] == "YES":
        if row[3] > 525:
            bannedFutureMoney += (((row[3]-525) % 475)/475.0)*5.0
        else:
            bannedFutureMoney += ((row[3]/525.0)*5.0)
    
    if row[4] == "NO":
        msg += "<tr class="+class_str+"><td>%25s</td><td>%6d</td><td>%6d</td><td>%16d</td></tr>" % (row[0], row[1], row[2], row[3])
        
        if class_str == "tableRow1":
            class_str = "tableRow2"
        else:
            class_str = "tableRow1"

msg += "</table><br><br>"

replace_str = "<b>%d Points Earned</b>" % totalPoints
replace_str += "<br><br>"
replace_str += "<b>$%.2f (Already received)</b><br><br><b>+ $%.2f (Future)</b><br><br><font size=6><b>= $%.2f</b></font>" % (moneyMade, lifetimeTotalDollars-moneyMade-bannedFutureMoney, lifetimeTotalDollars-bannedFutureMoney)

msg = msg.replace("?&@",replace_str)

moneyPerDay = totalPoints / 475.0
msg += "<font size=6><b>Estimated $%.2f today</b></font>" % (moneyPerDay*5)
msg += "<br><font size=3>(Assuming $5 is equal to 475 points)</font><br><br>"
    
msg += "</td></tr></table></body></html>"

sendEmail(to,msg)

cur.execute("UPDATE Settings Set SentEmail='YES'")
