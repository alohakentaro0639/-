"""Threads バズ投稿リサーチャー"""

import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()


class ThreadsResearcher:
    """Threadsのバズ投稿を収集するクラス"""

    def search_web(self, query: str, count: int = 10) -> list[dict]:
        """DuckDuckGo でThreadsの投稿を検索"""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            console.print("[red]duckduckgo-search がインストールされていません。")
            console.print("[yellow]pip install duckduckgo-search を実行してください。")
            return []

        search_query = f"site:threads.net {query}"
        results = []

        with console.status(f"[bold green]'{query}' を検索中..."):
            try:
                with DDGS() as ddgs:
                    for r in ddgs.text(search_query, max_results=count):
                        body = r.get("body", "").strip()
                        if body and len(body) > 20:
                            results.append({
                                "title": r.get("title", ""),
                                "url": r.get("href", ""),
                                "body": body,
                                "likes": "",
                                "source": "web_search"
                            })
            except Exception as e:
                console.print(f"[red]検索エラー: {e}")

        console.print(f"[green]{len(results)}件の投稿が見つかりました。")
        return results

    def fetch_from_url(self, url: str) -> dict | None:
        """Threads投稿URLから内容を取得"""
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            with console.status("[bold green]URLからデータ取得中..."):
                response = httpx.get(
                    url, headers=headers, follow_redirects=True, timeout=15
                )
                soup = BeautifulSoup(response.text, "html.parser")

                og_desc = soup.find("meta", attrs={"property": "og:description"})
                og_title = soup.find("meta", attrs={"property": "og:title"})

                content = (
                    og_desc["content"]
                    if og_desc and og_desc.get("content")
                    else ""
                )
                title = (
                    og_title["content"]
                    if og_title and og_title.get("content")
                    else ""
                )

                if content:
                    console.print(f"[green]取得成功: {content[:60]}...")
                    return {
                        "title": title,
                        "url": url,
                        "body": content,
                        "likes": "",
                        "source": "url"
                    }
                else:
                    console.print(
                        "[yellow]投稿の内容を取得できませんでした。"
                        "手動入力をお試しください。"
                    )
        except Exception as e:
            console.print(f"[red]URL取得エラー: {e}")

        return None

    def manual_input(self) -> list[dict]:
        """手動で投稿を入力"""
        posts = []
        console.print(
            "[dim]投稿テキストを貼り付けてください。"
            "空行を2回入力で1投稿確定。'q' で終了。\n"
        )

        while True:
            post_num = len(posts) + 1
            console.print(f"[cyan bold]投稿 {post_num}:[/]")

            lines = []
            empty_count = 0

            while True:
                try:
                    line = input()
                except EOFError:
                    return posts

                if line.lower() == "q":
                    return posts

                if line == "":
                    empty_count += 1
                    if empty_count >= 2 and lines:
                        break
                    elif empty_count >= 2:
                        console.print("[dim]テキストを入力してください...")
                        empty_count = 0
                else:
                    empty_count = 0
                    lines.append(line)

            if not lines:
                continue

            post_text = "\n".join(lines)
            likes = Prompt.ask(
                "  [dim]いいね・リポスト数（わからなければ空欄）", default=""
            )

            posts.append({
                "body": post_text,
                "likes": likes,
                "source": "manual",
                "url": ""
            })

            console.print(f"[green]  ✓ 追加しました（{len(posts)}件）\n")

            if not Confirm.ask("  続けて入力しますか？", default=True):
                break

        return posts
