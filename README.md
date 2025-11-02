# Raspberry Pi 5 YOLO物体検出システム

Raspberry Pi 5とYOLOv8を使用したリアルタイム物体検出システムです。カメラで撮影した映像から物体を検出し、結果をSSD1306 OLEDディスプレイに日本語で表示します。

## 📷 概要

このプロジェクトは、初心者向けの教材として設計されており、**単一のPythonファイル**で構成されています。Raspberry Pi 5、Camera V3またはUSBカメラ、YOLOv8、SSD1306 OLED（128×64）を組み合わせて、リアルタイムで物体検出を行います。

### 提供ファイル
- **yolo_picamera_detector.py**: Raspberry Pi Camera V3専用版
- **yolo_camera_detector.py**: Raspberry Pi Camera V3 / USBカメラ両対応版（コマンドライン引数で切り替え可能）

### 主な機能
- 📹 Raspberry Pi Camera V3 / USBカメラからのリアルタイム映像取得
- 🔍 YOLOv8による高精度な物体検出
- 📺 SSD1306 OLED（128×64, I2C）への日本語表示
- 📊 FPS（フレームレート）の計測・表示
- 🌐 日本語対応ラベル（80クラス）
- 📝 詳細なログ出力とエラーハンドリング
- 🎥 カメラタイプの切り替え（コマンドライン引数）

## 🛠️ ハードウェア要件

### 必須機器
- **Raspberry Pi 5** （電源27W以上推奨）
- **カメラ**（以下のいずれか）
  - **Raspberry Pi Camera V3** （オートフォーカス対応、推奨）
  - **USBカメラ** （UVC対応、640×480以上推奨）
- **SSD1306 OLED** （128×64ピクセル、I²C接続、0.96インチ推奨）
- **ジャンパワイヤ** （配線用）

### 接続方法
```
Raspberry Pi 5  ←→  SSD1306 OLED (I²C)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3.3V            ←→  VCC
GND             ←→  GND
GPIO2 (SDA)     ←→  SDA
GPIO3 (SCL)     ←→  SCL
```

**⚠️ 重要**:
- 3.3V OLEDを使用してください。5V OLEDの場合はBSS138方式のレベル変換モジュールが必要です。
- I²Cアドレスは通常 **0x3C** または **0x3D** です。

## 💻 ソフトウェア要件

- **OS**: Raspberry Pi OS (64-bit) 最新安定版
- **Python**: 3.11以上
- **カメラ有効化**: `raspi-config`でCamera interfaceを有効にする
- **I²C有効化**: `raspi-config`でI2C interfaceを有効にする

## ⚡ クイックスタート

### 1. リポジトリのクローン
```bash
git clone https://github.com/Murasan201/10-002-rpi5-yolov8-lcd-detector.git
cd 10-002-rpi5-yolov8-lcd-detector
```

### 2. 仮想環境の作成（推奨）
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. システム設定の確認
```bash
# カメラが認識されているか確認
libcamera-hello --list-cameras

# I²Cデバイスの確認
i2cdetect -y 1
```

### 5. 実行

#### Raspberry Pi Camera V3を使用する場合
```bash
# yolo_picamera_detector.py（Camera V3専用版）
python3 yolo_picamera_detector.py

# または yolo_camera_detector.py（両対応版）
python3 yolo_camera_detector.py --camera-type rpi
```

#### USBカメラを使用する場合
```bash
# yolo_camera_detector.py（両対応版）のみ対応
python3 yolo_camera_detector.py --camera-type usb

# USBカメラのデバイスIDを指定（デフォルト: 0）
python3 yolo_camera_detector.py --camera-type usb --device 1
```

#### ヘルプの表示
```bash
python3 yolo_camera_detector.py --help
```

## 📋 設定

すべての設定は`yolo_picamera_detector.py`内の定数として定義されています：

```python
# カメラ設定
CAMERA_WIDTH = 640      # 解像度幅
CAMERA_HEIGHT = 480     # 解像度高さ
CAMERA_FPS = 20         # フレームレート

# YOLO設定
MODEL_NAME = "yolov8n"       # モデル名（軽量版）
CONF_THRESHOLD = 0.5         # 信頼度閾値
IOU_THRESHOLD = 0.45         # IoU閾値

# OLED設定
OLED_I2C_BUS = 1        # I²Cバス番号
OLED_ADDRESS = 0x3C     # I²Cアドレス（0x3Dの場合も）
OLED_WIDTH = 128        # OLED幅（ピクセル）
OLED_HEIGHT = 64        # OLED高さ（ピクセル）

# フォント設定
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_SIZE_LARGE = 18    # 大きいフォントサイズ
FONT_SIZE_SMALL = 14    # 小さいフォントサイズ

# 表示設定
MAX_LABELS = 3          # 最大表示ラベル数
LABEL_LANG = "ja"       # ラベル言語（ja/en）
```

## 🎥 コマンドライン引数（yolo_camera_detector.py）

`yolo_camera_detector.py`では、以下のコマンドライン引数が使用できます：

