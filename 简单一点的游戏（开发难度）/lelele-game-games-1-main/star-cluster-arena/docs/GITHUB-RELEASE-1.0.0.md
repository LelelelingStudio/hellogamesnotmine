# 星团大作战 1.0.0 正式版

十模式单人 / 好友联机、Windows 安装与便携程序，以及可自部署的互联网房间服务。单人和服务器执行同一份原始玩法，保留 AI、事件、喂刺与各模式特色；独立单 HTML 历史版保持原状。

正式发布日期：2026-10-16，标签 `sca-v1.0.0`。本次将已交付的 1.0.0 构建正式发布，复用 10 月 3 日候选版的安装包 / ZIP，二进制与 SHA-256 不变，没有重新编译。发布前补做后台源码、规则和静态成品复核，不占用前台。`sca-v1.0.0-rc.1` 保留为历史预发布。

## 下载与开始

- **安装版**：`StarClusterArena-Setup-1.0.0-win-x64.exe`，向导内可选择安装目录，安装后从桌面 / 开始菜单启动。
- **便携版**：完整解压 `StarClusterArena-Portable-1.0.0-win-x64.zip`，双击目录中的 `StarClusterArena.exe`。不要单独复制 EXE；无需安装 Node.js。
- `SHA256SUMS.txt` 提供两份成品的校验值。构建未购买 Authenticode 签名，Windows 可能出现系统信誉提示。

```text
1E4EC4B7D06E9C10B2CA708A9CDF6CB0C4D26C2C8E9B81D9F0271DFAF597C305  StarClusterArena-Setup-1.0.0-win-x64.exe
7EE2B11FA5326B631D20B61BBC25146595AD8ED33F8A0B9E5E78C038CF743C20  StarClusterArena-Portable-1.0.0-win-x64.zip
```

## 1.0 玩法与改进

- 自由、团队、生存、大逃杀、闪电、孢子、霸屏、据点、巨行星、魔王十种模式；按原模式人数自动补 AI，例如 4 真人大逃杀配 96 AI。
- 修复房主阵亡后访客不能获胜、复活模式提前结束、魔王英雄超员，以及访客孢子回收规则不一致。
- 单人 Esc 暂停 / 继续，重开和离开有明确操作；失焦释放输入，暂停不消耗比赛时间。联机 Esc 打开菜单但不暂停服务器。
- 玩家首页、720p 可见开始按钮、个人中心、模式目标提示、阵亡观战、联机结算和本地星尘奖励。
- 同源材质 / 护盾 / 合球提示 / 镜头、程序生成声音和音量设置；稳定桌面进度路径、原子保存、备份和损坏恢复。
- 按需导出快照，减少重复复制；60Hz 玩法、20Hz 网络快照和画面帧率独立，不锁 60 FPS。
- 修复主页覆盖对局、启动器管道关闭后 EPIPE 日志错误框；Electron 44.5.1、收紧来源白名单。
- 新增互联网服务选择、房间码 / 邀请、私密房间和 HTTPS/WSS 部署配置。

## 联机方式

局域网从游戏界面创建房间，其他玩家自动发现并加入。异地需要所有人填写同一公网 HTTPS 服务，再分享房间码或邀请链接；**本项目没有附带正在运营的免费公共服务器**。

通常最多 8 真人，魔王合作最多 4 勇者，其余槽位由原模式 AI 补满。协议 `sca-v1` 不与旧 v4.0 客户端混房。公网容器配置尚未实际部署，不把 localhost / TLS 代理测试写成已上线。

## 验证记录与已知限制

**10 月 16 日后台复核**：源码检查 52 个关键文件 / 51 个脚本通过，`npm test` 198 / 198 通过；便携包版本为 1.0.0，45 个运行文件与当前运行源码逐字节一致，许可和运行时完整。没有启动 EXE 或占用前台，也没有重做帧率、真人试玩、安装或跨城验证。

**10 月 3 日历史验证**：十模式完整模拟长局及满真人后台压力门禁通过，物理 P95 为 1.812–10.271ms；便携 EXE 三轮九组流程回归通过。构建基线 `a7fec102fbf53a0f793f0399d55c985da1225c7b` 的 [Windows / Ubuntu CI](https://github.com/wangzifan396-wzf/mini-browser-games/actions/runs/37127687425) 已成功。这些压力、桌面和 CI 结果均保留原始日期与条件，不是 10 月 16 日重新执行。

本次已核对本地二进制 SHA-256 与 GitHub 候选资产 digest 一致。正式标签另包含发行文档调整；原 `CI-RESULTS.json` 保留 RC 标签与原提交，用作构建历史，不冒充新标签 CI。

- 历史源码本机 4K 全屏五分钟平均约 67 FPS，未稳定达到 120 FPS；不承诺所有硬件满帧。
- 最终包纯游戏前台长测按用户要求停止；实体跨城、全新机器完整安装 / 升级和多硬件验收仍待完成。
- 无代码签名、Steamworks AppID，也未通过 Steam 平台审核；平台好友、成就、云存档、Steam Deck / 手柄未接入。
- 自动化和后台压力不等于真人难度 / 平衡验收，也不等于公网容量或运营验收。

[完整发布说明](https://github.com/wangzifan396-wzf/mini-browser-games/blob/sca-v1.0.0/star-cluster-arena/docs/RELEASE-NOTES-1.0.0.md) · [测试记录与已知限制](https://github.com/wangzifan396-wzf/mini-browser-games/blob/sca-v1.0.0/star-cluster-arena/docs/QA-1.0.0.md) · [异地部署](https://github.com/wangzifan396-wzf/mini-browser-games/blob/sca-v1.0.0/star-cluster-arena/docs/INTERNET-MULTIPLAYER.md) · [Steam 发行前置清单](https://github.com/wangzifan396-wzf/mini-browser-games/blob/sca-v1.0.0/star-cluster-arena/docs/STEAM-RELEASE-CHECKLIST.md)

后续从 `star-cluster-arena/` 当前主分支升级 1.x；安装包和解压目录只是构建成品，不是第二份开发源码。旧工程版本保留在 Git 历史 / Releases。
