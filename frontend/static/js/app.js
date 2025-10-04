// Globální proměnné
let socket = null;
let currentRegion = 'CZ';
let charts = {};
let autoRefreshInterval = null;
let lastResults = {};

// Barvy pro strany
const partyColors = [
    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
    '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384',
    '#36A2EB', '#FFCE56', '#9966FF', '#FF9F40', '#C9CBCF'
];

// Inicializace aplikace
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Inicializace WebSocket
    initializeWebSocket();
    
    // Načtení regionů
    loadRegions();
    
    // Načtení stran pro filtry
    loadParties();
    
    // Nastavení event listenerů
    setupEventListeners();
    
    // Inicializace grafů
    initializeCharts();
    
    // Spuštění auto-refresh
    startAutoRefresh();
    
    // Aktualizace času
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    
    // Načtení počátečních dat
    loadCurrentResults();
}

function initializeWebSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to WebSocket');
        document.getElementById('connection-status').textContent = 'Connected';
        document.getElementById('connection-status').className = 'status-badge connected';
        
        // Přihlášení k odběru aktualizací
        socket.emit('subscribe', { region: currentRegion });
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from WebSocket');
        document.getElementById('connection-status').textContent = 'Disconnected';
        document.getElementById('connection-status').className = 'status-badge disconnected';
    });
    
    socket.on('update', function(data) {
        console.log('Received update:', data);
        handleRealtimeUpdate(data);
    });
    
    socket.on('time_series_data', function(data) {
        updateTimelineChart(data);
    });
    
    socket.on('counting_speed_data', function(data) {
        updateCountingSpeed(data);
    });
}

function setupEventListeners() {
    // Změna regionu
    document.getElementById('region-select').addEventListener('change', function(e) {
        currentRegion = e.target.value;
        changeRegion(currentRegion);
    });
    
    // Změna typu zobrazení
    document.getElementById('view-type').addEventListener('change', function(e) {
        switchView(e.target.value);
    });
    
    // Tlačítko refresh
    document.getElementById('refresh-btn').addEventListener('click', function() {
        refreshData();
    });
    
    // Export CSV
    document.getElementById('export-csv').addEventListener('click', function() {
        exportData('csv');
    });
    
    // Export JSON
    document.getElementById('export-json').addEventListener('click', function() {
        exportData('json');
    });
    
    // Timeline range
    document.getElementById('timeline-range').addEventListener('change', function(e) {
        const value = e.target.value;
        if (value === 'all') {
            loadAllTimelineData();
        } else {
            loadTimelineData(parseInt(value));
        }
    });
    
    // Zoom controls
    document.getElementById('zoom-reset').addEventListener('click', function() {
        if (charts.timeline) {
            charts.timeline.resetZoom();
        }
    });
    
    document.getElementById('zoom-in').addEventListener('click', function() {
        if (charts.timeline) {
            charts.timeline.zoom(1.1);
        }
    });
    
    document.getElementById('zoom-out').addEventListener('click', function() {
        if (charts.timeline) {
            charts.timeline.zoom(0.9);
        }
    });
    
    document.getElementById('pan-left').addEventListener('click', function() {
        if (charts.timeline) {
            charts.timeline.pan({x: -50}, undefined, 'default');
        }
    });
    
    document.getElementById('pan-right').addEventListener('click', function() {
        if (charts.timeline) {
            charts.timeline.pan({x: 50}, undefined, 'default');
        }
    });
    
    // Party filter pro kandidáty
    document.getElementById('party-filter').addEventListener('change', function(e) {
        loadCandidates(e.target.value);
    });
    
    // Total votes range
    document.getElementById('totalvotes-range').addEventListener('change', function(e) {
        const value = e.target.value;
        if (value === 'all') {
            loadAllTotalVotesData();
        } else {
            loadTotalVotesData(parseInt(value));
        }
    });
}

