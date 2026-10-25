#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dalamud 合并仓库更新脚本
=========================

把 sources.txt 里列出的所有第三方 Dalamud 插件仓库抓下来，去重合并成单个
pluginmaster.json，同时归档全部历史版本，然后提交并推送到 GitHub。

用法：
    python update.py                    # 抓取 + 合并 + 提交 + 推送
    python update.py --no-push          # 只更新文件，不提交
    python update.py --check-only       # 只跑链接校验，不写文件
    python update.py --from-dalamud     # 先从 Dalamud 配置导出仓库列表到 sources.txt
    python update.py --jobs 24          # 提高并发

只依赖 Python 标准库；本机有 curl 时优先用 curl 校验下载链接（更准）。
"""

import argparse
import collections
import datetime
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, '.cache', 'raw')
ARCHIVE = os.path.join(BASE, 'archive')
SOURCES_TXT = os.path.join(BASE, 'sources.txt')
PLUGINMASTER = os.path.join(BASE, 'pluginmaster.json')
README = os.path.join(BASE, 'README.md')
DALAMUD_CONFIG = os.path.join(
    os.environ.get('APPDATA', ''), 'XIVLauncherCN', 'dalamudConfig.json')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) DalamudRepoMerger/1.1'
CURL = shutil.which('curl')

# 常见失效镜像 / 已知可用替代地址
MIRROR_MAP = {
    'https://raw.fastgit.org/': 'https://raw.githubusercontent.com/',
    'https://ghproxy.com/https://raw.githubusercontent.com/': 'https://raw.githubusercontent.com/',
    'https://gh.atmoomen.top/raw.githubusercontent.com/': 'https://raw.githubusercontent.com/',
    'https://gh.atmoomen.top/https://raw.githubusercontent.com/': 'https://raw.githubusercontent.com/',
}


# --------------------------------------------------------------------------
# 小工具
# --------------------------------------------------------------------------
def log(msg=''):
    print(msg, flush=True)


def ensure_dirs():
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(ARCHIVE, exist_ok=True)


def read_json(path, default=None):
    try:
        with io.open(path, encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path, obj):
    tmp = path + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')
    os.replace(tmp, path)


def vtup(v):
    """把 '1.2.3.4' 变成 (1,2,3,4)，不足补 0。"""
    parts = [int(x) for x in re.findall(r'\d+', str(v or '0'))[:4]]
    parts += [0] * (4 - len(parts))
    return tuple(parts)


def to_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default


# --------------------------------------------------------------------------
# 1. 源列表
# --------------------------------------------------------------------------
def load_sources():
    if not os.path.isfile(SOURCES_TXT):
        log(f'[!] 找不到 {SOURCES_TXT}，请先运行 --from-dalamud 生成')
        sys.exit(1)
    urls = []
    with io.open(SOURCES_TXT, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line not in urls:
                urls.append(line)
    return urls


def export_from_dalamud():
    """把 Dalamud 当前启用的第三方仓库导出到 sources.txt。"""
    cfg = read_json(DALAMUD_CONFIG)
    if not cfg:
        log(f'[!] 读取失败：{DALAMUD_CONFIG}')
        sys.exit(1)
    repos = cfg.get('ThirdRepoList', {}).get('$values', [])
    urls = []
    for r in repos:
        u = (r or {}).get('Url')
        if u and u not in urls:
            urls.append(u)
    header = (
        '# Dalamud 第三方插件仓库源列表\n'
        f'# 由 update.py --from-dalamud 于 {datetime.datetime.now():%Y-%m-%d %H:%M:%S} 从\n'
        f'# {DALAMUD_CONFIG} 导出\n'
        '# 一行一个地址，# 开头为注释。失效的地址可以留着，脚本会记录状态并跳过。\n\n'
    )
    with io.open(SOURCES_TXT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(header + '\n'.join(urls) + '\n')
    log(f'[+] 已导出 {len(urls)} 个仓库地址到 sources.txt')
    return urls


# --------------------------------------------------------------------------
# 2. 抓取
# --------------------------------------------------------------------------
def url_candidates(url):
    """生成候选地址：镜像替换 -> 分支名互换 -> blob 转 raw。"""
    cands = []
    u = url
    for prefix, real in MIRROR_MAP.items():
        if u.startswith(prefix):
            cands.append(real + u[len(prefix):])
            if u.startswith('https://gh.atmoomen.top/'):
                cands.append(real + u.split('https://gh.atmoomen.top/', 1)[1]
                             .replace('https://', '', 1))
    cands.append(u)

    if 'raw.githubusercontent.com' in u:
        for a, b in (('/main/', '/master/'), ('/master/', '/main/'),
                     ('/refs/heads/main/', '/main/'), ('/main/', '/refs/heads/main/')):
            if a in u:
                cands.append(u.replace(a, b))

    if 'github.com' in u and '/blob/' in u:
        parts = u.split('github.com/', 1)[1].split('/')
        if len(parts) >= 5:
            owner, repo, _, branch = parts[:4]
            cands.append(f'https://raw.githubusercontent.com/{owner}/{repo}/{branch}/'
                         + '/'.join(parts[4:]))
    return list(dict.fromkeys(cands))


def lenient_load(txt):
    """容忍尾逗号等小毛病的 JSON 解析。"""
    txt = txt.strip().lstrip('\ufeff')
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        fixed = re.sub(r',(\s*[}\]])', r'\1', txt)
        return json.loads(fixed)


def fetch_one(item):
    idx, url = item
    last_err = ''
    for cand in url_candidates(url):
        for attempt in range(2):
            try:
                req = urllib.request.Request(cand, headers={'User-Agent': UA})
                with urllib.request.urlopen(req, timeout=25) as r:
                    body = r.read()
                data = lenient_load(body.decode('utf-8-sig', 'replace'))
                if isinstance(data, dict):
                    data = data.get('Plugins') or data.get('plugins') or []
                if not isinstance(data, list):
                    last_err = '内容不是插件数组'
                    continue
                write_json(os.path.join(CACHE, f'{idx:03d}.json'),
                           {'url': url, 'resolved': cand, 'data': data})
                return {'idx': idx, 'url': url, 'resolved': cand, 'count': len(data),
                        'status': 'OK'}
            except Exception as e:
                last_err = f'{type(e).__name__}: {e}'
                if attempt == 0:
                    time.sleep(0.8)
    return {'idx': idx, 'url': url, 'resolved': None, 'count': 0,
            'status': 'FAIL', 'error': last_err[:160]}


def fetch_all(urls, jobs):
    if os.path.isdir(CACHE):
        shutil.rmtree(CACHE, ignore_errors=True)
    os.makedirs(CACHE, exist_ok=True)
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        results = list(ex.map(fetch_one, list(enumerate(urls))))
    ok = [r for r in results if r['status'] == 'OK']
    fail = [r for r in results if r['status'] != 'OK']
    log(f'[+] 抓取完成：成功 {len(ok)} / {len(urls)}，失败 {len(fail)}')
    for r in fail:
        log(f"    [x] {r['url']}\n        {r.get('error', '')}")
    return results


def load_entries():
    entries = []
    if not os.path.isdir(CACHE):
        return entries
    for fn in sorted(os.listdir(CACHE)):
        d = read_json(os.path.join(CACHE, fn))
        if not d:
            continue
        for p in d.get('data') or []:
            if isinstance(p, dict) and p.get('InternalName'):
                entries.append((d['url'], p))
    return entries


# --------------------------------------------------------------------------
# 3. 下载链接校验
# --------------------------------------------------------------------------
def check_link(url):
    if not isinstance(url, str) or not url.startswith('http'):
        return 'EMPTY'
    if CURL:
        try:
            r = subprocess.run(
                [CURL, '-s', '-o', os.devnull, '-L', '-r', '0-0', '--max-time', '25',
                 '-w', '%{http_code}', url],
                capture_output=True, text=True, timeout=45)
            code = (r.stdout or '').strip()
            if code in ('200', '206'):
                return 'OK'
            if code in ('000', ''):
                return 'UNREACHABLE'
            return f'HTTP{code}'
        except Exception:
            return 'UNREACHABLE'
    # 没有 curl 时退化为 urllib
    for method in ('HEAD', 'GET'):
        try:
            hdr = {'User-Agent': UA}
            if method == 'GET':
                hdr['Range'] = 'bytes=0-0'
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=hdr, method=method), timeout=25) as r:
                return 'OK' if r.status in (200, 206) else f'HTTP{r.status}'
        except urllib.error.HTTPError as e:
            if e.code in (403, 405) and method == 'HEAD':
                continue
            if e.code == 429:
                return 'UNKNOWN'
            if method == 'GET':
                return f'HTTP{e.code}'
        except Exception:
            if method == 'GET':
                return 'UNREACHABLE'
    return 'UNKNOWN'


def check_links(entries, jobs):
    urls = sorted({p.get('DownloadLinkInstall') for _, p in entries
                   if isinstance(p.get('DownloadLinkInstall'), str)})
    log(f'[+] 校验下载链接 {len(urls)} 个 ...')
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        res = dict(zip(urls, ex.map(check_link, urls)))
    good = sum(1 for v in res.values() if v == 'OK')
    log(f'    链接正常 {good} / {len(urls)}')
    return res


# --------------------------------------------------------------------------
# 4. 去重合并
# --------------------------------------------------------------------------
def merge(entries, linkres):
    groups = collections.defaultdict(list)
    for src, p in entries:
        groups[p['InternalName']].append((src, p))

    def score(item):
        _, p = item
        ok = 1 if linkres.get(p.get('DownloadLinkInstall')) == 'OK' else 0
        return (ok, to_int(p.get('DalamudApiLevel')), vtup(p.get('AssemblyVersion')),
                to_int(p.get('LastUpdate')))

    chosen, variants, multi = {}, [], []
    for name, items in groups.items():
        ranked = sorted(items, key=score, reverse=True)
        chosen[name] = ranked[0][1]
        seen, group_variants = set(), []
        for i, (src, p) in enumerate(ranked):
            ver = str(p.get('AssemblyVersion'))
            if ver in seen:
                continue
            seen.add(ver)
            rec = dict(p)
            rec['_source'] = src
            rec['_linkCheck'] = linkres.get(p.get('DownloadLinkInstall'), 'EMPTY')
            rec['_selected'] = (i == 0)
            group_variants.append(rec)
        variants.extend(group_variants)
        if len(seen) > 1:
            multi.append({
                'InternalName': name,
                'Name': chosen[name].get('Name'),
                'occurrences': len(items),
                'distinctVersions': len(seen),
                'picked': {'AssemblyVersion': chosen[name].get('AssemblyVersion'),
                           'DalamudApiLevel': chosen[name].get('DalamudApiLevel'),
                           'source': ranked[0][0]},
                'allVersions': [{'AssemblyVersion': v['AssemblyVersion'],
                                 'DalamudApiLevel': v.get('DalamudApiLevel'),
                                 'source': v['_source'], 'link': v['_linkCheck'],
                                 'selected': v['_selected']} for v in group_variants],
            })

    final, dead = [], []
    for name in sorted(chosen, key=lambda x: chosen[x]['InternalName'].lower()):
        p = dict(chosen[name])
        st = linkres.get(p.get('DownloadLinkInstall'), 'EMPTY')
        if st != 'OK':
            dead.append({'InternalName': p['InternalName'], 'Name': p.get('Name'),
                         'Version': p.get('AssemblyVersion'), 'status': st,
                         'url': p.get('DownloadLinkInstall')})
        final.append(p)

    variants.sort(key=lambda x: (x['InternalName'].lower(), str(x.get('AssemblyVersion'))))
    multi.sort(key=lambda x: (-x['distinctVersions'], x['InternalName'].lower()))
    dead.sort(key=lambda x: x['InternalName'].lower())
    return final, variants, multi, dead


# --------------------------------------------------------------------------
# 5. README
# --------------------------------------------------------------------------
def build_readme(final, variants, multi, dead, src_results):
    repo_url = os.environ.get('REPO_URL', 'https://github.com/hytabc/DalamudMergedPlugins')
    raw_url = repo_url.replace('https://github.com/', 'https://raw.githubusercontent.com/') \
        + '/main/pluginmaster.json'
    apis = collections.Counter(to_int(p.get('DalamudApiLevel')) for p in final)
    api_line = ' / '.join(f'API {k}: {v}' for k, v in sorted(apis.items(), reverse=True))
    ok_src = sum(1 for r in src_results if r['status'] == 'OK')
    raw_entries = sum(r['count'] for r in src_results if r['status'] == 'OK')

    dead_rows = '\n'.join(
        f"| `{d['InternalName']}` | {d.get('Version', '')} | {d['status']} |" for d in dead) or '| - | - | - |'
    multi_rows = '\n'.join(
        f"| `{m['InternalName']}` | {m['distinctVersions']} | {m['picked']['AssemblyVersion']} | "
        + ', '.join(sorted({str(v['AssemblyVersion']) for v in m['allVersions']},
                           key=vtup, reverse=True)) + ' |'
        for m in multi[:20]) or '| - | - | - | - |'

    return f"""# Dalamud 合并插件仓库

