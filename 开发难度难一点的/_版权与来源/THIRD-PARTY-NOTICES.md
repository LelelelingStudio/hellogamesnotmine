# 第三方许可与素材声明

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
