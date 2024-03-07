from ultralytics import YOLO
import os
import numpy as np
import time
import json
import argparse
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# cur_time = time.strftime("%I:%M%pon%B%d,%Y")

CLASSES = {0: 'person',
 1: 'bicycle',
 2: 'car',
 3: 'motorcycle',
 4: 'airplane',
 5: 'bus',
 6: 'train',
 7: 'truck',
 8: 'boat',
 9: 'traffic light',
 10: 'fire hydrant',
 11: 'stop sign',
 12: 'parking meter',
 13: 'bench',
 14: 'bird',
 15: 'cat',
 16: 'dog',
 17: 'horse',
 18: 'sheep',
 19: 'cow',
 20: 'elephant',
 21: 'bear',
 22: 'zebra',
 23: 'giraffe',
 24: 'backpack',
 25: 'umbrella',
 26: 'handbag',
 27: 'tie',
 28: 'suitcase',
 29: 'frisbee',
 30: 'skis',
 31: 'snowboard',
 32: 'sports ball',
 33: 'kite',
 34: 'baseball bat',
 35: 'baseball glove',
 36: 'skateboard',
 37: 'surfboard',
 38: 'tennis racket',
 39: 'bottle',
 40: 'wine glass',
 41: 'cup',
 42: 'fork',
 43: 'knife',
 44: 'spoon',
 45: 'bowl',
 46: 'banana',
 47: 'apple',
 48: 'sandwich',
 49: 'orange',
 50: 'broccoli',
 51: 'carrot',
 52: 'hot dog',
 53: 'pizza',
 54: 'donut',
 55: 'cake',
 56: 'chair',
 57: 'couch',
 58: 'potted plant',
 59: 'bed',
 60: 'dining table',
 61: 'toilet',
 62: 'tv',
 63: 'laptop',
 64: 'mouse',
 65: 'remote',
 66: 'keyboard',
 67: 'cell phone',
 68: 'microwave',
 69: 'oven',
 70: 'toaster',
 71: 'sink',
 72: 'refrigerator',
 73: 'book',
 74: 'clock',
 75: 'vase',
 76: 'scissors',
 77: 'teddy bear',
 78: 'hair drier',
 79: 'toothbrush'}

def detecting_objects(DIR):
    print("Loading model (yolov8m.pt)...")
    model = YOLO("yolov8m.pt")
    # DIR = f"img_generations/img_generations_templatev0.3_lmd_plus_demo_gpt-4/run0"
    print(os.listdir(DIR))
    for dir in os.listdir(DIR):
        if os.path.isdir(os.path.join(DIR, dir)):
            for file in os.listdir(os.path.join(DIR, dir)):
                if file.endswith("0.png"):
                    cur_path = os.path.join(DIR, dir, file)
                    results = model.predict(
                        os.path.join(DIR, dir, file), 
                        save=True, 
                        imgsz=512, 
                        save_txt=True, 
                        project=f"object_detection/{DIR[16:]}", 
                        name=f"results_{dir}"
                        )


def convert_center_to_corner(bbox, img_width, img_height):
    """
    Convert YOLO format (center x, center y, width, height) to corner format
    (top-left x, top-left y, width, height).
    """
    cx, cy, w, h = bbox
    tl_x = (cx - w / 2) * img_width
    tl_y = (cy - h / 2) * img_height
    width = w * img_width
    height = h * img_height
    return [tl_x, tl_y, width, height]

