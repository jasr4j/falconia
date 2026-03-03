#!/usr/bin/python3
from time import sleep
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

# Initialize camera and configure output via FFmpeg to an RTP stream
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (1280, 720)})
picam2.configure(config)

# Send RTP stream to a destination IP
output = FfmpegOutput("-f rtp udp://192.168.1.10:9000")
picam2.start_recording(H264Encoder(), output=output)
print("Streaming to udp://192.168.1.10:9000")

try:
    while True: sleep(1)
except KeyboardInterrupt:
    picam2.stop_recording()
