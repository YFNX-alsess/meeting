# web — 前端

只负责 UI 组织与订阅，不含任何业务计算。

| 文件 | 职责 |
| --- | --- |
| `index.html` | 结构（无内联脚本、无内联样式） |
| `style.css` | 外观 |
| `api.js` | API 层：统一解析后端地址，暴露 `health()` / `detect(file)` / `sendChat(q)` / `subscribeChat(q, handlers)` |
| `app.js` | UI 逻辑：DOM 渲染、按钮状态、把订阅回调接到界面上 |

约定：
- `app.js` 不直接写 `fetch` / `EventSource`，网络细节全部收在 `api.js`；
- 所有数据用 `textContent` 写入 DOM，不用 `innerHTML` 拼接，避免 XSS；
- 后端地址默认与页面同源；只有用 `file://` 直接打开时才回退到 `http://127.0.0.1:8000`。

访问方式：启动后端后打开 <http://127.0.0.1:8000>（由后端托管本目录），不要双击 html 文件。
