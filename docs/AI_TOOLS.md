# AI Tools Usage Documentation

**Purpose**: Document AI coding assistant usage, prompt patterns, and lessons learned during SpendSense development  
**Last Updated**: November 10, 2025  
**Analysis Based On**: 270 user prompts across 9 chat log sessions

---

## Overview

This project leveraged Cursor (with Claude Sonnet 3.5) as the primary AI coding assistant throughout development. This document analyzes actual prompt patterns, communication styles, and effectiveness based on real usage data extracted from chat logs.

**Key Statistics**:

- **Total Prompts**: 270 across 9 sessions
- **Primary Tool**: Cursor with Claude Sonnet 3.5
- **Development Phases**: Planning → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Final Polish

---

## Prompt Distribution by Phase

### Phase Breakdown

- **Final Work (Phase 5+)**: 125 prompts (46%) - Polish, refinement, deployment troubleshooting
- **Phase 5**: 31 prompts (11%) - Fraud detection, UI improvements
- **Phase 1 Part 2**: 29 prompts (11%) - Setup, Docker, testing
- **Phase 3**: 24 prompts (9%) - Evaluation metrics, dashboard
- **Phase 4**: 21 prompts (8%) - End-user interface, decision traces
- **Phase 2**: 14 prompts (5%) - Recommendation engine
- **Phase 1 Part 1**: 14 prompts (5%) - Initial setup, architecture
- **Planning**: 9 prompts (3%) - PRD review, architecture planning
- **Phase 4 Planning**: 3 prompts (1%) - Gap analysis

**Observation**: Later phases required more prompts due to iterative refinement, troubleshooting, and polish work.

---

## Prompt Themes & Patterns

### 1. Troubleshooting & Debugging (30-40% of prompts)

**Pattern**: Iterative problem-solving with verification steps

**Example Prompts**:

```
"lots of this log `Error: Invalid value for '--server.port' (env var: 'STREAMLIT_SERVER_PORT'): '$PORT' is not a valid integer.`"
```

```
"`Error: Invalid value for '--server.port' (env var: 'STREAMLIT_SERVER_PORT'): '$PORT' is not a valid integer.` Your last two fixes did not work, so do not rush to attempt another fix; think deeply about what might be going on and talk to me."
```

```
"1 no logs (searched "Starting Streamlit on port") 2 no PORT 3 Railway does not add that env var (so no idea why it's in the logs)"
```

**Lessons**:

- When fixes fail, explicitly request deeper analysis before attempting another fix
- Provide specific error messages and context
- Request verification steps before committing

---

### 2. Documentation Requests (15-20% of prompts)

**Pattern**: Requests for documentation updates, guides, and explanations

**Example Prompts**:

```
"document the progress we've made in the docs-SpendSense/ folder but be concise. all we need is enough detail for the next session to learn that we need to (a) run the test commands you just gave, and (b) how and where to pick up on phase 1.3"
```

```
"update operator_dashboard_guide and quick_smoke_test"
```

```
"clean up the README to be comprehensive yet concise, including (ideally) one-command setup for local"
```

```
"you need to stop creating docs before asking me first. usually I just want you to tell me in the chat"
```

**Lessons**:

- Prefer chat explanations over document creation unless explicitly requested
- Documentation should be concise and action-oriented
- Update existing docs rather than creating new ones when possible

---

### 3. Testing & Validation (15-20% of prompts)

**Pattern**: Requests for test creation, manual testing instructions, and verification

**Example Prompts**:

```
"just to confirm, but have you completed your testing of the work so far?"
```

```
"Can you analyze why we have testing issues?"
```

```
"yes! and then also retry the testing earlier that failed due to compatibility issues — I want to be 100% sure what we have so far is rock-solid and identify any issues now rather than later"
```

```
"remind me how to smoke test it"
```

```
"how many unit tests are in this repo?"
```

**Lessons**:

- Explicitly request test verification before moving forward
- Request both automated and manual testing instructions
- Ask for test counts/coverage to track progress

---

### 4. UI/UX Improvements (10-15% of prompts)

**Pattern**: Iterative refinement of user interface elements

**Example Prompts**:

```
"make these buttons bigger"
```

```
"the new buttons are better but red is too aggresive"
```

```
"in the User View, hitting Enter in the "Enter Your User ID" text box should load that user. Also, for now make a list of all the test user IDs available in the UI on that page."
```

```
"can the Loading Recommendations be removed after page load?"
```

```
"also the dropdown actually shouldn't open while the recommendations view is loading"
```

**Lessons**:

