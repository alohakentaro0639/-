"""Threads バズ投稿パターン分析"""

import json
import anthropic
from rich.console import Console

console = Console()


class ThreadsAnalyzer:
    """Claude APIを使ってバズ投稿のパターンを分析・抽出するクラス"""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-opus-4-6"

    def analyze_posts(self, posts: list[dict]) -> dict:
        """投稿リストを分析してバズるパターンを抽出"""
        posts_text = self._format_posts(posts)

        prompt = f"""あなたはSNSマーケティングとコピーライティングの専門家です。
以下のThreadsバズ投稿を詳細に分析し、「バズる投稿の型」を抽出してください。

# 分析対象の投稿

{posts_text}

# 出力形式

以下のJSON構造のみを返してください（JSON以外は一切出力しないこと）：
{{
  "summary": "これらの投稿に共通する傾向の総評（3文程度）",
  "patterns": [
    {{
      "name": "パターン名（例: 共感→解決型、驚き→深掘り型）",
      "description": "このパターンの特徴と効果",
      "structure": "冒頭・展開・結末の構造説明",
      "hooks": ["冒頭のフック技法1", "フック技法2"],
      "emotional_triggers": ["感情トリガー1", "感情トリガー2"],
      "format_tips": "フォーマット上の特徴（長さ・改行・記号等）",
      "example_excerpt": "サンプル投稿からの引用"
    }}
  ],
  "common_elements": {{
    "opening_patterns": ["冒頭パターン1", "冒頭パターン2"],
    "closing_patterns": ["結末パターン1", "結末パターン2"],
    "power_words": ["強力なキーワード・表現"],
    "average_length": "平均的な文字数の目安",
    "line_break_style": "改行スタイルの説明",
    "tone": "全体的なトーン・文体の特徴"
  }},
  "engagement_secrets": [
    "エンゲージメントを高める秘訣1",
    "秘訣2",
    "秘訣3"
  ],
  "rewrite_template": "リライト時に使える穴埋めテンプレート（[テーマ]などの変数を使用）"
}}"""

        with console.status(
            "[bold green]Claude が投稿を分析中... (30秒ほどかかります)"
        ):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

        result_text = response.content[0].text.strip()

        try:
            if "```json" in result_text:
                result_text = result_text.split("```json", 1)[1].split("```", 1)[0]
            elif "```" in result_text:
                result_text = result_text.split("```", 1)[1].split("```", 1)[0]

            return json.loads(result_text.strip())
        except json.JSONDecodeError as e:
            console.print(f"[yellow]JSONパースエラー: {e}")
            return {
                "summary": "分析完了（JSONパースエラーのためテキスト形式で保存）",
                "raw_analysis": result_text,
                "patterns": []
            }

    def _format_posts(self, posts: list[dict]) -> str:
        """投稿リストをプロンプト用テキストに整形"""
        formatted = []
        for i, post in enumerate(posts, 1):
            body = post.get("body", "").strip()
            if not body:
                continue

            parts = [f"【投稿{i}】"]
            if post.get("likes"):
                parts.append(f"エンゲージメント: {post['likes']}")
            parts.append(body)
            parts.append("---")
            formatted.append("\n".join(parts))

        return "\n\n".join(formatted)
