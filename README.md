# NewAPI 管理助手 — AstrBot 插件

通过 API Token 调用 NewAPI 管理接口，在聊天中直接管理你的 NewAPI 实例。支持传统命令和 LLM 工具调用。

## 前置条件

1. NewAPI 实例已部署（需要渡鸦 Fork 的 dev/main 分支，含 `PATCH /api/user/:id/group` 接口）
2. 管理员账号下有一个 API Token（在后台「令牌管理」中创建）
3. AstrBot >= 4.16.0

## 安装

1. 将本仓库放到 AstrBot 的 `plugins/` 目录下
2. 在 AstrBot WebUI 的插件管理中启用
3. 填写配置（见下方）

## 配置

| 字段 | 说明 | 示例 |
|------|------|------|
| `base_url` | NewAPI 地址 | `https://your-newapi-domain.com` |
| `admin_token` | 管理员 API Token | `sk-xxx` |
| `admin_user_id` | 管理员用户 ID | `1` |
| `owner_discord_id` | Bot 主人 Discord ID（分组/余额管理权限） | `YOUR_DISCORD_ID` |
| `quota_per_usd` | 额度/$ 换算 | `500000` |
| `page_size` | 列表每页条数 | `10` |
| `request_timeout` | 请求超时（秒） | `15` |

## 传统命令

| 命令 | 别名 | 说明 |
|------|------|------|
| `nstatus` | 新api状态、站子状态 | 系统状态 |
| `nself` | 我的信息、个人信息 | 管理员信息 |
| `nuser [页码]` | 用户列表、查用户 | 用户列表 |
| `nsearch <关键词>` | 搜索用户、找用户 | 按用户名搜索 |
| `nbalance <用户ID>` | 查余额、用户余额 | 查指定用户余额 |
| `nchannel [页码]` | 渠道列表、查渠道 | 渠道列表 |
| `ntoken [页码]` | 令牌列表、查令牌 | 令牌列表 |
| `nlog [用户名]` | 查日志、日志 | 最近日志 |
| `nredeem [页码]` | 兑换码、查兑换码 | 兑换码列表 |
| `nban <用户ID>` | 禁用用户 | 禁用用户 |
| `nunban <用户ID>` | 启用用户 | 启用用户 |
| `nquota <ID> <额度> [模式]` | 改余额、设置额度 | 修改用户余额（仅限主人） |
| `ngroup <ID> <分组名>` | 改分组 | 修改用户分组（仅限主人） |
| `ngroups` | 分组列表 | 查看可用分组（仅限主人） |
| `nhelp` | 管理帮助、n帮助 | 显示帮助 |

**余额模式说明：**
- `add` — 增加额度（默认）
- `subtract` — 减少额度
- `override` — 覆盖为指定值

**示例：**
```
nquota 5 1000000 add        # 给用户5增加 1,000,000 额度（$2）
nquota 5 500000 subtract    # 给用户5减少 500,000 额度（$1）
nquota 5 2500000 override   # 将用户5的额度覆盖为 2,500,000（$5）
```

## LLM 工具

插件注册了以下工具，AI 可通过自然语言调用：

| 工具 | 说明 |
|------|------|
| `newapi_status` | 获取系统状态 |
| `newapi_user_info` | 查询用户详情（需要 NewAPI 用户 ID） |
| `newapi_search_user` | 按用户名搜索 |
| `newapi_resolve_discord_user` | 解析 Discord 提及 → NewAPI 用户 |
| `newapi_user_list` | 用户列表 |
| `newapi_channel_list` | 渠道列表 |
| `newapi_token_list` | 令牌列表 |
| `newapi_logs` | 查询日志 |
| `newapi_set_user_balance` | 修改用户余额（仅限主人） |
| `newapi_set_user_group` | 修改用户分组（仅限主人，自动验证分组存在） |

**自然语言示例：**
- "查一下用户123的余额"
- "最近有什么日志"
- "帮我看下渠道状态"
- "把用户456改成雏鸟分组"
- "给用户123增加10美元额度"
- "把用户789的余额改成50美元"

> **注意：** 当消息中出现 Discord 提及（如 `<@123456>`）时，AI 会自动调用 `newapi_resolve_discord_user` 将 Discord ID 转换为 NewAPI 用户名。

## 分组管理特性

- **智能验证**：修改分组前自动验证分组是否存在
- **模糊匹配**：如输入"杂鱼"会自动匹配"杂鱼分组"
- **安全接口**：使用 `PATCH /api/user/:id/group` 只更新分组字段，不影响其他数据
- **权限控制**：只有 `owner_discord_id` 指定的用户可以修改分组和余额

## 原理

NewAPI 的 `AdminAuth()` 中间件支持通过 API Token（sk-xxx）调用管理接口：

```
Authorization: Bearer ***
New-Api-User: 1
```

- Token 必须属于管理员用户（role >= 100）
- 两个 Header 缺一不可
- 与 Session 方式相比：不会过期、适合 Bot 长期使用

## 注意事项

- 不要在聊天中暴露完整的 sk-xxx key
- 额度换算：500,000 单位 = $1 USD
- 禁用/启用用户操作会立即生效，请谨慎使用
- 余额修改使用 `POST /api/user/manage` 接口的 `add_quota` 功能
- `owner_discord_id` 控制分组管理和余额管理权限，只有该 Discord 用户可以操作

## 更新日志

### v1.4.3 (2026-05-18)
- 修复 LLM 工具和命令的 yield/return 混用语法错误
- AST 分析器全量扫描验证通过

### v1.4.0 (2026-05-18)
- 新增分组验证：修改分组前自动检查分组是否存在
- 模糊匹配：输入部分名称可匹配最接近的分组
- 新增余额管理：`nquota` 命令和 `newapi_set_user_balance` LLM 工具
- 支持增加、减少、覆盖三种模式

### v1.3.0 (2026-05-18)
- 分组修改改用 `PATCH /api/user/:id/group` 专用接口
- 彻底解决修改分组后用户消失的问题

### v1.2.0 (2026-05-18)
- 新增 `newapi_resolve_discord_user` LLM 工具
- 支持从 Discord 提及解析用户并查找 NewAPI 账户
- 修复 event API 调用错误（`get_sender_id()`）

### v1.1.0 (2026-05-18)
- 新增 LLM 工具调用功能
- 新增分组管理命令（`ngroup`、`ngroups`）
- 新增 `owner_discord_id` 配置字段

### v1.0.2 (2026-05-18)
- 添加 User-Agent 头，绕过 Cloudflare 1010 浏览器完整性检查

### v1.0.0 (2026-05-18)
- 初始版本
- 支持用户、渠道、令牌、日志、兑换码查询
- 支持禁用/启用用户
- 支持系统状态查询
