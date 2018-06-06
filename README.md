# Deploying on python anywhere
We have two pythonanywhere accounts:
  - friendshiphouse
  - friendshiphousedev
  
 Go to the console tab within pythonanywhere, click on bash
 
 Need to add environment variables
 
 Make virtual environment
 mkvirtualenv --python=/usr/bin/python3.6 friendshiphouse
 
 Install packages
 pip istall flask
 pip install firebase_admin
 pip install flask_basicauth
 pip install pandas
 
 Copy HTTP clone from git hub and clone into pythonanywhere:
 git clone https://github.com/ia-community-analytics/friendship-house.git
 
 Copy config files into directory:
 cd friendship-house
 nano config.json (copy and paste)
 Ctrl + X, hit Y + Enter
 nano firebase_config.json (copy and paste)
 Ctrl + X, hit Y + Enter
 
 Go back to console and go to Web tab and select create App. 
 Select manual configuration
 Select Python 3.6
 
 Scroll down to select the virtual environment and type in "friendshiphouse" and hit the check box
 
 Now scroll up and select the friendshiphousedev_pythonanywhere_com_wsgi.py config file. 
 Comment out lines 18-47 (sample app)
 
 Scroll down, uncomment all pieces of code under "+++++++++++ FLASK +++++++++++"
 Change path to path to App (/home/friendshiphousedev/friendship-house/)
change "from main_flask_app_file import app as application" to "from main import app as application"

Save file 

Go to Web tab and refresh App
