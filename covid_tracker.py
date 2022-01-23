from email.mime import audio
from turtle import speed
from urllib import response
import requests
import json
import pyttsx3
import speech_recognition as sr
import re
import threading
import time

api_key = "t7bbSxKBTBro"
project_token = "tMrhZ1qmgph5"
run_token = "thXzcTWWNcdy"



class Covid:
    def __init__(self,api_key,project_token):
        self.api_key = api_key
        self.project_token = project_token
        self.parameters = {"api_key":self.api_key,"project_token":self.project_token}
        self.data = self.get_info()
    
    def get_info(self):
        #url = f"https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data"
        recieved_url = requests.get(f"https://www.parsehub.com/api/v2/projects/{project_token}/last_ready_run/data",params={'api_key':api_key})
        data = json.loads(recieved_url.text)
        return data
    
    def get_total_cases(self):
        cases=self.data.get('total')[0]
        if cases!=None:
            return cases.get('value')
        else:
            return "None"
    
    def get_total_deaths(self):
        deaths=self.data.get('total')[1]
        if deaths!=None:
            return deaths.get('value')
        else:
            return "None"
    
    def get_total_recovered(self):
        recovered=self.data.get('total')[2]
        if recovered!=None:
            return recovered.get('value')
        else:
            return "None"
    
    def get_country_info(self,country):
        country_name = self.data.get('country')
        for content in country_name:
            if content['name'].lower()==country.lower():
                return content
        
        return "0"
    
    def get_list_of_countries(self):
        country_list = []
        for country in self.data['country']:
            country_list.append(country['name'].lower())
        return country_list
    
    def update_info(self):
        response = requests.post(f"https://www.parsehub.com/api/v2/projects/{project_token}/run",params={'api_key':api_key}) #initializes a new run on the parsehub servers
        
        """we have to keep pulling data from the end point until we get some new data"""
        
        #this function will constantly interact with the server to get new data. So while this is happening, other functionalities should still work
        def poll():
            time.sleep(0.1) #if one thread is not working it will release it self and give control to some other thread
            old_data = self.data
            while True:
                new_data = self.get_data() #getting data every 5 seconds from the server
                if old_data!=new_data:
                    old_data=new_data
                    print("data updated")
                    break
                time.sleep(5) #the function will ping the url every 5 seconds to check for new info

        thread = threading.Thread(target=poll) #we create threads so that it does not interfere with our main function i.e the voice assisstant
        thread.start

def speak(txt):
    engine = pyttsx3.init() #initialize the pyttsx3 engine
    engine.say(txt)
    engine.runAndWait()

def speech_recognizer():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
        speech=""
        try:
            speech = recognizer.recognize_google(audio)
        except Exception as e:
            print(e)
    return speech.lower()

def main():
    end_phrase = 'quit' #the phrase that user has to say to quit the program
    data = Covid(api_key,project_token)
    list_of_countries = data.get_list_of_countries()
    print(data.get_country_info('india'))
    """some search patterns"""
    search_patterns = {
        re.compile("[\w\s]+ total [\w\s]+ cases"):data.get_total_cases,
        re.compile("[\w\s]+ total cases"):data.get_total_cases,
        re.compile("[\w\s]+ total [\w\s]+ deaths"):data.get_total_deaths,
        re.compile("[\w\s]+ total deaths"):data.get_total_deaths,
        re.compile("[\w\s]+ total [\w\s]+ recovered"):data.get_total_recovered,
        re.compile("[\w\s]+ total recovered"):data.get_total_recovered,
    }
    coutry_patterns = {
        re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_info(country)['total_cases'],
        re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_info(country)['total_death'],
        re.compile("[\w\s]+ recovered [\w\s]+") : lambda country: data.get_country_info(country)['total_recovered'],
        re.compile("[\w\s]+ tests done [\w\s]+"): lambda country: data.get_country_info(country)['total_tests'],
        re.compile("[\w\s]+ test done [\w\s]+"): lambda country: data.get_country_info(country)['total_tests']
    }
    update_pattern = "update"
    while True:
        print("Listening.....")
        speech = speech_recognizer()
        res = None
        print(speech) #print what user says

        """For country specific information"""

        for pattern,function in coutry_patterns.items():
            if pattern.match(speech): #check wehether user's speech pattern matches our patterns
                words = set(speech.split(" ")) #split into words for faster computation
                for country in list_of_countries: 
                    if country in words:
                        res = function(country)
                        break

        """For worldwide information"""

        for pattern,function in search_patterns.items():
            if pattern.match(speech):
                res = function()
                break
        if speech==update_pattern:
            print("Data is being updated. PLease wait for a moment")
            data.update_info()
        if res:
            speak(res)
            print(res)
        if speech.find(end_phrase) != -1:
            break

main()