function initializeCharts() {
    // Graf aktuálních výsledků
    const resultsCtx = document.getElementById('results-chart').getContext('2d');
    charts.results = new Chart(resultsCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Votes',
                data: [],
                backgroundColor: partyColors
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Party Results'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
    
    // Timeline graf s kombinovaným volume a zoom/pan
    const timelineCtx = document.getElementById('timeline-chart').getContext('2d');
    charts.timeline = new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        filter: function(item, chart) {
                            // Skrýt volume z legendy
                            return !item.text.includes('Volume');
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.type === 'bar') {
                                return 'New votes: ' + context.parsed.y.toLocaleString();
                            }
                            return context.dataset.label + ': ' + context.parsed.y?.toFixed(1) + '%';
                        }
                    }
                },
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: true,
                            speed: 0.1
                        },
                        drag: {
                            enabled: true,
                            backgroundColor: 'rgba(102, 126, 234, 0.1)'
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x',
                        onZoomComplete: function({chart}) {
                            console.log('Zoomed to:', chart.scales.x.min, '-', chart.scales.x.max);
                        }
                    },
                    pan: {
                        enabled: true,
                        mode: 'x',
                        onPanComplete: function({chart}) {
                            console.log('Panned to:', chart.scales.x.min, '-', chart.scales.x.max);
                        }
                    },
                    limits: {
                        x: {min: 'original', max: 'original'},
                        y: {min: 'original', max: 'original'}
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 15,
                        font: {
                            size: 10
                        }
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    beginAtZero: false,
                    min: 0,
                    max: 40, // Maximální procenta pro lepší zobrazení
                    title: {
                        display: true,
                        text: 'Party Support (%)',
                        font: {
                            size: 11
                        }
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    max: function(context) {
                        // Dynamicky nastavit max pro volume na 30% maxima
                        const datasets = context.chart.data.datasets;
                        const volumeDataset = datasets.find(d => d.type === 'bar');
                        if (volumeDataset && volumeDataset.data.length > 0) {
                            const maxVolume = Math.max(...volumeDataset.data.filter(v => v != null));
                            return maxVolume * 3.5; // Volume zabere max 30% výšky grafu
                        }
                        return 1000000;
                    },
                    title: {
                        display: true,
                        text: 'New Votes (Volume)',
                        font: {
                            size: 11
                        }
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        callback: function(value) {
                            if (value >= 1000000) {
                                return (value / 1000000).toFixed(1) + 'M';
                            }
                            if (value >= 1000) {
                                return (value / 1000).toFixed(0) + 'k';
                            }
                            return value;
                        }
                    }
                }
            }
        }
    });
    
    // Comparison graf
    const comparisonCtx = document.getElementById('comparison-chart').getContext('2d');
    charts.comparison = new Chart(comparisonCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Regional Comparison'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Percentage'
                    }
                }
            }
        }
    });
    
    // Total Votes graf - zobrazuje absolutní počty hlasů pro každou stranu
    const totalVotesCtx = document.getElementById('totalvotes-chart').getContext('2d');
    charts.totalVotes = new Chart(totalVotesCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        boxWidth: 12,
                        padding: 10,
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            let result = label + ': ' + value.toLocaleString() + ' votes';
                            
                            // Přidat změnu od předchozí minuty
                            if (context.dataIndex > 0) {
                                const prevValue = context.dataset.data[context.dataIndex - 1] || 0;
                                const diff = value - prevValue;
                                if (diff > 0) {
                                    result += ' (+' + diff.toLocaleString() + ')';
                                } else if (diff < 0) {
                                    result += ' (' + diff.toLocaleString() + ')';
                                }
                            }
                            return result;
                        }
                    }
                },
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: true,
                            speed: 0.1
                        },
                        drag: {
                            enabled: true,
                            backgroundColor: 'rgba(102, 126, 234, 0.1)'
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x',
                    },
                    pan: {
                        enabled: true,
                        mode: 'x',
                    },
                    limits: {
                        x: {min: 'original', max: 'original'},
                        y: {min: 0, max: 'original'}
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 15,
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Total Votes',
                        font: {
                            size: 12
                        }
                    },
                    ticks: {
                        callback: function(value) {
                            if (value >= 1000000) {
                                return (value / 1000000).toFixed(1) + 'M';
                            }
                            if (value >= 1000) {
                                return (value / 1000).toFixed(0) + 'k';
                            }
                            return value;
                        }
                    }
                }
            }
        }
    });
    
    // Prediction graf
    const predictionCtx = document.getElementById('prediction-chart').getContext('2d');
    charts.prediction = new Chart(predictionCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                label: 'Predicted Results',
                data: [],
                backgroundColor: partyColors
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

function loadRegions() {
    fetch('/api/regions')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('region-select');
            const checkboxContainer = document.getElementById('region-checkboxes');
            
            // Clear existing options
            select.innerHTML = '<option value="CZ">Czech Republic (Total)</option>';
            checkboxContainer.innerHTML = '';
            
            // Skupiny regionů
            const krajRegions = data.regions.filter(r => r.type === 'kraj');
            const okresRegions = data.regions.filter(r => r.type === 'okres');
            
            // Přidat kraje
            if (krajRegions.length > 0) {
                const krajGroup = document.createElement('optgroup');
                krajGroup.label = 'Regions (Kraje)';
                krajRegions.forEach(region => {
                    const option = document.createElement('option');
                    option.value = region.code;
                    option.textContent = region.name;
                    krajGroup.appendChild(option);
                });
                select.appendChild(krajGroup);
            }
            
            // Přidat okresy
            if (okresRegions.length > 0) {
                const okresGroup = document.createElement('optgroup');
                okresGroup.label = 'Districts (Okresy)';
                okresRegions.forEach(region => {
                    const option = document.createElement('option');
                    option.value = region.code;
                    option.textContent = region.name;
                    okresGroup.appendChild(option);
                });
                select.appendChild(okresGroup);
            }
            
            // Checkboxy pro porovnání
            krajRegions.forEach(region => {
                const checkbox = document.createElement('div');
                checkbox.className = 'region-checkbox';
                checkbox.innerHTML = `
                    <input type="checkbox" id="region-${region.code}" value="${region.code}" onchange="loadComparisonData()">
                    <label for="region-${region.code}">${region.name}</label>
                `;
                checkboxContainer.appendChild(checkbox);
            });
            
            // Přidat checkbox pro celou ČR
            const czCheckbox = document.createElement('div');
            czCheckbox.className = 'region-checkbox';
            czCheckbox.innerHTML = `
                <input type="checkbox" id="region-CZ" value="CZ" checked onchange="loadComparisonData()">
                <label for="region-CZ">Czech Republic (Total)</label>
            `;
            checkboxContainer.insertBefore(czCheckbox, checkboxContainer.firstChild);
        });
}

