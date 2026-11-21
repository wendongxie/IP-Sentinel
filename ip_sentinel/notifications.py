"""Windows Credential Manager and outbound notification adapters."""
import json
import re
from urllib.parse import urlsplit

import httpx

from .network import open_client
from keyring.backends.Windows import WinVaultKeyring

from .detection import TAGS, failure
from .risk_lists import evidence_line

FIELDS = {
    "risk_key": "IPWhois Pro API 密钥",
    "telegram_token": "Telegram Bot Token",
    "telegram_chat": "Telegram Chat ID",
    "wecom": "企业微信机器人 Webhook",
}


def load():
    vault = WinVaultKeyring()
    stored = vault.get_password("IP Sentinel", "settings")
    values = json.loads(stored) if stored else dict.fromkeys(FIELDS, "")
    validate(values)
    return values


def validate(values):
    token, chat = values["telegram_token"], values["telegram_chat"]
    if token or chat:
        if not re.fullmatch(r"\d+:[A-Za-z0-9_-]+", token) or not re.fullmatch(
            r"-?\d+|@[A-Za-z0-9_]+", chat
        ):
            raise ValueError("请同时填写有效的 Telegram Bot Token 和 Chat ID。")
    webhook = values["wecom"]
    if webhook:
        url = urlsplit(webhook)
        if (url.scheme != "https" or url.netloc != "qyapi.weixin.qq.com"
                or url.path != "/cgi-bin/webhook/send" or url.fragment
                or not re.fullmatch(r"key=[A-Za-z0-9_-]+", url.query)):
            raise ValueError("请填写有效的企业微信机器人 HTTPS Webhook。")


def save(values):
    validate(values)
    vault = WinVaultKeyring()
    if any(values.values()):
        vault.set_password("IP Sentinel", "settings", json.dumps(values))
    elif vault.get_password("IP Sentinel", "settings") is not None:
        vault.delete_password("IP Sentinel", "settings")


def format_change_alert(timestamp, observations):
    """Use current evidence only and keep both protocol sections readable."""
    changed = [obs for obs in observations if obs.previous]
    if not changed:
        return ""

    def compact(value):
        return " ".join(str(value if value is not None else "").split())[:18]

    local_time = timestamp.astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    lines = ["IP Sentinel｜公网出口变化", f"检测时间  {local_time}"]
    risk_states = {True: "命中", False: "未标记", None: "未知"}
    for obs in changed:
        location = " / ".join(filter(None, (compact(obs.info.get(key))
                                            for key in ("country", "region", "city"))))
        asn = compact(obs.info.get("asn"))
        provider = compact(obs.info.get("isp")) or compact(obs.info.get("org"))
        network = " · ".join(filter(None, (f"AS{asn}" if asn.isdecimal() else asn, provider)))
        risk = " · ".join(f"{name.upper()} {risk_states[obs.tags.get(name)]}" for name in TAGS)
        lines.extend((
            "", f"IPv{obs.family}",
            f"原 IP  {obs.previous}", f"新 IP  {obs.ip}",
            f"新出口归属  {location or '未知'}",
            f"网络  {network or '未知'}",
            f"风险标签  {risk}",
            f"情报来源  {obs.metadata_source or '未取得'}",
        ))
        lines.extend(evidence_line(item, compact=True) for item in obs.list_evidence)
    if any(obs.list_evidence for obs in changed):
        lines.append("名单未收录仅表示该来源未找到记录。")
    return "\n".join(lines)


def send(values, message, transport=None):
    validate(values)
    results = []
    with open_client(8, transport) as client:
        targets = []
        if values["telegram_token"]:
            targets.append((
                "Telegram", f"https://api.telegram.org/bot{values['telegram_token']}/sendMessage",
                {"chat_id": values["telegram_chat"], "text": message},
                lambda data: data.get("ok") is True,
            ))
        if values["wecom"]:
            targets.append((
                "企业微信", values["wecom"], {"msgtype": "text", "text": {"content": message}},
                lambda data: type(data.get("errcode")) is int and data["errcode"] == 0,
            ))
        for name, url, payload, accepted in targets:
            try:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                ok = isinstance(data, dict) and accepted(data)
                results.append(f"{name}：{'已发送' if ok else '服务拒绝请求'}")
            except (httpx.HTTPError, ValueError) as exc:
                results.append(f"{name}：发送失败 ({failure(exc)})")
    return results






