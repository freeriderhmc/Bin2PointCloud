import sys
import os
import numpy as np

path_dir = '../data/' # CHANGE HERE!
file_list = os.listdir(path_dir)
file_list.sort()

for files in file_list:
    tmp = np.fromfile(files,  dtype=np.float32)
    prev = tmp[0:3]
    for i in range(1, int(len(tmp))/4):
        prev = np.vstack([prev,tmp[4*i:4*i+3]])

'''
###############concatenate method######################
array_1 = np.array([1,2,3,4,5,6,7,8,9,10,11,12])
prev = array_1[0:3]
for i in range(1,int(len(array_1)/4)):
    prev = np.vstack([prev,array_1[4*i:4*i+3]])

print(prev)
########################################################
'''
