import cv2
import numpy as np
import subprocess
import socket
import netifaces

def main():
    

    def get_local_ip():
        preferred_interfaces = ["eth0", "wlan0"]  # Prioritize Ethernet (eth0), fallback to Wi-Fi (wlan0)
        
        for iface in preferred_interfaces:
            try:
                if iface in netifaces.interfaces():
                    addrs = netifaces.ifaddresses(iface)
                    if netifaces.AF_INET in addrs:
                        return addrs[netifaces.AF_INET][0]['addr']  # Return first available IP
            except Exception as e:
                print(f"Error checking {iface}: {e}")
        
        # Fallback: Get default IP based on routing table
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Google's DNS
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"Could not determine IP: {e}")
            return "127.0.0.1"  # Default to localhost if all else fails

    # Example Usage
    local_ip = get_local_ip()
    print("Detected IP:", local_ip)
    # Set the IP and port for HM30 video input
    #input_stream = "rtsp://192.168.144.25:8544"  # Replace with your HM30's stream URL

    # Load face detection model
    face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

    # Open video capture
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,240)
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return
        
#'cvlc','stream:///dev/stdin',
#        '--sout','#rtp{sdp=rtsp://192.168.144.25:8554/stream}',
#        '--no-sout-audio','--sout-keep'
    # Define GStreamer pipeline for UDP streaming
    rtsp_url=f"rtsp://{local_ip}:8554/stream"
    command = [
         'ffmpeg','-re','-f','rawvideo','-pix_fmt','bgr24',
         '-s','320x240','-r','15','-i','-','-c:v','h264_omx','-preset',
         'ultrafast','-tune','zerolatency','-f','rtsp',
         rtsp_url
    ]
    process  = subprocess.Popen(command,stdin=subprocess.PIPE)
    #out = cv2.VideoWriter(gst_pipeline, cv2.CAP_GSTREAMER, 0, 30, (640, 480))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to receive frame.")
            break 

        # Convert to grayscale for face detection
        small_frame = cv2.resize(frame, (160, 120))
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            x, y, w, h = x * 2, y * 2, w * 2, h * 2
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        process.stdin.write(frame.astype(np.uint8).tobytes())
        # Show the processed frame locally
        cv2.imshow("Processed Video", frame)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    process.terminate()

if __name__ == "__main__":
    main()