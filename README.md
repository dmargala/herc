## Files ##

reportcard.py
: The python script that generates the tex files for each member and the xls file for votes/scores.

BudgetVotes.csv
: Contains descriptions of votes on budget issues. reportcard.py uses this to look up members' voting records for the budget

LegVotes.csv
: Like BudgetVotes.csv, but for everything that's not the budget

BillDescriptions.csv
: Contains titles and descriptions of the bill that appear in LegVotes and BudgetVotes. Used when making the tex files

memberinfo.csv
: Member districts, full names, and paths to image files. Used when making tex files.

handout.txt
: Template tex file. Contains tags replaced by repordcard.py

images/
: Directory containing images of members
