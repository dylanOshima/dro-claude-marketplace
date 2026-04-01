---
name: chronos
description: |
  Use this skill when the user asks to schedule a command, set up a cron job, create a recurring task, schedule a one-off task, list scheduled jobs, search for scheduled jobs, enable or disable a job, or remove a scheduled job. Trigger phrases include: "schedule this", "run this every", "set a cron job", "remind me", "run this tomorrow", "run this at", "list my cron jobs", "what's scheduled", "remove that job", "disable that job". Also trigger when you (as an LLM) need to schedule a command to run later — for example, retrying after a rate limit, running a task at a specific time, or scheduling a follow-up action.
---

# Chronos

You are helping the user manage scheduled tasks using the `chronos` CLI. Chronos is a friendly interface over the system's `crontab` and `at` commands that understands natural language schedules.

## Step 1: Ensure Chronos is Installed

Before running any chronos command, check if it's available:

```bash
command -v chronos
```

If not found, check if cargo is available and install:

```bash
if command -v cargo &>/dev/null; then
    cargo install --git https://github.com/dylanOshima/chronos
else
    echo "Rust/Cargo is required. Install with: brew install rust"
fi
```

If cargo is not available, tell the user they need to install Rust first (`brew install rust` or `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`), then retry.

Do NOT proceed to step 2 until chronos is confirmed installed.

## Step 2: Determine the Action

Based on the user's request, map to one of these chronos commands:

| User intent | Command |
|---|---|
| Schedule a recurring task | `chronos add "<schedule>" "<command>" [--id <name>] [--source <source>]` |
| Schedule a one-off task | `chronos add "<datetime>" "<command>" [--id <name>] [--source <source>]` |
| List all scheduled jobs | `chronos list` or `chronos list --json` |
| Search for a job | `chronos search "<query>"` |
| Remove a job | `chronos remove <id-or-row-number>` |
| Disable a job | `chronos disable <id-or-row-number>` |
| Enable a job | `chronos enable <id-or-row-number>` |

### Schedule syntax

Chronos auto-detects recurring vs one-off:

**Recurring** (keywords: "every", "daily", "weekly", "monthly", "hourly", or raw cron expressions):
- `"every sunday at 6am"`
- `"daily at 8am"`
- `"every weekday at 9:30am"`
- `"every 2 hours"`
- `"0 8 * * *"` (raw cron)

**One-off** (specific dates/times):
- `"tomorrow at 1am"`
- `"sunday 6pm"` (this coming sunday)
- `"march 31 at noon"`

### Flags

- `--id <name>` — always provide a short, descriptive kebab-case id when adding jobs
- `--source claude` — always pass this flag when you (as an LLM) are scheduling a job on behalf of the user
- `--desc "<text>"` — optionally add a description
- `--force` — skip duplicate detection

## Step 3: Execute the Command

Run the chronos command via Bash. When scheduling:

- Always include `--id` with a descriptive name
- Always include `--source claude` when you are the one scheduling
- Confirm success by showing the output

When listing or searching:

- Default to the table output for human readability
- Use `--json` when you need to parse the results programmatically

## Examples

**User asks to schedule a daily brief:**
```bash
chronos add "daily at 8am" "claude -p 'write a daily brief'" --id daily-brief --source claude
```

**User asks to retry something after a rate limit:**
```bash
chronos add "tomorrow at 6am" "claude -p 'retry the deploy'" --id retry-deploy --source claude
```

**User asks what's scheduled:**
```bash
chronos list
```

**User asks to find jobs related to backups:**
```bash
chronos search "backup"
```

**User asks to remove a job:**
```bash
chronos remove daily-brief
```

## When You Schedule on Your Own Behalf

When you (as an LLM) need to defer work to a later time — for example, retrying a failed operation, scheduling a follow-up check, or running a command when conditions are met — use chronos directly:

1. Always use `--source claude` so the user can see what you scheduled
2. Always use `--id` with a clear name describing the purpose
3. Inform the user what you scheduled and why
