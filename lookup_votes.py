#!/usr/bin/env python

import bs4
import os.path
import re
import urllib2
import sys
import datetime
import subprocess

import herc

def get_session_span(year):
    """ Returns the two year span (as a string) of the legislature session for specified year """
    if year < 1999:
        raise RuntimeError('Invalid year. Cannot lookup vote infor prior to 1999.')
    # Sessions span odd-even
    if year % 2 == 0:
        return "%d%d"%(year-1,year)
    else:
        return "%d%d"%(year,year+1)

def build_url_query(bill):
    year = int(datetime.datetime.strptime(bill['vdate'], "%m/%d/%y").date().strftime("%Y"))
    bill_id = bill['id']
    leg_url = "http://leginfo.legislature.ca.gov/faces/billVotesClient.xhtml"
    query = "?bill_id=" + get_session_span(year) + bill_id
    return leg_url+query

def parse_table(bill, votetable):
    """
    Finds the ayes, nays, and no votes corresponding bill in the votetable
    """
    rows = votetable.findAll("tr")[1:]
    # Iterate over rows in table
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
        # If this is the vote for this bill we were looking for return votes now
        if i % 5 == 4:
            if vd == bill['vdate'] and vp == bill['vplace'] and vt == bill['vtitle']:
                return [ayes, noes, nvrs]
    # We reached the end of the table and didn't find the vote we were looking for
    raise RuntimeError("Failed: %s %s" % (bill['id'], bill['vplace']))


def lookup_votes(bill):
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

    Note that, in our rainbow state, names need to be encoded with utf-8.
    Lapsing into ascii will screw up everything.

    Finally, if something goes wrong, it prints something to stderr and
    returns [[],[],[]].
    """

    url_query = build_url_query(bill)
    page = urllib2.urlopen(url_query)
    soup = bs4.BeautifulSoup(page)
    votetable = soup.find("table", id="billvotes")
    [ayes, noes, nvrs] = parse_table(bill, votetable)
    return [ayes, noes, nvrs]

def vote_histories(vote_csv):
    vote_items = []
    for row in herc.util.unicode_csv_reader(open(vote_csv, 'rb'), delimiter="\t", quotechar = '"'):
        if row[0] == 'Bill Prefix':
            continue ##Skip the column title line
        print row
        bill = {}
        bill['prefix'] = row[0]
        bill['number'] = row[1]
        bill['id'] = row[2]
        bill['vdate'] = row[3]
        bill['vplace'] = re.sub("\s{2,}", " ", row[4].strip())
        bill['vtitle'] = re.sub("\s{2,}", " ", row[5].strip())
        bill['score'] = int(row[6])
        try:
            ayes, noes, nvrs = lookup_votes(bill)
        except RuntimeError,e:
            print "Something went wrong: ", e
            sys.exit(-1)
        bill['ayes'] = ayes
        bill['noes'] = noes
        bill['nvrs'] = nvrs
        vote_items.append(bill)
    return vote_items

def main():
    import argparse
    # parse command-line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v","--verbose", action = "store_true",
        help = "provide more verbose output")
    parser.add_argument("--year", type = int, default = 2012,
        help = "year to create report card for")
    parser.add_argument("--input", type = str, default = "LegVotes.csv",
        help = "name of csv file list of bills to lookup votes for")
    parser.add_argument("--output", type = str, default = "legvotes",
        help = "name of output file")
    parser.add_argument("--clobber", action = "store_true")
    # Read arguements
    args = parser.parse_args()

    vote_items = vote_histories(os.path.join(str(args.year),args.input))

    results = herc.results.Results(args)
    results['bills'] = vote_items
    results.save(os.path.join(str(args.year),args.output), overwriteOk=args.clobber)

if __name__ == '__main__':
    main()
