# dn42-geoip

从 [DN42 Registry](https://git.dn42.dev/dn42/registry) 自动生成 RFC 8805 格式的 `geofeed.csv`。

## 工作方式

```
DN42 Registry ──► generate_primary.py ──► geoip_primary.csv
                                                │
                        geoip_manual.csv ────────┼──► merge_primary_manual.py ──► geofeed.csv
```

- `generate_primary.py` 遍历 registry 中所有 inetnum/inet6num 对象，提取带 `country` 字段的条目
- `merge_primary_manual.py` 合并自动数据与人工修正，人工数据优先级更高
- GitHub Actions 每天自动运行，发布 dated release

## 手工修正

编辑 `geoip_manual.csv`，格式为：

```
prefix,country_code,region,city,postal_code
172.22.159.0/27,CA,Ontario,Toronto
```

相同前缀的条目会覆盖自动生成的数据。

## CI / Release

- 每天 UTC 00:07 自动触发
- 也可手动 `workflow_dispatch`
- 生成 `geofeed.csv` 并作为 GitHub Release 发布

## 许可证

见 [LICENSE](LICENSE)