function loadParties() {
    fetch('/api/parties')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('party-filter');
            select.innerHTML = '<option value="">All Parties</option>';
            
            data.parties.forEach(party => {
                const option = document.createElement('option');
                option.value = party.code;
                option.textContent = party.name;
                select.appendChild(option);
            });
        });
}

function loadCurrentResults() {
    fetch(`/api/current_results?region=${currentRegion}`)
        .then(response => response.json())
        .then(data => {
            updateResultsDisplay(data);
            loadProgress();
            loadPredictions();
            // Vždy použít REST API pro counting speed jako fallback
            loadCountingSpeedFromAPI();
            // Zkusit také WebSocket pokud je připojený
            requestCountingSpeed();
        });
}

function loadCountingSpeedFromAPI() {
    fetch(`/api/counting_speed?region=${currentRegion}`)
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                updateCountingSpeed({
                    districts_per_hour: data.districts_per_hour,
                    estimated_hours: data.estimated_hours_to_complete
                });
            }
        })
        .catch(error => {
            console.log('Counting speed data not available yet');
        });
}


function updateResultsDisplay(data) {
    if (!data.results) return;
    
    // Aktualizace grafu
    charts.results.data.labels = data.results.map(r => r.party_name);
    charts.results.data.datasets[0].data = data.results.map(r => r.votes);
    charts.results.update();
    
    // Aktualizace tabulky
    const tbody = document.getElementById('results-tbody');
    tbody.innerHTML = '';
    
    data.results.forEach((result, index) => {
        const row = tbody.insertRow();
        
        // Výpočet trendu
        const trend = calculateTrend(result.party_code, result.percentage);
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td><strong>${result.party_name}</strong></td>
            <td>${result.votes.toLocaleString()}</td>
            <td>${result.percentage.toFixed(2)}%</td>
            <td>${result.mandates || 0}</td>
            <td class="${trend.class}">${trend.symbol}</td>
        `;
    });
    
    // Uložit výsledky pro porovnání trendů
    lastResults = {};
    data.results.forEach(r => {
        lastResults[r.party_code] = r.percentage;
    });
    
    // Aktualizace času poslední aktualizace
    document.getElementById('last-update').textContent = new Date().toLocaleString();
}

function calculateTrend(partyCode, currentPercentage) {
    if (!lastResults[partyCode]) {
        return { symbol: '—', class: 'trend-stable' };
    }
    
    const diff = currentPercentage - lastResults[partyCode];
    
    if (diff > 0.1) {
        return { symbol: '↑', class: 'trend-up' };
    } else if (diff < -0.1) {
        return { symbol: '↓', class: 'trend-down' };
    } else {
        return { symbol: '→', class: 'trend-stable' };
    }
}

function loadProgress() {
    fetch(`/api/progress?region=${currentRegion}`)
        .then(response => response.json())
        .then(data => {
            updateProgressDisplay(data);
        });
}

function updateProgressDisplay(data) {
    document.getElementById('counted-districts').textContent = data.counted_districts || 0;
    document.getElementById('total-districts').textContent = data.total_districts || 0;
    document.getElementById('counted-percentage').textContent = `${(data.percentage_counted || 0).toFixed(1)}%`;
    document.getElementById('turnout').textContent = `${(data.turnout || 0).toFixed(1)}%`;
    document.getElementById('valid-votes').textContent = (data.valid_votes || 0).toLocaleString();
    
    // Aktualizace progress baru
    const progressBar = document.getElementById('progress-bar-fill');
    progressBar.style.width = `${data.percentage_counted || 0}%`;
}

function loadPredictions() {
    fetch(`/api/predictions?region=${currentRegion}`)
        .then(response => response.json())
        .then(data => {
            if (!data.parties) return;
            
            document.getElementById('prediction-percentage').textContent = 
                `${(data.current_counted_percentage || 0).toFixed(1)}%`;
            
            // Aktualizace grafu predikcí
            charts.prediction.data.labels = data.parties.map(p => p.party_name);
            charts.prediction.data.datasets[0].data = data.parties.map(p => p.predicted_percentage);
            charts.prediction.update();
        });
}

function requestCountingSpeed() {
    if (socket && socket.connected) {
        socket.emit('get_counting_speed', { region: currentRegion });
    }
}

function updateCountingSpeed(data) {
    document.getElementById('counting-speed').textContent = data.districts_per_hour || 0;
    
    if (data.estimated_hours > 0) {
        const completionTime = new Date();
        completionTime.setHours(completionTime.getHours() + data.estimated_hours);
        document.getElementById('est-completion').textContent = completionTime.toLocaleTimeString();
    } else {
        document.getElementById('est-completion').textContent = '--:--';
    }
}

function loadTimelineData(hours) {
    // Použít REST API místo WebSocket pro spolehlivější načítání
    fetch(`/api/time_series?region=${currentRegion}&hours=${hours}`)
        .then(response => response.json())
        .then(data => {
            updateTimelineChart(data);
        })
        .catch(error => {
            console.error('Error loading timeline data:', error);
        });
}

function loadAllTimelineData() {
    // Načíst všechna dostupná data (48 hodin nebo více)
    fetch(`/api/time_series?region=${currentRegion}&hours=168`) // 7 dní
        .then(response => response.json())
        .then(data => {
            updateTimelineChart(data);
        })
        .catch(error => {
            console.error('Error loading all timeline data:', error);
        });
}

function updateTimelineChart(data) {
    console.log('Updating timeline chart with data:', data);
    
    if (!data.time_series || data.time_series.length === 0) {
        console.log('No timeline data available');
        return;
    }
    
    // Získat všechny unikátní strany
    const partiesMap = {};
    let colorIndex = 0;
    
    // Projít všechna data a vytvořit mapu stran
    data.time_series.forEach(point => {
        if (point.parties) {
            Object.keys(point.parties).forEach(partyCode => {
                if (!partiesMap[partyCode]) {
                    const partyData = point.parties[partyCode];
                    partiesMap[partyCode] = {
                        label: partyData.name || partyCode,
                        type: 'line',
                        data: [],
                        borderColor: partyColors[colorIndex % partyColors.length],
                        backgroundColor: partyColors[colorIndex % partyColors.length] + '20',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: false,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        yAxisID: 'y'
                    };
                    colorIndex++;
                }
            });
        }
    });
    
    // Naplnit data pro každou stranu a volume data
    const volumeData = [];
    const labels = [];
    
    data.time_series.forEach(point => {
        const time = new Date(point.timestamp);
        const timeLabel = time.toLocaleTimeString('cs-CZ', { hour: '2-digit', minute: '2-digit' });
        labels.push(timeLabel);
        
        // Volume data - počet nových hlasů
        volumeData.push(point.new_votes || 0);
        
        // Data pro každou stranu - jednodušší formát
        Object.keys(partiesMap).forEach(partyCode => {
            if (point.parties && point.parties[partyCode]) {
                partiesMap[partyCode].data.push(point.parties[partyCode].percentage || 0);
            } else {
                partiesMap[partyCode].data.push(null);
            }
        });
    });
    
    // Seřadit strany podle posledního výsledku
    const datasets = Object.values(partiesMap).sort((a, b) => {
        const lastA = a.data[a.data.length - 1] || 0;
        const lastB = b.data[b.data.length - 1] || 0;
        return lastB - lastA;
    });
    
    // Přidat volume dataset jako sloupcový graf
    const maxVotes = Math.max(...volumeData);
    const volumeColors = volumeData.map(votes => {
        const intensity = votes / maxVotes;
        const alpha = 0.15 + (intensity * 0.35);
        return `rgba(102, 126, 234, ${alpha})`;
    });
    
    datasets.push({
        label: 'Volume (new votes)',
        type: 'bar',
        data: volumeData,
        backgroundColor: volumeColors,
        borderColor: 'rgba(102, 126, 234, 0.5)',
        borderWidth: 1,
        yAxisID: 'y1',
        order: 999 // Zobrazit pod linkami
    });
    
    // Aktualizovat timeline graf
    charts.timeline.data.labels = labels;
    charts.timeline.data.datasets = datasets;
    charts.timeline.update();
    
    console.log(`Chart updated: ${datasets.length-1} parties + volume, ${labels.length} time points, max volume: ${maxVotes.toLocaleString()} votes`);
}

function loadCandidates(partyCode = '') {
    const url = partyCode ? 
        `/api/candidates?party=${partyCode}&region=${currentRegion}` :
        `/api/candidates?region=${currentRegion}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            updateCandidatesTable(data.candidates || []);
        });
}

