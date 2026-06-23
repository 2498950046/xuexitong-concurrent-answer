# Concurrent Homework Runner Design

## Goal

Add a workflow that no longer requires manually copying one homework URL at a time. The user logs in once, manually opens the homework list page, confirms readiness in the terminal, and the program discovers unfinished homework items. The program then runs configurable concurrent workers, each using an independent Chrome/Driver window, to auto-answer one homework at a time. Submitting remains manual.

## Current Context

The project already has a single-homework flow in `finish_work.py`:

1. Read config.
2. Start Chrome.
3. Login.
4. Open `XUEXITONG_WORK_URL`.
5. Extract questions.
6. Ask the AI for answers.
7. Normalize and validate answers.
8. Click answers.

Relevant modules:

- `utils/start_browser.py`: starts a configured ChromeDriver.
- `utils/login.py`: performs login.
- `utils/find_questions.py`: extracts questions from a homework page.
- `utils/ai.py`: requests answers.
- `utils/answers.py`: parses, normalizes, and validates answers.
- `utils/click_answer.py`: clicks answers.
- `utils/course.py`: contains partial course/homework navigation helpers.

The new feature should reuse the single-homework answer pipeline instead of duplicating it.

## Requirements

### Manual Homework List Entry

- Start a controller Chrome window.
- Login using existing credentials/config.
- Let the user manually navigate to the homework list page.
- Terminal prompts: `已进入作业列表页后输入 y 继续`.
- After the user enters `y`, scan the current browser page for homework items.

### Homework Discovery

The scanner should extract best-effort fields:

- `title`
- `url`
- `work_id` if available
- `status_text`
- `is_submitted`
- `is_openable`

Only unfinished/openable homework should enter the queue. The first implementation can use conservative selectors and text heuristics, then print discovered items so the user can catch selector drift.

### Worker Model

- Use independent Chrome/Driver instances per worker.
- Do not share a Selenium `driver` across threads.
- Worker count is configurable with `XUEXITONG_WORKER_COUNT`, default `4`.
- Each worker opens one homework in its own window and runs the existing answer flow.
- If opening a homework fails, print the URL and allow manual recovery for that worker.

### Manual Submission

- The script never clicks submit.
- After auto-answering, each worker waits for the user to inspect, manually submit, and close that worker window.
- Once the window is closed, the worker becomes available for the next task.

### Refresh Loop

- The controller periodically or manually refreshes the homework list after workers finish.
- The user can be prompted to refresh manually and enter `y`.
- The scanner runs again and adds newly unfinished/openable homework not already processed.
- The process ends when no unfinished/openable homework remains and all workers are idle.

## Recommended Architecture

### `utils/homework_list.py`

Responsible for scanning the current homework list page.

Public functions:

- `scan_homework_list(driver) -> list[HomeworkItem]`
- `filter_unfinished(items) -> list[HomeworkItem]`

`HomeworkItem` should be a dataclass with title, url, work_id, status_text, and flags.

### `utils/homework_runner.py`

Responsible for answering one homework URL using an existing driver.

Public function:

- `answer_homework(driver, url, config) -> HomeworkRunResult`

This function should contain the reusable core currently embedded in `finish_work.py`.

### `utils/concurrent_runner.py`

Responsible for queueing and worker orchestration.

Public function:

- `run_concurrent_homework_session(config) -> int`

Responsibilities:

- Start controller browser and login.
- Wait for user confirmation on the homework list page.
- Scan homework items.
- Maintain a thread-safe queue.
- Start worker threads, each with its own Chrome/Driver.
- Track processed `work_id` or URL values to avoid duplicates.
- Wait for worker windows to close before reusing the worker.
- Trigger rescans until work is complete.

### `batch_homework.py`

New command-line entry point for the multi-homework workflow.

The existing `finish_work.py` should remain as the single-homework URL flow.

## Data Flow

```text
controller driver
  -> login
  -> user manually opens homework list
  -> scan_homework_list
  -> unfinished queue
  -> worker-1 independent driver -> answer_homework -> wait for manual submit/close
  -> worker-2 independent driver -> answer_homework -> wait for manual submit/close
  -> worker-N independent driver -> answer_homework -> wait for manual submit/close
  -> controller refresh/rescan
  -> repeat until no unfinished homework
```

## Error Handling

- If list scanning finds no items, print current URL and prompt the user to confirm they are on the homework list page.
- If a worker cannot open a homework URL, print the title and URL, then allow the user to manually open it in that worker window and type `y`.
- If AI answer parsing fails, stop only that homework and keep the worker/browser open for inspection.
- If answer validation fails, do not click anything for that homework.
- If a worker crashes, mark that homework as failed and continue with other workers.

## Testing Strategy

Unit tests should cover:

- Homework item filtering by status text.
- URL/workId extraction.
- Duplicate suppression by work_id or URL.
- Worker count config parsing.
- Single-homework runner behavior around empty questions, invalid AI answers, and validation failures.

Selenium/browser behavior should be verified manually first because the real Chaoxing DOM may vary. The code should print enough diagnostics to tune selectors without guessing.

## Open Decisions Resolved

- Worker model: independent Chrome/Driver per worker.
- Submission: always manual.
- Initial homework list navigation: manual after login, confirmed with terminal `y`.

