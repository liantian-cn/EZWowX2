# Demo

这个项目只提供一份用于重构的HowToRebuild.md和这个戒律牧demo.

其实json都拿到了，做这个一点都没难度

demo使用方法如下

安装环境和依赖

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv init --python 3.12 --name demo
uv add certifi==2026.1.4
uv add charset-normalizer==3.4.4
uv add idna==3.11
uv add markdown-it-py==4.0.0
uv add mdurl==0.1.2
uv add nuitka==4.0.1
uv add pygments==2.19.2
uv add pyside6==6.10.2
uv add pyside6-addons==6.10.2
uv add pyside6-essentials==6.10.2
uv add pywin32==311
uv add requests==2.32.5
uv add rich==14.3.2
uv add shiboken6==6.10.2
uv add urllib3==2.6.3
```

执行脚本

```powershell

uv run .\PriestDiscipline.py
```

其实改一改，就能做其他职业了把。