def calculate_iou(boxA, boxB):
    """
    Calculate the Intersection over Union (IoU) of two bounding boxes.
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)

    boxAArea = boxA[2] * boxA[3]
    boxBArea = boxB[2] * boxB[3]

    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou


def find_key_for_value(my_dict, search_value):
    """
    Finds the first key in the dictionary that corresponds to the given value.
    
    Parameters:
    my_dict (dict): The dictionary to search through.
    search_value: The value for which the corresponding key is to be found.

    Returns:
    The key corresponding to the given value if found, otherwise None.
    """
    for key, value in my_dict.items():
        if search_value in value:
            return key
    return None

def euclidean_distance(point1, point2):

    x1, y1 = point1
    x2, y2 = point2
    distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return distance

def spatial_eval(ind, converted_detections):
    annotation = GROUND_TRUTH[ind]
    # print(annotation)
    print(converted_detections)
    obj_attributes = annotation['obj_attributes']
    converted_detections_objects = [det[0] for det in converted_detections]

    centroid = [[rect[1][0]+rect[1][2]//2, rect[1][1]+rect[1][3]//2] for rect in converted_detections]
    # print(centroid)
    # print(converted_detections_objects)
    # print(obj_attributes)
    credit = 0
    for idx in range(len(obj_attributes) - 1):
        if obj_attributes[idx] not in converted_detections_objects or obj_attributes[idx + 1] not in converted_detections_objects:
            continue
        locate_idx1 = converted_detections_objects.index(obj_attributes[idx])
        locate_idx2 = converted_detections_objects.index(obj_attributes[idx + 1])
        # print(locate_idx1, locate_idx2)
        d = euclidean_distance(centroid[locate_idx1], centroid[locate_idx2])
        relationship = []
        if (centroid[locate_idx2][1] - centroid[locate_idx1][1])/d >= np.sin(np.pi/4):
            relationship += ["above"]
        if (centroid[locate_idx2][1] - centroid[locate_idx1][1])/d <= np.sin(-np.pi/4):
            relationship += ["below"]
        if (centroid[locate_idx1][0] - centroid[locate_idx2][0])/d >= np.cos(np.pi/4):
            relationship += ["to the right of"]
        if (centroid[locate_idx1][0] - centroid[locate_idx2][0])/d <= np.cos(3*np.pi/4):
            relationship += ["to the left of"]
        # print(relationship)
        if annotation['rel_type'][idx] in relationship:
            credit += 1

    return credit/len(annotation['rel_type'])

def evaluate_image(yolo_file_path, original_prompt, ind):
    yolo_detections = []

    # Read the file and parse the data
    with open(yolo_file_path, 'r') as file:
        for line in file:
            # Split the line into components and convert them to the correct data type
            class_id, cx, cy, w, h = line.strip().split()
            class_id = int(class_id)
            cx, cy, w, h = map(float, [cx, cy, w, h])

            # Append the parsed data to yolo_detections
            yolo_detections.append((class_id, cx, cy, w, h))

    img_width, img_height = 512, 512

    target_objs = set()
    for obj, cor in original_prompt:
        # Extract the noun from the object description (e.g. "a person" -> "person")
        # obj = extract_noun(obj)
        # print(obj)
        # Convert the object name to its corresponding class ID
        # target_objs.add(find_key_for_value(CLASSES, obj))
        target_objs.add(obj)

    # print(target_objs)

    converted_detections = []
    all_detected_objects = set()
    for det in yolo_detections:
        print(det)
        class_id = CLASSES[det[0]]
        all_detected_objects.add(class_id)
        
        if class_id in target_objs:
            bbox = convert_center_to_corner(det[1:], img_width, img_height)
            converted_detections.append([class_id, bbox])
    # print(converted_detections)
    # print(all_detected_objects)
    # Evaluate Object Count Accuracy
    expected_count = len(original_prompt)
    detected_count = len(converted_detections)
    # count_accuracy = detected_count == expected_count
    count_accuracy = abs(detected_count - expected_count) / expected_count

    # Evaluate Bounding Box Accuracy
    # iou_threshold = 0.9
    all_ious = []
    # accurate_boxes = 0
    for class_id, det_box in converted_detections:
        print(det_box)
        cur_ious = []
        for _, org_box in original_prompt:
            iou = calculate_iou(det_box, org_box)
            cur_ious.append(iou)
        # print(cur_ious)
        all_ious.append(max(cur_ious))
    # print(all_ious)
            # if iou > iou_threshold:
            #     accurate_boxes += 1
            #     break

    # bbox_accuracy = accurate_boxes / expected_count

    class_id_to_name = CLASSES
    expected_objects = target_objs 
    extra_detected_objects = all_detected_objects.difference(expected_objects)

    print(extra_detected_objects)
    # extra_detected_objects_names = [class_id_to_name[obj_id] for obj_id in extra_detected_objects]

    spatial_acc = 0
    if 'spatial' in args.prompt_type:
        spatial_acc = spatial_eval(ind, converted_detections)

    if all_ious == []:
        all_ious = [0]

    # Results
    return count_accuracy, np.mean(all_ious), extra_detected_objects, spatial_acc



def extract_noun(text):
    # Tokenize the text
    tokens = word_tokenize(text)
    # Part-of-speech tagging
    tagged = pos_tag(tokens)
    # Extract nouns
    nouns = [word for word, pos in tagged if pos.startswith('NN')]
    return nouns[0]

if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--lm", default='gpt-4', type=str)
    parser.add_argument("--template_version", default='v0.1', type=str)
    parser.add_argument("--prompt_type", default='lmd_spatial', type=str)
    parser.add_argument("--sdxl", default=True)
    args = parser.parse_args()

    if args.sdxl:
        DIR = f"img_generations/img_generations_template{args.template_version}_lmd_plus_{args.prompt_type}_{args.lm}_sdxl_0.3/run0"
    else:
        DIR = f"img_generations/img_generations_template{args.template_version}_lmd_plus_{args.prompt_type}_{args.lm}/run0"

    # Detecting objects from synthetic images
    detecting_objects(DIR)

    # Evaluate the detected objects
    if args.prompt_type.startswith("lmd"):
        prompts = json.load(open(f"cache/cache_{args.prompt_type.replace('lmd_', '')}_{args.template_version}_{args.lm}.json"))
    else:
        prompts = json.load(open(f"cache/cache_demo_{args.template_version}_{args.lm}.json")) 
    if "spatial" in args.prompt_type:
        GROUND_TRUTH = json.load(open("data/new_sample_3.json"))

    extra_miss_ratio = []
    ious = []
    spatial_accs = []


    for ind, (key, value) in enumerate(prompts.items()):
        original_prompt = eval(value[0].split("Background prompt:")[0])
        yolo_path = f"object_detection/{DIR[16:]}/results_{ind}/labels/img_0.txt"
        try:
            print("=================================")
            eval_result = evaluate_image(yolo_path, original_prompt, ind)
            print(f"extra/miss ratio: {eval_result[0]}, mean_iou: {eval_result[1]}, extra_detected_objects: {eval_result[2]}, spatial accuracy: {eval_result[3]}")
            print("=================================")
            extra_miss_ratio.append(eval_result[0])
            ious.append(eval_result[1])
            spatial_accs.append(eval_result[3])
        except:
            extra_miss_ratio.append(0)
            ious.append(0)
            spatial_accs.append(0)
            pass
    
    print(f"Extra/Miss Ratio: {np.mean(extra_miss_ratio)}")
    print(f"Mean IoU: {np.mean(ious)}")
    print(f"Spatial Accuracy: {np.mean(spatial_accs)}")

    eval_result = {
        "extra_miss_ratio": np.mean(extra_miss_ratio),
        "mean_iou": np.mean(ious),
        "spatial_accuracy": np.mean(spatial_accs)
    }
    json.dump(eval_result, open(f"results/evaluation_result_{DIR[16:-5]}.json", "w"), indent=2)
        # break
