from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
import multiprocessing

from .gemini_function_call_action import *

def check_and_run_function_calls_no_yolo(task: bool,
                                 input_text: multiprocessing.Queue,
                                 content: List,
                                 response,
                                 stop_runtime: EventClass,
                                 request_rect_reset: EventClass,
                                 request_depth_pose: EventClass,
                                 request_robot_reset: EventClass,
                                 shared_data,
                                 current_state_robo_1: SynchronizedArray,
                                 current_state_robo_2: SynchronizedArray,                                 
                                 goal_state_robo_1: SynchronizedArray,
                                 goal_state_robo_2: SynchronizedArray,
                                 request_positioning_robot_1: Synchronized,
                                 request_positioning_robot_2: Synchronized,
                                 request_positioning_gripper_1: Synchronized,
                                 request_positioning_gripper_2: Synchronized,
                                 history_saver: list):
    
    try:
        for part in response.candidates[0].content.parts:
                    if part.function_call is not None:
                        function_call = part.function_call
                        print(function_call.name)
                        print(function_call.args)

                        hist = shared_data.output_hist
                        hist += '<font color=#5AACE3>'+function_call.name+'</font><br>'
                        hist += '<font color=#EB8258>'+json.dumps(function_call.args)+'</font><br><br>'
                        shared_data.output_hist = hist

                        history_saver.append(function_call.name)
                        history_saver.extend(function_call.args)

                        if function_call.name == "get_object_pose":
                            handle_get_object_with_gemini(stop_runtime,
                                            input_text,
                                            function_call,
                                            shared_data,
                                            content,
                                            request_rect_reset,
                                            request_depth_pose)
                            
                        if function_call.name == "set_robot_state_dual":
                            robot_id, desired_pos, task = set_robot_state(**function_call.args)
                            handle_set_robot_pos(stop_runtime,
                                                input_text,
                                                robot_id,
                                                task,
                                                desired_pos,
                                                content,
                                                goal_state_robo_1,
                                                goal_state_robo_2,
                                                request_positioning_robot_1,
                                                request_positioning_robot_2)
                        
                        if function_call.name == 'close_gripper_dual':
                            robot_id = gripper_tool(**function_call.args)
                            handle_close_gripper(stop_runtime,
                                                input_text,
                                                robot_id,
                                                content,
                                                current_state_robo_1,
                                                current_state_robo_2,  
                                                goal_state_robo_1,
                                                goal_state_robo_2,
                                                request_positioning_gripper_1,
                                                request_positioning_gripper_2)

                        if function_call.name == 'open_gripper_dual':
                            robot_id = gripper_tool(**function_call.args)
                            handle_open_gripper(stop_runtime,
                                                input_text,
                                                robot_id,
                                                content,
                                                goal_state_robo_1,
                                                goal_state_robo_2,
                                                request_positioning_gripper_1,
                                                request_positioning_gripper_2)

                        if function_call.name == 'hand_over_object':
                            robot_master, robot_slave = hand_over_object(**function_call.args)
                            handle_hand_over(stop_runtime,
                                            input_text,
                                            content,
                                            robot_master,
                                            robot_slave,
                                            current_state_robo_1,
                                            current_state_robo_2,
                                            goal_state_robo_1,
                                            goal_state_robo_2,
                                            request_positioning_robot_1,
                                            request_positioning_robot_2,
                                            request_positioning_gripper_1,
                                            request_positioning_gripper_2)
                        

                        if function_call.name == 'end_task':
                            history_saver,task = handle_end_task(task,
                                                shared_data,
                                                request_robot_reset,
                                                request_rect_reset,
                                                goal_state_robo_1,
                                                goal_state_robo_2,
                                                history_saver)
                            
                        history_saver.extend(content)
    except:
         pass
    
    return history_saver, task