function updateCandidatesTable(candidates) {
    const tbody = document.getElementById('candidates-tbody');
    tbody.innerHTML = '';
    
    candidates.forEach(candidate => {
        const row = tbody.insertRow();
        const fullName = `${candidate.title_before || ''} ${candidate.name} ${candidate.surname} ${candidate.title_after || ''}`.trim();
        
        row.innerHTML = `
            <td>${fullName}</td>
            <td>${candidate.party_name}</td>
            <td>${candidate.region_name}</td>
            <td>${candidate.position}</td>
            <td>${candidate.preferential_votes.toLocaleString()}</td>
            <td>${candidate.preferential_percentage.toFixed(2)}%</td>
            <td>${candidate.elected ? '✓' : ''}</td>
        `;
    });
}

function switchView(viewType) {
    // Skrýt všechny panely
    document.querySelectorAll('.view-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    // Zobrazit vybraný panel
    document.getElementById(`${viewType}-view`).classList.add('active');
    
    // Načíst data pro daný pohled
    switch(viewType) {
        case 'current':
            loadCurrentResults();
            break;
        case 'timeline':
            loadAllTimelineData(); // Načíst všechna data při přepnutí
            break;
        case 'totalvotes':
            loadAllTotalVotesData(); // Načíst data celkových hlasů
            break;
        case 'comparison':
            // Při přepnutí na comparison načíst data
            setTimeout(() => {
                // Pokud žádný checkbox není zaškrtnutý, zaškrtnout CZ jako výchozí
                const hasChecked = document.querySelectorAll('#region-checkboxes input:checked').length > 0;
                if (!hasChecked) {
                    const czCheckbox = document.getElementById('region-CZ');
                    if (czCheckbox) {
                        czCheckbox.checked = true;
                    }
                }
                loadComparisonData();
            }, 100); // Malé zpoždění pro načtení checkboxů
            break;
        case 'candidates':
            loadCandidates();
            break;
    }
}

function loadComparisonData() {
    // Získat vybrané regiony
    const selectedRegions = [];
    document.querySelectorAll('#region-checkboxes input:checked').forEach(checkbox => {
        selectedRegions.push(checkbox.value);
    });
    
    if (selectedRegions.length === 0) {
        // Pokud nic není vybráno, zobrazit upozornění
        charts.comparison.data.labels = [];
        charts.comparison.data.datasets = [];
        charts.comparison.update();
        console.log('No regions selected for comparison');
        return;
    }
    
    const regionsParam = selectedRegions.join(',');
    console.log('Loading comparison for regions:', regionsParam);
    
    fetch(`/api/comparison?regions=${regionsParam}`)
        .then(response => response.json())
        .then(data => {
            console.log('Comparison data received:', data);
            updateComparisonChart(data.comparison || []);
        })
        .catch(error => {
            console.error('Error loading comparison data:', error);
        });
}

function updateComparisonChart(comparisonData) {
    if (comparisonData.length === 0) return;
    
    // Získat všechny unikátní strany
    const allParties = new Set();
    comparisonData.forEach(region => {
        region.results.forEach(result => {
            allParties.add(result.party_name);
        });
    });
    
    // Připravit datasety pro každý region
    const datasets = comparisonData.map((region, index) => {
        const data = [];
        allParties.forEach(partyName => {
            const result = region.results.find(r => r.party_name === partyName);
            data.push(result ? result.percentage : 0);
        });
        
        return {
            label: region.region_name,
            data: data,
            backgroundColor: partyColors[index % partyColors.length]
        };
    });
    
    charts.comparison.data.labels = Array.from(allParties);
    charts.comparison.data.datasets = datasets;
    charts.comparison.update();
}

function changeRegion(newRegion) {
    // Odhlásit se z předchozího regionu
    if (socket && socket.connected) {
        socket.emit('unsubscribe', { region: currentRegion });
    }
    
    currentRegion = newRegion;
    
    // Přihlásit se k novému regionu
    if (socket && socket.connected) {
        socket.emit('subscribe', { region: currentRegion });
    }
    
    // Načíst nová data
    refreshData();
}

function refreshData() {
    const viewType = document.getElementById('view-type').value;
    switchView(viewType);
}

function handleRealtimeUpdate(data) {
    // Aktualizace pouze pokud je to pro aktuální region
    if (data.region && data.region.code === currentRegion) {
        if (data.results) {
            // Seřadit výsledky podle hlasů před zobrazením (stejně jako REST API)
            const sortedResults = [...data.results].sort((a, b) => b.votes - a.votes);
            updateResultsDisplay({ results: sortedResults, region: data.region });
        }

        if (data.progress) {
            updateProgressDisplay(data.progress);
        }

        // Požádat o aktualizaci counting speed
        requestCountingSpeed();
    }
}

function exportData(format) {
    window.open(`/api/export/${format}?region=${currentRegion}`, '_blank');
}

function startAutoRefresh() {
    // Automatický refresh každých 10 sekund
    autoRefreshInterval = setInterval(() => {
        if (socket && socket.connected) {
            socket.emit('request_update', { region: currentRegion });
        } else {
            refreshData();
        }
    }, 10000);
}

function updateCurrentTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleString();
}

