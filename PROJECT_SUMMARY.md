# 项目总结 - Zlibrary 批量搜索工具

## 项目概述

基于 Zlibrary API 的 Python 批量搜索工具，支持智能约束策略和性能优化。

## 核心功能

### 1. 批量搜索
- ✅ JSON格式输入
- ✅ 支持多本书同时搜索
- ✅ 结果输出到list文件

### 2. 智能约束策略（优化版）
- ✅ 一次性在线搜索获取所有相关书籍
- ✅ 本地逐步筛选（书名 → 出版社 → 作者）
- ✅ 智能回退机制
- ✅ 性能提升约60-70%

### 3. 搜索结果
- ✅ 已找到书籍列表（多版本汇总）
- ✅ 未找到书籍列表
- ✅ 完整的搜索策略追踪
- ✅ 详细的书籍信息

## 文件清单

### 核心程序
- `batch_search.py` - 主程序（优化版，推荐）
- `batch_search_mock_v2.py` - 模拟版（优化版）
- `batch_search_mock_strategy.py` - 模拟版（旧版）
- `batch_search_mock.py` - 模拟版（原始版）
- `zlib_search.py` - 交互式搜索工具
- `test_search.py` - 单本搜索测试
- `Zlibrary.py` - API核心库

### 输入/输出文件
- `1.txt` - 输入示例（单本书）
- `sample_input.txt` - 输入示例（多本书）
- `list.txt` - 输出示例
- `list_optimized.txt` - 优化版输出示例
- `list_strategy.txt` - 策略版输出示例
- `demo_list.txt` - 演示输出

### 文档
- `README.md` - 项目主文档
- `QUICKSTART.md` - 快速开始指南
- `USAGE.md` - 详细使用指南
- `FEATURES.md` - 智能策略详细说明
- `OPTIMIZATION.md` - 优化策略说明
- `COMPARISON.md` - 优化前后对比
- `PROJECT_SUMMARY.md` - 本文档

### 测试/演示
- `simple_test.py` - 策略演示
- `test_strategy.py` - 策略测试
- `demo_output.py` - 输出格式演示

## 性能优化

### 优化前
```
网络请求: 3次/书
搜索时间: ~3.6秒/书
总时间: ~180秒（50本书）
```

### 优化后
```
网络请求: 1次/书
搜索时间: ~1.2秒/书
总时间: ~60秒（50本书）
```

### 提升
- 网络请求减少: 67%
- 搜索时间减少: 67%
- 性能提升: **约2-3倍**

## 使用方法

### 快速开始
```bash
# 创建输入文件
echo '[{"title":"Python编程"}]' > search.txt

# 运行搜索
python batch_search.py search.txt

# 查看结果
type list.txt
```

### 测试模式
```bash
# 使用模拟版测试（无需网络）
python batch_search_mock_v2.py sample_input.txt

# 查看结果
type list_optimized.txt
```

## 搜索策略

### 策略流程
```
步骤1: 在线搜索"书名"
  ↓ 获取所有相关书籍

步骤2: 本地按书名筛选
  ↓ 如果结果>1

步骤3: 本地按出版社筛选
  ↓ 如果结果>1

步骤4: 本地按作者筛选
  ↓ 智能回退机制
```

### 回退机制
- 如果筛选后结果为0，自动回退到上一步
- 确保不会因过严约束而遗漏书籍

## 输出示例

```
====================================================================================================
搜索条件: 书名: Python编程 | 作者: Eric Matthes | 出版社: 人民邮电出版社
────────────────────────────────────────────────────────────────────────────────────────────────────

搜索策略:
  初始搜索词: 'Python编程'
  步骤1 - 在线搜索: 'Python编程' -> 找到 4 本相关书籍
  步骤2 - 本地按书名筛选: 'Python编程' -> 3 本匹配
  步骤3 - 本地按出版社筛选: '人民邮电出版社' -> 2 本匹配
  步骤4 - 本地按作者筛选: 'Eric Matthes' -> 2 本匹配

找到 2 个可下载的EPUB版本:
  【版本 1】Python编程：从入门到实践 (2020, 8.2 MB)
  【版本 2】Python编程：从入门到实践（第2版） (2023, 9.5 MB)
```

## 配置说明

### 登录配置
编辑 `batch_search.py` 顶部配置区：

```python
# 邮箱+密码
DEFAULT_EMAIL = "your@email.com"
DEFAULT_PASSWORD = "your_password"

# 或使用Remix Token（推荐）
DEFAULT_REMIX_USERID = "你的remix_userid"
DEFAULT_REMIX_USERKEY = "你的remix_userkey"
```

### 输入格式
```json
[
    {
        "title": "书名",
        "author": "作者",
        "publisher": "出版社"
    }
]
```

## 技术实现

### 关键函数
- `search_epub_books_with_strategy()` - 智能约束搜索
- `search_books_by_condition()` - 在线搜索
- `filter_books_by_title()` - 本地书名筛选
- `filter_books_by_publisher()` - 本地出版社筛选
- `filter_books_by_author()` - 本地作者筛选
- `fuzzy_match()` - 模糊匹配

### 核心优化
1. 一次性获取所有相关书籍
2. 本地内存操作替代网络请求
3. 智能回退保证搜索结果

## 注意事项

1. **网络依赖**: 需要访问 `1lib.sk`
2. **账号限制**: 免费账号有每日下载次数限制
3. **编码格式**: 输入文件必须使用UTF-8编码
4. **搜索词**: 建议使用书名作为主要搜索条件
5. **性能优化**: 大批量搜索建议使用优化版

## 未来改进

1. **并发搜索**: 多本书并发执行初始搜索
2. **缓存机制**: 相同搜索词结果缓存
3. **智能limit**: 动态调整搜索结果数量
4. **批量详情**: 一次性获取多本书EPUB详情
5. **GUI界面**: 提供图形化操作界面

## 许可证

MIT License

## 致谢

- Zlibrary API: [Zlibrary-API](https://github.com/bipinkrish/Zlibrary-API)
- API文档: [zlibrary-eapi-documentation](https://github.com/baroxyton/zlibrary-eapi-documentation)

---

**项目完成时间**: 2026-02-03
**当前版本**: v2.0 (优化版)
**Python版本**: 3.6+
