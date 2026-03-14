<script lang="ts">
  import { onDestroy } from 'svelte';
  import { Chart, BarController, BarElement, CategoryScale, LinearScale, Legend, Tooltip, LineController, PointElement, LineElement } from 'chart.js';

  Chart.register(BarController, BarElement, CategoryScale, LinearScale, Legend, Tooltip, LineController, PointElement, LineElement);

  interface Props {
    rawData: number[];
    color: string;
    meanLine?: boolean;
    label?: string;
  }

  let { rawData, color, meanLine = false, label = 'Distribuição' }: Props = $props();

  let canvas: HTMLCanvasElement;
  let chart: Chart | null = null;

  const binData = $derived.by(() => {
    const counts = new Map<number, number>();
    for (const v of rawData) counts.set(v, (counts.get(v) ?? 0) + 1);
    const sortedLabels = [...counts.keys()].sort((a, b) => a - b);
    const values = sortedLabels.map(l => counts.get(l)!);
    return { sortedLabels, values };
  });

  const mean = $derived(
    rawData.length > 0 ? rawData.reduce((a, b) => a + b, 0) / rawData.length : 0
  );

  $effect(() => {
    if (!canvas) return;

    chart?.destroy();

    const { sortedLabels, values } = binData;
    const strLabels = sortedLabels.map(String);

    const datasets: any[] = [
      {
        type: 'bar' as const,
        label,
        data: values,
        backgroundColor: color.startsWith('rgba') ? color : hexToRgba(color, 0.7),
        borderColor: color,
        borderWidth: 1,
      },
    ];

    if (meanLine && rawData.length > 0) {
      // Find the closest label index to the mean
      const meanLabel = String(Math.round(mean));
      const meanIndex = strLabels.indexOf(meanLabel);
      const targetIndex = meanIndex >= 0 ? meanIndex : findClosestIndex(sortedLabels, mean);
      const maxVal = Math.max(...values);

      // Vertical mean line as a dataset with null values except at mean position
      const meanData = strLabels.map((_, i) => (i === targetIndex ? maxVal : null));
      datasets.push({
        type: 'bar' as const,
        label: `Média (${mean.toFixed(1)})`,
        data: meanData,
        backgroundColor: 'rgba(16,185,129,0.9)',
        borderColor: '#10b981',
        borderWidth: 2,
        barThickness: 3,
      });
    }

    chart = new Chart(canvas, {
      type: 'bar',
      data: { labels: strLabels, datasets },
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

  function hexToRgba(hex: string, alpha: number): string {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!result) return hex;
    const r = parseInt(result[1], 16);
    const g = parseInt(result[2], 16);
    const b = parseInt(result[3], 16);
    return `rgba(${r},${g},${b},${alpha})`;
  }

  function findClosestIndex(arr: number[], target: number): number {
    let closest = 0;
    let minDiff = Math.abs(arr[0] - target);
    for (let i = 1; i < arr.length; i++) {
      const diff = Math.abs(arr[i] - target);
      if (diff < minDiff) { minDiff = diff; closest = i; }
    }
    return closest;
  }
</script>

<canvas bind:this={canvas}></canvas>
