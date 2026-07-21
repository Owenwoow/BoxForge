# 用 Docker 部署到公网

[English](deployment.md) · [简体中文](deployment.zh-CN.md) · [← README](../README.zh-CN.md)

给**一个人**跑网页界面用 `streamlit run` 就够了。要部署到 VPS 让**很多人**用，请用仓库自带的 Docker 方案——它已经打包好 CadQuery/OpenCASCADE 所需的系统库，并做了面向公网的安全加固。

## 1. 一条命令启动

```bash
# 在服务器上，仓库根目录执行：
docker compose up -d --build

# 网页界面现在跑在   http://<服务器IP>:8501
# 查看日志：         docker compose logs -f
# git pull 后更新：  docker compose up -d --build
# 停止：             docker compose down
```

首次构建会下载 CadQuery/OCP 轮子，可能要几分钟；之后有缓存会很快。

## 2. 前面挂 TLS + 域名（推荐）

不要把 `8501` 端口直接暴露到公网。用反向代理终结 HTTPS 再转发到容器。Streamlit 走 WebSocket，代理必须透传 `Upgrade` 头。

**Caddy**（`Caddyfile`，自动申请 HTTPS 证书）：

```caddy
box.example.com {
    reverse_proxy localhost:8501
}
```

**Nginx**：

```nginx
server {
    server_name box.example.com;
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Upgrade $http_upgrade;      # WebSocket
        proxy_set_header Connection "upgrade";        # WebSocket
        proxy_read_timeout 3600s;
    }
    # 用 certbot 或自有证书配置 TLS
}
```

代理和应用在同一台机器时，把 compose 的端口映射改成 `"127.0.0.1:8501:8501"`，让容器只监听本机，公网只能经反向代理访问。

## 3. 面向公网做了哪些加固

- **容器非 root 运行**，关闭 Streamlit 遥测，隐藏开发工具栏和报错堆栈（`box_generator/.streamlit/config.toml`）。
- **资源上限**（`docker-compose.yml` 里的 `cpus`、`memory`、`pids_limit`）——CadQuery 建模吃 CPU/内存，这层上限能把单个恶意请求的破坏限制住。
- **缓存与磁盘有界**——预览文件放在限定大小的 `tmpfs`，旧预览和缓存模型会自动清理，磁盘/内存不会随时间涨上去。
- **输入滥用防护**（`box_builder/validate.py`）——隔板树（UI 里可粘贴原始 YAML）限制了嵌套深度和隔板总数；导出文件名会被裁成安全的纯文件名，无法穿越目录。

## 4. 调参

部署前按服务器情况改 `docker-compose.yml`：

| 配置项 | 含义 | 何时调大 |
|---|---|---|
| `cpus` / `memory` | 单容器硬上限 | 大配置服务器上建模嫌慢 |
| `pids_limit` | 最大进程/线程数 | 出现线程上限报错 |
| `tmpfs /tmp size` | 预览 STL 暂存空间 | 需要生成超大模型 |

模型成本相关的上限在代码里：`box_builder/validate.py` 的 `MAX_PARTITION_DEPTH` / `MAX_PARTITION_NODES`，以及 `box_generator/app.py` 的 `MAX_PREVIEW_FILES` 和缓存大小。
