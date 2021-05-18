#A program that uses web scraping to retrieve active fire incidents from Calfire webpage.

import requests, gmaps, sys
from bs4 import BeautifulSoup
from selenium import webdriver
from multiprocessing.dummy import Pool
from multiprocessing import cpu_count
from ipywidgets.embed import embed_minimal_html


def swapElem(list, pos1, pos2):
    list[pos1], list[pos2] = list[pos2], list[pos1]
    return list

def getLongLat(soup, cssNum):
    longLat = soup.select_one(f'tr:nth-child({str(cssNum)}) > td:nth-child(2)')

    if(longLat):
        longLat = longLat.text
        longLat = longLat[1: len(longLat) - 1]
        longLat = longLat.rsplit(', ')
        return longLat

    else:
        return getLongLat(soup, cssNum - 1)

def convertToText(list, index):
    if(index < len(list)):
        list[index] = list[index].text.strip()
        return convertToText(list, index + 1)

    else:
        return

def formatListA(list1, list2, county, acres, percent, status):
    newList = []

    list1.pop(3)
    list2.pop(3)

    del list1[4:]
    del list2[4:]

    # list1.insert(3, 'Status')
    # list1.insert(3, 'Percentage Contained')
    # list1.insert(3, 'Acres Burned')
    # list1.insert(3, 'Counties')
    
    list2.insert(3, status)
    list2.insert(3, percent)
    list2.insert(3, acres)
    list2.insert(3, county)

    list1.clear()
    #list2.clear()

    return list2

def formatListB(list1, list2):
    newList = []
    if(list1[4] != 'Acres Burned'):
        del list1[4:]
        del list2[4:]
    else:
        del list1[8:]
        del list2[8:]

        if(list1[6] == 'Cause'):
            #list1.pop(6)
            list2.pop(6)
        else:
            #list1.pop(7)
            list2.pop(7)

    if(len(list1) < 5 ):
        # list1.append('Acres Burned')
        # list1.append('Percentage Contained')
        # list1.append('Status')
        # list1.append('Administrative Unit')
 
        list2.append('Unknown')
        list2.append('Unknown')
        list2.append('Active')
        list2.append('Unknown')
    else:
        #list1.insert(6, 'Status')
        
        list2.insert(6, 'Active')
    
   

    list1.clear()
    #list2.clear()
    return list2
        
def getFireData(fireurl):
    formattedList = []
    newRequests = requests.get('https://www.fire.ca.gov/incidents/' + fireurl).text
    newSoup = BeautifulSoup(newRequests, 'lxml')

    incident = newSoup.find(id = 'incident-overview')

    if(incident):
        acresBurned = str(incident.find('div', class_='icon-with-data').find('h4').text.strip()).replace(' Acres', '')
        percentageContained = incident.find('div', class_='icon-label')

        if(percentageContained != None):
            percentageContained = percentageContained.text.strip()
        else:
            percentageContained = 'Unknown'
        
        longLat = getLongLat(newSoup, 4)
        longitude, latitude = float(longLat[0]), float(longLat[1])

        dataTable = incident.find('table', class_='table table-striped')
        
        daysActive = incident.select_one('div.col-md-6:nth-child(1) > div:nth-child(2) > div:nth-child(1) > p:nth-child(3)').text.strip()
        county = incident.select_one('div.col-md-6:nth-child(1) > div:nth-child(2) > div:nth-child(2) > p:nth-child(3)').text.strip()

        dataTitle, incidentData = dataTable.find_all('th'), dataTable.find_all('td')

        convertToText(dataTitle, 0)
        convertToText(incidentData, 0)
        swapElem(dataTitle, 0, 1)
        swapElem(incidentData, 0, 1)
    
        formattedList = formatListA(dataTitle, incidentData, county, acresBurned, percentageContained, daysActive)
        
    else:
        dataTable = newSoup.find('table', class_='table table-striped')
        
        dataTitle = dataTable.find_all('th')
        incidentData = dataTable.find_all('td')

        lonLat = getLongLat(dataTable, 13)
        longitude, latitude = float(lonLat[0]), float(lonLat[1])

        dataTitle.pop(0)
        incidentData.pop(0)

        convertToText(dataTitle, 0)
        convertToText(incidentData, 0)

        swapElem(dataTitle, 0, 1)
        swapElem(incidentData, 0, 1)

        formattedList = formatListB(dataTitle, incidentData)

    formattedList.extend([longitude, latitude])

    return formattedList

gmaps.configure(api_key='AIzaSyAQz4zCab-HfALvCr9h8P8MQ12O7J7GqzM')
mapCenter = (37.643756, -122.257603)
map = gmaps.figure(zoom_level = 5, center = mapCenter, map_type = 'TERRAIN')

URL = 'https://www.fire.ca.gov/incidents/'

driver = webdriver.Firefox()
driver.get(URL)
fireSource = driver.find_elements_by_xpath('/html/body/div[1]/main/div/div[4]/div/nav/ul/li')
#fireSource is invalid when there is only single page as there is no page navigation bar available

fireLink = []

for iterator in fireSource:
    if len(fireSource) > 1: #Temporary workaround for single paged active fire incidents
        iterator.click()
   
    newPage = driver.page_source
    soup = BeautifulSoup(newPage, 'lxml')

    fireList = soup.find('div', class_='responsive-table responsive-table--collapse')
    fireLink += fireList.find_all('a', href=True)

    if len(fireLink) == 0:
        sys.exit("No active fire found.\n\n")

driver.quit()

urlList = [f['href'].replace('/incidents/', '') for f in fireLink]
nameList = [x.contents[0] for x in fireLink]
fireLink.clear()

results = []
coordinateList = []
infoList = []

size = len(urlList)
numWorkers = cpu_count() * 2
chunksize = size // numWorkers * 4
pool = Pool(numWorkers)

results = pool.imap(getFireData, urlList)
pool.close()

for index, iterate in enumerate(results):
    infoList.append({'name': nameList[index],
                     'date': iterate[0], 
                     'lastUp': iterate[1], 
                     'location': iterate[2], 
                     'county' : iterate[3],
                     'acres': iterate[4],
                     'percent': iterate[5],
                     'status': iterate[6],
                     'units' : iterate[7],
                     'coordi': (iterate[8], iterate[9])})


coordinateList = [lonlat['coordi'] for lonlat in infoList]
infoBoxTemplate = """
<table>
    <tr>
        <th style="text-align:left">Name</th>
        <td>{name}</td>
    </tr>
    <tr>
        <th style="text-align:left">Date Started</th>
        <td>{date}</td>
    </tr>
    <tr>
        <th style="text-align:left">Last Updated</th>
        <td>{lastUp}</td>
    </tr>
    <tr>
        <th style="text-align:left">Location</th>
        <td>{location}</td>
    </tr>
    <tr>
        <th style="text-align:left">County</th>
        <td>{county}</td>
    </tr>
    <tr>
        <th style="text-align:left">Acres Burned</th>
        <td>{acres}</td>
    </tr>
    <tr>
        <th style="text-align:left">Percentage Contained</th>
        <td>{percent}</td>
    </tr>
    <tr>
        <th style="text-align:left">Status</th>
        <td>{status}</td>
    </tr>
    <tr>
        <th style="text-align:left">Admin Unit</th>
        <td>{units}</td>
    </tr>
</table>
"""

formattedInfo = [infoBoxTemplate.format(**info) for info in infoList]
markers = gmaps.marker_layer(coordinateList, info_box_content=formattedInfo)
map.add_layer(markers)
embed_minimal_html('fireMap.html', views=[map])

print("Executed successfully.")
