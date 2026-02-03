# 优化策略说明

## 性能优化

### 旧策略（多次在线搜索）
```
步骤1: 在线搜索"书名"
  └─ 如果结果>1 → 步骤2
      在线搜索"书名 + 出版社"
      └─ 如果结果>1 → 步骤3
          在线搜索"书名 + 出版社 + 作者"
```

**问题**: 每次约束条件都需要发起在线搜索请求，速度慢。

### 新策略（一次搜索 + 本地筛选）
```
步骤1: 一次性在线搜索"书名"（获取所有相关书籍）
  ↓
步骤2: 本地按书名筛选
  ↓ 如果结果>1
步骤3: 本地按出版社筛选
  ↓ 如果结果>1
步骤4: 本地按作者筛选
```

**优势**: 只需1次网络请求，其余操作在本地完成，速度大幅提升。

## 实现细节

### 1. 在线搜索
```python
def search_books_by_condition(zlib, search_term, limit=50):
    """一次性获取所有相关书籍"""
    result = zlib.search(message=search_term, limit=50)
    return result.get("books", [])
```

### 2. 本地筛选函数
```python
def filter_books_by_title(books, title):
    """按书名筛选"""
    filtered = []
    for book in books:
        if fuzzy_match(title, book.get("title", "")):
            filtered.append(book)
    return filtered

def filter_books_by_publisher(books, publisher):
    """按出版社筛选"""
    filtered = []
    for book in books:
        if fuzzy_match(publisher, book.get("publisher", "")):
            filtered.append(book)
    return filtered

def filter_books_by_author(books, author):
    """按作者筛选"""
    filtered = []
    for book in books:
        if fuzzy_match(author, book.get("author", "")):
            filtered.append(book)
    return filtered
```

### 3. 模糊匹配
```python
def normalize_string(text):
    """标准化字符串"""
    return text.strip().lower()

def fuzzy_match(search_term, target):
    """检查search_term是否包含在target中"""
    return normalize_string(search_term) in normalize_string(target)
```

## 策略流程

### 完整流程
```
输入: 书名="Python编程", 作者="Eric Matthes", 出版社="人民邮电出版社"

步骤0: 确定搜索词
  → 使用"Python编程"作为初始搜索词

步骤1: 在线搜索
  → 搜索"Python编程"，获取所有相关书籍
  → 假设找到4本书

步骤2: 本地按书名筛选
  → 从4本书中筛选书名包含"Python编程"的
  → 假设找到3本

步骤3: 本地按出版社筛选
  → 从3本书中筛选出版社包含"人民邮电出版社"的
  → 假设找到2本

步骤4: 本地按作者筛选
  → 从2本书中筛选作者包含"Eric Matthes"的
  → 假设找到2本

结果: 返回2本书（两个版本）
```

### 回退机制
```
如果按出版社筛选后结果为0:
  → 回退到按书名筛选的结果

如果按作者筛选后结果为0:
  → 回退到按出版社筛选的结果
```

## 性能对比

### 旧策略
- 网络请求: 3次（书名 → 书名+出版社 → 书名+出版社+作者）
- 总耗时: ~3-5秒（每次请求约1-1.5秒）

### 新策略
- 网络请求: 1次（仅初始搜索）
- 总耗时: ~1-1.5秒（本地筛选几乎无耗时）

**提升**: 约60-70%的搜索时间减少

## 使用示例

### 运行优化版
```bash
# 模拟版（测试）
python batch_search_mock_v2.py sample_input.txt

# 真实版（需要网络）
python batch_search.py 1.txt
```

### 输出示例
```
搜索策略:
  初始搜索词: 'Python编程'
  步骤1 - 在线搜索: 'Python编程' -> 找到 4 本相关书籍
  步骤2 - 本地按书名筛选: 'Python编程' -> 3 本匹配
  步骤3 - 本地按出版社筛选: '人民邮电出版社' -> 2 本匹配
  步骤4 - 本地按作者筛选: 'Eric Matthes' -> 2 本匹配
```

## 注意事项

1. **搜索词选择**: 优先使用书名作为初始搜索词，因为书名最具体
2. **搜索限制**: 设置较大的limit（如50）以获取更多候选书籍
3. **模糊匹配**: 使用包含关系匹配，而非精确匹配，提高匹配率
4. **回退机制**: 严格遵循回退逻辑，避免因过严约束而遗漏书籍

## 文件说明

| 文件 | 说明 |
|------|------|
| `batch_search.py` | 真实版（优化策略） |
| `batch_search_mock_v2.py` | 模拟版（优化策略） |
| `list_optimized.txt` | 优化版输出示例 |
