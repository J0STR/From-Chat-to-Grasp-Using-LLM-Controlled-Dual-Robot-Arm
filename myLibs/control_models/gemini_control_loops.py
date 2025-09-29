import numpy as np
from ultralytics import YOLOE
from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
import multiprocessing
import os

from.gemini_classes import GeminiChatDual
from .gemini_helper_functions import wait_processes_to_init_dual_setup
from .gemini_function_calling_handler import check_and_run_function_calls_no_yolo
from myLibs.ufactory.dual_arm_functions import transform_robo_to_coord_sys
from myLibs.video_sources.video_functions import convert_cv_2_pil_resize

       
def dual_arm_gemini_loop_no_yolo(stop_runtime: EventClass,
                         request_depth_pose: EventClass,
                         request_rect_reset: EventClass,
                         request_robot_reset: EventClass,
                         input_text: multiprocessing.Queue,
                         shared_data,
                         status_robo_1:Synchronized,
                         status_robo_2:Synchronized,
                         current_state_robo_1: SynchronizedArray,
                         current_state_robo_2: SynchronizedArray,
                         goal_state_robo_1: SynchronizedArray,
                         goal_state_robo_2: SynchronizedArray,
                         request_positioning_robot_1: Synchronized,
                         request_positioning_robot_2: Synchronized,
                         request_positioning_gripper_1: Synchronized,
                         request_positioning_gripper_2: Synchronized):
    # load init prompt
    script_dir = os.path.dirname(__file__)
    prompt_path = os.path.join(script_dir, "prompts/dual_task.txt")
    with open(prompt_path, "r", encoding="utf-8") as file:
        prompt = file.read()   
    wait_processes_to_init_dual_setup(shared_data,stop_runtime, status_robo_1, status_robo_2)
    all_time_history = []

    task = None
    while not stop_runtime.is_set():
        GeminiClient = GeminiChatDual()
        GeminiClient.start_chat()
        response = GeminiClient.message(prompt)

        hist = shared_data.output_hist
        hist.append(response.text)
        shared_data.output_hist = hist
        # get command description
        content = []
        wait_task = True
        while wait_task and not stop_runtime.is_set():
            if not input_text.empty():
                eingabe = input_text.get()
                content.append(eingabe)
                hist = shared_data.output_hist
                hist.append(eingabe)
                shared_data.output_hist = hist
                wait_task = False
                task = True

                print("Entered task")
                print("\n")

        all_time_history.append(response.text)

        # start control loop
        while not stop_runtime.is_set() and task:

            cv_img = shared_data.frame
            pil_img = convert_cv_2_pil_resize(cv_img)
            content.append(pil_img)
            
            content.append(f"""The current position(x,y,z,roll,pitch,yaw) of roboter arm 1 is: {current_state_robo_1.get_obj()[:6]}
                           and its gripper position is:  {current_state_robo_1.get_obj()[6]}""")
            
            robo_2_coord_transformed = transform_robo_to_coord_sys(current_state_robo_2.get_obj()[:6])
            content.append(f"""The current position(x,y,z,roll,pitch,yaw) of roboter arm 2 is: {robo_2_coord_transformed}
                           and its gripper position is:  {current_state_robo_2.get_obj()[6]}""")
            
            all_time_history.extend(content)
            all_time_history.append("---------------------------------------------------------------------------------------------")

            # Check for new user input during control loop
            if not input_text.empty():
                eingabe = input_text.get()
                content.append(eingabe)
                hist = shared_data.output_hist
                hist.append(eingabe)
                shared_data.output_hist = hist

            response = GeminiClient.message(content)
            content = []
            hist = shared_data.output_hist
            hist.append(response.text)
            shared_data.output_hist = hist

            all_time_history.append(response.text)
            all_time_history.append("---------------------------------------------------------------------------------------------")

            all_time_history, task = check_and_run_function_calls_no_yolo(task,
                                                input_text,
                                                content,
                                                response,
                                                stop_runtime,
                                                request_rect_reset,
                                                request_depth_pose,
                                                request_robot_reset,
                                                shared_data,
                                                current_state_robo_1,
                                                current_state_robo_2,                                                
                                                goal_state_robo_1,
                                                goal_state_robo_2,
                                                request_positioning_robot_1,
                                                request_positioning_robot_2,
                                                request_positioning_gripper_1,
                                                request_positioning_gripper_2,
                                                all_time_history)