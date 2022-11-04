import imagehash
from glob import glob
from tqdm import tqdm
from PIL import Image
import cv2, os, json, shutil

import datetime

import subprocess, ffmpy

def center_crop(img):
    h,w = img.shape[:2]
    crop_h, crop_w = h//4, w//4
    
    return img[crop_h:h-crop_h, crop_w:w-crop_w]

def reset_dir(save_dir):
    if os.path.isdir(save_dir):
        shutil.rmtree(save_dir)
        os.mkdir(save_dir)
    else:
        os.mkdir(save_dir)

def frame_to_hash(vid_list, json_dir = "dhkang/" , reshape = (1280, 720)):
    for vid_path in vid_list:
        json_path = os.path.join(json_dir, os.path.basename(vid_path).split(".")[0]+".json")
        try:
            cap = cv2.VideoCapture(vid_path)
            width, height = int(cap.get(3)), int(cap.get(4))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count/fps

        #     reset_dir(clip_dir)
            hash_dict = {}
            for i in tqdm(range(frame_count)):
                ret, frame = cap.read()
                
                if frame is None:
                    hash_dict[i] = None
                    continue
                
                if reshape[0] < width or reshape[1] < height:
                    frame = cv2.resize(frame, (reshape[0], reshape[1]))
                    
                hash_dict[i] = str(imagehash.phash(Image.fromarray(center_crop(frame))))
                
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(hash_dict, f, ensure_ascii=False, indent=4)
            f.close()
        except Exception as e:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(str(e), f, ensure_ascii=False, indent=4)
            f.close()
            
def load_hash(json_path):
    with open(json_path, 'r') as file:
        data = json.load(file)
    if data is dict:
        hashes = [imagehash.hex_to_hash(d) if d is not None else d for d in asdf.values()]
        
    if data is list:
        hashes = [imagehash.hex_to_hash(d) if d is not None else d for d in asdf]
    return hashes
    
        
def get_thumbnails(vid_path, clip_dir, threshold = 9, min_phase = 3, reshape = []):
    cap = cv2.VideoCapture(vid_path)
    width, height = int(cap.get(3)), int(cap.get(4))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count/fps
    
    reset_dir(clip_dir)
    
    min_frames = int(min_phase*fps)

    for i in tqdm(range(frame_count)):
        ret, frame = cap.read()
        if i == 0:
            prev_hash = imagehash.phash(Image.fromarray(center_crop(frame)))
        elif i%min_frames == 0:
            curr_hash = imagehash.phash(Image.fromarray(center_crop(frame)))
            h_dist = prev_hash - curr_hash
            if h_dist > threshold:
                if reshape:
                    frame = cv2.resize(frame, (reshape[0], reshape[1]))
                cv2.imwrite(os.path.join(clip_dir, "{:08d}.png".format(i)), frame)
            prev_hash = curr_hash
            
    return fps, frame_count

def get_hashs(clip_dir):
    hash_img_list = glob(os.path.join(clip_dir, "*.png"))
    hash_img_list.sort()
    hash_list = []
    for img_path in hash_img_list:
        img = cv2.imread(img_path)
        img_hash = imagehash.phash(Image.fromarray(center_crop(img)))
        hash_list.append(img_hash)
        
    return hash_img_list, hash_list

def calc_match(ori_hash_list, hl_hash_list, threshold, max_hl):
    
    init_min_thres = threshold
    process = True
    cnt = 0
    
    while(process):
    
        final_dict = {}
        prev_point = 0

        for idx, hl in tqdm(enumerate(hl_hash_list)):
