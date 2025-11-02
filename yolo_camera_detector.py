#!/usr/bin/env python3
"""
Raspberry Pi 5 YOLO Camera OLED Detector (Universal Version)
YOLOv8による物体検出結果をSSD1306 OLEDに日本語表示するシステム（USB/RPiカメラ対応）
"""

import cv2
import time
import logging
import sys
import argparse
from pathlib import Path
from threading import Thread, Event
from ultralytics import YOLO  # YOLOv8物体検出ライブラリ
from picamera2 import Picamera2  # Raspberry Pi公式カメラライブラリ
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306  # SSD1306 OLEDドライバ
from PIL import ImageFont  # 日本語フォント表示用

# ========================================
# 設定定数
# ========================================

# カメラ設定
CAMERA_WIDTH = 640  # カメラ解像度（幅）
CAMERA_HEIGHT = 480  # カメラ解像度（高さ）
CAMERA_FPS = 20  # フレームレート

# YOLOモデル設定
MODEL_NAME = "yolov8n"  # yolov8n（最軽量版、Raspberry Pi推奨）
CONF_THRESHOLD = 0.5  # 信頼度閾値（0.0-1.0、低いほど多く検出）
IOU_THRESHOLD = 0.45  # IoU閾値（重複検出の除去用）

# OLED設定（SSD1306、128x64）
OLED_I2C_BUS = 1  # I²Cバス番号（Raspberry Pi 5では通常1）
OLED_ADDRESS = 0x3C  # I²Cアドレス（0x3Cまたは0x3D、i2cdetect -y 1で確認）
OLED_WIDTH = 128  # OLED幅（ピクセル）
OLED_HEIGHT = 64  # OLED高さ（ピクセル）

# フォント設定（日本語表示用）
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_SIZE_LARGE = 18  # 大きいフォントサイズ（1件目の検出結果用）
FONT_SIZE_SMALL = 14  # 小さいフォントサイズ（2件目以降用）

