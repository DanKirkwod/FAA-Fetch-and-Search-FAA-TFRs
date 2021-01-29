import os
import time
import sys 
import requests
from lxml import etree
from datetime import datetime
import pandas as pd
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

#Grab TFR List and format it for python
TFRListURL=requests.get('https://tfr.faa.gov/tfr2/list.html')
OutputArray=""
TFRList=TFRListURL.content
soup=BeautifulSoup(TFRList, 'html.parser')
TFRarray = []
TFRs=soup.find_all("table")[4].find_all("tr")[5:]
print("Found TFRs")
#Grab every row and place it in an Array
for element in TFRs:
    TFRrow=[]
    for sub_element in element:
        try:
            TFRrow.append(sub_element.get_text())
        except:
            continue
    TFRarray.append(TFRrow)
print("Compiled TFR Data")
#Create Dataframe, remove last 3 rows.
dataframe = pd.DataFrame(data = TFRarray)
dataframe = dataframe[:-3]
print("Converted into DataFrame")
#convert NOTAM IDs to work as links
for index, row in dataframe.iterrows():
    TFR_ID=row[1].strip()
    TFR_ID=TFR_ID.replace("/","_")

    print("Here's the ID: "+str(TFR_ID))

#Locate XML of NOTAM
    CurrentXML="https://tfr.faa.gov/save_pages/detail_"+TFR_ID+".xml"
    print(CurrentXML)
    GetXML=requests.get(CurrentXML)
    print(GetXML)
    if str(requests.get(CurrentXML)) != '<Response [200]>':
        print("I Saved the day")
        CurrentXML='https://tfr.faa.gov/save_pages/detail_4_3634.xml'
        root=etree.fromstring(requests.get(CurrentXML).content)
    else:
        print("continuing as normal")
        root=etree.fromstring(requests.get(CurrentXML).content)

    #Confirm NOTAM is for Brownsville Space Ops, State, Cirt and Name fields can be changed, may compromise stability
    if root.findtext('.//txtNameUSState')=='TEXAS' and root.findtext('.//txtNameCity')=='BROWNSVILLE' and root.findtext('.//txtName')=='Space Operation Area1':
    #Collect NOTAM ID
        notamID=root.findtext('.//txtLocalName')
    #Get start and end date/times
        dateEffective=root.findtext('.//dateEffective')
        tfrStart=datetime.strptime(dateEffective,"%Y-%m-%dT%H:%M:%S")
        dateExpire=root.findtext('.//dateExpire')
        tfrEnd=datetime.strptime(dateExpire,"%Y-%m-%dT%H:%M:%S")
    #How High does the TFR go?
        if root.findtext('.//uomDistVerUpper') == 'FT':
            DistVerUpper=str(root.findtext('.//valDistVerUpper'))+" FT"
        else:
           DistVerUpper="Unlimited"

    #Is the TFR currently Active or Upcoming?
        if tfrStart<datetime.now() and tfrEnd>datetime.now():
            tfrActive="Active"
        elif tfrStart<datetime.now() and tfrEnd<datetime.now():
           tfrActive="Expired"
        elif tfrStart>datetime.now() and tfrEnd>datetime.now():
           tfrActive="Upcoming"
        else:
           tfrActive="Undetermined"
        print(str(notamID)+" "+str(tfrActive)+": "+str(tfrStart)+" - "+str(tfrEnd)+" up to "+str(DistVerUpper))
