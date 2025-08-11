# 🎯 Dance Pose Evaluation Game

📌 **This project is functional, though there’s still room for improvement 😄**  
Run the game with:

```bash
python dancegame_fully.py


✅ Features
Real-time pose tracking – Uses MediaPipe to detect human body keypoints

Motion similarity comparison – Calculates pose differences using FastDTW

Error calculation – Displays real-time error percentage

Movement accuracy scoring – Evaluates how accurately the user imitates the benchmark video

⚠ Known Issues
Video playback sometimes lags – needs optimization for smoother playback

Audio delay issue

📄 File Descriptions
move_comparison.py
Compares dance movements between the webcam feed and a pre-recorded pose video to measure accuracy for each frame.

pose_module.py
Pose detection module using MediaPipe for extracting human body keypoints.

🛠 Technologies Used
Python

OpenCV

MediaPipe Pose

FastDTW

NumPy
