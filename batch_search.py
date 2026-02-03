"""
批量搜索工具 - 从JSON文件读取搜索条件并输出结果
"""
import sys
import os
import io
import json
import re
from datetime import datetime
from pathlib import Path


def flush_stdout():
    """强制刷新标准输出"""
    try:
        sys.stdout.flush()
    except:
        pass


def safe_print(*args, **kwargs):
    """安全的打印函数，自动刷新缓冲区"""
    print(*args, **kwargs)
    flush_stdout()

# Windows终端设置UTF-8编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', write_through=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', write_through=True)
else:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Zlibrary import Zlibrary
import time

# ========== 配置区域 ==========
# 默认登录信息
DEFAULT_EMAIL = "YourUSERNAME"
DEFAULT_PASSWORD = "YourPASSWORD"

# 或者使用Remix Token（推荐）
DEFAULT_REMIX_USERID = ""
DEFAULT_REMIX_USERKEY = ""

# 网络超时设置（秒）
REQUEST_TIMEOUT = 30

# 连接测试搜索词
TEST_SEARCH_TERM = "python"
# ===============================


def load_search_requests(input_file: str) -> list:
    """
    从JSON文件加载搜索请求

    Args:
        input_file: JSON文件路径

    Returns:
        搜索请求列表
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)

        if not isinstance(requests, list):
            print(f"错误: 输入文件必须包含JSON数组")
            return []

        # 检测重复的搜索请求
        seen = {}
        duplicates = []
        for idx, req in enumerate(requests, 1):
            title = req.get('title', '')
            author = req.get('author', '')
            publisher = req.get('publisher', '')

            # 生成唯一标识
            search_key = f"{title}|{author}|{publisher}"

            if search_key in seen:
                duplicates.append({
                    'index': idx,
                    'duplicate_index': seen[search_key],
                    'title': title,
                    'author': author,
                    'publisher': publisher
                })
            else:
                seen[search_key] = idx

        if duplicates:
            print("\n" + "=" * 100)
            print("⚠️  警告: 检测到重复的搜索请求！")
            print("=" * 100)
            for dup in duplicates:
                print(f"\n重复项 #{dup['index']} 与 #{dup['duplicate_index']}:")
                print(f"  书名: {dup['title']}")
                print(f"  作者: {dup['author']}")
                print(f"  出版社: {dup['publisher']}")
            print("\n💡 提示: 后续的搜索结果会覆盖前面的结果")
            print("=" * 100)

        return requests

    except FileNotFoundError:
        print(f"错误: 文件不存在 - {input_file}")
        return []
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 - {e}")
        return []


def build_search_term(title: str = None, author: str = None, publisher: str = None) -> str:
    """
    构建搜索关键词

    Args:
        title: 书名
        author: 作者
        publisher: 出版社

    Returns:
        搜索关键词字符串
    """
    terms = []
    if title:
        terms.append(title)
    if author:
        terms.append(author)
    if publisher:
        terms.append(publisher)
    return " ".join(terms)


def normalize_string(text: str) -> str:
    """
    标准化字符串用于匹配（去除空格、特殊字符等）

    Args:
        text: 原始字符串

    Returns:
        标准化后的字符串
    """
    if not text:
        return ""
    return text.strip().lower()


def fuzzy_match(search_term: str, target: str) -> bool:
    """
    模糊匹配 - 检查search_term是否包含在target中

    Args:
        search_term: 搜索词
        target: 目标字符串

    Returns:
        是否匹配
    """
    if not search_term or not target:
        return False
    return normalize_string(search_term) in normalize_string(target)


def search_books_by_condition(zlib: Zlibrary, search_term: str, limit: int = 50, extensions: str = None) -> list:
    """
    根据搜索条件搜索书籍
    注意：这里使用较大的limit以获取更多候选

    Args:
        zlib: Zlibrary实例
        search_term: 搜索关键词
        limit: 返回结果数量限制
        extensions: 文件扩展名筛选（如"epub"）

    Returns:
        书籍列表
    """
    safe_print(f"      [网络请求] 正在连接服务器搜索...")
    start_time = time.time()

    result = zlib.search(message=search_term, limit=limit, extensions=extensions)

    elapsed_time = time.time() - start_time
    safe_print(f"      [网络请求] 完成 (耗时: {elapsed_time:.2f}秒)")

    if not result.get("success"):
        safe_print(f"    ❌ 搜索失败: {result.get('message', '未知错误')}")
        return []

    return result.get("books", [])


def is_epub_available(zlib: Zlibrary, book_id: str, book_hash: str) -> bool:
    """
    检查书籍是否有EPUB格式

    Args:
        zlib: Zlibrary实例
        book_id: 书籍ID
        book_hash: 书籍Hash

    Returns:
        是否有EPUB格式
    """
    try:
        book_info = zlib.getBookInfo(book_id, book_hash)
        if book_info.get("success"):
            formats = book_info.get("book", {}).get("formats", {})
            return formats.get("epub") is not None
    except Exception as e:
        print(f"      [警告] 检查EPUB格式时出错 (ID: {book_id}): {e}")
    return False


def get_epub_book_details(zlib: Zlibrary, book_id: str, book_hash: str, original_book: dict) -> dict:
    """
    获取EPUB书籍的详细信息

    Args:
        zlib: Zlibrary实例
        book_id: 书籍ID
        book_hash: 书籍Hash
        original_book: 原始书籍信息

    Returns:
        包含EPUB信息的书籍字典
    """
    try:
        book_info = zlib.getBookInfo(book_id, book_hash)
        if book_info.get("success"):
            formats = book_info.get("book", {}).get("formats", {})
            epub_info = formats.get("epub", {})
            return {
                "id": book_id,
                "hash": book_hash,
                "title": original_book.get("title"),
                "author": original_book.get("author"),
                "publisher": original_book.get("publisher"),
                "year": original_book.get("year"),
                "language": original_book.get("language"),
                "file_size": epub_info.get("filesize"),
                "pages": original_book.get("pages"),
                "cover": original_book.get("cover"),
            }
    except Exception as e:
        print(f"      [警告] 获取书籍详情时出错 (ID: {book_id}): {e}")
    return None


def filter_books_by_title(books: list, title: str) -> list:
    """
    根据书名筛选书籍

    Args:
        books: 书籍列表
        title: 书名

    Returns:
        匹配的书籍列表
    """
    if not title:
        return books[:]

    filtered = []
    for book in books:
        if fuzzy_match(title, book.get("title", "")):
            filtered.append(book)
    return filtered


def filter_books_by_publisher(books: list, publisher: str) -> list:
    """
    根据出版社筛选书籍

    Args:
        books: 书籍列表
        publisher: 出版社

    Returns:
        匹配的书籍列表
    """
    if not publisher:
        return books[:]

    filtered = []
    for book in books:
        if fuzzy_match(publisher, book.get("publisher", "")):
            filtered.append(book)
    return filtered


def filter_books_by_author(books: list, author: str) -> list:
    """
    根据作者/译者筛选书籍

    Args:
        books: 书籍列表
        author: 作者/译者

    Returns:
        匹配的书籍列表
    """
    if not author:
        return books[:]

    filtered = []
    for book in books:
        book_author = book.get("author", "")
        if fuzzy_match(author, book_author):
            filtered.append(book)
    return filtered


def test_connection(zlib: Zlibrary) -> bool:
    """
    测试与Zlibrary的连接是否正常

    Args:
        zlib: Zlibrary实例

    Returns:
        连接是否正常
    """
    print("\n" + "=" * 100)
    print("【前置检查】测试与Zlibrary的连接...")
    print("=" * 100)

    print(f"\n  [步骤1] 使用测试关键词 '{TEST_SEARCH_TERM}' 进行搜索测试...")
    start_time = time.time()

    try:
        result = zlib.search(message=TEST_SEARCH_TERM, limit=5)

        elapsed_time = time.time() - start_time
        print(f"  [步骤1] 完成 (耗时: {elapsed_time:.2f}秒)")

        if not result.get("success"):
            print(f"  ❌ 连接测试失败: {result.get('message', '未知错误')}")
            return False

        books = result.get("books", [])
        print(f"  ✅ 连接测试成功!")
        print(f"     - 找到 {len(books)} 本相关书籍")
        print(f"     - 响应时间: {elapsed_time:.2f}秒")
        print("=" * 100)
        return True

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"  [步骤1] 耗时: {elapsed_time:.2f}秒")
        print(f"  ❌ 连接测试异常: {e}")
        print("=" * 100)
        return False


def search_epub_books_with_strategy(zlib: Zlibrary, title: str = None, author: str = None, publisher: str = None) -> tuple:
    """
    使用智能约束策略搜索EPUB格式书籍
    优化版本：一次在线搜索获取所有EPUB格式书籍，然后本地筛选

    策略顺序:
    1. 使用书名（或最具体的搜索词）一次性搜索（直接筛选EPUB格式）
    2. 本地逐步筛选：先按书名，再按出版社，最后按作者
    3. 如果筛选后无结果，回退到上一步

    Args:
        zlib: Zlibrary实例
        title: 书名
        author: 作者
        publisher: 出版社

    Returns:
        (书籍列表, 使用的搜索策略描述)
    """
    if not title and not author and not publisher:
        return [], "错误: 至少需要提供一个搜索条件"

    strategy_log = []
    search_start_time = time.time()

    # 步骤0: 确定初始搜索词
    # 优先使用书名，如果没有书名则使用最具体的条件
    if title:
        initial_search_term = title
        strategy_log.append(f"初始搜索词: '{title}'")
    elif publisher:
        initial_search_term = publisher
        strategy_log.append(f"初始搜索词: '{publisher}' (无书名，使用出版社)")
    else:
        initial_search_term = author
        strategy_log.append(f"初始搜索词: '{author}' (无书名和出版社，使用作者)")

    # 步骤1: 在线搜索 - 直接获取EPUB格式书籍，避免后续逐个检查
    safe_print(f"    正在搜索EPUB格式书籍: {initial_search_term}...")
    epub_books = search_books_by_condition(zlib, initial_search_term, limit=50, extensions="epub")
    strategy_log.append(f"步骤1 - 在线搜索EPUB: '{initial_search_term}' -> 找到 {len(epub_books)} 本EPUB书籍")

    if not epub_books:
        elapsed_time = time.time() - search_start_time
        strategy_log.append(f"    未找到EPUB格式的书籍 (总耗时: {elapsed_time:.2f}秒)")
        return [], "\n".join(strategy_log)

    # 步骤2: 本地逐步筛选 - 按书名
    if title:
        safe_print(f"      [本地处理] 按书名筛选: '{title}'...")
        by_title = filter_books_by_title(epub_books, title)
        strategy_log.append(f"步骤2 - 按书名筛选: '{title}' -> {len(by_title)} 本匹配")
    else:
        by_title = epub_books[:]

    # 步骤3: 如果结果>1，按出版社筛选
    if len(by_title) > 1 and publisher:
        safe_print(f"      [本地处理] 按出版社筛选: '{publisher}'...")
        by_publisher = filter_books_by_publisher(by_title, publisher)
        strategy_log.append(f"步骤3 - 按出版社筛选: '{publisher}' -> {len(by_publisher)} 本匹配")

        if len(by_publisher) == 0:
            # 出版社筛选无结果，回退到按书名的结果
            strategy_log.append(f"    出版社筛选无结果，回退到步骤2结果 ({len(by_title)} 本)")
            final_books = by_title
        else:
            final_books = by_publisher
    else:
        final_books = by_title

    # 步骤4: 如果结果>1，按作者筛选
    if len(final_books) > 1 and author:
        safe_print(f"      [本地处理] 按作者筛选: '{author}'...")
        by_author = filter_books_by_author(final_books, author)
        strategy_log.append(f"步骤4 - 按作者筛选: '{author}' -> {len(by_author)} 本匹配")

        if len(by_author) == 0:
            # 作者筛选无结果，回退到上一步的结果
            strategy_log.append(f"    作者筛选无结果，回退到上一步结果 ({len(final_books)} 本)")
            # 保持final_books不变
        else:
            final_books = by_author

    # 转换为详细格式
    safe_print(f"      [本地处理] 整理书籍信息...")
    detail_start = time.time()
    result_books = []

    # 搜索返回的书籍已经包含了所有必要信息，直接使用
    for idx, book in enumerate(final_books, 1):
        # 尝试获取文件大小（可选，因为需要额外网络请求）
        # 如果不需要文件大小，可以直接使用搜索结果
        result_books.append({
            "id": book.get("id"),
            "hash": book.get("hash"),
            "title": book.get("title"),
            "author": book.get("author"),
            "publisher": book.get("publisher"),
            "year": book.get("year"),
            "language": book.get("language"),
            "file_size": "N/A",  # 搜索结果中不包含文件大小，需要单独获取
            "pages": book.get("pages"),
            "cover": book.get("cover"),
        })

    detail_time = time.time() - detail_start
    safe_print(f"      [本地处理] 完成 (耗时: {detail_time:.2f}秒)")

    total_elapsed = time.time() - search_start_time
    strategy_log.append(f"    搜索完成: 找到 {len(result_books)} 本 (总耗时: {total_elapsed:.2f}秒)")
    strategy_desc = "\n".join(strategy_log)

    return result_books, strategy_desc


def search_epub_books(zlib: Zlibrary, title: str = None, author: str = None, publisher: str = None) -> list:
    """
    搜索符合条件的EPUB格式书籍（旧版本，保留兼容性）

    Args:
        zlib: Zlibrary实例
        title: 书名
        author: 作者
        publisher: 出版社

    Returns:
        符合条件的EPUB书籍列表
    """
    search_term = build_search_term(title, author, publisher)

    if not search_term:
        return []

    # 搜索书籍
    result = zlib.search(message=search_term, extensions="epub", limit=20)

    if not result.get("success"):
        print(f"搜索失败: {result.get('message', '未知错误')}")
        return []

    books = result.get("books", [])
    if not books:
        return []

    # 筛选EPUB格式的书籍
    epub_books = []
    for book in books:
        # 检查书籍信息中的格式
        book_info = zlib.getBookInfo(book["id"], book["hash"])
        if book_info.get("success"):
            formats = book_info.get("book", {}).get("formats", {})
            if formats.get("epub"):
                epub_books.append({
                    "id": book["id"],
                    "hash": book["hash"],
                    "title": book.get("title"),
                    "author": book.get("author"),
                    "publisher": book.get("publisher"),
                    "year": book.get("year"),
                    "language": book.get("language"),
                    "file_size": formats.get("epub", {}).get("filesize"),
                    "pages": book.get("pages"),
                    "cover": book.get("cover"),
                })

    return epub_books


def format_file_size(size_str: str) -> str:
    """
    格式化文件大小

    Args:
        size_str: 文件大小字符串

    Returns:
        格式化后的大小
    """
    if not size_str:
        return "N/A"
    return size_str


def sort_books_by_year(books: list, descending: bool = True) -> list:
    """
    按年份排序书籍列表

    Args:
        books: 书籍列表
        descending: 是否降序排序（默认True，最新的在前）

    Returns:
        排序后的书籍列表
    """
    def extract_year(book: dict) -> int:
        """从书籍信息中提取年份"""
        year_str = book.get('year', '')
        if not year_str or year_str == 'N/A':
            return 0  # 无年份的排在最后
        try:
            # 尝试提取年份（可能包含其他字符）
            year_match = re.search(r'\d{4}', year_str)
            if year_match:
                return int(year_match.group())
            return 0
        except:
            return 0

    return sorted(books, key=extract_year, reverse=descending)


def save_results_to_file(output_file: str, found_books: dict, not_found_books: list, search_time: str, strategies: dict = None):
    """
    将结果保存到文件

    Args:
        output_file: 输出文件路径
        found_books: 找到的书籍字典 {search_key: [books]}
        not_found_books: 未找到的书籍列表
        search_time: 搜索时间
        strategies: 搜索策略字典 {search_key: strategy_desc}
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("Zlibrary 批量搜索结果\n")
        f.write("=" * 100 + "\n")
        f.write(f"搜索时间: {search_time}\n")
        f.write(f"总共搜索: {len(found_books) + len(not_found_books)} 本书\n")
        f.write(f"找到可下载EPUB: {len(found_books)} 本书\n")
        f.write(f"未找到: {len(not_found_books)} 本书\n")
        if strategies:
            f.write(f"去重后实际搜索: {len(found_books) + len(not_found_books)} 本书\n")
        f.write("=" * 100 + "\n\n")

        # 输出找到的书籍
        f.write("【已找到的书籍列表】\n")
        f.write("=" * 100 + "\n")

        for search_key, books in found_books.items():
            f.write(f"\n{'─' * 100}\n")
            f.write(f"搜索条件: {search_key}\n")
            f.write(f"{'─' * 100}\n")

            # 显示搜索策略
            if strategies and search_key in strategies:
                f.write(f"\n搜索策略:\n")
                for line in strategies[search_key].split('\n'):
                    f.write(f"  {line}\n")
                f.write(f"\n")

            f.write(f"找到 {len(books)} 个可下载的EPUB版本:\n\n")

            for idx, book in enumerate(books, 1):
                f.write(f"  【版本 {idx}】\n")
                f.write(f"    书名: {book['title']}\n")
                f.write(f"    作者: {book['author'] or 'N/A'}\n")
                f.write(f"    出版社: {book['publisher'] or 'N/A'}\n")
                f.write(f"    年份: {book['year'] or 'N/A'}\n")
                f.write(f"    语言: {book['language'] or 'N/A'}\n")
                f.write(f"    页数: {book['pages'] or 'N/A'}\n")
                f.write(f"    文件大小: {format_file_size(book['file_size'])}\n")
                f.write(f"    ID: {book['id']}\n")
                f.write(f"    Hash: {book['hash']}\n")

            f.write(f"\n{'─' * 100}\n")

        # 输出未找到的书籍
        if not_found_books:
            f.write("\n\n" + "=" * 100 + "\n")
            f.write("【未找到的书籍列表】\n")
            f.write("=" * 100 + "\n\n")

            for idx, not_found in enumerate(not_found_books, 1):
                title = not_found.get('title', 'N/A')
                author = not_found.get('author', 'N/A')
                publisher = not_found.get('publisher', 'N/A')

                f.write(f"{idx}. 书名: {title}\n")
                f.write(f"   作者: {author}\n")
                f.write(f"   出版社: {publisher}\n")
                f.write(f"   原因: 未找到可下载的EPUB格式\n\n")

        f.write("=" * 100 + "\n")
        f.write("搜索完成\n")
        f.write("=" * 100 + "\n")


