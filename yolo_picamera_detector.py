#!/usr/bin/env python3
"""
Raspberry Pi 5 YOLO Camera OLED Detector
YOLOv8による物体検出結果をOLEDに表示するシステム

要件:
- Raspberry Pi 5 + Camera V3
- YOLOv8による物体検出
- SSD1306 OLED (128x64, I2C接続)
- 初心者向け教材として単一ファイル構成
"""

import cv2
import time
import logging
import sys
from pathlib import Path
from threading import Thread, Event
from ultralytics import YOLO
from picamera2 import Picamera2
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

# 設定定数
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 20

MODEL_NAME = "yolov8n"
CONF_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45

# OLED設定
OLED_I2C_BUS = 1
OLED_ADDRESS = 0x3C
OLED_WIDTH = 128
OLED_HEIGHT = 64

# フォント設定
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_SIZE_LARGE = 14
FONT_SIZE_SMALL = 11

MAX_LABELS = 3
LABEL_LANG = "ja"

# 日本語ラベル変換テーブル
LABEL_TRANSLATION = {
    "person": "人",
    "bicycle": "自転車",
    "car": "車",
    "motorcycle": "バイク",
    "airplane": "飛行機",
    "bus": "バス",
    "train": "電車",
    "truck": "トラック",
    "boat": "ボート",
    "traffic light": "信号",
    "fire hydrant": "消火栓",
    "stop sign": "停止標識",
    "parking meter": "駐車場",
    "bench": "ベンチ",
    "bird": "鳥",
    "cat": "猫",
    "dog": "犬",
    "horse": "馬",
    "sheep": "羊",
    "cow": "牛",
    "elephant": "象",
    "bear": "熊",
    "zebra": "シマウマ",
    "giraffe": "キリン",
    "backpack": "リュック",
    "umbrella": "傘",
    "handbag": "ハンドバッグ",
    "tie": "ネクタイ",
    "suitcase": "スーツケース",
    "frisbee": "フリスビー",
    "skis": "スキー",
    "snowboard": "スノボ",
    "sports ball": "ボール",
    "kite": "凧",
    "baseball bat": "バット",
    "baseball glove": "グローブ",
    "skateboard": "スケボ",
    "surfboard": "サーフボード",
    "tennis racket": "ラケット",
    "bottle": "ボトル",
    "wine glass": "ワイングラス",
    "cup": "カップ",
    "fork": "フォーク",
    "knife": "ナイフ",
    "spoon": "スプーン",
    "bowl": "ボウル",
    "banana": "バナナ",
    "apple": "りんご",
    "sandwich": "サンドイッチ",
    "orange": "オレンジ",
    "broccoli": "ブロッコリー",
    "carrot": "にんじん",
    "hot dog": "ホットドッグ",
    "pizza": "ピザ",
    "donut": "ドーナツ",
    "cake": "ケーキ",
    "chair": "椅子",
    "couch": "ソファ",
    "potted plant": "植物",
    "bed": "ベッド",
    "dining table": "テーブル",
    "toilet": "トイレ",
    "tv": "テレビ",
    "laptop": "ノートPC",
    "mouse": "マウス",
    "remote": "リモコン",
    "keyboard": "キーボード",
    "cell phone": "スマホ",
    "microwave": "電子レンジ",
    "oven": "オーブン",
    "toaster": "トースター",
    "sink": "シンク",
    "refrigerator": "冷蔵庫",
    "book": "本",
    "clock": "時計",
    "vase": "花瓶",
    "scissors": "ハサミ",
    "teddy bear": "テディベア",
    "hair drier": "ドライヤー",
    "toothbrush": "歯ブラシ"
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

    def initialize_oled(self):
        """OLED初期化"""
        try:
            self.logger.info(f"OLED初期化中... (アドレス: 0x{OLED_ADDRESS:02X})")

            # I2Cシリアル接続の初期化
            serial = i2c(port=OLED_I2C_BUS, address=OLED_ADDRESS)

            # SSD1306デバイスの初期化
            self.oled = ssd1306(serial, width=OLED_WIDTH, height=OLED_HEIGHT)

            # フォントの読み込み
            try:
                self.font_large = ImageFont.truetype(FONT_PATH, FONT_SIZE_LARGE)
                self.font_small = ImageFont.truetype(FONT_PATH, FONT_SIZE_SMALL)
                self.logger.info(f"フォント読み込み完了: {FONT_PATH}")
            except Exception as font_error:
                self.logger.warning(f"フォント読み込みエラー: {font_error}")
                self.logger.info("デフォルトフォントを使用します")
                self.font_large = ImageFont.load_default()
                self.font_small = ImageFont.load_default()

            # 起動メッセージ表示
            with canvas(self.oled) as draw:
                draw.text((10, 20), "起動中...", font=self.font_large, fill="white")

            self.logger.info("OLED初期化完了")
            return True
        except Exception as e:
            self.logger.error(f"OLED初期化エラー: {e}")
            self.logger.info("OLED無しで続行...")
            self.oled = None
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

    def update_oled(self, detections, fps):
        """OLED表示更新"""
        if self.oled is None:
            return

        try:
            with canvas(self.oled) as draw:
                # FPS表示（右上）
                fps_text = f"FPS:{fps:.1f}"
                draw.text((80, 0), fps_text, font=self.font_small, fill="white")

                # 検出結果表示
                if detections:
                    y_position = 0
                    for i, detection in enumerate(detections):
                        if y_position >= OLED_HEIGHT - 12:
                            break  # 画面からはみ出る場合は表示しない

                        label = self.format_label(detection['class_name'])
                        conf_percent = int(detection['confidence'] * 100)
                        text = f"{i+1}.{label} {conf_percent}%"

                        # テキストサイズに応じてフォント選択
                        font = self.font_large if i == 0 else self.font_small
                        draw.text((0, y_position), text, font=font, fill="white")

                        # 次の行へ
                        y_position += (FONT_SIZE_LARGE + 2) if i == 0 else (FONT_SIZE_SMALL + 2)
                else:
                    # 検出なし
                    draw.text((20, 25), "検出なし", font=self.font_large, fill="white")

        except Exception as e:
            self.logger.error(f"OLED更新エラー: {e}")

    def run(self):
        """メインループ"""
        self.logger.info("YOLO Picamera OLED Detector 開始")

        # 初期化
        if not self.initialize_model():
            return False

        if not self.initialize_camera():
            return False

        self.initialize_oled()  # OLED初期化失敗でも続行

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

                # OLED更新
                self.update_oled(top_detections, fps)

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
            if self.oled:
                with canvas(self.oled) as draw:
                    draw.text((30, 25), "停止", font=self.font_large, fill="white")
                time.sleep(1)
                self.oled.clear()
                self.logger.info("OLED停止完了")
        except Exception as e:
            self.logger.error(f"OLED停止エラー: {e}")


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