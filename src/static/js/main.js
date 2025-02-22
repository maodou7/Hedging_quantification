// WebSocket连接和重连逻辑
let ws = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectDelay = 3000; // 3秒
const statusContent = document.getElementById('status-content');

function showStatus(message, type = 'info') {
    const colors = {
        info: 'black',
        success: 'green',
        warning: 'orange',
        error: 'red'
    };
    statusContent.innerHTML = `<div style="color: ${colors[type]};">${message}</div>`;
}

function connectWebSocket() {
    try {
        ws = new WebSocket('ws://localhost:8000/api/v1/monitor/ws');

        ws.onopen = () => {
            console.log('WebSocket连接已建立');
            showStatus('连接成功，正在获取数据...', 'success');
            reconnectAttempts = 0; // 重置重连计数
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                updateStatus(data);
            } catch (error) {
                console.error('数据解析错误:', error);
                showStatus('数据解析错误', 'error');
            }
        };

        ws.onclose = (event) => {
            console.log('WebSocket连接已关闭:', event.code, event.reason);
            handleDisconnection();
        };

        ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
            handleDisconnection();
        };
    } catch (error) {
        console.error('连接创建错误:', error);
        showStatus('无法创建连接', 'error');
    }
}

function handleDisconnection() {
    if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        showStatus(`连接已断开，正在尝试重新连接... (${reconnectAttempts}/${maxReconnectAttempts})`, 'warning');
        setTimeout(connectWebSocket, reconnectDelay);
    } else {
        showStatus('连接失败，请检查服务器状态或刷新页面重试', 'error');
    }
}

// 更新状态显示
function updateStatus(data) {
    const timestamp = new Date(data.timestamp);
    const timeString = timestamp.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    let html = '<div class="status-container" style="padding: 15px; background: #f8f9fa; border-radius: 5px;">';
    
    // 系统状态部分
    html += '<div class="system-status" style="margin-bottom: 20px;">';
    html += '<h3 style="margin: 0 0 10px 0;">系统状态</h3>';
    html += '<ul style="list-style: none; padding: 0; margin: 0;">';
    html += `<li style="margin-bottom: 10px;">API服务运行状态: ${data.api_service_running ? '✅ 运行中' : '❌ 已停止'}</li>`;
    html += `<li style="margin-bottom: 10px;">WebSocket连接状态: ${data.websocket_connected ? '✅ 已连接' : '❌ 未连接'}</li>`;
    html += `<li style="margin-bottom: 10px;">数据监控状态: ${data.data_monitoring_active ? '✅ 运行中' : '❌ 已停止'}</li>`;
    html += '</ul></div>';

    // 交易所状态部分
    if (data.exchange_status) {
        html += '<div class="exchange-status">';
        html += '<h3 style="margin: 0 0 10px 0;">交易所连接状态</h3>';
        html += '<ul style="list-style: none; padding: 0; margin: 0;">';
        for (const [exchange, status] of Object.entries(data.exchange_status)) {
            html += `<li style="margin-bottom: 15px;">
                <strong>${exchange}</strong><br>
                <span style="margin-left: 20px;">REST API: ${status.rest ? '✅ 已连接' : '❌ 未连接'}</span><br>
                <span style="margin-left: 20px;">WebSocket: ${status.websocket ? '✅ 已连接' : '❌ 未连接'}</span>
            </li>`;
        }
        html += '</ul></div>';
    }

    // 时间戳
    html += `<div style="margin-top: 15px; font-size: 0.9em; color: #666;">最后更新时间: ${timeString}</div>`;
    
    html += '</div>';
    statusContent.innerHTML = html;
}

// 页面加载完成后开始连接
document.addEventListener('DOMContentLoaded', () => {
    showStatus('正在连接到服务器...', 'info');
    connectWebSocket();
}); 