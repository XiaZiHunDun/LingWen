import { describe, it, expect, beforeEach } from 'vitest'
import { useWriteGoal } from '@/composables/useWriteGoal'

describe('useWriteGoal', () => {
  beforeEach(() => localStorage.clear())

  it('returns default goal of 3000 when not set', () => {
    const goal = useWriteGoal()
    expect(goal.dailyGoal.value).toBe(3000)
  })

  it('reads goal from localStorage', () => {
    localStorage.setItem('lingwen.write_goal.daily', '5000')
    const goal = useWriteGoal()
    expect(goal.dailyGoal.value).toBe(5000)
  })

  it('setDailyGoal persists to localStorage', () => {
    const goal = useWriteGoal()
    goal.setDailyGoal(8000)
    expect(goal.dailyGoal.value).toBe(8000)
    expect(localStorage.getItem('lingwen.write_goal.daily')).toBe('8000')
  })

  it('isGoalMet true when total >= daily', () => {
    const goal = useWriteGoal()
    goal.setDailyGoal(1000)
    expect(goal.isGoalMet(1000)).toBe(true)
    expect(goal.isGoalMet(999)).toBe(false)
  })
})
