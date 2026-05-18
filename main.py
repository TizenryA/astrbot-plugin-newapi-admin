"""
NewAPI 管理助手 AstrBot 插件
通过 API Token 调用 NewAPI 管理接口，支持查询用户、渠道、日志、余额、系统状态等。
"""

import json
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import astrbot.api.message_components as Comp
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register


@register(
    "newapi_admin",
    "渡鸦",
    "通过 API Token 管理 NewAPI 实例 — 查询用户、渠道、日志、余额、系统状态",
    "1.0.1",
)
class NewAPIAdmin(Star):
    """NewAPI 管理助手插件"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.base_url: str = config.get("base_url", "https://tizenry.xyz").rstrip("/")
        self.admin_token: str = config.get("admin_token", "").strip()
        self.admin_user_id: int = int(config.get("admin_user_id", 1))
        self.quota_per_usd: int = int(config.get("quota_per_usd", 500000))
        self.page_size: int = int(config.get("page_size", 10))
        self.timeout: int = int(config.get("request_timeout", 15))
        logger.info(f"[NewAPIAdmin] v1.0.1 已加载，目标: {self.base_url}, 用户ID: {self.admin_user_id}")

    # ── HTTP 工具 ──────────────────────────────────────────────

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "New-Api-User": str(self.admin_user_id),
            "Content-Type": "application/json",
        }

    def _get(self, path: str) -> Dict[str, Any]:
        """同步 GET 请求，返回 JSON dict"""
        url = f"{self.base_url}{path}"
        req = Request(url=url, method="GET")
        for k, v in self._headers().items():
            req.add_header(k, v)
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            # 尝试从 body 提取更详细的错误信息
            detail = ""
            if body:
                try:
                    err_json = json.loads(body)
                    detail = err_json.get("message", body[:200])
                except Exception:
                    detail = body[:200]
            msg = f"HTTP {e.code}: {e.reason}"
            if detail:
                msg += f" — {detail}"
            logger.warning(f"[NewAPIAdmin] GET {path} 失败: {msg}")
            return {"success": False, "message": msg}
        except URLError as e:
            logger.warning(f"[NewAPIAdmin] GET {path} 连接失败: {e.reason}")
            return {"success": False, "message": f"连接失败: {e.reason}"}
        except Exception as e:
            logger.warning(f"[NewAPIAdmin] GET {path} 异常: {e}")
            return {"success": False, "message": str(e)}

    def _put(self, path: str, data: Dict) -> Dict[str, Any]:
        """同步 PUT 请求"""
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode()
        req = Request(url=url, data=body, method="PUT")
        for k, v in self._headers().items():
            req.add_header(k, v)
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            detail = ""
            if body_text:
                try:
                    err_json = json.loads(body_text)
                    detail = err_json.get("message", body_text[:200])
                except Exception:
                    detail = body_text[:200]
            msg = f"HTTP {e.code}: {e.reason}"
            if detail:
                msg += f" — {detail}"
            logger.warning(f"[NewAPIAdmin] PUT {path} 失败: {msg}")
            return {"success": False, "message": msg}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── 额度换算 ──────────────────────────────────────────────

    def _fmt_quota(self, quota: int) -> str:
        """额度转美元显示"""
        usd = quota / self.quota_per_usd
        if usd >= 1:
            return f"${usd:.2f}"
        return f"${usd:.4f}"

    def _fmt_tokens(self, tokens: int) -> str:
        if tokens >= 1_000_000_000:
            return f"{tokens / 1_000_000_000:.1f}B"
        if tokens >= 1_000_000:
            return f"{tokens / 1_000_000:.1f}M"
        if tokens >= 1_000:
            return f"{tokens / 1_000:.1f}K"
        return str(tokens)

    def _ts_to_str(self, ts: int) -> str:
        if ts == 0:
            return "永不过期"
        dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
        return dt.strftime("%Y-%m-%d %H:%M")

    # ── 命令：系统状态 ────────────────────────────────────────

    @filter.command("nstatus", alias={"新api状态", "站子状态"})
    async def cmd_status(self, event: AstrMessageEvent):
        """查看 NewAPI 系统状态"""
        resp = self._get("/api/status")
        if not resp.get("success"):
            yield event.plain_result(f"❌ 查询失败: {resp.get('message', '未知错误')}")
            return

        d = resp.get("data", {})
        uptime_s = int(time.time()) - d.get("start_time", int(time.time()))
        days = uptime_s // 86400
        hours = (uptime_s % 86400) // 3600
        mins = (uptime_s % 3600) // 60

        lines = [
            f"🖥️ {d.get('system_name', 'NewAPI')} 状态",
            f"├ 版本: {d.get('version', '未知') or '自编译'}",
            f"├ 主题: {d.get('theme', '?')}",
            f"├ 运行: {days}天{hours}时{mins}分",
            f"├ 汇率: 1 USD = {d.get('usd_exchange_rate', 7.3)} CNY",
            f"├ 额度比: {d.get('quota_per_unit', 500000):,} = $1",
            f"└ Discord: {'✅' if d.get('discord_oauth') else '❌'}",
        ]
        yield event.plain_result("\n".join(lines))

    # ── 命令：查询自己 ────────────────────────────────────────

    @filter.command("nself", alias={"我的信息", "个人信息"})
    async def cmd_self(self, event: AstrMessageEvent):
        """查询管理员自身信息"""
        resp = self._get("/api/user/self")
        if not resp.get("success"):
            yield event.plain_result(f"❌ 查询失败: {resp.get('message')}")
            return

        u = resp["data"]
        quota = u.get("quota", 0)
        used = u.get("used_quota", 0)
        remain = quota - used
        lines = [
            f"👤 {u.get('username', '?')} (ID: {u.get('id')})",
            f"├ 角色: {'管理员' if u.get('role', 0) >= 100 else '用户'}",
            f"├ 总额度: {self._fmt_quota(quota)}",
            f"├ 已使用: {self._fmt_quota(used)}",
            f"├ 剩余: {self._fmt_quota(remain)}",
            f"└ 请求数: {u.get('request_count', 0):,}",
        ]
        yield event.plain_result("\n".join(lines))

    # ── 命令：用户列表 ────────────────────────────────────────

    @filter.command("nuser", alias={"用户列表", "查用户"})
    async def cmd_users(self, event: AstrMessageEvent, page: int = 1):
        """查询用户列表，支持翻页: nuser 2"""
        p = max(1, page)
        resp = self._get(f"/api/user/?p={p}&size={self.page_size}")
        if not resp.get("success"):
            yield event.plain_result(f"❌ 查询失败: {resp.get('message')}")
            return

        d = resp.get("data", {})
        items = d.get("items", [])
        total = d.get("total", 0)
        total_pages = (total + self.page_size - 1) // self.page_size

        if not items:
            yield event.plain_result("📭 没有用户数据")
            return

        lines = [f"👥 用户列表 ({total}人) 第{p}/{total_pages}页"]
        for u in items:
            role_icon = "👑" if u.get("role", 0) >= 100 else "👤"
            status_icon = "✅" if u.get("status", 1) == 1 else "🚫"
            remain = u.get("quota", 0) - u.get("used_quota", 0)
            lines.append(
                f"{status_icon}{role_icon} #{u['id']} {u.get('username', '?')} "
                f"| 余{self._fmt_quota(remain)} "
                f"| 用{self._fmt_quota(u.get('used_quota', 0))}"
            )
        if p < total_pages:
            lines.append(f"📄 下一页: nuser {p + 1}")
        yield event.plain_result("\n".join(lines))

    # ── 命令：搜索用户 ────────────────────────────────────────

    @filter.command("nsearch", alias={"搜索用户", "找用户"})
    async def cmd_search_user(self, event: AstrMessageEvent, keyword: str = ""):
        """按用户名搜索: nsearch 关键词"""
        if not keyword:
            yield event.plain_result("用法: nsearch <用户名关键词>")
            return

        resp = self._get(f"/api/user/search?keyword={keyword}&p=0&size=10")
        if not resp.get("success"):
            yield event.plain_result(f"❌ 搜索失败: {resp.get('message')}")
            return

        items = resp.get("data", {}).get("items", [])
        if not items:
            yield event.plain_result(f"🔍 未找到包含「{keyword}」的用户")
            return

        lines = [f"🔍 搜索「{keyword}」找到 {len(items)} 个用户"]
        for u in items:
            role_icon = "👑" if u.get("role", 0) >= 100 else "👤"
            remain = u.get("quota", 0) - u.get("used_quota", 0)
            lines.append(
                f"{role_icon} #{u['id']} {u.get('username', '?')} "
                f"| 余{self._fmt_quota(remain)} "
                f"| 请求{u.get('request_count', 0):,}"
            )
        yield event.plain_result("\n".join(lines))

    # ── 命令：查用户余额 ──────────────────────────────────────

    @filter.command("nbalance", alias={"查余额", "用户余额"})
    async def cmd_balance(self, event: AstrMessageEvent, user_id: int = 0):
        """查询指定用户余额: nbalance 用户ID"""
        if user_id <= 0:
            yield event.plain_result("用法: nbalance <用户ID>")
            return

        resp = self._get(f"/api/user/{user_id}")
        if not resp.get("success"):
            yield event.plain_result(f"❌ 查询失败: {resp.get('message')}")
            return

        u = resp["data"]
        quota = u.get("quota", 0)
        used = u.get("used_quota", 0)
        remain = quota - used
        lines = [
            f"💰 {u.get('username', '?')} (ID: {u.get('id')})",
            f"├ 总额度: {self._fmt_quota(quota)}",
            f"├ 已使用: {self._fmt_quota(used)}",
            f"├ 剩余: {self._fmt_quota(remain)}",
            f"├ 请求数: {u.get('request_count', 0):,}",
            f"└ 状态: {'正常' if u.get('status', 1) == 1 else '已禁用'}",
        ]
        yield event.plain_result("\n".join(lines))

    # ── 命令：渠道列表 ────────────────────────────────────────

    @filter.command("nchannel", alias={"渠道列表", "查渠道"})
    async def cmd_channels(self, event: AstrMessageEvent, page: int = 1):
        """查询渠道列表"""
        p = max(1, page)
        resp = self._get(f"/api/channel/?p={p}&size={self.page_size}")
        if not resp.get("success"):
            yield event.plain_result(f"❌ 查询失败: {resp.get('message')}")
            return

        d = resp.get("data", {})
        items = d.get("items", [])
        total = d.get("total", 0)

        if not items:
            yield event.plain_result("📭 没有渠道数据")
            return

        lines = [f"📡 渠道列表 ({total}个) 第{p}页"]
        for ch in items:
            status_icon = "✅" if ch.get("status", 1) == 1 else "🚫"
            balance = ch.get("balance", 0)
            balance_str = f"${balance:.2f}" if balance else "?"
            lines.append(
                f"{status_icon} #{ch['id']} {ch.get('name', '?')} "
                f"| 类型{ch.get('type', '?')} "
                f"| 余额{balance_str} "
                f"| 模型{len(ch.get('models', '').split(',')) if ch.get('models') else 0}个"
            )
        yield event.plain_result("\n".join(lines))

    # ── 命令：令牌列表 ────────────────────────────────────────

    @filter.command("ntoken", alias={"令牌列表", "查令牌"})
    async def cmd_tokens(self, event: AstrMessageEvent, page: int = 1):
        """查询令牌列表"""
        p = max(1, page)
        resp = self._get(f"/api/token/?p={p}&size={self.page_size}")
        if not resp.get("success"):
            yield event.plain_result(f"❌ 查询失败: {resp.get('message')}")
            return

        d = resp.get("data", {})
        items = d.get("items", [])
        total = d.get("total", 0)

        if not items:
            yield event.plain_result("📭 没有令牌数据")
            return

        lines = [f"🔑 令牌列表 ({total}个) 第{p}页"]
        for tk in items:
            status_icon = "✅" if tk.get("status", 1) == 1 else "🚫"
            remain = tk.get("remain_quota", 0)
            lines.append(
                f"{status_icon} #{tk['id']} {tk.get('name', '?')} "
                f"| 用户{tk.get('user_id', '?')} "
                f"| 余{self._fmt_quota(remain)} "
                f"| 已用{self._fmt_quota(tk.get('used_quota', 0))}"
            )
        yield event.plain_result("\n".join(lines))

    # ── 命令：日志查询 ────────────────────────────────────────

    @filter.command("nlog", alias={"查日志", "日志"})
    async def cmd_logs(self, event: AstrMessageEvent, username: str = ""):
        """查询最近日志: nlog 或 nlog 用户名"""
        path = f"/api/log/?p=0&size=10"
        if username:
            path += f"&username={username}"

        resp = self._get(path)
        if not resp.get("success"):
            yield event.plain_result(f"❌ 查询失败: {resp.get('message')}")
            return

        d = resp.get("data", {})
        items = d.get("items", [])
        total = d.get("total", 0)

        if not items:
            yield event.plain_result("📭 没有日志数据")
            return

        title = f"📋 日志{'（' + username + '）' if username else ''} 共{total}条"
        lines = [title]
        tz8 = timezone(timedelta(hours=8))
        for log in items[:10]:
            ts = log.get("created_at", 0)
            dt = datetime.fromtimestamp(ts, tz=tz8).strftime("%m-%d %H:%M")
            model = log.get("model_name", "?")
            quota = log.get("quota", 0)
            user = log.get("username", "?")
            lines.append(f"[{dt}] {user} → {model} | {self._fmt_quota(quota)}")
        yield event.plain_result("\n".join(lines))

    # ── 命令：兑换码列表 ──────────────────────────────────────

    @filter.command("nredeem", alias={"兑换码", "查兑换码"})
    async def cmd_redemptions(self, event: AstrMessageEvent, page: int = 1):
        """查询兑换码列表"""
        p = max(1, page)
        resp = self._get(f"/api/redemption/?p={p}&size={self.page_size}")
        if not resp.get("success"):
            yield event.plain_result(f"❌ 查询失败: {resp.get('message')}")
            return

        d = resp.get("data", {})
        items = d.get("items", [])
        total = d.get("total", 0)

        if not items:
            yield event.plain_result("📭 没有兑换码数据")
            return

        status_map = {1: "🟢未用", 2: "⚪已禁", 3: "🔴已用"}
        lines = [f"🎫 兑换码列表 ({total}个) 第{p}页"]
        for r in items:
            status = status_map.get(r.get("status", 1), "❓")
            max_uses = r.get("max_uses", 0)
            used_count = r.get("used_count", 0)
            if max_uses > 0:
                usage = f"{used_count}/{max_uses}次"
            else:
                usage = f"{used_count}/1次"
            lines.append(
                f"{status} #{r['id']} {r.get('name', '?')} "
                f"| {self._fmt_quota(r.get('quota', 0))} "
                f"| {usage}"
            )
        yield event.plain_result("\n".join(lines))

    # ── 命令：禁用用户 ────────────────────────────────────────

    @filter.command("nban", alias={"禁用用户"})
    async def cmd_ban_user(self, event: AstrMessageEvent, user_id: int = 0):
        """禁用用户: nban 用户ID"""
        if user_id <= 0:
            yield event.plain_result("用法: nban <用户ID>")
            return

        resp = self._put("/api/user/", {"id": user_id, "status": 2})
        if resp.get("success"):
            yield event.plain_result(f"🚫 已禁用用户 #{user_id}")
        else:
            yield event.plain_result(f"❌ 操作失败: {resp.get('message')}")

    # ── 命令：启用用户 ────────────────────────────────────────

    @filter.command("nunban", alias={"启用用户"})
    async def cmd_unban_user(self, event: AstrMessageEvent, user_id: int = 0):
        """启用用户: nunban 用户ID"""
        if user_id <= 0:
            yield event.plain_result("用法: nunban <用户ID>")
            return

        resp = self._put("/api/user/", {"id": user_id, "status": 1})
        if resp.get("success"):
            yield event.plain_result(f"✅ 已启用用户 #{user_id}")
        else:
            yield event.plain_result(f"❌ 操作失败: {resp.get('message')}")

    # ── 命令：帮助 ────────────────────────────────────────────

    @filter.command("nhelp", alias={"管理帮助", "n帮助"})
    async def cmd_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        lines = [
            "🔧 NewAPI 管理助手 v1.0.1",
            "━━━━━━━━━━━━━━━━━━━━",
            "nstatus — 系统状态",
            "nself — 管理员信息",
            "nuser [页码] — 用户列表",
            "nsearch <关键词> — 搜索用户",
            "nbalance <用户ID> — 查用户余额",
            "nchannel [页码] — 渠道列表",
            "ntoken [页码] — 令牌列表",
            "nlog [用户名] — 最近日志",
            "nredeem [页码] — 兑换码列表",
            "nban <用户ID> — 禁用用户",
            "nunban <用户ID> — 启用用户",
            "nhelp — 本帮助",
        ]
        yield event.plain_result("\n".join(lines))