#             min_val = threshold
            min_val = init_min_thres - 2*cnt
            match_val_list = []
            for jdx, ori in enumerate(ori_hash_list):
                dist = ori-hl        
                if dist < min_val:
                    min_val = dist
                    match_val_list = [jdx]

                elif dist == min_val:
                    match_val_list.append(jdx)

            if len(match_val_list):        
                final_dict[idx] = match_val_list[0]
                prev_point = match_val_list[0]

    #         if len(match_val_list) == 1:        
    #             final_dict[idx] = match_val_list[0]
    #             prev_point = match_val_list[0]

    #         elif len(match_val_list) > 1:
    #             for v in match_val_list:
    #                 if v > prev_point:
    #                     final_dict[idx] = v
    #                     prev_point = v
    
        if len(final_dict) < max_hl or (init_min_thres - 2*cnt -2) < 0:
            process = False
        else:
            cnt += 1
    return final_dict

def frames_to_time(frame, fps):
    sec = frame//fps
    return str(datetime.timedelta(seconds=sec))


def get_int_list(str_list):
    int_list = [int(s) for s in str_list]
    int_list.sort()
    return int_list
        

def get_return_dict(final_dict, ori_hash_img_list, hl_hash_img_list, ori_last_frame, hl_last_frame, ori_fps, hl_fps):
    clip_list = []
    
    keys = list(final_dict.keys())
    values = list(final_dict.values())
    
    int_keys = get_int_list(keys)
    int_values = get_int_list(values)
    
    cnt = 1
    
    for idx in range(len(keys)):
        
        data_dict = {}
        
        ori_start = int(os.path.basename(ori_hash_img_list[values[idx]]).split(".")[0])
        hl_start = int(os.path.basename(hl_hash_img_list[keys[idx]]).split(".")[0])
        
        ori_end_idx = int_values.index(int(values[idx])) + 1
        hl_end_idx = int_keys.index(int(keys[idx])) + 1
        
        if ori_end_idx != len(values):
            ori_end = int(os.path.basename(ori_hash_img_list[int_values[ori_end_idx]]).split(".")[0])
        else:
            ori_end = int(ori_last_frame)
            
            
        if hl_end_idx != len(keys):
            hl_end = int(os.path.basename(hl_hash_img_list[int_keys[hl_end_idx]]).split(".")[0])
        else:
            hl_end = int(hl_last_frame)
            
#         if idx+1 == len(keys):
#             ori_end = int(ori_last_frame)
#             hl_end = int(hl_last_frame)
#         else:
#             ori_end = int(os.path.basename(ori_hash_img_list[values[idx+1]]).split(".")[0])
#             hl_end = int(os.path.basename(hl_hash_img_list[keys[idx+1]]).split(".")[0])
            
        ori_duration = ori_end - ori_start
        hl_duration = hl_end - hl_start
        
        if ori_duration == 0 or hl_duration == 0:
            continue
        
#         ori_end -= 1
#         hl_end -= 1      
        
        
        data_dict["json_id"] = "{:08d}".format(cnt)
        
        data_dict["ori_start_time"] = frames_to_time(ori_start, ori_fps)
        data_dict["ori_end_time"] = frames_to_time(ori_end, ori_fps)
        data_dict["ori_duration_time"] = frames_to_time(ori_duration, ori_fps)
        
        data_dict["hl_start_time"] = frames_to_time(hl_start, hl_fps)
        data_dict["hl_end_time"] = frames_to_time(hl_end, hl_fps)
        data_dict["hl_duration_time"] = frames_to_time(hl_duration, hl_fps)
    
        clip_list.append(data_dict)
        
        cnt += 1
    
    return clip_list


def clear_dir(clip_dir):
    if os.path.isdir(clip_dir):
        shutil.rmtree(clip_dir)
        
        
