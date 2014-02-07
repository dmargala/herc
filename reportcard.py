from bs4 import BeautifulSoup
import csv
import os
import re
import urllib2
import sys
import xlwt

BUDGET_WEIGHT = 0.0
LEG_WEIGHT = 1.0

def lookup_votes(bill_id, vote_date, vote_place, vote_title):
    """Returns a list of three lists [ [aye voters], [no voters], [nvr voters]]

    Arguments:
    bill_id -- string that gets appended to the base leg_url to get the vote
               history. Usually something like 0AB69, but can vary a little.
    vote_date -- string of date of vote copied from website. Formatted like
                 06/11/2011
    vote_place -- string for where vote took place, things like "Senate Floor"
                  or "Asm Higher Education"
    vote_title -- string describing vote, for example "Assembly 2nd Reading
                AB32 Blumenfield By Leno"

    The arguments are read from the csv files which are just copied from
    the legislature's website.

    The voters are usually just last names, but there are a lot of members
    with the same last name. In that case, it returns full name.

    Note that, in out rainbow state, names need to be encoded with utf-8.
    Lapsing into ascii will screw up everything.

    Finally, if something goes wrong, it prints something to stderr and
    returns [[],[],[]].
    """

    leg_url = "http://leginfo.legislature.ca.gov/faces/billVotesClient.xhtml" \
            "?bill_id=20112012"
    page = urllib2.urlopen(leg_url + bill_id)
    soup = BeautifulSoup(page)
    votetable = soup.find("table", id="billvotes")
    rows = votetable.findAll("tr")[1:]

    for i in xrange(len(rows)):
        if i % 5 == 0: ##We're on an info line
            vd = rows[i].findAll("th")[0].string
            vp = re.sub("\s{2,}", " ",
                  rows[i].findAll("td")[1].string.strip()).\
                          replace("&amp;", "&")
            vt = re.sub("\s{2,}", " ",
                    rows[i].findAll("td")[5].string.strip()).\
                            replace("&amp;", "&")
        if i % 5 == 1: ##These are the ayes
            try:
                ayes = [k.strip() for k in rows[i].findAll("td")[1].\
                        findAll("span")[1].string.split(',')]
            except AttributeError:
                ayes = []
        if i % 5 == 2:
            try:
                noes = [k.strip() for k in rows[i].findAll("td")[1].\
                        findAll("span")[1].string.split(',')]
            except AttributeError:
                noes = []
        if i % 5 == 3:
            try:
                nvrs = [k.strip() for k in rows[i].findAll("td")[1].\
                        findAll("span")[1].string.split(',')]
            except AttributeError:
                nvrs = []

        if i % 5 == 4:
            if vd == vote_date and vp == vote_place and vt == vote_title:
                return [ayes, noes, nvrs]
    sys.stderr.write("Failed: " + bill_id + " " + vote_place + "\n")
    return [ [], [], [] ]

def write_result(budget_dict, leg_dict, member_scores, vote_items):

    #Create workbook and sheet that will contain votes
    book = xlwt.Workbook(encoding="utf-8")
    sheet = book.add_sheet("Higher Education Report Card")

    #Write the column headers
    for i in range(len(vote_items)):
        vi = vote_items[i]
        prefix = vi[0]
        bn = vi[1]
        vd = vi[2]
        loc = vi[3]
        sheet.write(0, i + 1, prefix + bn + " " + loc + " " + vd)
    sheet.write(0, len(vote_items) + 1, "Score")
    sheet.write(0, len(vote_items) + 2, "Max Score")
    sheet.write(0, len(vote_items) + 3, "Percent")

    #Create cell effects for good and bad votes
    good_vote_fx = xlwt.easyxf('pattern: pattern solid, fore_color green;')
    bad_vote_fx = xlwt.easyxf('pattern: pattern solid, fore_color red;')


    line_counter = 1
    for member in sorted(list(set(budget_dict.keys() + leg_dict.keys()))):
        sheet.write(line_counter, 0, member)
        member_votes = budget_dict.get(member, {})
        member_votes.update(leg_dict.get(member, {}))
        for i in range(len(vote_items)):
            vi = vote_items[i]
            if vi in member_votes:
                if (vi[5] > 0 and member_votes[vi] == "Y") or \
                        (vi[5] < 0 and member_votes[vi] == "N"):
                    sheet.write(line_counter, i+1, member_votes[vi],
                        good_vote_fx)
                elif (vi[5] < 0 and member_votes[vi] == "Y") or \
                        (vi[5] > 0 and member_votes[vi] == "N"):
                    sheet.write(line_counter, i+1, member_votes[vi],
                        bad_vote_fx)
                else:
                    sheet.write(line_counter, i+1, member_votes[vi] )


        sheet.write(line_counter, len(vote_items) + 1,
            member_scores[member]['score'])
        sheet.write(line_counter, len(vote_items) + 2,
            member_scores[member]['max_score'])
        sheet.write(line_counter, len(vote_items) + 3,
            member_scores[member]['overall_percent_score'])
        line_counter += 1

