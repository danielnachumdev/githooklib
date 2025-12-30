---
alwaysApply: true
---

# Issue Implementation Guide for AI Coding Assistants

This guide provides a comprehensive, step-by-step approach for implementing new features or fixing issues from start to finish. Follow this workflow to ensure thorough, well-tested implementations.

## Table of Contents

1. [Issue Analysis Phase](#issue-analysis-phase)
2. [Clarification Phase](#clarification-phase)
3. [Planning Phase](#planning-phase)
4. [Implementation Phase](#implementation-phase)
5. [Testing Phase](#testing-phase)
6. [Validation Phase](#validation-phase)
7. [Final Verification](#final-verification)

---

## Issue Analysis Phase

### Step 1: Understand the Issue

**DO:**
- Read the issue description carefully
- Identify the problem statement and expected behavior
- Note any constraints or requirements mentioned
- Check if the issue references specific files or components

**DON'T:**
- Don't start coding immediately
- Don't assume requirements without clarification
- Don't skip reading related code

### Step 2: Explore the Codebase

**DO:**
- Use semantic search to understand how the feature/component works
- Read relevant files mentioned in the issue
- Look for similar implementations as reference
- Check existing tests to understand expected behavior
- Use `grep` to find related code patterns

**DON'T:**
- Don't make changes yet
- Don't skip understanding the existing architecture
- Don't ignore related files that might be affected

### Step 3: Identify Affected Components

**DO:**
- List all files that will need modification
- Identify test files that need updates
- Note any dependencies or related components
- Check for breaking changes or backward compatibility concerns

**DON'T:**
- Don't modify files before planning
- Don't ignore potential side effects

---

## Clarification Phase

### Step 4: Ask Clarifying Questions

**DO:**
- Ask specific, focused questions (1-2 at a time)
- Provide multiple choice options when appropriate
- Ask about edge cases and error handling
- Clarify ambiguous requirements
- Ask about implementation preferences if multiple valid approaches exist

**DON'T:**
- Don't ask vague questions
- Don't ask too many questions at once (max 2 critical questions)
- Don't proceed with assumptions if requirements are unclear
- Don't skip asking when the issue description is ambiguous

**Question Format:**
- Use numbered lists
- Provide lettered options (a, b, c) for multiple choice
- First option should be the default assumption if user doesn't answer
- Keep questions under 200 characters each

### Step 5: Wait for User Confirmation

**DO:**
- Wait for user responses before proceeding
- Use the answers to refine your understanding
- Update your mental model based on clarifications

**DON'T:**
- Don't proceed with implementation until requirements are clear
- Don't ignore user feedback

---

## Planning Phase

### Step 6: Create a Detailed Plan

**DO:**
- Create a comprehensive plan using the planning tool
- Break down the implementation into clear, actionable steps
- Cite specific file paths and code locations
- Include test strategy in the plan
- Reference existing code patterns when relevant
- Keep plans proportional to complexity (don't over-engineer simple tasks)

**DON'T:**
- Don't start implementing without a plan
- Don't create vague or high-level plans
- Don't skip test planning
- Don't make the plan too complex for simple tasks

**Plan Should Include:**
- Overview of the changes
- Specific files to modify
- Implementation approach
- Test strategy
- Any architectural considerations

### Step 7: Get Plan Confirmation

**DO:**
- Present the plan to the user
- Wait for explicit confirmation before proceeding
- Be ready to adjust the plan based on feedback

**DON'T:**
- Don't start implementation until plan is confirmed
- Don't modify the plan file directly (unless explicitly asked)

---

## Implementation Phase

### Step 8: Create TODO List

**DO:**
- Create a TODO list based on the confirmed plan
- Mark the first task as `in_progress`
- Update TODO status as you complete tasks
- Only create TODOs for implementation tasks (not for searching, reading, etc.)

**DON'T:**
- Don't create TODOs for trivial operations
- Don't create duplicate TODOs if they already exist from the plan
- Don't forget to mark tasks as completed

### Step 9: Implement Changes

**DO:**
- Work on one task at a time
- Follow clean code principles (from workspace rules)
- Make small, focused changes
- Preserve existing code style and patterns
- Add necessary imports
- Handle edge cases and error conditions

**DON'T:**
- Don't make multiple unrelated changes in one go
- Don't ignore existing code patterns
- Don't add unnecessary comments (code should be self-documenting)
- Don't break existing functionality
- Don't skip error handling

### Step 10: Check for Linting Errors

**DO:**
- Run linter checks after making changes
- Fix any linting errors immediately
- Ensure type safety (mypy compliance)

**DON'T:**
- Don't ignore linting errors
- Don't use `# type: ignore` unless absolutely necessary
- Don't commit code with linting errors

---

## Testing Phase

### Step 11: Write/Update Tests

**DO:**
- Write tests for new functionality
- Update existing tests if behavior changes
- Follow the project's test structure and patterns
- Use `BaseTestCase` when appropriate
- Test edge cases and error conditions
- Ensure tests are isolated and independent
- Use descriptive test names

**DON'T:**
- Don't skip writing tests
- Don't write tests that depend on each other
- Don't ignore existing test patterns
- Don't test implementation details (test behavior instead)

**Test Quality Checklist:**
- Tests verify the exact behavior implemented
- Tests follow codebase patterns (mocking, assertions, etc.)
- Tests are isolated and don't depend on shared state
- Tests validate correct implementation
- Tests are maintainable and clear

### Step 12: Run Tests

**DO:**
- Run the specific test file you modified
- Run all tests in the affected test suite
- Verify all tests pass
- Fix any failing tests

**DON'T:**
- Don't proceed if tests fail
- Don't skip running the full test suite for affected files
- Don't ignore test failures

---

## Validation Phase

### Step 13: Baseline Testing Workflow

This critical step validates that your changes work correctly and don't break existing functionality.

**DO:**
1. **Stash Current Changes**
   ```bash
   git stash push -m "Description of changes"
   ```

2. **Run Baseline Tests**
   - Run tests for all files you modified
   - This establishes what the behavior was before your changes
   - Document any existing failures (if any)

3. **Pop Stashed Changes**
   ```bash
   git stash pop
   ```

4. **Run Tests Again**
   - Run the same tests with your changes applied
   - Verify your new tests pass
   - Verify all existing tests still pass (no regressions)

**DON'T:**
- Don't skip the baseline testing workflow
- Don't proceed if baseline tests show unexpected failures
- Don't ignore regressions in existing tests

**Why This Matters:**
- Establishes a baseline for comparison
- Confirms your changes work as intended
- Ensures no existing functionality was broken
- Validates that new tests actually test new behavior

### Step 14: Verify Test Coverage

**DO:**
- Ensure your new functionality is covered by tests
- Verify edge cases are tested
- Check that error conditions are handled

**DON'T:**
- Don't proceed with incomplete test coverage
- Don't ignore untested edge cases

---

## Final Verification

### Step 15: Final Code Review

**DO:**
- Review your implementation for:
  - Code quality and cleanliness
  - Proper error handling
  - Type safety
  - Adherence to project patterns
  - No unnecessary complexity
- Verify all TODOs are completed
- Check that the implementation matches the plan

**DON'T:**
- Don't skip the final review
- Don't leave incomplete implementations
- Don't ignore code quality issues

### Step 16: Documentation (if needed)

**DO:**
- Update documentation if the change affects user-facing behavior
- Add inline documentation only if code isn't self-explanatory
- Update README if installation or usage changes

**DON'T:**
- Don't add comments that restate what the code does
- Don't update documentation unless explicitly needed
- Don't create documentation files unless requested

### Step 17: Summary

**DO:**
- Provide a clear summary of:
  - What was implemented
  - Files modified
  - Tests added/updated
  - Key changes made
  - Validation results

**DON'T:**
- Don't skip the summary
- Don't be vague about what was done

---

## Common Pitfalls to Avoid

### Implementation Pitfalls

**DON'T:**
- Don't modify multiple unrelated things at once
- Don't ignore existing code patterns
- Don't break backward compatibility without justification
- Don't add features not requested in the issue
- Don't skip error handling
- Don't use magic numbers or strings (use constants)
- Don't create unnecessary abstractions

### Testing Pitfalls

**DON'T:**
- Don't write tests that are too coupled to implementation
- Don't skip testing edge cases
- Don't write tests that depend on execution order
- Don't ignore test failures
- Don't skip the baseline testing workflow

### Communication Pitfalls

**DON'T:**
- Don't proceed with unclear requirements
- Don't skip asking clarifying questions
- Don't ignore user feedback
- Don't make assumptions about user intent

---

## Workflow Summary

```
1. Read and understand the issue
   ↓
2. Explore codebase and find relevant code
   ↓
3. Ask clarifying questions (if needed)
   ↓
4. Create detailed plan
   ↓
5. Get plan confirmation
   ↓
6. Create TODO list
   ↓
7. Implement changes (one task at a time)
   ↓
8. Check linting errors
   ↓
9. Write/update tests
   ↓
10. Run tests and fix failures
    ↓
11. Stash changes → Run baseline tests → Pop changes → Run tests again
    ↓
12. Final code review
    ↓
13. Provide summary
```

---

## Key Principles

1. **Understand Before Implementing**: Always explore and understand the codebase first
2. **Plan Before Coding**: Create a detailed plan and get confirmation
3. **Test Thoroughly**: Write comprehensive tests and validate with baseline testing
4. **No Regressions**: Ensure existing functionality continues to work
5. **Clean Code**: Follow project patterns and clean code principles
6. **Iterative Approach**: Work in small, focused steps
7. **Validation**: Always validate changes with baseline testing workflow

---

## Example: Complete Workflow

### Issue: "When skipping a hook, print a log about it"

1. **Analysis**: Found skip logic in `githooklib/git_hook.py`, currently only logs at DEBUG level
2. **Clarification**: Asked about log levels and message content
3. **Planning**: Created plan for multi-level logging (INFO, DEBUG, TRACE)
4. **Implementation**: 
   - Modified `run()` method to gather patterns and files
   - Added INFO, DEBUG, and TRACE logging
5. **Testing**: 
   - Updated existing test to verify all three log levels
   - Used `assert_any_call` for methods called multiple times
6. **Validation**: 
   - Stashed → Baseline tests passed (17/17)
   - Popped → Tests with changes passed (17/17, including new logging verification)
7. **Result**: Feature implemented, tested, and validated with no regressions

---

## Notes for AI Assistants

- This guide should be followed systematically
- Each phase should be completed before moving to the next
- Don't skip steps even if they seem obvious
- When in doubt, ask for clarification
- Always validate with baseline testing workflow
- Quality over speed - thorough implementation is better than quick fixes