def single_match(data_dict):

    thres = data_dict["thres"]
    min_ph = data_dict["min_ph"]
    ori_path = data_dict["ori_path"]
    hl_path = data_dict["hl_path"]
    save_dir = data_dict["save_dir"]
    target_size = data_dict["target_size"]
    which_larger = data_dict["which"]
    max_hl = data_dict["max_hl"]

    ori_save_dir = os.path.join(save_dir, os.path.basename(ori_path).split(".")[0])
    hl_save_dir = os.path.join(save_dir, os.path.basename(hl_path).split(".")[0])

    if which_larger == "ori":
        ori_fps, ori_last_frame = get_thumbnails(ori_path, ori_save_dir, threshold = thres + 1, min_phase = min_ph, reshape = target_size)
        hl_fps, hl_last_frame = get_thumbnails(hl_path, hl_save_dir, threshold = thres + 1, min_phase = min_ph)
    elif which_larger == "hl":
        ori_fps, ori_last_frame = get_thumbnails(ori_path, ori_save_dir, threshold = thres + 1, min_phase = min_ph)
        hl_fps, hl_last_frame = get_thumbnails(hl_path, hl_save_dir, threshold = thres + 1, min_phase = min_ph, reshape = target_size)
    else:
        ori_fps, ori_last_frame = get_thumbnails(ori_path, ori_save_dir, threshold = thres + 1, min_phase = min_ph)        
        hl_fps, hl_last_frame = get_thumbnails(hl_path, hl_save_dir, threshold = thres + 1, min_phase = min_ph)

    ori_hash_img_list, ori_hash_list = get_hashs(ori_save_dir)    
    hl_hash_img_list, hl_hash_list = get_hashs(hl_save_dir)  

    result_dict = calc_match(ori_hash_list, hl_hash_list, thres, max_hl)

    return_dict = get_return_dict(result_dict, ori_hash_img_list, hl_hash_img_list, ori_last_frame, hl_last_frame, ori_fps, hl_fps)

    clear_dir(ori_save_dir)
    clear_dir(hl_save_dir)
        
    return return_dict

    
def multi_match(data_dict, ori_fps, ori_last_frame):

    thres = data_dict["thres"]
    min_ph = data_dict["min_ph"]
    ori_path = data_dict["ori_path"]
    hl_path = data_dict["hl_path"]
    save_dir = data_dict["save_dir"]
    target_size = data_dict["target_size"]
    which_larger = data_dict["which"]
    max_hl = data_dict["max_hl"]

    ori_save_dir = os.path.join(save_dir, os.path.basename(ori_path).split(".")[0])
    hl_save_dir = os.path.join(save_dir, os.path.basename(hl_path).split(".")[0])
    
    hl_fps, hl_last_frame = get_thumbnails(hl_path, hl_save_dir, threshold = thres + 1, min_phase = min_ph, reshape = target_size)
    
    ori_hash_img_list, ori_hash_list = get_hashs(ori_save_dir)    
    hl_hash_img_list, hl_hash_list = get_hashs(hl_save_dir)  

    result_dict = calc_match(ori_hash_list, hl_hash_list, thres, max_hl)

    return_dict = get_return_dict(result_dict, ori_hash_img_list, hl_hash_img_list, ori_last_frame, hl_last_frame, ori_fps, hl_fps)
        
    return return_dict
    

# 아래는 비디오 메타데이터 산출 및 연산 전/후 처리
    
def video_metadata(file_path):
    meta_dict = {}
    
    ext_meta = ffmpy.FFprobe(
        inputs={file_path: None},
        global_options=[
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams -select_streams v',
            '-show_entries format=filename',
        ]
    ).run(stdout=subprocess.PIPE)

    meta = json.loads(ext_meta[0].decode('utf-8'))
    
    video_stream = meta['streams'][0]
    
    meta_dict['file_name'] = os.path.basename(meta['format']['filename'])
    meta_dict['video_name'] = meta_dict['file_name'].split('.')[0]
    meta_dict['ext_video'] = meta_dict['file_name'].split('.')[1]
    meta_dict['category'] = meta_dict['file_name'].split('.')[0].split('-')[0]
    
#     numerator = int(video_stream['r_frame_rate'].split('/')[0])
#     denominator = int(video_stream['r_frame_rate'].split('/')[1])
#     meta_dict['fps'] = (numerator / denominator)
    
    video = cv2.VideoCapture(file_path)
    meta_dict['fps'] = video.get(cv2.CAP_PROP_FPS)
    
    meta_dict['width'] = video_stream['width']
    meta_dict['height'] = video_stream['height']
    
    return meta_dict


