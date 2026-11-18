import cv2

CAMERA_INDEX = 0  # Camera USB; nếu USB là index 0 thì đổi thành 0

qrc = cv2.QRCodeDetector()
cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    raise RuntimeError(f"Không thể mở camera index {CAMERA_INDEX}")

# Tăng độ phân giải của camera USB để QR dễ nhận hơn
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while True:
    ret, frame = cap.read()

    if not ret:
        print("Không đọc được hình từ camera.")
        break

    # Phóng hình trước khi quét để hỗ trợ QR nhỏ
    scan_frame = cv2.resize(
        frame,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    # Dùng cho một mã QR: ổn định hơn detectAndDecodeMulti
    text, points, _ = qrc.detectAndDecode(scan_frame)

    # Hiển thị camera đang dùng
    cv2.putText(
        frame,
        f"USB camera - index: {CAMERA_INDEX}",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2,
        cv2.LINE_AA
    )

    if text and points is not None:
        # Đưa tọa độ từ ảnh đã phóng về kích thước ảnh gốc
        corners = (points[0] / 2).astype(int)

        cv2.polylines(frame, [corners], True, (0, 255, 0), 3)

        x, y = corners[0]
        cv2.putText(
            frame,
            text,
            (int(x), max(int(y) - 10, 30)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

        print("QR da quet:", text)

    cv2.imshow("QR Code - USB Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()