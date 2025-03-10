import cv2
import numpy as np

def main():
    # Set the IP and port for HM30 video input
    input_stream = "udp://192.168.144.25:5600"  # Replace with your HM30's stream URL
    
    # Set the IP and port for sending processed video
    output_ip = "192.168.144.10"  # Replace with ground unit IP
    output_port = 5600

    # Load face detection model
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    # Open video capture
    cap = cv2.VideoCapture(input_stream, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    # Define GStreamer pipeline for UDP streaming
    gst_pipeline = (
        f"appsrc ! videoconvert ! video/x-raw,format=I420 ! "
        f"x264enc speed-preset=ultrafast tune=zerolatency ! "
        f"rtph264pay config-interval=1 pt=96 ! "
        f"udpsink host={output_ip} port={output_port}"
    )

    out = cv2.VideoWriter(gst_pipeline, cv2.CAP_GSTREAMER, 0, 30, (640, 480))
    if not out.isOpened():
        print("Error: Could not open video writer.")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to receive frame.")
            break

        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Show the processed frame locally
        cv2.imshow("Processed Video", frame)
        
        # Send processed video to the ground unit
        out.write(frame)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()