# Raspberry Pi 5 YOLO物体検出システム

Raspberry Pi 5とYOLOv8を使用したリアルタイム物体検出システムです。カメラで撮影した映像から物体を検出し、結果を16×2 LCDディスプレイに表示します。

## 📷 概要

このプロジェクトは、初心者向けの教材として設計されており、**単一のPythonファイル**で構成されています。Raspberry Pi 5、Camera V3、YOLOv8、16×2 LCDを組み合わせて、リアルタイムで物体検出を行います。

### 主な機能
- 📹 Raspberry Pi Camera V3からのリアルタイム映像取得
- 🔍 YOLOv8による高精度な物体検出
- 📺 16×2 I2C LCDへの検出結果表示
- 📊 FPS（フレームレート）の計測・表示
- 🌐 日本語対応ラベル（80クラス）
- 📝 詳細なログ出力とエラーハンドリング

## 🛠️ ハードウェア要件

### 必須機器
- **Raspberry Pi 5** （電源27W以上推奨）
- **Raspberry Pi Camera V3** （オートフォーカス対応）
- **16×2 LCD** （LCD1602互換） + I²Cバックパック（PCF8574系）
- **ジャンパワイヤ** （配線用）

### 接続方法
```
Raspberry Pi 5  ←→  16×2 LCD (I²C)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5V              ←→  VCC
GND             ←→  GND
GPIO2 (SDA)     ←→  SDA
GPIO3 (SCL)     ←→  SCL
```

**⚠️ 重要**: I²Cプルアップ電圧は3.3Vを使用してください。5Vプルアップの場合はレベル変換が必要です。

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
```bash
python yolo_picamera_detector.py
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

# LCD設定
LCD_I2C_BUS = 1         # I²Cバス番号
LCD_ADDRESS = 0x27      # I²Cアドレス（0x3Fの場合も）
LCD_COLS = 16           # LCD列数
LCD_ROWS = 2            # LCD行数

# 表示設定
MAX_LABELS = 2          # 最大表示ラベル数
LABEL_LANG = "ja"       # ラベル言語（ja/en）
```

## 📺 LCD表示例

```
Person 95%      ← 検出されたオブジェクト（信頼度）
FPS: 14.2       ← フレームレート
```

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

### LCDが表示されない
```bash
# I²Cアドレスの確認
i2cdetect -y 1

# 一般的なアドレス: 0x27, 0x3F
# yolo_picamera_detector.py内のLCD_ADDRESSを変更
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
├── yolo_picamera_detector.py    # メイン実装ファイル
├── requirements.txt             # 依存関係
├── README.md                   # このファイル
├── CLAUDE.md                   # プロジェクトルール
└── 01_001_rpi_5_yolo_camera_lcd_要件定義書.md
```

### 主要クラス・機能
- `YOLODetector`: メインクラス
  - `initialize_model()`: YOLOモデル初期化
  - `initialize_camera()`: カメラ初期化
  - `initialize_lcd()`: LCD初期化
  - `detect_objects()`: 物体検出実行
  - `update_lcd()`: LCD表示更新

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