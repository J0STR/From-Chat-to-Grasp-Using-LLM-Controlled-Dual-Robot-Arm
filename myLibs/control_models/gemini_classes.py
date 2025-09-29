from pydantic import BaseModel, Field
from typing import List
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from google.genai.errors import ServerError

from myLibs.control_models.gemini_function_declarations_json import *

API_KEY = '' ### Enter API-Key Here
    
class GeminiChatDual:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.tools = types.Tool(function_declarations=[get_object_with_gemini,
                                                       set_robot_pos_dual,
                                                       open_gripper_dual,
                                                       close_gripper_dual,
                                                       hand_over_object,
                                                       stop_loop,])
        self.config = types.GenerateContentConfig(tools=[self.tools],temperature=0.0)
        self.model = "gemini-2.5-flash"
        
        self.chat = None

    def start_chat(self):
        self.chat = self.client.chats.create(model=self.model,
                           config=self.config
                           )

    def message(self,content):
        while True:
            try:
                response = self.chat.send_message(content)
                break
            except ClientError as e:
                print(e)
            except ServerError as e:
                print(e)
            finally:
                pass
                
        return response

# TODO: this is the correct way to 
# give the model the response: https://ai.google.dev/gemini-api/docs/function-calling?example=meeting#step_3_execute_set_light_values_function_code
# look step 4
# function_response_part = types.Part.from_function_response(
#     name=function_call.name,
#     response={f"Result": object_pose},
# )
# content.append(function_response_part)