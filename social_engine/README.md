# social_engine

## 状态

顶层独立目录，**未**纳入 monorepo（apps/+packages/）。原因是它跟灵文流水线没有直接业务耦合。

## 计划

- 若 Phase 17.x 后仍有活跃维护，再决定是否迁入 apps/social/。
- 否则保留顶层独立。

## 关联

- 仅在 CI 中按 opt-in 触发（参见 .github/workflows/social-engine-*）。
- 数据: `.state/social_engine/`。