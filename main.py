#!/usr/bin/env python3
"""Threads バズ投稿分析・リライトツール"""

import click
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

load_dotenv()

console = Console()

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
POSTS_FILE = DATA_DIR / "posts.json"
PATTERNS_FILE = DATA_DIR / "patterns.json"


def get_api_key() -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]エラー: ANTHROPIC_API_KEY が設定されていません。")
        console.print("[yellow].env ファイルに ANTHROPIC_API_KEY=your_key_here を追加してください。")
        raise click.Abort()
    return api_key


def load_posts() -> list[dict]:
    if POSTS_FILE.exists():
        return json.loads(POSTS_FILE.read_text(encoding="utf-8"))
    return []


def save_posts(posts: list[dict]):
    POSTS_FILE.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")


def load_patterns() -> dict:
    if PATTERNS_FILE.exists():
        return json.loads(PATTERNS_FILE.read_text(encoding="utf-8"))
    return {}


def save_patterns(patterns: dict):
    PATTERNS_FILE.write_text(json.dumps(patterns, ensure_ascii=False, indent=2), encoding="utf-8")


@click.group()
@click.version_option("1.0.0")
def cli():
    """
    \b
    Threads バズ投稿分析・リライトツール

    1. research  - バズ投稿を収集
    2. analyze   - パターンを分析・抽出
    3. rewrite   - テーマを入れてリライト
    """
    pass


@cli.command()
@click.option("--query", "-q", help="検索キーワード（例: 副業 筋トレ）")
@click.option("--count", "-n", default=10, show_default=True, help="検索で収集する投稿数")
@click.option("--manual", "-m", is_flag=True, help="投稿を手動で入力する")
@click.option("--url", "-u", help="Threads投稿のURL")
@click.option("--clear", is_flag=True, help="既存の収集データをクリアして新規収集")
def research(query, count, manual, url, clear):
    """Threadsのバズ投稿をリサーチして収集する"""
    from src.researcher import ThreadsResearcher

    console.print(Panel.fit("[bold]Research Mode[/] - バズ投稿収集", style="blue"))

    researcher = ThreadsResearcher()
    existing_posts = [] if clear else load_posts()
    new_posts = []

    if manual:
        console.print("[cyan]手動入力モード: バズ投稿のテキストを貼り付けてください\n")
        new_posts = researcher.manual_input()
    elif url:
        post = researcher.fetch_from_url(url)
        if post:
            new_posts = [post]
    elif query:
        console.print(f"[cyan]'{query}' でThreadsバズ投稿を検索中...\n")
        new_posts = researcher.search_web(query, count)
    else:
        mode = Prompt.ask(
            "モードを選択",
            choices=["search", "manual", "url"],
            default="manual"
        )
        if mode == "search":
            q = Prompt.ask("検索キーワードを入力")
            new_posts = researcher.search_web(q, count)
        elif mode == "manual":
            new_posts = researcher.manual_input()
        elif mode == "url":
            u = Prompt.ask("Threads投稿のURLを入力")
            post = researcher.fetch_from_url(u)
            if post:
                new_posts = [post]

    if new_posts:
        all_posts = existing_posts + new_posts
        save_posts(all_posts)

        table = Table(title=f"収集した投稿 (合計: {len(all_posts)}件)")
        table.add_column("No.", style="cyan", width=5)
        table.add_column("内容（先頭60文字）", style="white")
        table.add_column("いいね", style="yellow", width=8)
        table.add_column("ソース", style="green", width=12)

        for i, post in enumerate(all_posts[-10:], 1):
            body_preview = post.get("body", "")[:60].replace("\n", " ")
            likes = str(post.get("likes", "-"))
            source = post.get("source", "-")
            table.add_row(str(i), body_preview, likes, source)

        console.print(table)
        console.print(f"\n[green]✓ {len(new_posts)}件の投稿を追加しました（合計: {len(all_posts)}件）")
        console.print(f"[dim]保存先: {POSTS_FILE}")
        console.print("\n次のステップ: [bold cyan]python main.py analyze[/]")
    else:
        console.print("[yellow]投稿が収集されませんでした。")