function updateTimelinePosition(value) {
    // Implementace pro posun na timeline
    const position = parseInt(value);
    const label = position === 100 ? 'Current' : `${position}%`;
    document.getElementById('timeline-position').textContent = label;
    
    // TODO: Implementovat zobrazení historických dat na dané pozici
}

function loadTotalVotesData(hours) {
    // Načíst data celkových hlasů za zadaný počet hodin
    fetch(`/api/time_series?region=${currentRegion}&hours=${hours}`)
        .then(response => response.json())
        .then(data => {
            updateTotalVotesChart(data);
        })
        .catch(error => {
            console.error('Error loading total votes data:', error);
        });
}

function loadAllTotalVotesData() {
    // Načíst všechna dostupná data celkových hlasů
    fetch(`/api/time_series?region=${currentRegion}&hours=168`) // 7 dní
        .then(response => response.json())
        .then(data => {
            updateTotalVotesChart(data);
        })
        .catch(error => {
            console.error('Error loading all total votes data:', error);
        });
}

function updateTotalVotesChart(data) {
    console.log('Updating total votes chart with data:', data);
    
    if (!data.time_series || data.time_series.length === 0) {
        console.log('No total votes data available');
        return;
    }
    
    // Získat všechny unikátní strany
    const partiesMap = {};
    let colorIndex = 0;
    let totalVotesOverTime = [];
    
    // Projít všechna data a vytvořit mapu stran
    data.time_series.forEach(point => {
        let totalVotesAtPoint = 0;
        if (point.parties) {
            Object.keys(point.parties).forEach(partyCode => {
                const partyData = point.parties[partyCode];
                totalVotesAtPoint += partyData.votes || 0;
                
                if (!partiesMap[partyCode]) {
                    partiesMap[partyCode] = {
                        label: partyData.name || partyCode,
                        data: [],
                        borderColor: partyColors[colorIndex % partyColors.length],
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: false,
                        pointRadius: 0,
                        pointHoverRadius: 4
                    };
                    colorIndex++;
                }
            });
        }
        totalVotesOverTime.push(totalVotesAtPoint);
    });
    
    // Naplnit data pro každou stranu
    const labels = [];
    const newVotesPerMinute = [];
    
    data.time_series.forEach((point, index) => {
        const time = new Date(point.timestamp);
        const timeLabel = time.toLocaleTimeString('cs-CZ', { hour: '2-digit', minute: '2-digit' });
        labels.push(timeLabel);
        
        // Počet nových hlasů za minutu (pro statistiku)
        if (index > 0) {
            const prevTotal = totalVotesOverTime[index - 1];
            const currentTotal = totalVotesOverTime[index];
            newVotesPerMinute.push(Math.max(0, currentTotal - prevTotal));
        } else {
            newVotesPerMinute.push(0);
        }
        
        // Data pro každou stranu - absolutní počty hlasů
        Object.keys(partiesMap).forEach(partyCode => {
            if (point.parties && point.parties[partyCode]) {
                partiesMap[partyCode].data.push(point.parties[partyCode].votes || 0);
            } else {
                partiesMap[partyCode].data.push(null);
            }
        });
    });
    
    // Seřadit strany podle posledního výsledku
    const datasets = Object.values(partiesMap).sort((a, b) => {
        const lastA = a.data[a.data.length - 1] || 0;
        const lastB = b.data[b.data.length - 1] || 0;
        return lastB - lastA;
    });
    
    // Vypočítat statistiky
    const currentTotal = totalVotesOverTime[totalVotesOverTime.length - 1] || 0;
    const avgVotesPerMinute = newVotesPerMinute.length > 0 
        ? Math.round(newVotesPerMinute.reduce((a, b) => a + b, 0) / newVotesPerMinute.length)
        : 0;
    const peakVotesPerMinute = Math.max(...newVotesPerMinute);
    
    // Najít vedoucí stranu
    let leadingParty = '';
    let leadingVotes = 0;
    if (datasets.length > 0 && datasets[0].data.length > 0) {
        leadingParty = datasets[0].label;
        leadingVotes = datasets[0].data[datasets[0].data.length - 1] || 0;
    }
    
    // Aktualizovat statistiky
    document.getElementById('current-total-votes').textContent = currentTotal.toLocaleString();
    document.getElementById('avg-votes-per-minute').textContent = avgVotesPerMinute.toLocaleString();
    document.getElementById('peak-votes-per-minute').textContent = `${leadingParty}: ${leadingVotes.toLocaleString()}`;
    
    // Aktualizovat graf
    if (charts.totalVotes) {
        charts.totalVotes.data.labels = labels;
        charts.totalVotes.data.datasets = datasets;
        charts.totalVotes.update();
    }
    
    console.log(`Total Votes chart updated: ${datasets.length} parties, ${labels.length} time points, total: ${currentTotal.toLocaleString()}`);
}