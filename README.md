### 快速上手 README
这是一个自动聚合和测试免费节点的公共仓库。你可以轻松获取最新的订阅，或直接抓取所有节点数据供爬虫使用。

#### 🚀 订阅地址
每次更新后，都会自动生成以下格式的链接。直接在客户端（如 v2rayN, Clash Verge）中添加即可。

*   📥 **通用订阅** (`Base64` 格式)🔗： [https://raw.githubusercontent.com/yhyh0000/-d8uzaH-Gwshz/main/data/list.txt](https://raw.githubusercontent.com/yhyh0000/-d8uzaH-Gwshz/main/data/list.txt)
*   📦 **Clash 订阅** (`YAML` 格式)🔗： [https://raw.githubusercontent.com/yhyh0000/-d8uzaH-Gwshz/main/data/list.yml](https://raw.githubusercontent.com/yhyh0000/-d8uzaH-Gwshz/main/data/list.yml)
*   📄 **原始节点列表** (`list_raw.txt`)： [https://raw.githubusercontent.com/yhyh0000/-d8uzaH-Gwshz/main/data/list_raw.txt](https://raw.githubusercontent.com/yhyh0000/-d8uzaH-Gwshz/main/data/list_raw.txt)

#### 📖 文件清单
仓库中的主要文件如下，方便你按需查找：

*   `data/list.txt`：**Base64** 编码的通用订阅，所有协议节点的全集。
*   `data/list_raw.txt`：未包含任何编码的原始节点 URI 列表，每行一个。
*   `data/list.yml`：**Clash** 内核的标准格式配置，可直接使用。
*   `data/list.meta.yml`：带策略组（UrlTest）的 **Clash.Meta** 内核格式配置。
*   `data/nodes.yml`：内容与 `list.yml` 一致，为 Clash 格式。
*   `data/list_result.csv`：以表格形式整理的节点摘要数据，方便进行数据分析。
*   `data/adblock.yml`：从上游项目同步的广告屏蔽规则，供 Clash 使用。

> 💡 **特别注意**：以上所有文件均通过 GitHub Actions **每 12 小时**自动更新一次，无需额外操作。

---