# 表示設定
MAX_LABELS = 3  # 最大表示ラベル数（128x64の画面では3件が適切）
LABEL_LANG = "ja"  # ラベル言語（"ja"=日本語、"en"=英語）

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
    """
    YOLOv8による物体検出とOLED表示を統合管理するクラス
    初心者向けに機能を整理し、単一ファイルで完結する実装にしています
    Raspberry Pi Camera V3とUSBカメラの両方に対応
    """

    def __init__(self, camera_type='rpi', device_id=0):
        """
        YOLODetectorの初期化
        モデル、カメラ、OLEDの各属性を初期化し、ログ設定を行う

        Args:
            camera_type (str): カメラタイプ（'rpi'=Raspberry Pi Camera V3、'usb'=USBカメラ）
            device_id (int): USBカメラのデバイスID（デフォルト: 0）
        """
        self.model = None
        self.camera_type = camera_type  # カメラタイプを保存
        self.device_id = device_id  # USBカメラのデバイスID
        self.setup_logging()

    def setup_logging(self):
        """
        ログ設定を構成する
        コンソール出力とファイル出力の両方を有効化し、デバッグ時に便利な形式で記録
        """
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
            self.logger.error("接続とパッケージインストールを確認してください")
            self.logger.error("ヒント: pip install ultralytics")
            return False

    def initialize_camera(self):
        """
        カメラの初期化
        camera_typeに応じてRaspberry Pi Camera V3またはUSBカメラを初期化
        """
        if self.camera_type == 'rpi':
            return self._initialize_rpi_camera()
        elif self.camera_type == 'usb':
            return self._initialize_usb_camera()
        else:
            self.logger.error(f"不明なカメラタイプ: {self.camera_type}")
            return False

    def _initialize_rpi_camera(self):
        """
        Raspberry Pi Camera V3の初期化
        元のyolo_picamera_detector.pyと同じ実装
        """
        try:
            self.logger.info("Raspberry Pi Camera V3を初期化中...")
            self.camera = Picamera2()
            config = self.camera.create_preview_configuration(
                main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT)}
            )
            self.camera.configure(config)
            self.camera.start()
            time.sleep(2)  # カメラの安定化待ち（オートフォーカス調整など）
            self.logger.info(f"Raspberry Pi Camera V3初期化完了: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
            return True
        except Exception as e:
            self.logger.error(f"Raspberry Pi Camera V3初期化エラー: {e}")
            self.logger.error("カメラ接続と設定を確認してください")
            self.logger.error("ヒント1: sudo raspi-config で Camera を有効化")
            self.logger.error("ヒント2: 他のプログラムがカメラを使用していないか確認")
            self.logger.error("        sudo pkill -f camera")
            return False

    def _initialize_usb_camera(self):
        """
        USBカメラの初期化
        OpenCVのVideoCaptureを使用
        """
        try:
            self.logger.info(f"USBカメラ（デバイス{self.device_id}）を初期化中...")
            self.camera = cv2.VideoCapture(self.device_id)

            # カメラが正常に開けるか確認
            if not self.camera.isOpened():
                raise Exception(f"USBカメラ（デバイス{self.device_id}）を開けませんでした")

            # 解像度とFPSを設定
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

            # 実際の設定値を取得して確認
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)

            self.logger.info(f"USBカメラ初期化完了: {actual_width}x{actual_height} @ {actual_fps}fps")

            # カメラの安定化待ち
            time.sleep(2)
            return True
        except Exception as e:
            self.logger.error(f"USBカメラ初期化エラー: {e}")
            self.logger.error("カメラ接続とデバイスIDを確認してください")
            self.logger.error("ヒント1: ls /dev/video* でデバイスを確認")
            self.logger.error("ヒント2: v4l2-ctl --list-devices で利用可能なカメラを確認")
            self.logger.error("ヒント3: 他のプログラムがカメラを使用していないか確認")
            return False

    def initialize_oled(self):
        """
        SSD1306 OLEDディスプレイを初期化する
        I2C接続のOLEDデバイスを設定し、日本語表示用フォントを読み込む
        フォント読み込みに失敗した場合はデフォルトフォントにフォールバック
        """
        try:
            self.logger.info(f"OLED初期化中... (アドレス: 0x{OLED_ADDRESS:02X})")

            # I2Cシリアル接続の初期化
            # luma.oledライブラリを使用してSSD1306 OLEDと通信
            serial = i2c(port=OLED_I2C_BUS, address=OLED_ADDRESS)

            # SSD1306デバイスの初期化（128x64、I2C接続）
            self.oled = ssd1306(serial, width=OLED_WIDTH, height=OLED_HEIGHT)

            # コントラストを最大に設定（明るさ調整、これがないと表示されない可能性あり）
            self.oled.contrast(255)
            self.logger.info("OLEDコントラスト設定: 255 (最大)")

            # 日本語フォントの読み込み
            # Noto Sans CJK（中国語・日本語・韓国語対応フォント）を使用
            try:
                self.font_large = ImageFont.truetype(FONT_PATH, FONT_SIZE_LARGE)
                self.font_small = ImageFont.truetype(FONT_PATH, FONT_SIZE_SMALL)
                self.logger.info(f"フォント読み込み完了: {FONT_PATH}")
            except Exception as font_error:
                # フォントが見つからない場合はデフォルトフォントにフォールバック
                # （日本語は表示できないが動作は継続）
                self.logger.warning(f"フォント読み込みエラー: {font_error}")
                self.logger.info("デフォルトフォントを使用します（日本語は表示できません）")
                self.logger.info("ヒント: sudo apt-get install fonts-noto-cjk")
                self.font_large = ImageFont.load_default()
                self.font_small = ImageFont.load_default()

            # 起動メッセージ表示
            with canvas(self.oled) as draw:
                draw.text((10, 20), "起動中...", font=self.font_large, fill="white")

            self.logger.info("OLED初期化完了")
            return True
        except Exception as e:
            self.logger.error(f"OLED初期化エラー: {e}")
            self.logger.error("OLED接続とI²C設定を確認してください")
            self.logger.error("ヒント1: i2cdetect -y 1 でアドレスを確認（通常0x3Cまたは0x3D）")
            self.logger.error("ヒント2: sudo raspi-config で I2C を有効化")
            self.logger.error("ヒント3: 配線を確認（VCC→3.3V, GND→GND, SDA→GPIO2, SCL→GPIO3）")
            self.logger.info("OLED無しで続行...")
            self.oled = None
            return False

    def detect_objects(self, frame):
        """
        YOLOv8で物体検出を実行する

        Args:
            frame (numpy.ndarray): BGR形式の画像フレーム（OpenCV形式）

        Returns:
            list: 検出結果のリスト（class_name, confidence, areaを含む辞書のリスト）
        """
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

                        # バウンディングボックスの面積計算
                        # 将来的に面積順でソートする場合に使用（現在は信頼度順）
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
        """
        検出結果から信頼度上位のものを選択する

        Args:
            detections (list): detect_objectsから返された検出結果リスト

        Returns:
            list: 信頼度順にソートされた上位MAX_LABELS件の検出結果
        """
        if not detections:
            return []

        # 信頼度で降順ソート
        detections.sort(key=lambda x: x['confidence'], reverse=True)

        # 最大MAX_LABELS件まで
        return detections[:MAX_LABELS]

    def format_label(self, class_name):
        """
        クラス名を表示用に整形する

        Args:
            class_name (str): YOLO検出結果の英語クラス名（例: "person", "car"）

        Returns:
            str: 整形されたラベル（LABEL_LANGが"ja"の場合は日本語変換）
        """
        if LABEL_LANG == "ja" and class_name in LABEL_TRANSLATION:
            return LABEL_TRANSLATION[class_name]
        return class_name.title()

    def update_oled(self, detections, fps):
        """
        OLED画面に検出結果とFPSを表示する

        Args:
            detections (list): 表示する検出結果のリスト（select_top_detectionsの出力）
            fps (float): 現在のフレームレート
        """
        if self.oled is None:
            return

        try:
            with canvas(self.oled) as draw:
                # FPS表示（最上部右端）
                fps_text = f"FPS:{fps:.1f}"
                draw.text((80, 0), fps_text, font=self.font_small, fill="white")

                # 検出結果表示（FPSの下から開始）
                if detections:
                    # 検出結果の表示開始位置（FPSと被らないように16ピクセル下から）
                    y_position = 16
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
                    # 検出なし（中央寄せ）
                    draw.text((20, 28), "検出なし", font=self.font_large, fill="white")

        except Exception as e:
            self.logger.error(f"OLED更新エラー: {e}")

    def get_frame(self):
        """
        カメラタイプに応じてフレームを取得する

        Returns:
            numpy.ndarray: BGR形式の画像フレーム（失敗時はNone）
        """
        try:
            if self.camera_type == 'rpi':
                # Raspberry Pi Camera V3の場合
                # Picamera2はRGB形式で出力するため、OpenCVのBGR形式に変換
                frame = self.camera.capture_array()
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                else:
                    frame_bgr = frame
                return frame_bgr

            elif self.camera_type == 'usb':
                # USBカメラの場合
                # VideoCaptureはすでにBGR形式で出力するため変換不要
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.warning("USBカメラからフレーム取得失敗")
                    return None
                return frame

            else:
                return None

        except Exception as e:
            self.logger.error(f"フレーム取得エラー: {e}")
            return None

    def run(self):
        """
        メインループを実行する
        初期化→フレーム取得→物体検出→OLED表示のサイクルを繰り返す
        """
        camera_type_name = "Raspberry Pi Camera V3" if self.camera_type == 'rpi' else f"USBカメラ（デバイス{self.device_id}）"
        self.logger.info(f"YOLO Camera OLED Detector 開始（カメラ: {camera_type_name}）")

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
                frame_bgr = self.get_frame()

                if frame_bgr is None:
                    # フレーム取得失敗時は少し待ってスキップ
                    time.sleep(0.1)
                    continue

                # 物体検出
                detections = self.detect_objects(frame_bgr)
                top_detections = self.select_top_detections(detections)

                # FPS計算（10フレームごとに更新）
                # 毎フレーム計算すると値が不安定になるため、10フレーム平均を使用
                fps_counter += 1
                if fps_counter >= 10:
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
        """
        リソースのクリーンアップ
        カメラタイプに応じて適切な停止処理を実行
        """
        self.logger.info("リソースをクリーンアップ中...")

        try:
            if hasattr(self, 'camera'):
                if self.camera_type == 'rpi':
                    # Raspberry Pi Camera V3の停止
                    self.camera.stop()
                    self.logger.info("Raspberry Pi Camera V3停止完了")
                elif self.camera_type == 'usb':
                    # USBカメラの停止
                    self.camera.release()
                    self.logger.info("USBカメラ停止完了")
        except Exception as e:
            self.logger.error(f"カメラ停止エラー: {e}")

        try:
            if hasattr(self, 'oled') and self.oled:
                with canvas(self.oled) as draw:
                    draw.text((30, 25), "停止", font=self.font_large, fill="white")
                time.sleep(1)
                self.oled.clear()
                self.logger.info("OLED停止完了")
        except Exception as e:
            self.logger.error(f"OLED停止エラー: {e}")


