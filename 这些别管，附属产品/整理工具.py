#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""了了了游投稿精选整理工具（仅 Python 标准库，零依赖、零构建）。

子命令：
  build              只读扫描六个来源，生成 投稿清单.json（逐款入选/剔除判定）
  apply [--dry-run]  按清单复制入选、移动剔除项、注入代码内署名，并生成审核清单
  verify             复核产物：署名齐全、无外部依赖、清单与磁盘一致

设计约束（来自已确认的 plan 与 https://game.leleleling.site/game_rules 5.0.0）：
  * 不物理删除任何文件，剔除项一律移动到 准备删除/，可完整回滚。
  * 不删改任何 LICENSE 的版权行，不把已知作者写成「未知作者」。
  * 不生成卡片导航页，不在游戏内内嵌三类法律协议页面。
  * 每款游戏独立存放，全套资源保留，游戏本体玩法/样式/交互不改。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "收集到的游戏"
TRASH = ROOT / "准备删除"
NOTICE_DIR = OUT / "_版权与来源"
MANIFEST = ROOT / "投稿清单.json"
REPORT = ROOT / "投稿审核清单.md"

S1 = ROOT / "lelele-game-games-1-main"
S3 = ROOT / "lelele-game-games-3-main"
S4 = ROOT / "lelele-game-games-4-main"
S5 = ROOT / "lelele-game-games-5-main"
S6 = ROOT / "lelele-game-games-6-main"

ATTR_BEGIN = "<!-- LELELE-ATTRIBUTION-START -->"
ATTR_END = "<!-- LELELE-ATTRIBUTION-END -->"
DIV_BEGIN = "<!-- LELELE-ATTRIBUTION-VISIBLE -->"

LICENSE_SOURCES = {
    "LICENSE-games-1-MIT.txt": S1 / "LICENSE",
    "LICENSE-games-3-MIT.txt": S3 / "LICENSE",
    "LICENSE-games-5-GPL-3.0.txt": S5 / "LICENSE",
    "LICENSE-games-5-hunt-MIT.txt": S5 / "hunt" / "LICENSE",
    "LICENSE-games-6-MIT.txt": S6 / "LICENSE",
}


def load_license_texts() -> dict:
    """许可原文可能已被移入 准备删除/，按 原位 -> 精选副本 -> 暂存 顺序回退读取。"""
    out: dict[str, str] = {}
    for name, src in LICENSE_SOURCES.items():
        candidates = (src, NOTICE_DIR / name, TRASH / src.relative_to(ROOT))
        for p in candidates:
            if p.is_file():
                out[name] = p.read_text(encoding="utf-8")
                break
        else:
            out[name] = ""
            print(f"[warn] 未找到许可原文：{src}", file=sys.stderr)
    return out


LICENSE_COPIES = load_license_texts()
MIT_1 = LICENSE_COPIES["LICENSE-games-1-MIT.txt"]
MIT_3 = LICENSE_COPIES["LICENSE-games-3-MIT.txt"]
MIT_5 = LICENSE_COPIES["LICENSE-games-5-hunt-MIT.txt"]
GPL_5 = LICENSE_COPIES["LICENSE-games-5-GPL-3.0.txt"]
MIT_6 = LICENSE_COPIES["LICENSE-games-6-MIT.txt"]

