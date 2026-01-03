# TODO (Prioritized)

## P0: High Risk / Correctness
- [ ] Normalize unified stereo route path to avoid double prefix and mixed hyphen/underscore; confirm desired URL in `src/api/endpoints/v1/process_unified_stereo.py` and `src/api/endpoints/v1/routers.py`.
- [ ] Convert error returns to proper HTTP exceptions in:
  - `src/api/endpoints/v1/process_json_transcript.py`
  - `src/api/endpoints/v1/process_qa_auditor.py`
- [ ] Avoid repeated ASR model instantiation across API lifespan and actions; centralize or inject `ASRModelManager`.

## P1: Reliability / Resource Use
- [ ] Fix memory warning thresholds (check >0.9 before >0.8) in action classes:
  - `src/execution/actions/process_wav_file_action.py`
  - `src/execution/actions/process_wav2file_action.py`
  - `src/execution/actions/process_file2choose_model_action.py`
- [ ] Replace debug `print` statements with logger calls and ensure PII-safe logging in `src/utils/transcript/prase_transcript.py`.
- [ ] Verify QA auditor uses tool-enabled agents if required; consider `get_agent_with_tools()` in `src/agents/agent_manager/agent_manager.py`.

## P2: Feature Completeness
- [ ] Implement real model selection logic in `src/execution/actions/process_unified_stereo_action.py`.
- [ ] Implement `auto_continue` to call transcript processing (currently returns `pending`) in `src/execution/actions/process_unified_stereo_action.py`.

## P3: Consistency / Cleanup
- [ ] Resolve duplicated `ModelSelectionResponse` class definition in `src/api/endpoints/v1/process_file2choose_model.py`.
- [ ] Align `build_workflow()` implementation with documented flow (context improver/self-checker) in `src/agents/workflows/build.py` or update docstring to match reality.
- [ ] Fix mismatch between comment and actual chunk size (comment says 100s but code uses 60s) in `src/execution/usecases/process_transcript_usecase.py`.
