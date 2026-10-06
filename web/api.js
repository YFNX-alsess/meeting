/*
 * 前端 API 层：集中管理后端地址、请求方式和事件订阅。
 *
 * 约定：app.js 只调用这里暴露的方法，不允许直接写 fetch / EventSource；
 *      后端地址只在这里解析一次，页面其它位置不再出现端口号。
 */
(function (global) {
    "use strict";

    // 与后端同源时用相对路径（推荐，由 app/main.py 托管本目录）；
    // 只有用 file:// 直接打开页面时才回退到本地端口。
    var API_BASE = global.__API_BASE__ ||
        (global.location && global.location.protocol === "file:" ? "http://127.0.0.1:8000" : "");

    /** 从 FastAPI 的错误响应里取出可读信息。 */
    function extractError(response) {
        return response.json()
            .then(function (body) {
                return typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail || body);
            })
            .catch(function () {
                return "请求失败，状态码 " + response.status;
            });
    }

    /** 统一处理响应：2xx 返回 JSON，否则抛出带 detail 的错误。 */
    function parse(response) {
        if (response.ok) {
            return response.json();
        }
        return extractError(response).then(function (message) {
            throw new Error(message);
        });
    }

    /** 查询后端与依赖服务状态。 */
    function health() {
        return fetch(API_BASE + "/api/health").then(parse);
    }

    /** 上传图片做识别，返回 {detections, model}。 */
    function detect(file) {
        var form = new FormData();
        form.append("file", file);
        return fetch(API_BASE + "/api/detect", { method: "POST", body: form }).then(parse);
    }

    /** 阻塞式对话，返回完整回答文本。 */
    function sendChat(query) {
        return fetch(API_BASE + "/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query })
        }).then(parse).then(function (data) {
            return data.reply;
        });
    }

    /**
     * 订阅式对话：后端用 SSE 持续推送文本增量。
     * handlers: {onDelta(text), onDone(), onFailed(message)}
     * 返回一个取消订阅的函数。
     */
    function subscribeChat(query, handlers) {
        var settled = false;
        var source = new EventSource(API_BASE + "/api/chat/stream?query=" + encodeURIComponent(query));

        function settle(callback, payload) {
            if (settled) return;
            settled = true;
            source.close();
            callback(payload);
        }

        source.addEventListener("delta", function (event) {
            if (settled) return;
            handlers.onDelta(JSON.parse(event.data).text);
        });

        source.addEventListener("done", function () {
            settle(handlers.onDone);
        });

        // 自定义事件命名为 failed：EventSource 自身的 error 事件与 SSE 的 error 事件重名
        source.addEventListener("failed", function (event) {
            settle(handlers.onFailed, JSON.parse(event.data).message);
        });

        source.onerror = function () {
            settle(handlers.onFailed, "连接中断，请确认后端服务已启动");
        };

        return function unsubscribe() {
            settled = true;
            source.close();
        };
    }

    global.AIApi = {
        base: API_BASE,
        health: health,
        detect: detect,
        sendChat: sendChat,
        subscribeChat: subscribeChat
    };
})(window);
