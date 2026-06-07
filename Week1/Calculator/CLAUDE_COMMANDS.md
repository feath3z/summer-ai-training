# Claude Code 常用命令速查表

> 适用于 Claude Code CLI、Desktop App、Web App (claude.ai/code) 及 IDE 扩展

---

## 1. CLI 启动与标志

### 基本启动

```bash
claude                              # 启动交互式 REPL
claude "你的提示"                    # 带初始提示启动 REPL
claude -p "提示"                    # 非交互模式，输出结果后退出（print mode）
claude -p "提示" | clip             # 管道模式，可与其他工具组合
```

### 常用标志

```bash
claude --help                       # 显示帮助信息
claude --version                    # 显示版本号
claude --model <model-id>           # 指定模型
claude --resume                     # 恢复最近的会话
claude --continue                   # 继续最近的会话
claude --conversation-id <id>       # 恢复指定会话
claude --max-turns <N>              # 限制最大交互轮次（自动化用）
claude --system-prompt "..."        # 自定义系统提示
claude --append-system-prompt "..." # 追加系统提示
claude --allowedTools "t1,t2"       # 限制可用工具列表
claude --disallowedTools "..."      # 禁用特定工具
claude --permission-mode <mode>     # 权限模式（见第 14 节）
claude --verbose                    # 详细日志输出
claude --debug                      # 调试模式
```

### 输出格式（脚本/管道）

```bash
claude -p "提示" --output-format json          # JSON 格式
claude -p "提示" --output-format text          # 纯文本
claude -p "提示" --output-format stream-json   # 流式 JSON
```

### 子命令

```bash
claude config                       # 查看/修改配置
claude config set <key> <value>     # 设置配置项
claude config get <key>             # 获取配置项
claude config list                  # 列出所有配置
claude update                       # 更新 Claude Code
claude doctor                       # 诊断安装问题
claude mcp add <name> -- <command>  # 添加 MCP 服务器
claude mcp list                     # 列出已配置的 MCP 服务器
claude mcp remove <name>            # 移除 MCP 服务器
```

---

## 2. REPL 斜杠命令

### 内置命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/clear` | 清除当前对话上下文 |
| `/compact [焦点]` | 压缩对话历史，可选指定压缩焦点 |
| `/cost` | 显示当前会话的 token 使用量和费用 |
| `/doctor` | 诊断环境问题 |
| `/init` | 在当前目录初始化 CLAUDE.md 文件 |
| `/login` | 登录 Anthropic 账户 |
| `/logout` | 登出账户 |
| `/memory` | 打开/编辑 CLAUDE.md 记忆文件 |
| `/model [model-id]` | 查看或切换模型 |
| `/permissions` | 查看当前权限设置 |
| `/review` | 审查当前 diff / PR |
| `/terminal-setup` | 配置终端集成（Shift+Enter 换行等） |
| `/vim` | 切换 Vim 编辑模式 |
| `/fast` | 切换到更快的模型（Haiku） |
| `/slow` | 切换到更强的模型（Opus） |
| `/config` | 打开/查看配置 |
| `/mcp` | 查看 MCP 服务器状态 |
| `/status` | 显示当前状态信息 |
| `/worktree` | 进入隔离的 git worktree 工作 |

### 自动补全

在 REPL 中输入 `/` 后按 `Tab` 可自动补全所有可用的斜杠命令。

---

## 3. 键盘快捷键

### 基本操作

| 快捷键 | 说明 |
|--------|------|
| `Enter` | 发送消息 |
| `Shift+Enter` | 换行（需先运行 `/terminal-setup`） |
| `Escape` | 中断当前生成 / 取消输入 |
| `Ctrl+C` | 中断当前操作 / 退出 |
| `Ctrl+D` | 退出 REPL |
| `Tab` | 自动补全（文件路径、命令等） |
| `Ctrl+L` | 清屏 |

### 行编辑