def data_dict(ori_path, hl_path, max_hl, thres=9, min_ph=3):
    data_dict = {}
    
    data_dict['thres'] = thres
    data_dict['min_ph'] = min_ph
    data_dict["max_hl"] = max_hl
    
    data_dict['ori_path'] = os.path.abspath(ori_path)
    data_dict['hl_path'] = os.path.abspath(hl_path)
    
    save_dir = os.path.join(os.getcwd(), 'save_dir')
    os.makedirs(save_dir, exist_ok=True)
    data_dict['save_dir'] = os.path.abspath(save_dir)
    
    ori_meta = video_metadata(ori_path)
    hl_meta = video_metadata(hl_path)
    
    ori_resolution = ori_meta['width'] * ori_meta['height']
    hl_resolution = hl_meta['width'] * hl_meta['height']
    
    if ori_resolution < hl_resolution:
        data_dict['target_size'] = [ori_meta['width'], ori_meta['height']]
        data_dict['which'] = 'hl'
    elif ori_resolution > hl_resolution:
        data_dict['target_size'] = [hl_meta['width'], hl_meta['height']]
        data_dict['which'] = 'ori'
    else:
        data_dict['target_size'] = [ori_meta['width'], ori_meta['height']]
        data_dict['which'] = None
    
    data_dict['ext_org'] = ori_meta['ext_video']
    data_dict['ext_hl'] = hl_meta['ext_video']
    
    data_dict['category'] = ori_meta['category']
    
    data_dict['ori_fps'] = ori_meta['fps']
    data_dict['hl_fps'] = hl_meta['fps']
    
    ori_width = ori_meta['width']
    ori_height = ori_meta['height']
    hl_width = hl_meta['width']
    hl_height = hl_meta['height']
    
    data_dict['ori_resolution'] = f'{ori_width}x{ori_height}'
    data_dict['hl_resolution'] = f'{hl_width}x{hl_height}'
    
    return data_dict


def video_json(input_dict, save_dir):
    json_dict = {}
    
    json_dict['json_id'] = input_dict['json_id']

    json_dict['filename_org'] = os.path.basename(input_dict['ori_path'])
    json_dict['filename_hl'] = os.path.basename(input_dict['hl_path'])
    
    json_dict['ori_start_time'] = input_dict['ori_start_time']
    json_dict['ori_end_time'] = input_dict['ori_end_time']
    json_dict['ori_duration_time'] = input_dict['ori_duration_time']
    
    json_dict['hl_start_time'] = input_dict['hl_start_time']
    json_dict['hl_end_time'] = input_dict['hl_end_time']
    json_dict['hl_duration_time'] = input_dict['hl_duration_time']
    
    json_dict['ext_org'] = input_dict['ext_org']
    json_dict['ext_hl'] = input_dict['ext_hl']
    
    json_dict['category'] = input_dict['category']
    
    json_dict['ori_fps'] = input_dict['ori_fps']
    json_dict['hl_fps'] = input_dict['hl_fps']
    
    json_dict['ori_resolution'] = input_dict['ori_resolution']
    json_dict['hl_resolution'] = input_dict['hl_resolution']
    
    json_file_name = json_dict['filename_hl'].split(".")[0] + "_" + json_dict['json_id']
#     print(json_file_name)
    json_path = os.path.join(save_dir, f'{json_file_name}.json')
#     print(json_path)
    with open(json_path, 'w') as f:
        json.dump(json_dict, f, indent='\t')

# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description='Master Tracking')
#     parser.add_argument('--ori_path', type=str, ,
#                     help='location of the video')
    
    
    
#     thres, min_ph, ori_path, hl_path
    
    
#     app.run(host='0.0.0.0', port='9009', debug=False)