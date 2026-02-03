# Zlibrary 下载工具 - 使用说明

## 快速开始

1. **配置账号密码**
   - 打开 `batch_search.py`，找到第42-43行
   - 打开 `batch_download.py`，找到第30-31行
   - 将 `YourUSERNAME` 替换为您的邮箱
   - 将 `YourPASSWORD` 替换为您的密码

2. **运行搜索**
   ```bash
   python batch_search.py 1.txt list.txt
   ```
   - 这会在 `list.txt` 中生成搜索结果

3. **标记下载版本**
   - 打开 `list.txt`
   - 在想要下载的版本前添加 `v` 标记
   - 例如：`v【版本 1】`

4. **预览下载**
   ```bash
   python batch_download.py --dry-run
   ```

5. **开始下载**
   ```bash
   python batch_download.py
   ```

## 文件说明

### 主要文件
- `batch_search.py` - 批量搜索工具
- `batch_download.py` - 批量下载工具
- `Zlibrary.py` - Zlibrary API 库
- `1.txt` - 搜索条件输入文件（JSON格式）
- `list.txt` - 搜索结果输出文件

### 说明文档
- `README.md` - 项目概述
- `USAGE.md` - 详细使用说明
- `QUICKSTART.md` - 快速开始指南
- `START_HERE.md` - 从这里开始
- `PROJECT_SUMMARY.md` - 项目总结
- `FEATURES.md` - 功能特性
- `OPTIMIZATION.md` - 性能优化说明
- `COMPARISON.md` - 版本对比

## 特性

### 搜索工具
- ✅ 智能约束策略（书名 → 出版社 → 作者）
- ✅ 自动回退机制
- ✅ 按年份排序（最新优先）
- ✅ 重复检测和提示
- ✅ 实时进度显示
- ✅ 2秒超时 + 3次重试

### 下载工具
- ✅ 解析 `v` 标记的版本
- ✅ Dry-run 模式（预览下载）
- ✅ 下载次数限制检查
- ✅ 断点续传（待下载任务持久化）
- ✅ 详细日志输出

## 常见问题

### Q: 如何处理重复的搜索请求？
A: 脚本会自动检测并提示重复，后续结果会覆盖前面的。

### Q: 下载次数限制怎么办？
A: 工具会自动保存未下载的任务，下次运行时会优先处理。

### Q: 如何只下载部分书籍？
A: 只在 `list.txt` 中给想要下载的版本前加 `v` 标记。

### Q: 如何跳过已下载的书籍？
A: 使用 `--force` 参数重新下载，或使用 `-f` 简写。

## 命令行参数

### 搜索工具
```bash
python batch_search.py <输入文件> [输出文件]
```

### 下载工具
```bash
python batch_download.py [选项]

选项：
  --dry-run, -d    仅预览，不实际下载
  --force, -f      忽略已下载记录，重新下载
```

## 配置项

### 账号配置
- `DEFAULT_EMAIL` - 登录邮箱
- `DEFAULT_PASSWORD` - 登录密码
- `DEFAULT_REMIX_USERID` - Remix Token 用户ID（可选）
- `DEFAULT_REMIX_USERKEY` - Remix Token 密钥（可选）

### 下载配置
- `DEFAULT_INPUT_FILE` - 输入文件（默认: list.txt）
- `DEFAULT_OUTPUT_DIR` - 输出目录（默认: downloads）
- `DEFAULT_STATE_FILE` - 状态文件（默认: download_state.json）
- `DEFAULT_MAX_DOWNLOADS_PER_DAY` - 每日最大下载次数（默认: 10）
- `REQUEST_TIMEOUT` - 网络超时时间（默认: 2秒）

## 注意事项

1. 每日下载限制为10次，请合理安排
2. 下载的文件保存在 `downloads` 目录
3. 状态文件 `download_state.json` 记录下载进度
4. 如果遇到网络问题，工具会自动重试3次
