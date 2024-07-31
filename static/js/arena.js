document.addEventListener('DOMContentLoaded', function() {
    fetchCharacters();
    fetchArenaChatMessages();
    fetchTacticsChatMessages();
    fetchGeneralChatMessages();

    document.getElementById('start-test-battle').addEventListener('click', function() {
        fetch('/arena/start_test_battle', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                console.log('Test battle started:', data);
                alert('Test battle started successfully!');
            })
            .catch(error => {
                console.error('Error starting test battle:', error);
                alert('Failed to start test battle.');
            });
    });

    function fetchCharacters() {
        fetch('/arena/get_characters')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('Characters data fetched:', data);
                const player1Name = document.getElementById('player1-name');
                const player2Name = document.getElementById('player2-name');
                const player1Image = document.getElementById('player1-image');
                const player2Image = document.getElementById('player2-image');
                const player1Description = document.getElementById('player1-description');
                const player2Description = document.getElementById('player2-description');

                if (!player1Name || !player2Name || !player1Image || !player2Image || !player1Description || !player2Description) {
                    console.error('One or more elements for characters are missing');
                    return;
                }

                if (data.length > 0) {
                    console.log('Player 1 data:', data[0]);
                    player1Name.textContent = data[0].name;
                    player1Image.src = `/static/${data[0].image_url}`;
                    player1Description.textContent = data[0].description;
                    createChart('player1-stats', data[0].stats);
                } else {
                    console.log('No data for Player 1');
                }

                if (data.length > 1) {
                    console.log('Player 2 data:', data[1]);
                    player2Name.textContent = data[1].name;
                    player2Image.src = `/static/${data[1].image_url}`;
                    player2Description.textContent = data[1].description;
                    createChart('player2-stats', data[1].stats);
                } else {
                    console.log('No data for Player 2');
                }

                if (data.length === 0) {
                    console.log('No data available, using default images');
                    player1Name.textContent = 'Player 1';
                    player2Name.textContent = 'Player 2';
                    player1Image.src = '/static/images/default/player1.png';
                    player2Image.src = '/static/images/default/player2.png';
                    player1Description.textContent = 'Player 1 description';
                    player2Description.textContent = 'Player 2 description';
                }
            })
            .catch(error => {
                console.error('Error fetching characters:', error);
                const player1Name = document.getElementById('player1-name');
                const player2Name = document.getElementById('player2-name');
                const player1Image = document.getElementById('player1-image');
                const player2Image = document.getElementById('player2-image');
                const player1Description = document.getElementById('player1-description');
                const player2Description = document.getElementById('player2-description');

                if (!player1Name || !player2Name || !player1Image || !player2Image || !player1Description || !player2Description) {
                    console.error('One or more elements for default characters are missing');
                    return;
                }

                console.log('Error fetching data, using default images');
                player1Name.textContent = 'Player 1';
                player2Name.textContent = 'Player 2';
                player1Image.src = '/static/images/default/player1.png';
                player2Image.src = '/static/images/default/player2.png';
                player1Description.textContent = 'Player 1 description';
                player2Description.textContent = 'Player 2 description';
            });
    }

    function createChart(canvasId, stats) {
        console.log(`Creating chart for canvas ${canvasId} with stats:`, stats);
        const ctx = document.getElementById(canvasId).getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(stats),
                datasets: [{
                    label: 'Attributes',
                    data: Object.values(stats),
                    backgroundColor: 'rgba(34, 139, 34, 0.8)',
                    borderColor: 'rgba(34, 139, 34, 1)',
                    borderWidth: 1
                }]
            },
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
    }

    function addMessageToArenaChat(message, sender, user_id) {
        const chatBox = document.getElementById('arena-chat-box');
        const messageElement = document.createElement('div');
        messageElement.classList.add('arena-chat-message');
        const timestamp = new Date().toLocaleTimeString();
        messageElement.innerHTML = `<p>${message}</p><span class="timestamp">${timestamp} - ${user_id}</span>`;

        if (user_id === getCookie('user_id')) {
            messageElement.classList.add('right');
        } else {
            messageElement.classList.add('left');
        }

        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function fetchArenaChatMessages() {
        fetch('/arena/get_arena_chat')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('Arena chat data fetched:', data);
                const chatBox = document.getElementById('arena-chat-box');
                chatBox.innerHTML = '';

                data.forEach(msg => {
                    addMessageToArenaChat(msg.content, msg.sender, msg.user_id);
                });
            })
            .catch(error => {
                console.error('Error fetching arena chat messages:', error);
            });
    }

    function sendArenaChatMessage(content, sender) {
        const user_id = getCookie('user_id');
        fetch('/arena/send_arena_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content, sender, user_id })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('Message sent:', data);
                fetchArenaChatMessages();
            })
            .catch(error => {
                console.error('Error sending arena chat message:', error);
            });
    }

    function addMessageToTacticsChat(message, sender, user_id) {
        const chatBox = document.getElementById('tactics-chat-box');
        const messageElement = document.createElement('div');
        messageElement.classList.add('tactics-chat-message');
        const timestamp = new Date().toLocaleTimeString();
        messageElement.innerHTML = `<p>${message}</p><span class="timestamp">${timestamp} - ${user_id}</span>`;

        if (user_id === getCookie('user_id')) {
            messageElement.classList.add('right');
        } else {
            messageElement.classList.add('left');
        }

        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function fetchTacticsChatMessages() {
        fetch('/arena/get_tactics_chat')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('Tactics chat data fetched:', data);
                const chatBox = document.getElementById('tactics-chat-box');
                chatBox.innerHTML = '';

                data.forEach(msg => {
                    addMessageToTacticsChat(msg.content, msg.sender, msg.user_id);
                });
            })
            .catch(error => {
                console.error('Error fetching tactics chat messages:', error);
            });
    }

    function sendTacticsChatMessage(content, sender) {
        const user_id = getCookie('user_id');
        fetch('/arena/send_tactics_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content, sender, user_id })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('Message sent:', data);
                fetchTacticsChatMessages();
            })
            .catch(error => {
                console.error('Error sending tactics chat message:', error);
            });
    }

    const tacticsChatForm = document.getElementById('tactics-chat-form');
    tacticsChatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const tacticsChatInput = document.getElementById('tactics-chat-input');
        const message = tacticsChatInput.value;
        const sender = 'user';

        if (message.trim() !== '') {
            sendTacticsChatMessage(message, sender);
            tacticsChatInput.value = '';
        }
    });

    function addMessageToGeneralChat(message, sender, user_id) {
        const chatBox = document.getElementById('general-chat-box');
        const messageElement = document.createElement('div');
        messageElement.classList.add('general-chat-message');
        const timestamp = new Date().toLocaleTimeString();
        messageElement.innerHTML = `<p>${message}</p><span class="timestamp">${timestamp} - ${user_id}</span>`;

        if (user_id === getCookie('user_id')) {
            messageElement.classList.add('right');
        } else {
            messageElement.classList.add('left');
        }

        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function fetchGeneralChatMessages() {
        fetch('/arena/get_general_chat')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('General chat data fetched:', data);
                const chatBox = document.getElementById('general-chat-box');
                chatBox.innerHTML = '';

                data.forEach(msg => {
                    addMessageToGeneralChat(msg.content, msg.sender, msg.user_id);
                });
            })
            .catch(error => {
                console.error('Error fetching general chat messages:', error);
            });
    }

    function sendGeneralChatMessage(content, sender) {
        const user_id = getCookie('user_id');
        fetch('/arena/send_general_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content, sender, user_id })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('Message sent:', data);
                fetchGeneralChatMessages();
            })
            .catch(error => {
                console.error('Error sending general chat message:', error);
            });
    }

    const generalChatForm = document.getElementById('general-chat-form');
    generalChatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const generalChatInput = document.getElementById('general-chat-input');
        const message = generalChatInput.value;
        const sender = 'viewer';

        if (message.trim() !== '') {
            sendGeneralChatMessage(message, sender);
            generalChatInput.value = '';
        }
    });

    function loadGeneralChat() {
        fetch('/arena/get_general_chat')
            .then(response => response.json())
            .then(data => {
                const chatBox = document.getElementById('general-chat-box');
                chatBox.innerHTML = '';
                data.forEach(msg => {
                    const msgElement = document.createElement('div');
                    msgElement.classList.add('general-chat-message');
                    msgElement.classList.add(msg.user_id === getCookie('user_id') ? 'right' : 'left');
                    msgElement.innerHTML = `<p>${msg.content}</p><span class="timestamp">${msg.timestamp} - ${msg.user_id}</span>`;
                    chatBox.appendChild(msgElement);
                });
                chatBox.scrollTop = chatBox.scrollHeight;
            });
    }

    fetchGeneralChatMessages();
    fetchTacticsChatMessages();
    loadGeneralChat();
});
