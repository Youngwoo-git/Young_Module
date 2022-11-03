import os
import json, cv2, shutil


def reset_dataset(dir_list):
    for d in dir_list:
        if os.path.isdir(d):
            shutil.rmtree(d)
            os.mkdir(d)
        else:
            os.mkdir(d)
            
def norm_xyxy2xywh(coord, ori_h, ori_w):
    x_c = abs((coord[0][0] + coord[1][0])/2)
    y_c = abs((coord[0][1] + coord[1][1])/2)
    w = abs(coord[1][0] - coord[0][0])
    h = abs(coord[1][1] - coord[0][1])

    return x_c/ori_w, y_c/ori_h, w/ori_w, h/ori_h