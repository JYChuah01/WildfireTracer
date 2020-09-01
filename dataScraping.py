from bs4 import BeautifulSoup
import requests
from selenium import webdriver
import threading


def swapElem(list, index1, index2):
    list[index1], list[index2] = list[index2], list[index1]
    return list

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

        if(incident):
    
            iconData = incident.find('div', class_='icon-with-data')
            acresBurned = iconData.find('h4')

            percentageContained = incident.find('div', class_='icon-label')
            
            if(percentageContained):
                percentageContained = percentageContained.text.strip()
            else:
                percentageContained = 'Unknown'
            
            dataTable = incident.find('table', class_='table table-striped')
        
            daysActive = incident.select('div.col-md-6:nth-child(1) > div:nth-child(2) > div:nth-child(1) > p:nth-child(3)')
            county = incident.select('div.col-md-6:nth-child(1) > div:nth-child(2) > div:nth-child(2) > p:nth-child(3)')

            print('Fire Name: ' + fireName)    
            print('CAL FIRE Incident: Yes')
        
            dataTitle = dataTable.find_all('th')
            incidentData = dataTable.find_all('td')

            dataTitle = swapElem(dataTitle, 3, 4)
            incidentData = swapElem(incidentData, 3, 4)

            for title, data in zip(dataTitle, incidentData):
                print(title.text.strip() + ': ' + data.text.strip())

                if(title.text.strip() == 'Location Information'):
                    print('Counties: ' + county[0].text.strip() 
                        + '\nAcres Burned: ' + str(acresBurned.text.strip()).replace(' Acres', '')
                        + '\nPercentage Contained: ' + percentageContained)

                if(title.text.strip() == 'Administrative Unit'):
                    print('Archive Year: Current Year' 
                        + '\nStatus: ' + daysActive[0].text.strip()
                        + '\nFinal: Unknown')

        else: 
            dataTable = newSoup.find('table', class_='table table-striped')
            
            dataTitle = dataTable.find_all('th')
            incidentData = dataTable.find_all('td')

            print('Fire Name: ' + fireName)  

            for title, data in zip(dataTitle, incidentData):
                print(title.text.strip() + ': ' + data.text.strip())

        
        print("\n")

driver.quit()

    
