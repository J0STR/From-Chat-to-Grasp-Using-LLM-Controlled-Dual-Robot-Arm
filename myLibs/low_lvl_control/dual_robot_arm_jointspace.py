import numpy as np
import time
from myLibs.ufactory.xarm_class_joint_space import xArm7
from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
import math

def control_loop_jointspace(stop_runtime: EventClass,
                                robo_ip: str,
                                request_robot_reset_gui: EventClass,
                                request_robot_reset: EventClass,
                                request_positioning_robot: Synchronized,
                                request_positioning_gripper: Synchronized,
                                current_state: SynchronizedArray,
                                goal_state: SynchronizedArray,
                                status: Synchronized,
                                z_min: int,
                                gripper_g2: bool=False):
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
    position = 0
    if not myArm.is_error():    
        position = myArm.get_states()
        gripper_state = myArm.get_gripper_pos()
        robo_state = np.hstack((position,gripper_state))    
        current_state.get_obj()[:] = robo_state
    
    # parameters
    dt = 0.02
    v_xyz = 100 # mm/s
    v_rot = 30 # deg/s

    # torque check
    torque_timer = 0
    torque_min_time = 0.2
    torque_timer_set = False

    # limits
    x_max = 680
    x_min = 180
    y_max = 400
    y_min = -400
    z_max = 800
  
    # reset var -> necessary to choose right mode
    reset = False
    manual_set = False
    #
    goal_saved = position
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

        
        # reset check
        if request_robot_reset_gui.is_set() and not manual_set:
            myArm.manual_mode()
            manual_set = True
        elif not request_robot_reset_gui.is_set() and manual_set:
            myArm.servo_mode()
            request_positioning_gripper.value = False
            manual_set = False
        else:
            pass

        if request_robot_reset_gui.is_set():
            continue

        # error check
        if myArm.is_error():
            status.value = myArm.get_arm_err()
            reset = True
        else:
            status.value = myArm.get_arm_err()
        
        if reset:
            print('running start up')
            myArm.start_up()
            reset = False
            continue
        
        # Collision detection
        joints, effort = myArm.get_joints_radian()
        effort_numpy = np.array(effort)
        
        # reset check
        if request_robot_reset.is_set():
            myArm.reset()
            request_robot_reset.clear()
            myArm.servo_mode()
            continue

        # check if new goal
        target = goal_state.get_obj()[:6]
        target = np.array(target)
        target[0]=max(x_min, min(target[0], x_max))
        target[1]=max(y_min, min(target[1], y_max))
        target[2]=max(z_min, min(target[2], z_max))
        if not np.array_equal(target,goal_saved):
            goal_saved = target
            current_pos = myArm.get_states()
            myArm.IK_Solver.calculate_trajectory(target,
                                     current_pos,
                                     v_xyz,
                                     v_rot,
                                     dt)

        
        # robot positioning
        if request_positioning_robot.value or effort_numpy[3]<8:
                # -----------------------------------------               
                if (effort_numpy[3]<7 
                        and abs(target[2])<50):
                    
                    if not torque_timer_set:
                        torque_timer = time.perf_counter()
                        torque_timer_set = True
                        myArm.IK_Solver.step_direction = 0 # stop movement for now
                    else:
                        pass
                    
                    if time.perf_counter()-torque_timer > torque_min_time:
                        print('ERROR controller: Xarm Torque to high')             
                        myArm.IK_Solver.nbr_trajectory_steps = myArm.IK_Solver.trajectory_step 

                        if myArm.IK_Solver.step_direction >= 0:
                            myArm.IK_Solver.step_direction = -1       
                else:
                    myArm.IK_Solver.step_direction = 1
                    torque_timer = time.perf_counter()
                    torque_timer_set = False
                # -----------------------------------------
                # Calc step
                moving, joints = myArm.IK_Solver.calculate_IK_trajectory_step()
                if not moving:
                    request_positioning_robot.value = False
                # Set to Robot
                # ----------------------------------------- 
                if joints is not None:
                    myArm.set_joints_radian(joints)
                # ----------------------------------------- 
            
        
        # gripper positioning
        if request_positioning_gripper.value:
            goal = goal_state.get_obj()[-1]
            myArm.set_gripper_pos(goal)
            if myArm.gripper_moving:
                pass
            else:         
                request_positioning_gripper.value = False
            # -----------------------------------------------------------------------
        else:
            myArm.gripper_timer = start_time
        
        delta_time = time.perf_counter() - start_time
        if delta_time<dt:
            time.sleep(dt-delta_time)      

    myArm.reset()
    myArm.destroy()

def controller_gui_test(stop_runtime: EventClass,
             robo_ip,
             request_robot_reset: EventClass,
             current_state,
             status):
    
    myArm = xArm7(robo_ip)
    myArm.start_up()
    myArm.servo_mode()
    # init shared variables
    position = 0
    if not myArm.is_error():    
        position = myArm.get_states()
        gripper_state = myArm.get_gripper_pos()
        robo_state = np.hstack((position,gripper_state))    
        current_state.get_obj()[:] = robo_state
    
    # parameters
    dt = 0.02

    # reset var -> necessary to choose right mode
    reset = False
    manual_set = False
    #
    goal_saved = position
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
        else:
            status.value = myArm.get_arm_err()
        
        if reset:
            print('running start up')
            myArm.start_up()
            reset = False
            continue

        # reset check
        if request_robot_reset.is_set() and not manual_set:
            myArm.manual_mode()
            manual_set = True
        elif not request_robot_reset.is_set() and manual_set:
            myArm.servo_mode()
            manual_set = False
        else:
            pass

        delta_time = time.perf_counter() - start_time
        if delta_time<dt:
            time.sleep(dt-delta_time)

    myArm.reset()
    myArm.destroy()