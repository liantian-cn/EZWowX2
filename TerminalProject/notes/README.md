# Terminal 实验笔记

这个目录只放 Python 实验笔记。

适合放的内容: 

- 从 gist 拿下来的小脚本
- 两个 API 的性能比较
- 某个库或写法的临时验证

不适合放的内容: 

- `Terminal/terminal/` 的正式实现
- `Terminal/tests/` 的项目测试
- 需要被正式模块 import 的公共代码

这里的脚本默认单独运行，例如: 

```powershell
uv run python Terminal/notes/example.py
```

如果某段实验代码后来被确认有长期价值，请复制整理到正式目录，不要直接把这里的文件继续扩写成正式功能。
