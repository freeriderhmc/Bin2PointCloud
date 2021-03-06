import sys
import os
import numpy as np
import open3d as o3d
import time
import math
import operator
from matplotlib import pyplot as plt
import matplotlib.style as mplstyle

import loadData
import sortCar_yimju as socar
# from TrackingModule_WJ import track
from TrackingModule_WJ2 import track
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()

import pandas as pd
#import cv2

def save_to_csv(index, start, duration, state, framenum, path_csv):
    datalist = np.full((start,5),np.nan)
    datalist = np.append(datalist, state, axis = 0)
    datalist = np.append(datalist, np.full((framenum-start-duration+1, 5), np.nan), axis = 0)
    pd.DataFrame(datalist).to_csv(path_csv + '{}.csv'.format(index))

import numpy as np

# scailing
def minmaxScailing(datalist, xmean, xstd, ymean, ystd, vmean, vstd):
    mean_array = np.array([xmean, ymean, vmean, 0, 0])
    std_array = np.array([xstd, ystd, vstd, 1, 1])
    for i in range(len(datalist)):
        datalist[i] = (datalist[i]-mean_array)/std_array
    return np.array(datalist)

# Set Track list
Track_list = []
Track_list_valid = []
frame_num = 0

mplstyle.use('fast')
plt.ion()
plt.figure(figsize=(10, 70))

path = "/media/jinyoung/Samsung_T5/Lyft_test/42/"
path_lidar = path + "lidar/"
path_csv = path + "csvdata/"
#path_image = path + "images/"

file_list = loadData.load_data(path_lidar)
#image_list = loadData.load_data(path_image)

#cv2.namedWindow('Show Image')

