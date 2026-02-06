"""
Zlibrary 批量下载工具 - 从list.txt解析标记版本并下载
支持：
- 解析标记了v的版本
- Dry-run模式（预览下载内容）
- 下载次数限制检查
- 断点续传（待下载任务持久化）
"""
import sys
import os
import io
import json
import re
import time
from datetime import datetime
from pathlib import Path

# Windows终端设置UTF-8编码（立即输出）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', write_through=True, line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', write_through=True, line_buffering=True)

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Zlibrary import Zlibrary

# ========== 配置区域 ==========
# 默认登录信息
DEFAULT_EMAIL = ""
DEFAULT_PASSWORD = ""

# 或者使用Remix Token（推荐）
DEFAULT_REMIX_USERID = ""
DEFAULT_REMIX_USERKEY = ""

# 下载配置
DEFAULT_INPUT_FILE = "list.txt"
DEFAULT_OUTPUT_DIR = "downloads"
DEFAULT_STATE_FILE = "download_state.json"
DEFAULT_MAX_DOWNLOADS_PER_DAY = 10  # 每日最大下载次数

# 网络超时设置（秒）
REQUEST_TIMEOUT = 2
# ===============================


class DownloadState:
    """下载状态管理类"""

    def __init__(self, state_file: str):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """加载状态文件"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[警告] 加载状态文件失败: {e}，使用默认状态")
        return {
            "downloaded": [],  # 已下载的书籍
            "pending": [],  # 待下载的书籍（因次数限制未下载）
            "failed": [],  # 下载失败的书籍
            "last_update": None
        }

    def save(self):
        """保存状态到文件"""
        self.state["last_update"] = datetime.now().isoformat()
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def add_downloaded(self, book: dict):
        """添加已下载的书籍"""
        book_key = self._get_book_key(book)
        if book_key not in [self._get_book_key(b) for b in self.state["downloaded"]]:
            self.state["downloaded"].append(book)
        # 从待下载列表中移除
        self.state["pending"] = [b for b in self.state["pending"]
                              if self._get_book_key(b) != book_key]

    def add_pending(self, book: dict):
        """添加待下载的书籍"""
        book_key = self._get_book_key(book)
        if book_key not in [self._get_book_key(b) for b in self.state["pending"]]:
            self.state["pending"].append(book)

    def add_failed(self, book: dict, reason: str):
        """添加下载失败的书籍"""
        book_key = self._get_book_key(book)
        # 检查是否已存在
        existing = next((b for b in self.state["failed"]
                       if self._get_book_key(b) == book_key), None)
        if existing:
            existing["fail_reason"] = reason
            existing["fail_count"] = existing.get("fail_count", 0) + 1
        else:
            self.state["failed"].append({
                **book,
                "fail_reason": reason,
                "fail_count": 1
            })

    def _get_book_key(self, book: dict) -> str:
        """生成书籍唯一标识"""
        return f"{book['id']}_{book['hash']}"

    def get_pending_count(self) -> int:
        """获取待下载书籍数量"""
        return len(self.state["pending"])

    def get_downloaded_count(self) -> int:
        """获取已下载书籍数量"""
        return len(self.state["downloaded"])


def parse_list_file(input_file: str) -> list:
    """
    解析list.txt文件，提取要下载的版本

    规则:
    1. 有 v 标记的版本优先下载
    2. 如果没有 v 标记但只有一个版本，自动下载

    Args:
        input_file: list.txt文件路径

    Returns:
        要下载的书籍版本列表
    """
    books_to_download = []

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_book_info = {}
    in_version_block = False
    marked_versions = {}  # {book_key: book_info}
    all_versions = {}     # {book_title: [book_info_list]}

    for line in lines:
        # 保留行首空白（用于识别v标记），但去除尾随空白
        stripped_line = line.strip()

        # 检查是否在版本块中且标记了v
        # 支持 "v【版本 1】", "v 【版本 1】", "v   【版本 1】" 等格式
        if re.match(r'^\s*v\s*【版本\s*\d+】', stripped_line):
            in_version_block = True
            continue
        elif re.match(r'^\s*【版本\s*\d+】', stripped_line):
            # 未标记v的版本
            in_version_block = True
            continue

        # 解析书籍信息
        if in_version_block:
            if stripped_line.startswith('书名:'):
                current_book_info['title'] = stripped_line.split(':', 1)[1].strip()
            elif stripped_line.startswith('作者:'):
                current_book_info['author'] = stripped_line.split(':', 1)[1].strip()
            elif stripped_line.startswith('出版社:'):
                current_book_info['publisher'] = stripped_line.split(':', 1)[1].strip()
            elif stripped_line.startswith('年份:'):
                current_book_info['year'] = stripped_line.split(':', 1)[1].strip()
            elif stripped_line.startswith('语言:'):
                current_book_info['language'] = stripped_line.split(':', 1)[1].strip()
            elif stripped_line.startswith('ID:'):
                current_book_info['id'] = stripped_line.split(':', 1)[1].strip()
            elif stripped_line.startswith('Hash:'):
                current_book_info['hash'] = stripped_line.split(':', 1)[1].strip()

                # 版本块结束
                if current_book_info.get('id') and current_book_info.get('hash'):
                    title = current_book_info.get('title', 'unknown')

                    # 收集所有版本
                    if title not in all_versions:
                        all_versions[title] = []
                    all_versions[title].append(current_book_info.copy())

                current_book_info = {}
                in_version_block = False

    # 第二遍：收集带v标记的版本
    in_version_block = False
    current_book_info = {}

    for line in lines:
        stripped_line = line.strip()
        is_marked = re.match(r'^\s*v\s*【版本\s*\d+】', stripped_line) is not None

        if is_marked or re.match(r'^\s*【版本\s*\d+】', stripped_line):
            in_version_block = True
            if is_marked:
                current_book_info['_marked'] = True
            else:
                current_book_info['_marked'] = False
            continue

        if in_version_block:
            if stripped_line.startswith('书名:'):
                current_book_info['title'] = stripped_line.split(':', 1)[1].strip()
            elif stripped_line.startswith('作者:'):
                current_book_info['author'] = stripped_line.split(':', 1)[1].strip()
            elif stripped_line.startswith('出版社:'):
                current_book_info['publisher'] = stripped_line.split(':', 1)[1].strip()
            elif stripped_line.startswith('年份:'):
                current_book_info['year'] = stripped_line.split(':', 1)[1].strip()
            elif stripped_line.startswith('语言:'):
                current_book_info['language'] = stripped_line.split(':', 1)[1].strip()
            elif stripped_line.startswith('ID:'):
                current_book_info['id'] = stripped_line.split(':', 1)[1].strip()
            elif stripped_line.startswith('Hash:'):
                current_book_info['hash'] = stripped_line.split(':', 1)[1].strip()

                if current_book_info.get('id') and current_book_info.get('hash'):
                    # 如果有v标记，添加到标记列表
                    if current_book_info.get('_marked'):
                        book_key = f"{current_book_info['id']}_{current_book_info['hash']}"
                        marked_versions[book_key] = {k: v for k, v in current_book_info.items() if k != '_marked'}

                current_book_info = {}
                in_version_block = False

    # 生成最终下载列表：
    # 1. 优先使用带v标记的版本
    # 2. 没有v标记但只有一个版本的，自动添加
    for title, versions in all_versions.items():
        # 检查是否有标记版本
        has_marked = False
        for version in versions:
            book_key = f"{version['id']}_{version['hash']}"
            if book_key in marked_versions:
                has_marked = True
                if book_key not in [f"{b['id']}_{b['hash']}" for b in books_to_download]:
                    books_to_download.append(version)
                break

        # 如果没有标记且只有一个版本，自动下载
        if not has_marked and len(versions) == 1:
            if versions[0]['id'] not in [b['id'] for b in books_to_download]:
                books_to_download.append(versions[0])

    return books_to_download


def download_book(zlib: Zlibrary, book_id: str, book_hash: str, output_dir: str, title: str, author: str, publisher: str) -> tuple:
    """
    下载单本书籍

    Args:
        zlib: Zlibrary实例
        book_id: 书籍ID
        book_hash: 书籍Hash
        output_dir: 输出目录
        title: 书名（用于显示）
        author: 作者（用于显示）
        publisher: 出版社（用于显示）

    Returns:
        (成功标志, 文件路径或错误信息)
    """
    try:
        print(f"      [下载请求] 正在获取下载链接...")
        start_time = time.time()

        # 使用 downloadBook 方法
        book_dict = {
            "id": book_id,
            "hash": book_hash
        }

        result = zlib.downloadBook(book_dict)

        elapsed_time = time.time() - start_time

        if result is None:
            print(f"      [下载请求] 完成 (耗时: {elapsed_time:.2f}秒)")
            # 检查是否是次数限制
            downloads_left = zlib.getDownloadsLeft()
            if downloads_left <= 0:
                return False, "download_limit_reached", "今日下载次数已用尽"
            return False, "download_failed", "下载失败，返回结果为空"

        filename, content = result
        print(f"      [下载请求] 完成 (耗时: {elapsed_time:.2f}秒)")

        # 保存文件
        print(f"      [文件保存] 正在保存: {filename}")
        save_start = time.time()

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(content)

        save_elapsed = time.time() - save_start
        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)

        print(f"      [文件保存] 完成 (大小: {file_size_mb:.2f}MB, 耗时: {save_elapsed:.2f}秒)")

        return True, filepath, "下载成功"

    except Exception as e:
        error_msg = str(e)
        elapsed_time = time.time() - start_time
        print(f"      [下载请求] 失败 (耗时: {elapsed_time:.2f}秒)")
        print(f"      [错误详情] {error_msg}")

        # 检查是否是次数限制
        if "limit" in error_msg.lower() or "quota" in error_msg.lower():
            return False, "download_limit_reached", error_msg
        return False, error_msg, error_msg


def main():
    """主函数"""
    import requests  # 导入requests库

    print("=" * 100)
    print("Zlibrary 批量下载工具")
    print("=" * 100)

    # 检查命令行参数
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    force = "--force" in sys.argv or "-f" in sys.argv

    if dry_run:
        print("\n🔍 Dry-run模式：仅预览，不实际下载")
    elif force:
        print("\n⚠️  强制模式：忽略已下载记录")

    print("=" * 100)

    # 登录
    if DEFAULT_REMIX_USERID and DEFAULT_REMIX_USERKEY:
        print(f"\n使用Remix Token登录...")
        zlib = Zlibrary(remix_userid=DEFAULT_REMIX_USERID, remix_userkey=DEFAULT_REMIX_USERKEY)
    else:
        print(f"\n使用邮箱+密码登录: {DEFAULT_EMAIL}")
        print(f"  [状态] 正在连接服务器...")
        zlib = Zlibrary(email=DEFAULT_EMAIL, password=DEFAULT_PASSWORD)

    if not zlib.isLoggedIn():
        print("\n❌ 登录失败！请检查配置")
        return

    profile = zlib.getProfile()
    print(f"\n✅ 登录成功!")
    print(f"   用户: {profile['user']['name']}")
    downloads_left = zlib.getDownloadsLeft()
    print(f"   今日剩余下载次数: {downloads_left}")

    # 加载下载状态
    download_state = DownloadState(DEFAULT_STATE_FILE)

    # 解析list.txt
    print(f"\n正在解析文件: {DEFAULT_INPUT_FILE}")
    print(f"[状态] 正在读取文件...", flush=True)
    books_to_download = parse_list_file(DEFAULT_INPUT_FILE)

    if not books_to_download:
        print("❌ 未找到标记了v的版本")
        return

    print(f"✅ 找到 {len(books_to_download)} 个标记版本")

    # 合并待下载列表（从状态文件中）
    if not force and download_state.get_pending_count() > 0:
        print(f"\n[注意] 从上次运行恢复 {download_state.get_pending_count()} 个待下载任务")
        print(f"[状态] 正在合并待下载列表...", flush=True)
        pending_books = download_state.state["pending"]
        # 去重：基于id+hash
        pending_keys = set(f"{b['id']}_{b['hash']}" for b in pending_books)
        existing_keys = set(f"{b['id']}_{b['hash']}" for b in books_to_download)

        for book in pending_books:
            book_key = f"{book['id']}_{book['hash']}"
            if book_key not in existing_keys:
                books_to_download.append(book)
                existing_keys.add(book_key)

        print(f"✅ 合并后待下载: {len(books_to_download)} 本")

    # 去重已下载
    if not force:
        downloaded_ids = [b['id'] for b in download_state.state["downloaded"]]
        books_to_download = [b for b in books_to_download if b['id'] not in downloaded_ids]
        print(f"[注意] 已下载: {download_state.get_downloaded_count()} 本")
        print(f"✅ 过滤后待下载: {len(books_to_download)} 本")

    if not books_to_download:
        print("\n🎉 所有书籍已下载完成！")
        return

    # Dry-run模式：只显示预览
    if dry_run:
        print("\n" + "=" * 100)
        print("【下载预览】")
        print("=" * 100)
        print(f"\n待下载书籍列表 ({len(books_to_download)} 本):\n")

        for idx, book in enumerate(books_to_download, 1):
            print(f"{idx}. {book['title']}")
            print(f"   作者: {book['author']}")
            print(f"   出版社: {book['publisher']}")
            print(f"   ID: {book['id']} | Hash: {book['hash']}")

        print("\n" + "=" * 100)
        print(f"\n📊 统计信息:")
        print(f"  待下载: {len(books_to_download)} 本")
        print(f"  今日剩余次数: {downloads_left}")
        print(f"  最大每日下载: {DEFAULT_MAX_DOWNLOADS_PER_DAY} 次")

        if len(books_to_download) > downloads_left:
            print(f"\n⚠️  警告: 待下载数量({len(books_to_download)}) 超过剩余次数({downloads_left})")
            print(f"  将优先下载前 {downloads_left} 本，剩余 {len(books_to_download) - downloads_left} 本将保存为待下载任务")

        print("\n要开始下载，请运行: python batch_download.py")
        print("或者使用强制模式: python batch_download.py --force")
        return

    # 实际下载
    print("\n" + "=" * 100)
    print("开始下载...")
    print("=" * 100)

    downloaded_count = 0
    pending_count = 0
    failed_count = 0

    for idx, book in enumerate(books_to_download, 1):
        if downloaded_count >= downloads_left:
            print(f"\n⚠️  已达到今日下载限制 ({downloads_left}次)")
            print(f"   将剩余 {len(books_to_download) - idx + 1} 本保存为待下载任务")

            # 保存剩余书籍到待下载列表
            remaining_books = books_to_download[idx-1:]
            for remaining_book in remaining_books:
                download_state.add_pending(remaining_book)
            download_state.save()

            break

        print(f"\n{'─' * 100}")
        print(f" [{idx}/{len(books_to_download)}] {book['title']}")
        print(f"{'─' * 100}")
        print(f"   ID: {book['id']} | Hash: {book['hash']}")
        print(f"   作者: {book['author']}")
        print(f"   出版社: {book['publisher']}")

        success, result, message = download_book(
            zlib, book['id'], book['hash'], DEFAULT_OUTPUT_DIR,
            book.get('title', ''), book.get('author', ''), book.get('publisher', '')
        )

        if success:
            # 下载成功
            download_state.add_downloaded(book)
            download_state.save()
            downloaded_count += 1
            print(f"  ✅ 下载成功: {result}")
        elif result == "download_limit_reached":
            # 下载次数限制
            print(f"  ⚠️  {message}")
            download_state.add_pending(book)
            download_state.save()
            pending_count += 1
            print(f"  📋 已保存到待下载任务")
            # 达到限制，停止下载
            break
        else:
            # 下载失败
            print(f"  ❌ 下载失败: {message}")
            download_state.add_failed(book, message)
            download_state.save()
            failed_count += 1

    # 统计信息
    print("\n" + "=" * 100)
    print(f"✅ 下载完成！")
    print("=" * 100)
    print(f"\n📊 本次统计:")
    print(f"  成功: {downloaded_count} 本")
    print(f"  待下载: {pending_count} 本（因次数限制）")
    print(f"  失败: {failed_count} 本")

    print(f"\n📋 累计统计:")
    print(f"  已下载总数: {download_state.get_downloaded_count()} 本")
    print(f"  待下载总数: {download_state.get_pending_count()} 本")

    if download_state.get_pending_count() > 0:
        print(f"\n💡 提示: 下次运行时会自动下载待下载任务")

    print(f"\n📁 文件保存位置: {os.path.abspath(DEFAULT_OUTPUT_DIR)}")
    print(f"📄 状态文件: {os.path.abspath(DEFAULT_STATE_FILE)}")
    print("=" * 100)


if __name__ == "__main__":
    main()
