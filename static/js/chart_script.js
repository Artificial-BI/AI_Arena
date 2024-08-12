function createChart(ctx, traits) {
    // Define background and border colors for specific traits
    const backgroundColors = [];
    const borderColors = [];

    for (const key of Object.keys(traits)) {
        if (key === 'Life') {
            backgroundColors.push('rgba(64, 224, 208, 0.8)'); // Turquoise for Life
            borderColors.push('rgba(64, 224, 208, 1)');
        } else if (key === 'Combat') {
            backgroundColors.push('rgba(255, 100, 30, 0.8)'); // Orange for Combat
            borderColors.push('rgba(255, 100, 30, 1)');
        } else if (key === 'Damage') {
            backgroundColors.push('rgba(255, 255, 0, 0.8)'); // Yellow for Damage
            borderColors.push('rgba(255, 255, 0, 1)');
        } else {
            backgroundColors.push('rgba(34, 139, 34, 0.8)'); // Green for other traits
            borderColors.push('rgba(34, 139, 34, 1)');
        }
    }

    // Create the chart
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(traits), // Trait names
            datasets: [{
                label: '', // No label for the chart
                data: Object.values(traits), // Trait values
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // Make chart height adaptive
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: false // Hide X-axis label
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: false // Hide Y-axis label
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
                    display: false // Hide the chart legend
                }
            }
        },
        plugins: [{
            afterDatasetsDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.font = '8px Arial';
                ctx.fillStyle = 'white'; // Set text color to white
                chart.data.datasets.forEach(function(dataset, i) {
                    const meta = chart.getDatasetMeta(i);
                    meta.data.forEach(function(bar, index) {
                        const data = dataset.data[index];
                        if (data !== 0) {
                            ctx.fillText(data, bar.x - 5, bar.y - 5); // Display values on the bars
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
