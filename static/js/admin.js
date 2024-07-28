// static/js/admin.js

document.addEventListener('DOMContentLoaded', function() {
    const roleSelect = document.getElementById('role-select');
    const instructionsField = document.getElementById('instructions');
    const saveRoleButton = document.getElementById('save-role');
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');

    roleSelect.addEventListener('change', function() {
        fetch('/admin/get_instructions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `role=${roleSelect.value}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.instructions) {
                instructionsField.value = data.instructions;
            } else {
                instructionsField.value = 'Инструкции не найдены для выбранной роли.';
            }
        })
        .catch(error => console.error('Error:', error));
    });

    saveRoleButton.addEventListener('click', function() {
        const instructions = instructionsField.value;
        const role = roleSelect.value;
        fetch('/admin/save_instructions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `role=${role}&instructions=${encodeURIComponent(instructions)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Инструкции сохранены');
            } else {
                alert('Ошибка при сохранении инструкций');
            }
        })
        .catch(error => console.error('Error:', error));
    });

    chatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const messageInput = document.getElementById('message');
        const formData = new FormData(chatForm);
        formData.append('role', roleSelect.value);

        fetch(chatForm.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'Message sent') {
                const messageElement = document.createElement('div');
                messageElement.className = 'chat-message right';
                messageElement.innerHTML = `<p>${messageInput.value}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                chatBox.appendChild(messageElement);

                const responseElement = document.createElement('div');
                responseElement.className = 'chat-message left';
                responseElement.innerHTML = `<p>${data.response}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                chatBox.appendChild(responseElement);

                messageInput.value = '';
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        })
        .catch(error => console.error('Error:', error));
    });
});
