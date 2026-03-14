<script lang="ts">
  import { onDestroy } from 'svelte';
  import { Chart, BarController, BarElement, CategoryScale, LinearScale, Legend, Tooltip } from 'chart.js';

  Chart.register(BarController, BarElement, CategoryScale, LinearScale, Legend, Tooltip);

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
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: team1,
            data: t1Values,
            backgroundColor: 'rgba(59,130,246,0.7)',
            borderColor: '#3b82f6',
            borderWidth: 1,
          },
          {
            label: team2,
            data: t2Values,
            backgroundColor: 'rgba(239,68,68,0.7)',
            borderColor: '#ef4444',
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: '#94a3b8' } },
        },
        scales: {
          x: {
            ticks: { color: '#94a3b8' },
            grid: { color: 'rgba(255,255,255,0.05)' },
          },
          y: {
            ticks: { color: '#94a3b8' },
            grid: { color: 'rgba(255,255,255,0.05)' },
            beginAtZero: true,
          },
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
