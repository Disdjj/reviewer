# AI Reviewer - 智能代码评审助手

<p align="center">
  <img src="https://img.shields.io/badge/AI-Powered-blue" alt="AI Powered">
  <img src="https://img.shields.io/badge/GitHub-Action-green" alt="GitHub Action">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/License-MIT-purple" alt="License MIT">
</p>

[English](#english) | [中文](#中文)

## 中文

### 🎯 简介

AI Reviewer 是一个基于人工智能的 GitHub Pull Request 自动评审工具。它使用先进的 AI 模型（如 GPT-4）来分析代码变更，提供专业的代码评审意见，帮助团队提高代码质量和开发效率。

### ✨ 特性

- 🤖 **智能代码分析**：使用 AI 深度分析代码变更，识别潜在问题
- 🔍 **多维度评审**：涵盖逻辑正确性、安全性、性能、可读性和可维护性
- 📊 **严重性分级**：将问题分为关键(critical)、警告(warning)和建议(suggestion)
- 💬 **行内评论**：直接在代码行上添加评审意见，方便开发者查看
- 🌍 **多语言支持**：支持多种自然语言的评审评论
- 🚫 **文件过滤**：支持通过 glob 模式排除特定文件
- 🔧 **灵活配置**：支持自定义 AI 模型和 API 端点

### 🚀 快速开始

#### 作为 GitHub Action 使用

1. 在你的仓库中创建 `.github/workflows/ai-review.yml` 文件：

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]
  issue_comment:
    types: [created]

jobs:
  review:
    # 仅在 PR 上运行（包括 PR 评论触发）
    if: github.event_name == 'pull_request' || (github.event.issue.pull_request && contains(github.event.comment.body, '/review'))
    runs-on: ubuntu-latest

    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: AI Review
        uses: Disdjj/reviewer@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          api-key: ${{ secrets.OPENAI_API_KEY }}
          base-url: https://api.openai.com/v1  # 可选，默认 OpenAI
          model: gpt-4o  # 可选，默认 gpt-4o
          language: zh  # 可选，默认 en
          exclude: "*.min.js,*.min.css,package-lock.json"  # 可选，排除文件
```

2. 在仓库设置中添加必要的 Secrets：
   - `OPENAI_API_KEY`：你的 OpenAI API 密钥（或其他兼容的 AI 服务密钥）

#### 本地运行

```bash
# 克隆仓库
git clone https://github.com/Disdjj/reviewer.git
cd reviewer

# 安装依赖
pip install -e .

# 设置环境变量
export GITHUB_TOKEN="your-github-token"
export API_KEY="your-openai-api-key"
export GITHUB_REPOSITORY="owner/repo"
export GITHUB_EVENT_PATH="path/to/event.json"

