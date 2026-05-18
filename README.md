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
| `base_url` | NewAPI 地址 | `https://tizenry.xyz` |
| `admin_token` | 管理员 API Token | `sk-xxx` |
| `admin_user_id` | 管理员用户 ID | `1` |
| `owner_discord_id` | Bot 主人 Discord ID（分组管理权限） | `1119117027831992350` |
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
| `ngroup <ID> <分组名>` | 改分组 | 修改用户分组（仅限主人） |
| `ngroups` | 分组列表 | 查看可用分组（仅限主人） |
| `nhelp` | 管理帮助、n帮助 | 显示帮助 |

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
| `newapi_set_user_group` | 修改用户分组（仅限主人） |

**自然语言示例：**
- "查一下用户123的余额"
- "最近有什么日志"
- "帮我看下渠道状态"
- "把用户456改成雏鸟分组"

> **注意：** 当消息中出现 Discord 提及（如 `<@123456>`）时，AI 会自动调用 `newapi_resolve_discord_user` 将 Discord ID 转换为 NewAPI 用户名。

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
- 分组管理使用 `PATCH /api/user/:id/group` 接口，只更新分组字段，不影响其他数据
- `owner_discord_id` 控制分组管理权限，只有该 Discord 用户可以修改分组
