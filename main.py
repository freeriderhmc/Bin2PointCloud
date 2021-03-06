import sys
import os
import numpy as np
import open3d as o3d
import time
import math
import operator
from sklearn.cluster import MeanShift
from sklearn.neighbors import KDTree
from matplotlib import pyplot as plt
from sklearn.linear_model import LinearRegression

import clusteringModule as clu
import lineSegmentation as seg
import loadData
import sortCar as socar
from TrackingModule import track

####################################################
########### Setting ################################
####################################################

pi = 3.141592653589793238

def get_angle(input_list):
    angle = math.atan2(input_list[1], input_list[0])
    return angle


# Set mod
mod = sys.modules[__name__]

# Set Track list
Track_list = []

# Expand iteration limit
sys.setrecursionlimit(5000)

# Set Car Standard
carz_min, carz_max = 0, 3
carx_min, carx_max = 1, 7.5
cary_min, cary_max = 1, 7.5

# Set Visualizer and Draw x, y Axis
#vis = o3d.visualization.Visualizer()
#vis.create_window()

Axis_Points = [[0,0,0], [20,0,0],[0,20,0]]
Axis_Lines = [[0,1],[0,2]]

colors = [[0,0,0] for i in range(len(Axis_Lines))]

line_set = o3d.geometry.LineSet(points = o3d.utility.Vector3dVector(Axis_Points), lines = o3d.utility.Vector2iVector(Axis_Lines))
line_set.colors = o3d.utility.Vector3dVector(colors)


# Load binary data
path = './2011_09_26/2011_09_26_drive_0005_sync/velodyne_points/data/'
f = open("./2011_09_26/2011_09_26_drive_0005_sync/velodyne_points/timestamps.txt","r")



file_list = loadData.load_data(path)
frame_num = 0
pre_time_stamp = None

##################################################################################
########################### Main Loop ############################################
##################################################################################


# get points from all lists
for files in file_list:
    res = np.empty([0,6])
    print("{}th Frame".format(frame_num + 1))
    # Draw Axis
    #vis.add_geometry(line_set)
    #vis.run()

    # Get dt
    line = f.readline()
    line = (line.split(" ")[1]).split(":")
    time_stamp = 3600 * float(line[0]) + 60 * float(line[1]) + float(line[2])
    if pre_time_stamp:
        dt = time_stamp - pre_time_stamp


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

    cloud_for_clustering = o3d.geometry.PointCloud()
    cloud_for_clustering.points = o3d.utility.Vector3dVector(cloudoutliers)

    # Clustering Pointcloud
    # adjust the threshold into Clustering
    labels = np.asanyarray(cloud_for_clustering.cluster_dbscan(0.5,2))
    #print("number of estimated clusters : ", len(clusters))
    #print("How much time for Clustering")
    #print(time.time() - start)

    # Visualize Clusters
    for i in range(np.max(labels)):

        # Find the Cars
        # 1) Extract each cluster
        cluster = cloud_for_clustering.select_by_index(np.where(labels == i)[0])
        clusterCloud = np.asarray(cluster.points)

        # if size of cluster <= 10, then dismiss
        if len(clusterCloud) <= 10:
            
            continue
        
        # 2) Find Cars with weak condition
        z_max=z_min=x_max=x_min=y_max=y_min=0
        
        z_max = np.max(clusterCloud[:,2])
        z_min = np.min(clusterCloud[:,2])
        z_for_slicing = 4/5*z_min + 1/5*z_max

        # slicing by z values
        clusterCloud = clusterCloud[(clusterCloud[:,2] >= z_for_slicing - 0.08)]#0.15
        clusterCloud = clusterCloud[(clusterCloud[:,2] <= z_for_slicing + 0.08)]
        
        if(len(clusterCloud) is not 0):
            x_max = np.max(clusterCloud[:,0])
            x_min = np.min(clusterCloud[:,0])
            y_max = np.max(clusterCloud[:,1])
            y_min = np.min(clusterCloud[:,1])
        
       
        else:
            continue
        
        x_len = abs(x_min - x_max)
        y_len = abs(y_min - y_max)
        z_len = abs(z_min - z_max)

        if  carx_min < x_len < carx_max and cary_min < y_len < cary_max and carz_min < z_len < carz_max:
            templist = socar.sort_Car(clusterCloud, z_max, z_min)
            if(templist is not None):
                res = np.append(res, [templist], axis = 0)
        
    

    ########################################################################
    ############################## Tracking ################################
    ########################################################################
    print("how many meaured?" , len(res))
    print(res[:])

    # z_meas == res
    z_processed = np.zeros(len(res))
    ########## Track Update #############
    if Track_list:
        for i in range(0,len(Track_list)):
            Track_list[i].unscented_kalman_filter(res, z_processed, dt)

    ########## Create Track #############
    for i in range(0, len(z_processed)):
        if z_processed[i] == 1:
            continue
        
        # z_meas[i] that are not used : Create new track
        Track = track(res[i])
        Track_list.append(Track)
    
    ########## Track Management #########
    if Track_list:
        try:
            for i in range(0, len(Track_list)):
                # Activate Track
                if Track_list[i].Activated == 0 and Track_list[i].Age >= 5:
                    Track_list[i].Activated = 1
                
                # deActivate Track
                if Track_list[i].Activated == 1 and Track_list[i].DelCnt >= 5:
                    Track_list[i].Activated = 0
                
                # Delete Track
                if Track_list[i].DelCnt >= 10:
                    del Track_list[i]
                
                # Initialize Tracks' processed check
                Track_list[i].processed = 0

                # Save Trace of the Track
                if Track_list[i].Activated == 1:
                    state_x_temp = Track_list[i].state[0]
                    state_y_temp = Track_list[i].state[1]
                    Track_list[i].trace_x.append(state_x_temp)
                    Track_list[i].trace_y.append(state_y_temp)
                    
                    # Keep the length of trace by 20
                    '''if len(Track_list[i].trace) > 20:
                        del Track_list[i].trace[0]'''
                    #print(len(Track_list[i].trace))

        except:
            print("Track was deleted")

    # Visualization
    plt.figure()
    plt.xlim(-20,20)
    plt.ylim(-20,20)

    # plot Ego Vehicle
    plt.text(0, 0, 'EgoCar')

    plt.plot(res[:,0], res[:,1], 'ro')
    for i in range(0, len(Track_list)):
        if Track_list[i].Activated == 1:
            plt.plot(Track_list[i].state[0], Track_list[i].state[1], 'b*')
            plt.text(Track_list[i].state[0], Track_list[i].state[1], 'Track{}'.format(i+1))
            
            # Plot Track's trace
            #for j in range(0, len(Track_list[i].trace)):
            #    trace_for_plot
            plt.plot(Track_list[i].trace_x[:], Track_list[i].trace_y[:], 'g')             
    plt.show()
    
    for i in range(0, len(Track_list)):
        print("Track value: ".format(i), Track_list[i].state)

    pre_time_stamp = time_stamp
    frame_num += 1    
    #input("Press Enter to continue...")