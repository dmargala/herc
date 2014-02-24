## UC Irvine Associated Gradudate Students
## External Affairs Committee (c) 2014

from bs4 import BeautifulSoup
import urllib
from urllib import urlretrieve
from collections import namedtuple
from operator import attrgetter
import re
import os
import csv


Politician = namedtuple('Politician',
                        'name member type district party image city')
District = namedtuple('District', 'number cities')
City = namedtuple('City', 'name pop pct')

AssemblyPage = "http://assembly.ca.gov/assemblymembers"
SenatePage = "http://senate.ca.gov/senators"
AssemblyMember = 'http://www.leginfo.ca.gov/pub/13-14/bill/' + \
  'index_assembly_author_bill_topic'
SenateMember = 'http://www.leginfo.ca.gov/pub/13-14/bill/' + \
  'index_senate_author_bill_topic' 
Year = '2014'
cities_csv = 'districts.csv'
outfile_csv = 'memberinfo.csv'    

def downloadImage(path, fullname):
    '''
    Downloads image file from path, saves locally to herc/<year>/images as
      first_mid_last_suf.jpg, returns file name
    '''
    if path == '':
        return ''
    
    name = fullname.split()
    file_name = ''
    
    for i in range(len(name) - 1):
        file_name = file_name + name[i].split('.')[0].lower() + '_'
    file_name = file_name + name[len(name)-1].split('.')[0].lower() + '.jpg'
    ## make file name friendly by ignoring special chars
    file_name = file_name.encode('ascii', 'ignore')
    urlretrieve(path, Year + '/images/' + file_name)
    
    return file_name

def exportMemberInfo(politicians):
    '''
    Writes out all politicians to memberinfo.csv
    '''
    ofile = open(Year + '/' + outfile_csv, 'w')
    c = csv.writer(ofile, delimiter=',')
    c.writerow(['Member', 'Body', 'District', 'PictureFile',
                'FullName', 'Party', 'District Cities'])
    
    for politician in politicians:
        c.writerow([politician.member.encode('utf-8'),
                    politician.type.encode('utf-8'),
                    politician.district.encode('utf-8'),
                    politician.image.encode('utf-8'),
                    politician.name.encode('utf-8'),
                    politician.party.encode('utf-8'),
                    politician.city.encode('utf-8')])
    
    ofile.close()


def importDistricts():
    '''
    Pulls from districts.csv file, returns Districts namedtuple
    '''
    districts = []
    cities = []
    cur_dist = 0    
    
    with open(cities_csv, 'r') as csvfile:
        cities_reader = csv.reader(csvfile, delimiter=':')
        
        for row in cities_reader:
            ## skip header
            if row[1] != 'number':
                if int(row[1]) > cur_dist:
                    if cities != []:
                        districts.append(District(str(cur_dist), cities))
                        cities = []
                    cur_dist = int(row[1])
                    cities.append(City(row[0], row[2], row[3]))
                else:
                    cities.append(City(row[0], row[2], row[3]))                
        districts.append(District(str(cur_dist), cities)) # last elem
        
    return districts


def getCities(district, numcities):
    '''
    Returns string of 1 to numcities cities with \n delimiter
    '''
    ret_val = ''
    i = 0
    
    for i in range(len(district.cities)):
        if i < numcities:
            ret_val = ret_val + district.cities[i].name + '\n' 
        else:
            break
        
    return ret_val[:-1]


