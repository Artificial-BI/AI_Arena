document.addEventListener('DOMContentLoaded', function() {
    const startTestBattleButton = document.getElementById('start-test-battle');
    const startTacticsButton = document.getElementById('start-tactics');
    const tacticsChatForm = document.getElementById('tactics-chat-form');
    const tacticsChatBox = document.getElementById('tactics-chat-box');
    const generalChatForm = document.getElementById('general-chat-form');
    const generalChatBox = document.getElementById('general-chat-box');
    const playersTable = document.getElementById('players-table');
    const arenaChatBox = document.getElementById('arena-chat-box');
    const tooltip = document.getElementById('tooltip');

    console.log("Document loaded");

    startTestBattleButton.addEventListener('click', function() {
        fetch('/arena/start_test_battle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'Test battle started') {
                console.log('Test battle started successfully');
            } else {
                console.error('Failed to start test battle:', data.error);
            }
        })
        .catch(error => console.error('Error:', error));
    });

    startTacticsButton.addEventListener('click', function() {
        fetch('/arena/start_tactics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'Tactics generated' || data.status === 'Unread tactics messages present') {
                console.log('Tactics started successfully:', data.response || 'Unread messages present');
            } else {
                console.error('Failed to start tactics:', data.error);
            }
        })
        .catch(error => console.error('Error:', error));
    });

    tacticsChatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const messageInput = document.getElementById('tactics-chat-input');
        const message = messageInput.value.trim();

        if (!message) {
            alert('Введите сообщение перед отправкой.');
            return;
        }

        fetch('/arena/send_tactics_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: message, sender: 'user', user_id: user_id })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'Message sent') {
                const messageElement = document.createElement('div');
                messageElement.className = 'chat-message right';
                messageElement.innerHTML = `<p>${message}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                tacticsChatBox.appendChild(messageElement);

                const responseElement = document.createElement('div');
                responseElement.className = 'chat-message left';
                responseElement.innerHTML = `<p>${data.response}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                tacticsChatBox.appendChild(responseElement);

                messageInput.value = '';
                tacticsChatBox.scrollTop = tacticsChatBox.scrollHeight;
            }
        })
        .catch(error => console.error('Error:', error));
    });

    generalChatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const messageInput = document.getElementById('general-chat-input');
        const message = messageInput.value.trim();

        if (!message) {
            alert('Введите сообщение перед отправкой.');
            return;
        }

        fetch('/arena/send_general_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: message, sender: 'user', user_id: user_id })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'Message sent') {
                const messageElement = document.createElement('div');
                messageElement.className = 'chat-message right';
                messageElement.innerHTML = `<p>${message}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                generalChatBox.appendChild(messageElement);

                const responseElement = document.createElement('div');
                responseElement.className = 'chat-message left';
                responseElement.innerHTML = `<p>${data.response}</p><span class="timestamp">${new Date().toLocaleString()}</span>`;
                generalChatBox.appendChild(responseElement);

                messageInput.value = '';
                generalChatBox.scrollTop = generalChatBox.scrollHeight;
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Function to create chart for character traits
    function createChart(ctx, traits) {
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(traits),
                datasets: [{
                    label: 'Attributes',
                    data: Object.values(traits),
                    backgroundColor: 'rgba(34, 139, 34, 0.8)',
                    borderColor: 'rgba(34, 139, 34, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
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

    function loadCharacterCharts() {
        document.querySelectorAll('tbody tr').forEach((row, index) => {
            const traits = JSON.parse(row.dataset.traits);
            const canvas = document.getElementById(`traits-chart-${index + 1}`);
            createChart(canvas.getContext('2d'), traits);
        });
    }

    playersTable.addEventListener('mouseover', function(event) {
        if (event.target.tagName === 'IMG' && event.target.classList.contains('character-image')) {
            const description = event.target.dataset.description;
            tooltip.innerHTML = description;
            tooltip.style.display = 'block';
            tooltip.style.left = `${event.pageX + 10}px`;
            tooltip.style.top = `${event.pageY + 10}px`;
        }
    });

    playersTable.addEventListener('mouseout', function(event) {
        if (event.target.tagName === 'IMG' && event.target.classList.contains('character-image')) {
            tooltip.style.display = 'none';
        }
    });

    playersTable.addEventListener('mousemove', function(event) {
        if (tooltip.style.display === 'block') {
            tooltip.style.left = `${event.pageX + 10}px`;
            tooltip.style.top = `${event.pageY + 10}px`;
        }
    });

    // Initial load of chat messages
    function loadChatMessages() {
        fetch('/arena/get_arena_chat')
        .then(response => response.json())
        .then(data => {
            data.forEach(msg => {
                const messageElement = document.createElement('div');
                messageElement.className = `chat-message ${msg.sender === 'user' ? 'right' : 'left'}`;
                messageElement.innerHTML = `<p>${msg.content}</p><span class="timestamp">${new Date(msg.timestamp).toLocaleString()}</span>`;
                arenaChatBox.appendChild(messageElement);
            });
            arenaChatBox.scrollTop = arenaChatBox.scrollHeight;
        })
        .catch(error => console.error('Error loading arena chat messages:', error));

        fetch('/arena/get_tactics_chat')
        .then(response => response.json())
        .then(data => {
            if (Array.isArray(data)) {
                data.forEach(msg => {
                    const messageElement = document.createElement('div');
                    messageElement.className = `chat-message ${msg.sender === 'user' ? 'right' : 'left'}`;
                    messageElement.innerHTML = `<p>${msg.content}</p><span class="timestamp">${new Date(msg.timestamp).toLocaleString()}</span>`;
                    tacticsChatBox.appendChild(messageElement);
                });
                tacticsChatBox.scrollTop = tacticsChatBox.scrollHeight;
            } else {
                console.error('Unexpected data format:', data);
            }
        })
        .catch(error => console.error('Error loading tactics chat messages:', error));

        fetch('/arena/get_general_chat')
        .then(response => response.json())
        .then(data => {
            data.forEach(msg => {
                const messageElement = document.createElement('div');
                messageElement.className = `chat-message ${msg.sender === 'user' ? 'right' : 'left'}`;
                messageElement.innerHTML = `<p>${msg.content}</p><span class="timestamp">${new Date(msg.timestamp).toLocaleString()}</span>`;
                generalChatBox.appendChild(messageElement);
            });
            generalChatBox.scrollTop = generalChatBox.scrollHeight;
        })
        .catch(error => console.error('Error loading general chat messages:', error));
    }

    loadChatMessages();
    loadCharacterCharts();
});