- UI improvements require multiple iterations
- Be specific about what's wrong and what's desired
- Request verification before committing UI changes

---

### 5. Feature Implementation (10-15% of prompts)

**Pattern**: Clear feature requests with context

**Example Prompts**:

```
"Auditability is a requirement: how feasible is to get the actual "decision traces" displayed / logged (and viewable in the operator dashboard somewhere) for how a user got a recommendation?"
```

```
"add some fake demographic data that can be used to show off fairness functionality"
```

```
"the User View needs to show a 'revoke consent' button that for now just flips the consent bit"
```

```
"are recommendations pre-computed? how feasible is to ALSO be able to get fresh recommendations? (if feasible let's add a prominent button saying 'Get New Recommendations' to the user view)"
```

**Lessons**:

- Ask about feasibility before requesting implementation
- Provide context about requirements and constraints
- Request both implementation and testing steps

---

### 6. Deployment & Infrastructure (5-10% of prompts)

**Pattern**: Setup and configuration troubleshooting

**Example Prompts**:

```
"I have a Railway account, free tier, connected to my GitHub. tell me in-app, succinctly, how to deploy and smoke-test"
```

```
"for Deploy step 4 are you saying I can run those commands from a shell/terminal within the Deployment > Logs section of the Railway web console?"
```

```
"`zsh: command not found: railway` i want to install it"
```

```
"what's the pip install command? pretty sure Railway app doesn't have any deps yet. in railway shell I ran those python commands and got tons of missing dependencies errors"
```

**Lessons**:

- Provide platform-specific context (Railway, Docker, etc.)
- Request succinct, actionable instructions
- Ask for verification steps after setup

---

## Communication Patterns

### 1. Verification-First Approach

**Pattern**: Frequent requests to verify before committing

**Example Prompts**:

```
"don't commit until I verify the fix"
```

```
"now we're in troubleshooting mode, so don't commit until I verify the fixes"
```

```
"ok commit"
```

**Observation**: User maintained tight control over commits, preferring to verify changes first.

---

### 2. Speed Emphasis

**Pattern**: Requests for rapid implementation when appropriate

**Example Prompts**:

```
"implement at lightning speed and commit!"
```

```
"yes implement asap then tell me how to do quick manual smoke testing"
```

```
"add all tests at lightning speed then, after they pass, commit"
```

**Observation**: Speed was prioritized for straightforward tasks, but verification was still required.

---

### 3. Iterative Refinement

**Pattern**: Multiple follow-ups on the same issue

**Example Prompts** (PORT error sequence):

```
"lots of this log `Error: Invalid value for '--server.port'..."
```

```
"`Error: Invalid value for '--server.port'...` Your last two fixes did not work..."
```

```
"1 no logs (searched "Starting Streamlit on port") 2 no PORT 3 Railway does not add that env var..."
```

```
"no matches at all for "Railway initialization" and still port errors"
```

```
"stop telling me there will be no more PORT errors, be less confident"
```

**Observation**: Persistent issues required multiple iterations and explicit requests to be less confident about fixes.

---

### 4. Context Switching

**Pattern**: Requests to read memory/session notes before starting

**Example Prompts**:

```
"in docs, read memory, session-pickup-notes, quick_smoke_test and pick up by populating recommendations for everyone"
```

```
"read memory and start!"
```

```
"read SpendSense-Session-Progress and advise my steps to test phases 1.1-1.2 so we can move on"
```

**Observation**: User relied on documentation to maintain context across sessions.

---

## Effective Prompt Patterns

### ✅ What Worked Well

1. **Specific Error Messages**

   ```
   "```python scripts/validate_implementation.py
   ❌ test_project_structure failed: Missing file: README.md
   ```"
   ```

   Providing exact error output helps AI diagnose issues accurately.

2. **Explicit Constraints**

   ```
   "I actually don't want to bother hashing a password for the remainder of development + demo"
   ```

   Stating constraints upfront prevents unnecessary work.

3. **Action-Oriented Requests**

   ```
   "update the testing-manual to add manual test steps for phase 4 and include a 'quick smoke test' section"
   ```

   Clear action verbs and specific deliverables lead to better results.

4. **Verification Requests**

   ```
   "did we already add unit tests for phase 4?"
   ```

   Checking status before proceeding prevents duplicate work.

5. **Feasibility Questions**

   ```
   "are recommendations pre-computed? how feasible is to ALSO be able to get fresh recommendations?"
   ```

   Asking about feasibility before implementation saves time.

---

### ⚠️ Challenges Encountered

