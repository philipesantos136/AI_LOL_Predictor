<script lang="ts">
  import { onDestroy } from 'svelte';
  import { Chart, DoughnutController, ArcElement, Tooltip } from 'chart.js';

  Chart.register(DoughnutController, ArcElement, Tooltip);

  interface Props {
    winRate: number;
    teamColor: string;
    teamName: string;
  }

  let { winRate, teamColor, teamName }: Props = $props();

  let canvas: HTMLCanvasElement;
  let chart: Chart | null = null;

  const delta = $derived(winRate - 50);
  const deltaText = $derived(delta >= 0 ? `+${delta.toFixed(1)}%` : `${delta.toFixed(1)}%`);
  const deltaColor = $derived(delta >= 0 ? '#10b981' : '#ef4444');

  $effect(() => {
    if (!canvas) return;

    chart?.destroy();

    chart = new Chart(canvas, {
      type: 'doughnut',
      data: {
        datasets: [
          {
            data: [winRate, 100 - winRate],
            backgroundColor: [teamColor, 'rgba(15,23,42,0.5)'],
            borderWidth: 0,
            // @ts-ignore — Chart.js supports these on dataset level
            circumference: 180,
            rotation: 270,
          },
        ],
      },
      options: {
        responsive: true,
        cutout: '70%',
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false },
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

<div class="gauge-wrapper">
  <canvas bind:this={canvas}></canvas>
  <div class="gauge-center">
    <span class="gauge-rate">{winRate.toFixed(1)}%</span>
    <span class="gauge-delta" style:color={deltaColor}>{deltaText}</span>
    <span class="gauge-label">{teamName}</span>
  </div>
</div>

<style>
  .gauge-wrapper {
    position: relative;
    display: inline-block;
    width: 100%;
  }

  .gauge-center {
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    flex-direction: column;
    align-items: center;
    pointer-events: none;
    padding-bottom: 0.5rem;
  }

  .gauge-rate {
    font-size: 1.5rem;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1;
  }

  .gauge-delta {
    font-size: 0.875rem;
    font-weight: 600;
    line-height: 1.2;
  }

  .gauge-label {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-top: 0.125rem;
  }
</style>