THIRD_PARTY_NOTICES = """# 第三方许可与素材声明

本目录存放投稿精选集中各来源仓库的许可证原文副本。以下为逐项说明，投稿时须随游戏一同保留。

## 各来源许可

| 来源 | 作者 | 许可 | 副本文件 |
|---|---|---|---|
| lelele-game-games-1-main（mini-browser-games） | wangzifan396-wzf | MIT，Copyright (c) 2026 | LICENSE-games-1-MIT.txt |
| lelele-game-games-3-main（game-collection） | kejilion | MIT，Copyright (c) 2026 | LICENSE-games-3-MIT.txt |
| lelele-game-games-5-main（HTML-Games） | highwindmx | GPL-3.0，Copyright (C) 2026 | LICENSE-games-5-GPL-3.0.txt |
| lelele-game-games-5-main/hunt | highwindmx | MIT，Copyright (c) 2026 | LICENSE-games-5-hunt-MIT.txt |
| lelele-game-games-6-main（games） | Saurabh Singh | MIT，Copyright (c) 2026 | LICENSE-games-6-MIT.txt |

lelele-game-games-4-main 无任何 LICENSE 文件，其 README 声明为街机原作的「Fan recreations」，
原作商标归 Atari / Namco / Taito / Midway / Williams 等各自权利人所有，故整仓不纳入投稿。

## 许可冲突说明

games-5 根目录为 GPL-3.0，但 hunt/ 子目录自带 MIT LICENSE，两者作者同为 highwindmx。
本整理不对任何许可做删改或重新授权：两份原文都保留，hunt 相关产物按子目录 MIT 随附，
其余 games-5 产物按 GPL-3.0 随附，并在游戏内声明中明示适用许可。GPL-3.0 作品仍以 GPL-3.0
发布，不额外施加限制；平台「通用万能协议」仅为展示层的法律协议挂载，不改变游戏代码许可。

## 第三方素材与库

- games-5/warship 本地 vendored Phaser 3 与 Three.js（MIT），库文件随游戏目录原样保留。
- games-5/hunt/web/lib/three.module.js 为本地 vendored Three.js r160（MIT）；其中
  `discourse.threejs.org` 仅是 `console.warn` 的弃用指引文本，不产生网络请求。
- games-5/hunt/docs/ 为 Godot 4 的 HTML5 导出产物，含 `index.js`、`index.wasm`、`index.pck`
  与 audio worklet；`godotengine.org`、`developer.mozilla.org` 仅出现在导出运行时的
  版权头与 JSDoc 注释中，不产生网络请求。
- games-1/slingstorm.html 内嵌 Matter.js（MIT，`http://brm.io/matter-js/` 为源码注释中的
  来源标注），本地内联、无外部加载。
- 上述库均为各自开源许可，来源与许可说明按守则 3.5 随游戏保留，未改动库代码。
- games-1/star-cluster-arena/THIRD-PARTY-NOTICES.md 列明 Electron（MIT）、Chromium（BSD 等）、
  Node.js（MIT）、ws（MIT）、Caddy（Apache-2.0）；该项目需构建与 Node 服务端，未纳入投稿。
- games-6 约 133 款游戏依赖公网 CDN 的 Phaser / Three.js / GSAP / Google Fonts 等外部资源，
  仓库内无本地引擎副本；按守则 2.3 链接安全、2.3 隐私保护与 3.5 第三方素材注明来源，
  无法在本地完成合规本地化的作品整仓不纳入投稿。

## 法律协议

按守则 4.6 默认②，三类协议（用户协议 / 隐私政策 / 服务条款）由平台在游戏详情页
自动挂载通用万能协议，本次不在游戏内内嵌协议页面，仅在投稿审核清单中登记。
"""

# 运行时外部资源特征（命中即视为存在外部依赖，守则 2.3 / 3.5）
EXTERNAL_MARKERS = (
    "cdn.jsdelivr", "cdnjs.cloudflare", "unpkg.com", "ajax.googleapis",
    "apis.google.com", "fonts.googleapis", "fonts.gstatic", "googletagmanager",
    "firebaseapp", "images.unsplash", "s3.ap-", "s3.amazonaws", "chaoswale",
    "chaotix.ai", "i.ibb.co", "<iframe", "api.github.com",
)
# 明确商业商标 / 商业游戏复刻（守则 3.1 / 3.4）
TRADEMARK_WORDS = (
    "mario", "pac-man", "pacman", "tetris", "candy crush", "cut the rope",
    "angry birds", "minecraft", "crossy road", "doodle jump", "wordle",
    "flappy", "level devil", "that level again", "space invaders",
    "sports heads", "fruit ninja", "subway surfers", "among us", "pokemon",
)
# 注册表模板残留的 title（games-6 共 121 款内容错配）
TEMPLATE_TITLES = {
    "jet fighter - portrait", "kaiju krush", "words of wonder", "pikoo game",
    "chaotix ai", "game", "tunnel rush – proper version", "tunnel rush - proper version",
    "veggie merge – chaos edition", "veggie merge - chaos edition",
}

# 守则 2.1 赌博 / 博彩 / 赌场题材（games-1）
GAMBLING_HTML = (
    "blackjack-table.html", "river-holdem.html", "charm-reels.html",
    "solitaire-classic.html", "dice-delver.html",
)

# 战斗 / 射击 / 惊悚等题材关键词，用于建议适龄分级（投稿前仍需人工复核）
MATURE_WORDS = (
    "shooter", "arena", "horde", "monster", "tank", "war", "battle", "gun",
    "hunt", "shadow", "dungeon", "detective", "midnight", "abyss", "pathogen",
    "dojo", "duel", "claw", "bomb", "storm", "vanguard", "tactical", "siege",
)

AGREEMENTS = {
    "用户协议": "平台通用万能协议（守则 4.6 默认②，详情页自动挂载）",
    "隐私政策": "平台通用万能协议（守则 4.6 默认②，详情页自动挂载）",
    "服务条款": "平台通用万能协议（守则 4.6 默认②，详情页自动挂载）",
    "内嵌协议页面": "否",
}

TEXT_SUFFIXES = {".html", ".htm", ".js", ".mjs", ".json", ".css", ".txt", ".md", ".svg"}


def read_text(path: Path) -> str:
    """按 UTF-8 读取并保留任意原始字节，避免破坏非 UTF-8 文件。"""
    return path.read_text(encoding="utf-8", errors="surrogateescape")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="surrogateescape")


