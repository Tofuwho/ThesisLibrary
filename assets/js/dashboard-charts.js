document.addEventListener("DOMContentLoaded", function () {

  console.log(courseData); // should log array from backend
  console.log(deptData);

  // ===== Submission Trend =====
  const trendCtx = document.getElementById('trendChart').getContext('2d');

  // Get data from Django context
    const months = JSON.parse(document.getElementById('months_data').textContent);
    const approvedData = JSON.parse(document.getElementById('approved_data_json').textContent);
    const pendingData = JSON.parse(document.getElementById('pending_data_json').textContent);
    const rejectedData = JSON.parse(document.getElementById('rejected_data_json').textContent);

  new Chart(trendCtx, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: 'Approved',
          data: approvedData,
          borderColor: '#1A43BF',
          backgroundColor: 'rgba(42, 97, 161, 0.2)',
          tension: 0.3,
          fill: true,
        },
        {
          label: 'Pending',
          data: pendingData,
          borderColor: '#ffc107',
          backgroundColor: 'rgba(255, 193, 7, 0.2)',
          tension: 0.3,
          fill: true,
        },
        {
          label: 'Rejected',
          data: rejectedData,
          borderColor: '#FF0000',
          backgroundColor: 'rgba(255, 0, 0, 0.2)',
          tension: 0.3,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: '#fff' } },
      },
      scales: {
        x: { ticks: { color: '#ccc' }, grid: { color: '#333' } },
        y: { ticks: { color: '#ccc' }, grid: { color: '#333' } },
      },
    },
  });

  // ✅ Prepare course chart data
  const courseCounts = courseData.map(item => item.count);
  const courseLabels = courseData.map(item => item.course_name);
  const totalCourse = courseCounts.reduce((a, b) => a + b, 0);

  const courseCtx = document.getElementById('courseChart').getContext('2d');
  new Chart(courseCtx, {
    type: 'pie',
    plugins: [ChartDataLabels],
    data: {
      labels: courseLabels,
      datasets: [{
        data: courseCounts,
        backgroundColor: ['#3f51b5', '#7e57c2', '#e91e63', '#ff9800', '#4caf50', '#00bcd4']
      }]
    },
    options: {
      plugins: {
        datalabels: {
          color: '#fff',
          formatter: value => ((value / totalCourse) * 100).toFixed(1) + '%'
        },
        legend: {
          position: 'right',
          labels: { color: '#fff' }
        }
      }
    }
  });

  // ✅ Theses by Department
  const deptLabels = deptData.map(item => item.department__name);
  const deptCounts = deptData.map(item => item.count);

  const ctxDept = document.getElementById('departmentChart').getContext('2d');
  new Chart(ctxDept, {
    type: 'bar',
    data: {
      labels: deptLabels,
      datasets: [{
        label: 'Thesis Count',
        data: deptCounts,
        backgroundColor: '#8b5cf6',
        borderRadius: 6
      }]
    },
    options: {
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { ticks: { color: '#d1d5db' } },
        y: { ticks: { color: '#d1d5db' } }
      }
    }
  });

});

