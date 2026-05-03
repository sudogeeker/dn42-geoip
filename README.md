# dn42-geoip

从 [DN42 Registry](https://git.dn42.dev/dn42/registry) 自动生成 GeoFeed CSV，每天通过 GitHub Actions 发布 Release。

## 输出格式

每次 Release 包含两份文件：

| 文件 | 格式 | 字段 | 用途 |
|---|---|---|---|
| `geofeed.csv` | RFC 8805 | `prefix,country_code,region,city,postal_code` | WHOIS GeoFeed |
| `geofeed_nt.csv` | NextTrace | `IP_CDIR,LtdCode,ISO3166-2,CityName,ASN,IPWhois` | `nexttrace --dn42` |

## 数据流程

```
                    ┌─────────────────────────────────────────┐
                    │         DN42 Registry (每日 clone)        │
                    └───────┬──────────────────┬──────────────┘
                            │                  │
              ┌─────────────▼──┐     ┌─────────▼──────────────┐
              │ generate_primary │     │ generate_primary_nt    │
              │   (RFC 8805)    │     │   (NextTrace)          │
              └───────┬─────────┘     └─────────┬──────────────┘
                      │                         │
              ┌───────▼──────────┐    ┌─────────▼──────────────┐
              │ geoip_primary.csv │    │ geoip_primary_nt.csv    │
              └───────┬──────────┘    └─────────┬──────────────┘
                      │                         │
              ┌───────▼──────────────────────────────────┐
              │         geoip_manual.csv (人工修正)       │
              └───────┬──────────────────────────────────┘
                      │
              ┌───────▼──────────┐    ┌──────────────────────────┐
              │ merge_primary     │    │ merge_primary_manual_nt   │
              │ _manual.py       │    │ .py (ASN/IPWhois 从       │
              │                  │    │      primary 最长前缀匹配) │
              └───────┬──────────┘    └─────────┬────────────────┘
                      │                         │
              ┌───────▼──────────┐    ┌─────────▼──────────────┐
              │   geofeed.csv    │    │   geofeed_nt.csv        │
              │   (RFC 8805)     │    │   (NextTrace)           │
              └──────────────────┘    └─────────────────────────┘
```

- `generate_primary.py` 遍历 inetnum/inet6num 对象，提取 `country` 字段
- `generate_primary_nt.py` 额外匹配 route/route6 对象提取 ASN，`mnt-by` 作为 IPWhois
- `merge_*.py` 合并自动数据与人工修正，人工数据优先级更高（按前缀去重覆盖）
- `validate.py` 校验所有输入：拒绝非法 CIDR、非标准国家代码、无效 ASN 格式

## 手工修正

只需编辑 `geoip_manual.csv` 一个文件：

```
prefix,country_code,region,city,postal_code
172.22.159.0/27,CA,Ontario,Toronto
```

相同前缀覆盖自动数据。NextTrace 版本的 ASN 和 IPWhois 由程序从 primary 数据中最长前缀匹配自动补全，无需手动填写。

## CI / Release

- 每天 UTC 00:07 自动触发
- 也可手动 `workflow_dispatch`
- 同步发布 `geofeed.csv` 和 `geofeed_nt.csv`

需要在仓库 Secrets 中配置 `DN42_SSH_KEY` 用于拉取 registry。

## 许可证

见 [LICENSE](LICENSE)
