// --- static/js/player.js ---

function selectCharacter(characterId) {
    fetch(`/player/select_character/${characterId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error(data.error);
        } else {
            document.getElementById('name').value = data.name;
            document.getElementById('description').value = data.description;
        }
    })
    .catch(error => console.error('Error:', error));
}

// Функция для отображения характеристик персонажа на графике
function displayCharacterStats(traits) {
    const ctx = document.getElementById('character-chart').getContext('2d');
    const chartData = {
        labels: Object.keys(traits),
        datasets: [{
            label: 'Характеристики персонажа',
            data: Object.values(traits),
            fill: false,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
        }]
    };
    const myChart = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(tooltipItem) {
                            return tooltipItem.label + ': ' + tooltipItem.raw + '%';
                        }
                    }
                }
            }
        }
    });
}

// Проверка, есть ли выбранный персонаж и его характеристики
document.addEventListener('DOMContentLoaded', function() {
    if (selectedCharacterTraits) {
        displayCharacterStats(selectedCharacterTraits);
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const generalChatForm = document.getElementById('general-chat-form');
    const generalChatBox = document.getElementById('general-chat-box');

    chatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const messageInput = document.getElementById('message');

        fetch(chatForm.action, {
            method: 'POST',
            body: new FormData(chatForm),
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

    generalChatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const generalMessageInput = document.getElementById('general-message');

        fetch(generalChatForm.action, {
            method: 'POST',
            body: new FormData(generalChatForm),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'General message sent') {
                const messageElement = document.createElement('div');
                messageElement.className = 'chat-message right';
                messageElement.innerHTML = `<p>${generalMessageInput.value}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                generalChatBox.appendChild(messageElement);
                generalMessageInput.value = '';
                generalChatBox.scrollTop = generalChatBox.scrollHeight;
            }
        })
        .catch(error => console.error('Error:', error));
    });
});
