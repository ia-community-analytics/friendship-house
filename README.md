# Deploying from git changes

Go into pythonanywhere console.
Navigate to git repo ('home/friendshiphousedev/friendship-house/')
'''
git pull origin master
'''
Refresh the webpage on the Web tab. 
Good to go!


# Deploying on python anywhere for first time
We have two pythonanywhere accounts:
  - friendshiphouse
  - friendshiphousedev
  
 Go to the console tab within pythonanywhere, click on bash
 
 Need to add environment variables
 
 Make virtual environment
 mkvirtualenv --python=/usr/bin/python3.6 friendshiphouse
 
 Install packages:
 '''
 pip istall flask
 pip install firebase_admin
 pip install flask_basicauth
 pip install pandas
 pip install python-dotenv
 '''
 Copy HTTP clone from git hub and clone into pythonanywhere:
 git clone https://github.com/ia-community-analytics/friendship-house.git
 
 Make a config directory
 mkdir config
 Create two config files witin the directory
 cd config
 Copy config files into directory:
 nano config.json (copy and paste)
 Ctrl + X, hit Y + Enter
 nano firebase_config.json (copy and paste)
 Ctrl + X, hit Y + Enter
 
 Go into .env file from the github clone and make sure it points to the right direction within the file system
 
 Go back to console and go to Web tab and select create App. 
 Select manual configuration
 Select Python 3.6
 
 Scroll down to select the virtual environment and type in "friendshiphouse" and hit the check box
 
 Now scroll up and select the friendshiphousedev_pythonanywhere_com_wsgi.py config file. 
 Comment out lines 18-47 (sample app)
 
 Scroll down, uncomment all pieces of code under "+++++++++++ FLASK +++++++++++"
 Add this code to it:
 '''
 import sys
import os

from dotenv import load_dotenv
project_folder = os.path.expanduser('~/friendship-house/')  # adjust as appropriate
load_dotenv(os.path.join(project_folder, '.env'))
'''
 Change path to path to App (/home/friendshiphousedev/friendship-house/)
change "from main_flask_app_file import app as application" to "from main import app as application"

Save file 

Go to Web tab and refresh App
