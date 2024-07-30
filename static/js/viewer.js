document.getElementById('general-chat-form').addEventListener('submit', function (event) {
    event.preventDefault();
    const messageInput = document.getElementById('general-chat-input');
    const message = messageInput.value;
    const userId = getCookie('user_id');

    fetch('/viewer/send_general_chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content: message,
            sender: 'player', // or another username
            user_id: userId,
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'Message sent') {
            messageInput.value = '';
            loadGeneralChat(); // Refresh the chat
        } else {
            console.error('Error:', data.error);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
});

function loadGeneralChat() {
    fetch('/arena/get_general_chat')
        .then(response => response.json())
        .then(data => {
            const chatBox = document.getElementById('general-chat-box');
            chatBox.innerHTML = '';
            data.forEach(msg => {
                const msgElement = document.createElement('div');
                msgElement.classList.add('general-chat-message');
                msgElement.classList.add(msg.user_id === getCookie('user_id') ? 'right' : 'left');
                msgElement.innerHTML = `<p>${msg.content}</p><span class="timestamp">${msg.timestamp} - ${msg.user_id}</span>`;
                chatBox.appendChild(msgElement);
            });
            chatBox.scrollTop = chatBox.scrollHeight;
        });
}

// Add automatic chat refresh every 5 seconds
setInterval(loadGeneralChat, 5000);
// Load chats when the page loads
document.addEventListener('DOMContentLoaded', function () {
    loadGeneralChat();
});
