import multiprocessing
from myLibs.video_sources.depth_cam import azure_loop_gui_no_yolo
from myLibs.low_lvl_control.dual_robo_arm_continous import dual_xarm7_control_loop
from myLibs.control_models.gemini_control_loops import dual_arm_gemini_loop_no_yolo
from myLibs.pygame.GUI import gui_dual_arm_loop


if __name__ == "__main__":
    stop_runtime = multiprocessing.Event()      # for stopping all processes
    request_depth_pose = multiprocessing.Event()
    request_robot_reset_gui = multiprocessing.Event()
    request_robot_reset = multiprocessing.Event()
    request_rect_reset = multiprocessing.Event()
    input_queue = multiprocessing.Queue()       # for terminal text input
    manager = multiprocessing.Manager()
    shared_data = manager.Namespace()
    # vars for videos
    shared_data.frame = None
    shared_data.gui_frame = None 
    shared_data.items = None
    shared_data.object_name = None
    # vars for robots
    # Robotarm 1 
    robo_ip_1 = '192.168.1.x'    
    status_robo_1 = multiprocessing.Value('i', 100)    
    current_state_robo_1 = multiprocessing.Array('d', [0.,0.,0.,0.,0.,0.,0.])
    goal_state_robo_1 = multiprocessing.Array('d', [0.,0.,0.,0.,0.,0.,0.])    
    request_positioning_robot_1 = multiprocessing.Value('b',False)
    request_positioning_gripper_1 = multiprocessing.Value('b',False)
    z_min_robo_1 = 2 # table at 5    
    # Robotarm 2
    robo_ip_2 = '192.168.1.x'
    status_robo_2 = multiprocessing.Value('i', 100)
    current_state_robo_2 = multiprocessing.Array('d', [0.,0.,0.,0.,0.,0.,0.])
    goal_state_robo_2 = multiprocessing.Array('d', [0.,0.,0.,0.,0.,0.,0.]) 
    request_positioning_robot_2 = multiprocessing.Value('b',False)
    request_positioning_gripper_2 = multiprocessing.Value('b',False)
    z_min_robo_2 = 5   

    # vars for LLM output
    shared_data.output_hist = []  

    p1 = multiprocessing.Process(target=azure_loop_gui_no_yolo, args=(stop_runtime,
                                                              request_depth_pose,
                                                              request_rect_reset,
                                                              shared_data))
    p1.start()
    p2 = multiprocessing.Process(target=dual_arm_gemini_loop_no_yolo, args=(stop_runtime,
                                                                request_depth_pose,
                                                                request_rect_reset, 
                                                                request_robot_reset,
                                                                input_queue, 
                                                                shared_data,
                                                                status_robo_1,
                                                                status_robo_2,
                                                                current_state_robo_1,
                                                                current_state_robo_2,
                                                                goal_state_robo_1,
                                                                goal_state_robo_2,
                                                                request_positioning_robot_1,
                                                                request_positioning_robot_2,
                                                                request_positioning_gripper_1,
                                                                request_positioning_gripper_2))
    p2.start()
    p3 = multiprocessing.Process(target=dual_xarm7_control_loop, args=(stop_runtime,
                                                                        robo_ip_1,
                                                                        request_robot_reset_gui,
                                                                        request_robot_reset,
                                                                        request_positioning_robot_1,
                                                                        request_positioning_gripper_1,
                                                                        current_state_robo_1,
                                                                        goal_state_robo_1,
                                                                        status_robo_1,
                                                                        z_min_robo_1))
    p3.start()
    p4 = multiprocessing.Process(target=dual_xarm7_control_loop, args=(stop_runtime,
                                                                        robo_ip_2,
                                                                        request_robot_reset_gui,
                                                                        request_robot_reset,
                                                                        request_positioning_robot_2,
                                                                        request_positioning_gripper_2,
                                                                        current_state_robo_2,
                                                                        goal_state_robo_2,
                                                                        status_robo_2,
                                                                        z_min_robo_2))
    p4.start()
    p5 = multiprocessing.Process(target=gui_dual_arm_loop, args=(stop_runtime,
                                                        request_robot_reset_gui,
                                                        shared_data,
                                                        current_state_robo_1,
                                                        status_robo_1,
                                                        current_state_robo_2,
                                                        status_robo_2,
                                                        input_queue,))
    p5.start()



    p1.join()
    p2.join()
    p3.join()
    p4.join()
    p5.join()
