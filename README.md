BingBot
===========

This is built off of Sealemar's BingReward program, however it supports Database interaction and a better email with html.

https://github.com/sealemar/BingRewards

This script will allow you to run an unlimited number of accounts on bing rewards (5 for each IP address you own). It uses a DB, which I will explain how to configure, to sync all your accounts together if you are using multiple machines.
This is made for any device that can run python, but is optimized for linux-based OS.

1a) Quick Database Configuration
===========================
Import db_setup.sql to your server or run the SQL in the file to setup your DB quickly

1b) Manual DataBase Configuration
======================
  a) Using your own personal server, create a DB called "BingRewards"

  b) Create 3 tables : Accounts, Machines, Settings

  c) Add the following fields to Accounts:

	ID (primary,int,AI), Email(varchar), Password(varchar), Points(int, default=0), PointsEarned(int, default=0), LifetimePoints(int, default=0), RanToday(varchar, default=NO), MachineID(int), Banned(varchar, default=NO)


  d) Add the following columns to Machines:

	ID (primary,AI), Name(varchar)


  e) Add the following column to Settings:

	SentEmail(varchar, default=NO)

  f) Run the following SQL command:

	INSERT INTO Settings VALUES ("NO")

1c) Add data to Database
====================
  a) Enter in all of your accounts to the Accounts table. All "Points" columns should default to zero, banned and RanToday should be set to "NO". 


```
INSERT INTO `BingRewards`.`Accounts` (`ID`, `Email`, `Password`, `Points`, `PointsEarned`, `LifetimePoints`, `RanToday`, `MachineID`, `Banned`) VALUES (NULL, 'myfakebingemail@gmail.com', 'mypassword', '0', '0', '0', 'NO', '1', 'NO');
```

  b) Enter in all of your Machines that will be running your program. Simply give them a name when you add them.


```
INSERT INTO `BingRewards`.`Machines` (ID, Name) VALUES (3, 'My Server')
```

2) Database Credentials (pkg/db_config.py)
==================================
Replace the host, user, and password with your own

```
db = MySQLdb.connect(host="your.hostname.com",
                     user="myuser",
                     passwd="mypass",
                     db="BingRewards")
```


3) Library Requirements
==================
Install MySQL on the device

	sudo apt-get install python-mysqldb

In some cases this library will not be on the PYTHONPATH. If this is the case, you will need to update every place main.py is called. This would be in crontab and config.xml


	/usr/bin/pythonX.X /path/to/bing-bot/main.py


4) main.py
=======
Change MachineID to the value specified in the DB correlating to the machine. (The declaration is somewhere at the head of the script)


```
MachineID = 2
```


5) notify/SendEmail.py
==================
Set email senders account (username and password)

This is the email that will send a summary of the account points you have earned to you


```
    #Currently supports only gmail accounts
    #Feel free to modify this for any email account
    email = "youremail@gmail.com"
    pass = "yourpass"
```

Also, you must specify what email you want to receive the alert with:


```
to = "youremail@domain.com"
```


6) config.xml
=========
Make sure all your directories for events are correct. They wont be, so you will have to fix this.

For example, change 'usr' to your current account on the machine (this has multiple occurrences):

	<notify cmd="/home/usr/bing-bot/notify/onError.sh %a %p %r %P %l %i %e" />
	...
	<notify cmd="cd /home/usr &amp;&amp; python -m bing-bot.notify.sendEmail" />
	...
	<notify cmd="/home/usr/bing-bot/notify/onScriptFailure.sh -mail" />
	...

You can also change the salts between searches, accounts, etc.

	<general
        betweenQueriesInterval="10.0"
        betweenQueriesSalt="8.0"
        betweenAccountsInterval="120"
        betweenAccountsSalt="900" />

7) Crontab 
=======

To get into cron:

	crontab -e

Then add these lines to cron

Make sure you change 'usr' in '/home/usr/bing-bot/main.py' to your current account on the machine
	
	SHELL=/bin/bash #place this at the top of crontab

	0 9,17 * * * /bin/sleep `/usr/bin/expr $RANDOM \% 14400`; python2 /home/usr/bing-bot/main.py

	0 0 * * * python /home/usr/bing-bot/account-reset.py
