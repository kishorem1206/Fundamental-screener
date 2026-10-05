# IMPORTANT DEVELOPMENT INSTRUCTION

Do NOT attempt to build the entire application in one generation, one response, or one task.

This is a serious, long-term project. Development can take many days or weeks, and that is completely acceptable.

You must divide the project into small, logical, dependency-aware phases and execute them incrementally.

Before implementing anything:

1. Inspect the existing repository and all existing MCP configurations.
2. Understand the available Kite MCP and TradingView MCP tools.
3. Create a complete implementation roadmap.
4. Break the roadmap into clearly defined milestones and sub-tasks.
5. Identify dependencies between tasks.
6. Maintain the roadmap in a Markdown file such as:
   `docs/IMPLEMENTATION_PLAN.md`

For every milestone:

- Clearly define the objective.
- List the exact tasks.
- Identify which files/modules will be created or modified.
- Implement only that milestone.
- Run tests and verify the implementation.
- Fix errors before moving forward.
- Update documentation.
- Mark completed tasks in `IMPLEMENTATION_PLAN.md`.
- Record important architectural decisions.
- Do not proceed to major dependent work if the current foundation is unstable.

## QUALITY OVER SPEED

Do NOT create a "name-sake" dashboard just to claim that the project is complete.

The goal is to build a genuinely useful, professional-grade stock analysis and screening platform.

Prioritize:

- Correctness
- Reliability
- Data provenance
- Performance
- Excellent UX
- Extensibility
- Maintainability
- Proper error handling
- Real MCP integration
- Proper testing
- Clean architecture

A partially completed but solid subsystem is much better than a large amount of incomplete or fake functionality.

Do not use placeholder/mock behavior in production paths merely to make features appear complete.

If a required capability is not yet implemented, explicitly document it and continue building the foundation needed for it.

## INCREMENTAL DEVELOPMENT

Work in dependency order.

For example:

Foundation
→ MCP integration
→ data normalization
→ universe management
→ database
→ indicator infrastructure
→ RSI/Bollinger
→ screening DSL
→ deterministic filter engine
→ orchestration
→ A2A communication
→ natural-language interface
→ dashboard
→ scoring/ranking
→ strategies
→ candlestick analysis
→ additional indicators
→ alerts
→ backtesting
→ future extensions

Do not skip foundational architecture merely because a UI feature looks more impressive.

## LONG-RUNNING PROJECT MEMORY

Maintain project knowledge in Markdown documentation so that development can continue across many sessions.

At minimum maintain:

`docs/IMPLEMENTATION_PLAN.md`
`docs/ARCHITECTURE.md`
`docs/DECISIONS.md`
`docs/MCP_INTEGRATIONS.md`
`docs/DEVELOPMENT_STATUS.md`

Before starting a new task/session:

1. Read these documents.
2. Inspect the current implementation.
3. Determine exactly what has already been completed.
4. Continue from the next unfinished task.
5. Never unnecessarily rebuild completed work.

At the end of every meaningful development session, update the documentation with:

- What was completed
- What remains
- Current known issues
- Tests performed
- Architectural decisions
- Next recommended task

## IMPORTANT

You are not being asked to finish the project as quickly as possible.

You are being asked to build it properly.

Take as many development iterations as necessary.

Never sacrifice architecture, correctness, UX, testing, or maintainability merely to reach a "finished" state.