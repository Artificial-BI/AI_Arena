document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const extraInput = document.getElementById('extraInput');
    const createCharacterForm = document.getElementById('create-character-form');
    const nameField = createCharacterForm.querySelector('#name');
    const descriptionField = createCharacterForm.querySelector('#description');
    const characterButtons = document.querySelectorAll('#character-list .character-item button[data-name]');

    let characterChart;

    function displayCharacterStats(traits) {
        console.log('Received traits:', traits); // Логирование данных характеристик

        const ctx = document.getElementById('character-chart').getContext('2d');
        const chartData = {
            labels: Object.keys(traits),
            datasets: [{
                label: 'Характеристики',
                data: Object.values(traits),
                backgroundColor: 'rgba(34, 139, 34, 0.8)',  // Темно-зеленый цвет баров
                borderColor: 'rgba(34, 139, 34, 1)',
                borderWidth: 1
            }]
        };

        if (characterChart) {
            characterChart.destroy();
        }

        characterChart = new Chart(ctx, {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Характеристики'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Значения'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(tooltipItem) {
                                return tooltipItem.label + ': ' + tooltipItem.raw;
                            }
                        }
                    },
                    legend: {
                        display: false // Убираем заголовок гистограммы
                    }
                }
            },
            plugins: [{
                afterDatasetsDraw: function(chart) {
                    const ctx = chart.ctx;
                    ctx.font = '8px Arial';  // Уменьшаем размер текста до обычного
                    ctx.fillStyle = 'rgba(0, 0, 0, 1)';

                    chart.data.datasets.forEach(function(dataset, i) {
                        const meta = chart.getDatasetMeta(i);
                        meta.data.forEach(function(bar, index) {
                            const data = dataset.data[index];
                            if (data !== 0) { // Отображать только ненулевые значения
                                ctx.fillText(data, bar.x, bar.y - 5);
                            }
                        });
                    });
                }
            }]
        });

        // Преобразование характеристик в строку и вставка в поле
        const traitsString = Object.entries(traits).map(([key, value]) => `${key}:${value}`).join(', ');
        extraInput.value = traitsString;
    }

    function selectCharacter(characterId) {
        const button = document.querySelector(`#character-list .character-item button[data-id='${characterId}']`);
        if (button) {
            nameField.value = button.dataset.name;
            descriptionField.value = button.dataset.description;

            // Обновление характеристик персонажа в поле extraInput
            const traits = JSON.parse(button.dataset.traits);
            console.log('Selected character traits:', traits); // Логирование данных выбранного персонажа
            displayCharacterStats(traits);
        }
    }

    characterButtons.forEach(button => {
        button.addEventListener('click', function() {
            selectCharacter(this.dataset.id);
        });
    });

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

                // Обновление имени, описания и характеристик персонажа, если они были распарсены
                if (data.character) {
                    if (data.character.name) {
                        document.getElementById('name').value = data.character.name;
                    }
                    if (data.character.description) {
                        document.getElementById('description').value = data.character.description;
                    }
                    if (data.character.strength !== undefined) {
                        const traits = {
                            "Здоровье": data.character.health,
                            "Интеллект": data.character.intelligence,
                            "Сила": data.character.strength,
                            "Магия": data.character.magic,
                            "Атака": data.character.attack,
                            "Защита": data.character.defense,
                            "Скорость": data.character.speed,
                            "Ловкость": data.character.agility,
                            "Выносливость": data.character.endurance,
                            "Удача": data.character.luck
                        };
                        console.log('Updated character traits:', traits); // Логирование данных обновленного персонажа
                        displayCharacterStats(traits);
                    }
                }
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Проверка, есть ли выбранный персонаж и его характеристики
    if (lastCharacterId !== null) {
        selectCharacter(lastCharacterId);
    } else if (selectedCharacterTraits) {
        console.log('Initial selected character traits:', selectedCharacterTraits); // Логирование данных первоначально выбранного персонажа
        displayCharacterStats(selectedCharacterTraits);
    }
});