#    sheet.write(line_counter, 0, "Vote entropy")
#    for i in range(len(vote_items)):
#        ayes = 0
#        noes = 0
#        vi = vote_items[i]
#        for member in mdict:
#            if vi in mdict[member]:
#                if mdict[member][vi] == 'Y':
#                    ayes += 1
#                if mdict[member][vi] == 'N':
#                    noes += 1
#        aye_frac = ayes/float(ayes+noes)
#        if aye_frac in (0, 1):
#            entropy = 0
#        else:
#            entropy = -aye_frac*math.log(aye_frac, 2) - \
#                (1-aye_frac)*math.log(1-aye_frac, 2)
#        sheet.write(line_counter, i + 1, entropy)


    book.save("ReportCard.xls")

def convert_to_ordinal(num):
    """Converts num to ordinal number. For example 1 becomes 1st,
    16 becomes 16th."""

    if num in ("11", "12", "13", "14", '15', '16', '17', '18', '19'):
        return num + "th"

    if num[-1] == "1":
        return num + "st"

    if num[-1] == "2":
        return num + "nd"

    if num[-1] == "3":
        return num + "rd"

    return num + "th"

def write_tex(budget_dict, leg_dict, score_dict):

    #Make the directory for the tex file for each member
    if not os.path.isdir('handout/'):
        os.mkdir('handout')

    ##Read in the members' information
    member_info = {}
    for row in unicode_csv_reader(open("./memberinfo.csv", "rU"),
            delimiter=",", codec='utf-8'):

        if row[0] == "Member":
            continue

        member = row[0]
        body = row[1]
        district = row[2]
        picturefile = row[3]
        fullname = row[4]
        party = row[5]
        cities = row[6]
        member_info[member] = {"body":body, "district":district,
                "picturefile":picturefile, "fullname":fullname,
                "party":party, "cities":cities}

    ##And now get the bill information
    billinfo = {}
    for row in unicode_csv_reader(open("./BillDescriptions.csv", "rb"),
            delimiter=",", codec='utf-8'):
        if row[0] == "Bill Prefix":
            continue

        prefix = row[0]
        number = row[1]
        title = row[2]
        description = row[3]
        description = description.replace("$", "\$")
        billinfo[ (prefix, number) ] = {"title":title,
                "description":description}

    for member in score_dict:
        raw_tex = file("./handout.tex").read()

        raw_tex = raw_tex.replace("#PICTURE_FILE#", "../images/" + \
                member_info[member]["body"] + "/" + \
                member_info[member]["picturefile"])

        #Get the percent score and the member's grade
        member_percent = score_dict[member]['overall_percent_score']
        roundmember = "%.1f" % round(member_percent*100, 3)
        if member_percent > .965:
            grade = "A+"
            color = "Green"
        elif member_percent > .935:
            grade = "A"
            color = "Green"
        elif member_percent > .895:
            grade = "A-"
            color = "Green"            
        elif member_percent > .865:
            grade = "B+"
            color = "YellowGreen"
        elif member_percent > .835:
            grade = "B"
            color = "YellowGreen"
        elif member_percent > .795:
            grade = "B-"
            color = "YellowGreen"            
        elif member_percent > .765:
            grade = "C+"
            color = "YellowOrange"
        elif member_percent > .735:
            grade = "C"
            color = "YellowOrange"
        elif member_percent > .695:
            grade = "C-"
            color = "YellowOrange"            
        elif member_percent > .665:
            grade = "D+"
            color = "RedOrange"
        elif member_percent > .635:
            grade = "D"
            color = "RedOrange"
        elif member_percent > .595:
            grade = "D-"
            color = "RedOrange"            
        elif member_percent >= 0:
            grade = "F"
            color = "Red"
        else:
            grade = ""
            color = "gray"
        raw_tex = raw_tex.replace("#NUMBERSCORE#", roundmember)    
        raw_tex = raw_tex.replace("#GRADE#", grade)
        raw_tex = raw_tex.replace("#GRADE_COLOR#", color)

        raw_tex = raw_tex.replace("#MEMBER_NAME#",
                member_info[member]["fullname"])

        raw_tex = raw_tex.replace("#ORDINAL_DISTRICT#",
                convert_to_ordinal(member_info[member]["district"]))
        raw_tex = raw_tex.replace("#HOUSE#",
                member_info[member]["body"].title())
        raw_tex = raw_tex.replace("#PARTY#",
                member_info[member]["party"])
        raw_tex = raw_tex.replace("#CITIES#",
                member_info[member]["cities"])

        ##And that's all the member's information, so move on to bills

        split_tex = raw_tex.split("\n")
        info_line = [k for k in split_tex if "#BILL_VOTE_COLOR#" in k][0]
        info_index = split_tex.index(info_line)

        bills_dict = dict(budget_dict.get(member, {}))
        bills_dict.update(leg_dict[member])

        for bill in sorted([k for k in bills_dict if isinstance(k, tuple)],
            key=lambda x:x[5], reverse=True):
            if not isinstance(bill, tuple):
                continue
            if bills_dict[bill] == "NVR":
                continue

            bill_title = str(bill[0]) + ' ' + str(bill[1])
            try:
                bill_description = billinfo[ (bill[0], bill[1]) ]["description"]
            except KeyError:
