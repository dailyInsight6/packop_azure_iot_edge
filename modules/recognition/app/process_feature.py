import os, sys
import datetime
import threading
import numpy as np
import csv

from manage_data import insert_data, get_connection, close_connection

base_dir = "temp/"
threshold_prob = 0.7

class FeatureProcessor(threading.Thread):
    def __init__(self, file_name: str, command: str, feature_list :list = [], transaction_id: str = ""):
        threading.Thread.__init__(self)
        self.file_name = file_name
        self.command = command
        self.feature_list = feature_list
        self.transaction_id = transaction_id

    def run(self):
        try:
            file_dir = base_dir + self.file_name
            
            if self.command == "get":
                
                # Get feautres    
                features = self.get_features(self.feature_list)
                # Open feature file
                feature_file = open(file_dir, mode='a', newline="")
                # Write features into the file
                writer = csv.writer(feature_file, delimiter=',')
                writer.writerow(features)

            elif self.command == "save":
                # Summarize features
                feature_summary = self.calc_feature_list(file_dir)
           
                #   Update Stranger
                data_dict = [
                                self.transaction_id, # "transaction_id"
                                int(feature_summary[0]), # "age"
                                int(feature_summary[1]), # "gender"
                                int(feature_summary[2]), # "moustache"
                                int(feature_summary[3]), # "beard"
                                int(feature_summary[4]), # "sideburns"
                                int(feature_summary[5]), # "glasses"
                                int(feature_summary[6]), # "mask"
                                int(feature_summary[7]), # "headwear"
                                int(feature_summary[8]), # "bald"
                                int(feature_summary[9]) # "hair_color" 
                            ]
                                            
                con = get_connection()
                insert_data(con, "stranger", data_dict)
                close_connection(con)

                # Create new file
                new_dir = base_dir + "feature_summary.csv"
                new_feature_file = open(new_dir, mode='a', newline="")
                
                # Write the summary on the file
                writer = csv.writer(new_feature_file, delimiter=',')
                writer.writerow(feature_summary)

                # Delete old data
                os.remove(file_dir)

        except Exception as e:
            print('Feature Processor::exited run loop. Exception - '+ str(e), file=sys.stderr)

    def close(self):
        print('Feature Processor is killed by the request', file=sys.stderr)

    # Do not use this method. 
    def write_feature_guesses(self, filename: str, feature_guesses: []):
        with open(filename, mode='a', newline="") as feature_file:
            writer = csv.writer(feature_file, delimiter=',')
            writer.writerow(feature_guesses)

    def calc_feature_list(self, filename: str):
        features = np.genfromtxt(filename, delimiter=',') # , skip_header=1
        averages = np.mean(features, axis=0)
        feature_list = np.rint(averages)
        return feature_list

    def get_features(self, feature_list):
        result = []
        
        if len(feature_list) > 0:
            # Age
            result.append(feature_list['age'])
            
            # Gender:  male: 0 / female: 1
            result.append(self.compare(feature_list['gender'], "male"))

            # Facial_hair(mustache):    no moustache: 0 / moustache: 1
            result.append(self.verify(feature_list['facialHair'], "moustache"))

            # facial_hair(beard):     no beard : 0 / beard : 1
            result.append(self.verify(feature_list['facialHair'], "beard"))

            # facial_hair(sideburns):    no sideburns : 0 / sideburns : 1
            result.append(self.verify(feature_list['facialHair'], "sideburns"))

            # accessories: glasses / mask  / headwear 
            accessory_list = ["glasses", "mask", "headwear"]
            index = 0
            if len(feature_list['accessories']) > 0:
                for i in range(len(feature_list['accessories'])):
                    for j in range(index, len(accessory_list)):
                        if feature_list['accessories'][i]["type"] == accessory_list[j]:
                            result.append(self.verify(feature_list['accessories'][i], "confidence"))
                            index = j + 1
                            break
                        result.append(0)
                for j in range(index, len(accessory_list)):
                    result.append(0)
            else:
                for j in range(len(accessory_list)):
                    result.append(0)
            
            # hair: bald    no bald : 0 / bald : 1
            result.append(self.verify(feature_list['hair'], "bald"))

            # hairColor :  "brown": 0, "blond": 1, "black": 2, "other": 3, "gray": 4, "red": 5
            color_list = {"brown": 0, "blond": 1, "black": 2, "other": 3, "gray": 4, "red": 5}
            result.append(self.pick_best(feature_list['hair']['hairColor'], "confidence", "color", color_list))
        else:
            # Default data in case of not getting face features
            result = [9,9,9,9,9,9,9,9,9,9]

        return result

    
    def compare(self, target: str, value: str):
        if target == value:
            return 1
        else:
            return 0

    def verify(self, target: dict, key: str):
        if key not in target:
            return 0
        else:
            if target[key] > threshold_prob:
                return 1
            else:
                return 0

    def pick_best(self, target: list, standard: str, target_value: str, value_list: list):
        confidence = []
        for i in range(len(target)):
            confidence.append(target[i][standard])
        return value_list[target[confidence.index(max(confidence))][target_value]]