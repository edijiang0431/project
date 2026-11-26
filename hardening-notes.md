# Hardening notes

## Main results checked for R2.1

- Current prepared data, USD 200, 2025 Q3: the new ranking caution list identifies Cuba (4 eligible cost quotes) and Somalia (5).
- Cuba across all selected quarters: the pooled ranking has no small-sample caution; the quarterly cost list identifies 29 affected points. These are different aggregation levels.

## Work list

- R2.1: implement the user's chosen nearby warning lists for 1–5 eligible cost quotes in the app ranking and cost trend. Preserve values, scores and markers; explain zero eligible costs separately. Implementation added; new tests pass. Full suite in UTF-8 mode has one pre-existing normalization failure; the user explicitly directed that it remain documented without changing scoring or its test during this refinement.

## Checks and findings

- Before implementation, ran `.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider tests/test_small_sample_cautions.py` from `prof-build-M2`: 8 failed, 2 passed in 11.99s. Missing zero/small-count messages, quarterly cautions despite a pooled count of six, and missing visible ranking warnings caused the failures.
- After implementation, same command: 10 passed in 6.79s. Includes counts 0/1/5/6, pooled versus quarterly counts, Streamlit AppTest visibility in both tabs, unchanged calculated tables and existing marker mode.
- Full suite in the sandbox: 1 failed, 103 passed, 35 errors in 87.87s. Setup errors included denied access to pytest's system temporary directory. Rerun with approved filesystem access: 2 failed, 137 passed in 86.95s. Failures: existing ACS export year-range assertion (test_acs_evidence.py:93), and pre-existing untracked selected-country normalization expectation (test_excluded_data_filtering.py:61, expected 0.0, actual 0.9). Neither test was edited; all-pass requirement remains unmet.
- Ran a direct real-data analysis using the application helpers to obtain the warning examples above. No browser or deployed-app inspection performed in this change.
- `git diff --check` returned no output.

## Limits

- The count threshold is a caution rule and does not establish statistical reliability.
- A long selection can create a long warning list; results remain visible as the user requested.
- This change targets the app ranking and cost trend. Export presentation is unchanged.

## Continued verification

- An isolated git archive HEAD copy, with the existing untracked filtering test copied in, reproduced expected normalized cost 0.0 versus actual 0.9. The ACS test in that diagnostic copy timed out at 60 seconds; that timeout does not establish the cause of the earlier text failure.
- Current ACS test under Python UTF-8 mode: 1 passed in 6.28s, without changing any test.
- Full suite: .venv/Scripts/python.exe -X utf8 -B -m pytest -q -p no:cacheprovider --tb=short --basetemp C:/Users/nr_pr/dso576/tmp/r2-utf8-suite-0926: 1 failed, 138 passed in 77.56s. Only test_excluded_data_filtering.py:61 fails, expected 0.0 versus actual 0.9.
- The existing app deliberately builds cost references from all countries before display filtering (src/dashboard_workflow.py:34). Asked the user how to handle the separate scoring/test disagreement while preserving their instruction to keep calculations and scores. No decision assumed, and no test expectation edited.

## Quarterly warning grouping refinement

- User reported that the repeated quarterly warnings were not user friendly and requested one caution sentence followed by complete, compact country groups in chronological order. Zero-cost groups must stay separate; thresholds, calculations, scores and markers stay unchanged.
- Updated presentation tests before production changes: 6 failed, 5 passed in 4.69s. After grouping implementation: 11 passed in 4.95s. Tests cover counts 0/1/5/6, pooled versus quarterly groups, complete chronological output of 40 affected quarters from reversed input, separate zero-count output, and the visible Streamlit presentation.
- Ran the helper on all Cuba quarters, USD 200: every one of the 29 affected quarters appears in a single country group, with counts; no zero-cost group for that selection. The app health endpoint returned ok. This is helper/AppTest verification, not a manual browser observation.
- Full UTF-8 regression suite: 1 failed, 139 passed in 75.43s. Only the documented normalization test at test_excluded_data_filtering.py:61 fails (expected 0.0, actual 0.9); all eleven revised R2 tests pass. Existing normalization test hash matches the unchanged baseline diagnostic copy. No scoring or test expectation changed for that failure.

## Personal app recheck reported by the user

- Earlier failed check: the exact error supplied in the user's screenshot was `ImportError: cannot import name 'QUARTERLY_COST_SAMPLE_CAUTION' from 'src.dashboard_presentation'`. The original check time remains unknown; A2 records this as a failed check. The user's correction supersedes the earlier statement that the error text was not supplied.
- After restarting, the user checked Cuba, all quarters, USD 200, in Survey quarters and saw one caution sentence followed by grouped quarters and quote counts. Assessment: “much better.” This is user-reported evidence, not an agent browser check.
- The app now displays successfully after restarting. No code change was made for the reported import error in this step, and the evidence does not establish that a code fix was needed.