def main():
    """主函数"""
    program_start = time.time()

    print("=" * 100)
    print("Zlibrary 批量搜索工具（智能约束策略）")
    print("=" * 100)
    print("\n搜索策略:")
    print("  1. 仅使用书名搜索")
    print("  2. 如果结果>1，增加出版社约束")
    print("  3. 如果仍然>1，增加作者/译者约束")
    print("  4. 如果约束后无结果，自动回退")
    print("=" * 100)

    # 检查命令行参数
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print("  python batch_search.py <输入JSON文件> [输出文件]")
        print("\n示例:")
        print("  python batch_search.py 1.txt")
        print("  python batch_search.py 1.txt output.txt")
        print("\n默认输入文件: 1.txt")
        print("默认输出文件: list.txt")
        return

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "list.txt"

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
        print(f"  可能原因:")
        print(f"  - 网络连接问题")
        print(f"  - 账号或密码错误")
        print(f"  - 服务器无响应")
        return

    profile = zlib.getProfile()
    print(f"\n✅ 登录成功!")
    print(f"   用户: {profile['user']['name']}")
    print(f"   今日剩余下载次数: {zlib.getDownloadsLeft()}")

    # 前置连接测试
    if not test_connection(zlib):
        print("\n❌ 连接测试失败，程序终止")
        print(f"  请检查:")
        print(f"  - 网络连接是否正常")
        print(f"  - 防火墙是否阻止了连接")
        print(f"  - Zlibrary服务器是否正常运行")
        return

    # 加载搜索请求
    print(f"\n[准备] 正在读取搜索条件: {input_file}")
    search_requests = load_search_requests(input_file)

    if not search_requests:
        print("❌ 错误: 无法加载搜索请求")
        return

    # 统计去重后的数量
    unique_keys = set()
    for req in search_requests:
        key = f"{req.get('title', '')}|{req.get('author', '')}|{req.get('publisher', '')}"
        unique_keys.add(key)

    print(f"✅ 找到 {len(search_requests)} 个搜索请求（其中 {len(search_requests) - len(unique_keys)} 个重复）")
    print(f"✅ 实际将搜索 {len(unique_keys)} 本不同的书")

    # 执行搜索
    found_books = {}
    not_found_books = []
    strategies = {}
    search_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "=" * 100)
    print("开始批量搜索...（使用智能约束策略）")
    print("=" * 100)

    search_total_start = time.time()

    for idx, request in enumerate(search_requests, 1):
        title = request.get('title')
        author = request.get('author')
        publisher = request.get('publisher')

        search_term = build_search_term(title, author, publisher)
        search_key = f"书名: {title or 'N/A'} | 作者: {author or 'N/A'} | 出版社: {publisher or 'N/A'}"

        print(f"\n{'─' * 100}")
        print(f" [{idx}/{len(search_requests)}] 搜索: {search_term}")
        print(f"{'─' * 100}")

        # 使用智能约束策略搜索
        epub_books, strategy_desc = search_epub_books_with_strategy(zlib, title, author, publisher)
        strategies[search_key] = strategy_desc

        if epub_books:
            # 按年份降序排序
            sorted_books = sort_books_by_year(epub_books, descending=True)
            found_books[search_key] = sorted_books
            print(f"  ✅ 找到 {len(sorted_books)} 个可下载的EPUB版本")

            # 显示找到的版本（已按年份降序排序）
            for v_idx, book in enumerate(sorted_books, 1):
                print(f"     版本{v_idx}: {book['title']} - {book['author']} - {book['year']} - {format_file_size(book['file_size'])}")
        else:
            not_found_books.append(request)
            print(f"  ❌ 未找到可下载的EPUB")

    search_total_time = time.time() - search_total_start
    print(f"\n{'─' * 100}")
    print(f"✅ 批量搜索完成！")
    print(f"   总耗时: {search_total_time:.2f}秒")
    print(f"   平均每本: {search_total_time / len(search_requests):.2f}秒")

    # 保存结果到文件
    print("\n" + "=" * 100)
    print(f"正在保存结果到: {output_file}")
    save_start = time.time()
    save_results_to_file(output_file, found_books, not_found_books, search_time, strategies)
    save_time = time.time() - save_start
    print(f"✅ 结果已保存 (耗时: {save_time:.2f}秒)")

    total_program_time = time.time() - program_start
    print("=" * 100)
    print(f"\n📊 统计信息:")
    print(f"  总搜索: {len(search_requests)} 本书")
    print(f"  找到可下载EPUB: {len(found_books)} 本书")
    print(f"  未找到: {len(not_found_books)} 本书")
    print(f"  结果已保存到: {output_file}")
    print(f"\n⏱️  时间统计:")
    print(f"  程序总运行时间: {total_program_time:.2f}秒")
    print(f"  搜索阶段: {search_total_time:.2f}秒")
    print(f"  保存文件: {save_time:.2f}秒")
    print("=" * 100)


if __name__ == "__main__":
    main()
