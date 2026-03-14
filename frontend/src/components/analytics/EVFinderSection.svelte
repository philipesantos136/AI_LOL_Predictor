<script lang="ts">
  import type { EVFinderSection, EVFinderTeamCard, BetEntryData } from '$lib/types/analytics';
  import BetEntry from './BetEntry.svelte';

  interface Props {
    data: EVFinderSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();

  const riskTiers = [
    { key: 'low' as const, label: '🟢 Baixo Risco' },
    { key: 'med' as const, label: '🟡 Risco Médio' },
    { key: 'high' as const, label: '🔴 Alto Risco' },
  ];

  function entriesByRisk(entries: BetEntryData[], tier: 'low' | 'med' | 'high'): BetEntryData[] {
    return entries.filter(e => e.risk_tier === tier);
  }

  function hasAnyEntries(markets: Record<string, BetEntryData[]>): boolean {
    return Object.values(markets).some(entries => entries.length > 0);
  }
</script>

<div class="section-wrapper">
  <!-- Green gradient header -->
  <div class="ev-header">
    <h2 class="ev-title">🎯 Expected Value Finder (Odd Mining)</h2>
    <p class="ev-subtitle">
      Algoritmo de varredura buscando Edges Estatísticos baseados nos Modelos do Elixir
    </p>
  </div>

  <!-- T1 Card -->
  <div class="team-card t1-card">
    <div class="team-card-header t1-header">
      <span class="team-card-title">{team1}</span>
      <span class="team-card-sub">Entradas de Valor Organizadas</span>
    </div>
    <div class="team-card-body">
      {#if hasAnyEntries(data.t1_card.markets)}
        {#each Object.entries(data.t1_card.markets) as [market, entries]}
          {#if entries.length > 0}
            <div class="market-group">
              <div class="market-title">{market}</div>
              {#each riskTiers as tier}
                {#if entriesByRisk(entries, tier.key).length > 0}
                  <div class="risk-tier-header">{tier.label}</div>
                  {#each entriesByRisk(entries, tier.key) as entry}
                    <BetEntry {entry} />
                  {/each}
                {/if}
              {/each}
            </div>
          {/if}
        {/each}
      {:else}
        <p class="no-entries">Nenhuma entrada de valor encontrada para {team1}.</p>
      {/if}
    </div>
  </div>

  <!-- T2 Card -->
  <div class="team-card t2-card">
    <div class="team-card-header t2-header">
      <span class="team-card-title">{team2}</span>
      <span class="team-card-sub">Entradas de Valor Organizadas</span>
    </div>
    <div class="team-card-body">
      {#if hasAnyEntries(data.t2_card.markets)}
        {#each Object.entries(data.t2_card.markets) as [market, entries]}
          {#if entries.length > 0}
            <div class="market-group">
              <div class="market-title">{market}</div>
              {#each riskTiers as tier}
                {#if entriesByRisk(entries, tier.key).length > 0}
                  <div class="risk-tier-header">{tier.label}</div>
                  {#each entriesByRisk(entries, tier.key) as entry}
                    <BetEntry {entry} />
                  {/each}
                {/if}
              {/each}
            </div>
          {/if}
        {/each}
      {:else}
        <p class="no-entries">Nenhuma entrada de valor encontrada para {team2}.</p>
      {/if}
    </div>
  </div>

  <!-- Joint Card -->
  <div class="team-card joint-card">
    <div class="team-card-header joint-header">
      <span class="team-card-title">{team1} vs {team2}</span>
      <span class="team-card-sub">Entradas de Valor Organizadas</span>
    </div>
    <div class="team-card-body">
      {#if hasAnyEntries(data.joint_card.markets)}
        {#each Object.entries(data.joint_card.markets) as [market, entries]}
          {#if entries.length > 0}
            <div class="market-group">
              <div class="market-title">{market}</div>
              {#each riskTiers as tier}
                {#if entriesByRisk(entries, tier.key).length > 0}
                  <div class="risk-tier-header">{tier.label}</div>
                  {#each entriesByRisk(entries, tier.key) as entry}
                    <BetEntry {entry} />
                  {/each}
                {/if}
              {/each}
            </div>
          {/if}
        {/each}
      {:else}
        <p class="no-entries">Nenhuma entrada de valor conjunta encontrada.</p>
      {/if}
    </div>
  </div>
</div>

<style>
  .section-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .ev-header {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.08) 100%);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 0.75rem;
    padding: 1.25rem 1.5rem;
  }

  .ev-title {
    color: #34d399;
    font-size: 1.125rem;
    font-weight: 700;
    margin: 0 0 0.375rem 0;
  }

  .ev-subtitle {
    color: #6ee7b7;
    font-size: 0.8125rem;
    margin: 0;
    opacity: 0.8;
  }

  .team-card {
    background: #1e293b;
    border-radius: 0.75rem;
    border: 1px solid #334155;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .team-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  }

  .team-card-header {
    padding: 0.875rem 1.25rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .t1-header {
    background: linear-gradient(90deg, rgba(59, 130, 246, 0.2) 0%, rgba(59, 130, 246, 0.05) 100%);
    border-bottom: 1px solid rgba(59, 130, 246, 0.25);
  }

  .t2-header {
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.2) 0%, rgba(239, 68, 68, 0.05) 100%);
    border-bottom: 1px solid rgba(239, 68, 68, 0.25);
  }

  .joint-header {
    background: linear-gradient(90deg, rgba(168, 85, 247, 0.2) 0%, rgba(168, 85, 247, 0.05) 100%);
    border-bottom: 1px solid rgba(168, 85, 247, 0.25);
  }

  .t1-card {
    border-left: 3px solid #3b82f6;
  }

  .t2-card {
    border-left: 3px solid #ef4444;
  }

  .joint-card {
    border-left: 3px solid #a855f7;
  }

  .team-card-title {
    font-size: 0.9375rem;
    font-weight: 700;
    color: #f1f5f9;
  }

  .team-card-sub {
    font-size: 0.75rem;
    color: #64748b;
  }

  .team-card-body {
    padding: 1rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .market-group {
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .market-title {
    font-size: 0.8125rem;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.375rem 0;
    border-bottom: 1px solid rgba(51, 65, 85, 0.6);
    margin-bottom: 0.5rem;
  }

  .risk-tier-header {
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748b;
    padding: 0.25rem 0;
    margin-top: 0.375rem;
  }

  .no-entries {
    color: #475569;
    font-size: 0.8125rem;
    font-style: italic;
    margin: 0;
    padding: 0.5rem 0;
  }
</style>