把 **{len(src_results)} 个第三方 Dalamud 插件仓库**抓取、去重、合并成的单一仓库。
以后在 Dalamud 里只需要添加这一个链接，不用再维护一长串仓库地址。

- 最近更新：{datetime.date.today().isoformat()}
- 源仓库：{ok_src} / {len(src_results)} 个可读取
- 原始插件条目：{raw_entries} 条 → 去重后 **{len(final)} 个插件**
- 同名不同版本：{len(multi)} 组，共 {len(variants)} 条版本记录已完整归档

## 使用方法

Dalamud 设置 → 实验性 → 第三方插件仓库 → 添加以下地址：

```
{raw_url}
```

（国内网络访问 raw.githubusercontent.com 不稳定时，可用镜像前缀，例如
`https://gh.atmoomen.top/{raw_url}`）

## 去重规则

1. 以 Dalamud 的 `InternalName` 作为唯一标识，**不按显示名去重**——显示名相同但
   InternalName 不同的插件（如 `Splatoon` 与 `SplatoonX`）会各自保留。
2. 同一 `InternalName` 有多个版本时，主表只收录最优版本：下载链接可用 →
   `DalamudApiLevel` 更高 → 版本号更高 → 更新时间更新。
   （API 等级优先，是因为低于当前 Dalamud API 的版本无法加载。）