def main():
    """
    メイン関数：コマンドライン引数を処理してYOLODetectorを初期化・実行
    エラー発生時は適切な終了コードを返す
    """
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(
        description='YOLOv8物体検出システム（Raspberry Pi Camera V3 / USBカメラ対応）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # Raspberry Pi Camera V3を使用（デフォルト）
  python3 yolo_camera_detector.py

  # Raspberry Pi Camera V3を明示的に指定
  python3 yolo_camera_detector.py --camera-type rpi

  # USBカメラを使用（デバイス0）
  python3 yolo_camera_detector.py --camera-type usb

  # USBカメラを使用（デバイス1）
  python3 yolo_camera_detector.py --camera-type usb --device 1
        """
    )

    # カメラタイプ引数
    parser.add_argument(
        '-c', '--camera-type',
        type=str,
        choices=['rpi', 'usb'],
        default='rpi',
        help='カメラタイプ（rpi: Raspberry Pi Camera V3、usb: USBカメラ）デフォルト: rpi'
    )

    # デバイスID引数（USBカメラ用）
    parser.add_argument(
        '-d', '--device',
        type=int,
        default=0,
        help='USBカメラのデバイスID（通常0または1）デフォルト: 0'
    )

    # 引数をパース
    args = parser.parse_args()

    # YOLODetectorの初期化
    detector = YOLODetector(camera_type=args.camera_type, device_id=args.device)

    try:
        success = detector.run()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"致命的エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
