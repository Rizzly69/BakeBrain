// Chart.js configuration and initialization for Smart Bakery Management

// Chart.js default configuration
Chart.defaults.color = '#b0b0b0';
Chart.defaults.backgroundColor = 'rgba(0, 255, 255, 0.1)';
Chart.defaults.borderColor = '#00ffff';

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
});

function initializeCharts() {
    // Sales Chart
    const salesChart = document.getElementById('salesChart');
    if (salesChart) {
        createSalesChart(salesChart);
    }
    
    // Orders Chart
    const ordersChart = document.getElementById('ordersChart');
    if (ordersChart) {
        createOrdersChart(ordersChart);
    }
    
    // Inventory Chart
    const inventoryChart = document.getElementById('inventoryChart');
    if (inventoryChart) {
        createInventoryChart(inventoryChart);
    }
    
    // Revenue Trend Chart
    const revenueTrendChart = document.getElementById('revenueTrendChart');
    if (revenueTrendChart) {
        createRevenueTrendChart(revenueTrendChart);
    }
}

function createSalesChart(canvas) {
    const ctx = canvas.getContext('2d');
    
    // Sample data - replace with actual data from your backend
    const salesData = {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
            label: 'Daily Sales',
            data: [120, 190, 300, 500, 200, 300, 450],
            backgroundColor: 'rgba(0, 255, 255, 0.1)',
            borderColor: '#00ffff',
            borderWidth: 2,
            fill: true,
            tension: 0.4
        }]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: salesData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#00ffff'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#b0b0b0',
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#b0b0b0'
                    }
                }
            }
        }
    });
}

function createOrdersChart(canvas) {
    const ctx = canvas.getContext('2d');
    
    const orderData = {
        labels: ['Pending', 'Confirmed', 'In Progress', 'Ready', 'Delivered'],
        datasets: [{
            data: [15, 25, 10, 8, 42],
            backgroundColor: [
                '#ffaa00',
                '#00aaff',
                '#8a2be2',
                '#00ff88',
                '#00ffff'
            ],
            borderWidth: 2,
            borderColor: '#1a1a1a'
        }]
    };
    
    new Chart(ctx, {
        type: 'doughnut',
        data: orderData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#b0b0b0',
                        padding: 20
                    }
                }
            }
        }
    });
}

function createInventoryChart(canvas) {
    const ctx = canvas.getContext('2d');
    
    const inventoryData = {
        labels: ['Bread', 'Pastries', 'Cakes', 'Cookies', 'Donuts', 'Muffins'],
        datasets: [{
            label: 'Stock Level',
            data: [85, 45, 30, 75, 60, 40],
            backgroundColor: [
                'rgba(0, 255, 255, 0.6)',
                'rgba(255, 0, 255, 0.6)',
                'rgba(0, 255, 0, 0.6)',
                'rgba(255, 255, 0, 0.6)',
                'rgba(138, 43, 226, 0.6)',
                'rgba(255, 170, 0, 0.6)'
            ],
            borderColor: [
                '#00ffff',
                '#ff00ff',
                '#00ff00',
                '#ffff00',
                '#8a2be2',
                '#ffaa00'
            ],
            borderWidth: 2
        }]
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: inventoryData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#b0b0b0',
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#b0b0b0'
                    }
                }
            }
        }
    });
}

function createRevenueTrendChart(canvas) {
    const ctx = canvas.getContext('2d');
    
    const revenueData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [
            {
                label: 'Regular Orders',
                data: [1200, 1900, 3000, 5000, 2000, 3000],
                backgroundColor: 'rgba(0, 255, 255, 0.1)',
                borderColor: '#00ffff',
                borderWidth: 2,
                fill: false
            },
            {
                label: 'Catering Orders',
                data: [800, 1200, 1500, 2200, 1800, 2500],
                backgroundColor: 'rgba(255, 0, 255, 0.1)',
                borderColor: '#ff00ff',
                borderWidth: 2,
                fill: false
            }
        ]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: revenueData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#b0b0b0'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#b0b0b0',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#b0b0b0'
                    }
                }
            }
        }
    });
}

// Function to update chart data dynamically
function updateChartData(chartId, newData) {
    const canvas = document.getElementById(chartId);
    if (canvas && canvas.chart) {
        const chart = canvas.chart;
        chart.data = newData;
        chart.update();
    }
}

// Function to create a real-time updating chart
function createRealTimeChart(canvas, type = 'line') {
    const ctx = canvas.getContext('2d');
    
    const config = {
        type: type,
        data: {
            labels: [],
            datasets: [{
                label: 'Real-time Data',
                data: [],
                backgroundColor: 'rgba(0, 255, 255, 0.1)',
                borderColor: '#00ffff',
                borderWidth: 2,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#b0b0b0'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#b0b0b0'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#b0b0b0'
                    }
                }
            },
            animation: {
                duration: 750
            }
        }
    };
    
    const chart = new Chart(ctx, config);
    canvas.chart = chart;
    
    return chart;
}

// Function to add data point to real-time chart
function addDataPoint(chartId, label, value) {
    const canvas = document.getElementById(chartId);
    if (canvas && canvas.chart) {
        const chart = canvas.chart;
        
        // Add new data point
        chart.data.labels.push(label);
        chart.data.datasets[0].data.push(value);
        
        // Keep only last 20 data points
        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }
        
        chart.update('none'); // Update without animation for real-time feel
    }
}

// Export functions for use in other scripts
window.chartUtils = {
    updateChartData,
    createRealTimeChart,
    addDataPoint
};
