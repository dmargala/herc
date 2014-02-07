import subprocess

for line in file("rep_filenames"):

    fn = line.strip()
    filetoget = "http://cssrc.us/lib/uploads/senators/" + fn
    P = subprocess.Popen("wget " + filetoget, shell=True)
    P.wait()
