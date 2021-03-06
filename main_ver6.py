# FreeRiderHMC Team
# main_Ver.5    0714
# Segment the road just by cutting the z values below threshold instead of RANSAC segmentation
# Visualize Each Clusters
# load binary data
# Add sequent visualization
# Add z slicing
# Add Sorting convexhull
# Add Line Ransac 
# Revise Extracting Line Algorithm

import sys
import os
import numpy as np
import open3d as o3d
import time
import math
import operator
from sklearn.cluster import MeanShift
from sklearn.neighbors import KDTree
from sklearn.linear_model import LinearRegression

from matplotlib import pyplot as plt

import clusteringModule as clu
import lineSegmentation as seg
import loadData

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

def get_distance(xy1,xy2):
    distance = ((xy1[0]-xy2[0])**2 + (xy1[1]-xy2[1])**2)**0.5
    return distance

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

file_list = loadData.load_data(path)
num = 0
car_count = 0


############################## Main Loop ############################

# get points from all lists
for files in file_list:
    # Draw Axis
    #vis.add_geometry(line_set)
    #vis.run()


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
    res = np.empty(shape = [0,6])
    
    
    for i in range(len(clusters)):     
        
        car_count = 0
        ###########################
        # Find the Cars
        
        # 1) Extract each cluster
        clusterCloud = cloudoutliers[clusters[i][:],:]
        
        #clustersCloud_pcd.points = np.append(clustersCloud_pcd.points,clusterCloud_pcd.points)
        
        # 2) Find Cars with weak condition
        z_max=z_min=x_max=x_min=y_max=y_min=0
        
        z_max = np.max(clusterCloud[:,2])
        z_min = np.min(clusterCloud[:,2])
        z_for_slicing = 5/6*z_min + 1/6*z_max

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
        clusterCloud = clusterCloud[(clusterCloud[:,2] >= z_for_slicing - 0.15)]
        clusterCloud = clusterCloud[(clusterCloud[:,2] <= z_for_slicing + 0.15)]
                
        x_max = np.max(clusterCloud[:,0])
        x_min = np.min(clusterCloud[:,0])
        y_max = np.max(clusterCloud[:,1])
        y_min = np.min(clusterCloud[:,1])
        
        
        x_len = abs(x_min - x_max)
        y_len = abs(y_min - y_max)
        z_len = abs(z_min - z_max)

        if  carx_min < x_len < carx_max and cary_min < y_len < cary_max and carz_min < z_len < carz_max:
            car_count += 1

            # Convert Numpy to Pointcloud
            clusterCloud_pcd = o3d.geometry.PointCloud()
            clusterCloud_pcd.points = o3d.utility.Vector3dVector(clusterCloud)

            convexhull = clusterCloud[(clusterCloud_pcd.compute_convex_hull()[1])[:],:]

            clusterCloud_2D = convexhull[:,0:2]
            points_x = clusterCloud_2D[:,0]
            points_y = clusterCloud_2D[:,1]

            # Line Segmentation to extract two lines
            inliers1_list, outliers1_list,_,_,_ = seg.RansacLine(clusterCloud_2D, 120, 0.1)

            line1_inliers = clusterCloud_2D[inliers1_list[:], :]
            line1_outliers = clusterCloud_2D[outliers1_list[:], :]
            

            #outliers = clusterCloud_2D[outliers1_list[:],:]
            inliers2_list, outliers2_list,_,_,_ = seg.RansacLine(line1_outliers, 60, 0.2)

            line2_inliers = line1_outliers[inliers2_list[:],:]

            #################### Linear Regression ###################
            line_fitter1 = LinearRegression()
            line_fitter2 = LinearRegression()
            len1 = len(line1_inliers[:][:,0])
            len2 = len(line2_inliers[:][:,0])

            xline1 = line1_inliers[:][:,0].reshape(len1,1)
            yline1 = line1_inliers[:][:,1].reshape(len1,1)
            xline2 = line2_inliers[:][:,0].reshape(len2,1)
            yline2 = line2_inliers[:][:,1].reshape(len2,1)

            
            line1_fit = line_fitter1.fit(xline1,yline1)
            line2_fit = line_fitter2.fit(xline2,yline2)
            line1dy = line1_fit.coef_
            #line1bias = line1_fit.intercept_ 
            line1pred = line1_fit.predict(xline1).reshape([len1,1])      
            
            line2dy = line2_fit.coef_       
            line2pred = line2_fit.predict(xline2).reshape([len2,1])      

            line1dict = {}
            line2dict = {}
            
            for i in range(0,len1):
                #line1dict[xline1[i]] = [xline1[i],yline1[i]]
                line1dict[xline1[i][0]] =line1_inliers[:][i,:]
            for i in range(0,len2):
                line2dict[xline2[i][0]] = line2_inliers[:][i,:]

            line1dict_sorted = sorted(line1dict.items())
            line2dict_sorted = sorted(line2dict.items())

            line1_sorted = np.empty([0,2])
            line2_sorted = np.empty([0,2])

            len1 = len(line1dict_sorted)
            len2 = len(line2dict_sorted)
            
            for j in range(0,len1):
                line1_sorted = np.append(line1_sorted, [line1dict_sorted[j][1]],axis = 0)

            for j in range(0,len2): 
                line2_sorted = np.append(line2_sorted, [line2dict_sorted[j][1]],axis = 0) 

            dis1= get_distance(line1_sorted[0],line1_sorted[len1-1])
            dis2= get_distance(line2_sorted[0],line2_sorted[len2-1])

            ####################### Get result #########################

            h = z_max - z_min + 0.5

            if dis1 > dis2:
                l = dis1
                w = dis2
                yaw = line1dy                 
                x1, y1 = line1_sorted[0][0], line1_sorted[0][1]
                x2, y2 = line1_sorted[len1-1][0], line1_sorted[len1-1][1]
                
                if get_distance([x1,y1], line2_sorted[len2//2]) < get_distance([x2,y2], line2_sorted[len2//2]):
                    xr, yr = x1, y1
                else: xr, yr = x2, y2

                if get_distance([xr,yr], line2_sorted[0]) < get_distance([xr,yr], line2_sorted[len2-1]):
                    x3, y3 = line2_sorted[len2-1][0], line2_sorted[len2-1][1] 
                else: x3, y3 = line2_sorted[0][0], line2_sorted[0][1] 

            else:
                l = dis2
                w = dis1
                yaw = line2dy
                x1, y1 = line2_sorted[0][0], line2_sorted[0][1]
                x2, y2 = line2_sorted[len2-1][0], line2_sorted[len2-1][1]

                if get_distance([x1,y1], line1_sorted[len2//2]) < get_distance([x2,y2], line1_sorted[len2//2]):
                    xr, yr = x1, y1
                else: xr, yr = x2, y2

                if get_distance([xr,yr], line1_sorted[0]) < get_distance([xr,yr], line1_sorted[len1-1]):
                    x3, y3 = line1_sorted[len1-1][0], line1_sorted[len1-1][1] 
                else: x3, y3 = line1_sorted[0][0], line1_sorted[0][1] 

            if get_distance([x1,y1], [x3,y3]) < get_distance([x2,y2], [x3,y3]):
                x4 , y4 = [x2-x1+x3,y2-y1+y3]
            else: x4 , y4 = [x1-x2+x3,y1-y2+y3]
            
            ##################### Get Centroid ######################

            xlist = np.array([x1,x2,x3,x4])
            ylist = np.array([y1,y2,y3,y4])
            print(xlist)
            print(ylist)
            center = [(x1+x2+x3+x4)/4,(y1+y2+y3+y4)/4]

            print(line2dy)
            print(get_angle([1,line2dy]))
            print(get_angle([1,line1dy]))
            print(360-abs(get_angle([1,line1dy])-get_angle([1,line2dy])))
            if(0.8<w<2.8 and 1.2<l<5.1 and 1.2<h<2.9): 
                if 55<360-abs(get_angle([1,line1dy])-get_angle([1,line2dy]))<140:
                    res = np.append(res, [[center[0],center[1], yaw, w, l, h]], axis = 0)

                    plt.plot(points_x, points_y, 'g*')
                    plt.plot(line1_inliers[:,0],line1_inliers[:,1], 'o')
                    plt.plot(line2_inliers[:,0],line2_inliers[:,1], 'ro')
                    plt.scatter(center[0],center[1],color ='green')
                    plt.scatter(xlist,ylist,color ='black')
                    plt.show()




            #points1_for_plt_x = line1[:,0]
            #points1_for_plt_y = line1[:,1]

            #points2_for_plt_x = line2[:,0]
            #points2_for_plt_y = line2[:,1]

            #input("Press Enter to continue...")

            #yaw_angle = math.atan2(-line1_a/line1_b, 1) * 180/math.pi
            #print("clusters yaw angle: ", yaw_angle) 
            
            



            
            

            temp_pcd = o3d.geometry.PointCloud()
            temp_pcd.points = o3d.utility.Vector3dVector(clusterCloud)

            if i%3 == 0:
                temp_pcd.paint_uniform_color([1,0,0])
            elif i%3 == 1:
                temp_pcd.paint_uniform_color([0,1,0])
            else:
                temp_pcd.paint_uniform_color([0,0,1])



            
            #vis.add_geometry(temp_pcd)
            #vis.run()
            
            ############ after convex hull , if not a car -> continue (next loop)
            

            

            
            '''# For Painting if it is a car
            if i%3 == 0:
                clusterCloud_pcd.paint_uniform_color([1,0,0])
            elif i%3 == 1:
                clusterCloud_pcd.paint_uniform_color([0,1,0])
            else:
                clusterCloud_pcd.paint_uniform_color([0,0,1])

            # Visualization
            vis.add_geometry(clusterCloud_pcd)
            vis.run()'''
            
            

    #print(car_count)
    num += 1
    #print (num)
    

    # if want to pause at each frame 
    input("Press Enter to continue...")

#     vis.clear_geometries()
    
        
        
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
