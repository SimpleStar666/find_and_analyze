# GitHub Repo Finder

从 GitHub 中搜索符合自己需求的仓库，并使用 AI 智能总结内容，输出到 Markdown 文档中。

## 功能特性

- 🔍 **关键词搜索**：输入关键词即可搜索 GitHub 上的相关仓库
- 🤖 **AI 智能总结**：基于 OpenAI 兼容 API（DeepSeek、通义千问等）对仓库进行智能总结
- 📄 **Markdown 导出**：一键将搜索结果和 AI 总结导出为 Markdown 文件
- 🖥️ **桌面应用**：基于 PyQt5 的原生桌面应用，界面美观
- 📦 **一键打包**：支持打包为独立 exe，无需安装 Python 即可运行

## Windows 用户（免安装运行）

### 方式一：直接运行打包好的 exe

1. 从 `dist/` 目录获取 `GitHubRepoFinder.exe`
2. 双击运行即可，无需安装 Python 或任何依赖
3. 导出的报告保存在 exe 同级目录的 `output/` 文件夹中

### 方式二：自己打包 exe

1. 安装 Python 3.8+（[下载地址](https://www.python.org/downloads/)），安装时勾选 "Add Python to PATH"
2. 双击运行 `build.bat`
3. 打包完成后，`dist/GitHubRepoFinder.exe` 即为独立可执行文件

## 开发者（从源码运行）

```bash
pip install -r requirements.txt
python main.py
```

## 使用说明

1. **配置 AI 服务**：在「设置」标签页填入 API 地址、API Key 和模型名称
2. **搜索仓库**：在「搜索」标签页输入关键词，点击搜索
3. **查看详情**：点击列表中的仓库查看详细信息
4. **AI 总结**：点击「AI 总结」对单个仓库总结，或「批量总结所有」
5. **导出报告**：点击「导出 Markdown」将结果保存为文件

## 项目结构

```
github-repo-finder/
├── main.py                  # 入口文件
├── build.bat                # Windows 一键打包脚本
├── GitHubRepoFinder.spec    # PyInstaller 打包配置
├── version_info.txt         # Windows 版本信息
├── app_icon.png             # 应用图标
├── requirements.txt         # 依赖
├── src/
│   ├── app.py               # 应用主入口
│   ├── ui/
│   │   ├── main_window.py   # 主窗口
│   │   ├── search_tab.py    # 搜索标签页
│   │   └── settings_tab.py  # 设置标签页
│   ├── services/
│   │   ├── github_service.py    # GitHub API
│   │   ├── ai_service.py        # AI 总结
│   │   └── export_service.py    # Markdown 导出
│   └── models/
│       └── repo.py          # 仓库数据模型
└── output/                  # 导出文件目录
```
