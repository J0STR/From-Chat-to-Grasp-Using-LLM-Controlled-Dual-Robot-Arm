from myLibs import *
import numpy as np
import time
from myLibs.ufactory.xarm_class import xArm7
from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
import math

def dual_xarm7_control_loop(stop_runtime: EventClass,
                                robo_ip: str,
                                request_robot_reset_gui: EventClass,
                                request_robot_reset: EventClass,
                                request_positioning_robot: Synchronized,
                                request_positioning_gripper: Synchronized,
                                current_state: SynchronizedArray,
                                goal_state: SynchronizedArray,
                                status: Synchronized,
                                z_min: int):
    """To control a single xArm7 in a dual setup

    Args:
        stop_runtime (EventClass): loop variable
        robo_ip (str): IP of the robot
        request_robot_reset (EventClass): For resetting the robot with the GUI
        current_state (SynchronizedArray[float]): current robot state
        goal_state (SynchronizedArray[float]): goal position
        status (Synchronized[bool]): error status
    """
    myArm = xArm7(robo_ip)
    myArm.start_up()
    myArm.servo_mode()
    # init shared variables
    if not myArm.is_error():    
        position = myArm.get_states()
        gripper_state = myArm.get_gripper_pos()
        robo_state = np.hstack((position,gripper_state))    
        current_state.get_obj()[:] = robo_state
    # limits
    x_max = 680
    x_min = 180
    y_max = 400
    y_min = -400
    z_max = 800
    
    # parameters
    dt = 0.02
    v_xyz = 100 # mm/s
    e_xyz = 0.05
    v_rot = 10 # mm/s
    e_rot = 0.8
    # reset var -> necessary to choose right mode
    reset = False
    # control loop
    while not stop_runtime.is_set():
        # track time
        start_time = time.perf_counter()
        # get current state
        if not myArm.is_error():
            position = myArm.get_states()
            gripper_state = myArm.get_gripper_pos()
            robo_state = np.hstack((position,gripper_state))    
            current_state.get_obj()[:] = robo_state
            myArm.is_gripper_moving(start_time)

        # error check
        if myArm.is_error():
            status.value = myArm.get_arm_err()
            reset = True
            myArm.manual_mode()
            continue
        else:
            status.value = myArm.get_arm_err()
        # reset check
        if not request_robot_reset_gui.is_set() and reset:
            reset = False
            myArm.servo_mode()
        elif request_robot_reset_gui.is_set() and not reset:
            reset = True
            myArm.manual_mode()
            continue
        else:
            pass
        
        torque_state = np.array(myArm.arm.joints_torque)
        
        if request_robot_reset.is_set():
            myArm.reset()
            request_robot_reset.clear()
            myArm.servo_mode()
            continue
        
        # robot positioning
        if request_positioning_robot.value or torque_state[3]<8:
            goal = goal_state.get_obj()[:6]
            goal = np.array(goal)
            # floor
            # check collision            
            if (torque_state[3]<8 
                and myArm.position[2]<300
                and abs(goal[4])<10):
                goal[2]= myArm.position[2]+0.5
                goal_state.get_obj()[2]=goal[2]
                print('ERROR controller: Xarm Torque to high')
            # limits
            goal[0]=max(x_min, min(goal[0], x_max))
            goal[1]=max(y_min, min(goal[1], y_max))
            goal[2]=max(z_min, min(goal[2], z_max))
            # check collision            
            # set to robot
            # implement loop here:
            # -----------------------------------------------------------------------
            # xyz controller
            # check diff of goal and current state
            goal_xyz = goal[:3]
            current_xyz = myArm.position[:3]
            diff_xyz = goal_xyz - current_xyz
            pos_reached_array = diff_xyz**2 <= e_xyz**2
            positioning_done = np.all(pos_reached_array)
            # check if positioning is done
            step_xyz = np.array([0,0,0],dtype=float)
            if positioning_done:
                step_xyz = np.array([0,0,0],dtype=float)
            else:
                # make control loop step
                step_xyz = np.clip(diff_xyz,-v_xyz*dt,v_xyz*dt)
            # -----------------------------------------------------------------------
            # rotation controller
            # check diff of goal and current state
            goal_rot = goal[3:]
            current_rot = myArm.position[3:]
            diff_rot = goal_rot - current_rot

            rot_reached_array = abs(diff_rot) <= e_rot
            element_needs_step = abs(diff_rot) > e_rot

            if abs(abs(goal_rot[0])-abs(current_rot[0]))<1:
                rot_reached_array[0]=True
            if abs(abs(goal_rot[1])-abs(current_rot[1]))<1:
                rot_reached_array[1]=True

            # check roll first
            step_rot = np.array([0,0,0],dtype=float)

            
            
            if not rot_reached_array[0]:
                if abs(current_rot[0])<179.5:
                    if abs(diff_rot[0])<5:
                        v_rot = 2
                    else:
                        v_rot = 15
                    step_rot[0] = np.clip(diff_rot[0],-v_rot*dt,v_rot*dt)
                else:
                    step_rot[0]=diff_rot[0]
                step_rot[0]= math.copysign(1, current_rot[0])*abs(step_rot[0])
                step_rot[0] = element_needs_step[0] * step_rot[0]
            else:
                step_rot[0] = 0
            # check pitch only if roll is good
            if (not rot_reached_array[1]):
                if abs(diff_rot[1])<5:
                        v_rot = 2
                else:
                        v_rot = 15
                step_pitch = np.clip(diff_rot[1],-v_rot*dt,v_rot*dt)
                step_pitch = element_needs_step[1] * step_pitch
                step_rot[1] = float(step_pitch)
            else:
                step_rot[1] = 0
            # check yaw only if roll,pitch is good
            if (not rot_reached_array[2]):
                if abs(diff_rot[2])<5:
                        v_rot = 2
                else:
                        v_rot = 15
                step_rot[2] = np.clip(diff_rot[2],-v_rot*dt,v_rot*dt)
                step_rot[2] = element_needs_step[2] * step_rot[2]
            else:
                step_rot[2] = 0

            rot_done = np.all(rot_reached_array)            
            # check if positioning is done
            if rot_done and positioning_done:
                request_positioning_robot.value = False
            else:
                step = np.hstack((step_xyz,step_rot))
                myArm.set_position_relative(step)
            # -----------------------------------------------------------------------
        else:
            pass
        
        # gripper positioning
        if request_positioning_gripper.value:
            goal = goal_state.get_obj()[-1]
            myArm.set_gripper_pos_con(goal)
            if myArm.gripper_moving:
                pass
            else:         
                request_positioning_gripper.value = False
            # -----------------------------------------------------------------------
        else:
            myArm.gripper_timer = start_time
        
        end_time = time.perf_counter()
        if end_time-start_time < dt:
            time.sleep(dt-(end_time-start_time))       

    myArm.reset()
    myArm.destroy()