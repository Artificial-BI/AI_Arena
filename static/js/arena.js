// arena.js

document.addEventListener('DOMContentLoaded', function() {
    const startTestBattleButton = document.getElementById('start-test-battle');

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
                alert('Test battle started successfully!');
                // Optionally, you can reload or update the page to reflect the battle start
            } else {
                alert('Error starting test battle: ' + data.error);
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Existing code for fetching and displaying chat messages, etc.
    fetchCharacters();
    fetchArenaChatMessages();
    fetchTacticsChatMessages();
    fetchGeneralChatMessages();
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

// Existing functions for fetching and displaying chat messages (fetchArenaChatMessages, fetchTacticsChatMessages, fetchGeneralChatMessages)