| 快捷键 | 说明 |
|--------|------|
| `Ctrl+A` | 移动到行首 |
| `Ctrl+E` | 移动到行尾 |
| `Ctrl+K` | 删除到行尾 |
| `Ctrl+U` | 删除到行首 |
| `Ctrl+W` | 删除前一个单词 |
| `Ctrl+Y` | 粘贴（yank） |
| `↑` / `↓` | 浏览命令历史 |

### Vim 模式（`/vim` 启用后）

| 快捷键 | 说明 |
|--------|------|
| `Esc` | 进入 Normal 模式 |
| `i` | 进入 Insert 模式 |
| `o` | 新行并进入 Insert 模式 |

---

## 4. 特殊输入前缀

| 前缀 | 说明 | 示例 |
|------|------|------|
| `!` | 直接执行 shell 命令 | `!git status`、`!npm test` |

---

## 5. 模型选择

```bash
# REPL 内切换
/model                              # 查看当前模型
/model claude-sonnet-4-6            # 切换到 Sonnet
/model claude-opus-4-8              # 切换到 Opus
/model claude-haiku-4-5-20251001    # 切换到 Haiku
/fast                               # 快速切换到轻量模型
/slow                               # 切换到最强模型

# CLI 启动时指定
claude --model claude-sonnet-4-6

# 环境变量覆盖
ANTHROPIC_MODEL=claude-sonnet-4-6 claude
```

**当前模型家族（2026）**

| 模型 | Model ID | 定位 |
|------|----------|------|
| Opus 4.8 | `claude-opus-4-8` | 最强能力 |
| Sonnet 4.6 | `claude-sonnet-4-6` | 均衡性能 |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | 快速响应 |

---

## 6. 权限模式

| 模式 | 说明 |
|------|------|
| `default` | 危险操作需用户逐次确认 |
| `auto-accept` (yolo) | 自动接受所有操作 |
| `plan` | 只读模式，不允许任何修改 |

### settings.json 精细控制

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash(npm test)",
      "Bash(git *)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(sudo *)"
    ]
  }
}
```

通配符示例：`Bash(git *)` 匹配所有 git 命令，`Read` / `Write` / `Edit` 匹配对应工具类。

---

## 7. 配置文件与位置

### 文件层级

```
~/.claude/settings.json                 # 用户全局设置
~/.claude/keybindings.json              # 键盘快捷键自定义
<project>/.claude/settings.json         # 项目级设置（可提交 git）
<project>/.claude/settings.local.json   # 项目本地设置（不提交）
<project>/CLAUDE.md                     # 项目级指令文件
<project>/subdir/CLAUDE.md              # 子目录级指令
~/.claude/CLAUDE.md                     # 全局指令（所有项目生效）
```

### 优先级（从高到低）

1. 项目本地 `.claude/settings.local.json`
2. 项目共享 `.claude/settings.json`
3. 用户全局 `~/.claude/settings.json`

### settings.json 完整结构

```json
{
  "permissions": {
    "allow": ["Bash(npm test)", "Read"],
    "deny": ["Bash(sudo *)"]
  },
  "env": {
    "MY_VAR": "value"
  },
  "hooks": {
    "PreToolUse": [],
    "PostToolUse": [],
    "Stop": []
  },
  "includeCoAuthoredBy": false
}
```

---

## 8. CLAUDE.md 记忆系统

### 层级结构

```
~/.claude/CLAUDE.md              # 全局记忆（所有项目生效）
<project>/CLAUDE.md              # 项目记忆（项目根目录）
<project>/subdir/CLAUDE.md       # 子目录记忆（在该目录工作时生效）
```

### 管理方式

| 方式 | 说明 |
|------|------|
| `/memory` | 在编辑器中打开 CLAUDE.md |
| `/init` | 自动分析项目并生成初始 CLAUDE.md |
| 直接编辑 | 用任意编辑器修改文件 |

### 推荐内容

- 项目架构说明
- 编码规范和约定
- 常用命令（构建、测试、部署）
- 已知问题和技术债务
- 团队工作流

---

## 9. MCP 服务器配置

### CLI 管理

```bash
claude mcp add <name> -- <command> [args...]   # 添加 stdio 服务器
claude mcp add <name> -t sse <url>             # 添加 SSE 类型服务器
claude mcp add <name> -t http <url>            # 添加 HTTP 类型服务器
claude mcp remove <name>                       # 移除服务器
claude mcp list                                # 列出服务器
```

### settings.json 配置

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "@example/mcp-server"],
      "env": { "API_KEY": "..." }
    },
    "sse-server": {
      "type": "sse",
      "url": "https://example.com/mcp"
    }
  }
}
```