## Checkout and deployment-source verification

Verified local checkout evidence:
- Repository root: C:/Users/nr_pr/dso576/project-dashboard.
- origin fetch/push URL: https://github.com/edijiang0431/project.git.
- Branch: feature/mvp-change-requests. HEAD: dafaffb349ad460a4a6021b9290d3e21ab4bfe10 (Add final product collaboration rules).
- .git points to C:/Users/nr_pr/dso576/project/.git/worktrees/project-dashboard; the common Git directory is C:/Users/nr_pr/dso576/project/.git. git worktree list confirms project on main at 6e8c3db715412037ede109440762b972eb35d55f and project-dashboard on feature/mvp-change-requests. git rev-parse --git-path info/exclude resolves to project/.git/info/exclude. This shared exclusion location is expected for linked worktrees.
- Upstream is origin/feature/mvp-change-requests. Local HEAD and the locally cached upstream ref differ by 0/0 commits; no fetch or remote-state verification was performed.
- R2 application edits: prof-build-M2/src/dashboard_presentation.py and prof-build-M2/streamlit_app.py. New R2 tests: prof-build-M2/tests/test_small_sample_cautions.py. R2 validation notes: hardening-notes.md. Paths are relative to project-dashboard. The ignored my-contribution-prae.md records the work and stays outside the proposed commit.
- Root README.md:7 names feature/mvp-change-requests and prof-build-M2/streamlit_app.py; README.md:9 links https://project-c2b8ykvnwmkqm8o59iqymy.streamlit.app/. README.md:45-52 documents Streamlit settings: repository edijiang0431/project, branch feature/mvp-change-requests, main file prof-build-M2/streamlit_app.py, Python 3.14, dependencies prof-build-M2/uv.lock and root requirements.txt. The lockfile, requirements file and entry file are tracked. No tracked .github workflow or .streamlit configuration was found by the targeted Git inventory. README evidence documents intended hosting settings; it does not verify current settings on the host.
- Other folders: project is the linked main checkout of the same Git repository. project-prof-build-M2 is a separate repository (https://github.com/USC-DSO-576-PS/project-prof-build-M2.git), main at f4c8f02ba15709992cb443258afff85b8661119f; its README describes a local notebook. project-mvp-M1 is a separate repository (https://github.com/USC-DSO-576-PS/project-mvp-M1.git), main at 718ea5f4e9dc9c8e79baa8be797530c0b0bc3359; its README links a different cvs-loss-prevention app. The nested project-dashboard/README.md is an Ana submission relocation note. These do not override the root deployment README.

Hosting verification limit and conditional conclusion:
- The web tool could not access the public app URL or the requested official Streamlit update documentation. No authenticated Streamlit hosting settings or deployment logs were inspected. Local evidence supports that R2 is in the checkout documented for the published MVP, but actual hosting wiring remains unverified.
- If the live app's settings match the root README and automatic deployment is active, pushing future R2 commits to origin/feature/mvp-change-requests would target the live app directly; no merge into main would be needed. A push now would not include the uncommitted R2 edits. If the host instead watches main or another branch/repository, a later merge or other explicitly authorized integration into that configured source would be required. No live update is guaranteed by this inspection.
- Check the app's Streamlit Community Cloud management/deployment details for repository owner/name edijiang0431/project, branch feature/mvp-change-requests, main file prof-build-M2/streamlit_app.py and the app URL project-c2b8ykvnwmkqm8o59iqymy.streamlit.app. Check deployment/build logs for the deployed commit SHA and successful latest deployment, and whether source updates are deploying automatically. Confirm Python 3.14 in advanced settings. Compare the deployed SHA with GitHub branch HEAD; local cached origin refs are not proof of current remote HEAD.

## R2 contribution branch decision

- Read AGENTS.md final-product rules; no different branch workflow is specified. User chose a separate contribution branch so the team can review and combine contributions before updating the live dashboard.
- Created fix/r2-small-sample-cautions at dafaffb349ad460a4a6021b9290d3e21ab4bfe10. SHA-256 checks confirmed all four R2 files and the ignored contribution log were unchanged by branch creation. A2 and these notes were then updated as authorized. Application/test content remains unchanged.
- Contribution log remains ignored and untracked; Part B unchanged; staging area empty. No commit, push, merge or deployment.