3. 未入选的版本**不会被丢弃**，全部原样保存在 `archive/variants.json`
   （{len(variants)} 条，含完整原始字段与来源仓库地址），
   `archive/multi-version.json` 是逐插件对比清单。

## 目录

| 文件 | 说明 |
| --- | --- |
| `pluginmaster.json` | Dalamud 读取的插件索引，{len(final)} 个插件，每个一条 |
| `archive/variants.json` | 全部 {len(variants)} 条版本记录（含未入选版本） |
| `archive/multi-version.json` | {len(multi)} 个多版本插件的逐项对比 |
| `archive/sources.json` | 每个源仓库的地址、解析后地址、抓取状态 |
| `archive/original-repos.json` | 合并前的原始仓库地址备份 |
| `archive/deadlinks.json` | 入选条目中下载链接不可用的清单（{len(dead)} 条） |
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
{multi_rows}

## 下载链接异常（{len(dead)} 条）

这些插件在**所有**源仓库里的下载地址都不可用，安装会失败，仅作索引保留：

| InternalName | 版本 | 状态 |
| --- | --- | --- |
{dead_rows}

## 说明

- 本仓库只做**索引合并**，不托管任何插件本体；插件仍从原作者发布地址下载，版权归各作者。
- 插件兼容性看 `DalamudApiLevel`：当前分布 {api_line}。
- 上游仓库更新不会自动同步，需要时手动运行 `update.py`。
"""


# --------------------------------------------------------------------------
# 6. git
# --------------------------------------------------------------------------
def git(args, check=True):
    r = subprocess.run(['git'] + args, cwd=BASE, capture_output=True, text=True)
    if check and r.returncode != 0:
        log(f"[x] git {' '.join(args)} 失败：{(r.stderr or r.stdout).strip()[:300]}")
        return False
    return True


def commit_and_push(push):
    if not git(['add', '-A'], check=False):
        return
    r = subprocess.run(['git', 'status', '--porcelain'], cwd=BASE,
                       capture_output=True, text=True)
    if not (r.stdout or '').strip():
        log('[=] 没有变化，跳过提交')
        return
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    if not git(['commit', '-q', '-m', f'Update plugin index ({ts})'], check=False):
        return
    log('[+] 已提交本地变更')
    if push and git(['push', '-q', 'origin', 'HEAD'], check=False):
        log('[+] 已推送到 GitHub')


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description='更新 Dalamud 合并插件仓库')
    ap.add_argument('--from-dalamud', action='store_true', help='先从 Dalamud 配置导出 sources.txt')
    ap.add_argument('--no-push', action='store_true', help='不提交、不推送')
    ap.add_argument('--no-fetch', action='store_true', help='复用 .cache/raw 里已抓取的数据')
    ap.add_argument('--check-only', action='store_true', help='只校验下载链接')
    ap.add_argument('--jobs', type=int, default=16, help='并发数，默认 16')
    args = ap.parse_args()

    ensure_dirs()
    if args.from_dalamud:
        export_from_dalamud()

    urls = load_sources()
    log(f'[i] 源仓库 {len(urls)} 个')

    if args.no_fetch and os.path.isdir(CACHE):
        src_results = read_json(os.path.join(ARCHIVE, 'sources.json'), []) or []
        log('[i] 复用已有缓存')
    else:
        src_results = fetch_all(urls, args.jobs)
    write_json(os.path.join(ARCHIVE, 'sources.json'), src_results)

    entries = load_entries()
    if not entries:
        log('[x] 没有抓到任何插件条目，终止')
        return 1
    log(f'[i] 原始条目 {len(entries)} 条')

    linkres = check_links(entries, args.jobs)
    if args.check_only:
        bad = [u for u, v in linkres.items() if v != 'OK']
        log(f'[i] 异常链接 {len(bad)} 个')
        for u in bad[:50]:
            log(f'    {linkres[u]:<12} {u}')
        return 0

    final, variants, multi, dead = merge(entries, linkres)

    if not os.path.isfile(os.path.join(ARCHIVE, 'original-repos.json')):
        write_json(os.path.join(ARCHIVE, 'original-repos.json'),
                   {'exportedAt': datetime.datetime.now().astimezone().isoformat(),
                    'count': len(urls),
                    'repos': [{'Url': u, 'IsEnabled': True} for u in urls]})

    write_json(PLUGINMASTER, final)
    write_json(os.path.join(ARCHIVE, 'variants.json'), variants)
    write_json(os.path.join(ARCHIVE, 'multi-version.json'), multi)
    write_json(os.path.join(ARCHIVE, 'deadlinks.json'), dead)

    with io.open(README, 'w', encoding='utf-8', newline='\n') as f:
        f.write(build_readme(final, variants, multi, dead, src_results))

    log(f'[+] 合并完成：{len(final)} 个插件 / 多版本 {len(multi)} 组 / '
        f'归档版本 {len(variants)} 条 / 异常链接 {len(dead)} 条')

    if not args.no_push:
        commit_and_push(push=True)
    else:
        log('[i] --no-push，未提交')
    return 0


if __name__ == '__main__':
    sys.exit(main())
