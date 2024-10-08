
document.addEventListener('DOMContentLoaded', function() {
    const playersTable = document.getElementById('players-table');
    const tacticsChatBox = document.getElementById('tactics-chat-box');
    const generalChatBox = document.getElementById('general-chat-box');
    const arenaChatBox = document.getElementById('arena-chat-box');
    const tacticsChatForm = document.getElementById('tactics-chat-form');
    const generalChatForm = document.getElementById('general-chat-form');

    let countdownInterval;
    let chatIntervals = [];

    console.log("Document loaded");

    function startCountdown(remainingTime) {
        const countdownElement = document.createElement('div');
        countdownElement.id = 'countdown';
        countdownElement.style.fontSize = '24px';
        countdownElement.style.fontWeight = 'bold';
        document.body.insertBefore(countdownElement, document.body.firstChild);
    
        countdownInterval = setInterval(() => {
            fetch('/arena/get_timer')
            .then(response => response.json())
            .then(data => {
                if (data.remaining_time <= 0) {
                    clearInterval(countdownInterval);
                    startBattle();
                } else {
                    countdownElement.textContent = `Battle starts in: ${data.remaining_time.toFixed(1)} seconds`;
                }
            })
            .catch(error => console.error('Error fetching timer:', error));
        }, 1000);
    }

    function startBattle() {
        fetch('/arena/start_battle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.error);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'Битва началась') {
                console.log('Battle started successfully');
            } else {
                console.error('Failed to start battle:', data.error);
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function checkAndStartCountdown() {
        fetch('/arena/check_registered_players', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.battle_in_progress) {
                console.log('Battle already in progress');
                document.body.innerHTML = '<h2>Ожидание окончания битвы</h2>';
            } else if (data.timer_in_progress) {
                console.log('Timer already in progress');
                startCountdown(data.remaining_time);
            } else if (data.registered_players >= 2) {
                fetch('/arena/start_timer', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(errorData => {
                            throw new Error(errorData.error);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'Таймер запущен') {
                        startCountdown(30);
                    } else {
                        console.error('Failed to start timer:', data.error);
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function updatePlayersTable() {
        fetch('/arena/get_registered_characters')
        .then(response => response.json())
        .then(data => {
            const tbody = playersTable.querySelector('tbody');
            tbody.innerHTML = ''; // Очищаем таблицу перед заполнением
    
            data.forEach((character, index) => {
                const row = document.createElement('tr');
                row.dataset.traits = JSON.stringify(character.traits);
    
                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${character.user_id}</td>
                    <td>${character.name}</td>
                    <td>
                        <div class="chart-container">
                            <canvas id="traits-chart-${index + 1}" class="chart-canvas"></canvas>
                        </div>
                    </td>
                    <td>
                        <img src="/static/${character.image_url}" alt="Character Image" class="character-image" data-description="${character.description}">
                    </td>
                `;
    
                tbody.appendChild(row);
            });
    
            loadCharacterCharts(); // Обновляем диаграммы характеристик
        })
        .catch(error => console.error('Error updating players table:', error));
    }

    function startPlayersTableUpdate() {
        updatePlayersTable();
        setInterval(updatePlayersTable, 5000);  // Обновление таблицы каждые 5 секунд
    }

    function showNotification(message) {
        const notificationPopup = document.getElementById('notification-popup');
        const notificationMessage = document.getElementById('notification-message');
        
        notificationMessage.textContent = message;
        notificationPopup.classList.add('show');
        
        setTimeout(() => {
            notificationPopup.classList.remove('show');
        }, 5000); // Сообщение исчезнет через 5 секунд
    }

    function updateChat(chatUrl, chatBox) {
        fetch(chatUrl)
        .then(response => response.json())
        .then(data => {
            chatBox.innerHTML = '';
            data.forEach(msg => {
                const messageElement = document.createElement('div');
                messageElement.className = `chat-message ${msg.sender === 'user' ? 'right' : 'left'}`;
                messageElement.innerHTML = `<p>${msg.content}</p><span class="timestamp">${new Date(msg.timestamp).toLocaleString()}</span>`;
                chatBox.appendChild(messageElement);
            });
            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch(error => console.error(`Error loading ${chatUrl} messages:`, error));
    }

    function startChatUpdates() {
        chatIntervals.push(setInterval(() => updateChat('/arena/get_arena_chat', arenaChatBox), 5000));
        chatIntervals.push(setInterval(() => updateChat('/arena/get_general_chat', generalChatBox), 5000));
        chatIntervals.push(setInterval(() => updateChat('/arena/get_tactics_chat', tacticsChatBox), 5000));
    }

    checkAndStartCountdown();
    startPlayersTableUpdate(); // Обновление таблицы и графиков
    startChatUpdates(); // Обновление чатов

    if (tacticsChatForm) {
        tacticsChatForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const messageInput = document.getElementById('tactics-chat-input');
            const message = messageInput.value.trim();

            if (!message) {
                alert('Введите сообщение перед отправкой.');
                return;
            }

            fetch('/arena/send_tactics_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: message, sender: 'user', user_id: user_id })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'Message sent') {
                    const messageElement = document.createElement('div');
                    messageElement.className = 'chat-message right';
                    messageElement.innerHTML = `<p>${message}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                    tacticsChatBox.appendChild(messageElement);

                    const responseElement = document.createElement('div');
                    responseElement.className = 'chat-message left';
                    responseElement.innerHTML = `<p>${data.response}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                    tacticsChatBox.appendChild(responseElement);

                    messageInput.value = '';
                    tacticsChatBox.scrollTop = tacticsChatBox.scrollHeight;
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }

    if (generalChatForm) {
        generalChatForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const messageInput = document.getElementById('general-chat-input');
            const message = messageInput.value.trim();

            if (!message) {
                alert('Введите сообщение перед отправкой.');
                return;
            }

            fetch('/arena/send_general_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: message, sender: 'user', user_id: user_id })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'Message sent') {
                    const messageElement = document.createElement('div');
                    messageElement.className = 'chat-message right';
                    messageElement.innerHTML = `<p>${message}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                    generalChatBox.appendChild(messageElement);

                    const responseElement = document.createElement('div');
                    responseElement.className = 'chat-message left';
                    responseElement.innerHTML = `<p>${data.response}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                    generalChatBox.appendChild(responseElement);

                    messageInput.value = '';
                    generalChatBox.scrollTop = generalChatBox.scrollHeight;
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }
    
    // Load the chart creation script
    const script = document.createElement('script');
    script.src = '/static/js/chart_script.js';
    document.head.appendChild(script);
});
