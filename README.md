# VideoMoverCropperCompressor
This program moves all files and videos from one location to another, providing an interface to crop videos. Cropped videos are losslessly compressed and saved to the target folder. Non-video files are also copied, preserving the folder structure.

## Features
- Interactive cropping GUI for each video
- Confirmation window with seekbar to verify crop
- Currently supports .avi input files
- Output formats: MKV (FFV1), MP4 (H.264), AVI (libx264)
- Lossless compression using FFmpeg
- Preserves original folder structure and non-video files

## Requirements
- opencv-python (Install via pip. Conda library does not have correct codecs.)
- FFmpeg (Must be installed and available in your system PATH)

# Usage

Modify the variables experiment_folder, upper_folder, and output_upper_folder to change the behaviour.
```python
main_folder = "E:\\Raw_Data\\2025-07-15-Durability-60nmDesc-1-1"
output_folder = "Z:\\Data\\2025-07-15-Durability-60nmDesc-1-1"
format = "mp4"  # or "ffv1", "libx264_avi"
move_and_crop(main_folder, output_folder, format)
```

Run and the cropping GUI will appear. It will run for all videos in the folder.
![image](https://github.com/user-attachments/assets/94516454-8637-4c26-b08d-f6cea9268a7e)

upon pressing enter, the window will close. A new window with a seekbar will apear, use this to confirm that the crop is correct.
![image](https://github.com/user-attachments/assets/a283a469-00ba-468a-ad42-04dc2003a339)

Once all images have been processed, the moving, cropping and compressing process will comence.
