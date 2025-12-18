import pygame
import cv2
import numpy as np
from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
import multiprocessing
import os

from pygame_gui import UIManager, UI_TEXT_ENTRY_CHANGED, UI_BUTTON_PRESSED
from pygame_gui.elements import  UITextEntryBox, UITextBox, UIImage, UIButton
from pygame_gui.core import ObjectID

class GuiHandler:
    def __init__(self, width: int, height: int):
        # general
        self.running = True
        self.x_pixel = width
        self.y_pixel = height
        self.current_time = 0
        # paths
        script_dir = os.path.dirname(__file__)
        config_path = os.path.join(script_dir, "themes/theme.json")
        img_path = os.path.join(script_dir, "assets/CameraInit.jpg")
        self.manager = UIManager((self.x_pixel, self.y_pixel), config_path)
        self.manager.preload_fonts([{'name': 'noto_sans', 'point_size': 14, 'style': 'bold', 'antialiased': '1'}])
        # input text field
        self.user_task = None
        self.x_text_entry_box = 50
        self.y_task_entry_box = 50
        self.width_task_entry_box = 400
        self.height_task_entry_box = 100    
        self.rect_task_entry_box = pygame.Rect(self.x_text_entry_box,
                                          self.y_task_entry_box,
                                          self.width_task_entry_box,
                                          self.height_task_entry_box)
        self.task_entry_box = UITextEntryBox(
            relative_rect=self.rect_task_entry_box,
            initial_text="",
            manager=self.manager,
            object_id=ObjectID(class_id="text_entry_box",
                            object_id="#text_entry_box_1"),
            placeholder_text="Enter Task here..."
            )
        self.entry_done = False
        # output text 
        self.input_history = []
        self.box_history_y = self.rect_task_entry_box.bottom + 25
        self.box_history_width = 550
        self.box_history_height = self.y_pixel - self.box_history_y - 50
        self.history_area_rect = pygame.Rect(self.rect_task_entry_box.x,
                                            self.box_history_y,
                                            self.box_history_width,
                                            self.box_history_height)
        self.chat_box = UITextBox(
            relative_rect=self.history_area_rect,
            object_id=ObjectID(class_id="text_box",
                            object_id="#text_box_1"),
                            html_text='',
                            )
        self.old_text = ''
        # Recording box
        self.record_button_text = "Record Task"        
        self.record_BOX_X = self.x_text_entry_box + self.width_task_entry_box + 10
        self.record_BOX_Y = self.y_task_entry_box
        self.record_BOX_WIDTH = 140        
        self.record_BOX_HEIGHT = self.height_task_entry_box  
        self.record_box_rect = pygame.Rect(self.record_BOX_X,
                                          self.record_BOX_Y,
                                          self.record_BOX_WIDTH,
                                          self.record_BOX_HEIGHT)
        self.record_button = UIButton(relative_rect=self.record_box_rect,
                                      text=self.record_button_text,
                                      manager=self.manager,
                                      object_id='button')
        self.recording_active = False
        # webcam frame
        self.webcam_width = 1080
        self.webcam_height = 720
        self.webcam_frame_width = 2
        self.x_cam_image = 600 + 60
        self.y_cam_image = 175        
        self.cam_rect = pygame.Rect(self.x_cam_image,self.y_cam_image,self.webcam_width,self.webcam_height)
        init_image = pygame.image.load(img_path)
        self.init_image = pygame.transform.scale(init_image, (self.webcam_width, self.webcam_height))
        self.surface = init_image
        self.cam_image = UIImage(relative_rect=self.cam_rect,
                                image_surface=self.surface,
                                manager=self.manager,
                                anchors={'left': 'left',
                                        'right': 'right',
                                        'top': 'top',
                                        'bottom': 'bottom'},
                                object_id='rounded_cam_image')
        # roboarm status and reset
        # roboter 1
        self.reset_arm_1 = False
        self.ip_arm_1 = "10.2.134.152"
        self.position_robo_1 = np.array([0., 0., 0., 0., 0., 0., 0.])
        self.status_robo_1 = 0
        self.width_box_robo = 150
        self.height_box_robo = 250
        self.origin_x_box_robo_1 = self.x_cam_image
        self.origin_y_box_robo_1 = self.y_cam_image        
        self.box_robo_1 = pygame.Rect(self.origin_x_box_robo_1,
                                          self.origin_y_box_robo_1,
                                          self.width_box_robo,
                                          self.height_box_robo)
        self.robo_status_text_1 = UITextBox(relative_rect=self.box_robo_1,
                                      html_text=
                                        '<b>Robot IP</b><br>'
                                        f"{self.ip_arm_1} <br>"
                                        '<b>X,Y,Z</b><br>' 
                                        f"{self.position_robo_1[0]:.1f},{self.position_robo_1[1]:.1f},{self.position_robo_1[2]:.1f}<br>"
                                        '<b>Roll, Pitch, Yaw</b><br>'
                                        f"{self.position_robo_1[3]:.1f},{self.position_robo_1[4]:.1f},{self.position_robo_1[5]:.1f}<br>"
                                        '<b>Gripper</b><br>'
                                        f"{self.position_robo_1[-1]:.1f}<br>"
                                        '<b>Status</b><br>'
                                        f"{self.status_robo_1}",
                                      manager=self.manager,
                                      object_id='robot_box')
        self.old_color_robot_status = self.robo_status_text_1.background_colour
        # roboter 2
        self.reset_arm_2 = False
        self.ip_arm_2 = "10.2.134.151"
        self.position_robo_2 = np.array([0., 0., 0., 0., 0., 0.,0.])
        self.status_robo_2 = 0
        self.origin_x_box_robo_2 = self.x_cam_image + self.webcam_width - self.width_box_robo
        self.origin_y_box_robo_2 = self.y_cam_image      
        self.box_robo_2 = pygame.Rect(self.origin_x_box_robo_2,
                                          self.origin_y_box_robo_2,
                                          self.width_box_robo,
                                          self.height_box_robo)
        self.robo_status_text_2 = UITextBox(relative_rect=self.box_robo_2,
                                      html_text=
                                        '<b>Robot IP</b><br>'
                                        f"{self.ip_arm_2} <br>"
                                        '<b>X,Y,Z</b><br>' 
                                        f"{self.position_robo_2[0]:.1f},{self.position_robo_2[1]:.1f},{self.position_robo_2[2]:.1f}<br>"
                                        '<b>Roll, Pitch, Yaw</b><br>'
                                        f"{self.position_robo_2[3]:.1f},{self.position_robo_2[4]:.1f},{self.position_robo_2[5]:.1f}<br>"
                                        '<b>Gripper</b><br>'
                                        f"{self.position_robo_2[-1]:.1f}<br>"
                                        '<b>Status</b><br>'
                                        f"{self.status_robo_2}",
                                      manager=self.manager,
                                      object_id='robot_box')
        # Robot Reset Button
        self.reset_button_text = "Reset Robots"        
        self.x_reset_button = self.x_cam_image
        self.y_reset_button = self.y_task_entry_box
        self.width_reset_button = 140        
        self.height_reset_button = self.height_task_entry_box  
        self.reset_button_rect = pygame.Rect(self.x_reset_button,
                                          self.y_reset_button,
                                          self.width_reset_button,
                                          self.height_reset_button)
        self.reset_button = UIButton(relative_rect=self.reset_button_rect,
                                      text=self.reset_button_text,
                                      manager=self.manager,
                                      object_id='button')
        self.reset_active = False
        
        
        
    def update_robo_status(self, current_state_robo_1: SynchronizedArray,current_state_robo_2: SynchronizedArray,status_robo_1: Synchronized, status_robo_2: Synchronized):
        self.position_robo_1 = current_state_robo_1.get_obj()[:]
        self.status_robo_1 = status_robo_1.value
        self.position_robo_2 = current_state_robo_2.get_obj()[:]
        self.status_robo_2 = status_robo_2.value
        self.robo_status_text_1.set_text('<b>Robot IP</b><br>'
                                        f"{self.ip_arm_1} <br>"
                                        '<b>X,Y,Z</b><br>' 
                                        f"{self.position_robo_1[0]:.1f},{self.position_robo_1[1]:.1f},{self.position_robo_1[2]:.1f}<br>"
                                        '<b>Roll, Pitch, Yaw</b><br>'
                                        f"{self.position_robo_1[3]:.1f},{self.position_robo_1[4]:.1f},{self.position_robo_1[5]:.1f}<br>"
                                        '<b>Gripper</b><br>'
                                        f"{self.position_robo_1[-1]:.1f}<br>"
                                        '<b>Status</b><br>'
                                        f"{self.status_robo_1}")
        self.robo_status_text_2.set_text('<b>Robot IP</b><br>'
                                        f"{self.ip_arm_2} <br>"
                                        '<b>X,Y,Z</b><br>' 
                                        f"{self.position_robo_2[0]:.1f},{self.position_robo_2[1]:.1f},{self.position_robo_2[2]:.1f}<br>"
                                        '<b>Roll, Pitch, Yaw</b><br>'
                                        f"{self.position_robo_2[3]:.1f},{self.position_robo_2[4]:.1f},{self.position_robo_2[5]:.1f}<br>"
                                        '<b>Gripper</b><br>'
                                        f"{self.position_robo_2[-1]:.1f}<br>"
                                        '<b>Status</b><br>'
                                        f"{self.status_robo_2}")
        
    def update_chat_box(self, shared_data):
        history_text = shared_data.output_hist
        if self.old_text != history_text:
            self.chat_box.set_text(history_text)
            self.old_text = history_text
            if self.chat_box.scroll_bar:
                self.chat_box.scroll_bar.set_scroll_from_start_percentage(1.0)

    def update_cam_feed(self, shared_data):
        frame = shared_data.gui_frame
        if frame is None:
            frame = self.init_image
            self.cam_image.set_image(frame)
        else:
            resized_surfaced_frame = self.webcam_to_pygame(frame, rotation=True, flip=True)
            self.cam_image.set_image(resized_surfaced_frame)

    def webcam_to_pygame(self, frame: tuple, rotation:bool=False, flip:bool=False):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if rotation:
            frame = np.rot90(frame)
        if flip:
           frame = np.flipud(frame) 

        pygame_frame = pygame.surfarray.make_surface(frame)
        resized_pygame_frame = pygame.transform.scale(pygame_frame, (self.webcam_width, self.webcam_height))

        img_rect = resized_pygame_frame.get_rect()
        rounded_surface = pygame.Surface(img_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(rounded_surface, (255, 255, 255), img_rect, border_radius=9)
        rounded_surface.blit(resized_pygame_frame, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        return rounded_surface
    
    def input_management(self, input_queue:multiprocessing.Queue , request_record: EventClass, request_robot_reset: EventClass):
        self.current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.entry_done = True
                        text = self.task_entry_box.get_text()
                        if text != '':
                            input_queue.put(text)
                            print(f"task is: {text}")
                        self.task_entry_box.set_text('') 
                        self.task_entry_box.unfocus()                                       

            if event.type == UI_BUTTON_PRESSED:
                if event.ui_element == self.record_button:
                    # Handle record Button
                    self.recording_active = not self.recording_active
                    if (self.recording_active):
                        self.record_button.set_text("Recording...")
                        request_record.set()
                    else:
                        self.record_button.set_text("Press to Record")
                        request_record.clear()
                if event.ui_element == self.reset_button:
                    # Handle record Button
                    self.reset_active = not self.reset_active
                    if (self.reset_active):
                        self.reset_button.set_text("Reset Active")
                        request_robot_reset.set()
                        color = pygame.Color('#FCA350')
                        self.robo_status_text_1.background_colour = color
                        self.robo_status_text_1.rebuild()
                        self.robo_status_text_2.background_colour = color
                        self.robo_status_text_2.rebuild()
                    else:
                        self.reset_button.set_text("Reset Robots")
                        request_robot_reset.clear()
                        self.robo_status_text_1.background_colour = self.old_color_robot_status
                        self.robo_status_text_1.rebuild()
                        self.robo_status_text_2.background_colour = self.old_color_robot_status
                        self.robo_status_text_2.rebuild()


                   
            
            self.manager.process_events(event)