import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar

def main():
    # Set the IP and port for HM30 video input
    input_stream = "udp://192.168.144.25:5600"  # Replace with your HM30's stream URL
    
    # Set the IP and port for sending processed video
    output_ip = "192.168.144.10"  # Replace with ground unit IP
    output_port = 5600

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

        # Detect QR codes
        decoded_objects = pyzbar.decode(frame)
        for obj in decoded_objects:
            points = obj.polygon
            if len(points) == 4:
                pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=3)
            
            qr_text = obj.data.decode("utf-8")
            cv2.putText(frame, qr_text, (points[0].x, points[0].y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            print(f"QR Code Detected: {qr_text}")

        # Show the processed frame locally
        cv2.imshow("QR Code Detection", frame)
        
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