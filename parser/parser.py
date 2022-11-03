import os, json, shutil
import cv2
from tqdm import tqdm
from glob import glob
from omegaconf import DictConfig, OmegaConf
import random
import numpy as np
import argparse
import threading

import sys
sys.path.append("../common/")
from module import reset_dataset, norm_xyxy2xywh

class DataOrganizer():
    def __init__(self, opt):
        
        save_dir = opt.save_dir
        
        if opt.type == "YOLOP":
            self.new_img_dir = os.path.join(save_dir, "Images")
            self.new_label_dir = os.path.join(save_dir, "Labels")
            self.seg_dir = os.path.join(save_dir, "Seg")

            parsings = [save_dir, self.new_img_dir, self.new_label_dir, self.seg_dir]
            reset_dataset(parsings)
            
            self.blank = np.zeros((opt.height, opt.width, 3), dtype=np.uint8)
            
        elif opt.type == "YOLO":
            self.train_dir = os.path.join(save_dir, "train")
            self.val_dir = os.path.join(save_dir, "val")
            
            parsings = [save_dir, self.train_dir, self.val_dir]
            reset_dataset(parsings)
            
            cfg = OmegaConf.load(opt.config)
            self.train_obj_list = cfg.names
            self.train_obj_dict = {}

            for i, obj_name in enumerate(self.train_obj_list):
                self.train_obj_dict[obj_name] = i
        
        self.total_img_list = []
        self.datatype = opt.type
        
        
                
    def find_labeled_data(self, base_source):
        tasks = next(os.walk(base_source))[1]
        
        for task in tasks:
            source = os.path.join(base_source, task)
            dir_list = next(os.walk(source))[1]
            dir_list.sort()
            
            for f_i, d in enumerate(dir_list):
                label_txt_path = os.path.join(source, d, "label.txt")

                if not os.path.isfile(label_txt_path):
                    continue
                with open(label_txt_path) as f:
                    label_count = int(f.readlines()[0])


                img_dir = os.path.join(source, d)

                img_list = glob(os.path.join(img_dir, "*.png"))
                img_list = sorted(img_list, key = lambda x: x.split("-")[-2])[:label_count-(f_i*500)]
                self.total_img_list += img_list
        return self.total_img_list
                
    def organize_data(self, total_img_list, thread_count = 10, split_list = ["val", "train"]):
        random.shuffle(total_img_list)
        split_amount = int(len(total_img_list)*0.1)
        
        if self.datatype == "YOLOP":
            for split_key in split_list:
                self.img_subdir = os.path.join(self.new_img_dir, split_key)
                self.label_subdir = os.path.join(self.new_label_dir, split_key)
                self.seg_subdir = os.path.join(self.seg_dir, split_key)

                subdirs = [self.img_subdir, self.label_subdir, self.seg_subdir]
                reset_dataset(subdirs)

                if split_key == "train":
                    transfer_img_list = total_img_list[:-split_amount]

                    thread_count = thread_count
                    file_unit = len(transfer_img_list)//thread_count

                    # file_unit
                    for i in range(thread_count-1):
                        thread = threading.Thread(target=self.create_yolop_dataset, args = (transfer_img_list[(i)*file_unit:(i+1)*file_unit],))
                        thread.start()
                    thread = threading.Thread(target=self.create_yolop_dataset, args = (transfer_img_list[(i+1)*file_unit:],))
                    thread.start()

                elif split_key == "val":
