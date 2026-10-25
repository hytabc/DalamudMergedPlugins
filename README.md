# Dalamud 合并插件仓库

把 **50 个第三方 Dalamud 插件仓库**抓取、去重、合并成的单一仓库。
以后在 Dalamud 里只需要添加这一个链接，不用再维护一长串仓库地址。

- 最近更新：2026-10-25
- 源仓库：43 / 50 个可读取
- 原始插件条目：408 条 → 去重后 **206 个插件**
- 同名不同版本：71 组，共 327 条版本记录已完整归档

## 使用方法

Dalamud 设置 → 实验性 → 第三方插件仓库 → 添加以下地址：

```
https://raw.githubusercontent.com/hytabc/DalamudMergedPlugins/main/pluginmaster.json
```

（国内网络访问 raw.githubusercontent.com 不稳定时，可用镜像前缀，例如
`https://gh.atmoomen.top/https://raw.githubusercontent.com/hytabc/DalamudMergedPlugins/main/pluginmaster.json`）

## 去重规则

1. 以 Dalamud 的 `InternalName` 作为唯一标识，**不按显示名去重**——显示名相同但
   InternalName 不同的插件（如 `Splatoon` 与 `SplatoonX`）会各自保留。
2. 同一 `InternalName` 有多个版本时，主表只收录最优版本：下载链接可用 →
   `DalamudApiLevel` 更高 → 版本号更高 → 更新时间更新。
   （API 等级优先，是因为低于当前 Dalamud API 的版本无法加载。）
3. 未入选的版本**不会被丢弃**，全部原样保存在 `archive/variants.json`
   （327 条，含完整原始字段与来源仓库地址），
   `archive/multi-version.json` 是逐插件对比清单。

## 目录

| 文件 | 说明 |
| --- | --- |
| `pluginmaster.json` | Dalamud 读取的插件索引，206 个插件，每个一条 |
| `archive/variants.json` | 全部 327 条版本记录（含未入选版本） |
| `archive/multi-version.json` | 71 个多版本插件的逐项对比 |
| `archive/sources.json` | 每个源仓库的地址、解析后地址、抓取状态 |
| `archive/original-repos.json` | 合并前的原始仓库地址备份 |
| `archive/deadlinks.json` | 入选条目中下载链接不可用的清单（21 条） |
| `sources.txt` | **更新脚本的输入**，一行一个仓库地址 |
| `update.py` | 更新脚本，见下 |
| `update.bat` | Windows 双击运行入口（转调 `update.py`） |

## 如何更新

Windows 上直接双击 `update.bat`，或在命令行里：

```bash
python update.py                 # 抓取 + 合并 + 提交并推送
python update.py --no-push       # 只改本地文件
python update.py --from-dalamud  # 先从 Dalamud 配置重新导出 sources.txt
python update.py --no-fetch      # 复用 .cache 里的数据，只重算
python update.py --check-only    # 只校验下载链接
python update.py --jobs 24       # 提高并发
```

想让某个上游仓库参与合并，把它加到 `sources.txt` 再跑一次即可；
`--from-dalamud` 会把 Dalamud 里当前启用的第三方仓库整体重新导出。

## 关于版本归档

Dalamud 对同一个 `InternalName` 只会显示一个可安装项，因此同一插件的多个历史版本
无法同时出现在插件列表里。所以主表只放最优版本，其余版本完整留在
`archive/variants.json`；需要某个旧版本时，从该文件里取它的
`DownloadLinkInstall` 手动安装即可。

## 多版本插件（版本数最多的 20 个）

