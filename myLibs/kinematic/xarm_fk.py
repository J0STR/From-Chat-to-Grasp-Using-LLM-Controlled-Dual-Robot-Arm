import sympy as sp
import numpy as np
from myLibs.translation_rotation.matrices import *

def calculate_pose_matrix(joints):
    j_1 = joints[0]
    j_2 = joints[1]
    j_3 = joints[2]
    j_4 = joints[3]
    j_5 = joints[4]
    j_6 = joints[5]
    j_7 = joints[6]

    # parameter z
    d1 = 267
    d3 = 293
    d5 = 342.5
    d7 = 97
    # parameter x
    a4 = 52.5
    a5 = 77.5
    a7 = 76
    # model
    pose_matrix =  (trans_z(d1) @ rot_z(j_1) 
                    @ rot_x(-np.pi/2) @ rot_z(j_2) 
                    @ rot_x(np.pi/2) @ trans_z(d3) @ rot_z(j_3) 
                    @ trans_x(a4) @  rot_x(np.pi/2) @ rot_z(j_4)
                    @ trans_x(a5) @ rot_x(np.pi/2) @ trans_z(d5) @ rot_z(j_5) 
                    @ rot_x(np.pi/2) @ rot_z(j_6) 
                    @ trans_x(a7) @ rot_x(-np.pi/2) @ trans_z(d7) @ rot_z(j_7) @ trans_z(172) )
    
    return pose_matrix

def rotation_matrix_to_6d(Matrix):
    P = np.array(Matrix[:, :]).astype(float)
    x = P[0,3]/1000
    y = P[1,3]/1000
    z = P[2,3]/1000
    print(x)
    R = np.array(Matrix[:3, :3]).astype(float)
    roll = 0
    pitch = 0
    yaw = 0
    # Check for gimbal lock singularity
    if np.isclose(R[2, 0], -1.0): # Pitch is +90 degrees
        pitch = np.pi / 2.0
        yaw = np.arctan2(R[0, 1], R[0, 2])
        roll = 0.0    
    elif np.isclose(R[2, 0], 1.0): # Pitch is -90 degrees
        pitch = -np.pi / 2.0
        yaw = np.arctan2(-R[0, 1], -R[0, 2])
        roll = 0.0       
    else:
        # General case
        pitch = np.arctan2(-R[2, 0], np.sqrt(R[0, 0]**2 + R[1, 0]**2))
        yaw = np.arctan2(R[1, 0], R[0, 0])
        roll = np.arctan2(R[2, 1], R[2, 2])
    
    pose = np.array([x, y, z, roll, pitch, yaw])
    return pose