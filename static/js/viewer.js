document.addEventListener('DOMContentLoaded', function() {
    fetchCharacters();
    fetchBattleUpdates();
    fetchBattleImages();
    fetchChatMessages();

    function fetchCharacters() {
        fetch('/get_characters')
            .then(response => response.json())
            .then(data => {
                const player1Name = document.getElementById('player1-name');
                const player2Name = document.getElementById('player2-name');
                const player1Image = document.getElementById('player1-image');
                const player2Image = document.getElementById('player2-image');
                const player1Description = document.getElementById('player1-description');
                const player2Description = document.getElementById('player2-description');
                const charactersList = document.getElementById('characters-list');

                charactersList.innerHTML = '';
                data.forEach((character, index) => {
                    const characterElement = document.createElement('div');
                    characterElement.classList.add('character');
                    characterElement.innerHTML = `
                        <img src="/static/${character.image_url}" alt="${character.name}">
                        <h3>${character.name}</h3>
                        <p>${character.description}</p>
                    `;
                    charactersList.appendChild(characterElement);
                    
                    if (index === 0) {
                        player1Name.textContent = character.name;
                        player1Image.src = `/static/${character.image_url}`;
                        player1Description.textContent = character.description;
                    } else if (index === 1) {
                        player2Name.textContent = character.name;
                        player2Image.src = `/static/${character.image_url}`;
                        player2Description.textContent = character.description;
                    }
                });

                // Если данных нет, использовать изображения по умолчанию
                if (data.length === 0) {
                    player1Name.textContent = 'Игрок 1';
                    player2Name.textContent = 'Игрок 2';
                    player1Image.src = '/static/images/default/player1.png';
                    player2Image.src = '/static/images/default/player2.png';
                    player1Description.textContent = 'Описание игрока 1';
                    player2Description.textContent = 'Описание игрока 2';
                }
            })
            .catch(error => {
                console.error('Error fetching characters:', error);
                // В случае ошибки использовать изображения по умолчанию
                const player1Name = document.getElementById('player1-name');
                const player2Name = document.getElementById('player2-name');
                const player1Image = document.getElementById('player1-image');
                const player2Image = document.getElementById('player2-image');
                const player1Description = document.getElementById('player1-description');
                const player2Description = document.getElementById('player2-description');
                
                player1Name.textContent = 'Игрок 1';
                player2Name.textContent = 'Игрок 2';
                player1Image.src = '/static/images/default/player1.png';
                player2Image.src = '/static/images/default/player2.png';
                player1Description.textContent = 'Описание игрока 1';
                player2Description.textContent = 'Описание игрока 2';
            });
    }

    function fetchBattleUpdates() {
        fetch('/get_battle_updates')
            .then(response => response.json())
            .then(data => {
                const battleUpdates = document.getElementById('battle-updates');
                battleUpdates.innerHTML = '';
                data.forEach(update => {
                    const updateElement = document.createElement('div');
                    updateElement.classList.add('battle-update');
                    updateElement.innerHTML = `
                        <p>${update.content}</p>
                        <span class="timestamp">${update.timestamp}</span>
                    `;
                    battleUpdates.appendChild(updateElement);
                });
            })
            .catch(error => console.error('Error fetching battle updates:', error));
    }

    function fetchBattleImages() {
        fetch('/get_battle_images')
            .then(response => response.json())
            .then(data => {
                const slidesContainer = document.getElementById('slides');
                slidesContainer.innerHTML = '';
                if (data.length > 0) {
                    data.forEach(image => {
                        const imgElement = document.createElement('img');
                        imgElement.src = `/static/${image.url}`;
                        slidesContainer.appendChild(imgElement);
                    });
                } else {
                    // Используем изображения по умолчанию, если нет сгенерированных изображений
                    const defaultImages = [
                        'battle1.png',
                        'battle2.png',
                        'battle3.png'
                    ];
                    defaultImages.forEach(imageName => {
                        const imgElement = document.createElement('img');
                        imgElement.src = `/static/images/default/${imageName}`;
                        slidesContainer.appendChild(imgElement);
                    });
                }
                setUpSlideshow();
            })
            .catch(error => {
                console.error('Error fetching battle images:', error);
                // В случае ошибки использовать изображения по умолчанию
                const slidesContainer = document.getElementById('slides');
                slidesContainer.innerHTML = '';
                const defaultImages = [
                    'battle1.png',
                    'battle2.png',
                    'battle3.png'
                ];
                defaultImages.forEach(imageName => {
                    const imgElement = document.createElement('img');
                    imgElement.src = `/static/images/default/${imageName}`;
                    slidesContainer.appendChild(imgElement);
                });
                setUpSlideshow();
            });
    }

    function fetchChatMessages() {
        fetch('/get_messages')
            .then(response => response.json())
            .then(data => {
                const chatBox = document.getElementById('chat-box');
                chatBox.innerHTML = '';
                data.forEach(message => {
                    const messageElement = document.createElement('div');
                    messageElement.classList.add('chat-message');
                    if (message.user_id === 1) {
                        messageElement.classList.add('right');
                    } else {
                        messageElement.classList.add('left');
                    }
                    messageElement.innerHTML = `
                        <p>${message.content}</p>
                        <span class="timestamp">${message.timestamp}</span>
                    `;
                    chatBox.appendChild(messageElement);
                });
                chatBox.scrollTop = chatBox.scrollHeight; // Прокручиваем чат вниз
            })
            .catch(error => console.error('Error fetching chat messages:', error));
    }

    document.getElementById('chat-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const messageInput = document.getElementById('message');
        const message = messageInput.value;
        if (message.trim() !== '') {
            fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({ 'message': message })
            }).then(response => {
                if (response.ok) {
                    messageInput.value = '';
                    fetchChatMessages();
                } else {
                    console.error('Failed to send message');
                }
            });
        }
    });

    let slideIndex = 0;
    let autoSlide;

    function setUpSlideshow() {
        const slidesContainer = document.getElementById('slides');
        const slides = slidesContainer.getElementsByTagName('img');
        const prevSlide = document.getElementById('prev-slide');
        const nextSlide = document.getElementById('next-slide');

        function showSlide(index) {
            slideIndex = index;
            const offset = -index * slides[0].clientWidth;
            slidesContainer.style.transform = `translateX(${offset}px)`;
        }

        function next() {
            slideIndex = (slideIndex + 1) % slides.length;
            showSlide(slideIndex);
        }

        function prev() {
            slideIndex = (slideIndex - 1 + slides.length) % slides.length;
            showSlide(slideIndex);
        }

        prevSlide.addEventListener('click', prev);
        nextSlide.addEventListener('click', next);

        autoSlide = setInterval(next, 3000);

        slidesContainer.addEventListener('mouseenter', () => clearInterval(autoSlide));
        slidesContainer.addEventListener('mouseleave', () => {
            autoSlide = setInterval(next, 3000);
        });

        showSlide(slideIndex);
    }

    setInterval(fetchBattleUpdates, 5000); // Обновлять каждые 5 секунд
    setInterval(fetchBattleImages, 30000); // Обновлять каждые 30 секунд
    setInterval(fetchChatMessages, 5000); // Обновлять сообщения чата каждые 5 секунд
});
