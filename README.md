# quickfuck — Optimized for Python 3.12+ and WSL2

[English](#english) | [中文](#chinese)

---

<a name="english"></a>
## English

Based on [thefuck](https://github.com/nvbn/thefuck) v3.32 with Python 3.12 compatibility fixes,
~20x performance improvements for WSL2, and structural refactoring for maintainability.

### What's Improved

#### Python 3.12 Compatibility
| File | Issue | Fix |
|------|-------|-----|
| `thefuck/system/unix.py` | `distutils.spawn.find_executable` removed in 3.12 | Replaced with `shutil.which` |
| `thefuck/conf.py` | `imp.load_source` removed in 3.12 | Replaced with `importlib.util.spec_from_file_location` |
| `thefuck/types.py` | `imp.load_source` removed in 3.12 | Same as above |

#### Performance Optimizations
| Optimization | Location | Effect |
|-------------|----------|--------|
| Single-pass PATH scan + dict cache | `utils.py: which()` | Eliminates ~1943 stat() calls (85% of original latency) |
| `os.scandir()` + PATH dedup | `utils.py: get_all_executables()` | Avoids redundant scanning |
| Thread-safe double-checked locking | `cache.py: _executable_cache` | Prevents race conditions during parallel rule loading |
| Parallel rule loading + output capture | `fix_command.py` + `corrector.py` | Two slowest steps run concurrently via Thread + ThreadPoolExecutor (~32 workers) |
| Shell alias captures `TF_LAST_OUTPUT` | `shells/{bash,zsh,fish}.py` | Skips Python Popen re-execution of the failed command (3.4x faster on the hot path) |
| Subprocess result caching | `fish.py`, `git_checkout.py`, `apt_invalid_operation.py`, `gradle_no_task.py` | `@memoize` on subprocess-heavy helpers |
| Settings compilation cached | `conf.py` | `functools.lru_cache` avoids recompiling `settings.py` every invocation |
| Lazy debug formatting | `logs.py` | `.format()` deferred until `settings.debug` check passes |
| Wasted sorts removed | `corrector.py` | Removed `sorted()` call whose result was immediately discarded by set construction |
| Regex → `str.endswith` | `utils.py: replace_argument()` | Avoids dynamic regex compilation per call |
| `split(' ', 1)` micro-optimizations | `shells/` | First-token extraction without full string split |

#### Bug Fixes (8 crash-level)
| Bug | File | Symptom |
|-----|------|---------|
| `brew_path_prefix` is `None` → `TypeError` | `brew_unknown_command.py`, `brew_install.py` | Crash when Homebrew not installed |
| `script_parts[2]` accessed with only 2 parts | `docker_not_command.py`, `git_fix_stash.py` | `IndexError` on short commands |
| `else` clause on `if` instead of `for` | `shell_logger.py: get_output()` | Only first command ever checked |
| `filename_index` uninitialized | `git_flag_after_filename.py` | `UnboundLocalError` with all-flag args |
| History commands hijacking fuzzy matches | `no_command.py` | `dcker` → `clear` instead of `docker` |
| `chmod x` not corrected to `chmod +x` | *(new rule)* `chmod_missing_plus.py` | Missing rule added |

#### Code Quality & Refactoring
| Change | Detail |
|--------|--------|
| `utils.py`: 386 → 218 lines | Extracted caching to `cache.py` (176 lines) |
| `logs.py`: 149 → 65 lines | Extracted UI rendering to `display.py` (94 lines) |
| Rules reorganized | 168 rules grouped into 34 domain subdirectories (`rules/git/`, `rules/apt/`, `rules/brew/`, etc.) |
| Thread-safe `Settings` | `threading.RLock` on all mutation methods |
| Thread-safe `Cache` | `threading.Lock` protecting `_init_db()` |
| `DEVNULL` fd leak fixed | Replaced with `subprocess.DEVNULL` |
| `TypeVar` dead import removed | `utils.py` |
| `test.py.py` renamed | Double extension fixed → `test_dot_py.py` |

### Project Structure (after refactoring)

```
thefuck/
├── cache.py              # Memoization, persistent cache, state reset
├── conf.py               # Settings (thread-safe singleton)
├── const.py              # Constants & defaults
├── corrector.py          # Rule discovery & command correction engine
├── display.py            # Terminal UI rendering (colors, prompts, wizards)
├── exceptions.py         # Exception classes
├── logs.py               # Debug/warning/exception logging
├── types.py              # Domain models: Command, Rule, CorrectedCommand
├── ui.py                 # Interactive keyboard-driven command selector
├── utils.py              # PATH scanning, fuzzy matching, decorators, helpers
├── argument_parser.py
├── entrypoints/          # CLI entry points (main, fix_command, alias, etc.)
├── shells/               # Shell adapters (bash, zsh, fish, tcsh, powershell)
├── system/               # Platform abstraction (unix.py, win32.py)
├── output_readers/       # Command output capture strategies
├── specific/             # Tool-specific helpers (git, sudo, apt, brew, npm, etc.)
└── rules/                # 168 correction rules in 34 domain directories
    ├── git/ (15)          ├── git_branch/ (11)    ├── git_sync/ (17)
    ├── system/ (15)       ├── shell/ (15)         ├── file_ops/ (10)
    ├── typo/ (10)         ├── npm_yarn/ (7)       ├── brew/ (7)
    ├── apt/ (5)           └── ...19 more categories
```

### Benchmarks (WSL2)

| Phase | Original | Optimized |
|-------|----------|-----------|
| PATH executable scan | ~2.24s (1943 stat calls) | ~0.01s (single scandir) |
| Rule loading | ~2.13s (sequential) | ~0.05s (parallel + cache) |
| Command re-execution | ~0.14s (Python Popen) | ~0s (shell alias pre-capture) |
| **Total** | **~2.64s** | **~0.13s (~20x faster)** |

109 tests passing. All 12 tested correction scenarios verified on WSL2.

### Installation

```bash
# Clone
git clone https://github.com/JesseLee-CN/quickfuck.git ~/projects/fuck
cd ~/projects/fuck

# Install (recommended: pipx for isolated venv)
pipx install -e .

# Or: pip user install
pip install --user -e .

# Configure shell alias
echo 'eval "$(thefuck --alias)"' >> ~/.bashrc
source ~/.bashrc

# WSL2: skip Windows mount points (optional but recommended)
mkdir -p ~/.config/thefuck
cp user-settings.py ~/.config/thefuck/settings.py

# Verify
fuck --version
```

### Dependencies

- Python >= 3.7
- psutil, colorama, pyte

### License

MIT (same as upstream)

---

<a name="chinese"></a>
## 中文

基于 [thefuck](https://github.com/nvbn/thefuck) v3.32 的深度优化版本。
修复 Python 3.12 兼容性，WSL2 下性能提升约 20 倍，并完成结构化重构。

### 改进总览

#### Python 3.12 兼容性
| 文件 | 问题 | 修复 |
|------|------|------|
| `thefuck/system/unix.py` | `distutils.spawn.find_executable` 在 3.12 中移除 | 替换为 `shutil.which` |
| `thefuck/conf.py` | `imp.load_source` 在 3.12 中移除 | 替换为 `importlib.util.spec_from_file_location` |
| `thefuck/types.py` | 同上 | 同上 |

#### 性能优化（13 项）
| 优化 | 位置 | 效果 |
|------|------|------|
| 单次 PATH 扫描 + dict 缓存 | `utils.py: which()` | 消除 ~1943 次 stat() 调用 |
| 线程安全双检锁 | `cache.py` | 防止并行规则加载竞态 |
| 规则加载与输出捕获并行 | `fix_command.py` + `corrector.py` | Thread + ThreadPoolExecutor(32) 并行 |
| Shell alias 预捕获输出 (`TF_LAST_OUTPUT`) | `shells/{bash,zsh,fish}.py` | 跳过 Python Popen 重执行，热路径 3.4x 加速 |
| 子进程结果缓存 | `fish.py`, `git_checkout.py` 等 4 处 | `@memoize` 避免重复 subprocess |
| 用户配置编译缓存 | `conf.py` | `functools.lru_cache` 避免每次编译 settings.py |
| 惰性 debug 格式化 | `logs.py` | debug 关闭时不执行 `.format()` |
| 消除无效排序 | `corrector.py` | 移除 set 构造前被丢弃的 `sorted()` |
| 正则 → `str.endswith` | `utils.py: replace_argument()` | 消除每次调用的动态正则编译 |
| `split(' ', 1)` 微优化 | `shells/` | 只切分第一个空格 |

#### Bug 修复（8 个崩溃级）
| Bug | 文件 | 症状 |
|-----|------|------|
| `brew_path_prefix` 为 `None` → `TypeError` | `brew_unknown_command.py`, `brew_install.py` | Homebrew 未安装时崩溃 |
| `script_parts[2]` 仅 2 个元素时访问 | `docker_not_command.py`, `git_fix_stash.py` | 短命令触发 `IndexError` |
| `else` 错挂在 `if` 而非 `for` | `shell_logger.py: get_output()` | 只检查第一条命令即返回 |
| `filename_index` 未初始化 | `git_flag_after_filename.py` | 全 flag 参数时 `UnboundLocalError` |
| 历史命令劫持模糊匹配 | `no_command.py` | `dcker` → `clear` 而非 `docker` |
| `chmod x` 无法纠正为 `chmod +x` | *(新规则)* `chmod_missing_plus.py` | 新增规则 |

#### 工程重构
| 变更 | 详情 |
|------|------|
| `utils.py`: 386 → 218 行 | 拆分出 `cache.py` (176 行)，打破循环导入 |
| `logs.py`: 149 → 65 行 | 拆分出 `display.py` (94 行)，UI 渲染独立 |
| 规则重组 | 168 个规则按 34 个领域分目录（`rules/git/`、`rules/apt/` 等） |
| `Settings` 线程安全 | 所有写操作加 `threading.RLock` |
| `Cache` 线程安全 | `_init_db()` 加锁保护 |
| `DEVNULL` fd 泄露修复 | 替换为 `subprocess.DEVNULL` |
| 死代码清理 | 移除未使用的 `TypeVar` 导入，修复 `test.py.py` 双扩展名 |

### 项目结构（重构后）

```
thefuck/
├── cache.py              # 缓存系统（memoize, Cache, reset_state）
├── conf.py               # 配置（线程安全单例）
├── const.py              # 常量与默认值
├── corrector.py          # 规则发现与命令修正引擎
├── display.py            # 终端 UI 渲染
├── exceptions.py         # 异常类
├── logs.py               # 日志系统
├── types.py              # 领域模型
├── ui.py                 # 交互式键盘选择器
├── utils.py              # PATH 扫描、模糊匹配、装饰器、辅助函数
├── entrypoints/          # CLI 入口（5 个文件）
├── shells/               # Shell 适配器（6 种 shell）
├── system/               # 平台抽象（unix.py / win32.py）
├── output_readers/       # 输出捕获策略（3 种）
├── specific/             # 工具特定辅助（11 个模块）
└── rules/                # 168 条修正规则（34 个子目录）
```

### 性能数据 (WSL2)

| 阶段 | 优化前 | 优化后 |
|------|--------|--------|
| PATH 可执行文件扫描 | ~2.24s | ~0.01s |
| 规则加载 | ~2.13s (顺序) | ~0.05s (并行 + 缓存) |
| 命令重执行 | ~0.14s (Python Popen) | ~0s (shell alias 预捕获) |
| **总计** | **~2.64s** | **~0.13s (~20 倍提速)** |

109 个测试全部通过。12 个实际纠正场景均在 WSL2 上验证通过。

### 安装方法

```bash
# 克隆项目
git clone https://github.com/JesseLee-CN/quickfuck.git ~/projects/fuck
cd ~/projects/fuck

# 安装（推荐 pipx，隔离虚拟环境）
pipx install -e .

# 或 pip 用户安装
pip install --user -e .

# 配置 shell 别名
echo 'eval "$(thefuck --alias)"' >> ~/.bashrc
source ~/.bashrc

# WSL2 优化（跳过 Windows 挂载路径）
mkdir -p ~/.config/thefuck
cp user-settings.py ~/.config/thefuck/settings.py

# 验证
fuck --version
```

### 依赖

- Python >= 3.7
- psutil, colorama, pyte

### License

MIT（同上游）