| 插件 | 版本数 | 主表选用 | 全部版本 |
| --- | --- | --- | --- |
| `AetheryteLinkInChat` | 6 | 7.5.1.4 | 7.5.1.4, 7.5.0.0, 7.3.1.41, 7.3.1.14, 7.3.0.0, 6.58.12.0 |
| `PandorasBox` | 6 | 1.6.4.16 | 1.6.4.16, 1.6.4.6, 1.6.4.3, 1.6.3.24, 1.6.3.18, 1.5.4.9 |
| `AutoRetainer` | 5 | 4.6.2.14 | 4.6.2.14, 4.6.1.2, 4.6.0.8, 4.2.6.3, 4.2.5.10 |
| `Lifestream` | 5 | 2.6.0.8 | 2.6.0.8, 2.6.0.5, 2.5.4.8, 2.5.3.3, 2.1.0.0 |
| `AutoHook` | 4 | 6.0.2.10 | 6.0.2.10, 6.0.0.12, 4.2.2.0, 3.0.4.2 |
| `BOCCHI` | 4 | 4.2.0.19 | 4.2.0.19, 3.3.4.0, 2.1.1.4, 0.69.1.12 |
| `BossMod` | 4 | 7.5.7.9 | 7.5.7.9, 7.5.7.4, 0.0.0.164, 0.0.0.122 |
| `LazyLoot` | 4 | 5.3.3.3 | 5.3.3.3, 5.3.2.5, 5.3.2.2, 5.2.0.5 |
| `LuckyStar` | 4 | 1.2.0.0 | 1.2.0.0, 1.1.0.0, 1.0.0.0, 0.0.0.21 |
| `Marketbuddy` | 4 | 0.2.4.2 | 0.2.4.2, 0.2.4.1, 0.2.3.0, 0.2.2.13 |
| `MidiBard2` | 4 | 3.2.5.6 | 3.2.5.6, 3.2.4.0, 2.5.5.0, 2.2.3.1 |
| `AntiAfkKick-Dalamud` | 3 | 2.1.0.12 | 2.1.0.12, 2.1.0.11, 2.1.0.5 |
| `BDTHPlugin` | 3 | 1.7.3 | 1.7.3, 1.6.3, 1.5.7.2 |
| `BossModReborn` | 3 | 7.5.7.2 | 7.5.7.2, 7.4.5.18, 7.3.5.27 |
| `DailyRoutines` | 3 | 2.2.5.1 | 2.2.5.1, 2.0.4.4, 1.9.3.3 |
| `FFLogsViewer` | 3 | 2.5.3.5 | 2.5.3.5, 2.4.1.0, 2.1.6.2 |
| `FuckAnimationLock` | 3 | 3.0.17.1 | 3.0.17.1, 3.0.14.6, 3.0.13.0 |
| `HuntTrainAssistant` | 3 | 1.0.4.8 | 1.0.4.8, 1.0.2.15, 1.0.0.8 |
| `IINACT` | 3 | 2.10.3.11 | 2.10.3.11, 2.5.1.0, 2.1.4.3 |
| `NecroLens` | 3 | 1.0.8.24 | 1.0.8.24, 1.0.8.12, 1.0.7.4 |

## 下载链接异常（21 条）

这些插件在**所有**源仓库里的下载地址都不可用，安装会失败，仅作索引保留：

| InternalName | 版本 | 状态 |
| --- | --- | --- |
| `Accountant` | 1.8.3.0 | HTTP403 |
| `AetherBox` | 1.0.0.13 | HTTP404 |
| `BetterTargetingSystemPvP` | 1.0.0.5 | HTTP404 |
| `Debugger` | 6.58.12.0 | HTTP404 |
| `DiscordIntegration` | 6.58.12.0 | HTTP404 |
| `FATEAutoSync` | 1.3.0.0 | HTTP404 |
| `FoodCheck` | 1.0.0.0 | HTTP404 |
| `FuckDalamudCN` | 2.0.0.10 | HTTP403 |
| `GrowUp` | 0.0.0.3 | HTTP404 |
| `HoardFarm` | 1.6.0.2 | EMPTY |
| `InstanceIDViewer` | 6.58.12.0 | HTTP404 |
| `LootMaster` | 1.0.0.6 | HTTP404 |
| `MacroChain-Ori` | 999.999.999.999 | HTTP404 |
| `MareSynchronos` | 0.9.43 | UNREACHABLE |
| `MaskedCarnivale` | 0.0.0.7 | EMPTY |
| `PFClassifier` | 1.2.30 | HTTP403 |
| `PFRadar` | 1.5.0.7 | HTTP403 |
| `PotatoFamine2` | 2.0.0.1 | HTTP404 |
| `SamplePlugin` | 0.0.0.8 | HTTP404 |
| `XIVSlothCombo` | 3.1.2.1 | HTTP404 |
| `XIVSlothComboX` | 3.3.2.5 | HTTP404 |

## 说明

- 本仓库只做**索引合并**，不托管任何插件本体；插件仍从原作者发布地址下载，版权归各作者。
- 插件兼容性看 `DalamudApiLevel`：当前分布 API 15: 132 / API 14: 8 / API 13: 2 / API 12: 4 / API 11: 5 / API 10: 5 / API 9: 36 / API 8: 2 / API 7: 4 / API 6: 4 / API 5: 2 / API 0: 2。
- 上游仓库更新不会自动同步，需要时手动运行 `update.py`。
