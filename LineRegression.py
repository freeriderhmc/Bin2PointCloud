# FreeRiderHMC Team
# main_Ver.3    0708
# Segment the road just by cutting the z values below threshold instead of RANSAC segmentation
# Visualize Each Clusters
# load binary data
# Add sequent visualization
# Add z slicing
# Add Sorting convexhull

import sys
import os
import numpy as np
import open3d as o3d
import time
import math
import operator
from sklearn.cluster import MeanShift
from sklearn.neighbors import KDTree
import clusteringModule as clu
import planeSegmentation as seg
import loadData
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

############################## Macro ###############################
pi = 3.141592653589793238


######################### Define Function ##########################

def get_angle(input_list):
    angle = math.atan2(input_list[1], input_list[0])
    if input_list[1]<0:
        angle = angle+2*pi
    return angle*180/pi

def diff_angle(ang1, ang2):
    if abs(ang1-ang2) >180:
        diffang = 360-abs(ang1-ang2)
    else:
        diffang = abs(ang1-ang2)
    return diffang


########################### Variable init ##########################

# Set mod
mod = sys.modules[__name__]

# Expand iteration limit
sys.setrecursionlimit(5000)

# Set Car Standard
carz_min, carz_max = 0, 2
carx_min, carx_max = 1.5, 5
cary_min, cary_max = 1.5, 5
car_count = 0
car = False

Axis_Points = [[0,0,0], [20,0,0],[0,20,0]]
Axis_Lines = [[0,1],[0,2]]

colors = [[0,0,0] for i in range(len(Axis_Lines))]

line_set = o3d.geometry.LineSet(points = o3d.utility.Vector3dVector(Axis_Points), lines = o3d.utility.Vector2iVector(Axis_Lines))
line_set.colors = o3d.utility.Vector3dVector(colors)


# Load binary data
path = './2011_09_26/2011_09_26_drive_0005_sync/velodyne_points/data/'

file_list = loadData.load_data(path)
num = 0

############################## Main Loop ############################

# get points from all lists
#for files in file_list:
    

files = file_list[2]
data = np.fromfile(path+files, dtype = np.float32)
data = data.reshape(-1,4)
data = data[:,0:3]



# Convert numpy into pointcloud 
cloud = o3d.geometry.PointCloud()
cloud.points = o3d.utility.Vector3dVector(data)

# Downsampling pointcloud
cloud_downsample = cloud.voxel_down_sample(voxel_size=0.1)

#print(cloud_downsample.segment_plane(0.4,300,300)[1])
#outerBox = [[20,-10,-1.8],[20,-10,-1.8]]
#cloud_downsample.crop()


# Convert pcd to numpy array
cloud_downsample = np.asarray(cloud_downsample.points)

# Crop Pointcloud -20m < x < 20m && -20m < y < 20m && z > -1.80m
cloud_downsample = cloud_downsample[((cloud_downsample[:, 0] <= 15))]
cloud_downsample = cloud_downsample[((cloud_downsample[:, 0] >= -15))]
cloud_downsample = cloud_downsample[((cloud_downsample[:, 1] <= 10))]
cloud_downsample = cloud_downsample[((cloud_downsample[:, 1] >= -10))]

# threshold z value cut the road
cloudoutliers = cloud_downsample[((cloud_downsample[:, 2] >= -1.3))] # -1.56


# Clustering Pointcloud
# adjust the threshold into Clustering
start = time.time()

tree = KDTree(cloudoutliers, leaf_size = 100)
clusters = clu.euclideanCluster(cloudoutliers, tree, 0.5)
print("number of estimated clusters : ", len(clusters))

print("How much time for Clustering")
print(time.time() - start)

cluster = np.empty([0,3])

clustersCloud = np.empty(shape = [0,3])
# Visualize Clusters

