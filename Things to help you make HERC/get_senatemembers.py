from bs4 import BeautifulSoup
import urllib2

page = urllib2.urlopen("http://senate.ca.gov/senators")
soup = BeautifulSoup(page)

membertable = soup.find("table" )
mtbody = membertable.find("tbody")
rows = membertable.findAll("tr")

for row in rows:
    name = ''
    district = ''
    party = ''
    image = ''
    elements = row.findAll("td")
    for i in range(len(elements)):
        if i == 0:
            mname = elements[i].findAll("a")[0].string.strip()
            uname = unicode(mname)
            name = ' '.join(k.strip() for k in uname.split(',')[::-1])
        if i == 1:
            district = elements[i].string.strip()
        if i == 2:
            party = elements[i].string.strip()
            
    print name.encode('utf-8') + ','.encode('utf-8') + district.encode('utf-8') + ','.encode('utf-8') + party.encode('utf-8')


