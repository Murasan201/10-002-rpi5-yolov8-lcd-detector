#!/usr/bin/env python3
"""
Raspberry Pi 5 YOLO Camera LCD Detector
YOLOv8による物体検出結果をLCDに表示するシステム

要件:
- Raspberry Pi 5 + Camera V3
- YOLOv8による物体検出
- 16x2 LCD (I2C接続)
- 初心者向け教材として単一ファイル構成
"""

import cv2
import time
import logging
import sys
from threading import Thread, Event
from ultralytics import YOLO
from picamera2 import Picamera2
import smbus2
from RPLCD.i2c import CharLCD

# 設定定数
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 20

MODEL_NAME = "yolov8n"
CONF_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45

LCD_I2C_BUS = 1
LCD_ADDRESS = 0x27
LCD_COLS = 16
LCD_ROWS = 2

MAX_LABELS = 2
LABEL_LANG = "ja"

# 日本語ラベル変換テーブル
LABEL_TRANSLATION = {
    "person": "Person",
    "bicycle": "Bicycle",
    "car": "Car",
    "motorcycle": "Bike",
    "airplane": "Plane",
    "bus": "Bus",
    "train": "Train",
    "truck": "Truck",
    "boat": "Boat",
    "traffic light": "Light",
    "fire hydrant": "Hydrant",
    "stop sign": "Stop",
    "parking meter": "Meter",
    "bench": "Bench",
    "bird": "Bird",
    "cat": "Cat",
    "dog": "Dog",
    "horse": "Horse",
    "sheep": "Sheep",
    "cow": "Cow",
    "elephant": "Elephant",
    "bear": "Bear",
    "zebra": "Zebra",
    "giraffe": "Giraffe",
    "backpack": "Backpack",
    "umbrella": "Umbrella",
    "handbag": "Handbag",
    "tie": "Tie",
    "suitcase": "Suitcase",
    "frisbee": "Frisbee",
    "skis": "Skis",
    "snowboard": "Snowboard",
    "sports ball": "Ball",
    "kite": "Kite",
    "baseball bat": "Bat",
    "baseball glove": "Glove",
    "skateboard": "Skateboard",
    "surfboard": "Surfboard",
    "tennis racket": "Racket",
    "bottle": "Bottle",
    "wine glass": "Glass",
    "cup": "Cup",
    "fork": "Fork",
    "knife": "Knife",
    "spoon": "Spoon",
    "bowl": "Bowl",
    "banana": "Banana",
    "apple": "Apple",
    "sandwich": "Sandwich",
    "orange": "Orange",
    "broccoli": "Broccoli",
    "carrot": "Carrot",
    "hot dog": "Hot Dog",
    "pizza": "Pizza",
    "donut": "Donut",
    "cake": "Cake",
    "chair": "Chair",
    "couch": "Couch",
    "potted plant": "Plant",
    "bed": "Bed",
    "dining table": "Table",
    "toilet": "Toilet",
    "tv": "TV",
    "laptop": "Laptop",
    "mouse": "Mouse",
    "remote": "Remote",
    "keyboard": "Keyboard",
    "cell phone": "Phone",
    "microwave": "Microwave",
    "oven": "Oven",
    "toaster": "Toaster",
    "sink": "Sink",
    "refrigerator": "Fridge",
    "book": "Book",
    "clock": "Clock",
    "vase": "Vase",
    "scissors": "Scissors",
    "teddy bear": "Teddy",
    "hair drier": "Dryer",
    "toothbrush": "Toothbrush"
}


