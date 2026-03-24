---
name: remember-that
description: Reflect on the current session to extract and persist learnings — corrections, processes, preferences, and domain knowledge — to the appropriate documentation (CLAUDE.md, auto-memory, or project docs). Use this skill whenever the user says "remember this", "remember that", "don't forget", "save this for next time", "learn from this", "capture that", or phrases like "write this down somewhere", "i want this documented", "save all the corrections". Also trigger when you notice the user correcting you on something for the second time — proactively offer to persist it. Trigger when the user demonstrates a workflow or process and wants it captured ("can you capture that?", "save this process"), when they share undocumented project/domain knowledge ("none of that was documented", "update the docs with what we discovered"), or when they ask you to reflect on session mistakes ("save those two things so we don't repeat this"). Do NOT trigger for normal coding tasks, file reads, git operations, README edits, PR reviews, or creating a new CLAUDE.md from scratch — only when the user wants to persist learnings from the current session.
---

# Remember That

You are reflecting on the current conversation to extract learnings and persist them so they carry across sessions. Your job is to be a thoughtful curator — capturing what matters, routing it to the right place, and skipping what's already known or ephemeral.

## When This Skill Activates

- The user explicitly says "remember this/that", "save this", "don't forget", etc.
- The user walks you through a process or workflow they want preserved
- The user shares domain context, preferences, or conventions that aren't in any docs yet

### Proactive Triggering on Repeated Corrections

If you notice the user correcting you on the same thing a second time in a session, don't wait for them to ask you to remember — they shouldn't have to. Instead, after acknowledging the correction, offer:

> "Should I save this so I remember it going forward?"

If they confirm, proceed with the full skill flow (scan, present plan, confirm, write). This is the highest-signal scenario — a repeated correction means the knowledge clearly isn't persisted and needs to be. Catching it proactively saves the user from having to manage your memory for you.

## Step 1: Scan the Conversation for Learnings

Read back through the current session and identify things worth remembering. Focus on:

**High-signal learnings (always capture):**
- Direct corrections: "no, use X not Y", "that's wrong", "actually..."
- Explicit requests: "remember:", "always do X", "never do Y"
- Process demonstrations: the user showed you a multi-step workflow
- Repeated corrections: you made the same mistake more than once in this session
- Tool rejections: the user blocked a tool call and explained why

**Medium-signal learnings (capture if substantive):**
- Preferences expressed through feedback: "perfect, do it like that", "yes exactly"
- Domain knowledge shared in passing: project relationships, team structure, technical constraints
- Conventions demonstrated by example: naming patterns, file organization, communication style

**Low-signal (skip unless explicitly asked):**
- One-off task details that won't recur
- Information already in CLAUDE.md or existing memory files
- Debugging steps specific to a transient issue
- Things derivable from code, git history, or project structure

Before listing anything, check what's already persisted. Read:
1. The project's `CLAUDE.md` (if it exists in the working directory)
2. The user's global `~/.claude/CLAUDE.md`
3. The project's auto-memory index at `~/.claude/projects/<project-path>/memory/MEMORY.md` (if it exists)
4. **Project documentation directories** — scan for existing docs structures (see "Discovering Project Docs" below)

Filter out anything that's already captured. The goal is *net new* knowledge only.

### Discovering Project Docs

Many projects maintain their own documentation beyond CLAUDE.md. Before proposing where to save learnings, check whether the project has a docs structure that should receive certain types of knowledge. Look for:

- `docs/`, `documentation/`, `wiki/`, `notes/` directories
- Architecture docs: `docs/architecture.md`, `docs/adr/`, `ARCHITECTURE.md`
- Runbooks or guides: `docs/runbooks/`, `docs/guides/`
- Design docs or specs: `docs/design/`, `docs/specs/`, `docs/plans/`
- READMEs in subdirectories that document specific subsystems

Also check `CLAUDE.md` and `CONTRIBUTING.md` for references to where documentation lives — projects sometimes have non-obvious locations (e.g., `docs/docs/plans/` in a Docusaurus project).

When you find a project docs structure, certain learnings belong there instead of (or in addition to) CLAUDE.md:

- **Architecture insights** from deep dives — understanding of how systems connect, why things are structured a certain way → architecture docs
- **Process/workflow documentation** — deployment steps, release procedures, onboarding steps → runbooks or guides
- **Design decisions and rationale** — why a particular approach was chosen → ADRs or design docs
- **Subsystem knowledge** — deep understanding of a specific module or service → that subsystem's README or docs section

The key distinction: CLAUDE.md tells Claude *how to behave*. Project docs capture *knowledge about the system* that benefits anyone (human or AI) reading them. When a learning is more about understanding than instruction, it likely belongs in project docs.

## Step 2: Present the Learning Plan

Keep the summary short and scannable. Show the destination path and a one-line description of what you'd save — no verbatim content previews, no routing rationale. The user can see where things are going and ask questions if something looks wrong. Group by destination:

```
Here's what I'd save from this session:

**Project CLAUDE.md** (`./CLAUDE.md`)
- Add no-database-mocking rule to Testing section (with why: mocks hid a prod migration failure)

**Global CLAUDE.md** (`~/.claude/CLAUDE.md`)
- Preference for integration tests over mocks across all projects

**Project Docs** (`docs/runbooks/deployment.md`)
- Full 5-step deployment process

**Auto-Memory**
- feedback: testing approach correction (repeated twice this session)
```

Always show the actual file paths. For CLAUDE.md updates, note whether it's project-level or global scope.

### Routing Rules

Use these to decide where each learning goes:

