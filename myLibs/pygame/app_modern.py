import pygame
import numpy as np
import cv2
from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
import multiprocessing
import os

from myLibs.pygame.render_class_modern import GuiHandler

class PyGameApp:
    def __init__(self, fullscreen= False,uses_multiprocess:bool=False):
        pygame.init()
        self.width = 1920
        self.height = 1080
        app_name = "XARM Agent"

        if fullscreen:
            self.screen = pygame.display.set_mode((self.width, self.height),pygame.FULLSCREEN, vsync=1)
        else:
            self.screen = pygame.display.set_mode((self.width, self.height),vsync=1)
        pygame.display.set_caption(app_name)
        self.app_loop = True

        self.GuiHandler = GuiHandler(self.width, self.height)
        if uses_multiprocess:
            self.cam = None            
        else:
            self.cam = cv2.VideoCapture('/dev/video2')

        script_dir = os.path.dirname(__file__)
        img_path = os.path.join(script_dir, "assets/Background2.png")
        background_original = pygame.image.load(img_path).convert_alpha()
        self.background = pygame.transform.scale(background_original, (self.width, self.height))
        

    def GUI_loop(self,
                stop_flag: EventClass,
                request_robot_reset: EventClass,
                request_record: EventClass,
                shared_data,
                current_state_robo_1: SynchronizedArray,
                status_robo_1: Synchronized,
                current_state_robo_2: SynchronizedArray,
                status_robo_2: Synchronized,
                input_queue: multiprocessing.Queue,
                test_mode: bool=False): 
        clock = pygame.time.Clock()   
        while self.GuiHandler.running:
            time_delta = clock.tick(60)/1000.0
            if stop_flag.is_set():
                self.GuiHandler.running = False

            self.screen.blit(self.background, (0, 0))

            self.GuiHandler.update_chat_box(shared_data)
            
            self.GuiHandler.update_robo_status(current_state_robo_1,
                                               current_state_robo_2,
                                               status_robo_1,
                                               status_robo_2)

            self.GuiHandler.update_cam_feed(shared_data)           

            self.GuiHandler.input_management(input_queue, request_record,request_robot_reset)       
            
            self.GuiHandler.manager.update(time_delta)
            self.GuiHandler.manager.draw_ui(self.screen)            

            self.refresh_frame()
        stop_flag.set()

    def refresh_frame(self):
        pygame.display.flip()

    def destroy(self):
        pygame.quit()