#                print "Looking for", (bill[0], bill[1]), "in",
                if bill[5] > 0:
                    bill_description = "A very good bill."
                else:
                    bill_description = "A very bad bill."

            newinfo = str(info_line)
            newinfo = newinfo.replace("#BILL_TITLE#", bill_title)
            newinfo = newinfo.replace("#BILL_DESCRIPTION#", bill_description)
            if bill[5] > 0:
                right_vote = "Y"
            else:
                right_vote = "N"
            newinfo = newinfo.replace("#GOOD_VOTE#", right_vote)
            newinfo = newinfo.replace("#MEMBER_VOTE#", bills_dict[bill])
            newinfo = newinfo.replace("#VOTE_WEIGHT#", str(abs(int(bill[5]))))
            if bills_dict[bill] != right_vote:
                newinfo = newinfo.replace("#BILL_VOTE_COLOR#", "red")
            else:
                newinfo = newinfo.replace("#BILL_VOTE_COLOR#", "green")

            split_tex.insert(info_index, newinfo)
        split_tex.remove(info_line)

        f = open("./handout/" + member.encode("ascii",
            "ignore").replace(' ', '').replace('.', '') + ".tex", "w")
        #print split_tex
        flag = False
        if not flag:
            try:
                row = [unicode(k).encode("utf-8") for k in split_tex]
                flag = True
            except UnicodeDecodeError:
                pass
        if not flag:
            try:                
                row = [k.encode("latin1") for k in split_tex]
                flag = True
            except UnicodeDecodeError:
                pass
        if not flag:
            row = [repr(k) for k in split_tex]
            print "Forcing row to output.."
            
        f.write("\n".join(row))
        f.close()



