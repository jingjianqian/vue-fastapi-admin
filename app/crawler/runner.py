import asyncio
import os
import sys
import tempfile
import time
import contextlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

from app.log import logger
from app.models.script import Script, ScriptRun, CrawlerSetting

RUNTIME_DIR = Path("app_runtime/scripts").resolve()
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


async def get_settings() -> CrawlerSetting:
    obj = await CrawlerSetting.filter(id=1).first()
    if not obj:
        obj = await CrawlerSetting.create(id=1)
    return obj


def _truncate_tail(text: str, max_bytes: int) -> str:
    if text is None:
        return text
    b = text.encode("utf-8", errors="ignore")
    if len(b) <= max_bytes:
        return text
    tail = b[-max_bytes:]
    return tail.decode("utf-8", errors="ignore")


def _to_epoch_ms(dt: datetime) -> int:
    """将 datetime 安全地转为 epoch 毫秒，自动处理有/无时区的情况，避免 naive/aware 相减报错"""
    if dt is None:
        return 0
    try:
        return int(dt.timestamp() * 1000)
    except Exception:
        # 极端情况下兜底：去掉 tzinfo 再转
        return int(dt.replace(tzinfo=None).timestamp() * 1000)


async def run_script(script: Script, timeout_sec: Optional[int] = None) -> ScriptRun:
    settings = await get_settings()
    if timeout_sec is None:
        timeout_sec = settings.default_timeout_sec
    max_log_bytes = settings.max_log_bytes

    run = await ScriptRun.create(script=script, status="queued")

    # 将代码写入临时文件
    ts = int(time.time())
    work_dir = RUNTIME_DIR / f"s_{script.id}_{ts}"
    work_dir.mkdir(parents=True, exist_ok=True)
    script_path = work_dir / "main.py"
    script_path.write_text(script.code, encoding="utf-8")

    # 运行子进程
    cmd = [sys.executable, "-u", str(script_path)]
    logger.info(f"[script] run id={run.id} script_id={script.id} name={script.name} cmd={' '.join(cmd)}")

    await ScriptRun.filter(id=run.id).update(status="running", started_at=datetime.now())
    run = await ScriptRun.filter(id=run.id).first()

    try:
        try:
            # 优先使用 asyncio 子进程
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(work_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await ScriptRun.filter(id=run.id).update(pid=proc.pid)

            try:
                outs, errs = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
                exit_code = proc.returncode
                status = "success" if exit_code == 0 else "error"
            except asyncio.TimeoutError:
                with contextlib.suppress(Exception):
                    proc.kill()
                outs, errs = await proc.communicate()
                exit_code = None
                status = "timeout"
        except NotImplementedError:
            # Windows Proactor 回退：在线程中运行阻塞式 subprocess.run
            import subprocess
            try:
                completed = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    cwd=str(work_dir),
                    capture_output=True,
                    text=False,
                    timeout=timeout_sec,
                    shell=False,
                )
                outs = completed.stdout or b""
                errs = completed.stderr or b""
                exit_code = completed.returncode
                status = "success" if exit_code == 0 else "error"
            except subprocess.TimeoutExpired as e:
                outs = (e.stdout or b"")
                errs = (e.stderr or b"TimeoutExpired")
                exit_code = None
                status = "timeout"

        stdout_txt = (outs or b"").decode("utf-8", errors="ignore")
        stderr_txt = (errs or b"").decode("utf-8", errors="ignore")

        stdout_txt = _truncate_tail(stdout_txt, max_log_bytes)
        stderr_txt = _truncate_tail(stderr_txt, max_log_bytes)

        ended_at = datetime.now()
        # 使用 epoch 计算避免 naive/aware 混用报错
        try:
            duration_ms = max(0, _to_epoch_ms(ended_at) - _to_epoch_ms(run.started_at or ended_at))
        except Exception as _:
            duration_ms = None
        await ScriptRun.filter(id=run.id).update(
            status=status,
            ended_at=ended_at,
            exit_code=exit_code,
            stdout=stdout_txt,
            stderr=stderr_txt,
            duration_ms=duration_ms,
        )

    except Exception as e:
        logger.exception(f"[script] run failed id={run.id} err={e}")
        await ScriptRun.filter(id=run.id).update(
            status="error",
            ended_at=datetime.now(),
            exit_code=-1,
            stderr=str(e),
        )

    # 清理历史记录
    await cleanup_runs()

    run = await ScriptRun.filter(id=run.id).first()
    return run


async def cleanup_runs() -> int:
    settings = await get_settings()
    keep_before = datetime.now() - timedelta(days=settings.retention_days)
    qs = ScriptRun.filter(ended_at__lt=keep_before)
    count = await qs.count()
    if count:
        await qs.delete()
        logger.info(f"[script] cleanup runs deleted={count} before={keep_before}")
    return count
