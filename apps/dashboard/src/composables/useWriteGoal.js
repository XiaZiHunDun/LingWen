import { ref } from 'vue'

const STORAGE_KEY = 'lingwen.write_goal.daily'
const DEFAULT = 3000

export function useWriteGoal() {
  const stored = Number(localStorage.getItem(STORAGE_KEY)) || DEFAULT
  const dailyGoal = ref(stored)

  function setDailyGoal(n) {
    dailyGoal.value = n
    localStorage.setItem(STORAGE_KEY, String(n))
  }

  function isGoalMet(total) {
    return total >= dailyGoal.value
  }

  return { dailyGoal, setDailyGoal, isGoalMet }
}