@cli.command()
@click.option("--min-posts", default=3, show_default=True, help="分析に必要な最低投稿数")
def analyze(min_posts):
    """収集した投稿を分析してバズるパターン・型を抽出する"""
    from src.analyzer import ThreadsAnalyzer

    console.print(Panel.fit("[bold]Analyze Mode[/] - パターン抽出", style="green"))

    api_key = get_api_key()
    posts = load_posts()

    if len(posts) < min_posts:
        console.print(f"[red]投稿が{min_posts}件未満です（現在: {len(posts)}件）")
        console.print("[yellow]先に 'research' コマンドで投稿を収集してください。")
        return

    console.print(f"[cyan]{len(posts)}件の投稿を分析します...")

    analyzer = ThreadsAnalyzer(api_key)
    patterns = analyzer.analyze_posts(posts)
    save_patterns(patterns)

    console.print("\n[bold green]✓ 分析完了！バズる型を抽出しました\n")

    if "summary" in patterns:
        console.print(Panel(patterns["summary"], title="総評", style="blue"))

    if "patterns" in patterns and patterns["patterns"]:
        console.print("\n[bold]抽出されたパターン:[/]")
        for i, pattern in enumerate(patterns["patterns"], 1):
            console.print(f"\n[cyan bold]{i}. {pattern.get('name', 'パターン')}[/]")
            console.print(f"  {pattern.get('description', '')}")
            if pattern.get("structure"):
                console.print(f"  [dim]構造: {pattern['structure']}[/]")

    if "engagement_secrets" in patterns:
        console.print("\n[bold]エンゲージメントの秘訣:[/]")
        for secret in patterns["engagement_secrets"]:
            console.print(f"  • {secret}")

    if "rewrite_template" in patterns:
        console.print(Panel(
            patterns["rewrite_template"],
            title="リライトテンプレート",
            style="yellow"
        ))

    console.print(f"\n[dim]保存先: {PATTERNS_FILE}")
    console.print("\n次のステップ: [bold cyan]python main.py rewrite --theme \"あなたのテーマ\"[/]")


@cli.command()
@click.option("--theme", "-t", required=True, help="投稿のテーマ（例: 朝活の習慣化）")
@click.option("--count", "-n", default=3, show_default=True, help="生成する投稿のバリエーション数")
@click.option("--save", "-s", is_flag=True, help="生成した投稿をファイルに保存する")
def rewrite(theme, count, save):
    """テーマを入れてバズる投稿にリライトする"""
    from src.rewriter import ThreadsRewriter

    console.print(Panel.fit("[bold]Rewrite Mode[/] - 投稿生成", style="yellow"))

    api_key = get_api_key()
    patterns = load_patterns()

    if not patterns:
        console.print("[red]分析データがありません。")
        console.print("[yellow]先に 'analyze' コマンドでパターンを抽出してください。")
        return

    console.print(f"[cyan]テーマ '{theme}' で{count}つの投稿を生成します...\n")

    rewriter = ThreadsRewriter(api_key)
    posts = rewriter.rewrite_with_theme(patterns, theme, count)

    console.print(f"[bold green]✓ {len(posts)}つの投稿を生成しました！\n")

    output_lines = []
    for i, post_content in enumerate(posts, 1):
        console.print(Panel(post_content, title=f"投稿 {i}", style="green"))
        output_lines.append(f"=== 投稿 {i} ===\n{post_content}\n")

    if save:
        safe_theme = theme[:20].replace(" ", "_").replace("/", "_")
        output_file = DATA_DIR / f"rewrite_{safe_theme}.txt"
        output_file.write_text("\n".join(output_lines), encoding="utf-8")
        console.print(f"\n[dim]保存先: {output_file}")


@cli.command()
def status():
    """現在の収集・分析状況を確認する"""
    console.print(Panel.fit("[bold]Status[/] - 現在の状況", style="white"))

    posts = load_posts()
    patterns = load_patterns()

    table = Table(show_header=False, box=None)
    table.add_column("項目", style="cyan")
    table.add_column("状態", style="white")

    table.add_row("収集した投稿数", f"{len(posts)} 件")
    table.add_row("分析データ", "あり" if patterns else "なし")
    table.add_row(
        "抽出パターン数",
        str(len(patterns.get("patterns", []))) if patterns else "0"
    )

    console.print(table)

    if posts:
        console.print("\n[dim]最新の投稿:[/]")
        for post in posts[-3:]:
            preview = post.get("body", "")[:60].replace("\n", " ")
            console.print(f"  • {preview}...")


@cli.command()
@click.confirmation_option(prompt="全データを削除してもよいですか？")
def reset():
    """収集・分析データをすべてリセットする"""
    if POSTS_FILE.exists():
        POSTS_FILE.unlink()
    if PATTERNS_FILE.exists():
        PATTERNS_FILE.unlink()
    console.print("[green]✓ データをリセットしました。")


if __name__ == "__main__":
    cli()
