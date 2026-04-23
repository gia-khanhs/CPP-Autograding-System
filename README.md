# CPP-Autograding-System

A Python-based system for processing, auto-correcting, and grading weekly C++ programming submissions.

## Overview

This project is built to reduce the manual workload of grading large batches of C++ assignments.  
It processes raw weekly submission folders, extracts assignment PDFs and student archives, uses an LLM to auto-correct code with minimal edits, and then grades each submission by comparing the corrected code against the original using weighted structural similarity.

The system currently includes:

- a GUI entrypoint for running the workflow
- a data pipeline for ingestion, processing, caching, and updating weeks
- an LLM-based C++ auto-correction module
- a grading module based on line similarity and weighted code-role classification
- Excel score export for each processed week

---

## Main Workflow

The project follows this high-level pipeline:

1. **Load raw course data**
   - Reads weekly folders from the raw data directory
   - Normalizes week names to the form `W1`, `W2`, etc.
   - Extracts submission archives and discovers student C++ projects

2. **Process assignment data**
   - Reads the assignment PDF
   - Extracts problem titles and statements
   - Classifies each problem as:
     - `paper`
     - `manual_coding`
     - `online_judge`
   - For online judge problems, attempts to retrieve the exact statement from the linked URL

3. **Cache processed weeks**
   - Saves processed output to a separate processed-data directory
   - Uses folder fingerprints / hashes to detect outdated weeks and reprocess only what changed

4. **Auto-correct student code**
   - Loads the original C++ project
   - Sends the project plus problem details to an LLM
   - Requests the smallest possible set of edits needed to make the solution correct
   - Writes the corrected project to the output folder

5. **Grade each submission**
   - Compares original and corrected code line by line
   - Classifies lines into roles such as logic, input, output, and other
   - Applies weighted scoring and insertion penalties
   - Produces a final score on a 10-point scale

6. **Export results**
   - Writes one Excel file per week
   - Each row is a submitter
   - Each column is a problem (`P1`, `P2`, ...)

---

## Repository Structure

```text
CPP-Autograding-System/
├── config/
│   └── paths.py
├── docs/
│   ├── papers/
│   ├── papers.md
│   └── papers.pdf
├── logs/
├── src/
│   ├── cpp/
│   │   └── program.py
│   ├── data/
│   │   ├── consts.py
│   │   ├── fingerprints.py
│   │   ├── ingestion.py
│   │   ├── persistence.py
│   │   ├── pipeline.py
│   │   ├── processing.py
│   │   └── structures.py
│   ├── grading/
│   │   ├── correction.py
│   │   ├── grade.py
│   │   ├── line_classifier.py
│   │   ├── pipeline.py
│   │   └── similarity.py
│   ├── gui/
│   │   ├── backend.py
│   │   ├── frontend.py
│   │   ├── logger.py
│   │   ├── main.py
│   │   └── state.py
│   ├── llm/
│   │   ├── auto_corrector.py
│   │   ├── auto_corrector_old.py
│   │   ├── injection_detector.py
│   │   ├── oj_problem.py
│   │   └── problem_classifier.py
│   └── misc/
├── main.py
├── README.md
└── requirements.txt
```

### Folder roles

- `src/data/`: ingestion, processing, persistence, and update logic for raw and processed course data
- `src/llm/`: LLM-powered problem classification, online-judge statement retrieval, and code correction
- `src/grading/`: auto-correction orchestration, similarity scoring, line classification, and score export
- `src/gui/`: application frontend/backend and run-state management
- `src/cpp/`: C++ project discovery, include handling, and compile-related helpers
- `config/`: project paths and local configuration
- `docs/`: project notes and research references
- `logs/`: runtime logs
- `data/` and `output/`: created locally during use and ignored by git

---

## Data and Output Paths

The project uses the following local directories:

- raw data: `data/raw`
- processed data: `data/processed`
- corrected code output: `output/corrected_code`
- score output: `output/scores`

These folders are created or used through `config/paths.py`.

---

## Expected Input Layout

The system is designed around a weekly folder structure inside `data/raw`.

At a high level, each week folder should contain:

- one assignment PDF
- one master submissions archive

During ingestion, the system:

- extracts the master archive into a `SUBMISSIONS` folder
- extracts per-submission archives
- searches each student project recursively for a C++ file containing `main`

Because the ingestion logic assumes a fairly specific archive layout, this project is best suited to the Moodle-style export structure it was built around.

---

## Requirements

### Python

Use **Python 3.12+**.

The codebase uses modern generic class syntax such as:

- `class Ingestor[T]`
- `class Processor[T]`

which requires Python 3.12 or newer.

### System tools

You will likely need:

- **g++**  
  used for syntax-only compilation checks

- **libclang / clang Python bindings**  
  used to parse C++ files and detect `main`

- **unrar** commandline tool
  used to help with extracting .rar files

### Python packages

All required packages are specified in the file requirements.txt, to install, run:
```
pip install -r requirements.txt
```

---

## API Key Setup

The LLM modules import `GROQ_API_KEY` from `config/apikey.py`, and that file is gitignored.

Create:

```python
# config/apikey.py
GROQ_API_KEY = "your_api_key_here"
```

Without that file, the LLM-based problem classification and code correction pipeline will not run.

---

## Running the Project

From the repository root:

```bash
python main.py
```

`main.py` launches the GUI through `src.gui.main`.

---

## How Grading Works

The grading pipeline does **not** run hidden test cases or evaluate program output directly.

Instead, the current grading approach is based on **how much the corrected version differs from the original submission**.

### Current scoring idea

- The original and corrected code are compared line by line using `SequenceMatcher`
- Modified lines receive partial credit based on text similarity
- Each original line is classified into a coarse role:
  - `logic`
  - `input`
  - `output`
  - `other`
- Roles are weighted:
  - logic: `3.0`
  - input: `2.0`
  - output: `1.0`
  - other: `0.2`
- Inserted corrected lines can add penalty through the total weight
- Final scores are scaled to a **10-point score**

This makes the system closer to a **minimal-edit correction-based grader** than a traditional judge-based grader.

---

## Output

For each processed week, the system saves:

- corrected student code under `output/corrected_code`
- an Excel score sheet under `output/scores`

Example score file:

```text
output/scores/W1_scores.xlsx
```

The exported sheet uses:

- rows = submitters
- columns = problems (`P1`, `P2`, ...)

---

## Credits

Created by **Chu Nguyen Gia Khanh**.
