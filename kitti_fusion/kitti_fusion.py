import numpy as np
import open3d as o3d
import time
import copy
import loadData
import cv2
from checkCoin import checkCoin

######################## Initialization Various ########################

RT = np.array([[7.533745e-03, -9.999714e-01, -6.166020e-04, -4.069766e-03],
               [1.480249e-02, 7.280733e-04, -9.998902e-01, -7.631618e-02],
               [9.998621e-01, 7.523790e-03, 1.480755e-02, -2.717806e-01],
               [0.0, 0.0, 0.0, 1.0]])

R_rect_00 = np.array([[9.999239e-01, 9.837760e-03, -7.445048e-03, 0.0],
                      [-9.869795e-03, 9.999421e-01, -4.278459e-03, 0.0],
                      [7.402527e-03, 4.351614e-03, 9.999631e-01, 0.0],
                      [0.0, 0.0, 0.0, 1]])

P_rect_00 = np.array([[7.215377e+02, 0.000000e+00, 6.095593e+02, 0.000000e+00],
                      [0.000000e+00, 7.215377e+02, 1.728540e+02, 0.000000e+00],
                      [0.000000e+00, 0.000000e+00, 1.000000e+00, 0.000000e+00]])

Calibration_matrix = P_rect_00 @ R_rect_00 @ RT

############################### Load Data ################################
path = "./"
path_lidar = path + "velodyne_points/data/"
path_image = path + "image_02/data/"

file_list = loadData.load_data(path_lidar)
image_list = loadData.load_data(path_image)

filename = 'save.bin'
f = open(filename,'rb')
data = f.read()
semanticmap = np.frombuffer(data, dtype=np.int64)
semanticmap = semanticmap.reshape(620,2048)
print(semanticmap)
f.close()

cv2.namedWindow('Show Image')

##########################################################################
############################### Main Loop ################################
##########################################################################

# files = file_list[0]
# for i in range(len(file_list)):

i=1
img = cv2.imread(path_image + image_list[i], cv2.IMREAD_COLOR)
pointcloud = np.fromfile(path_lidar+file_list[i], dtype = np.float32)
pointcloud = pointcloud.reshape(-1,4)

# Cropping
#pointcloud = pointcloud[(pointcloud[:,2] >= -1.40)]
pointcloud = pointcloud[(pointcloud[:,0] >= 0)]
pointcloud = pointcloud[(pointcloud[:,0] <= 30)]
pointcloud = pointcloud[(pointcloud[:,1] >= -10)]
pointcloud = pointcloud[(pointcloud[:,1] <= 10)]

pointcloud[:,3] = 1.0

start = time.time()
Y = (Calibration_matrix @ pointcloud.T).T
print(time.time() - start)

Point_x = Y[:,0] / Y[:,2]
Point_y = Y[:,1] / Y[:,2]

Point_x = Point_x.astype('int32')
Point_y = Point_y.astype('int32')

Point_x = Point_x.reshape(-1,1)
Point_y = Point_y.reshape(-1,1)
lidar2pixel = np.append(Point_x,Point_y, axis =1)
# print(len(lidar2pixel))
# print(Point_y)

# start = time.time()
for i in range(0, len(Point_x)):
    cv2.circle(img, (Point_x[i], Point_y[i]), 1, (0, 0, 255), -1)
# print(time.time() - start)

# print(semanticmap.shape)
# print(lidar2pixel.shape)
fusion_index = checkCoin(lidar2pixel,semanticmap,24)

pointcloud_3d = pointcloud[:,0:2]
roadpoint = pointcloud_3d[fusion_index,:]
roadpoint2pixel = lidar2pixel[fusion_index,:]

# for i in range(0, len(semanticmap)):
#     print(semanticmap[i][:])


for i in range(0, len(roadpoint2pixel)):
    cv2.circle(img, (roadpoint2pixel[i][0], roadpoint2pixel[i][1]), 1, (0, 255, 0), -1)

# cv2.circle(img,(1,1), 1, (255, 255, 0), -1)
cv2.imshow("Show Image", img)
cv2.waitKey(0)

#for files in file_list:
#    dt = 0.2
