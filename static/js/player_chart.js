function createChart(ctx, traits) {
    const backgroundColors = [];
    const borderColors = [];

    for (const key of Object.keys(traits)) {
        if (key === 'Life') {
            backgroundColors.push('rgba(64, 224, 208, 0.8)');
            borderColors.push('rgba(64, 224, 208, 1)');
        } else if (key === 'Combat') {
            backgroundColors.push('rgba(255, 100, 30, 0.8)');
            borderColors.push('rgba(255, 100, 30, 1)');
        } else if (key === 'Damage') {
            backgroundColors.push('rgba(255, 255, 0, 0.8)');
            borderColors.push('rgba(255, 255, 0, 1)');
        } else {
            backgroundColors.push('rgba(34, 139, 34, 0.8)');
            borderColors.push('rgba(34, 139, 34, 1)');
        }
    }

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(traits),
            datasets: [{
                label: '',
                data: Object.values(traits),
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { beginAtZero: true, title: { display: false }},
                y: { beginAtZero: true, title: { display: false }, max: 100 }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(tooltipItem) {
                            return tooltipItem.label + ': ' + tooltipItem.raw + '%';
                        }
                    }
                },
                legend: { display: false }
            }
        },
        plugins: [{
            afterDatasetsDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.font = '8px Arial';
                ctx.fillStyle = 'white';
                chart.data.datasets.forEach(function(dataset, i) {
                    const meta = chart.getDatasetMeta(i);
                    meta.data.forEach(function(bar, index) {
                        const data = dataset.data[index];
                        if (data !== 0) {
                            ctx.fillText(data, bar.x - 5, bar.y - 5);
                        }
                    });
                });
            }
        }]
    });
}

function displayCharacterStats(traits) {
    const ctx = document.getElementById('character-chart').getContext('2d');
    if (ctx) {
        if (window.characterChart) {
            window.characterChart.destroy();
        }
        window.characterChart = createChart(ctx, traits);
    }
}

// document.addEventListener('DOMContentLoaded', function() {
//     if (selectedCharacterTraits) {
//         console.log("3 --- traits:", selectedCharacterTraits);

//         displayCharacterStats(selectedCharacterTraits);
//     }

//     document.querySelectorAll('tbody tr').forEach((row, index) => {
//         const traitsData = row.dataset.traits;
//         if (traitsData) {
//             try {
//                 const traits = JSON.parse(traitsData);
//                 const canvas = document.getElementById(`traits-chart-${index + 1}`);
//                 if (canvas) {
//                     createChart(canvas.getContext('2d'), traits);
//                 }
//             } catch (e) {
//                 console.error('Error parsing traits data:', e);
//             }
//         }
//     });
// });
