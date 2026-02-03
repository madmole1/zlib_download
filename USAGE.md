# 批量搜索使用指南

## 智能约束搜索策略

程序使用逐步约束策略来找到最准确的书籍：

```
步骤1: 仅使用书名搜索
  ↓ 如果找到1本书 → 返回结果
  ↓ 如果找到>1本书 → 继续步骤2

步骤2: 增加出版社约束（书名 + 出版社）
  ↓ 如果找到1本书 → 返回结果
  ↓ 如果找到>1本书 → 继续步骤3
  ↓ 如果无结果 → 回退到步骤1

步骤3: 增加作者/译者约束（书名 + 出版社 + 作者）
  ↓ 如果找到0本书 → 回退到步骤2
  ↓ 返回最终结果
```

**示例**：
- 搜索"Python编程"，找到2本 → 加入"人民邮电出版社"，仍找到2本 → 加入"Eric Matthes"，仍找到2本 → 返回2个版本
- 搜索"深度学习"，找到1本 → 直接返回唯一结果

## 快速开始

### 1. 准备输入文件

创建一个JSON格式的文本文件（如 `1.txt`），格式如下：

```json
[
    {
        "title": "书名",
        "author": "作者",
        "publisher": "出版社"
    },
    {
        "title": "另一本书",
        "author": "另一作者",
        "publisher": "另一出版社"
    }
]
```

**注意**：
- 文件扩展名可以是 `.txt` 或 `.json`
- 必须是JSON数组格式 `[]`
- 每个搜索条件至少需要提供书名、作者、出版社中的一个
- 字段名必须是：`title`、`author`、`publisher`

### 2. 运行批量搜索

```bash
python batch_search.py 1.txt
```

### 3. 查看结果

搜索结果会自动保存到 `list.txt` 文件中。

## 输入文件示例

### 示例1：只搜索书名

```json
[
    {
        "title": "Python编程"
    }
]
```

### 示例2：书名+作者

```json
[
    {
        "title": "Python编程",
        "author": "Eric Matthes"
    }
]
```

### 示例3：完整信息

```json
[
    {
        "title": "Python编程",
        "author": "Eric Matthes",
        "publisher": "人民邮电出版社"
    },
    {
        "title": "深度学习",
        "author": "Ian Goodfellow"
    },
    {
        "title": "二战全史",
        "author": "白虹",
        "publisher": "中国华侨出版社"
    }
]
```

## 命令行参数

### 基本用法

```bash
python batch_search.py <输入文件> [输出文件]
```

### 参数说明

- **输入文件**：必需，JSON格式的搜索条件文件
- **输出文件**：可选，默认为 `list.txt`

### 示例

```bash
# 使用默认输出文件 list.txt
python batch_search.py 1.txt

# 指定输出文件名
python batch_search.py 1.txt my_results.txt

# 批量搜索多个文件
python batch_search.py books.txt results.txt
```

## 输出文件格式

输出文件包含以下内容：

### 1. 搜索统计
- 搜索时间
- 总共搜索书籍数量
- 找到可下载EPUB的数量
- 未找到的数量

### 2. 已找到的书籍列表
每个搜索条件下，显示所有找到的可下载EPUB版本：
- 版本编号
- 书名
- 作者
- 出版社
- 年份
- 语言
- 页数
- 文件大小
- ID
- Hash

**重要**：如果一本书找到多个版本，会汇总在一起显示，方便比较。

### 3. 未找到的书籍列表
显示搜索条件及未找到的原因。

## 配置登录信息

### 方法1：修改代码配置

在 `batch_search.py` 文件顶部修改：

```python
# ========== 配置区域 ==========
# 邮箱+密码登录
DEFAULT_EMAIL = "your@email.com"
DEFAULT_PASSWORD = "your_password"

# 或者使用Remix Token（推荐，更稳定）
DEFAULT_REMIX_USERID = "你的remix_userid"
DEFAULT_REMIX_USERKEY = "你的remix_userkey"
# ===============================
```

### 方法2：获取Remix Token

1. 在浏览器中登录 [https://1lib.sk](https://1lib.sk)
2. 打开开发者工具 (按 F12)
3. 进入 **Application (应用程序)** 标签页
4. 左侧找到 **Cookies** → 选择 `1lib.sk`
5. 找到以下两个cookie值并复制：
   - `remix_userid`
   - `remix_userkey`
6. 在代码中填入这两个值

## 常见问题

### Q1: 批量搜索时出现网络错误？

**A**: 网络连接到 `1lib.sk` 可能不稳定。可以尝试：
- 使用Remix Token登录（更稳定）
- 多次重试
- 使用模拟版 `batch_search_mock.py` 测试输出格式

### Q2: 找到了书籍但没有EPUB格式？

**A**: 这说明Zlibrary上有这本书，但只有PDF等其他格式，没有EPUB格式。输出会将其归类到"未找到"列表。

### Q3: 如何处理一本书有多个版本？

**A**: 程序会自动将同一搜索条件下的所有版本汇总显示，例如：

```
搜索条件: 书名: Python编程 | 作者: Eric Matthes | 出版社: 人民邮电出版社
────────────────────────────────────────────────────────────────────────────────────────────────────
找到 2 个可下载的EPUB版本:

  【版本 1】
    书名: Python编程：从入门到实践
    年份: 2020
    文件大小: 8.2 MB

  【版本 2】
    书名: Python编程：从入门到实践（第2版）
    年份: 2023
    文件大小: 9.5 MB
```

### Q4: 输入文件的编码问题？

**A**: 确保输入文件使用 **UTF-8** 编码保存。使用记事本或其他文本编辑器保存时，选择UTF-8编码。

### Q5: 可以同时搜索多少本书？

**A**: 理论上没有限制，但建议一次搜索不要超过100本，以免：
- 请求过多导致被限制
- 处理时间过长
- 下载次数不足

## 高级用法

### 结合脚本自动化

可以将批量搜索集成到自动化脚本中：

```bash
# 创建搜索文件
echo '[{"title":"Python编程"}]' > search.txt

# 执行搜索
python batch_search.py search.txt

# 查看结果
type list.txt
```

### 处理多个搜索文件

```bash
# 搜索编程类书籍
python batch_search.py programming.txt prog_results.txt

# 搜索历史类书籍
python batch_search.py history.txt history_results.txt
```

## 注意事项

1. **下载次数限制**：Zlibrary有每日下载次数限制，请在搜索前查看剩余次数
2. **网络连接**：确保网络能够访问 `1lib.sk`
3. **账号安全**：不要将包含密码的配置文件分享给他人
4. **版权问题**：请遵守Zlibrary的使用条款和当地法律法规
