import cv2
from PIL import Image
import numpy as np
import math as m
from myLibs.control_models.gemini_helper_functions import SegmentationItem

from pykinect_azure import k4a_float3_t

BACKGROUND = (235,249,255)
LIGHT_BLUE = (164,212,233)
DARK_BLUE = (0,159,227)

LIGHT_BLUE_BGR = (233,212,164)
DARK_BLUE_BGR = (240,159,0)
GREEN_BRG = (0,255,0)

def convert_cv_2_pil(cv_image):
    rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(rgb_image)
    return im

def convert_cv_2_pil_resize(cv_image):
    rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(rgb_image)
    im.thumbnail([1024, 1024], Image.Resampling.LANCZOS)
    return im

def convert_pil_2_cv(pil_image):
    frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return frame

def draw_item_infos(frame: tuple, item:SegmentationItem):
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [item.mask_points], 255)
        rect = cv2.minAreaRect(item.mask_points)
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        cv2.drawContours(frame, [box], 0, GREEN_BRG, 5) 
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        font_color = GREEN_BRG
        font_thickness = 2
        (center_x, center_y), (width, height), angle = rect
        angle = adapt_angle_to_yaw(width, height, angle) 

        if item is None:
            return

        cv2.circle(frame, item.grasping_pos[0].astype(int), 10, (255,0,0), -1)
        cv2.circle(frame, item.grasping_pos[1].astype(int), 10, (255,0,0), -1)
        cv2.line(frame,item.grasping_pos[0].astype(int),item.grasping_pos[1].astype(int), (255,0,0),2 )

        if item.name is not None:
            text_origin = (int(center_x) + int(width/2) + 15 + int(m.sin(angle*m.pi/180)*height), int(center_y) - int(height/2))
            text = item.name
            cv2.putText(frame, text, text_origin, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        text_origin = (int(center_x) + int(width/2) +15 + int(m.sin(angle*m.pi/180)*height), int(center_y) - int(height/2)+40)
        text = f"x = {item.pose_6d[0]:.1f} mm"
        cv2.putText(frame, text, text_origin, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        text_origin = (int(center_x) + int(width/2) +15 + int(m.sin(angle*m.pi/180)*height), int(center_y) - int(height/2)+80)
        text = f"y = {item.pose_6d[1]:.1f} mm"
        cv2.putText(frame, text, text_origin, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        text_origin = (int(center_x) + int(width/2) +15 + int(m.sin(angle*m.pi/180)*height), int(center_y) - int(height/2)+120)
        text = f"z = {item.pose_6d[2]:.1f} mm"
        cv2.putText(frame, text, text_origin, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        text_origin = (int(center_x) + int(width/2) +15 + int(m.sin(angle*m.pi/180)*height), int(center_y) - int(height/2)+160)
        text = f"Angle: {angle:.1f}"
        cv2.putText(frame, text, text_origin, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        text_origin = (int(center_x) + int(width/2) +15 + int(m.sin(angle*m.pi/180)*height), int(center_y) - int(height/2)+200)
        text = f"Width in mm: {item.grasping_mm:.1f}"
        cv2.putText(frame, text, text_origin, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

def calculate_gripping_pos(x_center, y_center, width, height, angle):
     distance = width/2
     if width > height:
          distance = height/2
     else:
          distance = width/2
     print(f"height :{height}, width :{width}")
     print(distance)
     x1 = x_center + np.sin(angle*(np.pi/180))*(distance)
     x2 = x_center - np.sin(angle*(np.pi/180))*(distance)
     
     y1 = y_center + np.cos(angle*(np.pi/180))*(distance)
     y2 = y_center - np.cos(angle*(np.pi/180))*(distance)


     return np.array([[x1,y1],[x2,y2]])

def calculate_gripping_mm(left_gripper_pos: k4a_float3_t, right_gripper_pos: k4a_float3_t):
     x_l = left_gripper_pos.xyz.x
     y_l = left_gripper_pos.xyz.y

     x_r = right_gripper_pos.xyz.x
     y_r = right_gripper_pos.xyz.y

     x_diff = x_l - x_r
     y_diff = y_l - y_r

     width_mm = m.sqrt( x_diff**2 + y_diff**2 )
     return width_mm
     

def adapt_angle_to_yaw(width, height,angle):
        if width > height:
            angle = -angle            
            width, height = height, width
        else:
            angle =90-angle

        return angle