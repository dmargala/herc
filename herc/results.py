import os
import sys
import time
import subprocess
import json

def githash(what='HEAD'):
    """
    Returns the hash for the HEAD of the git repo containing this file or a helpful
    error message string if this cannot be determined
    """
    # find the path of this file
    mypath = os.path.dirname(os.path.realpath(__file__))
    # get our git repo path assuming a standard checkout
    gitpath = os.path.join(mypath,os.pardir,'.git')
    if os.path.exists(gitpath):
        try:
            hash = subprocess.check_output(['git','--git-dir',gitpath,'rev-parse',what],stderr=subprocess.STDOUT).rstrip()
        except subprocess.CalledProcessError,e:
            hash = e.output
        except Exception,e:
            hash = repr(e)
    else:
        hash = 'cannot find git repo for %r' % mypath
    return hash

class Results(dict):
    """
    Represents a dictionary of results suitable for saving as json
    """
    def __init__(self, args=None):
        """
        Creates and returns a new dictionary with some standard headers. The optional
        args should be a dictionary (or something convertible to a dictionary via vars())
        of parsed command-line args.
        """
        self['time'] = time.ctime()
        self['argv'] = sys.argv
        self['uname'] = os.uname()
        self['git'] = githash()
        if args is not None:
            # vars() will convert an argparse.Namespace(...) into an arg dictionary
            self['args'] = vars(args)

    def save(self,name,overwriteOk=False):
        """
        Saves these results using the specified resource name.
        """
        jsonPath = name+'.json'
        if os.path.exists(jsonPath) and not overwriteOk:
            raise RuntimeError('results.save: will not overwrite %r' % jsonPath)
        with open(jsonPath,'w') as out:
            json.dump(self,out,indent=2,separators=(',', ': '))

def load(name):
    """
    Loads and returns the results for the specified named resource, or raises a RuntimeError
    if the resource is not available. Note that the return value is a plain dict and not a Results object.
    """
    jsonPath = name+'.json'
    if not os.path.exists(jsonPath):
        raise RuntimeError('load: resource not found %r' % jsonPath)
    with open(jsonPath,'r') as fin:
        results = json.load(fin)
    return results