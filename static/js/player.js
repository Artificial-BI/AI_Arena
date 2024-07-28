document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const extraInput = document.getElementById('extraInput');

    let characterChart;

    function displayCharacterStats(traits) {
        const ctx = document.getElementById('character-chart').getContext('2d');
        const chartData = {
            labels: Object.keys(traits),
            datasets: [{
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
                scales: {
                    y: {
                        beginAtZero: true
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
                            ctx.fillText(data, bar.x, bar.y - 5);
                        });
                    });
                }
            }]
        });

        // Преобразование характеристик в строку и вставка в поле
        const traitsString = Object.entries(traits).map(([key, value]) => `${key}:${value}`).join(', ');
        extraInput.value = traitsString;
    }

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
                            Strength: data.character.strength,
                            Agility: data.character.agility,
                            Intelligence: data.character.intelligence,
                            Endurance: data.character.endurance,
                            Speed: data.character.speed,
                            Magic: data.character.magic,
                            Defense: data.character.defense,
                            Attack: data.character.attack,
                            Charisma: data.character.charisma,
                            Luck: data.character.luck
                        };
                        displayCharacterStats(traits);
                    }
                }
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Проверка, есть ли выбранный персонаж и его характеристики
    if (selectedCharacterTraits) {
        displayCharacterStats(selectedCharacterTraits);
    }
});