#                     continue
                    transfer_img_list = total_img_list[-split_amount:]
                    self.create_yolop_dataset(transfer_img_list)
            
        elif self.datatype == "YOLO":
            for split_key in split_list:
                if split_key == "train":

                    self.img_subdir = os.path.join(self.train_dir, "images")
                    self.label_subdir = os.path.join(self.train_dir, "labels")
                    subdirs = [self.img_subdir, self.label_subdir]
                    reset_dataset(subdirs)

                    transfer_img_list = total_img_list[:-split_amount]

                    thread_count = thread_count
                    file_unit = len(transfer_img_list)//thread_count

                    for i in range(thread_count-1):
                        thread = threading.Thread(target=self.create_yolo_dataset, args = (transfer_img_list[(i)*file_unit:(i+1)*file_unit],))
                        thread.start()
                    thread = threading.Thread(target=self.create_yolo_dataset, args = (transfer_img_list[(i+1)*file_unit:],))
                    thread.start()

                elif split_key == "val":
                    continue
                    self.img_subdir = os.path.join(self.val_dir, "images")
                    self.label_subdir = os.path.join(self.val_dir, "labels")
                    subdirs = [self.img_subdir, self.label_subdir]
                    reset_dataset(subdirs)

                    transfer_img_list = total_img_list[-split_amount:]
                    self.create_yolo_dataset(transfer_img_list)

    def create_yolop_dataset(self, img_list):
        for img_path in tqdm(img_list):
            json_path = img_path.replace(".png", ".json")
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
            except:
                continue
            
            shutil.copy(img_path, self.img_subdir)
            shutil.copy(json_path, self.label_subdir)

            seg = self.blank.copy()
            seg_path = os.path.join(self.seg_subdir, os.path.basename(json_path).replace(".json", ".png"))

            obj_list = data["shapes"]
            points = []
            for obj in obj_list:
                if obj["label"] == "road":
                    points = obj["points"]
                    break
            if len(points):
                seg = cv2.fillPoly(seg, [np.array(points, np.int32)], (255,255,255))
            cv2.imwrite(seg_path, seg)
            f.close()
            
            
    def create_yolo_dataset(self, img_list):
        for img_path in tqdm(img_list):
            bname = os.path.basename(img_path)
            new_label_path = os.path.join(self.label_subdir, bname).replace(".png", ".txt")
            img = cv2.imread(img_path)

            try:
                ori_h, ori_w = img.shape[:2]
            except:
#                 print(img_path)
                continue
            ori_h, ori_w = img.shape[:2]
            label_path = img_path.replace(".png", ".json")
            obj_for_label_list = []

            try:
                with open(label_path, 'r') as f:
                    data = json.load(f)
                obj_list = data["shapes"]
            except:
                print(img_path)
                continue
                
            shutil.copy(img_path, self.img_subdir)
            
            for obj in obj_list:
                if obj["label"] in self.train_obj_list:
                    ori_pts = obj["points"]
                    try:
                        pt0 = ori_pts[0][0]
                        pt1 = ori_pts[1][0]
                        pt2 = ori_pts[0][1]
                        pt3 = ori_pts[1][1]
                    except:
#                         print(img_path)
                        continue
                    x_c, y_c, w, h = norm_xyxy2xywh(ori_pts, ori_h, ori_w)
                    with open(new_label_path, "a") as l:
                        lbl_text = "{} {} {} {} {}\n".format(int(self.train_obj_dict[obj["label"]]), x_c, y_c, w, h)
                        l.write(lbl_text)
            
            f.close()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, default="/mnt/vitasoft/2022_Patrasche/Images_label_processing/", help="source directory")
    parser.add_argument('--save-dir', type=str, default="/home/ubuntu/workspace/ywshin/personal_snippet/parser/dataset", help="save directory")
    parser.add_argument('--config', type=str, default="config/patrasche.yaml", help="source directory")
    parser.add_argument('--width', type=int, default=1920, help="image width")
    parser.add_argument('--height', type=int, default=1088, help="image height")
    parser.add_argument('--thread', type=int, default=10, help="number of threads")
    parser.add_argument('--type', type=str, required = True, choices=['YOLOP', 'YOLO'])
    opt = parser.parse_args()
    
    organizer = DataOrganizer(opt)
    
    total_img_list = organizer.find_labeled_data(base_source = opt.source)
    
    print("There are {} files to process".format(len(total_img_list)))
    
    organizer.organize_data(total_img_list, thread_count = opt.thread, split_list = ["val", "train"])
