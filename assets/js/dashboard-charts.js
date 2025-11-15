document.addEventListener("DOMContentLoaded", function () {
  console.log(courseData);
  console.log(deptData);

  // Get theme colors dynamically from CSS variables
  const getThemeColors = () => {
    const styles = getComputedStyle(document.documentElement);
    return {
      textColor: styles.getPropertyValue('--text-color').trim(),
      mutedText: styles.getPropertyValue('--muted-text').trim(),
      gridColor: styles.getPropertyValue('--border-color').trim(),
    };
  };

  // Helper function to create charts with theme-aware text
  const createTrendChart = () => {
    const trendCtx = document.getElementById('trendChart').getContext('2d');
    const colors = getThemeColors();

    const months = JSON.parse(document.getElementById('months_data').textContent);
    const approvedData = JSON.parse(document.getElementById('approved_data_json').textContent);
    const pendingData = JSON.parse(document.getElementById('pending_data_json').textContent);
    const rejectedData = JSON.parse(document.getElementById('rejected_data_json').textContent);

    return new Chart(trendCtx, {
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
          legend: {
            labels: { color: colors.textColor },
          },
        },
        scales: {
          x: {
            ticks: { color: colors.textColor },
            grid: { color: colors.gridColor },
          },
          y: {
            ticks: { color: colors.textColor },
            grid: { color: colors.gridColor },
          },
        },
      },
    });
  };

  const createCourseChart = () => {
    const courseCounts = courseData.map(item => item.count);
    const courseLabels = courseData.map(item => item.course_name);
    const totalCourse = courseCounts.reduce((a, b) => a + b, 0);
    const colors = getThemeColors();

    const courseCtx = document.getElementById('courseChart').getContext('2d');
    return new Chart(courseCtx, {
      type: 'pie',
      plugins: [ChartDataLabels],
      data: {
        labels: courseLabels,
        datasets: [{
          data: courseCounts,
          backgroundColor: ['#3f51b5', '#7e57c2', '#e91e63', '#ff9800', '#4caf50', '#00bcd4'],
        }],
      },
      options: {
        plugins: {
          datalabels: {
            color: '#fff',
            formatter: value => ((value / totalCourse) * 100).toFixed(1) + '%',
          },
          legend: {
            position: 'right',
            labels: { color: colors.textColor },
          },
        },
      },
    });
  };

  const createDeptChart = () => {
    const deptLabels = deptData.map(item => item.department__name);
    const deptCounts = deptData.map(item => item.count);
    const colors = getThemeColors();

    const ctxDept = document.getElementById('departmentChart').getContext('2d');
    return new Chart(ctxDept, {
      type: 'bar',
      data: {
        labels: deptLabels,
        datasets: [{
          label: 'Thesis Count',
          data: deptCounts,
          backgroundColor: '#8b5cf6',
          borderRadius: 6,
        }],
      },
      options: {
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: { ticks: { color: colors.textColor } },
          y: { ticks: { color: colors.textColor } },
        },
      },
    });
  };

  // Initial chart creation
  let trendChart = createTrendChart();
  let courseChart = createCourseChart();
  let deptChart = createDeptChart();

  // 🔄 Re-render charts when theme changes
  const observer = new MutationObserver(() => {
    trendChart.destroy();
    courseChart.destroy();
    deptChart.destroy();

    trendChart = createTrendChart();
    courseChart = createCourseChart();
    deptChart = createDeptChart();
  });

  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
});
