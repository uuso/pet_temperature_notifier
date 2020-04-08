import os

def file_cutlines(filepath, linescount):
    if not os.path.exists(filepath): return

    os.rename(filepath, filepath+".backup")
    with open(filepath+".backup", "r") as srcfile:
        with open(filepath, "w") as dstfile:
            for num, line in enumerate(srcfile):
                if num >= linescount:
                    dstfile.write(line)
    os.remove(filepath+".backup")