# Dalamud 合并插件仓库

把 **50 个第三方 Dalamud 插件仓库**抓取、去重、合并成的单一仓库。
以后在 Dalamud 里只需要添加这一个链接，不用再维护一长串仓库地址。

- 抓取时间：2026-10-25
- 成功读取的源仓库：43 个（50 个链接中）
- 原始插件条目：408 条 → 去重后 **206 个插件**
- 同名不同版本：71 组，共 326 条版本记录已完整归档

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
2. 同一 `InternalName` 有多个版本时，主表 `pluginmaster.json` 只收录 **206 条中的最优版本**：
   优先取下载链接可用 → 再比 `DalamudApiLevel` → 再比版本号 → 最后比更新时间。
   （API 等级优先是因为低于当前 Dalamud API 的版本无法加载。）
3. 未入选的版本**没有被丢弃**，全部原样保存在 `archive/variants.json`（326 条，
   含完整原始字段与来源仓库地址），`archive/multi-version.json` 是逐插件的对比清单。

## 目录

| 文件 | 说明 |
| --- | --- |
| `pluginmaster.json` | Dalamud 读取的插件索引，206 个插件，每个插件一条 |
| `archive/variants.json` | 全部 326 条版本记录（含未入选版本），带 `_source` / `_linkCheck` / `_selected` |
| `archive/multi-version.json` | 71 个多版本插件的逐项对比 |
| `archive/sources.json` | 每个源仓库的原始链接、解析后地址、抓到多少条 |
| `archive/original-repos.json` | 合并前的 50 个原始仓库地址备份 |
| `archive/deadlinks.json` | 入选条目中下载链接不可用的清单（21 条） |

## 关于版本归档

Dalamud 对同一个 `InternalName` 只会显示一个可安装项，因此同一插件的多个历史版本
无法同时出现在插件列表里。这里采取的方式是：主表只放最优版本，其余版本完整留在
`archive/variants.json`。如果你确实需要某个旧版本，可以在该文件里找到它的
`DownloadLinkInstall` 直接手动安装。

## 多版本插件（版本数最多的 20 个）

| 插件 | 版本数 | 主表选用 | 全部版本 |
| --- | --- | --- | --- |
| `PandorasBox` | 6 | 1.6.4.16 | 1.6.4.6, 1.6.4.3, 1.6.4.16, 1.6.3.24, 1.6.3.18, 1.5.4.9 |
| `AetheryteLinkInChat` | 6 | 7.5.1.4 | 7.5.1.4, 7.5.0.0, 7.3.1.41, 7.3.1.14, 7.3.0.0, 6.58.12.0 |
| `AutoRetainer` | 5 | 4.6.2.14 | 4.6.2.14, 4.6.1.2, 4.6.0.8, 4.2.6.3, 4.2.5.10 |
| `Lifestream` | 5 | 2.6.0.8 | 2.6.0.8, 2.6.0.5, 2.5.4.8, 2.5.3.3, 2.1.0.0 |
| `AutoHook` | 4 | 6.0.2.10 | 6.0.2.10, 6.0.0.12, 4.2.2.0, 3.0.4.2 |
| `LazyLoot` | 4 | 5.3.3.3 | 5.3.3.3, 5.3.2.5, 5.3.2.2, 5.2.0.5 |
| `Marketbuddy` | 4 | 0.2.4.2 | 0.2.4.2, 0.2.4.1, 0.2.3.0, 0.2.2.13 |
| `BOCCHI` | 4 | 4.2.0.19 | 4.2.0.19, 3.3.4.0, 2.1.1.4, 0.69.1.12 |
| `LuckyStar` | 4 | 1.2.0.0 | 1.2.0.0, 1.1.0.0, 1.0.0.0, 0.0.0.21 |
| `MidiBard2` | 4 | 3.2.5.6 | 3.2.5.6, 3.2.4.0, 2.5.5.0, 2.2.3.1 |
| `IINACT` | 3 | 2.10.3.11 | 2.5.1.0, 2.10.3.11, 2.1.4.3 |
| `YesAlready` | 3 | 1.15.7.4 | 1.6.3.3, 1.15.7.4, 1.14.14.0 |
| `Saucy` | 3 | 2.1.2.5 | 2.1.2.5, 1.6.0.0, 1.3.0.6 |
| `Radar` | 3 | 2.0.5.0 | 3.0.0.0, 2.0.5.0, 2.0.3.1 |
| `HuntTrainAssistant` | 3 | 1.0.4.8 | 1.0.4.8, 1.0.2.15, 1.0.0.8 |
| `AntiAfkKick-Dalamud` | 3 | 2.1.0.12 | 2.1.0.5, 2.1.0.12, 2.1.0.11 |
| `BossModReborn` | 3 | 7.5.7.2 | 7.5.7.2, 7.4.5.18, 7.3.5.27 |
| `FuckAnimationLock` | 3 | 3.0.17.1 | 3.0.17.1, 3.0.14.6, 3.0.13.0 |
| `NyaDraw` | 3 | 1.15.1.8 | 1.15.1.8, 1.14.0.35, 1.13.1.8 |
| `PalacePal` | 3 | 4.15.0.0 | 4.9.0.0, 4.15.0.0, 4.14.0.1 |

## 下载链接异常（21 条）

这些插件在**所有**源仓库里的下载地址都不可用，安装会失败，仅作索引保留：

| InternalName | 版本 | 状态 |
| --- | --- | --- |
| `MaskedCarnivale` | 0.0.0.7 | EMPTY |
| `HoardFarm` | 1.6.0.2 | EMPTY |
| `XIVSlothComboX` | 3.3.2.5 | HTTP404 |
| `FATEAutoSync` | 1.3.0.0 | HTTP404 |
| `FoodCheck` | 1.0.0.0 | HTTP404 |
| `LootMaster` | 1.0.0.6 | HTTP404 |
| `PotatoFamine2` | 2.0.0.1 | HTTP404 |
| `XIVSlothCombo` | 3.1.2.1 | HTTP404 |
| `MacroChain-Ori` | 999.999.999.999 | HTTP404 |
| `Debugger` | 6.58.12.0 | HTTP404 |
| `DiscordIntegration` | 6.58.12.0 | HTTP404 |
| `InstanceIDViewer` | 6.58.12.0 | HTTP404 |
| `MareSynchronos` | 0.9.43 | UNREACHABLE |
| `AetherBox` | 1.0.0.13 | HTTP404 |
| `SamplePlugin` | 0.0.0.8 | HTTP404 |
| `BetterTargetingSystemPvP` | 1.0.0.5 | HTTP404 |
| `GrowUp` | 0.0.0.3 | HTTP404 |
| `PFRadar` | 1.5.0.7 | HTTP403 |
| `FuckDalamudCN` | 2.0.0.10 | HTTP403 |
| `Accountant` | 1.8.3.0 | HTTP403 |
| `PFClassifier` | 1.2.30 | HTTP403 |

## 说明

- 本仓库只做**索引合并**，不托管任何插件本体；插件仍从原作者发布地址下载，版权归各作者。
- 插件兼容性看 `DalamudApiLevel`：当前分布 API 15: 132 / API 14: 8 / API 13: 2 / API 12: 4 / API 11: 5 / API 10: 5 / API 9: 36 / API 8: 2 / API 7: 4 / API 6: 4 / API 5: 2 / API 0: 2。
  低于当前 Dalamud API 等级的条目无法加载，属于上游仓库未更新。
- 上游仓库后续更新不会自动同步到本仓库。