# 运行评审
python -m reviewer
```

### ⚙️ 配置选项

| 参数 | 必需 | 默认值 | 描述 |
|------|------|--------|------|
| `github-token` | ✅ | - | GitHub Token，用于 API 调用 |
| `api-key` | ✅ | - | AI 服务的 API 密钥 |
| `base-url` | ❌ | - | AI API 的基础 URL |
| `model` | ❌ | `gpt-4o` | 使用的 AI 模型 |
| `language` | ❌ | `en` | 评审评论的语言 |
| `exclude` | ❌ | - | 要排除的文件模式（逗号分隔） |

### 📋 工作原理

1. **事件触发**：当 PR 创建、更新或收到特定评论时触发
2. **获取变更**：通过 GitHub API 获取 PR 的 diff
3. **智能分析**：将代码变更按 hunk 分块，发送给 AI 进行分析
4. **生成评论**：AI 返回结构化的评审意见
5. **提交评审**：将评论作为 PR review 提交到 GitHub

### 🎨 评审重点

AI Reviewer 会重点关注以下方面：

- **逻辑正确性**：代码是否按预期工作，是否有逻辑错误
- **安全问题**：SQL 注入、XSS、硬编码密钥等安全漏洞
- **性能问题**：N+1 查询、低效算法、内存泄漏等
- **代码质量**：可读性、可维护性、命名规范、复杂度
- **最佳实践**：是否遵循语言和框架的最佳实践

### 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

### 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## English

### 🎯 Introduction

AI Reviewer is an AI-powered automatic code review tool for GitHub Pull Requests. It uses advanced AI models (like GPT-4) to analyze code changes and provide professional code review comments, helping teams improve code quality and development efficiency.

### ✨ Features

- 🤖 **Intelligent Code Analysis**: Deep analysis of code changes using AI to identify potential issues
- 🔍 **Multi-dimensional Review**: Covers logic correctness, security, performance, readability, and maintainability
- 📊 **Severity Classification**: Categorizes issues as critical, warning, or suggestion
- 💬 **Inline Comments**: Adds review comments directly on code lines for easy reference
- 🌍 **Multi-language Support**: Supports review comments in multiple natural languages
- 🚫 **File Filtering**: Supports excluding specific files via glob patterns
- 🔧 **Flexible Configuration**: Supports custom AI models and API endpoints

### 🚀 Quick Start

#### Using as GitHub Action

1. Create `.github/workflows/ai-review.yml` in your repository:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]
  issue_comment:
    types: [created]

jobs:
  review:
    # Only run on PRs (including PR comment triggers)
    if: github.event_name == 'pull_request' || (github.event.issue.pull_request && contains(github.event.comment.body, '/review'))
    runs-on: ubuntu-latest

    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: AI Review
        uses: Disdjj/reviewer@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          api-key: ${{ secrets.OPENAI_API_KEY }}
          base-url: https://api.openai.com/v1  # Optional, defaults to OpenAI
          model: gpt-4o  # Optional, defaults to gpt-4o
          language: en  # Optional, defaults to en
          exclude: "*.min.js,*.min.css,package-lock.json"  # Optional, exclude files
```

2. Add required Secrets in repository settings:
   - `OPENAI_API_KEY`: Your OpenAI API key (or other compatible AI service key)

#### Running Locally

```bash
# Clone repository
git clone https://github.com/Disdjj/reviewer.git
cd reviewer

# Install dependencies
pip install -e .

# Set environment variables
export GITHUB_TOKEN="your-github-token"
export API_KEY="your-openai-api-key"
export GITHUB_REPOSITORY="owner/repo"
export GITHUB_EVENT_PATH="path/to/event.json"

# Run review
python -m reviewer
```

### ⚙️ Configuration Options

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `github-token` | ✅ | - | GitHub Token for API calls |
| `api-key` | ✅ | - | API key for AI service |
| `base-url` | ❌ | - | Base URL for AI API |
| `model` | ❌ | `gpt-4o` | AI model to use |
| `language` | ❌ | `en` | Language for review comments |
| `exclude` | ❌ | - | File patterns to exclude (comma-separated) |

### 📋 How It Works

1. **Event Trigger**: Triggered when PR is created, updated, or receives specific comments
2. **Fetch Changes**: Get PR diff via GitHub API
3. **Intelligent Analysis**: Split code changes into hunks and send to AI for analysis
4. **Generate Comments**: AI returns structured review comments
5. **Submit Review**: Submit comments as PR review to GitHub

### 🎨 Review Focus

AI Reviewer focuses on the following aspects:

- **Logic Correctness**: Whether code works as intended, logic errors
- **Security Issues**: SQL injection, XSS, hardcoded secrets, etc.
- **Performance Issues**: N+1 queries, inefficient algorithms, memory leaks
- **Code Quality**: Readability, maintainability, naming conventions, complexity
- **Best Practices**: Following language and framework best practices

### 🤝 Contributing

Contributions are welcome! Please see [Contributing Guide](CONTRIBUTING.md) for details.

### 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ by AI enthusiasts
</p>