def getMembers(politicians):
    '''
    Pulls from AssemblyMember/SenateMember site for member (username that
    reflects in bill votes for each politician), matches member (username)
    with Politician namedtuple, returns updated namedtuple list,
    ignores vacant positions since those spots don't have members
    '''
    members = []
    pol_ret = []
    
    data1 = urllib.urlopen(AssemblyMember)
    data2 = urllib.urlopen(SenateMember)
    committee = False
    
    for line in data1:
        ## check if committee
        if committee:
            if line.find('AB') > -1:
                committee = False
        elif line.find('Committee') > -1:
            committee = True
        elif line[0] != ' ' and line[0] != '\n' and line.find('AUTHOR') == -1:
            members.append(line[:-1].decode('iso-8859-1'))
    
    for line in data2:
        if committee:
            if line.find('SB') > -1:
                committee = False
        elif line.find('Committee') > -1:
            committee = True
        elif line[0] != ' ' and line[0] != '\n' and line.find('AUTHOR') == -1:
            members.append(line[:-1].decode('iso-8859-1'))

    for poli in politicians:
        m_names = []
        
        for memb in members:
            if memb in poli.name:
                m_names.append(memb)
        
        if len(m_names) > 1:
            ## look for best fit
            cur_mname = ''
            lname = ''
            pname = poli.name.split(' ')
            
            if len(pname) < 2:
                return
            elif len(pname) == 2:
                lname = pname[1]
            elif len(pname) >= 3:
                if '.' in pname[1]:
                    # middle initial
                    for i in range(len(pname)-2):
                        lname = pname[i+2] + ' '
                else:
                    for i in range(len(pname)-2):
                        lname = pname[i+2] + ' '    

            for mn in m_names:
                if mn in lname:
                    cur_mname = mn
            pol_ret.append(poli._replace(member = cur_mname))

        elif len(m_names) == 0:
            pol_ret.append(poli._replace(member = ''))
        else:
            pol_ret.append(poli._replace(member = m_names[0]))

    return pol_ret

def getAssembly(politicians, districts):
    '''
    Imports Assembly info from webpage into Politician namedTuple,
    Assembly page formats each politician as a table row, which
    differs from the Senate page (div).  No vacancy handling.
    '''
    page = urllib.urlopen(AssemblyPage)
    soup = BeautifulSoup(page)

    membertable = soup.find("table" )
    mtbody = membertable.find("tbody")
    rows = membertable.findAll("tr")

    for row in rows:
        name = ''
        district = ''
        party = ''
        img = ''
        elements = row.findAll("td")
        for i in range(len(elements)):
            if i == 0:
                mname = elements[i].findAll("a")[0].string.strip()
                uname = unicode(mname)
                name = ' '.join(k.strip() for k in uname.split(',')[::-1])
                image = elements[i].findAll("img")[0]['src']
                img = downloadImage(image, name)
            if i == 1:
                district = elements[i].string.strip()
                district = (district[-2:] if int(district[-2]) \
                            else district[-1:])
            if i == 2:
                party = elements[i].string.strip()
        
        if name != '':
            top3cities = getCities(districts[int(district)-1], 3)
            politicians.append(Politician(name, '', 'assembly', district,
                                          party, img, top3cities))

    return politicians


def getSenate(politicians, districts):
    '''
    Imports Senate info from webpage into Politician namedTuple,
    Senate page formats each politician as div's, which differs from
    Assembly (tables), ignores vacancies (can't rate nonexistent politicians).
    '''
    page = urllib.urlopen(SenatePage)
    soup = BeautifulSoup(page)

    ## 1st elem (membertable) are politicians, 2nd are vacancies
    membertable = soup.findAll("div", attrs={'class': 'view-content'} )
    rows = membertable[0].findAll("div",
                                  attrs={'class': re.compile('views-row.*')})
    for row in rows:
      
        district = row.find("span",
                            attrs={'class': 'district-number'}).text
        district = (district[-2:] if int(district[-2]) else district[-1:])
        name_party = row.find("h2").text
        name = name_party[:-4]
        party = name_party[-2]
        party = ('Republican' if party == 'R' else 'Democrat')
        image = row.find("img")['src']
        img = downloadImage(image, name)
        
        if name != '':
            top3cities = getCities(districts[int(district)-1], 3)
            politicians.append(Politician(name, '', 'senate', district,
                                          party, img, top3cities))
    
    return politicians
    
    
def main():
    
    ## if year/images dir doesn't exist, create it..
    if not os.path.exists(Year + '/images'):
        os.makedirs(Year + '/images')
    
    politicians = []
    districts = []
    
    districts = importDistricts()
    politicians = getAssembly(politicians, districts)
    politicians = getSenate(politicians, districts)
    
    politicians = sorted(politicians, key=attrgetter('district'))
    politicians = getMembers(politicians)

    exportMemberInfo(politicians)
    
## run!    
if __name__ == '__main__':
    main()