def unicode_csv_reader(unicode_csv_data, dialect=csv.excel,
        codec="iso-8859-1", **kwargs):
    """Outputs utf-8 encoded strings from CSV"""
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data, codec),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
		yield [unicode(cell.strip(), 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data, codec):
    """A little generator for encoding data from the CSV files"""
    for line in unicode_csv_data:
        dline = line.decode(codec)
        yield dline.encode('utf-8')

def update_member_dict(member_dict, prefix, number, vdate, vplace, vtitle,
        score, ayes, noes, nvrs):
    """Updates member dict with results for a particular vote.

    Arguments:
    member_dict -- dictionary keyed by member names. Contains record of vote
                   cast for particular votes as well as score and max_score
    prefix, number, vdate, vtitle -- identifier for the vote
    score -- weight for vote. Positive value means we want an aye, negative
             means we want a nay
    ayes, noes, nvrs -- lists of member names who cast each type of vote
    """

    #If there's a member name that doesn't currently appear in member_dict
    #initialize with zero score and max_score
    for member in ayes+noes+nvrs:
        if member not in member_dict:
            member_dict[member] = {'score':0, 'max_score':0}

    for member in ayes:
        member_dict[member][ (prefix, number, vdate, vplace,
            vtitle, score) ] = 'Y'
        if score > 0: #They voted ayes on positive score
            member_dict[member]['score'] += score
            member_dict[member]['max_score'] += score
        else:
            member_dict[member]['max_score'] += abs(score)
    for member in noes:
        member_dict[member][ (prefix, number, vdate, vplace,
            vtitle, score) ] = 'N'
        if score > 0:
            member_dict[member]['max_score'] += score
        else:  #Voted no on negative score
            member_dict[member]['score'] += abs(score)
            member_dict[member]['max_score'] += abs(score)
    for member in nvrs: #For NVRs, don't change the score, just record the NVR
        member_dict[member][ (prefix, number, vdate, vplace,
            vtitle, score) ] = 'NVR'

def member_vote_histories(vote_csv):

    member_dict = {}
    vote_items = []

    for row in unicode_csv_reader(open(vote_csv, 'rb'), delimiter="\t",
            quotechar = '"'):

        if row[0] == 'Bill Prefix':
            continue ##Skip the column title line

        prefix = row[0]
        number = row[1]
        billid = row[2]
        vdate = row[3]
        vplace = re.sub("\s{2,}", " ", row[4].strip())
        vtitle = re.sub("\s{2,}", " ", row[5].strip())
        score = int(row[6])

        ayes, noes, nvrs = lookup_votes(billid, vdate, vplace, vtitle)

        update_member_dict(member_dict, prefix, number, vdate, vplace,
                vtitle, score, ayes, noes, nvrs)

        vote_items.append( (prefix, number, vdate, vplace, vtitle, score) )

    return member_dict, vote_items

def overall_member_scores(budget_dict, leg_dict):

    members = list(set(budget_dict.keys() + leg_dict.keys()))

    member_scores = {}
    for member in members:
        budget_score = budget_dict.get(member, {'score':0})['score']
        budget_max_score = budget_dict.get(member, {'max_score':0})['max_score']
        leg_score = leg_dict.get(member, {'score':0})['score']
        leg_max_score = leg_dict.get(member, {'max_score':0})['max_score']
        member_scores[member] = {}
        member_scores[member]['score'] = budget_score + leg_score
        member_scores[member]['max_score'] = budget_max_score + leg_max_score

        if budget_max_score > 0 and leg_max_score > 0:
            overall_score = (BUDGET_WEIGHT*budget_score/budget_max_score +
                    LEG_WEIGHT*leg_score/leg_max_score)/\
                            (BUDGET_WEIGHT + LEG_WEIGHT)
        elif budget_max_score > 0:
            overall_score = float(budget_score)/budget_max_score
        elif leg_max_score > 0:
            overall_score = float(leg_score)/leg_max_score
        else:
            overall_score = None

        member_scores[member]['overall_percent_score'] = overall_score

    return member_scores


def main(budget_vote_csv, leg_vote_csv):
    """Arguments:
    budget_vote_csv -- name of csv file containing budget votes
    leg_vote_csv -- name of csv file containing non-budget votes
    """
    budget_member_dict, budget_vote_items = \
            member_vote_histories(budget_vote_csv)

    leg_member_dict, leg_vote_items = \
            member_vote_histories(leg_vote_csv)

    member_scores = overall_member_scores(budget_member_dict, leg_member_dict)

    write_result(budget_member_dict, leg_member_dict, member_scores,
            budget_vote_items + leg_vote_items)
    write_tex(budget_member_dict, leg_member_dict, member_scores)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        print "Usage: python2 reportcard.py <budget_csv> <leg_csv>"
