import time
import os
import sys
import cognitive_face as CF
import keymanager

from PIL import Image
from process_feature import FeatureProcessor
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient

face_api_key = keymanager.MODULE_FACE_API_KEY
face_api_url = keymanager.MODULE_FACE_API_URL
face_group_id = keymanager.MODULE_FACE_GROUP_ID
package_api_key = keymanager.MODULE_PACKAGE_API_KEY
package_api_project_id = keymanager.MODULE_PACKAGE_API_PROJECT_ID
package_api_iteration_name = keymanager.MODULE_PACKAGE_API_ITERATION_NAME
package_api_endpoint = keymanager.MODULE_PACKAGE_API_ENDPOINT

face_features = 'age,gender,hair,facialHair,accessories'

def get_width(people_list):
    pre_value = 0
    biggest_value = 0
    index = 0
    best_index = 0
    for faceDictionary in people_list:
        rect = faceDictionary['faceRectangle']
        width = rect['width']
        
        if pre_value == 0 or biggest_value == 0 or (biggest_value < width):
            biggest_value = width
            best_index = index

        pre_value = width
        index += 1
    return int(biggest_value), best_index

def recognize_face(faces):
    for face in faces:
        if len(face['candidates'])>0:
            return True

def predict_image(img, role):
    start_time = time.time()
    result = []
    img = Image.open(img)
    img.save("frame.jpg")
    
    with open("frame.jpg", mode="rb") as frame:
        
        if role == "person":
            # Connectiong to the Face API service
            subscription_key = face_api_key
            base_url = face_api_url
            person_group_id = face_group_id
            CF.BaseUrl.set(base_url)
            CF.Key.set(subscription_key)
            
            detected_people = CF.face.detect(frame, attributes=face_features)     
            
            if len(detected_people)>0:
               
                face_ids = [d['faceId'] for d in detected_people]
                faces = CF.face.identify(face_ids, person_group_id)
  
                biggest_width, index = get_width(detected_people)
                
                if(recognize_face(faces)):
                    result.append("member")
                else:
                    processor = FeatureProcessor("feature_temp.csv", "get", detected_people[index]["faceAttributes"])
                    processor.start()
                    result.append("stranger")
                
                result.append(biggest_width)
            else:
                result.append("nothing")
                result.append(0)
            
            end_time = time.time()
            elasped_time = str(int((end_time-start_time) * 1000)) + " ms"

        elif role == "package":
            # Connectiong to the Custom Vision service
            prediction_key = package_api_key
            project_id = package_api_project_id
            iteration_name = package_api_iteration_name
            endpoint = package_api_endpoint
            predictor = CustomVisionPredictionClient(prediction_key, endpoint=endpoint)
                    
            results = predictor.detect_image(project_id, iteration_name, frame)
            max_prob = 0.77
            tag = ""
            
            package_counter = 0
            
            for prediction in results.predictions:
                if prediction.probability > max_prob:
                    package_counter += 1
                    tag = prediction.tag_name
            
            if tag != "" and tag.lower() == "package":
                result.append("package")
                result.append(package_counter)
            else:
                result.append("nothing")
                result.append(0)
            end_time = time.time()
            elasped_time = str(int((end_time-start_time) * 1000)) + " ms"
        return result
