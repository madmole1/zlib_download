# 快速开始指南

## 项目概述

Zlibrary 批量搜索工具 - 支持智能约束策略的EPUB书籍搜索工具。

## 核心功能

✅ **智能约束搜索策略**
  - 逐步缩小搜索范围
  - 自动回退机制
  - 完整策略追踪

✅ **批量搜索**
  - JSON格式输入
  - 多版本汇总显示
  - 详细的输出报告

✅ **多种搜索模式**
  - 批量搜索（推荐）
  - 交互式搜索
  - 单本搜索测试

## 快速开始

### 1. 创建搜索条件文件

创建 `1.txt` (JSON格式):

```json
[
    {
        "title": "Python编程",
        "author": "Eric Matthes",
        "publisher": "人民邮电出版社"
    }
]
```

### 2. 运行批量搜索

```bash
python batch_search.py 1.txt
```

或使用模拟版（无需网络）:

```bash
python batch_search_mock_strategy.py 1.txt
```

### 3. 查看结果

结果保存在 `list.txt` 或 `list_strategy.txt`

## 文件说明

| 文件 | 说明 |
|------|------|
| `batch_search.py` | **主程序** - 批量搜索（智能策略） |
| `batch_search_mock_strategy.py` | 模拟版 - 测试智能策略（无需网络） |
| `1.txt` | 输入文件示例 |
| `sample_input.txt` | 完整输入文件示例 |
| `list.txt` | 输出文件示例 |
| `simple_test.py` | 策略演示 |

## 智能约束策略

```
步骤1: 仅书名搜索
  ├─ 找到1本 → 返回
  └─ 找到多本 → 步骤2

步骤2: 书名 + 出版社
  ├─ 找到0本 → 回退步骤1
  ├─ 找到1本 → 返回
  └─ 找到多本 → 步骤3

步骤3: 书名 + 出版社 + 作者
  └─ 返回或回退
```

## 演示策略流程

```bash
python simple_test.py
```

## 测试完整流程

```bash
# 1. 使用示例输入测试
python batch_search_mock_strategy.py sample_input.txt

# 2. 查看结果
type list_strategy.txt

# 3. 创建自己的搜索文件
echo '[{"title":"你的书名"}]' > my_search.txt

# 4. 运行搜索
python batch_search.py my_search.txt
```

## 输出示例

```
====================================================================================================
搜索条件: 书名: Python编程 | 作者: Eric Matthes | 出版社: 人民邮电出版社
────────────────────────────────────────────────────────────────────────────────────────────────────

搜索策略:
  步骤1 - 仅书名搜索: 'Python编程' -> 找到 2 本EPUB
  步骤2 - 书名+出版社: 'Python编程 人民邮电出版社' -> 找到 2 本EPUB
  步骤3 - 完整条件: 'Python编程 Eric Matthes 人民邮电出版社' -> 找到 2 本EPUB

找到 2 个可下载的EPUB版本:
  【版本 1】Python编程：从入门到实践 (2020, 8.2 MB)
  【版本 2】Python编程：从入门到实践（第2版） (2023, 9.5 MB)
```

## 配置登录

编辑 `batch_search.py` 顶部配置区:

```python
DEFAULT_EMAIL = "your@email.com"
DEFAULT_PASSWORD = "your_password"

# 或使用Remix Token（推荐）
DEFAULT_REMIX_USERID = "你的remix_userid"
DEFAULT_REMIX_USERKEY = "你的remix_userkey"
```

## 文档

- **README.md** - 项目说明
- **USAGE.md** - 详细使用指南
- **FEATURES.md** - 智能策略详细说明

## 注意事项

1. 需要有效的Zlibrary账号（1lib.sk）
2. 免费账号有每日下载次数限制
3. 输入文件必须使用UTF-8编码
4. 建议使用Remix Token登录（更稳定）

## 故障排除

### 网络连接问题
- 使用模拟版测试: `batch_search_mock_strategy.py`
- 检查防火墙设置

### 编码问题
- 确保输入文件使用UTF-8编码保存
- Windows用户无需额外配置（已处理）

### 找不到书籍
- 检查搜索条件是否正确
- 查看 `list.txt` 中的策略追踪
- 尝试放宽搜索条件

## 获取帮助

查看详细文档:
- `README.md` - 快速参考
- `USAGE.md` - 完整指南
- `FEATURES.md` - 策略详解
