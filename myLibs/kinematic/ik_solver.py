import os
import sys
import pybullet as p
import pybullet_data as pd
import numpy as np
from myLibs.kinematic.xarm_sim import XArm7Sim
from myLibs.kinematic.xarm_fk import *
from myLibs.ufactory.dual_arm_functions import rotation_direction, goal_milli_to_meter_and_def_to_rad

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))


class IK_Solver:
    def __init__(self):
        self.p = p.connect(p.DIRECT)
        p.setAdditionalSearchPath(pd.getDataPath())
        p.setGravity(0,0,-9.8)
        self.xarm_model = XArm7Sim(p,[0,0,0])
        self.trajectory: np.ndarray
        self.nbr_trajectory_steps: int = 0
        self.trajectory_step: int = 0
        self.step_direction: int = 1

    def calculate_IK(self, goal: np.ndarray):
        joints = self.xarm_model.calculate_joints(goal)

        return joints
    
    def calculate_trajectory(self, goal:np.ndarray, current_pos:np.ndarray, v_xyz: float,v_rot: float,dt: float):
        diff_xyz = goal[:3] - current_pos[:3]
        diff_rot = np.abs(goal[3:]) - np.abs(current_pos[3:])

        time_steps_xyz = np.ceil((np.abs(diff_xyz)/(v_xyz*dt)).astype(int))
        time_steps_rot = np.ceil((np.abs(diff_rot)/(v_rot*dt)).astype(int))
        time_steps = np.hstack((time_steps_xyz,time_steps_rot))
        nbr_time_steps = np.max(time_steps)

        trajectory = np.zeros((nbr_time_steps+1, 6), dtype=np.float32)
        trajectory[0] = np.array(current_pos)
        for i in range(0,nbr_time_steps+1):
            previous_point = trajectory[i,:] # first coloumn
            next_point_xyz = goal[:3] - previous_point[:3]
            next_point_rot = np.abs(goal[3:]) - np.abs(previous_point[3:])
            next_point_rot[2] = goal[-1] - previous_point[-1] # yaw is different
            rot_dir = rotation_direction(previous_point[3:])
            diff_xyz = next_point_xyz
            diff_rot = next_point_rot*rot_dir
            step_xyz = np.clip(diff_xyz,-v_xyz*dt,v_xyz*dt)
            step_rot = np.clip(diff_rot,-v_rot*dt,v_rot*dt)
            step = np.hstack((step_xyz,step_rot))
            next_point = previous_point + step
            if i == nbr_time_steps:
                break
            trajectory[i+1] = next_point

        self.nbr_trajectory_steps = nbr_time_steps
        self.trajectory = trajectory
        self.trajectory_step = 1
        self.step_direction = 1

        return nbr_time_steps, trajectory
    
    def calculate_IK_trajectory_step(self):
        success = True
        self.trajectory_step += self.step_direction

        if ((self.trajectory_step > self.nbr_trajectory_steps)
            or (self.trajectory_step<0)):
            # set to last element
            
            self.trajectory_step = self.nbr_trajectory_steps
            success = False
            return success, None        
        
        new_pos = self.trajectory[self.trajectory_step]        
        new_pos_transformed = goal_milli_to_meter_and_def_to_rad(new_pos)
        joints = self.calculate_IK(new_pos_transformed)
        
        return success, joints
    
    def destroy(self):
        p.disconnect(physicsClientId = self.p)
