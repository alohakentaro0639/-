# Threads バズ投稿分析・リライトツール

Threadsのバズ投稿をリサーチして、パターンを分析し、テーマを入れるだけでバズる投稿を自動生成するCLIツールです。

## 使い方（3ステップ）

```
research → analyze → rewrite
```

### Step 1: バズ投稿を収集

```bash
# キーワードで検索
python main.py research --query "副業"

# 手動で貼り付け
python main.py research --manual

# URLから取得
python main.py research --url https://www.threads.net/@user/post/xxxxx
```

### Step 2: パターンを分析・抽出

```bash
python main.py analyze
```

Claude APIが投稿を分析し、バズる「型」を自動抽出します。

### Step 3: テーマを入れてリライト

```bash
python main.py rewrite --theme "朝活の習慣化"

# 5つ生成してファイルに保存
python main.py rewrite --theme "副業で月5万" --count 5 --save
```

## セットアップ

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を設定
```

## コマンド一覧

| コマンド | 説明 |
|----------|------|
| `research` | バズ投稿を収集する |
| `analyze` | パターン・型を抽出する |
| `rewrite` | テーマでリライトする |
| `status` | 現在の収集・分析状況を確認 |
| `reset` | 全データをリセット |

## 抽出される分析データ

- **パターン名と構造** - 共感型、驚き型など
- **フック技法** - 冒頭で読者を引き込む手法
- **感情トリガー** - エンゲージメントを高める感情的要素
- **共通要素** - 強力なキーワード、文体、改行スタイル
- **エンゲージメントの秘訣** - バズる理由
- **リライトテンプレート** - 穴埋め形式のテンプレート
