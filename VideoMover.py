"""
This program moves video and data from one folder to another.
First, the user is prompted to select the region of the video for cropping.
Then, a subset of frames is selected and the user checks if the cropping is correct.
Then the video is cropped, and unlossily compressed and saved to the output folder.
The data is also moved to the output folder.
"""

import os
import cv2
import ctypes
import subprocess
import shutil
from pathlib import Path
from typing import Sequence, Optional
import time


def Mbox(title, text, style):
    val = ctypes.windll.user32.MessageBoxW(0, text, title, style)
    if val == 6:
        return True
    else:
        return False

def find_video_files(input_folder: str) -> list:
    """
    Find all video files in the input folder.
    """
    video_files = []
    for file in os.listdir(input_folder):
        if file.endswith(".avi"):
            video_files.append(file)
    return video_files

def get_roi(video_file: str) -> Optional[Sequence[int]]:
    """
    Get the region of interest (ROI) for cropping the video.
    """
    
    #Check if the video file exists
    if not os.path.exists(video_file):
        print("Error: Video file does not exist.")
        return None
    video_file = video_file.replace("\\", "/")
    video_file_quoted = "\"" + video_file + "\""
    print(video_file_quoted)
    #cap = cv2.VideoCapture("filesrc location=" + video_file_quoted + " ! decodebin ! videoconvert ! appsink", cv2.CAP_GSTREAMER)
    # Wait for the video to load
    cap = cv2.VideoCapture(video_file, cv2.CAP_FFMPEG)
    time.sleep(1)
    can_seek = cap.get(cv2.CAP_PROP_POS_FRAMES)
    print("can_seek: ", can_seek)
    # h = int(cap.get(cv2.CAP_PROP_FOURCC))
    # codec = chr(h&0xff) + chr((h>>8)&0xff) + chr((h>>16)&0xff) + chr((h>>24)&0xff)
    # print("codec: " + codec)
    ret, frame = cap.read()
    print(ret,frame)
    if not ret:
        print("Error: Could not read video file.")
        return None
    #cv2.imshow("Select ROI", frame)
    roi = cv2.selectROI(frame)
    cv2.destroyAllWindows()
    cap.release()
    return roi

def confirm_roi(video_file: str, roi: Sequence[int]) -> bool:
    """
    Show the ROI on the video by cropping the view. Add a seek bar to move through the video.
    """
    video_file = video_file.replace("\\", "/")
    video_file_quoted = "\"" + video_file + "\""
    print(video_file_quoted)

    #cap = cv2.VideoCapture("filesrc location=" + video_file_quoted + " ! decodebin ! videoconvert ! appsink", cv2.CAP_GSTREAMER)
    cap = cv2.VideoCapture(video_file, cv2.CAP_FFMPEG)
    can_seek = cap.get(cv2.CAP_PROP_POS_FRAMES)
    print("can_seek: ", can_seek)
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read video file.")
        return False
    if roi is None:
        print("Error: ROI is None.")
        return False
    x, y, w, h = roi
    window_name = "ROI"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    min_width = 400
    automatic_min_height = 80
    display_width = max(w, min_width)
    display_height = h + automatic_min_height
    cv2.resizeWindow(window_name, display_width, display_height)
    cv2.moveWindow(window_name, 100, 100)
    cv2.createTrackbar("Frame", window_name, 0, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), lambda x: None)
    while True:
        frame_number = cv2.getTrackbarPos("Frame", window_name)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        if not ret:
            break
        frame = frame[y:y+h, x:x+w]
        # Pad the frame left/right if needed to center it in the window
        if w < min_width:
            pad_left = (min_width - w) // 2
            pad_right = min_width - w - pad_left
            frame = cv2.copyMakeBorder(frame, 0, 0, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[0,0,0])
        if h < automatic_min_height:
            pad_top = (automatic_min_height - h) // 2
            pad_bottom = automatic_min_height - h - pad_top
            frame = cv2.copyMakeBorder(frame, pad_top, pad_bottom, 0, 0, cv2.BORDER_CONSTANT, value=[0,0,0])
        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1)
        if key == ord("q"):
            break

    keepROI = Mbox('ROI', 'Is the ROI correct?', 4)
    cv2.destroyAllWindows()
    cap.release()
    return keepROI

