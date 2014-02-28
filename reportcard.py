#!/usr/bin/env python

from bs4 import BeautifulSoup
import csv
import os
import re
import urllib2
import sys
#import xlwt

import argparse

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

def write_tex(budget_dict, leg_dict, score_dict, year, member_info_filename, bill_desc_filename, template_name):

    # Make the directory for the tex file for each member
    handout_dir = os.path.join(str(year),template_name)
    if not os.path.isdir(handout_dir):
        os.mkdir(handout_dir)

    # Read in the members' information
    member_info = {}
    for row in unicode_csv_reader(open(member_info_filename, "r"), delimiter=",", codec='utf-8'):

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
    for row in unicode_csv_reader(open(bill_desc_filename, "r"), delimiter=",", codec='utf-8'):
        if row[0] == "Bill Prefix":
            continue

        prefix = row[0]
        number = row[1]
        title = row[2]
        description = row[3]
        description = description.replace("$", "\$")
        billinfo[ (prefix, number) ] = {"title":title, "description":description}

    for member in score_dict:
        raw_tex = file("%s.tex" % template_name).read()

        raw_tex = raw_tex.replace("#YEAR#", str(year))

        picture_filename = os.path.join("..","images",member_info[member]["body"],member_info[member]["picturefile"])
        raw_tex = raw_tex.replace("#PICTURE_FILE#", picture_filename)

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

        name_stripped = member.encode("ascii","ignore").replace(' ', '').replace('.', '')
        save_filename = os.path.join(str(year),template_name,"%s.tex"%name_stripped)
        outfile = open(save_filename, "w")
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
            
        outfile.write("\n".join(row))
        outfile.close()

def overall_member_scores(budget_dict, leg_dict, budget_weight, leg_weight):

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
            overall_score = (budget_weight*budget_score/budget_max_score +
                    leg_weight*leg_score/leg_max_score)/\
                            (budget_weight + leg_weight)
        elif budget_max_score > 0:
            overall_score = float(budget_score)/budget_max_score
        elif leg_max_score > 0:
            overall_score = float(leg_score)/leg_max_score
        else:
            overall_score = None

        member_scores[member]['overall_percent_score'] = overall_score

    return member_scores


def main():
    # parse command-line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v","--verbose", action = "store_true",
        help = "provide more verbose output")
    parser.add_argument("--budget-vote", type = str, default = "BudgetVotes.csv",
        help = "name of csv file containing budget votes")
    parser.add_argument("--leg-vote", type = str, default = "LegVotes.csv",
        help = "name of csv file containing non-budget votes")
    parser.add_argument("--member-info", type = str, default = "memberinfo.csv",
        help = "name of csv file containing member info")
    parser.add_argument("--bill-desc", type = str, default = "BillDescriptions.csv",
        help = "name of csv file containing bill descriptions")
    parser.add_argument("--tex-template", type = str, default = "handout")
    parser.add_argument("--year", type = int, default = 2012,
        help = "year to create report card for")
    parser.add_argument("--budget-weight", type = float, default = 0.0,
        help = "weight for budget portion of overall score")
    parser.add_argument("--leg-weight", type = float, default = 1.0,
        help = "weight for leg portion of overall score")
    # Read arguements
    args = parser.parse_args()

    budget_file_name = os.path.join(str(args.year),args.budget_vote)
    budget_member_dict, budget_vote_items = member_vote_histories(budget_file_name, args.year)
    
    leg_file_name = os.path.join(str(args.year),args.leg_vote)
    leg_member_dict, leg_vote_items = member_vote_histories(leg_file_name, args.year)

    member_scores = overall_member_scores(budget_member_dict, leg_member_dict, args.budget_weight, args.leg_weight)

    #write_result(budget_member_dict, leg_member_dict, member_scores, budget_vote_items + leg_vote_items)

    member_info_filename = os.path.join(str(args.year),args.member_info)
    bill_desc_filename = os.path.join(str(args.year),args.bill_desc)
    write_tex(budget_member_dict, leg_member_dict, member_scores, args.year, 
        member_info_filename, bill_desc_filename, args.tex_template)

if __name__ == '__main__':
    main()