| What you learned | Where it goes |
|---|---|
| Project convention, structure, tooling | Project `./CLAUDE.md` |
| Architecture insights, system understanding | Project docs (e.g., `docs/architecture.md`) |
| Process/workflow steps (deploy, release, etc.) | Project docs (e.g., `docs/runbooks/`) |
| Design decisions and rationale | Project docs (e.g., ADRs, design docs) |
| Personal workflow preference, cross-project habit | Global `~/.claude/CLAUDE.md` |
| User role, background, domain expertise | Auto-memory (`user` type) |
| Correction or approach feedback | Auto-memory (`feedback` type) |
| Project context not in code (deadlines, team decisions) | Auto-memory (`project` type) |
| Pointers to external resources | Auto-memory (`reference` type) |
| Ambiguous scope — could be project or global | Ask the user |

Strong directives ("always use X", "never do Y") → CLAUDE.md. Softer context ("user prefers concise answers", "the migration is driven by compliance") → auto-memory.

## Step 3: Wait for Confirmation

Do not write anything until the user approves. They might:
- Approve everything: "looks good" / "yes" / "go ahead"
- Edit the list: "skip the first one" / "actually put that in global instead"
- Add something you missed: "also remember that..."
- Reject everything: "nevermind" / "not worth saving"

Respect their edits. If they redirect scope (e.g., "that should be project-level, not global"), follow their judgment — they know their setup better than you do.

## Step 4: Write the Learnings

Once approved, write each learning to its destination.

### Writing to CLAUDE.md files

Learnings should fit naturally into the existing document structure — not land as isolated bullets tacked onto the end. Think about what process or workflow the learning belongs to, and integrate it there.

1. Read the current file first and understand its sections and structure
2. Find the process or workflow the learning belongs to. If the file has a "## Making Commits" section and you're adding a lint step, add it as a numbered step in that workflow — not as a standalone "## Linting" section
3. If no relevant section exists, create one that frames the learning as part of a workflow. For example, instead of "- Use `make lint`, not `golangci-lint` directly", create:
   ```
   ## Making Commits
   Before submitting a commit:
   1. Run `make lint` to check for lint errors (use `make lint`, not `golangci-lint` directly — it includes extra checks)
   2. Fix any errors before committing
   ```
4. Keep the same style and formatting as the rest of the file
5. Don't duplicate existing content — if you're reinforcing something already there, strengthen the existing wording instead

### Writing to project docs

When adding to an existing project doc:
1. Read the current file and understand its structure and voice
2. Add the learning in the appropriate section, matching the existing style
3. If the doc uses a specific format (e.g., ADR template, numbered sections), follow it
4. Attribute the source where useful — "discovered during [date] session investigating [topic]"

When creating a new doc in the project's docs structure:
1. Follow existing naming conventions in that directory
2. Match the format of sibling docs
3. Keep it focused — one doc per topic, not a dump of everything learned

**Always cross-reference from CLAUDE.md.** When you create or update a project doc, also add a pointer in the project's CLAUDE.md so Claude knows the doc exists and when to consult it. For example, if you create `docs/runbooks/deployment.md`, add a line to CLAUDE.md like:
```
- See `docs/runbooks/deployment.md` for the full deployment process
```
Without this cross-reference, the doc might exist but Claude won't know to look there in future sessions.

If the project doesn't have an obvious docs structure and the learning is substantial enough to warrant its own doc (e.g., a full architecture deep-dive), suggest creating one and let the user decide where it should live.

### Writing to auto-memory

Follow the auto-memory system's conventions:
1. Create a file in `~/.claude/projects/<project-path>/memory/` with a descriptive kebab-case name (e.g., `feedback_testing-approach.md`, `user_background.md`)
2. Use the standard frontmatter format:

```markdown
---
name: [descriptive name]
description: [one-line description — specific enough to judge relevance later]
type: [user|feedback|project|reference]
---

[content — for feedback/project types, structure as rule/fact, then **Why:** and **How to apply:** lines]
```

3. Update `MEMORY.md` index with a pointer to the new file
4. If an existing memory file covers the same topic, update it instead of creating a duplicate

### Writing style

- Be concise. A learning that takes a paragraph to explain should probably be two bullets.
- Include the *why* when it's not obvious — "Use pytest instead of unittest" is less useful than "Use pytest instead of unittest — the project's CI is configured for pytest and unittest fixtures don't work with the existing conftest."
- Use the user's own words when possible. If they said "always run tests before deploying", don't rephrase it as "ensure test execution precedes deployment operations."
- Convert relative dates to absolute: "next Thursday" becomes "2026-03-26".

## Step 5: Confirm What Was Written

After writing, give a brief confirmation:

```
Done. Saved 3 learnings:
- Added testing convention to ./CLAUDE.md
- Created memory: feedback_api-naming.md
- Updated ~/.claude/CLAUDE.md with model preference
```

No need to re-list the full content — the user already approved it.

## Edge Cases

**The user says "remember this" but the thing is already saved:**
Tell them: "This is already captured in [location]. Want me to update the wording?"

**The user corrects you and seems frustrated:**
This is a strong signal that the correction has happened before. Check existing docs — if it's already there, the issue isn't memory but attention. Say so honestly: "I see this is already in CLAUDE.md — I should have caught it. I'll reinforce the wording."

**Conflicting information:**
If a new learning contradicts something already saved, flag it: "This conflicts with [existing learning]. Should I replace it, or is this a special case?"

**No learnings found:**
If the session doesn't have anything worth saving, say so: "I looked through this session and didn't find anything that isn't already captured or would be useful long-term. Anything specific you wanted me to remember?"
