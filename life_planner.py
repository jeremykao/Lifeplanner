#all our imports
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import random
from google.appengine.dist import use_library
import logging
import decimal
import datetime
import re
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users

#all our classes
class Messages(db.Model):  #all messages are stored using this class
  user = db.StringProperty(required = False)
  content = db.StringProperty(required = False, multiline = True)
  calendar = db.StringProperty(required = False)
  money = db.StringProperty(required = False)
  flashcards = db.StringProperty(required = False)
  AM = db.StringProperty(required = False)
  PM = db.StringProperty(required = False)

class FavSite(db.Model):
  user = db.StringProperty(required = False)
  site = db.StringProperty(required = False)

class CalendarEvents(db.Model): #calendar messages specially stored as this. Allows us to associate entries with their time.
  date = db.StringProperty(required = False)
  user = db.StringProperty(required = False)
  hours = db.StringProperty(required = False)
  minutes = db.StringProperty(required = False)
  events = db.StringProperty(required = False)
  AM = db.StringProperty(required = False)
  PM = db.StringProperty(required = False)

class Settings(db.Model): #used for the settings
  user = db.StringProperty(required = False)
  savings = db.StringProperty(required = False)
  monthly_income = db.StringProperty(required = False)
  monthly_expenses = db.StringProperty(required = False)

def message_creator(self): #yay, condensing repetative code!
  content = self.request.get('content')
  cal_tag = self.request.get('cal_tag')
  mon_tag = self.request.get('mon_tag')
  fla_tag = self.request.get('fla_tag')
  AM = self.request.get('AM')
  PM = self.request.get('PM')
  message = Messages(user=str(users.get_current_user()), content=content, calendar=cal_tag, money=mon_tag, flashcards=fla_tag, AM=AM, PM=PM)
  message.put()
  if message.calendar:
    c = re.search(r'\d+', message.content)
    content = message.content
    if c:
      if message.content.__contains__(':'):
        i = message.content.index(':')
        hour = message.content[0:i]
        minute = message.content[i+1:i+3].replace(',','').replace('.','').replace('!','').replace(';','').replace('?','')
        hour_search = re.search(r'\d+', hour)
        minute_search = re.search(r'\d+', minute)
        if hour_search and minute_search: 
          if int(hour_search.group(0)) <= 24:
            if int(hour_search.group(0)) > 12:
              hour_san = str(int(hour_search.group(0)) - 12)
            else:
              hour_san = hour_search.group(0)
            if int(minute_search.group(0)) < 60:
              minute_san = minute_search.group(0)
            else:
              hour_san = "Unknown"
              minute_san = "Time"
          else: 
            hour_san = "Unknown"
            minute_san = "Time"
        else:
          hour_san = "Hour"
          minute_san = "Minute"
          content = "Please enter time following the format on the left."  
        AM = message.AM
        PM = message.PM
            
        calendar = CalendarEvents(date=str(datetime.date.today()), user=str(users.get_current_user()), hours=hour_san, minutes=minute_san, events=content, AM=AM, PM=PM)
        calendar.put()


#all our handlers
class SettingHandler(webapp.RequestHandler):  #handles the settings page
  def get(self):
    template_values = {}
    valid_messages = []

    messages = Messages.all()
    for message in messages:
      if message.content == '' and message.calendar == '' and message.money == '' and message.flashcards == '':
        message.delete() #if a message has no content at all, it is deleted, as extra blank messages were being generated on post
      if message.user == str(users.get_current_user()): 
        valid_messages.append(message)
    template_values['messages'] = valid_messages #passes only the user's messages to the template

    path = os.path.join(os.path.dirname(__file__), 'settings.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    message_creator(self)
    savings = self.request.get('savings').replace(',','') #allows for commas when entering the settings values
    monthly_income = self.request.get('monthly_income').replace(',','')
    monthly_expenses = self.request.get('monthly_expenses').replace(',','')
    if savings.isdigit() and monthly_income.isdigit() and monthly_expenses.isdigit():
      sav = savings
      mon_in = monthly_income
      mon_ex = monthly_expenses
      user = users.get_current_user()
      settings = Settings(user=str(user), savings=sav, monthly_income=mon_in, monthly_expenses=mon_ex)
      settings.put()
    else:
      pass
    
    cal_tag_on = self.request.get('cal_tag_on') #the following are used to toggle the settings
    if cal_tag_on:
      messages = Messages.get(cal_tag_on)
      if messages:
        messages.calendar = None;
        messages.put()

    cal_tag_off = self.request.get('cal_tag_off')
    if cal_tag_off:
      messages = Messages.get(cal_tag_off)
      if messages:
        messages.calendar = 'on';
        messages.put()

    mon_tag_on = self.request.get('mon_tag_on')
    if mon_tag_on:
      messages = Messages.get(mon_tag_on)
      if messages:
        messages.money = None;
        messages.put()

    mon_tag_off = self.request.get('mon_tag_off')
    if mon_tag_off:
      messages = Messages.get(mon_tag_off)
      if messages:
        messages.money = "on";
        messages.put()

    fla_tag_on = self.request.get('fla_tag_on')
    if fla_tag_on:
      messages = Messages.get(fla_tag_on)
      if messages:
        messages.flashcards = None;
        messages.put()

    fla_tag_off = self.request.get('fla_tag_off')
    if fla_tag_off:
      messages = Messages.get(fla_tag_off)
      if messages:
        messages.flashcards = "on";
        messages.put()

    message_to_delete = self.request.get('delete') #allows user to delete messages
    if message_to_delete:
      messages = Messages.get(message_to_delete)
      if messages:
        messages.delete() 

    messages = Messages.all() #deletes messages that were generated on the post of the page, which have no content
    for message in messages:
      if message.content == '' and message.calendar == '' and message.money == '' and message.flashcards == '':
        message.delete()   

    self.get() 

class InstructionHandler(webapp.RequestHandler): #the handler for the instructions page
  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'instructions.html')
    self.response.out.write(template.render(path, template_values))
  def post(self):
    message_creator(self)
    self.get() 