class YOLODetector:
    """YOLO物体検出クラス"""

    def __init__(self):
        self.model = None
        self.setup_logging()

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('detector.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def initialize_model(self):
        """YOLOモデルの初期化"""
        try:
            self.logger.info(f"YOLOモデル '{MODEL_NAME}' を読み込み中...")
            self.model = YOLO(MODEL_NAME)
            self.logger.info("YOLOモデルの読み込み完了")
            return True
        except Exception as e:
            self.logger.error(f"YOLOモデルの読み込みエラー: {e}")
            return False

    def initialize_camera(self):
        """カメラの初期化"""
        try:
            self.logger.info("カメラを初期化中...")
            self.camera = Picamera2()
            config = self.camera.create_preview_configuration(
                main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT)}
            )
            self.camera.configure(config)
            self.camera.start()
            time.sleep(2)  # カメラの安定化待ち
            self.logger.info(f"カメラ初期化完了: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
            return True
        except Exception as e:
            self.logger.error(f"カメラ初期化エラー: {e}")
            return False

    def initialize_lcd(self):
        """LCD初期化"""
        try:
            self.logger.info(f"LCD初期化中... (アドレス: 0x{LCD_ADDRESS:02X})")
            self.lcd = CharLCD(
                i2c_expander='PCF8574',
                address=LCD_ADDRESS,
                port=LCD_I2C_BUS,
                cols=LCD_COLS,
                rows=LCD_ROWS
            )
            self.lcd.clear()
            self.lcd.write_string("Starting...")
            self.logger.info("LCD初期化完了")
            return True
        except Exception as e:
            self.logger.error(f"LCD初期化エラー: {e}")
            self.logger.info("LCD無しで続行...")
            self.lcd = None
            return False

    def detect_objects(self, frame):
        """物体検出"""
        if self.model is None:
            return []

        try:
            results = self.model(
                frame,
                conf=CONF_THRESHOLD,
                iou=IOU_THRESHOLD,
                verbose=False
            )

            detections = []
            if results and len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None:
                    for box in boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        class_name = self.model.names[class_id]

                        # 面積計算（優先順位用）
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        area = (x2 - x1) * (y2 - y1)

                        detections.append({
                            'class_name': class_name,
                            'confidence': confidence,
                            'area': area
                        })

            return detections
        except Exception as e:
            self.logger.error(f"物体検出エラー: {e}")
            return []

    def select_top_detections(self, detections):
        """上位検出結果の選択"""
        if not detections:
            return []

        # 信頼度で降順ソート
        detections.sort(key=lambda x: x['confidence'], reverse=True)

        # 最大MAX_LABELS件まで
        return detections[:MAX_LABELS]

    def format_label(self, class_name):
        """ラベル名の整形"""
        if LABEL_LANG == "ja" and class_name in LABEL_TRANSLATION:
            return LABEL_TRANSLATION[class_name]
        return class_name.title()

    def update_lcd(self, detections, fps):
        """LCD表示更新"""
        if self.lcd is None:
            return

        try:
            self.lcd.clear()

            if detections:
                # 1行目: 最上位検出結果
                detection = detections[0]
                label = self.format_label(detection['class_name'])
                conf_percent = int(detection['confidence'] * 100)
                line1 = f"{label} {conf_percent}%"

                # 16文字制限
                if len(line1) > LCD_COLS:
                    line1 = line1[:LCD_COLS]

                self.lcd.write_string(line1)
            else:
                self.lcd.write_string("No objects")

            # 2行目: FPS
            self.lcd.cursor_pos = (1, 0)
            fps_text = f"FPS: {fps:.1f}"
            if len(fps_text) > LCD_COLS:
                fps_text = fps_text[:LCD_COLS]
            self.lcd.write_string(fps_text)

        except Exception as e:
            self.logger.error(f"LCD更新エラー: {e}")

    def run(self):
        """メインループ"""
        self.logger.info("YOLO Picamera Detector 開始")

        # 初期化
        if not self.initialize_model():
            return False

        if not self.initialize_camera():
            return False

        self.initialize_lcd()  # LCD初期化失敗でも続行

        # FPS計算用
        fps_counter = 0
        fps_start_time = time.time()
        fps = 0.0

        try:
            self.logger.info("検出ループ開始...")

            while True:
                # フレーム取得
                frame = self.camera.capture_array()

                # BGR変換（OpenCV用）
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                else:
                    frame_bgr = frame

                # 物体検出
                detections = self.detect_objects(frame_bgr)
                top_detections = self.select_top_detections(detections)

                # FPS計算
                fps_counter += 1
                if fps_counter >= 10:  # 10フレームごとに計算
                    fps_end_time = time.time()
                    fps = fps_counter / (fps_end_time - fps_start_time)
                    fps_start_time = fps_end_time
                    fps_counter = 0

                # LCD更新
                self.update_lcd(top_detections, fps)

                # ログ出力（検出時のみ）
                if top_detections:
                    detection_info = ", ".join([
                        f"{self.format_label(d['class_name'])}({d['confidence']:.2f})"
                        for d in top_detections
                    ])
                    self.logger.info(f"検出: {detection_info} | FPS: {fps:.1f}")

                # 少し待機
                time.sleep(0.01)

        except KeyboardInterrupt:
            self.logger.info("Ctrl+Cで終了")
        except Exception as e:
            self.logger.error(f"実行エラー: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """リソースのクリーンアップ"""
        self.logger.info("リソースをクリーンアップ中...")

        try:
            if hasattr(self, 'camera'):
                self.camera.stop()
                self.logger.info("カメラ停止完了")
        except Exception as e:
            self.logger.error(f"カメラ停止エラー: {e}")

        try:
            if self.lcd:
                self.lcd.clear()
                self.lcd.write_string("Stopped")
                self.logger.info("LCD停止完了")
        except Exception as e:
            self.logger.error(f"LCD停止エラー: {e}")


def main():
    """メイン関数"""
    detector = YOLODetector()

    try:
        success = detector.run()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"致命的エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()