from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
import multiprocessing

from myLibs.ufactory.dual_arm_functions import *
from .gemini_helper_functions import *
from myLibs.video_sources.video_functions import convert_cv_2_pil
from myLibs.history_saver.function import write_list_to_file

def handle_get_object_with_gemini(stop_runtime: EventClass,
                      input_text: multiprocessing.Queue,
                        function_call,
                        shared_data,  
                        content: list,
                        request_rect_reset: EventClass,
                        request_depth_pose: EventClass):

    request_rect_reset.set()
    shared_data.object_name = function_call.args['object_name']
    frame = shared_data.frame
    pil_img = convert_cv_2_pil(frame)
    item = get_structured_segmentation(pil_img, function_call.args['object_name'])
    if item is None:
        content.append(f"{function_call.args['object_name']} was not found in the image.")
        return
    
    shared_data.items = item
    request_depth_pose.set()
    while request_depth_pose.is_set() and not stop_runtime.is_set() and input_text.empty():
        pass
    complete_item: SegmentationItem = shared_data.items
    content.append(f"The pose/coordinates of the object {function_call.args['object_name']} is: {complete_item.pose_6d}")


def handle_set_robot_pos(stop_runtime: EventClass,
                        input_text: multiprocessing.Queue,
                        robot_id: int,
                        task: str,
                        desired_pos,
                        content: list,
                        goal_state_robo_1: SynchronizedArray,
                        goal_state_robo_2: SynchronizedArray,
                        request_positioning_robot_1: Synchronized,
                        request_positioning_robot_2: Synchronized):
    if task == 'place':
        desired_pos[2]=95
        content.append(f"Target z-coordinate changed to z=95 due to safety concerns. Consider placing done.")

    if robot_id ==1:
        goal_state_robo_1.get_obj()[:]=np.hstack((desired_pos,0))
        request_positioning_robot_1.value = True
    elif robot_id ==2:
        transformed_desired_pos = transform_coord_sys_to_robo(desired_pos)
        goal_state_robo_2.get_obj()[:]=np.hstack((transformed_desired_pos,0))
        request_positioning_robot_2.value = True

    interrupted = wait_moving(stop_runtime, request_positioning_robot_1,request_positioning_robot_2, input_text)
    if not interrupted:
        content.append(f"Position is set to the robot.")
    else:
        content.append(f"The function call was interrupted by a user intervention with the following prompt:")

def handle_open_gripper(stop_runtime: EventClass,
                        input_text: multiprocessing.Queue,
                        robot_id: int,
                        content: list,
                        goal_state_robo_1: SynchronizedArray,
                        goal_state_robo_2: SynchronizedArray,
                        request_positioning_gripper_1: Synchronized,
                        request_positioning_gripper_2: Synchronized):
    if robot_id ==1:
        goal_state_robo_1.get_obj()[-1]=840
        request_positioning_gripper_1.value = True
    elif robot_id ==2:
        goal_state_robo_2.get_obj()[-1]=840
        request_positioning_gripper_2.value = True
    interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2, input_text)
    if not interrupted:
        content.append(f"Gripper of robot {robot_id} opened.")

def handle_close_gripper(stop_runtime: EventClass,
                        input_text: multiprocessing.Queue,
                        robot_id: int,
                        content: list,
                        current_state_robo_1: SynchronizedArray,
                        current_state_robo_2: SynchronizedArray,  
                        goal_state_robo_1: SynchronizedArray,
                        goal_state_robo_2: SynchronizedArray,
                        request_positioning_gripper_1: Synchronized,
                        request_positioning_gripper_2: Synchronized):
    if robot_id ==1:
        goal_state_robo_1.get_obj()[-1]=5
        request_positioning_gripper_1.value = True
    elif robot_id ==2:
        goal_state_robo_2.get_obj()[-1]=5
        request_positioning_gripper_2.value = True
    interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2, input_text)
    if not interrupted:
        content.append(f"Gripper of robot {robot_id} closed.")
        if (robot_id == 1 and current_state_robo_1.get_obj()[-1]> 10) or (robot_id == 2 and current_state_robo_2.get_obj()[-1]> 10) :
            content.append(f"The grasp was succesfull.")
        else:
            content.append(f"The grasp failed.")
    else:
        content.append(f"The function call was interrupted by a user intervention with the following prompt:")

def handle_end_task(task,
                    shared_data,
                    request_robot_reset: EventClass,
                    request_rect_reset: EventClass,
                    goal_state_robo_1: SynchronizedArray,
                    goal_state_robo_2: SynchronizedArray,
                    history_saver: list):
    task = False
    request_robot_reset.set()
    request_rect_reset.set()
    goal_state_robo_1.get_obj()[:] =np.array([200,0, 300,-180, 0,0, 840])
    goal_state_robo_2.get_obj()[:] =np.array([200,0, 300,-180, 0,0, 840])
    print('--------------new task---------------------------')
    hist = shared_data.output_hist
    hist += '<b>---NEW TASK---</b> <br><br><br><br>'
    shared_data.output_hist = hist
    write_list_to_file(history_saver)
    history_saver = []
    return history_saver,task