def crop_video(video_file: str, roi: tuple, output_folder: str, codec: str) -> None:
    """
    Crop the video using the ROI and save the cropped video to the output folder.
    
    This uses the ffmpeg command line tool.
    """

    x = roi[0]
    y = roi[1]
    w = roi[2]
    h = roi[3]
    
    output_file = os.path.join(output_folder, os.path.splitext(os.path.basename(video_file))[0] + "_cropped.avi")
    output_file = output_file.replace("\\", "/")
    output_file = "\"" + output_file + "\""
    video_file = video_file.replace("\\", "/")
    video_file = "\"" + video_file + "\""
    ffmpeg_command = f"ffmpeg -y -i {video_file} -vf \"crop={w}:{h}:{x}:{y}\" -c:v {codec} -qp 0 -f avi {output_file}"
    subprocess.run(ffmpeg_command)
    
def recreate_file_structure(input_folder: str, output_folder: str) -> None:
    """
    Recreate the file structure of the input folder in the output folder.
    
    Args:
        input_folder (str): The path to the input folder.
        output_folder (str): The path to the output folder.
    """
    try:
        # Make the output folder if it does not exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        dir_items = os.listdir(input_folder)
        folders = []
        files = []
        
        for item in dir_items:
            item_path = os.path.join(input_folder, item)
            if os.path.isdir(item_path):
                folders.append(item)
            elif os.path.isfile(item_path):
                files.append(item)
        
        videos = find_video_files(input_folder)
        non_videos = [f for f in files if f not in videos]
        
        # Move the non-video files
        for file in non_videos:
            src_file = os.path.join(input_folder, file)
            dest_file = os.path.join(output_folder, file)
            shutil.copy2(src_file, dest_file)
        
        for folder in folders:
            src_folder = os.path.join(input_folder, folder)
            dest_folder = os.path.join(output_folder, folder)
            recreate_file_structure(src_folder, dest_folder)
    
    except Exception as e:
        print(f"Error: {e}")

def is_valid_roi(roi: Optional[Sequence[int]]) -> bool:
    """
    Check if the ROI is valid.
    
    Args:
        roi (Sequence[int]): The region of interest (ROI) as a sequence of integers.
        
    Returns:
        bool: True if the ROI is valid, False otherwise.
    """
    if roi is None:
        return False
    try:
        x, y, w, h = roi
    except ValueError:
        print("Error: ROI must be a sequence of four integers.")
        return False
    if w <= 0 or h <= 0:
        print("Error: Width and height must be greater than 0.")
        return False

    return all(isinstance(i, int) and i >= 0 for i in [x, y, w, h]) and w > 0 and h > 0
    return all(isinstance(i, int) and i >= 0 for i in [x, y, w, h])
