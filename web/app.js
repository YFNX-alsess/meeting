/*
 * 页面逻辑：只负责 UI 组织与订阅回调绑定。
 *
 * 约定：本文件不做 HTTP 细节（交给 api.js），也不用 innerHTML 拼接数据（统一 textContent，防 XSS）。
 */
(function () {
    "use strict";

    var els = {
        status: document.getElementById("status-line"),
        chatBox: document.getElementById("chat-box"),
        chatForm: document.getElementById("chat-form"),
        userInput: document.getElementById("user-input"),
        sendBtn: document.getElementById("send-btn"),
        imageInput: document.getElementById("image-input"),
        detectBtn: document.getElementById("detect-btn"),
        detectResult: document.getElementById("detect-result")
    };

    /** 追加一条聊天气泡，返回该气泡元素（流式更新时复用）。 */
    function appendBubble(role, text) {
        var bubble = document.createElement("div");
        bubble.className = "message " + role;
        bubble.textContent = text;
        els.chatBox.appendChild(bubble);
        els.chatBox.scrollTop = els.chatBox.scrollHeight;
        return bubble;
    }

    /** 清空识别结果列表。 */
    function clearResult() {
        while (els.detectResult.firstChild) {
            els.detectResult.removeChild(els.detectResult.firstChild);
        }
    }

    /** 写入一条识别结果或提示。 */
    function addResult(text, kind) {
        var item = document.createElement("li");
        item.textContent = text;
        if (kind) item.className = kind;
        els.detectResult.appendChild(item);
    }

    /** 启动时读取后端状态，缺依赖时明确提示，而不是等到用户点击才报错。 */
    function refreshStatus() {
        window.AIApi.health().then(function (data) {
            var parts = [
                data.model.ready ? "✅ YOLO 就绪（" + data.model.detail + "）" : "⚠️ YOLO 不可用：" + data.model.detail,
                data.dify.ready ? "✅ Dify 已配置" : "⚠️ Dify 未配置：" + data.dify.detail
            ];
            els.status.textContent = parts.join("　|　");
        }).catch(function (error) {
            els.status.textContent = "❌ 无法连接后端：" + error.message;
            els.status.classList.add("error");
        });
    }

    /** 提交问题：订阅后端推送，边收边渲染。 */
    function handleChatSubmit(event) {
        event.preventDefault();
        var query = els.userInput.value.trim();
        if (!query) return;

        appendBubble("user", "你: " + query);
        els.userInput.value = "";
        els.sendBtn.disabled = true;
        els.sendBtn.textContent = "思考中…";

        var bubble = appendBubble("ai", "AI: ");
        var received = 0;

        function finish() {
            els.sendBtn.disabled = false;
            els.sendBtn.textContent = "发送";
        }

        window.AIApi.subscribeChat(query, {
            onDelta: function (text) {
                received += 1;
                bubble.textContent += text;
                els.chatBox.scrollTop = els.chatBox.scrollHeight;
            },
            onDone: function () {
                if (!received) bubble.textContent = "AI: （没有返回内容）";
                finish();
            },
            onFailed: function (message) {
                bubble.classList.add("error");
                bubble.textContent = received ? bubble.textContent + "\n[中断] " + message : "❌ " + message;
                finish();
            }
        });
    }

    /** 上传图片：识别期间禁用按钮，结果用列表渲染。 */
    function handleDetect() {
        var file = els.imageInput.files && els.imageInput.files[0];
        clearResult();

        if (!file) {
            addResult("⚠️ 请先选择一张图片！", "warn");
            return;
        }

        els.detectBtn.disabled = true;
        els.detectBtn.textContent = "识别中…";
        addResult("⏳ 正在识别中，请稍候…");

        window.AIApi.detect(file).then(function (data) {
            clearResult();
            if (!data.detections.length) {
                addResult("🙁 未识别到任何目标物体。", "warn");
                return;
            }
            addResult("🎯 使用模型：" + data.model);
            data.detections.forEach(function (item) {
                addResult("- " + item["class"] + "（置信度 " + item.confidence + "，位置 " + item.bbox.join(", ") + "）");
            });
        }).catch(function (error) {
            clearResult();
            addResult("❌ " + error.message, "error");
        }).then(function () {
            els.detectBtn.disabled = false;
            els.detectBtn.textContent = "上传并识别";
        });
    }

    els.chatForm.addEventListener("submit", handleChatSubmit);
    els.detectBtn.addEventListener("click", handleDetect);
    refreshStatus();
})();
