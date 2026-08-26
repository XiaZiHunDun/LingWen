import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWorldStore = defineStore('world', () => {
  const activeTab = ref('characters')  // 'characters' | 'factions' | 'timeline' | 'lore'
  const canonLevelFilter = ref(null)    // null | 'Draft' | 'Provisional' | 'Established'
  const selectedCharacterId = ref(null)
  const proposalInboxOpen = ref(false)

  function switchTab(tab) {
    activeTab.value = tab
  }

  function setCanonLevelFilter(level) {
    canonLevelFilter.value = level
  }

  return {
    activeTab, canonLevelFilter, selectedCharacterId, proposalInboxOpen,
    switchTab, setCanonLevelFilter,
  }
})