1. **Deployment Troubleshooting**
   - Railway deployment issues required many iterations
   - PORT environment variable confusion
   - Container lifecycle issues

2. **UI State Management**
   - Loading indicators not appearing/disappearing correctly
   - Button states and interactions
   - Navigation blocking during loads

3. **Data Persistence**
   - Confusion about database state
   - Missing data after deployment
   - Silent script failures

4. **Documentation Over-Creation**
   - AI created docs without being asked
   - User preferred chat explanations

---

## Lessons Learned

### For Future AI-Assisted Development

1. **Verification Loops**: Always request verification before committing, especially for fixes
2. **Error Context**: Provide full error messages and context, not just descriptions
3. **Iterative Approach**: Expect multiple iterations for complex issues
4. **Documentation Preference**: Prefer chat explanations unless documentation is explicitly needed
5. **Speed vs. Quality**: Request speed for straightforward tasks, but maintain quality gates
6. **Feasibility First**: Ask about feasibility before requesting complex implementations
7. **Less Confidence**: When fixes fail, explicitly request deeper analysis and less confidence

### Prompt Best Practices

1. **Be Specific**: Include exact error messages, file paths, and context
2. **State Constraints**: Mention time constraints, preferences, and limitations upfront
3. **Request Verification**: Ask for verification steps and test instructions
4. **Iterate Explicitly**: When something doesn't work, explicitly request re-analysis
5. **Check Status**: Ask about current state before requesting new work
6. **Prefer Chat**: Request chat explanations over document creation unless needed

---

## Impact Assessment

### Development Efficiency

- **Prompt Volume**: 270 prompts across 9 sessions shows iterative, collaborative development
- **Phase Distribution**: Later phases (polish, refinement) required more prompts than initial implementation
- **Troubleshooting**: ~30-40% of prompts were troubleshooting, indicating complex integration challenges

### Communication Effectiveness

- **Verification-First**: Tight control over commits prevented regressions
- **Iterative Refinement**: Multiple follow-ups on issues led to eventual resolution
- **Context Management**: Documentation and memory reading helped maintain continuity

### Areas of High AI Value

1. **Boilerplate Generation**: Project structure, API endpoints, test frameworks
2. **Documentation**: Implementation guides, testing manuals, architecture docs
3. **Debugging Assistance**: Error analysis, troubleshooting guidance
4. **Code Refactoring**: Structural improvements, test additions

### Areas Requiring Human Judgment

1. **Architecture Decisions**: Database choices, deployment strategies
2. **Business Logic**: Persona classification rules, recommendation scoring
3. **UX/UI Design**: Button placement, loading states, user flows
4. **Deployment Configuration**: Environment variables, port handling, container setup

---

## Conclusion

The development process showed a collaborative pattern where AI handled implementation details while the user maintained strategic control through:

- Explicit verification requests
- Iterative refinement cycles
- Context management via documentation
- Quality gates before commits

**Key Takeaway**: Effective AI-assisted development requires clear communication, explicit verification steps, and maintaining human oversight for critical decisions and quality control.

---

## Example Prompt Sequences

### Successful Sequence: Feature Implementation

```
Prompt 1: "Auditability is a requirement: how feasible is to get the actual "decision traces" displayed / logged (and viewable in the operator dashboard somewhere) for how a user got a recommendation?"

[AI responds with feasibility analysis]

Prompt 2: "wait where am I supposed to see the decision trace in the UI?"

[AI explains location]

Prompt 3: "I don't see it!"

[AI fixes and verifies]

Prompt 4: "great! take out the debug log that's visible in the UI on that page and commit"
```

**Pattern**: Feasibility → Implementation → Verification → Polish → Commit

### Challenging Sequence: Deployment Troubleshooting

```
Prompt 1: "lots of this log `Error: Invalid value for '--server.port'...`"

[AI attempts fix]

Prompt 2: "`Error: Invalid value for '--server.port'...` Your last two fixes did not work, so do not rush to attempt another fix; think deeply about what might be going on and talk to me."

[AI analyzes more deeply]

Prompt 3: "1 no logs (searched "Starting Streamlit on port") 2 no PORT 3 Railway does not add that env var..."

[Multiple iterations continue...]

Prompt 4: "stop telling me there will be no more PORT errors, be less confident"
```

**Pattern**: Error → Fix Attempt → Failure → Deeper Analysis → Multiple Iterations → Explicit Request for Less Confidence

This sequence demonstrates the importance of:

- Explicitly requesting deeper analysis when fixes fail
- Providing multiple data points (logs, env vars, behavior)
- Requesting less confidence when AI is overconfident
