"""Cầu nối QR: quét camera USB, cung cấp mã cho App Kho qua localhost."""
import argparse
import json
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "App Kho"
state = {"id": 0, "text": "", "time": None}
latest_jpeg = None
lock = threading.Lock()
stop_event = threading.Event()


def scanner(camera_index: int, show_window: bool) -> None:
    global latest_jpeg
    detector = cv2.QRCodeDetector()
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Không thể mở camera index {camera_index}.")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    previous_text, missed_frames = "", 0
    print("Camera QR đã sẵn sàng. Nhấn q ở cửa sổ camera để dừng.")
    while not stop_event.is_set():
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.1)
            continue
        enlarged = cv2.resize(frame, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        text, points, _ = detector.detectAndDecode(enlarged)
        if text and points is not None:
            missed_frames = 0
            corners = (points[0] / 2).astype(int)
            cv2.polylines(frame, [corners], True, (0, 255, 0), 3)
            cv2.putText(frame, text, tuple(corners[0]), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 0), 2)
            if text != previous_text:
                with lock:
                    state["id"] += 1
                    state["text"] = text
                    state["time"] = time.time()
                previous_text = text
                print(f"QR da quet: {text}")
        else:
            missed_frames += 1
            if missed_frames > 12:
                previous_text = ""
        encoded, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if encoded:
            with lock:
                latest_jpeg = jpeg.tobytes()
        if show_window:
            cv2.putText(frame, f"USB camera - index: {camera_index}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 255), 2)
            cv2.imshow("QR Code - App Kho", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                stop_event.set()
    cap.release()
    cv2.destroyAllWindows()


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/qr":
            with lock:
                payload = dict(state)
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/video":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            try:
                while not stop_event.is_set():
                    with lock:
                        frame = latest_jpeg
                    if frame:
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n")
                        self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode())
                        self.wfile.write(frame + b"\r\n")
                    time.sleep(0.06)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        if "/api/qr" not in args[0]:
            super().log_message(fmt, *args)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0, help="Chỉ số camera USB")
    parser.add_argument("--no-window", action="store_true", help="Không hiển thị cửa sổ OpenCV")
    args = parser.parse_args()
    if not APP_DIR.exists():
        raise FileNotFoundError(f"Không thấy thư mục app: {APP_DIR}")
    threading.Thread(target=scanner, args=(args.camera, not args.no_window), daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", 5000), AppHandler)
    print("Mở App Kho tại http://127.0.0.1:5000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        server.server_close()


if __name__ == "__main__":
    main()
