document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const createCharacterForm = document.getElementById('create-character-form');
    const nameField = createCharacterForm.querySelector('#name');
    const descriptionField = createCharacterForm.querySelector('#description');
    const characterImage = document.querySelector('.selected-character img');
    const loadingMessage = document.getElementById('loading-message');
    //const arenaButton = document.getElementById('to-arena-button'); // Используем идентификатор для надежности
    const toArenaButton = document.getElementById('to-arena-button');
    const characterList = document.getElementById('character-list');
    const noCharactersMessage = document.getElementById('no-characters-message');

// Загружаем данные при первой загрузке страницы из переданного selected_character
if (selectedCharacterId && selectedCharacterTraits) {
    nameField.value = selectedCharacterName || 'Unknown';
    descriptionField.value = selectedCharacterDescription || 'No description available';
    characterImage.src = `/static/${selectedCharacterImageUrl.replace(/ /g, "_")}`;
    
    if (selectedCharacterTraits && typeof selectedCharacterTraits === 'object') {
        const traits = selectedCharacterTraits;
        traits['Life'] = selectedCharacterLife || 100;
        traits['Combat'] = selectedCharacterCombat || 0;
        traits['Damage'] = selectedCharacterDamage || 0;

        displayCharacterStats(traits);
    } else {
        console.error("selectedCharacterTraits is not an object or is null:", selectedCharacterTraits);
    }
}


    function addCharacterToList(character) {
        const li = document.createElement('li');
        li.classList.add('character-item');
        li.style.display = 'flex';
        li.style.alignItems = 'center';
    
        const img = document.createElement('img');
        img.src = `/static/${character.image_url.replace(/ /g, "_")}`;
        img.alt = 'Character Image';
        img.style.width = '50px';
        img.style.height = '50px';
        img.style.objectFit = 'cover';
        img.style.marginRight = '10px';
    
        const button = document.createElement('button');
        button.type = 'button';
        button.classList.add('character-name');
        button.dataset.id = character.id;
        button.dataset.name = character.name;
        button.dataset.description = character.description;
        button.dataset.traits = JSON.stringify(character.traits);
        button.dataset.imageUrl = character.image_url;
        button.textContent = character.name;
    
        button.addEventListener('click', function() {
            selectCharacter(character.id);
        });
    
        const deleteForm = document.createElement('form');
        deleteForm.method = 'post';
        deleteForm.action = `/delete_character/${character.id}`;
        deleteForm.classList.add('delete-form');
    
        const deleteButton = document.createElement('button');
        deleteButton.type = 'submit';
        deleteButton.textContent = 'Delete';
    
        deleteForm.appendChild(deleteButton);
    
        li.appendChild(img); // Добавляем изображение
        li.appendChild(button);
        li.appendChild(deleteForm);
        characterList.appendChild(li);
    }

    function selectCharacter(characterNum) {
        selectedCharacterId = characterNum;

        const button = document.querySelector(`#character-list .character-item button[data-id='${selectedCharacterId}']`);

        if (button) {
            nameField.value = button.dataset.name;
            descriptionField.value = button.dataset.description;
            characterImage.src = `/static/${button.dataset.imageUrl.replace(/ /g, "_")}`;

            if (button.dataset.traits && button.dataset.traits !== "{}") {
                try {
                    const traits = JSON.parse(button.dataset.traits);
                    displayCharacterStats(traits);
                } catch (error) {
                    console.error("Error parsing traits JSON:", error);
                }
            }

            fetch(`/player/select_character/${characterNum}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (!data.error) {
                    nameField.value = data.name;
                    descriptionField.value = data.description;
                    const traits = data.traits;
                    traits['Life'] = data.Life;
                    traits['Combat'] = data.Combat;
                    traits['Damage'] = data.Damage;
                    displayCharacterStats(traits);
                    characterImage.src = `/static/${data.image_url.replace(/ /g, "_")}`;
                }
            })
            .catch(error => console.error("Error fetching character data:", error));
        }
    }

    createCharacterForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(createCharacterForm);

        fetch(createCharacterForm.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'Character created') {
                addCharacterToList(data.character);
                selectCharacter(data.character.id);
                if (characterList.children.length > 0) {
                    noCharactersMessage.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error:', error));
    });

   
    if (toArenaButton) {
        toArenaButton.addEventListener('click', function() {
            if (selectedCharacterId && selectedCharacterId !== 'null') {
                fetch('/player/register_for_arena', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ character_id: selectedCharacterId })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'registered' || data.status === 'updated' || data.status === 'already_registered') {
                        window.location.href = '/arena';
                    } else {
                        alert('Ошибка при регистрации в арену: ' + data.error);
                    }
                })
                .catch(error => console.error('Ошибка:', error));
            } else {
                alert('Пожалуйста, выберите персонажа перед регистрацией в арену.');
            }
        });
    } else {
        console.error("Кнопка 'Arena' не найдена!");
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
                console.log("Received data:", data);
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
                    const character = data.character;
                    nameField.value = character.name;
                    descriptionField.value = character.description;

                    if (character.image_url) {
                        characterImage.src = `/static/${character.image_url.replace(/ /g, "_")}`;
                    }

                    if (character.traits) {
                        const traits = character.traits;  // Уже объект, не нужно парсить
                        console.log("Traits for generated character:", traits);
                        traits['Life'] = character.life;
                        traits['Combat'] = character.combat;
                        traits['Damage'] = character.damage;
                        displayCharacterStats(traits);
                    }
                }
            }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
            loadingMessage.style.display = 'none';
        });
    });

    if (characterList.children.length === 0) {
        noCharactersMessage.style.display = 'block';
    } else {
        noCharactersMessage.style.display = 'none';
    }

    document.querySelectorAll('#character-list .character-item button[data-id]').forEach(button => {
        button.addEventListener('click', function() {
            selectCharacter(this.dataset.id);
        });
    });

    
    document.querySelectorAll('#character-list .delete-form').forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            const characterId = form.action.split('/').pop();

            fetch(form.action, {
                method: 'POST',
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'Character deleted') {
                    form.parentElement.remove();
                    if (selectedCharacterId == characterId) {
                        selectedCharacterId = null;
                        nameField.value = '';
                        descriptionField.value = '';
                        characterImage.src = '';
                        if (window.characterChart) {
                            window.characterChart.destroy();
                            window.characterChart = null;
                        }
                        const remainingCharacters = document.querySelectorAll('#character-list .character-item button[data-id]');
                        if (remainingCharacters.length > 0) {
                            const lastCharacter = remainingCharacters[remainingCharacters.length - 1];
                            selectCharacter(lastCharacter.dataset.id);
                        } else {
                            noCharactersMessage.style.display = 'block';
                        }
                    }
                } else {
                    console.error("Error deleting character:", data.error);
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
});
