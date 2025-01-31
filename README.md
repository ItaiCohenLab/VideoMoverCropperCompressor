# VideoMoverCropperCompressor
Program that moves all files and videos from one location to another, while providing an interface to crop. Upon cropping, videos are cropped, losslessly compressed and then moved to the target folder.

requirements:
opencv (if using anaconda, you need to install via pip, the anaconda package does not work)
numpy
ctypes
shutil
subprocess

Currently works for .avi files.

Modify the variables experiment_folder, upper_folder, and output_upper_folder to change the behaviour.
![image](https://github.com/user-attachments/assets/34923a3e-f78e-435a-868a-13da216ff121)

Run and the cropping GUI will appear. It will run for all videos in the folder.
![image](https://github.com/user-attachments/assets/94516454-8637-4c26-b08d-f6cea9268a7e)

upon pressing enter, the window will close. A new window with a seekbar will apear, use this to confirm that the crop is correct.
![image](https://github.com/user-attachments/assets/a283a469-00ba-468a-ad42-04dc2003a339)

Once all images have been processed, the moving, cropping and compressing process will comence.