for i in range(len(clusters)):
    car_count = 0
    # Find the Cars
    
    # 1) Extract each cluster
    clusterCloud = cloudoutliers[clusters[i][:],:]
    
    #clustersCloud_pcd.points = np.append(clustersCloud_pcd.points,clusterCloud_pcd.points)
    
    # 2) Find Cars with weak condition
    z_max=z_min=x_max=x_min=y_max=y_min=0
    
    z_max = np.max(clusterCloud[:,2])
    z_min = np.min(clusterCloud[:,2])
    z_for_slicing = 4/5*z_min + 1/5*z_max

    '''
    #clusterCloud = clusterCloud[:,0:2]
    #clusterCloud[:,2] = z_for_slicing

    tempcloud = o3d.geometry.PointCloud()
    tempcloud.points = o3d.utility.Vector3dVector(clusterCloud)

    tempcloud.compute_convex_hull()
    
    print(type(clusterCloud))
    print(clusterCloud.shape)
    '''
    # slicing by z values
    clusterCloud = clusterCloud[(clusterCloud[:,2] >= z_for_slicing - 0.07)]
    clusterCloud = clusterCloud[(clusterCloud[:,2] <= z_for_slicing + 0.07)]
            
    x_max = np.max(clusterCloud[:,0])
    x_min = np.min(clusterCloud[:,0])
    y_max = np.max(clusterCloud[:,1])
    y_min = np.min(clusterCloud[:,1])
    
    
    x_len = abs(x_min - x_max)
    y_len = abs(y_min - y_max)
    z_len = abs(z_min - z_max)

    if  carx_min < x_len < carx_max and cary_min < y_len < cary_max and carz_min < z_len < carz_max:
        car_count += 1
        car = True
        end = False
    
    while(car):

        # Get Centroid
        x_sum = clusterCloud[:,0].sum() 
        y_sum = clusterCloud[:,1].sum()
        z_sum = clusterCloud[:,2].sum()
        
        num_points = len(clusterCloud)
        x_inner = x_sum / num_points
        y_inner = y_sum / num_points
        #z_inner = z_sum / num_points
        
        inner_point = [x_inner, y_inner]

        # Should get Centroid in other way
        # clusterCloud = np.append(clusterCloud, mean, axis=0)
        # print(clusterCloud)

        # Convert Numpy to Pointcloud
        clusterCloud_pcd = o3d.geometry.PointCloud()
        clusterCloud_pcd.points = o3d.utility.Vector3dVector(clusterCloud)
        
        

        ################ Convex hull and Sorting ################

        convexhull = clusterCloud[(clusterCloud_pcd.compute_convex_hull()[1])[:],:]
        length = len(convexhull)
        # Ordering the convex hull result
        convexhull_2D = convexhull[:,0:2]
        convexhull_2D = convexhull_2D - inner_point

        convexhull_angle = list(map(get_angle, convexhull_2D))
        #print(convexhull_angle)
        convexhull_dict = {}

        for j in range(0,length):
            convexhull_dict[convexhull_angle[j]] = convexhull_2D[j]
        
        convexhull_dict_sorted = sorted(convexhull_dict.items())

        convexhull_sorted_numpy = np.empty([0,2])
        for j in range(0,length):
            convexhull_sorted_numpy = np.append(convexhull_sorted_numpy, [convexhull_dict_sorted[j][1]],axis = 0) 
        #convexhull_dict = list(convexhull_dict.values())
        #convexhull_dict_sorted = convexhull_dict_sorted[:][1]

        #print(convexhull_sorted_numpy)    


        ################### Linear Regression ###################
                        
        line1_clust = np.empty([0,2])
        line2_clust = np.empty([0,2])
        line3_clust = np.empty([0,2])
        flag1 = False
        flag2 = False

        angle_clust = np.array([0,1]).reshape(-1,1)

        longline = np.empty([0,2])
        shortline = np.empty([0,2])

        cnt = 0
        
        for j in range(length):
            #x_0~x_len-1
            x=convexhull_sorted_numpy[j][0]
            y=convexhull_sorted_numpy[j][1]
            if j-4<=0:
                xback1 = convexhull_sorted_numpy[0][0]
                yback1 = convexhull_sorted_numpy[0][1]
                xback2 = convexhull_sorted_numpy[0][0] 
                yback2 = convexhull_sorted_numpy[0][0]   
                xfront1 = convexhull_sorted_numpy[j+4][0]
                yfront1 = convexhull_sorted_numpy[j+4][1]
                xfront2 = convexhull_sorted_numpy[j+5][0]
                yfront2 = convexhull_sorted_numpy[j+5][1]
            elif j+4 >= length-1:
                xback1 = convexhull_sorted_numpy[j-4][0]
                yback1 = convexhull_sorted_numpy[j-4][1]
                xback2 = convexhull_sorted_numpy[j-5][0] 
                yback2 = convexhull_sorted_numpy[j-5][0]   
                xfront1 = convexhull_sorted_numpy[length-1][0]
                yfront1 = convexhull_sorted_numpy[length-1][1]
                xfront2 = convexhull_sorted_numpy[length-1][0]
                yfront2 = convexhull_sorted_numpy[length-1
                ][1]
            else:
                xback1 = convexhull_sorted_numpy[j-4][0]
                yback1 = convexhull_sorted_numpy[j-4][1]
                xback2 = convexhull_sorted_numpy[j-5][0] 
                yback2 = convexhull_sorted_numpy[j-5][0]   
                xfront1 = convexhull_sorted_numpy[j+4][0]
                yfront1 = convexhull_sorted_numpy[j+4][1]
                xfront2 = convexhull_sorted_numpy[j+5][0]
                yfront2 = convexhull_sorted_numpy[j+5][1]

            aback1 = get_angle([xback1-x, yback1-y])
            aback2 = get_angle([xback2-x, yback2-y])
            afront1 = get_angle([xfront1-x, yfront1-y])
            afront2 = get_angle([xfront2-x, yfront2-y])
            print(diff_angle(aback1,afront1))
            
            if flag1 == False and flag2 == False:
                line1_clust = np.append(line1_clust, [convexhull_sorted_numpy[j][:]], axis = 0)
                if 120>diff_angle(aback1,afront1)>85 or 120>diff_angle(aback2,afront2)>85:    
                    flag1 = True
            elif flag1 == True and flag2 == False:
                line2_clust = np.append(line2_clust, [convexhull_sorted_numpy[j][:]], axis = 0)
                cnt +=1
                if(cnt >= 5):
                    if 100>diff_angle(aback1,afront1)>80 or 100>diff_angle(aback2,afront2)>80:    
                        flag2 = True    
                        car = False
                # if 100>diff_angle(aback1,afront1)>80 or 100>diff_angle(aback2,afront2)>80:    
                #     flag2 = True
            # elif flag1 == True and flag2 == True:
            #     line3_clust = np.append(line3_clust, [convexhull_sorted_numpy[j][:]], axis = 0)
            #     if 100>diff_angle(aback1,afront1)>80 or 100>diff_angle(aback2,afront2)>80:    
            #         list1_clust = []
            #         list2_clust = []
            #         #print(line1_clust)
                    
            
        #make fitter
        line_fitter = LinearRegression()
        if line1_clust != np.empty([0,2]):
            length = len(line1_clust[:][:,0])
            xline1 = line1_clust[:][:,0].reshape([length,1])
            yline1 = line1_clust[:][:,1].reshape([length,1])
            line1_fit = line_fitter.fit(xline1,yline1)
            line1dy = line1_fit.coef_
            line1bias = line1_fit.intercept_ 
            line1pred = line1_fit.predict(xline1).reshape([length,1])       
            print('*'*8)
            print(line1pred[:])
            print('*'*20)
    
        if line2_clust != np.empty([0,2]):
            length = len(line2_clust[:][:,0])
            xline2 = line2_clust[:][:,0].reshape([length,1])
            yline2 = line2_clust[:][:,1].reshape([length,1])
            line2_fit = line_fitter.fit(xline2,yline2)
            line2dy = line2_fit.coef_
            line2bias = line2_fit.intercept_

        #plot for check
        plt.figure()        
        plt.scatter(line1_clust[:][:,0],line1_clust[:][:,1],color ='black')
        plt.scatter(line2_clust[:][:,0],line2_clust[:][:,1],color ='blue')
        plt.plot(xline1,line1pred[:],color = 'red')
        plt.show()

        break
        
    # temp_pcd = o3d.geometry.PointCloud()
    # temp_pcd.points = o3d.utility.Vector3dVector(convexhull)

    # if i%3 == 0:
    #     temp_pcd.paint_uniform_color([1,0,0])
    # elif i%3 == 1:
    #     temp_pcd.paint_uniform_color([0,1,0])
    # else:
    #     temp_pcd.paint_uniform_color([0,0,1])



    # # Set Visualizer and Draw x, y Axis
    # vis = o3d.visualization.Visualizer()
    # vis.create_window()
    
    # #Draw Axis
    # vis.add_geometry(line_set)
    # vis.run()
    
    # vis.add_geometry(temp_pcd)
    # vis.run()
        
        ############ after convex hull , if not a car -> continue (next loop)
        
     
'''
# For Painting if it is a car
if i%3 == 0:
    clusterCloud_pcd.paint_uniform_color([1,0,0])
elif i%3 == 1:
    clusterCloud_pcd.paint_uniform_color([0,1,0])
else:
    clusterCloud_pcd.paint_uniform_color([0,0,1])

# Visualization
vis.add_geometry(clusterCloud_pcd)
vis.run()'''
    
            

# #print(car_count)
# num += 1
# #print (num)


# # if want to pause at each frame 
# input("Press Enter to continue...")

# vis.clear_geometries()

    
    
# vis.destroy_window()
    

#clusterCloud.paint_uniform_color([0.1, 0.9, 0.1])



# Visualization
#pcd_processed = o3d.geometry.PointCloud()
#pcd_processed.points = o3d.utility.Vector3dVector(cloudoutliers)





'''
# Load a pcd data
pcd_load = o3d.io.read_point_cloud("./kitti_pcd/pcd0000000000.pcd")
pcd_downsample = pcd_load.voxel_down_sample(voxel_size=0.3)
print(pcd_load)
'''
