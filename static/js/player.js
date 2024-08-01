document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const extraInput = document.getElementById('extraInput');
    const createCharacterForm = document.getElementById('create-character-form');
    const nameField = createCharacterForm.querySelector('#name');
    const descriptionField = createCharacterForm.querySelector('#description');
    const characterButtons = document.querySelectorAll('#character-list .character-item button[data-name]');
    const registerButton = document.getElementById('register-arena-button');

    let characterChart;

    function displayCharacterStats(traits) {
        console.log('Received traits:', traits); // Logging traits data

        const ctx = document.getElementById('character-chart').getContext('2d');
        const chartData = {
            labels: Object.keys(traits),
            datasets: [{
                label: 'Attributes',
                data: Object.values(traits),
                backgroundColor: 'rgba(34, 139, 34, 0.8)',  // Dark green bars
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
                        display: false // Remove the chart title
                    }
                }
            },
            plugins: [{
                afterDatasetsDraw: function(chart) {
                    const ctx = chart.ctx;
                    ctx.font = '8px Arial';  // Reduce text size to normal
                    ctx.fillStyle = 'rgba(0, 0, 0, 1)';

                    chart.data.datasets.forEach(function(dataset, i) {
                        const meta = chart.getDatasetMeta(i);
                        meta.data.forEach(function(bar, index) {
                            const data = dataset.data[index];
                            if (data !== 0) { // Display only non-zero values
                                ctx.fillText(data, bar.x, bar.y - 5);
                            }
                        });
                    });
                }
            }]
        });

        // Convert traits to a string and insert into the field
        const traitsString = Object.entries(traits).map(([key, value]) => `${key}:${value}`).join(', ');
        extraInput.value = traitsString;
    }

    function selectCharacter(characterId) {
        const button = document.querySelector(`#character-list .character-item button[data-id='${characterId}']`);
        if (button) {
            const user_id = button.dataset.user_id;
            nameField.value = button.dataset.name;
            descriptionField.value = button.dataset.description;

            // Update character traits in the extraInput field
            const traits = JSON.parse(button.dataset.traits);
            console.log('Selected character traits:', traits); // Logging selected character data
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
        const message = messageInput.value.trim();

        if (!message) {
            alert('Enter a message before sending.');
            return; // Check for empty message
        }

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

                // Update character name, description, and traits if they were parsed
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
                        console.log('Updated character traits:', traits); // Logging updated character data
                        displayCharacterStats(traits);
                    }
                }
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Check if a character is selected and their traits
    if (lastCharacterId !== null) {
        selectCharacter(lastCharacterId);
    } else if (selectedCharacterTraits) {
        console.log('Initial selected character traits:', selectedCharacterTraits); // Logging initial selected character data
        displayCharacterStats(selectedCharacterTraits);
    }

    // Register for arena button handler
    registerButton.addEventListener('click', function() {
        const selectedCharacterId = lastCharacterId; // Using lastCharacterId as selected character id
        if (!selectedCharacterId) {
            alert('Please select a character first.');
            return;
        }

        fetch(`/player/register_for_arena`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ character_id: selectedCharacterId }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' || data.status === 'registered' || data.status === 'updated') {
                window.location.href = '/arena'; // Redirect to the arena page
            } else {
                alert('Failed to register for the arena: ' + data.error);
            }
        })
        .catch(error => console.error('Error:', error));
    });
});
