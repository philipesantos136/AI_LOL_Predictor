<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import gsap from 'gsap';

  let matchId = $page.params.id;
  let matchData: any = $state(null);
  let loading = $state(true);

  async function fetchDetails() {
    try {
      const res = await fetch(`http://localhost:8000/api/live/games`);
      const games = await res.json();
      // Encontra a partida específica
      matchData = games.find((g: any) => g.game_id === matchId || g.match_id === matchId);
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchDetails();
    gsap.from('.fade-in', { opacity: 0, y: 15, duration: 0.6, stagger: 0.1 });
    
    const interval = setInterval(fetchDetails, 10000);
    return () => clearInterval(interval);
  });
</script>

<div class="p-8 font-sans bg-[#0f172a] min-h-screen text-white fade-in">
  <a href="/" class="text-blue-400 hover:text-blue-300 mb-6 inline-flex border border-blue-900 px-4 py-2 rounded-lg transition-colors bg-[#1e293b]">
    ← Voltar ao Dashboard
  </a>

  {#if loading}
    <div class="h-64 flex items-center justify-center animate-pulse text-slate-500">
      Sincronizando Telemetria...
    </div>
  {:else if !matchData}
    <div class="bg-[#1e293b] p-10 rounded-xl border border-slate-700 text-center fade-in text-red-300">
      ⚠️ Partida não encontrada ou os dados da Riot Esports API ainda não estão disponíveis.<br>
      Aguarde o status "In-Game".
    </div>
  {:else}
    <!-- Cabecalho -->
    <div class="text-center mb-10 fade-in">
      <h1 class="text-3xl font-extrabold text-[#90CDF4]">{matchData.league}</h1>
      <p class="text-slate-400 mt-2">Jogo {matchData.game_number || 1} • Status: <span class="text-red-400 uppercase font-bold">{matchData.state}</span></p>
    </div>

    <!-- Placar Ouro e Kills -->
    <div class="flex items-center justify-between bg-[#1e293b] p-8 rounded-2xl shadow-xl border border-[#334155] mb-8 fade-in">
      
      <!-- Azul -->
      <div class="flex flex-col items-center">
        <h2 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-blue-200">
          {matchData.team_blue.name}
        </h2>
        <div class="text-4xl font-black mt-2 text-blue-300">{matchData.blue_kills ?? '-'} Kills</div>
        <div class="text-sm font-medium mt-1 text-slate-400">💰 {matchData.blue_gold ? (matchData.blue_gold/1000).toFixed(1) + 'k' : '-'}</div>
      </div>

      <div class="text-5xl font-black text-slate-600 px-10">VS</div>

      <!-- Vermelho -->
      <div class="flex flex-col items-center">
        <h2 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-red-400 to-red-200">
          {matchData.team_red.name}
        </h2>
        <div class="text-4xl font-black mt-2 text-red-300">{matchData.red_kills ?? '-'} Kills</div>
        <div class="text-sm font-medium mt-1 text-slate-400">💰 {matchData.red_gold ? (matchData.red_gold/1000).toFixed(1) + 'k' : '-'}</div>
      </div>

    </div>

    <!-- Tabela Jogadores (Simplificada) -->
    <div class="grid grid-cols-2 gap-8 fade-in">
      
      <!-- Blue Table -->
      <div class="bg-[#1e293b] p-4 rounded-xl border border-blue-900">
        <h3 class="font-bold text-center text-blue-400 mb-4 uppercase">Equipe Azul</h3>
        {#if matchData.blue_champs && matchData.blue_champs.length > 0}
          <div class="flex flex-col gap-3">
             {#each matchData.blue_champs as p}
               <div class="flex justify-between items-center bg-[#0a1628] p-3 rounded-lg border border-slate-700">
                 <div class="flex items-center gap-3">
                   <img src="https://ddragon.leagueoflegends.com/cdn/14.5.1/img/champion/{p.champion}.png" class="w-10 h-10 rounded-md border border-slate-600" alt={p.champion}>
                   <div>
                     <div class="font-bold text-sm text-slate-200">{p.summonerName}</div>
                     <div class="text-xs text-slate-500">{p.role}</div>
                   </div>
                 </div>
                 <div class="text-right">
                   <div class="font-mono text-sm text-[#90CDF4]">{p.kills}/{p.deaths}/{p.assists}</div>
                   <div class="text-xs text-slate-400">{p.cs} CS</div>
                 </div>
               </div>
             {/each}
          </div>
        {:else}
          <div class="text-center text-slate-500 py-10">Escalação indisponível</div>
        {/if}
      </div>

      <!-- Red Table -->
      <div class="bg-[#1e293b] p-4 rounded-xl border border-red-900">
        <h3 class="font-bold text-center text-red-400 mb-4 uppercase">Equipe Vermelha</h3>
        {#if matchData.red_champs && matchData.red_champs.length > 0}
          <div class="flex flex-col gap-3">
             {#each matchData.red_champs as p}
               <div class="flex justify-between items-center bg-[#0a1628] p-3 rounded-lg border border-slate-700">
                 <div class="flex items-center gap-3">
                   <img src="https://ddragon.leagueoflegends.com/cdn/14.5.1/img/champion/{p.champion}.png" class="w-10 h-10 rounded-md border border-slate-600" alt={p.champion}>
                   <div>
                     <div class="font-bold text-sm text-slate-200">{p.summonerName}</div>
                     <div class="text-xs text-slate-500">{p.role}</div>
                   </div>
                 </div>
                 <div class="text-right">
                   <div class="font-mono text-sm text-[#FC8181]">{p.kills}/{p.deaths}/{p.assists}</div>
                   <div class="text-xs text-slate-400">{p.cs} CS</div>
                 </div>
               </div>
             {/each}
          </div>
        {:else}
          <div class="text-center text-slate-500 py-10">Escalação indisponível</div>
        {/if}
      </div>

    </div>
  {/if}
</div>
