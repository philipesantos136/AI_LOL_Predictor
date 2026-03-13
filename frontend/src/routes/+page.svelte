<script lang="ts">
  import { onMount } from 'svelte';
  import gsap from 'gsap';
  import MatchCard from '$lib/components/MatchCard.svelte';

  let liveGames: any[] = [];
  let pandascoreFixtures: any[] = [];
  let loading = true;
  let titleElement: HTMLElement;
  let subtitleElement: HTMLElement;

  async function fetchMatches() {
    try {
      // Fetch live matches
      const liveRes = await fetch('http://localhost:8000/api/live/games');
      if (liveRes.ok) {
        liveGames = await liveRes.json();
      }

      // Fetch pandascore fixtures (today scheduled)
      const psRes = await fetch('http://localhost:8000/api/live/pandascore');
      if (psRes.ok) {
        pandascoreFixtures = await psRes.json();
      }
    } catch (e) {
      console.error("Error fetching games:", e);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchMatches();

    gsap.from(titleElement, { opacity: 0, y: -20, duration: 0.8, ease: "power3.out" });
    gsap.from(subtitleElement, { opacity: 0, y: -10, duration: 0.8, delay: 0.2, ease: "power3.out" });

    // Polling every 10 seconds
    const interval = setInterval(fetchMatches, 10000);
    return () => clearInterval(interval);
  });
</script>

<div class="min-h-screen bg-[#0f172a] text-[#f8fafc] p-8 font-sans">
  
  <div class="mb-12 flex flex-col items-center justify-center text-center">
    <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[#1e293b] text-3xl shadow-lg">
      🏆
    </div>
    
    <h1 bind:this={titleElement} class="text-3xl font-extrabold tracking-tight text-white mb-2">
      Live Esports Dashboard
    </h1>
    <p bind:this={subtitleElement} class="text-[#cbd5e1] max-w-2xl text-sm">
      Partidas profissionais de League of Legends em tempo real. Os dados são atualizados automaticamente a cada 10 segundos.
    </p>
  </div>

  {#if loading && liveGames.length === 0 && pandascoreFixtures.length === 0}
    <div class="flex h-64 items-center justify-center">
      <div class="text-lg font-medium text-[#64748b] animate-pulse">Carregando partidas...</div>
    </div>
  {:else}
    
    <!-- AO VIVO -->
    <div class="mb-10">
      <h2 class="mb-6 text-center text-lg font-bold tracking-widest text-[#cbd5e1] uppercase">
        Ao Vivo (<span class="text-red-400">{liveGames.length}</span>)
      </h2>
      
      {#if liveGames.length > 0}
        <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {#each liveGames as match}
            <MatchCard {match} isLive={true} />
          {/each}
        </div>
      {:else}
        <div class="rounded-xl border border-[#1e293b] bg-[#0a1628] p-8 text-center text-sm text-[#64748b]">
          NENUM JOGO AO VIVO NESTE MOMENTO
        </div>
      {/if}
    </div>

    <!-- Divider -->
    <hr class="my-10 border-[#334155]" />

    <!-- JOGOS DO DIA (Pandascore fallback / Today scheduled) -->
    <div>
      <h2 class="mb-6 text-center text-lg font-bold tracking-widest text-[#cbd5e1] uppercase">
        Todos os Jogos do Dia (<span class="text-blue-400">{pandascoreFixtures.length}</span>)
      </h2>
      
      {#if pandascoreFixtures.length > 0}
        <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {#each pandascoreFixtures as match}
            <!-- Se já não estiver na lista de ao vivo, desenha aqui -->
            {#if !liveGames.some(l => l.match_id === match.match_id)}
              <MatchCard {match} isLive={false} />
            {/if}
          {/each}
        </div>
      {:else}
         <div class="rounded-xl border border-[#1e293b] bg-[#0a1628] p-8 text-center text-sm text-[#64748b]">
          NENHUM OUTRO JOGO ENCONTRADO PARA HOJE
        </div>
      {/if}
    </div>

  {/if}
</div>
