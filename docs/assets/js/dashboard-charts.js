document.addEventListener("DOMContentLoaded", function () {

  // Global Chart Defaults
  Chart.defaults.color = '#636e72';
  Chart.defaults.font.family = "'Poppins', sans-serif";

  // ===== Submission Trend =====
  const trendCtx = document.getElementById('trendChart').getContext('2d');

  const trendData = JSON.parse(document.getElementById('trend_data_json').textContent);
  const courseData = JSON.parse(document.getElementById('course_data_json').textContent);
  const deptData = JSON.parse(document.getElementById('dept_data_json').textContent);
  const rangeSelect = document.getElementById('trendRangeSelect');

  let activeRange = rangeSelect ? rangeSelect.value : '12m';
  let activeData = trendData[activeRange] || trendData['12m'];

  const trendChart = new Chart(trendCtx, {
    type: 'line',
    data: {
      labels: activeData.labels,
      datasets: [
        {
          label: 'Approved',
          data: activeData.approved,
          borderColor: '#1e7e34',
          backgroundColor: 'rgba(30, 126, 52, 0.05)',
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#1e7e34',
          pointRadius: 4
        },
        {
          label: 'Pending',
          data: activeData.pending,
          borderColor: '#b08d00',
          backgroundColor: 'rgba(176, 141, 0, 0.05)',
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#b08d00',
          pointRadius: 4
        },
        {
          label: 'Rejected',
          data: activeData.rejected,
          borderColor: '#a31d23',
          backgroundColor: 'rgba(163, 29, 35, 0.05)',
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#a31d23',
          pointRadius: 4
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            usePointStyle: true,
            padding: 20
          }
        },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.05)' }
        },
      },
    },
  });

  if (rangeSelect) {
    rangeSelect.addEventListener('change', function () {
      const selectedRange = this.value;
      const newData = trendData[selectedRange];
      if (newData) {
        trendChart.data.labels = newData.labels;
        trendChart.data.datasets[0].data = newData.approved;
        trendChart.data.datasets[1].data = newData.pending;
        trendChart.data.datasets[2].data = newData.rejected;
        trendChart.update();
      }
    });
  }

  // ===== Manuscript Entry & Archival Frequency =====
  const entryCtx = document.getElementById('entryTrendChart');
  if (entryCtx) {
    const entryRangeSelect = document.getElementById('entryRangeSelect');
    let activeEntryRange = entryRangeSelect ? entryRangeSelect.value : '12m';
    let activeEntryData = trendData[activeEntryRange] || trendData['12m'];

    const entryTrendChart = new Chart(entryCtx.getContext('2d'), {
      type: 'line',
      data: {
        labels: activeEntryData.labels,
        datasets: [
          {
            label: 'Manuscripts Entered',
            data: activeEntryData.entered,
            borderColor: '#0984e3',
            backgroundColor: 'rgba(9, 132, 227, 0.05)',
            tension: 0.4,
            fill: true,
            pointBackgroundColor: '#0984e3',
            pointRadius: 4
          },
          {
            label: 'Approved',
            data: activeEntryData.approved,
            borderColor: '#1e7e34',
            backgroundColor: 'rgba(30, 126, 52, 0.05)',
            tension: 0.4,
            fill: true,
            pointBackgroundColor: '#1e7e34',
            pointRadius: 4
          },
          {
            label: 'Pending',
            data: activeEntryData.pending,
            borderColor: '#b08d00',
            backgroundColor: 'rgba(176, 141, 0, 0.05)',
            tension: 0.4,
            fill: true,
            pointBackgroundColor: '#b08d00',
            pointRadius: 4
          },
          {
            label: 'Rejected',
            data: activeEntryData.rejected,
            borderColor: '#a31d23',
            backgroundColor: 'rgba(163, 29, 35, 0.05)',
            tension: 0.4,
            fill: true,
            pointBackgroundColor: '#a31d23',
            pointRadius: 4
          },
          {
            label: 'Archived',
            data: activeEntryData.archived,
            borderColor: '#c5b358',
            backgroundColor: 'rgba(197, 179, 88, 0.05)',
            tension: 0.4,
            fill: true,
            pointBackgroundColor: '#c5b358',
            pointRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            align: 'end',
            labels: {
              usePointStyle: true,
              padding: 20
            }
          }
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(0,0,0,0.05)' }
          }
        }
      }
    });

    if (entryRangeSelect) {
      entryRangeSelect.addEventListener('change', function () {
        const selectedRange = this.value;
        const newData = trendData[selectedRange];
        if (newData) {
          entryTrendChart.data.labels = newData.labels;
          entryTrendChart.data.datasets[0].data = newData.entered;
          entryTrendChart.data.datasets[1].data = newData.approved;
          entryTrendChart.data.datasets[2].data = newData.pending;
          entryTrendChart.data.datasets[3].data = newData.rejected;
          entryTrendChart.data.datasets[4].data = newData.archived;
          entryTrendChart.update();
        }
      });
    }
  }

  // ===== Course Chart (Pie/Doughnut) =====
  const courseCounts = courseData.map(item => item.count);
  const courseLabels = courseData.map(item => item.course_name);
  const totalCourse = courseCounts.reduce((a, b) => a + b, 0);

  const courseCtx = document.getElementById('courseChart').getContext('2d');
  new Chart(courseCtx, {
    type: 'doughnut',
    plugins: [ChartDataLabels],
    data: {
      labels: courseLabels,
      datasets: [{
        data: courseCounts,
        backgroundColor: [
          '#a31d23', '#2d3436', '#636e72', '#b2bec3', '#dfe6e9', '#000000'
        ],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '60%',
      plugins: {
        datalabels: {
          color: '#fff',
          font: { weight: 'bold' },
          formatter: value => totalCourse > 0 ? ((value / totalCourse) * 100).toFixed(0) + '%' : '0%'
        },
        legend: {
          display: false
        }
      }
    }
  });

  // ===== Department Chart (Bar) =====
  const deptLabels = deptData.map(item => item.department__name);
  const deptCounts = deptData.map(item => item.count);

  const ctxDept = document.getElementById('departmentChart').getContext('2d');
  new Chart(ctxDept, {
    type: 'bar',
    data: {
      labels: deptLabels,
      datasets: [{
        label: 'Approved Theses',
        data: deptCounts,
        backgroundColor: 'rgba(163, 29, 35, 0.8)',
        hoverBackgroundColor: '#a31d23',
        borderRadius: 8,
        barThickness: 30
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.05)' }
        }
      }
    }
  });

});


