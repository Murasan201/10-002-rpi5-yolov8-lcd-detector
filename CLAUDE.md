# Claude Code Rules

このファイルはClaude Codeがプロジェクトを理解し、適切に作業するためのルールファイルです。

## プロジェクト概要
Raspberry Pi 5でYOLOv8を使用したLCDディスプレイ検出システム

## 開発環境
- Platform: Raspberry Pi 5
- Python環境: 仮想環境推奨
- 主要ライブラリ: YOLOv8, OpenCV

## コーディング規約
- Python PEP 8に従う
- 関数とクラスには適切なdocstringを記述
- 変数名は英語で分かりやすく命名

## テスト実行方法
```bash
# テストコマンドが判明次第追記
```

## リント・型チェック実行方法
```bash
# リントコマンドが判明次第追記
```

## 利用可能なMCP（Model Context Protocol）
- Google検索エージェント: `mcp__gemini-google-search__google_search`
- Serena: IDE統合機能（診断、コード実行など）

## その他の注意事項
- 作業開始時に利用可能なMCPを確認し、必要に応じて呼び出して使用すること
- コミット前にテストとリントを実行すること
- 機密情報をコードに含めないこと