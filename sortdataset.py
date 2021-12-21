import h5py
import os
import numpy as np
import shutil
import time
import errno
import os
from datetime import datetime

def create_output_folders(wd):
    mydir = os.path.join(wd, f"sorted_dataset{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
    defdir = os.path.join(mydir,'defect')
    faultfdir = os.path.join(mydir,'faultfree')
    try:
        os.makedirs(defdir)
        os.makedirs(faultfdir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise  # This was not a "directory exist" error..
    return [defdir, faultfdir]

def get_path_list(wd):
    path_list = []
    for subdir, dirs, files in os.walk(wd):
        for file in files:
            #print os.path.join(subdir, file)
            filepath = subdir + os.sep + file

            if "sorted_dataset" not in filepath:
                if filepath.endswith(".hdf5"):
                    # print (filepath)
                    path_list.append(filepath)
    return path_list

def count_classes(segmap):
    counts = {'casing':0, 'defect':0, 'background':0}
    for row in segmap:
            counts['background'] += np.count_nonzero(row==0)
            counts['casing'] += np.count_nonzero(row==1)
            counts['defect'] += np.count_nonzero(row==2)
    return counts

wd = os.path.abspath(os.path.dirname(__file__))
# get list with location of all hdf5 files of the data set
path_list = get_path_list(wd)
# print(path_list)

# create output folders for defect and fault free images
out = create_output_folders(wd)
# print(out)

defcount = 0
faultfcount = 0
backgcount = 0
sdefcount = 0
for p in path_list:
    f = h5py.File(p,'r')
    segmap = f['segmap']
    segmap = np.dsplit(segmap,2)[0]
    # t0 = time.time()
    counts = count_classes(segmap)
    # print(counts)
    # print(time.time()-t0)    
    # if counts['background'] == 0:
    if counts['defect'] >= 50:
        shutil.copy(p,os.path.join(out[0],f"{defcount}.hdf5"))
        defcount += 1
    elif counts['defect'] == 0:
        shutil.copy(p,os.path.join(out[1],f"{faultfcount}.hdf5"))
        faultfcount += 1
    else:
        sdefcount += 1
    # else:
    #     backgcount += 1
print([defcount,faultfcount,backgcount,sdefcount])