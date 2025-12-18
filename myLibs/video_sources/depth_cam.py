import cv2
from myLibs.azure.azure_functions import Azure, transform_cam_to_robo_coord
import time
import numpy as np
from multiprocessing.synchronize import Event as EventClass


from .video_functions import draw_item_infos, calculate_gripping_pos, calculate_gripping_mm, adapt_angle_to_yaw
from myLibs.control_models.gemini_helper_functions import SegmentationItem

def depthcam_and_object_extraction_loop(stop_runtime: EventClass,
                   request_depth_pose: EventClass,
                   request_rect_reset: EventClass,
                   shared_data):
    device = Azure()
    fps = 50
    dt = 1/fps
    length_gripper = 0
    item: SegmentationItem | None = None

    while not stop_runtime.is_set():
        start_time = time.time()
        device.recieve_frame()
        sucess_read, frame = device.get_color_image()
        if not sucess_read:
            continue

        shared_data.frame = frame[:,:,:3]
        if request_depth_pose.is_set():
            item = shared_data.items             
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [item.mask_points], 255)
            y_coords, x_coords = np.where(mask == 255)
            pixel_coordinates = np.vstack((x_coords,y_coords)).T
            # create rectangle
            rect = cv2.minAreaRect(item.mask_points)
            (center_x, center_y), (width, height), angle = rect
            point = np.array([center_x,center_y],dtype=int)
            # calculate gripper angle
            yaw= adapt_angle_to_yaw(width, height, angle) # is in degree
            item.grasping_pos = calculate_gripping_pos(center_x,center_y,width,height,yaw)
            print(item.grasping_pos)       
            #calculate 3d pose
            succes_transform, pose3d = device.point_averaged_to_3d(point,pixel_coordinates)
            # calculate left and right gripper pos
            succes_transform_1, left_gripper = device.point_to_3d(item.grasping_pos[0].astype(int))
            succes_transform_2, right_gripper = device.point_to_3d(item.grasping_pos[1].astype(int))
            item.grasping_mm = calculate_gripping_mm(left_gripper, right_gripper)

            if succes_transform:    
                pos_object_arm_coord = transform_cam_to_robo_coord(pose3d,length_gripper)
                item.pose_6d = np.hstack((pos_object_arm_coord[:3],np.array([-179, 0]),yaw))
                shared_data.items = item
                request_depth_pose.clear()

        # if request_rect_reset.is_set():
        #     item = None
        #     request_rect_reset.clear()

        if item is not None:
            draw_item_infos(frame,item)
               
        shared_data.gui_frame = frame
        
        time_diff =time.time()-start_time
        if time_diff < dt:
            time.sleep(dt-(time_diff))
        
    stop_runtime.set()
    device.destroy()