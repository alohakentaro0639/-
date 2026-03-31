"""Threads バズ投稿リライター"""

import re
import json
import anthropic
from rich.console import Console

console = Console()


class ThreadsRewriter:
    """バズパターンを使ってテーマに合わせた投稿を生成するクラス"""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-opus-4-6"

    def rewrite_with_theme(self, patterns: dict, theme: str, count: int = 3) -> list[str]:
        """バズパターンを使ってテーマに合わせた投稿を生成"""
        pattern_summary = self._build_pattern_summary(patterns)

        prompt = f"""あなたはThreadsで数万いいねを獲得するバイラル投稿の専門家です。
以下のバズパターン分析に基づき、テーマ「{theme}」で{count}つの投稿を作成してください。

# バズパターン分析

{pattern_summary}

# 作成ルール

1. 各投稿は実際にThreadsに投稿できる形式で書く
2. 抽出されたパターンの型を忠実に適用する
3. テーマの内容を自然に組み込む
4. 読者が「わかる」「シェアしたい」「コメントしたい」と感じる内容に
5. 各投稿は異なるパターン・角度で書き、十分に差別化する

# 出力形式（この形式を厳守）

[投稿1]
（投稿本文をそのまま記載。Threadsに貼り付けてすぐ使える状態で）
[使用パターン: パターン名] [工夫: 一言でポイント]

[投稿2]
...

[投稿3]
...

# テーマ

{theme}"""

        with console.status(
            f"[bold green]'{theme}' で{count}つの投稿を生成中..."
        ):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

        result = response.content[0].text.strip()
        return self._parse_posts(result, count)

    def _build_pattern_summary(self, patterns: dict) -> str:
        """パターンデータを読みやすいテキストに変換"""
        if "raw_analysis" in patterns:
            return patterns["raw_analysis"]

        lines = []

        if "summary" in patterns:
            lines.append(f"## 総評\n{patterns['summary']}\n")

        if "patterns" in patterns and patterns["patterns"]:
            lines.append("## 抽出されたパターン")
            for p in patterns["patterns"]:
                lines.append(f"\n### {p.get('name', 'パターン')}")
                lines.append(p.get("description", ""))
                lines.append(f"構造: {p.get('structure', '')}")
                if p.get("hooks"):
                    lines.append(f"フック: {', '.join(p['hooks'])}")
                if p.get("emotional_triggers"):
                    lines.append(f"感情トリガー: {', '.join(p['emotional_triggers'])}")
            lines.append("")

        if "common_elements" in patterns:
            ce = patterns["common_elements"]
            lines.append("## 共通要素")
            if ce.get("opening_patterns"):
                lines.append(f"冒頭パターン: {', '.join(ce['opening_patterns'])}")
            if ce.get("power_words"):
                lines.append(f"強力な言葉: {', '.join(ce['power_words'])}")
            if ce.get("tone"):
                lines.append(f"トーン: {ce['tone']}")
            lines.append("")

        if "engagement_secrets" in patterns:
            lines.append("## エンゲージメントの秘訣")
            for s in patterns["engagement_secrets"]:
                lines.append(f"• {s}")
            lines.append("")

        if "rewrite_template" in patterns:
            lines.append(f"## リライトテンプレート\n{patterns['rewrite_template']}")

        return "\n".join(lines)

    def _parse_posts(self, text: str, expected_count: int) -> list[str]:
        """生成されたテキストから投稿を分割"""
        parts = re.split(r'\[投稿\d+\]', text)
        posts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 20]

        if not posts:
            return [text]

        return posts
