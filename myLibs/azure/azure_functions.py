import pykinect_azure as pykinect
from pykinect_azure import K4A_CALIBRATION_TYPE_COLOR, K4A_CALIBRATION_TYPE_DEPTH, k4a_float2_t,k4a_float3_t

from myLibs.translation_rotation.matrices import *

class Azure:
    def __init__(self):
        pykinect.initialize_libraries()
        self.device_config = pykinect.default_configuration
        self.device_config.color_format = pykinect.K4A_IMAGE_FORMAT_COLOR_BGRA32
        self.device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
        self.device_config.depth_mode = pykinect.K4A_DEPTH_MODE_WFOV_2X2BINNED
        self.device = pykinect.start_device(config=self.device_config)
        self.capture = self.device.update()


    def recieve_frame(self):
        self.capture = self.device.update()

    def get_color_image(self):
        ret, color_image = self.capture.get_color_image()
        
        return ret, color_image
    
    def get_depth_colored_image(self):
        ret, color_image = self.capture.get_colored_depth_image()
        
        return ret,color_image
    
    def get_depth_transformed_image(self):
        ret, color_image = self.capture.get_transformed_depth_image()
        
        return ret,color_image
    
    def get_color_transformed_image(self):
        ret, color_image = self.capture.get_transformed_color_image()
        
        return ret,color_image
    
    def point_to_3d(self, point)-> tuple[bool, k4a_float3_t | int]:
        success = True
        ret_d, transformed_depth_image = self.get_depth_transformed_image()
        
        if not ret_d:
            success = False
            return success,0
        
        pixels = k4a_float2_t((point[0], point[1]))
        rgb_depth = transformed_depth_image[point[1], point[0]] # somehow y and x are swapped?
        pos3d_color = self.device.calibration.convert_2d_to_3d(pixels, rgb_depth, K4A_CALIBRATION_TYPE_COLOR, K4A_CALIBRATION_TYPE_COLOR)

        return success,pos3d_color
    
    def mask_to_depth(self, points):
        success = True
        ret_d, transformed_depth_image = self.get_depth_transformed_image()
        
        if not ret_d:
            success = False
            return success,0
                 
        number_pixel = points.shape[0]
        average_height = 0
        for i in range(0 ,number_pixel):
            rgb_depth = int(transformed_depth_image[points[i,1], points[i,0]])
            average_height += rgb_depth

        average_height = average_height/number_pixel

        return success, average_height

    def point_averaged_to_3d(self, point, polylines)-> tuple[bool, k4a_float3_t | int]:
        pixels = k4a_float2_t((point[0], point[1]))
        success, rgb_depth = self.mask_to_depth(polylines)
        pos3d_color = self.device.calibration.convert_2d_to_3d(pixels, rgb_depth, K4A_CALIBRATION_TYPE_COLOR, K4A_CALIBRATION_TYPE_COLOR)
        return success,pos3d_color
    
    def destroy(self):
        self.device.close()
    

def transform_cam_to_robo_coord(pose3d: k4a_float3_t, length_tool: float):
    pos_arm = np.array([0,0,0,1])
    Translation_to_cam =  trans_y(-20) @ trans_x(555) @ trans_z(972) @ rot_x(np.pi)         
    pos_cam = Translation_to_cam @ pos_arm
    translation_to_object = Translation_to_cam @ trans_z(pose3d.xyz.z - length_tool) @ trans_x(pose3d.xyz.x) @ trans_y(pose3d.xyz.y)
    coord_arm_zero = np.array([0,0,0,1])
    pos_object_arm_coord = translation_to_object @ coord_arm_zero
    # subtract from total height 1cm so the gripper can
    # grasp it tide
    pos_object_arm_coord[2] = pos_object_arm_coord[2] -10
    return pos_object_arm_coord