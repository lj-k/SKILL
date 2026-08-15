---
name: "html-frontend-checker"
description: "Comprehensive HTML frontend checker for technical documentation. Invoke when creating/modifying HTML docs, before delivery, or when diagnosing HTML bugs. Covers structure, CSS, JS, navigation, diagrams, content, and version integrity."
---

# HTML Frontend Checker

## When to Invoke

- After creating or modifying any HTML documentation file
- Before delivering an HTML document to verify compliance
- When diagnosing HTML frontend bugs (broken scroll-spy, missing JS, layout issues)
- After restoring/rebuilding HTML from backups (to detect JS stripping or corruption)
- When auditing a directory of HTML files for quality

## What It Does

Runs 80+ automated checks across 8 categories, derived from 40+ historical bugs found across 5 documentation projects. Produces a self-contained HTML report with pass/fail/warning/error status per check.

## Usage

```bash
# Check a single file
python3 html_frontend_checker.py --file path/to/file.html

# Check all HTML files in a directory
python3 html_frontend_checker.py --dir path/to/directory

# List all registered checks
python3 html_frontend_checker.py --list

# Filter by tags
python3 html_frontend_checker.py --file path/to/file.html --tags structure,css

# Custom output path
python3 html_frontend_checker.py --file path/to/file.html --output report.html
```

## Check Categories

| Category | Checks | Key Areas |
|----------|--------|-----------|
| structure | 18 | Tag pairing (div/html/body/script/style/code/pre/figure/details/article/section), heading hierarchy, DOM element position, stray tags |
| css | 15 | Modal transparency, no size constraints, sidebar nowrap, overflow-x hidden, margin-left, white background, table-layout fixed, responsive cascade order |
| js | 16 | Function completeness (scroll-spy/collapse/diagram/sidebar/tooltip/back-to-top), DOMContentLoaded, async mermaid, duplicate detection, null-reference prevention |
| navigation | 10 | Sidebar presence, ToC presence, link integrity, scroll-spy attributes, sidebar-heading count match, scroll-spy recalc after fold |
| diagram | 12 | Viewer buttons (zoom/drag/pan/reset/ESC/prev-next), no duplicate buttons, figure.diagram wrapping, figcaption presence, SVG container |
| content | 8 | Code block default collapsed, heading numbering, table caption, figure numbering, cross-reference consistency, callout presence |
| version | 6 | Version consistency (3 locations), version format (0.01+), filename-version match, corruption detection, backup file detection |
| known_bugs | 8 | Mermaid label compatibility, double-nested code, hardcoded duplicate buttons, collapsed-by-default sections, version mixing |

## Historical Bug Prevention

This checker encodes lessons from 40+ bugs across these projects:
- C910 CIU/L2 Cache Design (v0.01-v0.22, 18 versions)
- GEM5 Architecture Simulation Manual (v0.01-v0.07)
- SOC Integration Challenges (v0.01-v0.03)
- CHI Design Implementation (v0.01-v0.09)
- CMN-700 TRM (v0.01)

See `known_bugs.md` for the complete catalog of historical bugs and their detection rules.

## Report Format

The generated HTML report includes:
- Summary cards (pass/fail/warning/error counts, pass rate, file count, duration)
- Failure distribution by category
- Per-file collapsible detail panels with status icons
- Color-coded pass rate (green >=90%, orange >=70%, red <70%)

## Integration with Existing Tools

This checker is designed to complement (not replace) the existing `html-check` tool. Key differences:
- **html-check**: 51 checks, focuses on base structure and content
- **html-frontend-checker**: 80+ checks, adds CSS compliance, JS integrity, diagram viewer, known bug patterns, and corruption detection

Both tools can be run together for maximum coverage.
