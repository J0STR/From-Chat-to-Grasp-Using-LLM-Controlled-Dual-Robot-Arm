from myLibs.pygame.app_class import PyGameApp
from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
import multiprocessing

def gui_dual_arm_loop(stop_runtime: EventClass,
             request_robot_reset: EventClass,
             shared_data: EventClass,
             current_state_robo_1: SynchronizedArray,
             status_robo_1: Synchronized,
             current_state_robo_2: SynchronizedArray,
             status_robo_2: Synchronized,
             input_queue: multiprocessing.Queue,
             fullscreen = False,
             test_mode: bool = False):
    
    App = PyGameApp(fullscreen=fullscreen,uses_multiprocess=True)
    App.loop_dual_arm_multiprocess(stop_runtime,
                          request_robot_reset,
                          shared_data,
                          current_state_robo_1,
                          status_robo_1,
                          current_state_robo_2,
                          status_robo_2,
                          input_queue,
                          test_mode)
    App.destroy()
