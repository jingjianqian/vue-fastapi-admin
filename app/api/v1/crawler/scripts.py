from fastapi import APIRouter, Body, Query
from typing import Optional
import sys
import json
import asyncio
import subprocess
import contextlib

from app.schemas.base import Success, Fail, SuccessExtra
from app.models.script import Script, ScriptRun, CrawlerSetting
from app.crawler.runner import run_script, get_settings, cleanup_runs

router = APIRouter(tags=["爬虫脚本平台"])


@router.get("/script/list", summary="脚本列表")
async def script_list(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    qs = Script.all().order_by("-id")
    total = await qs.count()
    rows = await qs.offset((page-1)*page_size).limit(page_size)
    data = [
        {
            "id": r.id,
            "name": r.name,
            "desc": r.desc,
            "enabled": r.enabled,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        } for r in rows
    ]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/script/get", summary="获取脚本")
async def script_get(id: int = Query(...)):
    r = await Script.filter(id=id).first()
    if not r:
        return Fail(code=404, msg="脚本不存在")
    return Success(data={
        "id": r.id,
        "name": r.name,
        "desc": r.desc,
        "code": r.code,
        "requirements": r.requirements,
        "enabled": r.enabled,
    })


@router.post("/script/create", summary="创建脚本")
async def script_create(body: dict = Body(...)):
    try:
        obj = await Script.create(
            name=body.get("name"),
            desc=body.get("desc"),
            code=body.get("code") or "print('hello world')\n",
            requirements=body.get("requirements"),
            enabled=bool(body.get("enabled", True)),
        )
        return Success(data={"id": obj.id})
    except Exception as e:
        return Fail(code=500, msg=str(e))


@router.post("/script/update", summary="更新脚本")
async def script_update(body: dict = Body(...)):
    r = await Script.filter(id=body.get("id")).first()
    if not r:
        return Fail(code=404, msg="脚本不存在")
    for k in ["name", "desc", "code", "requirements", "enabled"]:
        if k in body:
            setattr(r, k, body.get(k))
    await r.save()
    return Success(data={"ok": True})


@router.delete("/script/delete", summary="删除脚本")
async def script_delete(id: int = Query(...)):
    deleted = await Script.filter(id=id).delete()
    return Success(data={"deleted": deleted})


@router.post("/script/run", summary="运行脚本")
async def script_run(body: dict = Body(...)):
    script_id = int(body.get("id"))
    timeout_sec: Optional[int] = body.get("timeout_sec")
    r = await Script.filter(id=script_id, enabled=True).first()
    if not r:
        return Fail(code=404, msg="脚本不存在或未启用")
    run = await run_script(r, timeout_sec=timeout_sec)
    return Success(data={"run_id": run.id, "status": run.status})


@router.get("/script/run_status", summary="运行状态")
async def script_run_status(run_id: int = Query(...)):
    run = await ScriptRun.filter(id=run_id).first()
    if not run:
        return Fail(code=404, msg="运行不存在")
    return Success(data={
        "id": run.id,
        "script_id": run.script_id,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "ended_at": run.ended_at.isoformat() if run.ended_at else None,
        "exit_code": run.exit_code,
        "pid": run.pid,
        "duration_ms": run.duration_ms,
    })


@router.get("/script/run_logs", summary="运行日志")
async def script_run_logs(run_id: int = Query(...)):
    run = await ScriptRun.filter(id=run_id).first()
    if not run:
        return Fail(code=404, msg="运行不存在")
    return Success(data={
        "stdout": run.stdout or "",
        "stderr": run.stderr or "",
    })


# ---- 依赖管理 ----
async def _run_cmd(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """
    统一的命令执行器：
    - 优先使用 asyncio 子进程（POSIX 以及 Windows Selector Loop 可用）
    - 在 Windows ProactorEventLoop 上回退到线程中的 subprocess.run，避免 NotImplementedError
    """
    try:
        # 尝试原生异步子进程（Linux/macOS/部分 Windows 配置可用）
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            with contextlib.suppress(Exception):
                proc.kill()
            out, err = await proc.communicate()
        code = proc.returncode
        return code, out.decode('utf-8', errors='ignore'), err.decode('utf-8', errors='ignore')
    except NotImplementedError:
        # Windows 下 ProactorEventLoop 不支持 subprocess，回退到线程执行阻塞式 subprocess.run
        try:
            completed = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )
            return completed.returncode, completed.stdout or "", completed.stderr or ""
        except subprocess.TimeoutExpired as e:
            return 1, (e.stdout or ""), (e.stderr or "TimeoutExpired")
        except Exception as e:
            return 1, "", f"subprocess error: {e}"
    except Exception as e:
        # 兜底，确保接口不会因异常而崩溃
        return 1, "", f"{type(e).__name__}: {e}"


@router.get("/pip/list", summary="已安装依赖")
async def pip_list():
    code, out, err = await _run_cmd([sys.executable, "-m", "pip", "list", "--format", "json"], timeout=120)
    if code != 0:
        return Fail(code=500, msg=err.strip() or "pip list failed")
    try:
        data = json.loads(out)
    except Exception:
        data = []
    return Success(data=data)


@router.get("/pip/show", summary="查询依赖信息（按名称）")
async def pip_show(name: str = Query(...)):
    # 优先从 PyPI JSON 获取元数据
    import httpx
    url = f"https://pypi.org/pypi/{name}/json"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                j = resp.json()
                info = j.get("info", {})
                releases = j.get("releases", {})
                latest = info.get("version")
                return Success(data={
                    "name": info.get("name") or name,
                    "version": latest,
                    "summary": info.get("summary"),
                    "home_page": info.get("home_page"),
                    "project_url": info.get("project_url") or info.get("project_urls"),
                    "releases": list(releases.keys())[-20:],
                })
    except Exception:
        pass
    # 回退 pip index versions
    code, out, err = await _run_cmd([sys.executable, "-m", "pip", "index", "versions", name], timeout=20)
    if code != 0:
        return Fail(code=404, msg="未找到该包")
    return Success(data={"raw": out})


@router.post("/pip/install", summary="安装依赖（到当前后端环境）")
async def pip_install(body: dict = Body(...)):
    name = (body.get("name") or "").strip()
    if not name:
        return Fail(code=400, msg="缺少 name")
    code, out, err = await _run_cmd([sys.executable, "-m", "pip", "install", "-U", name], timeout=900)
    ok = code == 0
    return Success(data={"ok": ok, "stdout": out, "stderr": err, "code": code})


# ---- 设置 ----
@router.get("/settings/get", summary="获取脚本平台设置")
async def settings_get():
    s = await get_settings()
    return Success(data={
        "retention_days": s.retention_days,
        "default_timeout_sec": s.default_timeout_sec,
        "max_log_bytes": s.max_log_bytes,
    })


@router.post("/settings/update", summary="更新脚本平台设置")
async def settings_update(body: dict = Body(...)):
    s = await get_settings()
    for k in ["retention_days", "default_timeout_sec", "max_log_bytes"]:
        if k in body and body[k] is not None:
            setattr(s, k, int(body[k]))
    await s.save()
    return Success(data={"ok": True})


@router.post("/maintenance/cleanup_runs", summary="手动清理过期运行记录")
async def maintenance_cleanup_runs():
    deleted = await cleanup_runs()
    return Success(data={"deleted": deleted})
