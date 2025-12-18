import multiprocessing
from myLibs.video_sources.depth_cam import depthcam_and_object_extraction_loop
from myLibs.low_lvl_control.dual_robot_arm_jointspace import control_loop_jointspace
from myLibs.control_models.gemini_control_loops import gemini_loop_new_gui
from myLibs.pygame.GUI_modern import GUI_modern_loop
from myLibs.audio_input.recorder import AudioRecorder


if __name__ == "__main__":
    AudioRec = AudioRecorder()
    stop_runtime = multiprocessing.Event()      # for stopping all processes
    request_depth_pose = multiprocessing.Event()
    request_robot_reset_gui = multiprocessing.Event()
    request_robot_reset = multiprocessing.Event()
    request_record = multiprocessing.Event()
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
    robo_ip_1 = '10.2.134.152'    
    status_robo_1 = multiprocessing.Value('i', 100)    
    current_state_robo_1 = multiprocessing.Array('d', [0.,0.,0.,0.,0.,0.,0.])
    goal_state_robo_1 = multiprocessing.Array('d', [0.,0.,0.,0.,0.,0.,0.])    
    request_positioning_robot_1 = multiprocessing.Value('b',False)
    request_positioning_gripper_1 = multiprocessing.Value('b',False)
    z_min_robo_1 = 2 # table at 5    
    # Robotarm 2
    robo_ip_2 = '10.2.134.151'
    status_robo_2 = multiprocessing.Value('i', 100)
    current_state_robo_2 = multiprocessing.Array('d', [0.,0.,0.,0.,0.,0.,0.])
    goal_state_robo_2 = multiprocessing.Array('d', [0.,0.,0.,0.,0.,0.,0.]) 
    request_positioning_robot_2 = multiprocessing.Value('b',False)
    request_positioning_gripper_2 = multiprocessing.Value('b',False)
    z_min_robo_2 = 5   

    # vars for LLM output
    shared_data.output_hist = '' 

    p1 = multiprocessing.Process(target=depthcam_and_object_extraction_loop, args=(stop_runtime,
                                                              request_depth_pose,
                                                              request_rect_reset,
                                                              shared_data))
    p1.start()
    p2 = multiprocessing.Process(target=gemini_loop_new_gui, args=(stop_runtime,
                                                                request_depth_pose,
                                                                request_rect_reset, 
                                                                request_robot_reset,
                                                                request_record,
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
    p3 = multiprocessing.Process(target=control_loop_jointspace, args=(stop_runtime,
                                                                        robo_ip_1,
                                                                        request_robot_reset_gui,
                                                                        request_robot_reset,
                                                                        request_positioning_robot_1,
                                                                        request_positioning_gripper_1,
                                                                        current_state_robo_1,
                                                                        goal_state_robo_1,
                                                                        status_robo_1,
                                                                        z_min_robo_1,
                                                                        True))
    p3.start()
    p4 = multiprocessing.Process(target=control_loop_jointspace, args=(stop_runtime,
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
    p5 = multiprocessing.Process(target=GUI_modern_loop, args=(stop_runtime,
                                                        request_robot_reset_gui,
                                                        request_record,
                                                        shared_data,
                                                        current_state_robo_1,
                                                        status_robo_1,
                                                        current_state_robo_2,
                                                        status_robo_2,
                                                        input_queue,))
    p5.start()

    while not stop_runtime.is_set():
        AudioRec.record(request_record)



    p1.join()
    p2.join()
    p3.join()
    p4.join()
    p5.join()
