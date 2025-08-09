# Contributing to AI Reviewer / 贡献指南

Thank you for your interest in contributing to AI Reviewer! / 感谢您对 AI Reviewer 项目的贡献意向！

## How to Contribute / 如何贡献

### Reporting Issues / 报告问题

1. Check if the issue already exists / 检查问题是否已存在
2. Create a new issue with a clear title and description / 创建新问题，提供清晰的标题和描述
3. Include steps to reproduce if applicable / 如果适用，包含重现步骤

### Submitting Pull Requests / 提交 PR

1. Fork the repository / Fork 仓库
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Make your changes / 进行修改
4. Add tests if applicable / 如果适用，添加测试
5. Commit your changes (`git commit -m 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Create a Pull Request / 创建 Pull Request

### Code Style / 代码风格

- Follow PEP 8 for Python code / Python 代码遵循 PEP 8
- Use meaningful variable and function names / 使用有意义的变量和函数名
- Add comments for complex logic / 为复杂逻辑添加注释
- Keep functions focused and small / 保持函数专注且小巧

### Testing / 测试

- Write tests for new features / 为新功能编写测试
- Ensure all tests pass before submitting PR / 提交 PR 前确保所有测试通过
- Test with different Python versions if possible / 如果可能，测试不同的 Python 版本

### Documentation / 文档

- Update README if needed / 如需要，更新 README
- Add docstrings to functions and classes / 为函数和类添加文档字符串
- Include examples when appropriate / 适当时包含示例

## Development Setup / 开发设置

```bash
# Clone your fork / 克隆你的 fork
git clone https://github.com/Disdjj/reviewer.git
cd reviewer

# Create virtual environment / 创建虚拟环境
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode / 开发模式安装
pip install -e .

# Install development dependencies / 安装开发依赖
pip install pytest black isort mypy
```

## Questions? / 有问题？

Feel free to open an issue or start a discussion! / 欢迎开启 issue 或讨论！
