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

def find_video_files(input_folder: str, video_format: str) -> list:
    """
    Find all video files in the input folder.
    """
    video_files = []
    for file in os.listdir(input_folder):
        if file.endswith(video_format):
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
    # can_seek = cap.get(cv2.CAP_PROP_POS_FRAMES)
    # h = int(cap.get(cv2.CAP_PROP_FOURCC))
    # codec = chr(h&0xff) + chr((h>>8)&0xff) + chr((h>>16)&0xff) + chr((h>>24)&0xff)
    # print("codec: " + codec)
    ret, frame = cap.read()
    # print(ret, frame)
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
        # Press enter or 'q' to confirm the ROI
        if key == ord("q") or key == 13:  # 13 is the Enter key
            break

    keepROI = Mbox('ROI', 'Is the ROI correct?', 4)
    cv2.destroyAllWindows()
    cap.release()
    return keepROI

def crop_video(video_file: str, roi: tuple, output_folder: str, format_choice: str) -> None:
    """
    Crop the video using the ROI and save the cropped video to the output folder.
    
    This uses the ffmpeg command line tool.
    
    Args:
        video_file: Path to the input video file
        roi: Tuple of (x, y, width, height) for cropping
        output_folder: Directory to save the cropped video
        format_choice: Output format ("ffv1", "mp4", or "libx264_avi")
        
    Raises:
        ValueError: If format_choice is not supported
        FileNotFoundError: If input video file doesn't exist
        subprocess.CalledProcessError: If ffmpeg command fails
    """
    # Input validation
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"Input video file not found: {video_file}")
    
    if len(roi) != 4:
        raise ValueError("ROI must be a tuple of 4 values (x, y, width, height)")
    
    x, y, w, h = roi
    
    # Validate ROI values
    if w <= 0 or h <= 0:
        raise ValueError(f"Width and height must be positive, got width={w}, height={h}")
    
    file_endings = {
        "ffv1": "mkv",
        "mp4": "mp4",
        "libx264_avi": "avi",
    }
    
    if format_choice not in file_endings:
        raise ValueError(f"Unsupported format choice: {format_choice}. Supported formats are: {', '.join(file_endings.keys())}")
    
    file_ending = file_endings[format_choice]
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Generate output file path
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_file = os.path.join(output_folder, f"{base_name}_cropped.{file_ending}")
    
    # Build ffmpeg command using list for better security
    ffmpeg_commands = {
        "ffv1": [
            "ffmpeg", "-y", "-i", video_file,
            "-vf", f"crop={w}:{h}:{x}:{y}",
            "-c:v", "ffv1", "-level", "3",
            "-f", "matroska", output_file
        ],
        "mp4": [
            "ffmpeg", "-y", "-i", video_file,
            "-vf", f"crop={w}:{h}:{x}:{y}",
            "-c:v", "libx264", "-preset", "ultrafast", "-qp", "0",
            "-f", "mp4", output_file
        ],
        "libx264_avi": [
            "ffmpeg", "-y", "-i", video_file,
            "-vf", f"crop={w}:{h}:{x}:{y}",
            "-c:v", "libx264", "-preset", "ultrafast", "-qp", "0",
            "-f", "avi", output_file
        ]
    }
    
    ffmpeg_command = ffmpeg_commands[format_choice]
    
    try:
        print(f"Cropping video: {video_file} -> {output_file}")
        
        # Add progress flag to FFmpeg command for better progress reporting
        ffmpeg_command_with_progress = ffmpeg_command + ["-progress", "pipe:2"]
        
        # Run with stderr displayed for progress but capture stdout
        result = subprocess.run(ffmpeg_command_with_progress, check=True, 
                              stdout=subprocess.PIPE, text=True)
        print(f"Successfully cropped video to: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg command failed with return code {e.returncode}")
        # Try to run without progress flag to get error details
        try:
            error_result = subprocess.run(ffmpeg_command, check=False, 
                                        capture_output=True, text=True)
            if error_result.stderr:
                print(f"Error details: {error_result.stderr}")
        except:
            pass
        raise subprocess.CalledProcessError(e.returncode, e.cmd, None, None) from e
    except FileNotFoundError:
        raise FileNotFoundError("FFmpeg not found. Please ensure FFmpeg is installed and in your PATH.")
    
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
        
        videos = find_video_files(input_folder, "avi")
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

def move_videos(input_folder: str, output_folder: str, format: str = "mp4") -> None:
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
        crop_video(video, roi, video_output_folder, format)

def double_check_files_copied(input_folder: str, output_folder: str, video_format: str, fail:bool = False) -> bool:
    """
    Double check that all files were copied from the input folder to the output folder.
    
    Args:
        input_folder (str): The path to the input folder.
        output_folder (str): The path to the output folder.
        video_format (str): The video format (e.g., "mp4", "avi", "mkv").
        fail (bool): Whether to fail if any files are missing.
    """
    did_fail = fail
    input_files = os.listdir(input_folder)
    output_files = os.listdir(output_folder)
    
    input_video_format = "avi"
    input_video_files = find_video_files(input_folder, input_video_format)
    output_video_files = find_video_files(output_folder, video_format)
    #Check that output files are the same as input with "_cropped" appended before the extension
    for input_file in input_video_files:
        output_file = os.path.splitext(input_file)[0] + f"_cropped.{video_format}"
        if output_file not in output_video_files:
            print(f"Error: {output_file} not found in {output_folder}.")
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
        fail_to_combine = double_check_files_copied(input_subfolder, output_subfolder, video_format, fail)
        did_fail = fail or fail_to_combine
    
    return did_fail


def ensure_all_videos_playable(folder: str, video_format: str) -> bool:

    is_playable = True
    videos = find_video_files(folder, video_format)
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
        if not ensure_all_videos_playable(next_folder, video_format):
            is_playable = False
    
    return is_playable

format_endings = {
    "ffv1": "mkv",
    "mp4": "mp4",
    "libx264_avi": "avi",
}

def move_and_crop(main_folder, output_folder, format):
    recreate_file_structure(main_folder, output_folder)
    move_videos(main_folder, output_folder, format)
    did_fail_to_move = double_check_files_copied(main_folder, output_folder, format_endings[format], fail=False)
    all_files_playable = ensure_all_videos_playable(output_folder, format_endings[format])
    return did_fail_to_move, all_files_playable

# experiment_folder = "2025-07-15-Durability-60nmDesc-1-1"
# upper_folder = "E:\\Raw_Data"
# output_upper_folder = "Z:\\Data"

def get_format_options()-> dict:
    """
    Returns a dictionary of format options for the user to choose from.
    The keys are the display names and the values are the format codes.
    """
    
    format_options_dict = {
        "mkv FFV1 (uncompressed) (recommended)": "ffv1",
        "mp4 H.264 (uncompressed) (most compatible)": "mp4",
        "avi (libx264) (uncompressed)": "libx264_avi",
    }
    return format_options_dict

if __name__ == "__main__":
    main_folder = "E:\\Raw_Data\\2025-07-15-Durability-60nmDesc-1-1" # Path to the experiment set folder
    output_folder = "Z:\\Data\\2025-07-15-Durability-60nmDesc-1-1" # Path to the output folder including the experiment set folder name
    format = "mp4"
    move_and_crop(main_folder, output_folder, format)
