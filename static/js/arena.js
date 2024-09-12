document.addEventListener("DOMContentLoaded", function() {
    const playersTable = document.getElementById('players-table');
    const notificationPopup = document.getElementById('notification-popup');
    const notificationMessage = document.getElementById('notification-message');
    const arenaImage = document.getElementById('arena-image');

    function checkStatus() {
        fetch('/arena/get_status', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => updateStatus(data))
        .catch(error => console.error('Ошибка при проверке статуса:', error));
    }

    function updateStatus(data) {
        const statusMessage = `
            Game Status: ${data.game_status} <br>
            Arena Status: ${data.arena_status} <br>
            Battle Status: ${data.battle_status} <br>
            Timer Status: ${data.timer_status}
        `;

        if (notificationMessage.innerHTML !== statusMessage) {
            notificationMessage.innerHTML = statusMessage;
            notificationPopup.style.display = 'block';
        }
    }

    function updateArenaImage() {
        fetch('/arena/get_latest_arena_image')
        .then(response => response.json())
        .then(data => {
            if (data.arena_image_url && arenaImage.src !== data.arena_image_url) {
                arenaImage.src = data.arena_image_url;
            }
        })
        .catch(error => console.error('Error fetching latest arena image:', error));
    }

    function loadCharacterCharts() {
        document.querySelectorAll('tbody tr').forEach((row, index) => {
            const traitsData = row.dataset.traits;
            if (traitsData) {
                try {
                    const traits = JSON.parse(traitsData);
                    const canvas = document.getElementById(`traits-chart-${index + 1}`);
                    if (canvas) {
                        createChart(canvas.getContext('2d'), traits);
                    }
                } catch (e) {
                    console.error('Error parsing traits data:', e);
                }
            }
        });
    }

    function updatePlayersTable() {
        fetch('/arena/get_registered_characters')
        .then(response => response.json())
        .then(data => {
            //console.log("--- Received characters:", data);
            const tbody = playersTable.querySelector('tbody');
            tbody.innerHTML = '';

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

            loadCharacterCharts();
        })
        .catch(error => console.error('Error updating players table:', error));
    }
    
    setInterval(checkStatus, 1000);
    setInterval(updateArenaImage, 5000);
    setInterval(updatePlayersTable, 5000);

    checkStatus();
    updatePlayersTable();

    fetch('/arena/start_async_tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) { 
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => console.log(data))
    .catch(error => console.error('Ошибка при запуске фоновых задач:', error));


    // function updateChats() {
    //     // Обновление арена чата
    //     fetch('/arena/get_arena_chat')
    //         .then(response => response.json())
    //         .then(data => updateChatBox('arena-chat-box', data))
    //         .catch(error => console.error('Ошибка обновления арена чата:', error));
    
    //     // Обновление тактического чата
    //     fetch('/arena/get_tactics_chat')
    //         .then(response => response.json())
    //         .then(data => updateChatBox('tactics-chat-box', data))
    //         .catch(error => console.error('Ошибка обновления тактического чата:', error));
    
    //     // Обновление общего чата
    //     fetch('/arena/get_general_chat')
    //         .then(response => response.json())
    //         .then(data => updateChatBox('general-chat-box', data))
    //         .catch(error => console.error('Ошибка обновления общего чата:', error));
    // }
    
    function updateChats() {
        const chatTypes = ['arena', 'tactics', 'general'];
    
        chatTypes.forEach(chatType => {
            fetch(`/arena/get_chat_messages/${chatType}`)
                .then(response => response.json())
                .then(data => updateChatBox(`${chatType}-chat-box`, data))
                .catch(error => console.error(`Ошибка обновления ${chatType} чата:`, error));
        });
    }
    

    function updateChatBox(chatBoxId, messages) {
        const chatBox = document.getElementById(chatBoxId);
        //console.log("chatBoxId:",chatBoxId,"messages:",messages)
        chatBox.innerHTML = '';  // Очищаем старые сообщения
    
        messages.forEach(msg => {
            const msgElement = document.createElement('p');
            msgElement.textContent = `[${msg.timestamp}] ${msg.sender}: ${msg.content}`;
            chatBox.appendChild(msgElement);
        });
    }
    
    // Запуск обновления чатов каждые 1 секунду
    setInterval(updateChats, 1000);

});