def handle_hand_over(stop_runtime: EventClass,
                     input_text: multiprocessing.Queue,
                     content: list,
                     robot_master: int,
                     robot_slave: int,
                     current_state_robo_1: SynchronizedArray,
                     current_state_robo_2: SynchronizedArray,
                     goal_state_robo_1: SynchronizedArray,
                     goal_state_robo_2: SynchronizedArray,
                     request_positioning_robot_1: Synchronized,
                     request_positioning_robot_2: Synchronized,
                     request_positioning_gripper_1: Synchronized,
                     request_positioning_gripper_2: Synchronized):
    
    interrupted = False

    transfer_offset = 40
    transfer_x_pos  = 565

    reset_pose_first = np.array([350, 0, 500, -180, 0, 0])

    horizontal_pose_lower  = np.array([500, 0, 500, -180,-90,0])
    horizontal_pose_higher = np.array([500, 0, 500 + transfer_offset, -179,-89.5,0])

    transfer_pose  = np.array([transfer_x_pos, 0, 500, -180,-90,0])
    transfer_pose_higher = np.array([transfer_x_pos, 0, 500 + transfer_offset, -180,-90,0])

    correction_pose  = np.array([transfer_x_pos, 0, 500 - transfer_offset, -180,-90,0])

    if robot_master == 1 and robot_slave == 2 and not interrupted:
        goal_state_robo_1.get_obj()[:]=np.hstack((reset_pose_first,0))
        goal_state_robo_2.get_obj()[:]=np.hstack((reset_pose_first,840))
        request_positioning_robot_1.value = True
        request_positioning_robot_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_2,input_text)
        # Step 1: move gripper horizontal
        # robot 1
        hand_over_pos = horizontal_pose_lower
        goal_state_robo_1.get_obj()[:]=np.hstack((hand_over_pos,0))
        request_positioning_robot_1.value = True
        # robot 2
        hand_over_pos = horizontal_pose_higher
        goal_state_robo_2.get_obj()[:]=np.hstack((hand_over_pos,840))
        request_positioning_robot_2.value = True
        request_positioning_gripper_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_2,input_text)
        # ------------------------------------------------
        # Step 2: move robots near
        # step 2 robot 1
        hand_over_pos = transfer_pose
        goal_state_robo_1.get_obj()[:]=np.hstack((hand_over_pos,0))
        request_positioning_robot_1.value = True
        # step 2 robot 2
        hand_over_pos = transfer_pose_higher
        goal_state_robo_2.get_obj()[:]=np.hstack((hand_over_pos,840))
        request_positioning_robot_2.value = True
        request_positioning_gripper_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_2,input_text)
    elif robot_master == 2 and robot_slave == 1 and not interrupted:
        goal_state_robo_1.get_obj()[:]=np.hstack((reset_pose_first,840))
        goal_state_robo_2.get_obj()[:]=np.hstack((reset_pose_first,0))
        request_positioning_robot_1.value = True
        request_positioning_robot_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_2,input_text)
        # step 1 robot 1
        hand_over_pos = horizontal_pose_higher
        goal_state_robo_1.get_obj()[:]=np.hstack((hand_over_pos,840))
        request_positioning_robot_1.value = True
        request_positioning_gripper_1.value = True
        # step 1 robot 2
        hand_over_pos = horizontal_pose_lower
        goal_state_robo_2.get_obj()[:]=np.hstack((hand_over_pos,0))
        request_positioning_robot_2.value = True
        request_positioning_gripper_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_2,input_text)
        # step 2 robot 1
        hand_over_pos = transfer_pose_higher
        goal_state_robo_1.get_obj()[:]=np.hstack((hand_over_pos,840))
        request_positioning_robot_1.value = True
        request_positioning_gripper_1.value = True
        # step 2 robot 2
        hand_over_pos = transfer_pose
        goal_state_robo_2.get_obj()[:]=np.hstack((hand_over_pos,0))
        request_positioning_robot_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_2,input_text)


    # step 3 both robots
    if robot_master == 1 and robot_slave == 2 and not interrupted:
        # Transfer item: 
        # close slave gripper
        goal_state_robo_2.get_obj()[-1]=0
        request_positioning_gripper_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2,input_text)
        # open master gripper
        goal_state_robo_1.get_obj()[-1]=840
        request_positioning_gripper_1.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2,input_text)
        # Correct grasp pose:
        # move down master and close again
        goal_state_robo_1.get_obj()[:]=np.hstack((correction_pose,840))
        request_positioning_robot_1.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_2,input_text)
        goal_state_robo_1.get_obj()[-1]=0
        request_positioning_gripper_1.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2,input_text)
        # now move upper grip to middle pick position
        goal_state_robo_2.get_obj()[-1]=840
        request_positioning_gripper_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2,input_text)
        goal_state_robo_2.get_obj()[:]=np.hstack((transfer_pose,840))
        request_positioning_robot_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_2,input_text)
        goal_state_robo_2.get_obj()[-1]=0
        request_positioning_gripper_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2,input_text)
        # open master again
        goal_state_robo_1.get_obj()[-1]=840
        request_positioning_gripper_1.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2,input_text)

                               
    elif robot_master == 2 and robot_slave == 1 and not interrupted:
        # Transfer item: 
        # close slave gripper
        goal_state_robo_1.get_obj()[-1]=0
        request_positioning_gripper_1.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2,input_text)
        # open master gripper
        goal_state_robo_2.get_obj()[-1]=840
        request_positioning_gripper_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2,input_text)
        # Correct grasp pose:
        # move down master and close again
        goal_state_robo_2.get_obj()[:]=np.hstack((correction_pose,840))
        request_positioning_robot_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_2,input_text)
        goal_state_robo_2.get_obj()[-1]=0
        request_positioning_gripper_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2,input_text)
        # now move upper grip to middle pick position
        goal_state_robo_1.get_obj()[-1]=840
        request_positioning_gripper_1.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2,input_text)
        goal_state_robo_1.get_obj()[:]=np.hstack((transfer_pose,840))
        request_positioning_robot_1.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_2,input_text)
        goal_state_robo_1.get_obj()[-1]=0
        request_positioning_gripper_1.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2,input_text)
        # open master again
        goal_state_robo_2.get_obj()[-1]=840
        request_positioning_gripper_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_gripper_1, request_positioning_gripper_2,input_text)


    move_apart_pose = np.array([400, 0, 500, -180,-90,0])
    face_down_pose  = np.array([400, 0, 300, -180,0,0])
    init_pose       = np.array([200, 0, 300, -180,0,0])

    # step 4 move back slave
    if robot_master == 1 and not interrupted:
        # move back robo 1
        reset_pos = move_apart_pose
        goal_state_robo_1.get_obj()[:]=np.hstack((reset_pos,0))
        request_positioning_robot_1.value = True
        # face down robo 2
        reset_pos = face_down_pose
        goal_state_robo_2.get_obj()[:]=np.hstack((reset_pos,0))
        request_positioning_robot_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_1,input_text)
        # face down robo 1 - > robo 2 has item now
        reset_pos = face_down_pose
        goal_state_robo_1.get_obj()[:]=np.hstack((reset_pos,0))
        request_positioning_robot_1.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_2,input_text)
        # move start pos robo 1
        reset_pos = init_pose
        goal_state_robo_1.get_obj()[:]=np.hstack((reset_pos,0))
        request_positioning_robot_1.value = True  
        goal_state_robo_2.get_obj()[:]=np.hstack((reset_pos,0))
        request_positioning_robot_2.value = True 
    elif robot_master == 2 and not interrupted:
        # move back robo 2
        reset_pos = move_apart_pose
        goal_state_robo_2.get_obj()[:]=np.hstack((reset_pos,0))
        request_positioning_robot_2.value = True
        # face down robo 1
        reset_pos = face_down_pose
        goal_state_robo_1.get_obj()[:]=np.hstack((reset_pos,0))
        request_positioning_robot_1.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_2, request_positioning_robot_2,input_text)
        # face down robo 2 - > robo 1 has item now
        reset_pos = face_down_pose
        goal_state_robo_2.get_obj()[:]=np.hstack((reset_pos,0))
        request_positioning_robot_2.value = True
        interrupted = wait_moving(stop_runtime, request_positioning_robot_1, request_positioning_robot_2,input_text)
        # move start pos robo 2
        reset_pos = init_pose
        goal_state_robo_1.get_obj()[:]=np.hstack((reset_pos,0))
        request_positioning_robot_1.value = True  
        goal_state_robo_2.get_obj()[:]=np.hstack((reset_pos,0))
        request_positioning_robot_2.value = True 

    if not interrupted:
        if ((robot_slave == 1 and current_state_robo_1.get_obj()[-1] > 5) 
            or robot_slave == 2 and current_state_robo_2.get_obj()[-1] > 5):
            content.append('Hand over completed.')
        else:
            content.append('The hand over failed. Try to pick the object again.')
    else:
        request_positioning_robot_1= False
        request_positioning_robot_2 = False
        request_positioning_gripper_1 = False
        request_positioning_gripper_2 = False
        content.append('Hand over interrupted by a user intervention with the following prompt:')