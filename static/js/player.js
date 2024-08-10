document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const extraInput = document.getElementById('extraInput');
    const createCharacterForm = document.getElementById('create-character-form');
    const nameField = createCharacterForm.querySelector('#name');
    const descriptionField = createCharacterForm.querySelector('#description');
    const characterImage = document.querySelector('.selected-character img');
    const characterButtons = document.querySelectorAll('#character-list .character-item button[data-name]');
    const noCharactersMessage = document.getElementById('no-characters-message');
    const loadingMessage = document.createElement('div');
    const arenaButton = document.querySelector('a[href="/arena"]'); // Находим кнопку Arena

    let characterChart;
    let selectedCharacterId = null;

    // Создание и стилизация элемента для сообщения "Generating..."
    loadingMessage.id = 'loading-message';
    loadingMessage.style.display = 'none';
    loadingMessage.style.position = 'fixed';
    loadingMessage.style.top = '50%';
    loadingMessage.style.left = '50%';
    loadingMessage.style.transform = 'translate(-50%, -50%)';
    loadingMessage.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    loadingMessage.style.color = 'white';
    loadingMessage.style.padding = '20px';
    loadingMessage.style.borderRadius = '5px';
    loadingMessage.style.zIndex = '1000';
    loadingMessage.textContent = 'Generating...';
    document.body.appendChild(loadingMessage);

    function displayCharacterStats(traits) {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded');
            return;
        }

        console.log('Received traits:', traits);

        const ctx = document.getElementById('character-chart').getContext('2d');
        const chartData = {
            labels: Object.keys(traits),
            datasets: [{
                label: 'Attributes',
                data: Object.values(traits),
                backgroundColor: 'rgba(34, 139, 34, 0.8)',
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
                            text: 'Attributes'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Values'
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
                        display: false
                    }
                }
            },
            plugins: [{
                afterDatasetsDraw: function(chart) {
                    const ctx = chart.ctx;
                    ctx.font = '8px Arial';
                    ctx.fillStyle = 'rgba(0, 0, 0, 1)';

                    chart.data.datasets.forEach(function(dataset, i) {
                        const meta = chart.getDatasetMeta(i);
                        meta.data.forEach(function(bar, index) {
                            const data = dataset.data[index];
                            if (data !== 0) {
                                ctx.fillText(data, bar.x, bar.y - 5);
                            }
                        });
                    });
                }
            }]
        });

        const traitsString = Object.entries(traits).map(([key, value]) => `${key}:${value}`).join(', ');
        extraInput.value = traitsString;
    }

    function selectCharacter(characterId) {
        selectedCharacterId = characterId;
        const button = document.querySelector(`#character-list .character-item button[data-id='${characterId}']`);
        if (button) {
            nameField.value = button.dataset.name;
            descriptionField.value = button.dataset.description;
    
            const traits = JSON.parse(button.dataset.traits);
            displayCharacterStats(traits);
    
            const imageUrl = button.dataset.imageUrl.replace(/ /g, "_");
            if (imageUrl && characterImage) {
                characterImage.src = imageUrl.startsWith('/') ? imageUrl : `/${imageUrl}`;
            } else {
                characterImage.src = '/static/images/default/character.png';
            }
        }
    }
    
    

    if (characterButtons.length === 0) {
        noCharactersMessage.style.display = 'block';
    } else {
        noCharactersMessage.style.display = 'none';
        characterButtons.forEach(button => {
            button.addEventListener('click', function() {
                selectCharacter(this.dataset.id);
            });
        });
    }

    chatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const messageInput = document.getElementById('message');
        const message = messageInput.value.trim();

        if (!message) {
            alert('Enter a message before sending.');
            return;
        }

        // Показать сообщение "Generating..."
        loadingMessage.style.display = 'block';

        fetch(chatForm.action, {
            method: 'POST',
            body: new FormData(chatForm),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'Message sent') {
                const messageElement = document.createElement('div');
                messageElement.className = 'chat-message right';
                messageElement.innerHTML = `<p>${message}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                chatBox.appendChild(messageElement);

                const responseElement = document.createElement('div');
                responseElement.className = 'chat-message left';
                responseElement.innerHTML = `<p>${data.response}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                chatBox.appendChild(responseElement);

                messageInput.value = '';
                chatBox.scrollTop = chatBox.scrollHeight;

                // Обновление характеристик персонажа если присутствуют
                if (data.character) {
                    if (data.character.name) {
                        document.getElementById('name').value = data.character.name;
                    }
                    if (data.character.description) {
                        document.getElementById('description').value = data.character.description;
                    }
                    if (data.character.strength !== undefined) {
                        const traits = {
                            "Health": data.character.health,
                            "Intelligence": data.character.intelligence,
                            "Strength": data.character.strength,
                            "Magic": data.character.magic,
                            "Attack": data.character.attack,
                            "Defense": data.character.defense,
                            "Speed": data.character.speed,
                            "Agility": data.character.agility,
                            "Endurance": data.character.endurance,
                            "Luck": data.character.luck
                        };
                        displayCharacterStats(traits);
                    }

                    if (data.image_url) {
                        characterImage.src = `/static/${data.image_url.replace(/ /g, "_")}`;
                    }
                }
            }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
            // Скрыть сообщение "Generating..."
            loadingMessage.style.display = 'none';
        });
    });

    // При нажатии на кнопку Arena
if (arenaButton) {
    arenaButton.addEventListener('click', function(event) {
        event.preventDefault(); // Отменяем переход по ссылке

        if (selectedCharacterId !== null) {
            fetch('/player/register_for_arena', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ character_id: selectedCharacterId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Ошибка:', data.error);
                    alert('Ошибка при регистрации персонажа на арену');
                } else {
                    console.log('Персонаж успешно зарегистрирован для арены:', data);
                    window.location.href = '/arena';
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alert('Произошла ошибка при попытке зарегистрировать персонажа на арену');
            });
        } else {
            alert('Пожалуйста, выберите персонажа перед регистрацией на арену.');
        }
    });
}
    

    // Загружаем выбранного персонажа при открытии страницы
    if (lastCharacterId !== null) {
        selectCharacter(lastCharacterId);
    } else if (selectedCharacterTraits) {
        displayCharacterStats(selectedCharacterTraits);
    }
});
