// Функциональность для обновления чата и отправки сообщений

document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    chatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const messageInput = document.getElementById('message');
        const message = messageInput.value;
        if (message.trim() !== '') {
            // Отправка сообщения на сервер
            fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({ 'message': message })
            }).then(response => {
                if (response.ok) {
                    // Очистка поля ввода после успешной отправки
                    messageInput.value = '';
                }
            });
        }
    });
});
