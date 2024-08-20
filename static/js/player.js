document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const createCharacterForm = document.getElementById('create-character-form');
    const nameField = createCharacterForm.querySelector('#name');
    const descriptionField = createCharacterForm.querySelector('#description');
    const characterImage = document.querySelector('.selected-character img');
    const loadingMessage = document.getElementById('loading-message');
    const arenaButton = document.querySelector('a[href="/arena"]');
    const characterList = document.getElementById('character-list');
    const noCharactersMessage = document.getElementById('no-characters-message');

    let selectedCharacterId = lastCharacterId; // Используем lastCharacterId, который передается из backend

    function addCharacterToList(character) {
        const li = document.createElement('li');
        li.classList.add('character-item');

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

        li.appendChild(button);
        li.appendChild(deleteForm);
        characterList.appendChild(li);
    }
    
    //-------------------- select Character (WORK)----------------------------
    function selectCharacter(characterId) {
        selectedCharacterId = characterId;
        const button = document.querySelector(`#character-list .character-item button[data-id='${characterId}']`);
        if (button) {
            console.log("--------- ID:", characterId);

            nameField.value = button.dataset.name;
            descriptionField.value = button.dataset.description;
            characterImage.src = `/static/${button.dataset.imageUrl.replace(/ /g, "_")}`;
            
            if (button.dataset.traits && button.dataset.traits !== "{}") {
                try {
                    const traits = JSON.parse(button.dataset.traits);
                    traits['Life'] = 100;
                    traits['Combat'] = 0;
                    traits['Damage'] = 0;
                    displayCharacterStats(traits);
                } catch (error) {
                    console.error("Error parsing traits JSON:", error);
                }
            } else {
                console.error("No traits data found for this character or traits are empty.");
            }
    
            // Добавим запрос на сервер для получения актуальной информации о персонаже
            fetch(`/player/select_character/${characterId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log("Server response:", data);
                if (data.error) {
                    console.error("Error from server:", data.error);
                } else {
                    console.log("Selected character from server:", data);
                    // Обновляем данные на клиенте, если нужно
                    nameField.value = data.name;
                    descriptionField.value = data.description;
                    if (data.traits) {
                        traits = data.traits;
                        console.log("----sel------- Traits:", traits);
                        traits['Life'] = data.Life;
                        traits['Combat'] = data.Combat;
                        traits['Damage'] = data.Damage;
                        displayCharacterStats(traits);
                    }
                    if (data.image_url) {
                        characterImage.src = `/static/${data.image_url.replace(/ /g, "_")}`;
                    }
                }
            })
            .catch(error => console.error("Error fetching character data:", error));
        }
    }

    //----------- add Event Listener ---------
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
                // Добавляем нового персонажа в список
                addCharacterToList(data.character);
                // Автоматически выбираем нового персонажа
                selectCharacter(data.character.id);
                if (characterList.children.length > 0) {
                    noCharactersMessage.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Вызов функции при загрузке страницы, если есть выбранный персонаж
    if (selectedCharacterId) {
        selectCharacter(selectedCharacterId);
    }

    //------------ WORK -------------
    // Вызов функции при генерации персонажа
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
                    if (data.character.name) {
                        nameField.value = data.character.name;
                    }
                    if (data.character.description) {
                        descriptionField.value = data.character.description;
                    }

                    if (data.image_url) {
                        characterImage.src = `/static/${data.image_url.replace(/ /g, "_")}`;
                    }
                    if (data.character.traits) {
                        // Преобразование строки в объект, если traits передаются в виде строки
                        let traits;
                        if (typeof data.character.traits === 'string') {
                            try {
                                traits = JSON.parse(data.character.traits);
                            } catch (error) {
                                console.error("Error parsing traits JSON:", error);
                                return;
                            }
                        } else {
                            traits = data.character.traits;
                        }
                        console.log("Traits for generated character:", traits);
                        traits['Life'] = 100;
                        traits['Combat'] = 0;
                        traits['Damage'] = 0;
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

    //---------------------------
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

    // Начальная проверка наличия персонажей
    if (characterList.children.length === 0) {
        noCharactersMessage.style.display = 'block';
    } else {
        noCharactersMessage.style.display = 'none';
    }

    // Добавляем обработчики для уже существующих персонажей
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
                    // Удаляем персонажа из списка
                    form.parentElement.remove();

                    // Если персонаж был выбранным, сбрасываем выбор
                    if (selectedCharacterId == characterId) {
                        selectedCharacterId = null;
                        nameField.value = '';
                        descriptionField.value = '';
                        characterImage.src = '';
                        // Также можно сбросить график
                        if (window.characterChart) {
                            window.characterChart.destroy();
                            window.characterChart = null;
                        }
                    }

                    // Проверка на наличие оставшихся персонажей в списке
                    if (characterList.children.length === 0) {
                        noCharactersMessage.style.display = 'block';
                    }
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
});