### 作用域

- 用户级：`~/.claude/settings.json`
- 项目级：`.claude/settings.json` 或 `.claude/settings.local.json`

---

## 10. Hooks 系统

Hooks 在特定事件触发时自动执行 shell 命令，配置在 `settings.json` 中。

### 事件类型

| 事件 | 触发时机 |
|------|---------|
| `PreToolUse` | 工具调用之前 |
| `PostToolUse` | 工具调用之后 |
| `Stop` | Claude 停止响应时 |
| `Notification` | 发送通知时 |

### 环境变量

| 变量 | 说明 |
|------|------|
| `$CLAUDE_TOOL_NAME` | 工具名称 |
| `$CLAUDE_TOOL_INPUT` | 工具输入（JSON） |
| `$CLAUDE_TOOL_OUTPUT` | 工具输出（PostToolUse） |
| `$CLAUDE_FILE_PATH` | 涉及的文件路径（Write/Edit） |

### 配置示例

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write $CLAUDE_FILE_PATH"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "say '任务完成'"
          }
        ]
      }
    ]
  }
}
```

---

## 11. 会话管理

```bash
# 恢复会话
claude --resume                     # 恢复最近会话
claude --continue                   # 继续最近会话
claude --conversation-id <id>       # 恢复指定会话

# REPL 内管理
/clear                              # 清除当前上下文
/compact                            # 压缩对话历史（节省 context window）
/cost                               # 查看 token 用量和费用
```

会话自动保存在 `~/.claude/projects/` 目录下。

---

## 12. IDE 集成

### VS Code

- 扩展名：**Claude Code**
- 安装：VS Code 扩展市场搜索 "Claude Code"
- 功能：侧边栏集成、文件选择、差异对比查看

### JetBrains（IntelliJ / PyCharm / WebStorm 等）

- 插件名：**Claude Code**
- 安装：Settings → Plugins → 搜索 "Claude Code"
- 功能：与 VS Code 类似的集成体验

### 终端集成

运行 `/terminal-setup` 配置终端以支持 `Shift+Enter` 换行。支持 iTerm2、Terminal.app、Windows Terminal、GNOME Terminal 等。

---

## 13. 更新

```bash
claude update                                           # 内置更新
npm update -g @anthropic-ai/claude-code                 # 通过 npm 更新
```

---

## 14. 常见场景速查

| 场景 | 命令 / 操作 |
|------|------------|
| 快速提问 | `claude -p "Python 怎么读 JSON 文件"` |
| 代码审查 | REPL 中输入 `/review` 或粘贴 diff |
| 初始化项目指令 | `/init` |
| 查看费用 | `/cost` |
| 上下文太长 | `/compact` 或 `/clear` |
| 切换模型 | `/model claude-sonnet-4-6` |
| 执行 shell 命令 | `!git status` |
| 减少确认弹窗 | settings.json 中配置 `permissions.allow` |
| 自动格式化 | Hooks 的 `PostToolUse` + prettier |
| 并行任务 | 使用 `/worktree` 或 Agent 工具 |
| 恢复上次对话 | `claude --resume` |
| 管道集成 | `claude -p "提示" --output-format json` |
