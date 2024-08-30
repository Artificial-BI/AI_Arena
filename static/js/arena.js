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

            setTimeout(() => {
                notificationPopup.style.display = 'none';
            }, 5000);
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

    setInterval(checkStatus, 1000);
    setInterval(updateArenaImage, 5000);

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
            console.log("--- Received characters:", data); // Логирование данных
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
    
            loadCharacterCharts();
        })
        .catch(error => console.error('Error updating players table:', error));
    }
    
    checkStatus();
    updatePlayersTable();

    fetch('/arena/start_async_tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {  // Проверка на успешный статус HTTP
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => console.log(data))
    .catch(error => console.error('Ошибка при запуске фоновых задач:', error));
});
