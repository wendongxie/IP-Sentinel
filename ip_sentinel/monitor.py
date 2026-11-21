"""Schedule and serialize manual and automatic checks."""
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler

from . import detection, notifications


class Monitor:
    def __init__(self, history, started, observed, finished, risk=None):
        self.history = history
        self.risk = risk
        self.started = started
        self.observed = observed
        self.finished = finished
        self.lock = Lock()
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self.scheduler.add_job(self.run, "interval", hours=1, coalesce=True,
                               misfire_grace_time=3600, max_instances=1)
        self.scheduler.start()
        if self.risk:
            self.risk.start()

    def run(self):
        if not self.lock.acquire(blocking=False):
            return
        stage = "初始化"
        try:
            self.started()
            try:
                values = notifications.load()
                credential_status = []
            except Exception as exc:
                values = dict.fromkeys(notifications.FIELDS, "")
                credential_status = [f"凭据读取失败 ({type(exc).__name__})"]
            stage = "探测公网出口"
            timestamp, observations = detection.detect(values["risk_key"])
            if self.risk:
                for obs in observations:
                    if obs.ip:
                        obs.list_evidence = self.risk.evidence(obs.ip)
            stage = "保存检测历史"
            self.history.record(timestamp, observations)
            stage = "处理检测结果"
            message = notifications.format_change_alert(timestamp, observations)
            self.observed(timestamp, observations, message)
            if message:
                stage = "发送变化通知"
                credential_status.extend(notifications.send(values, message))
            status = " · ".join(credential_status) or "检测完成"
        except Exception as exc:
            status = f"{stage}失败 ({type(exc).__name__})"
        finally:
            self.lock.release()
        self.finished(status)

    def manual(self):
        self.scheduler.add_job(self.run, misfire_grace_time=10)

    def shutdown(self):
        if self.risk:
            self.risk.stop()
        self.scheduler.shutdown(wait=True)





