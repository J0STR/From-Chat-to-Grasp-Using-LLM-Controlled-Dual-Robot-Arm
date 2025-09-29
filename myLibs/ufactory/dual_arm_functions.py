from myLibs.translation_rotation.matrices import *
from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
import multiprocessing

def transform_robo_to_coord_sys(pose_robot):
    pos_arm = np.array([pose_robot[0],pose_robot[1],pose_robot[2],1])
    Translation_to_coord_sys =  trans_x(1100) @ rot_z(np.pi)
    transformed_pos = Translation_to_coord_sys @ pos_arm
    final_pose = np.hstack((transformed_pos[:3],pose_robot[3:]))

    return final_pose

def transform_coord_sys_to_robo(pose_coordinate_sys):
    pos_arm = np.array([pose_coordinate_sys[0],pose_coordinate_sys[1],pose_coordinate_sys[2],1])
    Translation_to_coord_sys =  trans_z(0) @ trans_x(1100) @ rot_z(np.pi)
    transformed_pos = Translation_to_coord_sys @ pos_arm   
    final_pose = np.hstack((transformed_pos[:3],pose_coordinate_sys[3:]))

    return final_pose

def wait_moving(stop_runtime,moving_1: Synchronized, moving_2: Synchronized, input_text: multiprocessing.Queue)-> bool:
    while ((moving_1.value or moving_2.value) 
        and not stop_runtime.is_set()
        and input_text.empty()):
        # stay in this loop till robot is set
        pass
    if input_text.empty():
        interrupted_by_new_prompt = False
        return interrupted_by_new_prompt
    else:
        interrupted_by_new_prompt = True
        return interrupted_by_new_prompt
    
def wait_moving_simple(moving_1: Synchronized, moving_2: Synchronized):
    while moving_1.value or moving_2.value:
        # stay in this loop till robot is set
        pass