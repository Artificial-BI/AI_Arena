document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const createCharacterForm = document.getElementById('create-character-form');
    const nameField = createCharacterForm.querySelector('#name');
    const descriptionField = createCharacterForm.querySelector('#description');
    const characterImage = document.querySelector('.selected-character img');
    const characterButtons = document.querySelectorAll('#character-list .character-item button[data-name]');
    const noCharactersMessage = document.getElementById('no-characters-message');
    const loadingMessage = document.getElementById('loading-message');
    const arenaButton = document.querySelector('a[href="/arena"]');

    let characterChart;
    let selectedCharacterId = null;

    function displayCharacterStats(traits) {
        const ctx = document.getElementById('character-chart').getContext('2d');
        if (characterChart) {
            characterChart.destroy();
        }
        characterChart = createChart(ctx, traits);
    }

    function selectCharacter(characterId) {
        selectedCharacterId = characterId;
        const button = document.querySelector(`#character-list .character-item button[data-id='${characterId}']`);
        if (button) {
            nameField.value = button.dataset.name;
            descriptionField.value = button.dataset.description;
            try {

                const imageUrl = button.dataset.imageUrl.replace(/ /g, "_");
                if (imageUrl && characterImage) {
                    characterImage.src = imageUrl.startsWith('/') ? imageUrl : `/${imageUrl}`;
                    console.log("1 Image URL:", imageUrl);

                } else {
                    characterImage.src = '/static/images/default/character.png';
                    console.log("2 Image URL:", imageUrl);

                }
            } catch (error) {
                console.error("Error parsing traits JSON:", error);  // Логируем ошибку парсинга
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

                if (data.character) {
                    if (data.character.name) {
                        document.getElementById('name').value = data.character.name;
                    }
                    if (data.character.description) {
                        document.getElementById('description').value = data.character.description;
                    }
                    if (data.character.strength !== undefined) {
                        const traits = {
                            "Strength": data.character.strength,
                            "Dexterity": data.character.dexterity,
                            "Intelligence": data.character.intelligence, 
                            "Endurance": data.character.endurance,
                            "Speed": data.character.speed,
                            "Magic": data.character.magic,
                            "Defense": data.character.defense,
                            "Attack": data.character.attack,
                            "Luck": data.character.luck,
                            "Charisma": data.character.charisma,
                            "Life": data.character.life,
                            "Combat": data.character.combat,
                            "Damage": data.character.damage
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
            loadingMessage.style.display = 'none';
        });
    });

    if (arenaButton) {
        arenaButton.addEventListener('click', function(event) {
            event.preventDefault();

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

    if (lastCharacterId !== null) {
        selectCharacter(lastCharacterId);
    } else if (selectedCharacterTraits) {
        displayCharacterStats(selectedCharacterTraits);
    }
});