def sha256_short(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def rel(path: Path, base: Path) -> str:
    return str(path.relative_to(base))


def title_of(path: Path) -> str:
    if not path.is_file():
        return ""
    m = re.search(r"<title[^>]*>(.*?)</title>", read_text(path), re.I | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def name_matches_title(name: str, title: str) -> bool:
    if not title or title.lower() in TEMPLATE_TITLES:
        return False
    words = [w.lower() for w in re.findall(r"[A-Za-z0-9]+", name) if len(w) >= 3]
    low = title.lower()
    return any(w in low for w in words)


def external_markers_in(directory: Path) -> list[str]:
    found: set[str] = set()
    for p in directory.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = read_text(p)
        except (OSError, UnicodeError):
            continue
        low = text.lower()
        for marker in EXTERNAL_MARKERS:
            if marker in low:
                found.add(marker)
    return sorted(found)


def suggested_age(name: str) -> tuple[str, str]:
    low = name.lower()
    if any(w in low for w in MATURE_WORDS):
        return "12岁以上", "含战斗/对抗题材，投稿前请人工复核；如含轻微刺激内容需标注家长指引"
    return "全年龄", "益智/休闲/经营题材，投稿前请人工复核"


def entry(key: str, **kw) -> dict:
    d = {"key": key}
    d.update(kw)
    return d


# ---------------------------------------------------------------------------
# build：只读扫描 + 逐款判定
# ---------------------------------------------------------------------------

def build() -> dict:
    tiers = json.loads((S1 / "GAME_TIERS.json").read_text(encoding="utf-8"))["tiers"]
    registry = json.loads((S6 / "games" / "registry.json").read_text(encoding="utf-8"))

    keep: list[dict] = []
    remove: list[dict] = []

    # --- 收集到的游戏/tetris.html：唯一既无署名又无许可的现存文件 ---
    tetris = OUT / "tetris.html"
    age, note = suggested_age("tetris")
    keep.append(entry(
        "tetris", name="Tetris（原始收集文件）", unit="file",
        src=str(tetris), dst=str(tetris), entry_files=[str(tetris)],
        author="未知作者", author_mode="unknown",
        license="无（未找到 LICENSE / 署名信息）", license_text="", source="原「收集到的游戏」目录",
        age=age, age_note=note, reason="无署名无许可，按守则 3.1 标注授权待确认、暂不建议投稿，先保留待补授权",
        rule="守则 3.1 / 4.2", risk="授权待确认",
    ))

    # --- games-1：SSS/SS/S/A 为优质准入，赌博题材与 C/E 级剔除 ---
    selected = []
    for tier in ("SSS", "SS", "S", "A"):
        for filename in tiers.get(tier, []):
            if filename in GAMBLING_HTML:
                continue
            selected.append((tier, filename))
    for tier, filename in selected:
        src = S1 / filename
        if not src.is_file():
            print(f"[build] 警告：games-1 缺失 {filename}", file=sys.stderr)
            continue
        age, note = suggested_age(filename)
        keep.append(entry(
            f"g1:{filename}", name=filename.removesuffix(".html"), unit="file",
            src=str(src), dst=str(OUT / filename), entry_files=[str(OUT / filename)],
            author="wangzifan396-wzf", author_mode="original",
            license="MIT License · Copyright (c) 2026 wangzifan396-wzf",
            license_text=MIT_1,
            source="https://github.com/wangzifan396-wzf/mini-browser-games",
            age=age, age_note=note,
            tier=tier,
            reason=f"GAME_TIERS.json 评级 {tier}（优质准入）；单文件自包含、零外链、零服务端；MIT 授权明确",
            rule="守则 1.2 / 2.3 / 3.1；RATING_STANDARD.md A 级准入线",
            risk="无",
        ))

    removed_g1: set[str] = set(GAMBLING_HTML)
    removed_g1.update(tiers.get("C", []))
    removed_g1.update(tiers.get("E", []))
    for filename in sorted(removed_g1):
        src = S1 / filename
        if not src.is_file():
            continue
        is_gambling = filename in GAMBLING_HTML
        remove.append(entry(
            f"g1-rm:{filename}", name=filename, src=str(src),
            dst=str(TRASH / S1.name / filename),
            reason=("守则 2.1 赌博/博彩/赌场题材（纯虚拟筹码亦按题材从严剔除）" if is_gambling
                    else "GAME_TIERS.json 评为 C/E 级：原型或历史废案，不满足优质准入"),
            rule="守则 2.1 / 2.3；GAME_TIERS.json",
        ))

    # games-1 中需构建 / 需服务端 / 非游戏内容的子目录与卡片页
    for sub in ("star-cluster-arena", "starforge-nexus", "minesweeper-c",
                "promo-video", "scripts", "docs", "development", "index.html"):
        src = S1 / sub
        if not src.exists():
            continue
        remove.append(entry(
            f"g1-rm-dir:{sub}", name=sub, src=str(src),
            dst=str(TRASH / S1.name / sub),
            reason=("卡片导航页，用户明确不要卡片页" if sub == "index.html"
                    else "需构建 / Node 服务端 / Electron 桌面 / C 源码 / 文档视频脚本，非纯前端静态游戏"),
            rule="守则 1.2 / 2.3；用户要求不生成卡片页",
        ))

    # --- games-3：整仓剔除（Express + ws 权威服务端） ---
    remove.append(entry(
        "g3-all", name=S3.name, src=str(S3), dst=str(TRASH / S3.name),
        reason="5 款游戏均含 server/index.js（Express + ws / Socket.IO），客户端必须连 WebSocket 才能运行，纯静态托管只能打开空壳",
        rule="守则 1.2（不接收带服务端逻辑、需服务器环境启动的项目）",
    ))

    # --- games-4：整仓剔除（无许可 + 商业街机商标复刻） ---
    remove.append(entry(
        "g4-all", name=S4.name, src=str(S4), dst=str(TRASH / S4.name),
        reason="无任何 LICENSE；README 自述为 Atari / Namco / Taito / Midway / Williams 街机原作的 Fan recreations，原作商标归各自权利人",
        rule="守则 2.1 / 3.1 / 3.4 / 3.5",
    ))

    # --- games-5：GPL-3.0，六款游戏目录整体保留（排除需构建的 Godot 工程与 Node 测试脚本） ---
    g5_units = {
        "gravity": ["index.html"],
        "boids": ["index.html"],
        "magnetic": ["index.html"],
        "racecar": ["index.html"],
        "warship": ["25D/index.html", "3D/index.html"],
        "hunt": ["web/index.html", "docs/index.html"],
    }
    g5_exclude = {
        "warship": ("archive", "smoke.js"),
        "hunt": ("hunt", "bow", "bullet", "project.godot", ".godot", ".venv"),
    }
    for unit_name, entries in g5_units.items():
        src_dir = S5 / unit_name
        if not src_dir.is_dir():
            print(f"[build] 警告：games-5 缺失 {unit_name}", file=sys.stderr)
            continue
        dst_dir = OUT / unit_name
        existing = [e for e in entries if (src_dir / e).is_file()]
        age, note = suggested_age(unit_name)
        is_hunt = unit_name == "hunt"
        lic = ("MIT License · Copyright (c) 2026 highwindmx" if is_hunt
               else "GNU GPL v3.0 · Copyright (C) 2026 highwindmx")
        keep.append(entry(
            f"g5:{unit_name}", name=unit_name, unit="dir",
            src=str(src_dir), dst=str(dst_dir),
            exclude=list(g5_exclude.get(unit_name, ())),
            entry_files=[str(dst_dir / e) for e in existing],
            author="highwindmx", author_mode="original",
            license=lic, license_text=(MIT_5 if is_hunt else GPL_5),
            source="https://github.com/highwindmx/HTML-Games",
            age=age, age_note=note,
            reason=("零构建、本地 vendored 库、无外部 CDN；hunt 按子目录 MIT 随附，与根 GPL 两份许可都保留"
                    if is_hunt else
                    "零构建、纯静态可运行、无外部 CDN；GPL-3.0 授权明确，源码与许可全文随附"),
            rule="守则 1.2 / 2.3 / 3.1 / 3.5；GPL-3.0 第 4、5 条",
            risk=("hunt 子目录 MIT 与根 GPL-3.0 并存，清单已注明，不声称改用其他许可" if is_hunt else "无"),
        ))
        for ex in g5_exclude.get(unit_name, ()):
            p = src_dir / ex
            if p.exists():
                remove.append(entry(
                    f"g5-rm:{unit_name}/{ex}", name=f"{unit_name}/{ex}",
                    src=str(p), dst=str(TRASH / S5.name / unit_name / ex),
                    reason="Godot 工程源码 / 早期原型 / Node 冒烟测试脚本，需构建或非纯前端产物，不随投稿包上传",
                    rule="守则 1.2 / 2.3",
                ))

    # --- games-6：逐款校验 path/title/外链/商标，无法通过者整款剔除 ---
    g6_categories: dict[str, list[dict]] = {}
    for g in registry["games"]:
        slug, name, path_s = g["slug"], g["name"], g["path"]
        game_dir = (S6 / path_s).parent
        idx = S6 / path_s
        problems: list[str] = []

        if not idx.is_file():
            problems.append("registry.path 指向的 index.html 不存在")
        title = title_of(idx) if idx.is_file() else ""
        if idx.is_file() and not name_matches_title(name, title):
            problems.append(f"页面 title「{title}」与注册表名称「{name}」错配")

        if any(w in name.lower() for w in TRADEMARK_WORDS):
            problems.append("复刻第三方商业游戏名称/商标")

        ext = external_markers_in(game_dir) if game_dir.is_dir() else []
        if ext:
            problems.append("存在外部 CDN / 第三方资源或追踪脚本：" + "、".join(ext))

        if game_dir.is_dir() and not any(game_dir.rglob("*.js")):
            problems.append("目录内无游戏脚本，疑似空壳")

        record = {
            "slug": slug, "name": name, "category": g["category"],
            "path": path_s, "tech": g.get("tech", ""), "title": title,
            "external": ext, "problems": problems,
        }
        g6_categories.setdefault(g["category"], []).append(record)

        if problems:
            remove.append(entry(
                f"g6-rm:{slug}", name=name, src=str(game_dir),
                dst=str(TRASH / S6.name / rel(game_dir, S6)),
                reason="；".join(problems),
                rule="守则 2.3（可运行性/链接安全/隐私/代码安全）、3.1、3.4、3.5",
            ))
            continue

        age, note = suggested_age(name)
        keep.append(entry(
            f"g6:{slug}", name=name, unit="dir",
            src=str(game_dir), dst=str(OUT / "games-6" / slug),
            entry_files=[str(OUT / "games-6" / slug / "index.html")],
            author="Saurabh Singh", author_mode="original",
            license="MIT License · Copyright (c) 2026 Saurabh Singh",
            license_text=MIT_6, source="https://github.com/sausi-7/games",
            age=age, age_note=note,
            reason="registry.path 存在、title 与名称一致、无第三方商标、目录内零外部资源依赖、游戏脚本齐全",
            rule="守则 1.2 / 2.3 / 3.1",
            risk="无",
        ))

    # games-6 仓库级非游戏内容（卡片页、站点、脚本、assets）整体移入准备删除
    for sub in ("index.html", "site", "scripts"):
        src = S6 / sub
        if not src.exists():
            continue
        remove.append(entry(
            f"g6-rm-root:{sub}", name=f"{S6.name}/{sub}", src=str(src),
            dst=str(TRASH / S6.name / sub),
            reason="卡片导航页 / 站点 / 构建脚本，非独立游戏单元；用户明确不要卡片页",
            rule="用户要求每款独立、不要卡片页；守则 1.2",
        ))

    # 其余仓库的元文件保留原处（版权依据），仅复制到 _版权与来源/
    data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "rules_version": "5.0.0",
        "rules_url": "https://game.leleleling.site/game_rules",
        "output_dir": str(OUT),
        "trash_dir": str(TRASH),
        "agreements": AGREEMENTS,
        "license_copies": {k: str(NOTICE_DIR / k) for k in LICENSE_COPIES},
        "games6_audit": {
            "total": len(registry["games"]),
            "by_category": {k: len(v) for k, v in g6_categories.items()},
            "records": [r for v in g6_categories.values() for r in v],
        },
        "keep": keep,
        "remove": remove,
        "attribution_files": sorted({p for k in keep for p in k["entry_files"]}),
        "summary": {
            "keep_total": len(keep),
            "keep_games1": sum(1 for k in keep if k["key"].startswith("g1:")),
            "keep_games5": sum(1 for k in keep if k["key"].startswith("g5:")),
            "keep_games6": sum(1 for k in keep if k["key"].startswith("g6:")),
            "keep_other": 1,
            "remove_total": len(remove),
            "attribution_file_total": len({p for k in keep for p in k["entry_files"]}),
        },
    }
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[build] 已生成 {MANIFEST}")
    print(f"[build] 入选 {data['summary']['keep_total']} 款"
          f"（games-1 {data['summary']['keep_games1']} / games-5 {data['summary']['keep_games5']}"
          f" / games-6 {data['summary']['keep_games6']} / 其他 {data['summary']['keep_other']}），"
          f"剔除 {len(remove)} 项，需署名文件 {data['summary']['attribution_file_total']} 个")
    return data


# ---------------------------------------------------------------------------
# 署名注入
# ---------------------------------------------------------------------------

def build_comment(item: dict) -> str:
    author = item["author"]
    license_line = item["license"]
    source = item["source"]
    age = item["age"]
    extra = item.get("risk", "无")
    lines = [
        ATTR_BEGIN,
        "  了了了游投稿精选 · 作者与版权信息（请勿删除）",
        f"  作品：{item['name']}",
        f"  作者：{author}",
        f"  许可：{license_line}",
        f"  来源：{source}",
        f"  适龄分级（建议，投稿前需人工复核）：{age}",
        f"  法律协议：用户协议 / 隐私政策 / 服务条款均使用平台通用万能协议（守则 4.6 默认②）",
        f"  风险标注：{extra}",
        "  说明：本文件为原作品的完整副本，未改动玩法、样式与交互；原许可与版权声明均保留。",
    ]
    if item.get("license_text"):
        full = item["license_text"].replace("-->", "-- >")
        lines.append("  ---- 随附许可全文开始 ----")
        lines.extend("  " + ln for ln in full.splitlines())
        lines.append("  ---- 随附许可全文结束 ----")
    lines.append(ATTR_END)
    return "\n".join(lines) + "\n"


def build_visible(item: dict) -> str:
    label = f"作者：{item['author']} · {item['license'].split(' · ')[0]}"
    return (
        DIV_BEGIN
        + f'\n<div data-lelele-attribution style="position:fixed;right:6px;bottom:4px;'
          f'z-index:2147483647;pointer-events:none;opacity:.38;'
          f'font:10px/1.2 system-ui,-apple-system,sans-serif;color:#777;'
          f'text-shadow:0 1px 1px #fff;letter-spacing:.02em">{label}</div>\n'
    )


def inject(path: Path, item: dict) -> str:
    if not path.is_file():
        return "missing"
    text = read_text(path)
    if ATTR_BEGIN in text:
        return "already"
    before_hash = sha256_short(path)
    comment = build_comment(item)
    visible = build_visible(item)

    head = re.search(r"</head\s*>", text, re.I)
    if head:
        text = text[:head.start()] + comment + text[head.start():]
    else:
        html = re.search(r"<html[^>]*>", text, re.I)
        if html:
            text = text[:html.end()] + "\n" + comment + text[html.end():]
        else:
            text = comment + text

    body = re.search(r"</body\s*>", text, re.I)
    if body:
        text = text[:body.start()] + visible + text[body.start():]
    else:
        text = text + "\n" + visible

    write_text(path, text)
    if ATTR_BEGIN not in read_text(path):
        raise RuntimeError(f"署名注入校验失败：{path}")
    return f"injected (sha256 {before_hash} -> {sha256_short(path)})"


# ---------------------------------------------------------------------------
# apply：复制 / 移动 / 注入 / 生成清单
# ---------------------------------------------------------------------------

def copy_unit(src: Path, dst: Path, exclude: tuple[str, ...], unit: str, dry: bool) -> str:
    if src == dst:
        return "in-place"
    if dst.exists():
        return "exists"
    if dry:
        return "dry-copy"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if unit == "file":
        shutil.copy2(src, dst)
    else:
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*exclude) if exclude else None)
    return "copied"


