(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();

  // --- Chart 1: 创作者核心痛点调查 ---
  var chart1 = echarts.init(document.getElementById('chart-pain'), null, { renderer: 'svg' });
  chart1.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      appendToBody: true,
      formatter: function(params) {
        return params[0].name + '<br/>占比: ' + params[0].value + '%';
      }
    },
    grid: { left: '3%', right: '6%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'value',
      max: 100,
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: muted, formatter: '{value}%' },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: ['风格不一致', '灵感枯竭', '情节断裂', '设定遗忘'],
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: ink, fontSize: 13 }
    },
    series: [{
      type: 'bar',
      data: [62, 73, 81, 89],
      itemStyle: {
        color: function(params) {
          var colors = [accent2, accent2 + 'cc', accent + 'cc', accent];
          return colors[params.dataIndex];
        },
        borderRadius: [0, 4, 4, 0]
      },
      barWidth: '50%',
      label: {
        show: true,
        position: 'right',
        formatter: '{c}%',
        color: ink,
        fontSize: 13,
        fontWeight: 600
      }
    }]
  });
  window.addEventListener('resize', function() { chart1.resize(); });

  // --- Chart 2: 功能模块效率提升 ---
  var chart2 = echarts.init(document.getElementById('chart-efficiency'), null, { renderer: 'svg' });
  chart2.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      appendToBody: true
    },
    legend: {
      data: ['使用前（分钟）', '使用后（分钟）'],
      top: 0,
      textStyle: { color: muted, fontSize: 12 }
    },
    grid: { left: '3%', right: '6%', bottom: '3%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['设定查阅', '一致性检查', '灵感恢复', '情节规划', '角色管理'],
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: ink, fontSize: 12, interval: 0 }
    },
    yAxis: {
      type: 'value',
      name: '耗时（分钟）',
      nameTextStyle: { color: muted, fontSize: 12 },
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: muted },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    series: [
      {
        name: '使用前（分钟）',
        type: 'bar',
        data: [15, 25, 120, 40, 20],
        itemStyle: { color: muted + '80', borderRadius: [4, 4, 0, 0] },
        barGap: '20%'
      },
      {
        name: '使用后（分钟）',
        type: 'bar',
        data: [4.5, 5, 40, 12, 6],
        itemStyle: { color: accent, borderRadius: [4, 4, 0, 0] }
      }
    ]
  });
  window.addEventListener('resize', function() { chart2.resize(); });

  // --- Chart 3: 产品路线图 ---
  var chart3 = echarts.init(document.getElementById('chart-roadmap'), null, { renderer: 'svg' });
  chart3.setOption({
    animation: false,
    tooltip: {
      trigger: 'item',
      appendToBody: true,
      formatter: function(params) {
        var desc = {
          'Phase 1\n创作工具': '核心五大功能上线\nWeb端单人创作\n积累种子用户',
          'Phase 2\n协作平台': '多人协作创作\n设定共享库\n社区化世界观市场',
          'Phase 3\n创作生态': '开放API\n接入出版/影视/游戏\nAI辅助IP孵化'
        };
        return desc[params.name] || params.name;
      }
    },
    grid: { left: '8%', right: '8%', bottom: '12%', top: '15%' },
    xAxis: {
      type: 'category',
      data: ['2026 Q3', '2026 Q4', '2027 Q1', '2027 Q2', '2027 Q3+'],
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: muted, fontSize: 12 },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLine: { show: false },
      axisLabel: { show: false },
      splitLine: { lineStyle: { color: rule, type: 'dashed', opacity: 0.5 } }
    },
    series: [
      {
        type: 'line',
        data: [20, 35, 35, 35, 35],
        lineStyle: { color: accent2, width: 0 },
        itemStyle: { color: accent2 },
        symbol: 'none',
        silent: true
      },
      {
        type: 'line',
        data: [null, 35, 60, 60, 60],
        lineStyle: { color: accent2, width: 0 },
        itemStyle: { color: accent2 },
        symbol: 'none',
        silent: true
      },
      {
        type: 'line',
        data: [null, null, 60, 60, 90],
        lineStyle: { color: accent2, width: 0 },
        itemStyle: { color: accent2 },
        symbol: 'none',
        silent: true
      },
      {
        type: 'line',
        data: [20, 35, 60, 60, 90],
        lineStyle: { color: accent, width: 2, type: 'dashed' },
        itemStyle: { color: accent },
        symbol: 'circle',
        symbolSize: 10,
        label: {
          show: true,
          position: 'top',
          formatter: function(params) {
            var labels = ['Phase 1\n创作工具', '', 'Phase 2\n协作平台', '', 'Phase 3\n创作生态'];
            return labels[params.dataIndex] || '';
          },
          color: ink,
          fontSize: 11,
          fontWeight: 600,
          lineHeight: 14
        }
      },
      {
        type: 'bar',
        data: [20, 35, 60, 60, 90],
        itemStyle: {
          color: function(params) {
            var colors = [accent + '20', accent + '30', accent + '40', accent + '50', accent + '60'];
            return colors[params.dataIndex];
          },
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: '40%',
        z: 1
      }
    ]
  });
  window.addEventListener('resize', function() { chart3.resize(); });
})();
