#!/usr/bin/env python
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

def write_tex(tex_template, outdir, members, member_info, bill_desc, year):
    for member in members:
        raw_tex = file("%s.tex" % tex_template).read()

        raw_tex = raw_tex.replace("#YEAR#", str(year))

        if member in member_info:
            current_member_info = member_info[member]
        else:
            current_member_info = {'member':member, 'body':'<missing>', 'district':"0", 'picturefile':'missing.jpg', 'fullname':member, 'party':'<missing>', 'cities':'<missing>'}

        picture_filename = os.path.join("..","images",current_member_info['body'],current_member_info["picturefile"])
        raw_tex = raw_tex.replace("#PICTURE_FILE#",picture_filename)

        #Get the percent score and the member's grade
        member_percent = members[member]['overall_percent_score']
        roundedscore = "%.1f" % round(member_percent*100, 3)
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
        raw_tex = raw_tex.replace("#NUMBERSCORE#", roundedscore)    
        raw_tex = raw_tex.replace("#GRADE#", grade)
        raw_tex = raw_tex.replace("#GRADE_COLOR#", color)
        raw_tex = raw_tex.replace("#MEMBER_NAME#", current_member_info["fullname"])
        raw_tex = raw_tex.replace("#ORDINAL_DISTRICT#", convert_to_ordinal(current_member_info["district"]))
        raw_tex = raw_tex.replace("#HOUSE#", current_member_info["body"].title())
        raw_tex = raw_tex.replace("#PARTY#", current_member_info["party"])
        raw_tex = raw_tex.replace("#CITIES#", current_member_info["cities"])

        # And that's all the member's information, so move on to bills

        split_tex = raw_tex.split("\n")
        info_line = [k for k in split_tex if "#BILL_VOTE_COLOR#" in k][0]
        info_index = split_tex.index(info_line)

        bills_dict = dict(members.get(member, {}))

        for bill in sorted([k for k in bills_dict if isinstance(k, tuple)], key=lambda x:x[5], reverse=True):
            if not isinstance(bill, tuple):
                raise RuntimeError('bill is not instance? : %s ' % bill)
            # if bills_dict[bill] == "NVR":
            #     continue
            bill_title = str(bill[0]) + ' ' + str(bill[1])
            try:
                bill_description = bill_desc[ (bill[0], bill[1]) ]["description"]
            except KeyError:
                raise RuntimeError('No bill info for %s %s' % (bill[0], bill[1]))

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
            if bills_dict[bill] == 'Y':
                newinfo = newinfo.replace("#BILL_VOTE_COLOR#", "green")
            elif bills_dict[bill] == 'N':
                newinfo = newinfo.replace("#BILL_VOTE_COLOR#", "red")
            else:
                newinfo = newinfo.replace("#BILL_VOTE_COLOR#", "gray")

            split_tex.insert(info_index, newinfo)
        split_tex.remove(info_line)

        name_stripped = member.encode("ascii","ignore").replace(' ', '').replace('.', '')
        save_filename = os.path.join(outdir,"%s.tex"%name_stripped)
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
    prefix, number, id, vdate, vtitle -- identifier for the vote
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
    """
    Updates member dict with final scores (calculates 'overall_percent_score')

    Arguments:
    members -- dictionary keyed by member names. 
    """
    for member,votes in members.iteritems():
        members[member]['overall_percent_score'] = float(votes['score'])/votes['max_score']

def main():
    # parse command-line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v","--verbose", action = "store_true",
        help = "provide more verbose output")
    parser.add_argument("--leg-vote", type = str, default = "legvotes",
        help = "name of csv file containing bill vote records")
    parser.add_argument("--member-info", type = str, default = "memberinfo.csv",
        help = "name of csv file containing member info")
    parser.add_argument("--bill-desc", type = str, default = "BillDescriptions.csv",
        help = "name of csv file containing bill descriptions")
    parser.add_argument("--tex-template", type = str, default = "handout",
        help = "name of tex file to use as reportcard template")
    parser.add_argument("--year", type = int, default = 2012,
        help = "year to create report card for")
    parser.add_argument("--clobber", action = "store_true")
    # Read arguements
    args = parser.parse_args()
    
    # Load leg votes from file
    leg_votes_filename = os.path.join(str(args.year),args.leg_vote)
    if args.verbose:
        print 'Reading bill vote records from file: %s' % os.path.abspath(leg_votes_filename)+'.json'
    leg_votes = herc.results.load(leg_votes_filename)
    leg_vote_items = leg_votes['bills']
    if args.verbose:
        print 'Read %d bill vote records.' % len(leg_vote_items)

    # Create member voting record from leg votes entries
    members = {}
    for bill in leg_vote_items:
        update_members(members, **bill)
    if args.verbose:
        print 'There are %d members listed in the bill vote records.' % len(members)
    # Finalize member vote scores
    finalize_scores(members)

    # Load member info
    member_info_filename = os.path.join(str(args.year),args.member_info)
    if args.verbose:
        print 'Reading member info from file: %s' % os.path.abspath(member_info_filename)
    member_info = load_member_info(member_info_filename)
    if args.verbose:
        print 'Found member info for %d members.' % len(member_info)

    # Load bill descriptions
    bill_desc_filename = os.path.join(str(args.year),args.bill_desc)
    if args.verbose:
        print 'Reading bill description from file: %s' % os.path.abspath(bill_desc_filename)
    bill_desc = load_bill_desc(bill_desc_filename)
    if args.verbose:
        print 'Read %d bill descriptions.' % len(bill_desc)

    # Create output directory
    outdir = os.path.join(str(args.year),args.tex_template)
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    # Save a log file in output reportcard directory
    results = herc.results.Results(args)
    results.save(os.path.join(outdir,'reportcard'), overwriteOk=args.clobber)

    # Write tex file output
    write_tex(args.tex_template, outdir, members, member_info, bill_desc, args.year)
    if args.verbose:
        print 'Finished writing tex files to: %s' % os.path.abspath(outdir)
        print 'To make pdf\'s from tex files:'
        print '\tcd %s' % os.path.abspath(outdir)
        print '\tfor fn in $(ls -1 *.tex); do /usr/texbin/pdflatex -interaction=nonstopmode $fn; done'

if __name__ == '__main__':
    main()
