set_robot_pos = {
    "name": "set_robot_state",
    "description": "Use this function to set a desired position with [x,y,z,roll,pitch,yaw] format to the robot. Units are in milimeter for x,y,z and degree for roll,yaw,pitch.",
    "parameters": {
        "type": "object",
        "properties": {
            "position": {
                "type": "array",
                 "items": {"type": "number"},
                "description": "The desired position in [x,y,z,roll,pitch,yaw] format.",
            },
        },
        "required": ["position"],
    },
}

set_robot_pos_dual = {
    "name": "set_robot_state_dual",
    "description": "Use this function to set a desired position to the robot.",
    "parameters": {
        "type": "object",
        "properties": {
            "robot_id": {
                "type": "number",
                "description": "ID of the robot which wants to be used",
            },
            "position": {
                "type": "array",
                 "items": {"type": "number"},
                "description": "The desired position in [x,y,z,roll,pitch,yaw] format.",
            },
            "task":{
                "type": "string",
                "description": "Description what the position is set for. It needs to be one of the 2 following tasks: move, place",
            }
        },
        "required": ["position","robot_id", "task"],
    },
}

close_gripper = {
    "name": "close_gripper",
    "description": "Use this function to close the robot's gripper to grasp an object.",
    "parameters": {
        "type": "object",
        "properties": {
            "call":{
                "type": "boolean",
                "description": "True to close the gripper",
            }
        },
        "required": ["call"],    
    }
}

close_gripper_dual = {
    "name": "close_gripper_dual",
    "description": "Use this function to close the robot's gripper to grasp an object.",
    "parameters": {
        "type": "object",
        "properties": {
            "robot_id": {
                "type": "number",
                "description": "ID of the robot which wants to be used",
            },
        },
        "required": ["robot_id"],    
    }
}

open_gripper = {
    "name": "open_gripper",
    "description": "Use this function to open the the robot's gripper",
    "parameters": {
        "type": "object",
        "properties": {
            "call":{
                "type": "boolean",
                "description": "True to open the gripper",
            }
        },
        "required": ["call"],    
    }
}

open_gripper_dual = {
    "name": "open_gripper_dual",
    "description": "Use this function to open the the robot's gripper",
    "parameters": {
        "type": "object",
        "properties": {
            "robot_id": {
                "type": "number",
                "description": "ID of the robot which wants to be used",
            },
        },
        "required": ["robot_id"],    
    }
}


get_object_rect = {
    "name": "get_object_rect",
    "description": "Use this functions to find the pose/coordinate of the desired object",
    "parameters": {
        "type": "object",
        "properties": {
            "object_name":{
                "type": "string",
                "description": "Object name which needs to be tracked",
            }
        },
        "required": ["object_name"],    
    }
}

stop_loop = {
    "name": "end_task",
    "description": "Use this function if the task is done",
    "parameters": {
        "type": "object",
        "properties": {
            "end_loop":{
                "type": "boolean",
                "description": "true to end the task",
            }
        },
        "required": ["end_loop"],    
    }
}


hand_over_object ={
    "name": "hand_over_object",
    "description": "Use this function to execute an automated hand over action from robot_master to robot_slave. This function handles to set the robots in a appropriate position.",
    "parameters":{
        "type": "object",
        "properties":{
            "robot_master":{
                "type": "number",
                "description": "Robot index of the arm which grasped the object",
            },
            "robot_slave":{
                "type": "number",
                "description": "Robot index of the arm which the object shall be handed over to",
            },
            "position": {
                "type": "array",
                 "items": {"type": "number"},
                "description": "The position of the object in [x,y,z,roll,pitch,yaw] format, which shall be grasp.",
            },
        },
        "required":["robot_master", "robot_slave","position"],
    },
}


get_object_with_gemini = {
    "name": "get_object_pose",
    "description": "Use this functions to find the coordinates of the desired object",
    "parameters": {
        "type": "object",
        "properties": {
            "object_name":{
                "type": "string",
                "description": "The descriptive name of the object which the coordinates should be found",
            }
        },
        "required": ["object_name"],    
    }
}

request_image = {
    "name": "request_image",
    "description": "Use this function to recieve an image of the scene.",
    "parameters": {
        "type": "object",
        "properties": {
            "call":{
                "type": "boolean",
                "description": "True to recieve an image.",
            }
        },
        "required": ["call"],    
    }
}