// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

let currentFileId = null;
let currentVideoUrl = null;

// Устанавливаем тему
document.body.style.backgroundColor = tg.themeParams.bg_color || '#ffffff';

async function downloadVideo() {
    const url = document.getElementById('videoUrl').value.trim();
    const btn = document.getElementById('downloadBtn');
    const btnText = document.getElementById('btnText');
    const loader = document.getElementById('loader');
    const status = document.getElementById('status');
    const result = document.getElementById('result');

    if (!url) {
        showStatus('Введи ссылку на видео!', 'error');
        tg.HapticFeedback.notificationOccurred('error');
        return;
    }

    if (!url.match(/^https?:\/\//)) {
        showStatus('Неверный формат ссылки!', 'error');
        tg.HapticFeedback.notificationOccurred('error');
        return;
    }

    // Блокируем кнопку и показываем загрузку
    btn.disabled = true;
    btnText.classList.add('hidden');
    loader.classList.remove('hidden');
    result.classList.add('hidden');
    status.classList.add('hidden');

    tg.HapticFeedback.impactOccurred('light');

    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (data.success) {
            currentFileId = data.file_id;
            currentVideoUrl = url;
            
            // Показываем результат
            document.getElementById('videoTitle').textContent = data.title;
            document.getElementById('videoSize').textContent = 
                `Размер: ${(data.size / 1024 / 1024).toFixed(2)} МБ`;
            
            result.classList.remove('hidden');
            showStatus('✅ Видео готово!', 'success');
            
            tg.HapticFeedback.notificationOccurred('success');
        } else {
            showStatus('❌ ' + (data.error || 'Ошибка загрузки'), 'error');
            tg.HapticFeedback.notificationOccurred('error');
        }
    } catch (error) {
        showStatus('❌ Ошибка сети: ' + error.message, 'error');
        tg.HapticFeedback.notificationOccurred('error');
    } finally {
        btn.disabled = false;
        btnText.classList.remove('hidden');
        loader.classList.add('hidden');
    }
}

function downloadToDevice() {
    if (!currentFileId) return;

    // Открываем файл в новой вкладке - браузер/Telegram предложит скачать
    const downloadUrl = window.location.origin + `/api/file/${currentFileId}`;
    
    tg.HapticFeedback.notificationOccurred('success');
    showStatus('📥 Открываю файл...', 'success');
    
    // Открываем ссылку через Telegram
    tg.openLink(downloadUrl);
    
    // НЕ закрываем Mini App сразу - пусть пользователь сам закроет
}


function showStatus(message, type) {
    const status = document.getElementById('status');
    status.textContent = message;
    status.className = `status ${type}`;
    status.classList.remove('hidden');
}

// Обработка Enter
document.getElementById('videoUrl').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        downloadVideo();
    }
});