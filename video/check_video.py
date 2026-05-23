import cv2
import imageio_ffmpeg
import subprocess

cap = cv2.VideoCapture("final.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)
frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
duration = frames / fps if fps else 0

print(f"OpenCV properties:")
print(f"  FPS: {fps}")
print(f"  Frames: {frames}")
print(f"  Width: {width}")
print(f"  Height: {height}")
print(f"  Duration: {duration:.2f}s")

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
print(f"\nFFmpeg path: {ffmpeg_exe}")
print(f"Inspecting with FFmpeg...")
cmd = [ffmpeg_exe, "-i", "final.mp4"]
result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
print("FFmpeg stderr (contains video info):")
print(result.stderr)
