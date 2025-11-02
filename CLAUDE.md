# Claude Code Rules

このファイルはClaude Codeがプロジェクトを理解し、適切に作業するためのルールファイルです。

## プロジェクト概要
Raspberry Pi 5でYOLOv8を使用したLCDディスプレイ検出システム

## 開発環境
- Platform: Raspberry Pi 5
- Python環境: 仮想環境推奨
- 主要ライブラリ: YOLOv8, OpenCV

## コーディング規約

本プロジェクトでは、初心者向けの教育教材として最適なコード品質を目指します。

### 適用ガイドライン
- **COMMENT_STYLE_GUIDE.md**: コメント記載の標準化
- **python_coding_guidelines.md**: Pythonコーディング全般の標準化

### 基本規約
- **Python PEP 8**: インデント（4スペース）、命名規則（snake_case、PascalCase、UPPER_CASE）
- **docstring**: 全ての関数・クラスに記述（初心者にわかりやすく日本語）
- **ファイルヘッダー**: シバン＋docstring＋要件定義書への参照
- **if __name__ == "__main__":**: 実行可能なファイルに必ず含める
- **try-finally**: リソースのクリーンアップを確実に実行
- **エラーメッセージ**: ユーザー向けの対処方法を提示
- **初心者向けコメント**: ライブラリ仕様、トラブルシューティング、ハードウェア固有情報を記載

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