```bash
# カメラタイプの指定
-c, --camera-type {rpi,usb}
    カメラタイプ（rpi: Raspberry Pi Camera V3、usb: USBカメラ）
    デフォルト: rpi

# USBカメラのデバイスID指定
-d, --device DEVICE_ID
    USBカメラのデバイスID（通常0または1）
    デフォルト: 0
```

### 使用例
```bash
# Raspberry Pi Camera V3を使用（デフォルト）
python3 yolo_camera_detector.py

# Raspberry Pi Camera V3を明示的に指定
python3 yolo_camera_detector.py --camera-type rpi

# USBカメラ（デバイス0）を使用
python3 yolo_camera_detector.py --camera-type usb

# USBカメラ（デバイス1）を使用
python3 yolo_camera_detector.py -c usb -d 1
```

## 📺 OLED表示例

```
1.人 95%           FPS:14.2
2.椅子 82%
3.ボトル 76%
```

128×64ピクセルのOLEDディスプレイに、検出された物体を日本語で表示します。最大3つまでの検出結果を同時に表示可能です。

## 🎯 対応オブジェクト

COCO データセットの80クラスに対応：
- 人物（Person）、動物（Cat, Dog, Bird等）
- 乗り物（Car, Bus, Bicycle等）
- 日用品（Bottle, Cup, Chair等）
- 食べ物（Apple, Pizza, Banana等）

## 🔧 トラブルシューティング

### カメラが認識されない
```bash
# カメラの接続確認
libcamera-hello --list-cameras

# カメラが使用中の場合
sudo systemctl stop motion
sudo pkill -f camera
```

### OLEDが表示されない
```bash
# I²Cアドレスの確認
i2cdetect -y 1

# 一般的なアドレス: 0x3C, 0x3D
# yolo_picamera_detector.py または yolo_camera_detector.py 内のOLED_ADDRESSを変更

# 日本語フォントのインストール（必要な場合）
sudo apt-get update
sudo apt-get install fonts-noto-cjk
```

**重要**: OLEDが正常に表示されない場合、コントラスト設定が必要です。最新版のコード（yolo_camera_detector.py）では`device.contrast(255)`が設定されています。

### USBカメラが認識されない（yolo_camera_detector.py使用時）
```bash
# 利用可能なカメラデバイスの確認
ls /dev/video*

# カメラデバイスの詳細情報
v4l2-ctl --list-devices

# デバイス0を使用する場合
python3 yolo_camera_detector.py --camera-type usb --device 0
```

### パフォーマンスが低い
- 解像度を下げる（320×240推奨）
- より軽量なモデルを使用
- GPU/メモリ設定を調整

```bash
# GPU メモリ設定
sudo raspi-config
# Advanced Options → Memory Split → 256
```

## 📈 性能目標

- **フレームレート**: 10FPS以上（640×480, yolov8n使用時）
- **検出精度**: COCO標準ベンチマーク準拠
- **応答性**: リアルタイム表示（遅延 < 100ms）

## 📚 開発者向け情報

### ファイル構成
```
10-002-rpi5-yolov8-lcd-detector/
├── yolo_picamera_detector.py    # Raspberry Pi Camera V3専用版
├── yolo_camera_detector.py      # Camera V3 / USBカメラ両対応版
├── requirements.txt             # 依存関係
├── README.md                   # このファイル
├── CLAUDE.md                   # プロジェクトルール
├── COMMENT_STYLE_GUIDE.md      # コメント記載標準
└── 01_001_rpi_5_yolo_camera_lcd_要件定義書.md
```

### 主要クラス・機能
- `YOLODetector`: メインクラス
  - `initialize_model()`: YOLOモデル初期化
  - `initialize_camera()`: カメラ初期化（yolo_camera_detector.pyではカメラタイプに応じて分岐）
  - `initialize_oled()`: OLED初期化とフォント読み込み（コントラスト設定含む）
  - `detect_objects()`: 物体検出実行
  - `update_oled()`: OLED表示更新（日本語対応）
  - `get_frame()`: カメラタイプに応じたフレーム取得（yolo_camera_detector.pyのみ）
  - `cleanup()`: リソースのクリーンアップ

### ログファイル
実行時に`detector.log`が生成され、詳細なログが記録されます。

## 🚀 今後の拡張予定

- [ ] Hailo-8L アクセラレータ対応
- [ ] Web UIでの遠隔監視
- [ ] 動画・画像保存機能
- [ ] カスタムモデル対応
- [ ] GPIO停止ボタン対応

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 👥 コントリビューション

プルリクエストやイシューの報告を歓迎します。初心者向け教材としての性格を保ちつつ、機能改善にご協力ください。

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/Murasan201/10-002-rpi5-yolov8-lcd-detector/issues)
- **Wiki**: プロジェクトWikiで詳細情報を確認

---

**🎓 教育目的**: このプロジェクトは学習用途で設計されており、単一ファイル構成でコードが理解しやすくなっています。