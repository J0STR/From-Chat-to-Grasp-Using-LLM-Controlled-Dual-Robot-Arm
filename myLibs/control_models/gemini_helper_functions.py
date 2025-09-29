from multiprocessing.synchronize import Event as EventClass
from multiprocessing.sharedctypes import Synchronized, SynchronizedArray
import json
import numpy as np
from PIL import Image
import base64
from dataclasses import dataclass
from google import genai
from google.genai import types
from typing import List
import io

from myLibs.yolo.yolo_functions import crop_image, uncrop_rect, uncrop_polygon
from myLibs.yolo.yolo_classes import YoloPromptSegmenter
from myLibs.control_models.gemini_classes import API_KEY

@dataclass
class SegmentationItem:
    name: str
    mask_points: np.ndarray
    height: float | None = None
    pose_6d: np.ndarray | None = None

def get_structured_segmentation(image: Image.Image, object_description: str)->SegmentationItem | None:

    height = image.size[1]
    width = image.size[0]
    image.thumbnail([1024, 1024], Image.Resampling.LANCZOS)
    prompt = f"""
    Give the segmentation masks for the following object: '{object_description}'.
    Output a JSON list of segmentation masks where each entry contains the 2D
    bounding box in the key "box_2d", the segmentation mask in key "mask", and
    the text label in the key "label". Use descriptive labels.
    """

    client = genai.Client(api_key=API_KEY)
    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0) # set thinking_budget to 0 for better results in object detection
        )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image], # Pillow images can be directly passed as inputs (which will be converted by the SDK)
        config=config
    )
    
    try:
        items_json = json.loads(parse_json(response.text))
        items = []
        for i, item in enumerate(items_json):
            points_of_mask = None
            name = item['label']
            box = item["box_2d"]
            y0 = int(box[0] / 1000 * height)
            x0 = int(box[1] / 1000 * width)
            y1 = int(box[2] / 1000 * height)
            x1 = int(box[3] / 1000 * width)
            
            if y0 >= y1 or x0 >= x1:
                continue

            png_str = item["mask"]
            if not png_str.startswith("data:image/png;base64,"):
                continue
            png_str = png_str.removeprefix("data:image/png;base64,")
            mask_data = base64.b64decode(png_str)
            mask = Image.open(io.BytesIO(mask_data))
            mask = mask.resize((x1 - x0, y1 - y0), Image.Resampling.BILINEAR)
            mask_array = np.array(mask)

            # Create overlay for the mask
            
            points_of_mask = None
            for y in range(y0, y1):
                for x in range(x0, x1):
                    if mask_array[y - y0, x - x0] > 128:  # Threshold for mask
                        point = np.array([x, y])
                        if points_of_mask is None:
                            points_of_mask = point
                        else:
                            points_of_mask = np.vstack((points_of_mask,point))
            items.append(SegmentationItem(name=name, mask_points=points_of_mask))

        return items[0]
    except:
        return None



def parse_json(json_output: str):
    # Parsing out the markdown fencing
    lines = json_output.splitlines()
    for i, line in enumerate(lines):
        if line == "```json":
            json_output = "\n".join(lines[i+1:])  # Remove everything before "```json"
            output = json_output.split("```")[0]  # Remove everything after the closing "```"
            break  # Exit the loop once "```json" is found

    return output

def get_object_rect(segmenter: YoloPromptSegmenter, frame, object_name):
    name_list = [object_name]
    segmenter.change_object(name_list)    
    rect = None
    cropped_img, roi_x, roi_y = crop_image(frame)
    results = segmenter.segment(cropped_img[:,:,:3])
    rect, xy_polygon = segmenter.get_rect_from_result()
    if rect is None:
        return None , None
    rect = uncrop_rect(rect,roi_x,roi_y)
    polylines = xy_polygon[0]
    polylines = uncrop_polygon(polylines, roi_x, roi_y)
    return rect, polylines

def set_robot_state(robot_id, position, task):
    return robot_id, position, task

def gripper_tool(robot_id):
    return robot_id

def hand_over_object(robot_master, robot_slave, position):
    return robot_master, robot_slave

def wait_processes_to_init(shared_data,stop_runtime: EventClass):
    while (
        # shared_data.frame_POV is None or
        not stop_runtime.is_set() and
        (shared_data.frame is None
        or shared_data.current_state is None
        or shared_data.current_gripper_state is None)
    ):
        pass

def wait_processes_to_init_dual_setup(shared_data,stop_runtime,status_robo_1: Synchronized, status_robo_2: Synchronized):
    while (
        # shared_data.frame_POV is None or
        not stop_runtime.is_set() and
        (shared_data.frame is None
        or status_robo_1.value != 0
        or status_robo_2.value != 0)
    ):
        pass