def move_videos(input_folder: str, output_folder: str, codec: str = "libx264") -> None:
    """
    Move the video files from the input folder to the output folder.
    
    Args:
        input_folder (str): The path to the input folder.
        output_folder (str): The path to the output folder.
    """

    #Find all video files in the input folder
    videos = list(Path(input_folder).rglob('*.avi'))
    roi_list = []
    for video in videos:
        video = str(video)
        roi = None
        keepROI = False
        while not keepROI:
            roi = get_roi(video)
            # Make a sequence of integers of (0,0,0,0) to compare to the roi
            is_valid = is_valid_roi(roi)
            if not is_valid:
                # Make popup to ask if the user wants to skip this video
                skip_video = Mbox('ROI', 'ROI is None or invalid. Do you want to skip this video?', 4)
                if skip_video:
                    print("Skipping video:", video)
                    roi = None
                    break
            else:
                assert roi is not None, "ROI should not be None here"
                keepROI = confirm_roi(video, roi)
        if roi is None:
            print("Error: ROI is None. Skipping video.")
            continue
        roi_list.append(roi)
    
    for video, roi in zip(videos, roi_list):
        video = str(video)
        #Standardize the video path
        video = video.replace("\\", "/")
        input_folder = input_folder.replace("\\", "/")
        output_folder = output_folder.replace("\\", "/")
        video_output_folder = video.replace(input_folder, output_folder)
        video_output_folder = os.path.dirname(video_output_folder)
        if not os.path.exists(video_output_folder):
            os.makedirs(video_output_folder)
        crop_video(video, roi, video_output_folder, codec)

def double_check_files_copied(input_folder: str, output_folder: str, fail:bool = False) -> bool:
    """
    Double check that all files were copied from the input folder to the output folder.
    
    Args:
        input_folder (str): The path to the input folder.
        output_folder (str): The path to the output folder.
    """
    did_fail = fail
    input_files = os.listdir(input_folder)
    output_files = os.listdir(output_folder)
    
    input_video_files = find_video_files(input_folder)
    output_video_files = find_video_files(output_folder)
    #Check that output files are the same as input with "_cropped" appended before the extension
    for input_file in input_video_files:
        output_file = os.path.splitext(input_file)[0] + "_cropped.avi"
        print(output_file)
        if output_file not in output_video_files:
            print(f"Error: {output_file} not found in output folder.")
            fail = True
    
    non_video_files = [f for f in input_files if f not in input_video_files]
    
    #Check that non-video files are the same in input and output folders
    for file in non_video_files:
        if file not in output_files:
            print(f"Error: {file} not found in output folder.")
            fail = True
    
    folders = [f for f in input_files if os.path.isdir(os.path.join(input_folder, f))]
    
    #Check that the subfolders have the same files
    
    for folder in folders:
        input_subfolder = os.path.join(input_folder, folder)
        output_subfolder = os.path.join(output_folder, folder)
        fail_to_combine = double_check_files_copied(input_subfolder, output_subfolder)
        did_fail = fail or fail_to_combine
    
    return did_fail


def ensure_all_videos_playable(folder: str) -> bool:
    
    is_playable = True
    videos = find_video_files(folder)
    for video in videos:
        video = os.path.join(folder, video)
        cap = cv2.VideoCapture(video, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print(f"Error: {video} is not playable.")
            is_playable = False
        cap.release()
        
    dir_items = os.listdir(folder)
    folders = []
      
    for item in dir_items:
        item_path = os.path.join(folder, item)
        if os.path.isdir(item_path):
            folders.append(item)
            
    for folder1 in folders:
        next_folder = os.path.join(folder, folder1)
        if not ensure_all_videos_playable(next_folder):
            is_playable = False
    
    return is_playable

def move_and_crop(main_folder, output_folder, codec):
    recreate_file_structure(main_folder, output_folder)
    move_videos(main_folder, output_folder, codec)
    did_fail_to_move = double_check_files_copied(main_folder, output_folder)
    all_files_playable = ensure_all_videos_playable(output_folder)
    return did_fail_to_move, all_files_playable

# experiment_folder = "2025-07-15-Durability-60nmDesc-1-1"
# upper_folder = "E:\\Raw_Data"
# output_upper_folder = "Z:\\Data"


if __name__ == "__main__":
    main_folder = "E:\\Raw_Data\\2025-07-15-Durability-60nmDesc-1-1" # Path to the experiment set folder
    output_folder = "Z:\\Data\\2025-07-15-Durability-60nmDesc-1-1" # Path to the output folder including the experiment set folder name
    codec = "libx264"
    move_and_crop(main_folder, output_folder, codec)
    