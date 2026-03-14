<script lang="ts">
  import { onDestroy } from 'svelte';
  import { Chart, LineController, LinearScale, CategoryScale, PointElement, LineElement, Legend, Tooltip, Filler } from 'chart.js';
  import type { TimelineSection } from '$lib/types/analytics';

  Chart.register(LineController, LinearScale, CategoryScale, PointElement, LineElement, Legend, Tooltip, Filler);

  interface Props {
    timelineData: TimelineSection;
    team1: string;
    team2: string;
  }

  let { timelineData, team1, team2 }: Props = $props();

  let goldCanvas: HTMLCanvasElement;
  let csCanvas: HTMLCanvasElement;
  let xpCanvas: HTMLCanvasElement;

  let goldChart: Chart | null = null;
  let csChart: Chart | null = null;
  let xpChart: Chart | null = null;

  const minuteLabels = $derived(timelineData.minutes.map(m => `${m}min`));

  function makeZeroLine(length: number) {
    return Array(length).fill(0);
  }

  function buildDatasets(
    historical: number[],
    draft: number[] | undefined,
    color: string,
    label: string,
    minutes: number[]
  ) {
    const datasets: any[] = [
      {
        label: `${label} (zero)`,
        data: makeZeroLine(minutes.length),
        borderColor: 'rgba(255,255,255,0.2)',
        borderDash: [4, 4],
        borderWidth: 1,
        pointRadius: 0,
        fill: false,
      },
      {
        label,
        data: historical,
        borderColor: color,
        backgroundColor: 'transparent',
        borderWidth: 2,
        pointRadius: 3,
        fill: false,
        tension: 0.3,
      },
    ];

    if (draft && draft.length > 0) {
      datasets.push({
        label: `${label} (Draft)`,
        data: draft,
        borderColor: color,
        backgroundColor: 'transparent',
        borderWidth: 2,
        borderDash: [5, 5],
        pointRadius: 3,
        fill: false,
        tension: 0.3,
      });
    }

    return datasets;
  }

  function createChart(canvas: HTMLCanvasElement, title: string, datasets: any[], labels: string[]): Chart {
    return new Chart(canvas, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        plugins: {
          legend: {
            labels: {
              color: '#94a3b8',
              filter: (item) => !item.text.includes('(zero)'),
            },
          },
          tooltip: { mode: 'index', intersect: false },
        },
        scales: {
          x: {
            ticks: { color: '#94a3b8' },
            grid: { color: 'rgba(255,255,255,0.05)' },
          },
          y: {
            ticks: { color: '#94a3b8' },
            grid: { color: 'rgba(255,255,255,0.05)' },
            title: { display: true, text: title, color: '#94a3b8' },
          },
        },
      },
    });
  }

  $effect(() => {
    if (!goldCanvas || !csCanvas || !xpCanvas) return;

    goldChart?.destroy();
    csChart?.destroy();
    xpChart?.destroy();

    const labels = minuteLabels;

    goldChart = createChart(
      goldCanvas,
      'Gold Diff',
      buildDatasets(timelineData.gold_diff_t1, timelineData.draft_gold_diff_t1, '#3b82f6', `${team1} Gold Diff`, timelineData.minutes),
      labels
    );

    csChart = createChart(
      csCanvas,
      'CS Diff',
      buildDatasets(timelineData.cs_diff_t1, timelineData.draft_cs_diff_t1, '#10b981', `${team1} CS Diff`, timelineData.minutes),
      labels
    );

    xpChart = createChart(
      xpCanvas,
      'XP Diff',
      buildDatasets(timelineData.xp_diff_t1, timelineData.draft_xp_diff_t1, '#f59e0b', `${team1} XP Diff`, timelineData.minutes),
      labels
    );

    return () => {
      goldChart?.destroy();
      csChart?.destroy();
      xpChart?.destroy();
      goldChart = null;
      csChart = null;
      xpChart = null;
    };
  });

  onDestroy(() => {
    goldChart?.destroy();
    csChart?.destroy();
    xpChart?.destroy();
    goldChart = null;
    csChart = null;
    xpChart = null;
  });
</script>

<div class="flex flex-col gap-4">
  <div class="chart-subplot">
    <canvas bind:this={goldCanvas}></canvas>
  </div>
  <div class="chart-subplot">
    <canvas bind:this={csCanvas}></canvas>
  </div>
  <div class="chart-subplot">
    <canvas bind:this={xpCanvas}></canvas>
  </div>
</div>

<style>
  .chart-subplot {
    position: relative;
    height: 180px;
  }
</style>