def move_unit(src: Path, dst: Path, dry: bool) -> str:
    # 先判断目标，保证幂等重跑时「已移动」不会被误报成丢失
    if dst.exists():
        return "exists"
    if not src.exists():
        return "gone"
    if dry:
        return "dry-move"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return "moved"


def apply(data: dict, dry: bool = False) -> dict:
    stats = {"copied": 0, "moved": 0, "injected": 0, "skipped": 0, "errors": []}

    if not dry:
        OUT.mkdir(parents=True, exist_ok=True)
        TRASH.mkdir(parents=True, exist_ok=True)
        NOTICE_DIR.mkdir(parents=True, exist_ok=True)
        for filename, content in LICENSE_COPIES.items():
            write_text(NOTICE_DIR / filename, content)
        write_text(NOTICE_DIR / "THIRD-PARTY-NOTICES.md", THIRD_PARTY_NOTICES)

    for item in data["keep"]:
        src, dst = Path(item["src"]), Path(item["dst"])
        result = copy_unit(src, dst, tuple(item.get("exclude", ())), item["unit"], dry)
        if result == "copied":
            stats["copied"] += 1
        else:
            stats["skipped"] += 1
        if not dry:
            for entry_path in item["entry_files"]:
                r = inject(Path(entry_path), item)
                if r.startswith("injected"):
                    stats["injected"] += 1
                elif r == "missing":
                    stats["errors"].append(f"缺少入口文件：{entry_path}")
                elif r == "already":
                    stats["injected"] += 1  # 幂等重跑：已注入，计入完成
                else:
                    stats["skipped"] += 1

    # 剔除项按路径深度从深到浅处理，避免父目录先被移走导致子项丢失
    ordered = sorted(data["remove"], key=lambda x: len(Path(x["src"]).parts), reverse=True)
    for item in ordered:
        r = move_unit(Path(item["src"]), Path(item["dst"]), dry)
        if r == "moved":
            stats["moved"] += 1
        elif r == "gone":
            stats["errors"].append(f"剔除项已不存在：{item['src']}")
        else:
            stats["skipped"] += 1

    if not dry:
        write_report(data)
    print(f"[apply] 复制 {stats['copied']} / 移动 {stats['moved']} / 注入署名 {stats['injected']}"
          f" / 跳过 {stats['skipped']} / 问题 {len(stats['errors'])}")
    for e in stats["errors"][:20]:
        print(f"[apply] ! {e}", file=sys.stderr)
    return stats


