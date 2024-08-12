
function createChart(ctx, traits) {
    // Используем данные, которые поступают из базы данных
    // Обновляем цвета для баров
    const backgroundColors = [];
    const borderColors = [];

    for (const key of Object.keys(traits)) {
        if (key === 'Life') {
            backgroundColors.push('rgba(64, 224, 208, 0.8)'); // Бирюзовый для Life
            borderColors.push('rgba(64, 224, 208, 1)');
        } else if (key === 'Combat') {
            backgroundColors.push('rgba(255, 100, 30, 0.8)'); // Оранжевый для Combat
            borderColors.push('rgba(255, 100, 30, 1)');
        } else if (key === 'Damage') {
            backgroundColors.push('rgba(255, 255, 0, 0.8)'); // Желтый для Damage
            borderColors.push('rgba(255, 255, 0, 1)');
        } else {
            backgroundColors.push('rgba(34, 139, 34, 0.8)'); // Зеленый для остальных
            borderColors.push('rgba(34, 139, 34, 1)');
        }
    }

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(traits),
            datasets: [{
                label: '', // Убираем название графика
                data: Object.values(traits),
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // График адаптируется по высоте
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: false // Убираем подпись оси X
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: false // Убираем подпись оси Y
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
                    display: false // Убираем легенду графика
                }
            }
        },
        plugins: [{
            afterDatasetsDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.font = '8px Arial';
                ctx.fillStyle = 'white'; // Изменяем цвет текста на белый
                chart.data.datasets.forEach(function(dataset, i) {
                    const meta = chart.getDatasetMeta(i);
                    meta.data.forEach(function(bar, index) {
                        const data = dataset.data[index];
                        if (data !== 0) {
                            ctx.fillText(data, bar.x - 5, bar.y - 5); // Выводим значение на белом фоне
                        }
                    });
                });
            }
        }]
    });
}

function loadCharacterCharts() {
    document.querySelectorAll('tbody tr').forEach((row, index) => {
        const traitsData = row.dataset.traits;
        if (traitsData) {
            try {
                const traits = JSON.parse(traitsData);
                const canvas = document.getElementById(`traits-chart-${index + 1}`);
                if (canvas) {
                    createChart(canvas.getContext('2d'), traits);
                }
            } catch (e) {
                console.error('Error parsing traits data:', e);
            }
        }
    });
}
