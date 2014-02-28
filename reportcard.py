#!/usr/bin/env python

import csv
import os
import re
import sys
import argparse


import herc

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

def load_member_info(member_info_filename):
    # Read in the members' information
    member_info = {}
    keys = ('member', 'body', 'district', 'picturefile', 'fullname', 'party', 'cities')
    for row in herc.util.unicode_csv_reader(open(member_info_filename, "r"), delimiter=",", codec='utf-8'):
        if row[0] == "Member":
            continue
        member = row[0]
        member_info[member] = { key : row[i+1] for i, key in enumerate(keys[1:]) }
    return member_info

def load_bill_desc(bill_desc_filename):
    # Read in the bill information
    bill_desc = {}
    for row in herc.util.unicode_csv_reader(open(bill_desc_filename, "r"), delimiter=",", codec='utf-8'):
        if row[0] == "Bill Prefix":
            continue
        prefix = row[0]
        number = row[1]
        title = row[2]
        description = row[3]
        description = description.replace("$", "\$")
        bill_desc[ (prefix, number) ] = {"title":title, "description":description}
    return bill_desc

def load_tex_template(tex_template):
    # Make the directory for the tex file for each member
    if not os.path.isdir(tex_template):
        os.mkdir(tex_template)
    return file("%s.tex" % tex_template).read()

def write_tex(tex_template, members, member_info, bill_desc, year):
    for member in members:
        raw_tex = load_tex_template(tex_template)

        raw_tex = raw_tex.replace("#YEAR#", str(year))

        picture_filename = os.path.join("..","images",member_info[member]["body"],member_info[member]["picturefile"])
        raw_tex = raw_tex.replace("#PICTURE_FILE#", picture_filename)

        #Get the percent score and the member's grade
        member_percent = members[member]['overall_percent_score']
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

        bills_dict = dict(members.get(member, {}))

        for bill in sorted([k for k in bills_dict if isinstance(k, tuple)],
            key=lambda x:x[5], reverse=True):
            if not isinstance(bill, tuple):
                continue
            if bills_dict[bill] == "NVR":
                continue

            bill_title = str(bill[0]) + ' ' + str(bill[1])
            try:
                bill_description = bill_desc[ (bill[0], bill[1]) ]["description"]
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
        save_filename = os.path.join(tex_template,"%s.tex"%name_stripped)
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

def update_members(members, prefix, number, id, vdate, vplace, vtitle, score, ayes, noes, nvrs):
    """
    Updates member dict with results for a particular vote.

    Arguments:
    members -- dictionary keyed by member names. Contains record of vote
                   cast for particular votes as well as score and max_score
    prefix, number, vdate, vtitle -- identifier for the vote
    score -- weight for vote. Positive value means we want an aye, negative
             means we want a nay
    ayes, noes, nvrs -- lists of member names who cast each type of vote
    """
    # If there's a member name that doesn't currently appear in members
    # initialize with zero score and max_score
    for member in ayes+noes+nvrs:
        if member not in members:
            members[member] = {'score':0, 'max_score':0}
    for member in ayes:
        members[member][ (prefix, number, vdate, vplace, vtitle, score) ] = 'Y'
        if score > 0: # They voted ayes on positive score
            members[member]['score'] += score
            members[member]['max_score'] += score
        else:
            members[member]['max_score'] += abs(score)
    for member in noes:
        members[member][ (prefix, number, vdate, vplace, vtitle, score) ] = 'N'
        if score > 0:
            members[member]['max_score'] += score
        else:  # Voted no on negative score
            members[member]['score'] += abs(score)
            members[member]['max_score'] += abs(score)
    for member in nvrs: #For NVRs, don't change the score, just record the NVR
        members[member][ (prefix, number, vdate, vplace, vtitle, score) ] = 'NVR'

def finalize_scores(members):
    for member,votes in members.iteritems():
        members[member]['overall_percent_score'] = votes['score']/votes['max_score']

def main():
    # parse command-line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v","--verbose", action = "store_true",
        help = "provide more verbose output")
    parser.add_argument("--leg-vote", type = str, default = "legvotes",
        help = "name of csv file containing non-budget votes")
    parser.add_argument("--member-info", type = str, default = "memberinfo.csv",
        help = "name of csv file containing member info")
    parser.add_argument("--bill-desc", type = str, default = "BillDescriptions.csv",
        help = "name of csv file containing bill descriptions")
    parser.add_argument("--tex-template", type = str, default = "handout")
    parser.add_argument("--year", type = int, default = 2012,
        help = "year to create report card for")
    # Read arguements
    args = parser.parse_args()
    
    # Open leg votes
    leg_votes = herc.results.load(os.path.join(str(args.year),args.leg_vote))
    leg_vote_items = leg_votes['bills']

    members = {}
    for bill in leg_vote_items:
        update_members(members, **bill)

    finalize_scores(members)

    member_info_filename = os.path.join(str(args.year),args.member_info)
    member_info = load_member_info(member_info_filename)

    bill_desc_filename = os.path.join(str(args.year),args.bill_desc)
    bill_desc = load_bill_desc(bill_desc_filename)

    write_tex(os.path.join(str(args.year),args.tex_template), members, member_info, bill_desc, args.year)

if __name__ == '__main__':
    main()
