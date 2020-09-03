from bs4 import BeautifulSoup
import requests
from selenium import webdriver
import threading


def swapElem(list, index1, index2):
    list[index1], list[index2] = list[index2], list[index1]
    return list

def findLongLat(soup, cssNum):
    longLat = soup.select_one('tr:nth-child(' + str(cssNum) + ') > td:nth-child(2)')

    if(longLat == None):
        return findLongLat(soup, cssNum - 1)
    else:
        return longLat.text


URL = 'https://www.fire.ca.gov/incidents/'

driver = webdriver.Firefox()
driver.get(URL)

nextPage = driver.find_elements_by_xpath('/html/body/div[1]/main/div/div[4]/div/nav/ul/li')


for iterator in nextPage:
    iterator.click()

    currPage = driver.page_source
    soup = BeautifulSoup(currPage, 'lxml')

    fireList = soup.find('div', class_='responsive-table responsive-table--collapse')
    fireLink = fireList.find_all('a', href=True)
    
    for fire in fireLink:
        fireName = fire.contents[0]
        newRequest = requests.get(URL + str(fire['href'].replace('/incidents/', ''))).text
        newSoup = BeautifulSoup(newRequest, 'lxml')
        
        incident = newSoup.find(id='incident-overview')

        print('Fire Name: ' + fireName)

        if(incident):
    
            iconData = incident.find('div', class_='icon-with-data')
            acresBurned = iconData.find('h4')
            longLat = incident.select_one('tr:nth-child(4) > td:nth-child(2)').text
            percentageContained = incident.find('div', class_='icon-label')

            if(percentageContained):
                percentageContained = percentageContained.text.strip()
            else:
                percentageContained = 'Unknown'
            
            dataTable = incident.find('table', class_='table table-striped')
        
            daysActive = incident.select_one('div.col-md-6:nth-child(1) > div:nth-child(2) > div:nth-child(1) > p:nth-child(3)')
            county = incident.select_one('div.col-md-6:nth-child(1) > div:nth-child(2) > div:nth-child(2) > p:nth-child(3)')

            print('CAL FIRE Incident: Yes')
        
            dataTitle = dataTable.find_all('th')
            incidentData = dataTable.find_all('td')

            dataTitle = swapElem(dataTitle, 3, 4)
            incidentData = swapElem(incidentData, 3, 4)

            for title, data in zip(dataTitle, incidentData):
                print(title.text.strip() + ': ' + data.text.strip())

                if(title.text.strip() == 'Location Information'):
                    print('Counties: ' + county.text.strip() 
                        + '\nAcres Burned: ' + str(acresBurned.text.strip()).replace(' Acres', '')
                        + '\nPercentage Contained: ' + percentageContained)

                if(title.text.strip() == 'Administrative Unit'):
                    print('Archive Year: Current Year' 
                        + '\nStatus: ' + daysActive.text.strip()
                        + '\nFinal: Unknown')
                       

        else: 
            dataTable = newSoup.find('table', class_='table table-striped')
            
            dataTitle = dataTable.find_all('th')
            incidentData = dataTable.find_all('td')
            
            longLat = findLongLat(dataTable, 13)
          
            for title, data in zip(dataTitle, incidentData):
                print(title.text.strip() + ': ' + data.text.strip())
            

        
        print("\n")

driver.quit()

    