class ContentHandler(webapp.RequestHandler): #the handler for the home page
  def get(self):
    user = users.get_current_user()
    template_values = {'username': user.email()}
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))
  def post(self):
    message_creator(self)
    self.get()  

class ContactHandler(webapp.RequestHandler): #the handler for the Contact Us page
  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'contact_us.html')
    self.response.out.write(template.render(path, template_values))
  def post(self):
    message_creator(self)
    self.get() 

class LifePlannerHandler(webapp.RequestHandler): #the handler for the Life Planner page. Most of the calulations occur here.
  def get(self):
    template_values = {}
    m = 0
    money_list = []
    add_money = []
    minus_money = []
    flashcard_dict = {}
    total_money = 0
    income = 0
    expenses = 0
    A = 0
    B = 0
    month_income = 0
    month_expenses = 0
    monies = 0
    valid_calendar_entriesAM = []
    valid_calendar_entriesPM = []
    valid_calendar_entries = []

    settings = Settings.all() #gets the settings to pass into the budget
    for setting in settings:
     if setting.user == str(users.get_current_user()):
       if setting.savings:
         savings = setting.savings
         template_values['savings'] = savings
       if setting.monthly_income:
         monthly_income = setting.monthly_income
         template_values['monthly_income'] = monthly_income
       if setting.monthly_expenses:
         monthly_expenses = setting.monthly_expenses
         template_values['monthly_expenses'] = monthly_expenses
       if savings and monthly_income and monthly_expenses:
         monies = int(savings) + int(monthly_income) - int(monthly_expenses)

    messages = Messages.all()
    for message in messages:
      if message.user == str(users.get_current_user()):
        if message.flashcards: #creates flashcards
          if ":" in str(message.content):
            l = message.content.split(":")
            flashcard_dict[l[0]] = l[1]
            rk = random.choice(flashcard_dict.keys())
            answer = flashcard_dict[rk]
            template_values['rk'] = rk
            template_values['answer'] = answer
          else:
            pass
        if message.money: #creates budget
          content_money = str(message.content)
          m = re.search(r'\d+', content_money)
          if m: 
            money = m.group(0)
            if "+" + str(money) in content_money:
              template_values['m'] = m.group(0)
              add_money.append(money)
              template_values['add_money'] = add_money
              while A < len(add_money):
                b = add_money[A]
                income += int(b) 
                A += 1
            if "-" + str(money) in content_money:
              minus_money.append(money)
              template_values['minus_money'] = minus_money
              while B < len(minus_money):
                b = minus_money[B]
                expenses += int(b)
                B += 1
            
            total_money = monies + income - expenses
            template_values['income'] = income
            template_values['expenses'] = expenses
            template_values['total_money'] = total_money 

    calendars = CalendarEvents.all()
    for calendar in calendars:
      if calendar.user == str(users.get_current_user()): 
        if calendar.date == str(datetime.date.today()): 
          if calendar.AM:  
            valid_calendar_entriesAM.append(calendar)
            a = sorted(valid_calendar_entriesAM, key=lambda calendar: calendar.hours)
            template_values['calendarsAM'] = a 
          if calendar.PM:
            valid_calendar_entriesPM.append(calendar)
            b = sorted(valid_calendar_entriesPM, key=lambda calendar: calendar.hours)
            template_values['calendarsPM'] = b
          if calendar not in valid_calendar_entriesPM and calendar not in valid_calendar_entriesAM:
            valid_calendar_entries.append(calendar)
            c = sorted(valid_calendar_entries, key=lambda calendar: calendar.hours)
            template_values['calendars'] = c

    template_values['date'] = datetime.date.today()

    path = os.path.join(os.path.dirname(__file__), 'life_planner.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    message_creator(self)
    calendar_to_delete = self.request.get('check')

    if calendar_to_delete:
      calendars_to_destroy = CalendarEvents.get(calendar_to_delete)
      if calendars_to_destroy:
        calendars_to_destroy.delete() 
    self.get()   

class FavSiteHandler(webapp.RequestHandler):
  def get(self):
    template_values = {}
    websites = Messages.all()
    for website in websites:
      url = website.content
      logging.info(url)
      if url:
        if url.__contains__('@'):
          indexat = url.index('@')
          if url.__contains__('@http://'):
            parse = url[indexat:].replace('@','').strip()
            userSite = FavSite(user = str(users.get_current_user()), site = parse)
            userSite.put()
          else:
            parse = url[indexat:].replace('@', 'http://').strip()
            userSite = FavSite(user = str(users.get_current_user()), site = parse)
            userSite.put()
          template_values['site'] = userSite.site
    path = os.path.join(os.path.dirname(__file__), 'favSite.html')
    self.response.out.write(template.render(path, template_values))
  def post(self):
    message_creator(self)

    self.get() 
  

def main():
  application = webapp.WSGIApplication([('/',ContentHandler),
					('/favSite', FavSiteHandler),
                                        ('/life_planner', LifePlannerHandler),
                                        ('/settings', SettingHandler),
                                        ('/contact', ContactHandler),
                                        ('/instructions', InstructionHandler)],
                                       debug=True)
  run_wsgi_app(application)

if __name__ == '__main__':
  main()