# ---------------------------------------------------------------------------
# 审核清单（纯文本，非导航页）
# ---------------------------------------------------------------------------

def write_report(data: dict) -> None:
    s = data["summary"]
    lines = [
        "# 了了了游投稿审核清单",
        "",
        f"- 生成时间：{data['generated_at']}",
        f"- 依据规则：[了了了游游戏守则 {data['rules_version']}]({data['rules_url']})（2026-11-15 生效）",
        f"- 入选输出目录：`{data['output_dir']}`（每款游戏独立，无卡片导航页）",
        f"- 剔除暂存目录：`{data['trash_dir']}`（只移动、不物理删除，可完整回滚）",
        f"- 许可原文副本：`{NOTICE_DIR}`",
        f"- 入选合计：**{s['keep_total']}** 款（games-1 {s['keep_games1']} / games-5 {s['keep_games5']}"
        f" / games-6 {s['keep_games6']} / 其他 {s['keep_other']}）；剔除合计：**{s['remove_total']}** 项",
        f"- 需在代码内显示作者信息的文件：**{s['attribution_file_total']}** 个（见文末清单）",
        "",
        "## 三类法律协议登记（守则 4.6）",
        "",
        "| 协议 | 登记方式 |",
        "|---|---|",
    ]
    for k, v in data["agreements"].items():
        lines.append(f"| {k} | {v} |")
    lines += [
        "",
        "> 按守则 4.6 默认②，代码形式投稿未自带协议页面时由平台在详情页自动挂载通用万能协议；",
        "> 本次不在游戏内内嵌协议页面、不改动游戏逻辑。协议模板基于 Apache-2.0，若日后改为自带协议，",
        "> 须在游戏内保留「本法律条款由了了了游提供」声明。",
        "",
        "## 适龄分级说明（守则 2.2）",
        "",
        "本清单按题材关键词给出**建议分级**，未经逐款人工完整试玩，投稿前须如实复核并在投稿表单中确认；",
        "含轻微刺激或需一定心理承受能力的内容须另行标注「家长指引」。故意虚报分级平台有权下架。",
        "",
        "## 入选游戏逐款记录",
        "",
        "| # | 游戏 | 作者 | 许可 | 来源 | 建议分级 | 输出路径 | 判定依据 |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for i, k in enumerate(data["keep"], 1):
        lines.append(
            f"| {i} | {k['name']} | {k['author']} | {k['license']} | {k['source']} | "
            f"{k['age']} | `{k['dst']}` | {k['reason']}（{k['rule']}） |"
        )
    lines += [
        "",
        "### 风险标注",
        "",
    ]
    for k in data["keep"]:
        if k.get("risk") and k["risk"] != "无":
            lines.append(f"- **{k['name']}**：{k['risk']}")
    lines += [
        "",
        "## 剔除项逐款记录（均已移入 `准备删除/`）",
        "",
        "| # | 名称 | 判定依据 | 适用条款 | 暂存路径 |",
        "|---:|---|---|---|---|",
    ]
    for i, r in enumerate(data["remove"], 1):
        lines.append(f"| {i} | {r['name']} | {r['reason']} | {r['rule']} | `{r['dst']}` |")
    lines += [
        "",
        "## games-6 逐款审计明细",
        "",
        f"registry.json 共 {data['games6_audit']['total']} 款；分类计数："
        + "、".join(f"{k} {v}" for k, v in data["games6_audit"]["by_category"].items()),
        "",
        "| slug | 名称 | 实际 title | 外部资源特征 | 判定 |",
        "|---|---|---|---|---|",
    ]
    for r in data["games6_audit"]["records"]:
        verdict = "剔除：" + "；".join(r["problems"]) if r["problems"] else "入选"
        lines.append(
            f"| {r['slug']} | {r['name']} | {r['title']} | "
            f"{'、'.join(r['external']) or '无'} | {verdict} |"
        )
    lines += [
        "",
        "## 需要写入作者信息的文件（完整清单）",
        "",
        "下列文件均已在 `<head>` 注入版权/许可/来源注释块，并在 `</body>` 前注入一处低调可见署名",
        "（`pointer-events:none`，不拦截操作、不遮挡界面、不引入外部资源）。注入使用唯一标记保证幂等。",
        "",
    ]
    for p in data["attribution_files"]:
        lines.append(f"- `{p}`")
    lines += [
        "",
        "## 复核结论见 `python3 整理工具.py verify` 输出",
        "",
    ]
    write_text(REPORT, "\n".join(lines))
    print(f"[apply] 已生成 {REPORT}")


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------

def verify(data: dict) -> bool:
    ok = True
    def check(cond: bool, msg: str) -> None:
        nonlocal ok
        print(f"[verify] {'OK  ' if cond else 'FAIL'} {msg}")
        if not cond:
            ok = False

    missing_dst = [k["dst"] for k in data["keep"] if not Path(k["dst"]).exists()]
    check(not missing_dst, f"入选单元全部存在（{len(data['keep'])} 项，缺失 {len(missing_dst)}）")

    no_attr, no_visible, wrong_author = [], [], []
    for p in data["attribution_files"]:
        f = Path(p)
        if not f.is_file():
            no_attr.append(p)
            continue
        t = read_text(f)
        if ATTR_BEGIN not in t or ATTR_END not in t:
            no_attr.append(p)
        if DIV_BEGIN not in t:
            no_visible.append(p)
    check(not no_attr, f"代码内版权署名齐全（{len(data['attribution_files'])} 个文件，缺失 {len(no_attr)}）")
    check(not no_visible, f"可见署名条齐全（缺失 {len(no_visible)}）")

    for k in data["keep"]:
        for p in k["entry_files"]:
            f = Path(p)
            if f.is_file() and k["author"] not in read_text(f):
                wrong_author.append(p)
    check(not wrong_author, f"作者名称逐款正确（异常 {len(wrong_author)} 个）")
    unknown = [k["name"] for k in data["keep"] if k.get("author_mode") == "unknown"]
    check(unknown == ["Tetris（原始收集文件）"], f"「未知作者」仅用于无署名无许可文件（{unknown}）")

    for filename in data["license_copies"]:
        check((NOTICE_DIR / filename).is_file(), f"许可副本：{filename}")
    check((NOTICE_DIR / "THIRD-PARTY-NOTICES.md").is_file(), "第三方声明文件")

    # 入选集内不得存在运行时外部依赖
    offenders: list[str] = []
    for p in OUT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".html", ".htm", ".js", ".json", ".css"}:
            continue
        if NOTICE_DIR in p.parents:
            continue
        low = read_text(p).lower()
        for marker in EXTERNAL_MARKERS:
            if marker in low:
                offenders.append(f"{p.relative_to(ROOT)} -> {marker}")
                break
    check(not offenders, f"入选集零外部依赖（命中 {len(offenders)}）")
    for o in offenders[:15]:
        print(f"         {o}")

    # 通用域名白名单：允许许可原文、来源超链接与 SVG 命名空间，其余外部域名一律告警
    # 允许：许可全文 / 来源超链接 / SVG 命名空间 / vendored 库内注释与提示字符串。
    # 后者已逐处核实为注释或 console.warn 文本，不产生网络请求，且按守则 3.5 须保留来源。
    allowed_hosts = {
        "www.w3.org", "github.com", "wangzifan396-wzf.github.io", "schema.org",
        "tetris.fandom.com", "free-tex-packer.com", "fsf.org", "www.gnu.org",
        "phaser.io", "threejs.org", "localhost", "127.0.0.1",
        "godotengine.org", "developer.mozilla.org", "brm.io", "discourse.threejs.org",
    }
    url_re = re.compile(r"https?://([A-Za-z0-9._-]+)", re.I)
    bad_hosts: dict[str, int] = {}
    malicious = re.compile(r"(coinhive|cryptonight|stratum\+tcp|webminer|minerd)", re.I)
    mal_hits: list[str] = []
    for p in OUT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".html", ".htm", ".js", ".json", ".css"}:
            continue
        if NOTICE_DIR in p.parents:
            continue
        text = read_text(p)
        for host in url_re.findall(text):
            if host.lower() not in allowed_hosts:
                bad_hosts[host.lower()] = bad_hosts.get(host.lower(), 0) + 1
        if p.suffix.lower() in {".html", ".htm", ".js"} and malicious.search(text):
            mal_hits.append(str(p.relative_to(ROOT)))
    check(not bad_hosts, f"入选集无白名单外域名（命中 {sum(bad_hosts.values())} 处）")
    for h, c in sorted(bad_hosts.items(), key=lambda x: -x[1])[:15]:
        print(f"         {h}: {c}")
    check(not mal_hits, f"无挖矿 / 恶意脚本特征（命中 {len(mal_hits)}）")

    # 注入位置：注释块在 </head> 前，可见署名条在 </body> 前且不落入 head
    misplaced = []
    for p in data["attribution_files"]:
        f = Path(p)
        if not f.is_file():
            continue
        t = read_text(f)
        if ATTR_BEGIN not in t or DIV_BEGIN not in t:
            continue
        head = re.search(r"</head\s*>", t, re.I)
        body = re.search(r"</body\s*>", t, re.I)
        if head and not (0 <= t.index(ATTR_BEGIN) < head.start()):
            misplaced.append(p)
        if body and not ((head.end() if head else 0) <= t.index(DIV_BEGIN) < body.start()):
            misplaced.append(p)
    check(not misplaced, f"署名注入位置正确、未破坏 HTML 结构（异常 {len(set(misplaced))}）")

    # 剔除项应已离开原位、落到准备删除
    missing = [r["src"] for r in data["remove"] if Path(r["src"]).exists() and not Path(r["dst"]).exists()]
    check(not missing, f"剔除项已全部移入 准备删除/（残留 {len(missing)}）")

    check(MANIFEST.is_file() and REPORT.is_file(), "审核清单文件齐备")
    print(f"[verify] 结论：{'全部通过' if ok else '存在问题，请按上方 FAIL 项处理'}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="了了了游投稿精选整理工具")
    ap.add_argument("command", choices=("build", "apply", "verify"))
    ap.add_argument("--dry-run", action="store_true", help="apply 只打印计划动作，不改动文件")
    args = ap.parse_args()

    if args.command == "build":
        build()
        return 0
    if not MANIFEST.is_file():
        print("请先执行：python3 整理工具.py build", file=sys.stderr)
        return 2
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if args.command == "apply":
        apply(data, dry=args.dry_run)
        return 0
    return 0 if verify(data) else 1


if __name__ == "__main__":
    sys.exit(main())
