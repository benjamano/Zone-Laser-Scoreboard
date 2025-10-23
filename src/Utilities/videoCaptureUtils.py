import cv2

def list_capture_devices(max_devices=10):
    """Return a list of available capture device indexes."""
    available = []
    for i in range(max_devices):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available

if __name__ == "__main__":
    devices = list_capture_devices()
    print("Available capture devices:", devices)
