from xarm.wrapper import XArmAPI
from myLibs.ufactory.xarm_errors import controller_error_codes,gripper_error_codes
import numpy as np

class xArm7:
    def __init__(self, ip):
        self.arm = XArmAPI(ip)
        self.ip = ip
        self.arm.motion_enable(enable=True)
        self.arm.set_collision_tool_model(tool_type=1)
        self.arm.set_gripper_enable(enable=True)        
        self.status_code, self.position = self.arm.get_position()
        self.x = self.position[0]
        self.y = self.position[1]
        self.z = self.position[2]
        self.roll = self.position[3]
        self.pitch = self.position[4]
        self.yaw = self.position[5]
        self.gripper_pos = self.get_gripper_pos()
        self.previous_gripper_pos = self.get_gripper_pos()
        self.gripper_timer = 0
        self.gripper_moving = True

    def start_up(self):
        self.is_error()        
        self.position_mode()        
        self.arm.set_position(x=200,y=0, z=300,roll=-179, pitch=0,yaw=0, speed=500, mvacc=100, wait=True, radius=20, motion_type=2)
        self.open_gripper()

    def get_states(self)->None:
        self.status, self.position = self.arm.get_position()
        self.x = self.position[0]
        self.y = self.position[1] 
        self.z = self.position[2] 
        self.roll = self.position[3] 
        self.pitch = self.position[4] 
        self.yaw = self.position[5]
        return self.position        

    def write_states_into_position(self)->None:
        self.position[0] = self.x
        self.position[1] = self.y
        self.position[2] = self.z
        self.position[3] = self.roll
        self.position[4] = self.pitch
        self.position[5] = self.yaw

    def write_position(self, new_pos: np.array)-> None:
        self.position = new_pos

    def set_position(self)->None:
        self.arm.set_servo_cartesian(mvpose = self.position,speed=500,mvacc=100, relative =True)

    def set_position_relative(self, step)->None:
        self.arm.set_servo_cartesian_aa(axis_angle_pose = step, speed=1000,mvacc=2000,wait = False,relative=True)

    def set_position_wait(self,position)->None:
        self.arm.set_position(x=position[0] ,y=position[1], z=position[2],roll=position[3], pitch=position[4],yaw=position[5], speed=500, mvacc=100, wait=True, motion_type=1)

    def destroy(self)->None:
        self.arm.set_state(state=4)
        self.arm.disconnect()

    def close_gripper(self)->None:
        self.arm.set_gripper_position(pos=0)

    def open_gripper(self)->None:
        self.arm.set_gripper_position(pos=850)

    def set_gripper_pos(self,pos)-> None:
        self.arm.set_gripper_position(pos=pos,wait=True)

    def set_gripper_pos_con(self,pos)-> None:
        self.arm.set_gripper_position(pos=pos)

    def get_gripper_pos(self)->float:
        gripper_pos = self.arm.get_gripper_position()
        self.gripper_pos = gripper_pos[1]
        return gripper_pos[1]

    def is_gripper_moving(self, current_time)->bool:
        pose = self.get_gripper_pos()
        time_diff = current_time - self.gripper_timer

        if pose is None or self.previous_gripper_pos is None:
            self.gripper_moving = False
            return self.gripper_moving

        if abs(pose-self.previous_gripper_pos) < 2:
            if time_diff > 0.5:
                self.previous_gripper_pos = pose
                self.gripper_moving = False
                return self.gripper_moving
            else:
                self.previous_gripper_pos = pose
                self.gripper_moving = True
                return self.gripper_moving
        else:
            self.gripper_timer = current_time
            self.previous_gripper_pos = pose
            self.gripper_moving = True
            return self.gripper_moving        
        

    def manual_mode(self)-> None:
        self.arm.motion_enable(enable=True)
        # Set robot to ready state
        self.arm.set_mode(0)
        self.arm.set_state(0)
        # Set to manual mode
        self.arm.set_mode(2)
        self.arm.set_state(0)
    
    def position_mode(self)-> None:
        self.arm.motion_enable(enable=True)
        # Set robot to ready state
        self.arm.set_mode(0)
        self.arm.set_state(0)

    def servo_mode(self)-> None:
        self.arm.motion_enable(enable=True)
        # Set robot to ready state
        self.arm.set_mode(1)
        self.arm.set_state(0)


    def reset(self)-> None:
        if self.is_error():
            return
        self.position_mode()
        self.get_states()
        if self.x > 400:
            self.arm.set_position(x=self.x-200,y=self.y, z=400,roll=self.roll, pitch=self.pitch,yaw=self.yaw, speed=200, mvacc=500, wait=True, motion_type=1)
            self.arm.set_position(x=self.x-200,y=self.y, z=400,roll=-179, pitch=0,yaw=0, speed=200, mvacc=500, wait=True, motion_type=1)
        else:
            self.arm.set_position(x=self.x,y=self.y, z=self.z,roll=self.roll, pitch=self.pitch,yaw=self.yaw, speed=200, mvacc=500, wait=True, motion_type=1)
            self.arm.set_position(x=self.x,y=self.y, z=self.z,roll=-179, pitch=0,yaw=0, speed=200, mvacc=500, wait=True, motion_type=1)

        self.arm.set_position(x=200,y=0, z=300,roll=-179, pitch=0,yaw=0, speed=200, mvacc=500, wait=True, motion_type=1)
        self.open_gripper()

    def is_error(self)->bool:
        code_robo, [error_code_robo, warn_code]= self.arm.get_err_warn_code()
        if code_robo == 0 and error_code_robo!=0:
            print(controller_error_codes[error_code_robo])

        code_gripper, error_code_gripper = self.arm.get_gripper_err_code()
        if code_gripper == 0 and error_code_gripper!=0:
            print(gripper_error_codes[error_code_gripper])

        if (code_gripper and code_robo)==0 and (error_code_gripper or error_code_robo) !=0:
            return True
        
        return False
    
    def get_arm_err(self):
        code_robo, [error_code_robo, warn_code]= self.arm.get_err_warn_code()
        return error_code_robo
    
    def get_gripper_err(self):
        code_gripper, error_code_gripper = self.arm.get_gripper_err_code()
        return error_code_gripper

    
