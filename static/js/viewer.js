document.addEventListener('DOMContentLoaded', function() {
    fetchCharacters();
    fetchBattleUpdates();
    fetchBattleImages();
    fetchChatMessages();

    function fetchCharacters() {
        fetch('/get_characters')
            .then(response => response.json())
            .then(data => {
                console.log('Characters data fetched:', data);  // Логирование
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
                    player1Name.textContent = data[0].name;
                    player1Image.src = `/static/${data[0].image_url}`;
                    player1Description.textContent = data[0].description;
                    createChart('player1-stats', data[0].stats);
                }

                if (data.length > 1) {
                    player2Name.textContent = data[1].name;
                    player2Image.src = `/static/${data[1].image_url}`;
                    player2Description.textContent = data[1].description;
                    createChart('player2-stats', data[1].stats);
                }

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

                if (!player1Name || !player2Name || !player1Image || !player2Image || !player1Description || !player2Description) {
                    console.error('One or more elements for default characters are missing');
                    return;
                }

                player1Name.textContent = 'Игрок 1';
                player2Name.textContent = 'Игрок 2';
                player1Image.src = '/static/images/default/player1.png';
                player2Image.src = '/static/images/default/player2.png';
                player1Description.textContent = 'Описание игрока 1';
                player2Description.textContent = 'Описание игрока 2';
            });
    }

    function createChart(canvasId, stats) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(stats),
                datasets: [{
                    label: 'Характеристики',
                    data: Object.values(stats),
                    backgroundColor: 'rgba(34, 139, 34, 0.8)',  // Темно-зеленый цвет баров
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
                            text: 'Характеристики'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Значения'
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
                            if (data !== 0) { // Отображать только ненулевые значения
                                ctx.fillText(data, bar.x, bar.y - 5);
                            }
                        });
                    });
                }
            }]
        });
    }

    // Остальные функции fetchBattleUpdates, fetchBattleImages, fetchChatMessages остаются без изменений

    setInterval(fetchBattleUpdates, 5000); // Обновлять каждые 5 секунд
    setInterval(fetchBattleImages, 30000); // Обновлять каждые 30 секунд
    setInterval(fetchChatMessages, 5000); // Обновлять сообщения чата каждые 5 секунд
});
