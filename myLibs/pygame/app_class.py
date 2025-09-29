import pygame
import numpy as np
import cv2
from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
import multiprocessing
import os

from .render_class import GuiHandler

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
        img_path = os.path.join(script_dir, "assets/Background.png")
        self.background = pygame.image.load(img_path).convert_alpha()


    def refresh_frame(self):
        pygame.display.flip()

    def loop_dual_arm_multiprocess(self,
                                    stop_flag: EventClass,
                                    request_robot_reset: EventClass,
                                    shared_data,
                                    current_state_robo_1: SynchronizedArray,
                                    status_robo_1: Synchronized,
                                    current_state_robo_2: SynchronizedArray,
                                    status_robo_2: Synchronized,
                                    input_queue: multiprocessing.Queue,
                                    test_mode: bool=False):    
        while self.GuiHandler.running:
            if stop_flag.is_set():
                self.GuiHandler.running = False
            self.screen.blit(self.background, (0, 0))

            frame = shared_data.gui_frame
            if frame is None:
                continue

            resized_pygame_frame = self.GuiHandler.webcam_to_pygame(frame, rotation=True, flip=True)
            self.GuiHandler.draw_webcam_image(resized_pygame_frame,self.screen)

            self.GuiHandler.input_management_multiprocess(input_queue, request_robot_reset)


            self.GuiHandler.position_robo_1 = current_state_robo_1.get_obj()[:]
            self.GuiHandler.status_robo_1 = status_robo_1.value
            self.GuiHandler.position_robo_2 = current_state_robo_2.get_obj()[:]
            self.GuiHandler.status_robo_2 = status_robo_2.value
            self.GuiHandler.robo_fields(self.screen,request_robot_reset)

            self.GuiHandler.text_field(self.screen)
            self.GuiHandler.history_field_multiprocessing(self.screen, shared_data, test_mode)              

            self.refresh_frame()
        stop_flag.set()
        self.destroy()


    def destroy(self):
        pygame.quit()