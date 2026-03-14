<script lang="ts">
  import { onDestroy } from 'svelte';
  import { Chart, RadarController, RadialLinearScale, PointElement, LineElement, Filler, Legend, Tooltip } from 'chart.js';

  Chart.register(RadarController, RadialLinearScale, PointElement, LineElement, Filler, Legend, Tooltip);

  interface Props {
    labels: string[];
    t1Values: number[];
    t2Values: number[];
    team1: string;
    team2: string;
  }

  let { labels, t1Values, t2Values, team1, team2 }: Props = $props();

  let canvas: HTMLCanvasElement;
  let chart: Chart | null = null;

  $effect(() => {
    if (!canvas) return;

    chart?.destroy();

    chart = new Chart(canvas, {
      type: 'radar',
      data: {
        labels,
        datasets: [
          {
            label: team1,
            data: t1Values,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59,130,246,0.2)',
            pointBackgroundColor: '#3b82f6',
          },
          {
            label: team2,
            data: t2Values,
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239,68,68,0.2)',
            pointBackgroundColor: '#ef4444',
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          r: {
            min: 0,
            max: 100,
            ticks: { display: false },
            grid: { color: 'rgba(255,255,255,0.1)' },
            angleLines: { color: 'rgba(255,255,255,0.1)' },
            pointLabels: { color: '#94a3b8', font: { size: 12 } },
          },
        },
        plugins: {
          legend: { labels: { color: '#94a3b8' } },
        },
      },
    });

    return () => {
      chart?.destroy();
      chart = null;
    };
  });

  onDestroy(() => {
    chart?.destroy();
    chart = null;
  });
</script>

<canvas bind:this={canvas}></canvas>