with tf.Session() as sess:
    saver = tf.train.import_meta_graph('./model/model/lr0.001_batch128_cnt12_span5_hidden64_.meta')
    saver.restore(sess, tf.train.latest_checkpoint('./model/model'))
    graph = tf.get_default_graph()

    for files in file_list:
        starttime = time.time()
        #clusterClass_list = [] 
        measured_centroid = np.empty([0,3])
        measured_box = np.empty([0,4])
        cluster_id = []
        processed = []
        
        dt = 0.2


        # img = cv2.imread(path_image + image_list[frame_num], cv2.IMREAD_COLOR)


        # cv2.imshow("Show Image", img)
        # cv2.waitKey(1)

        data = np.fromfile(path_lidar+files,dtype = np.float32)
        data = data.reshape(-1,5)
        data = data[:,0:3]
        data = (np.array([[math.cos(177*math.pi/180),-math.sin(177*math.pi/180),0], [math.sin(177*math.pi/180),math.cos(177*math.pi/180),0], [0,0,1]]) @ data.T).T

        data = data[(data[:,0] <= 40)]
        data = data[(data[:,0] >= -30)]
        data = data[(data[:,1] <= 10)]
        data = data[(data[:,1] >= -10)]

        data_plot = (np.array([ [0,-1,0], [1,0,0], [0,0,1]]) @ data.T).T    
        plt.plot(data_plot[:,0], data_plot[:,1],'ko', markersize = 0.3)
        plt.xlim(-10,10)
        plt.ylim(-10,40)
        plt.text(0, 20, '{}-th frame'.format(frame_num))
        plt.text(0,0,'EGO')

        data = data[((data[:, 2] >= -1.3))] # -1.56
        data = data[((data[:, 2] <= 1.5))] # -1.56

        cloud = o3d.geometry.PointCloud()
        cloud.points = o3d.utility.Vector3dVector(data)

        cloud_downsample = cloud.voxel_down_sample(voxel_size=0.05)

        # cloud_downsample_plot = np.asarray(cloud_downsample.points)
        # cloud_downsample_plot = (np.array([ [0,-1,0], [1,0,0], [0,0,1]]) @ cloud_downsample_plot.T).T    
        # plt.plot(cloud_downsample_plot[:,0], cloud_downsample_plot[:,1],'ko', markersize = 0.4)
        # plt.xlim(-40,40)
        # plt.ylim(-20,60)
        # plt.text(-40, 20, '{}-th frame'.format(frame_num))

        clustertime = time.time()
        labels = np.asanyarray(cloud_downsample.cluster_dbscan(0.7,3))
        #print("Clustering time: ", time.time() - clustertime)

        for i in range(np.max(labels)+1):

            DBSCAN_Result = cloud_downsample.select_by_index(np.where(labels == i)[0])
            clusterCloud = np.asarray(DBSCAN_Result.points)
            
            if len(clusterCloud) <= 10: 
                continue
            
            z_max=z_min=x_max=x_min=y_max=y_min=0
            
            z_max = np.max(clusterCloud[:,2])
            z_min = np.min(clusterCloud[:,2])

            center = DBSCAN_Result.get_center()

            clusterCloud_plot = (np.array([[0,-1,0], [1,0,0], [0,0,1]]) @ clusterCloud.T).T 
            plt.plot(clusterCloud_plot[:,0], clusterCloud_plot[:,1],'bo', markersize = 0.4)

            # center_plot = (np.array([[0,-1,0], [1,0,0], [0,0,1]]) @ center.T).T
            # plt.plot(center_plot[0], center_plot[1],'ro', markersize = 0.8)

            # Get 4 Box Points
            box = DBSCAN_Result.get_oriented_bounding_box()
            box_center = box.center
            box_center_plot = (np.array([[0,-1,0], [1,0,0], [0,0,1]]) @ box_center.T).T
            #plt.plot(box_center_plot[0], box_center_plot[1],'go', markersize = 1.5)
            box_center = box_center[:2]

            box_points = box.get_box_points()
            box_points_numpy = np.asarray(box_points)
            #print(box_points_numpy)
            box_points_numpy_plot = (np.array([[0,-1,0], [1,0,0], [0,0,1]]) @ box_points_numpy.T).T 
            #plt.plot(box_points_numpy_plot[:,0], box_points_numpy_plot[:,1], 'go', markersize = 1.5)
            # for i in range(0,8):
            #     plt.text(box_points_numpy_plot[i,0], box_points_numpy_plot[i,1], '{}'.format(i))
            box = np.array([[(box_points_numpy[0,0]+box_points_numpy[3,0])/2, (box_points_numpy[0,1]+box_points_numpy[3,1])/2],
                            [(box_points_numpy[2,0]+box_points_numpy[5,0])/2, (box_points_numpy[2,1]+box_points_numpy[5,1])/2],
                            [(box_points_numpy[4,0]+box_points_numpy[7,0])/2, (box_points_numpy[4,1]+box_points_numpy[7,1])/2],
                            [(box_points_numpy[1,0]+box_points_numpy[6,0])/2, (box_points_numpy[1,1]+box_points_numpy[6,1])/2]])
            box_plot = (np.array([[0,-1], [1,0,]]) @ box.T).T
            #plt.plot(box_plot[:,0], box_plot[:,1], 'ro', markersize = 3)

            # Sort box
            box = socar.sortline_angle(box, box_center)
            
            # Get length of 4 line
            width = 100
            length = 0
            yaw = 0
            yaw_norm = 0
            # width : min / length : max
            for i in range(0,len(box)-1):
                tmp = math.sqrt((box[i,0] - box[i+1,0])**2 + (box[i,1] - box[i+1,1])**2)

                if width > tmp:
                    width = tmp
                    yaw_norm = math.atan( (box[i,1] - box[i+1,1]) / (box[i,0] - box[i+1,0]) )
                if length < tmp:
                    length = tmp
                    yaw = math.atan( (box[i,1] - box[i+1,1]) / (box[i,0] - box[i+1,0]) )

            templist_res = [box_center[0], box_center[1], yaw]
            templist_box = [width, length, z_max - z_min,box]
            
            # Sort Car by length and angle conditions
            # Save measured centroid, box, id, and processed
            if (width >= 1 or length >= 1) and width<=4 and length <= 8:
                if math.fabs(yaw - yaw_norm) >= math.pi/3:
                    # cluster = clusterClass(np.array(templist_res), np.array(templist_box), i, 1)
                    # clusterClass_list.append(cluster)
                    measured_centroid = np.append(measured_centroid, [templist_res], axis = 0)
                    measured_box = np.append(measured_box, [templist_box], axis = 0)
                    cluster_id.append(i)
                    #plt.plot(box_plot[:,0], box_plot[:,1], 'ro', markersize = 3)

                
                    # u, v = math.cos(yaw), math.sin(yaw)
                    # [u,v] = (np.array([ [0,-1], [1,0]]) @ np.asarray([u,v]).T).T 
                    # plt.quiver(box_center_plot[0], box_center_plot[1], u, v, scale= 3, scale_units = 'inches', color = 'red')

                # else:
                #     cluster = clusterClass(np.array(templist_res), np.array(templist_box), i, 0)
                #     clusterClass_list.append(cluster)

        processed = np.zeros(len(cluster_id))

        trackingtime = time.time()
        ########### Track Update ############
        if Track_list:
            for i in range(0,len(Track_list)):
                if Track_list[i].dead_flag == 1:
                    continue
                Track_list[i].unscented_kalman_filter(measured_centroid, measured_box, cluster_id, processed, dt)

        ########### Create Track ###########
        
        for i in range(0, len(measured_centroid)):
            if processed[i] == 1:
                continue
            
            # z_meas[i] that are not used : Create new track
            #clusterClass_list[i].processed = 1
            Track = track(measured_centroid[i], measured_box[i], frame_num, cluster_id[i])
            Track_list.append(Track)
        
        ########## Track Management ########
        if Track_list:
            try:
                for i in range(0, len(Track_list)):

                    # Dismiss DeadTrack
                    if Track_list[i].dead_flag == 1:
                        continue

                    # Activate Track
                    if Track_list[i].Activated == 0 and Track_list[i].Age >= 5:
                        Track_list[i].Activated = 1
                    
                    # deActivate Track
                    if Track_list[i].DelCnt >= 7:
                        Track_list[i].dead_flag = 1
                    
                    '''# Delete Track
                    if Track_list[i].DelCnt >= 20:
                        #del Track_list[i]
                        Track_list[i].dead_flag = 1'''
                    
                    # Initialize Tracks' processed check
                    #Track_list[i].processed = 0
            
            except:
                print("Track was deleted")
            
        #print("Tracking time: ", time.time() - trackingtime)
        
        # cloud_downsample_plot = (np.array([ [0,-1,0], [1,0,0], [0,0,1]]) @ cloud_downsample.T).T
        # # Plot all points
        # plt.xlim(-40,40)
        # plt.ylim(-20,60)
        # plt.plot(cloud_downsample_plot[:,0], cloud_downsample_plot[:,1],'ko', markersize = 0.4)
        # plt.text(-40, 20, '{}-th frame'.format(frame_num))
        
        for i in range(0, len(Track_list)):

            #start_dl_time = time.time()
            length_his_state = len(Track_list[i].history_state)
            if(Track_list[i].Activated==1 and Track_list[i].dead_flag==0 and length_his_state>=12):
                temp_state = Track_list[i].history_state[length_his_state-12:]
                final_state = minmaxScailing(temp_state.tolist(), 16.908, 12.341, 2.585,3.848, 0.164,6.698)
                x = graph.get_tensor_by_name('x_:0')
                feed_dict ={x:final_state.reshape(-1, 12,5)} 
                op_to_restore = graph.get_tensor_by_name('pred:0')
                car_state = np.argmax(sess.run(op_to_restore,feed_dict),axis=1)

                if(car_state ==[1]):
                    Track_list[i].motionPredict=1
                elif(car_state==[2]):
                    Track_list[i].motionPredict=2
                #print('deep learning time : ', time.time()-start_dl_time)

            if Track_list[i].Activated == 1 and Track_list[i].processed == 1:
                temp = cloud_downsample.select_by_index(np.where(labels == Track_list[i].ClusterID)[0])
                temp = np.asarray(temp.points)
                Track_list[i].processed = 0

                if len(temp) == 0:
                    continue

                plt.xlim(-10,10)
                plt.ylim(-10,40)
                temp = (np.array([ [0,-1,0], [1,0,0], [0,0,1]]) @ temp.T).T
                center = np.array([Track_list[i].state[0], Track_list[i].state[1]])
                
                w_box = Track_list[i].width_max
                l_box = Track_list[i].length_max
                yaw_box = Track_list[i].yaw_angle
                # if(yaw_box>=0):
                #     rec_box_1 = np.array([center[0] + math.cos(yaw_box) * l_box / 2 - math.sin(yaw_box) * w_box / 2
                #                         ,center[1] + math.sin(yaw_box) * l_box / 2 + math.cos(yaw_box) * w_box / 2])
                #     rec_box_2 = np.array([center[0] - math.cos(yaw_box) * l_box / 2 - math.sin(yaw_box) * w_box / 2
                #                         ,center[1] - math.sin(yaw_box) * l_box / 2 + math.cos(yaw_box) * w_box / 2])
                #     rec_box_3 = np.array([center[0] - math.cos(yaw_box) * l_box / 2 + math.sin(yaw_box) * w_box / 2
                #                         ,center[1] - math.sin(yaw_box) * l_box / 2 - math.cos(yaw_box) * w_box / 2])
                #     rec_box_4 = np.array([center[0] + math.cos(yaw_box) * l_box / 2 + math.sin(yaw_box) * w_box / 2
                #                         ,center[1] + math.sin(yaw_box) * l_box / 2 - math.cos(yaw_box) * w_box / 2])

                # elif(yaw_box<0):
                #     rec_box_1 = np.array([center[0] - math.cos(yaw_box) * l_box / 2 - math.sin(yaw_box) * w_box / 2
                #                         ,center[1] - math.sin(yaw_box) * l_box / 2 + math.cos(yaw_box) * w_box / 2])
                #     rec_box_2 = np.array([center[0] - math.cos(yaw_box) * l_box / 2 + math.sin(yaw_box) * w_box / 2
                #                         ,center[1] - math.sin(yaw_box) * l_box / 2 - math.cos(yaw_box) * w_box / 2])
                #     rec_box_3 = np.array([center[0] + math.cos(yaw_box) * l_box / 2 + math.sin(yaw_box) * w_box / 2
                #                         ,center[1] + math.sin(yaw_box) * l_box / 2 - math.cos(yaw_box) * w_box / 2])
                #     rec_box_4 = np.array([center[0] + math.cos(yaw_box) * l_box / 2 - math.sin(yaw_box) * w_box / 2
                #                         ,center[1] + math.sin(yaw_box) * l_box / 2 + math.cos(yaw_box) * w_box / 2])
                rec_box_1= Track_list[i].points[0]
                rec_box_2= Track_list[i].points[1]
                rec_box_3= Track_list[i].points[2]
                rec_box_4= Track_list[i].points[3]
                
                rec_box_1 = (np.array([[0,-1], [1,0]]) @ rec_box_1.T).T
                rec_box_2 = (np.array([[0,-1], [1,0]]) @ rec_box_2.T).T
                rec_box_3 = (np.array([[0,-1], [1,0]]) @ rec_box_3.T).T
                rec_box_4 = (np.array([[0,-1], [1,0]]) @ rec_box_4.T).T

                            
                center = (np.array([[0,-1], [1,0]]) @ center.T).T
                if(abs(Track_list[i].state[2])>0.5):
                    if(Track_list[i].motionPredict == 0):
                        plt.plot((rec_box_1[0], rec_box_2[0], rec_box_3[0], rec_box_4[0], rec_box_1[0]), (rec_box_1[1], rec_box_2[1], rec_box_3[1], rec_box_4[1], rec_box_1[1]), 'g')
                        # plt.plot(center[0], center[1], 'go', markersize=20)
                    elif(Track_list[i].motionPredict==1):
                        plt.plot((rec_box_1[0], rec_box_2[0], rec_box_3[0], rec_box_4[0], rec_box_1[0]), (rec_box_1[1], rec_box_2[1], rec_box_3[1], rec_box_4[1], rec_box_1[1]), 'r')
                        # plt.plot(center[0], center[1], 'ro', markersize=20)
                    elif(Track_list[i].motionPredict ==2):
                        plt.plot((rec_box_1[0], rec_box_2[0], rec_box_3[0], rec_box_4[0], rec_box_1[0]), (rec_box_1[1], rec_box_2[1], rec_box_3[1], rec_box_4[1], rec_box_1[1]), 'c')
                        # plt.plot(center[0], center[1], 'co', markersize=20)
                    else:
                        plt.plot((rec_box_1[0], rec_box_2[0], rec_box_3[0], rec_box_4[0], rec_box_1[0]), (rec_box_1[1], rec_box_2[1], rec_box_3[1], rec_box_4[1], rec_box_1[1]), 'Y')
                
                # plt.plot(temp[:,0], temp[:,1], 'ro', markersize = 0.4)
                # plt.plot(center[0], center[1], 'go')
                plt.text(center[0], center[1], 'Track{}'.format(i+1))
                #u, v = math.cos(Track_list[i].state[3]), math.sin(Track_list[i].state[3])

                if Track_list[i].state[2] >= 1:
                    u, v = math.cos(Track_list[i].state[3]), math.sin(Track_list[i].state[3])
                    [u,v] = (np.array([ [0,-1], [1,0]]) @ np.asarray([u,v]).T).T 
                    plt.quiver(center[0], center[1], u, v, scale= 3, scale_units = 'inches', color = 'red')
                elif Track_list[i].state[2] < -1:
                    u, v = math.cos(Track_list[i].state[3] + math.pi), math.sin(Track_list[i].state[3] + math.pi)
                    [u,v] = (np.array([ [0,-1], [1,0]]) @ np.asarray([u,v]).T).T 
                    plt.quiver(center[0], center[1], u, v, scale= 3, scale_units = 'inches', color = 'red')
                
                #[u,v] = (np.array([ [0,-1], [1,0]]) @ np.asarray([u,v]).T).T 
                
                # Plot Track's trace
                #for j in range(0, len(Track_list[i].trace)):
                #    trace_for_plot
                #plt.plot(Track_list[i].trace_x[:], Track_list[i].trace_y[:], 'g')

            # Initialize Tracks' processed check
            
        #print("enumerate time: ", time.time() - starttime)
        
        plttime = time.time()
        plt.draw()
        plt.pause(0.001)
        plt.clf()
        #print("plot time: ", time.time() - plttime)
        # plot Ego Vehicle
        '''plt.text(0, 0, 'EgoCar')
        plt.plot(res[:,0], res[:,1], 'ro')
        for i in range(0, len(Track_list)):
            if Track_list[i].Activated == 1 and Track_list[i].dead_flag == 0:
                plt.plot(Track_list[i].state[0], Track_list[i].state[1], 'b*')
                plt.text(Track_list[i].state[0], Track_list[i].state[1], 'Track{}'.format(i+1))
                
                # Plot Track's trace
                #for j in range(0, len(Track_list[i].trace)):
                #    trace_for_plot
                #plt.plot(Track_list[i].trace_x[:], Track_list[i].trace_y[:], 'g')             
        plt.show()'''
        
        #for i in range(0, len(Track_list)):
        #    print("Track value: ".format(i), Track_list[i].state)

        #pre_time_stamp = time_stamp
        frame_num += 1    
        #input("Press Enter to continue...")
    '''
    for i in range(0, len(Track_list)):
        if Track_list[i].Activated == 1:
            Track_list_valid.append((Track_list[i], i+1))

    validtracklistnum =len(Track_list_valid)
    print("# of all track_list : ", len(Track_list))
    print("# of valid track_list : ", validtracklistnum)

    for i in range(validtracklistnum):
        index = Track_list_valid[i][1]
        start = Track_list_valid[i][0].Start
        duration = len(Track_list_valid[i][0].history_state)
        state = Track_list_valid[i][0].history_state
        framenum = frame_num
        save_to_csv(index, start, duration, state, framenum, path_csv)
        
    # reach to csv file
    # csv_file = pd.read_csv('{}.csv'.format(i), index_col=0) # set i~
    '''

        # '''for i in range(len(Track_list)):
        # print("Track_list {}-th all state".format(i+1))
        # print(Track_list[i].history_state)
        # plt.figure()
        # plt.plot(range(1,len(Track_list[i].history_state) + 1) , Track_list[i].history_state[:,0], label = 'x_point', color = 'b')
        # plt.plot(range(1,len(Track_list[i].history_state) + 1) , Track_list[i].history_state[:,1], label = 'y_point', color = 'g')
        # plt.plot(range(1,len(Track_list[i].history_state) + 1) , Track_list[i].history_state[:,2], label = 'velocity', color = 'r')
        # plt.plot(range(1,len(Track_list[i].history_state) + 1) , Track_list[i].history_state[:,3], label = 'yaw-angle', color = 'c')
        # plt.plot(range(1,len(Track_list[i].history_state) + 1) , Track_list[i].history_state[:,4], label = 'yaw_rate', color = 'm')
        # plt.plot(range(1,len(Track_list[i].history_state) + 1) , Track_list[i].history_box[:,0], label = 'width', color = 'y')
        # plt.plot(range(1,len(Track_list[i].history_state) + 1) , Track_list[i].history_box[:,1], label = 'length', color = 'k')
        # plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
        # plt.show()'''
