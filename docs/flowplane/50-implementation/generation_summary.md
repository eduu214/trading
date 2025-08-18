# Batch Processing Summary

**Generation Date:** 2025-08-18T20:39:52.696Z
**Output Path:** /Users/andywillis/dev/workspace/jack-trading/docs/flowplane/50-implementation
**Model:** claude-sonnet-4-20250514
**Temperature:** 0.3
**Processing Mode:** Streaming API
**API Calls:** Real API calls
**Step:** Custom batch processing

## Processing Statistics

- **Total Items:** 18
- **Successful:** 18
- **Failed:** 0
- **Success Rate:** 100.0%
- **Processing Time:** 109.3 seconds
- **Processing Speed:** 9.9 items/minute
- **Token Throughput:** 486.131 tokens/second

## Token Usage

### Summary
- **Total Input Tokens:** 19,888
- **Total Output Tokens:** 33,251
- **Total Tokens:** 53,139

### Cache Performance
- **Cache Creation Tokens:** 356,135
- **Cache Read Tokens:** 28,441
- **Cache Hit Rate:** 100.0%
- **Tokens Saved:** 25,596.9 (90% discount on cached tokens)

### Averages Per Item
- **Average Input Tokens:** 1,104
- **Average Output Tokens:** 1,847

## Document Caching Breakdown

### Cache Optimization
Documents are automatically ordered from broadest to narrowest scope for optimal cache reuse:
1. **Project-wide** → Cached once, used by all items
2. **Feature-wide** → Cached per feature, shared by all stories
3. **Story-specific** → Not cached, unique per story

### Document Usage
| Document | Scope | Cacheable | Times Used | Cache Efficiency |
|----------|-------|-----------|------------|------------------|
| 30-1002-story-registry.yaml | Project | ✅ Yes | 18 | 94% reuse |
| 30-2001-design-system.yaml | Project | ✅ Yes | 18 | 94% reuse |
| 30-3001-infrastructure-registry.yaml | Project | ✅ Yes | 18 | 94% reuse |
| 40-1001-shared-components.yaml | Project | ✅ Yes | 18 | 94% reuse |
| 40-3001-F001-technical.md | Feature | ✅ Yes | 3 | 67% reuse |
| 40-3001-F002-technical.md | Feature | ✅ Yes | 3 | 67% reuse |
| 40-3001-F003-technical.md | Feature | ✅ Yes | 3 | 67% reuse |
| 40-3001-F004-technical.md | Feature | ✅ Yes | 3 | 67% reuse |
| 40-3001-F005-technical.md | Feature | ✅ Yes | 3 | 67% reuse |
| 40-3001-F006-technical.md | Feature | ✅ Yes | 3 | 67% reuse |
| 40-2001-F001-US003-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F001-US003-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F001-US004-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F001-US004-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F001-US005-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F001-US005-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F002-US001-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F002-US001-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F002-US002-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F002-US002-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F002-US003-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F002-US003-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F003-US001-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F003-US001-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F003-US002-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F003-US002-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F004-US001-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 40-2001-F003-US003-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F004-US001-plan.md | Story | ❌ No | 1 | N/A |
| 50-2001-F003-US003-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F004-US002-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F004-US002-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F004-US003-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F004-US003-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F005-US001-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F005-US001-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F005-US002-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F005-US002-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F005-US003-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 40-2001-F006-US001-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F005-US003-plan.md | Story | ❌ No | 1 | N/A |
| 50-2001-F006-US001-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F006-US002-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F006-US002-plan.md | Story | ❌ No | 1 | N/A |
| 40-2001-F006-US003-ux-spec.md | Story | ✅ Yes | 1 | First use |
| 50-2001-F006-US003-plan.md | Story | ❌ No | 1 | N/A |

### Cache Statistics
- **Documents Processed:** 46
- **Cacheable Documents:** 28 (61%)
- **Total Document Uses:** 126
- **Cached Document Uses:** 108 (86%)


## Cost Analysis

### Detailed Breakdown
- **Input Token Cost:** $0.0000
- **Output Token Cost:** $0.4988
- **Cache Write Cost:** $1.3355
- **Cache Read Cost:** $0.0085

### Total Cost
- **Total Cost:** $1.8428
- **Average Cost per Item:** $0.1024

### Cache Savings
- **Input Cost Without Caching:** $19.2313
- **Input Cost With Caching:** $1.3440
- **Cache Savings:** $17.8873 (93.0%)
- **Note:** Output costs ($0.4988) are the same regardless of caching

## Model Cost Comparison

Estimated costs for this same workload using different Claude models:

### Claude 3.5 Haiku (Latest)
- **Cost:** $0.4914
- **Comparison:** 0.3x current run cost
- **Per Item:** $0.0273

### Claude 4 Sonnet (Current Run)
- **Cost:** $1.8428
- **Comparison:** Baseline
- **Per Item:** $0.1024

### Claude 4 Opus
- **Cost:** $9.2140
- **Comparison:** 5.0x current run cost
- **Per Item:** $0.5119

## File Processing Details

### Input Files Used
- ./docs/flowplane/30-refinement/30-1002-story-registry.yaml
- ./docs/flowplane/30-refinement/30-2001-design-system.yaml
- ./docs/flowplane/30-refinement/30-3001-infrastructure-registry.yaml
- ./docs/flowplane/40-design/40-1001-shared-components.yaml
- ./docs/flowplane/40-design/40-2001-F001-US003-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F001-US004-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F001-US005-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F002-US001-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F002-US002-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F002-US003-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F003-US001-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F003-US002-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F003-US003-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F004-US001-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F004-US002-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F004-US003-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F005-US001-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F005-US002-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F005-US003-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F006-US001-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F006-US002-ux-spec.md
- ./docs/flowplane/40-design/40-2001-F006-US003-ux-spec.md
- ./docs/flowplane/40-design/40-3001-F001-technical.md
- ./docs/flowplane/40-design/40-3001-F002-technical.md
- ./docs/flowplane/40-design/40-3001-F003-technical.md
- ./docs/flowplane/40-design/40-3001-F004-technical.md
- ./docs/flowplane/40-design/40-3001-F005-technical.md
- ./docs/flowplane/40-design/40-3001-F006-technical.md
- ./docs/flowplane/50-implementation/50-2001-F001-US003-plan.md
- ./docs/flowplane/50-implementation/50-2001-F001-US004-plan.md
- ./docs/flowplane/50-implementation/50-2001-F001-US005-plan.md
- ./docs/flowplane/50-implementation/50-2001-F002-US001-plan.md
- ./docs/flowplane/50-implementation/50-2001-F002-US002-plan.md
- ./docs/flowplane/50-implementation/50-2001-F002-US003-plan.md
- ./docs/flowplane/50-implementation/50-2001-F003-US001-plan.md
- ./docs/flowplane/50-implementation/50-2001-F003-US002-plan.md
- ./docs/flowplane/50-implementation/50-2001-F003-US003-plan.md
- ./docs/flowplane/50-implementation/50-2001-F004-US001-plan.md
- ./docs/flowplane/50-implementation/50-2001-F004-US002-plan.md
- ./docs/flowplane/50-implementation/50-2001-F004-US003-plan.md
- ./docs/flowplane/50-implementation/50-2001-F005-US001-plan.md
- ./docs/flowplane/50-implementation/50-2001-F005-US002-plan.md
- ./docs/flowplane/50-implementation/50-2001-F005-US003-plan.md
- ./docs/flowplane/50-implementation/50-2001-F006-US001-plan.md
- ./docs/flowplane/50-implementation/50-2001-F006-US002-plan.md
- ./docs/flowplane/50-implementation/50-2001-F006-US003-plan.md

### Output Files Created
- 50-3001-F001-US003-file-01.md
- 50-3001-F001-US003-file-02.md
- 50-3001-F001-US004-file-01.md
- 50-3001-F001-US004-file-02.md
- 50-3001-F001-US005-file-01.md
- 50-3001-F001-US005-file-02.md
- 50-3001-F002-US001-file-01.md
- 50-3001-F002-US001-file-02.md
- 50-3001-F002-US001-file-03.md
- 50-3001-F002-US002-file-01.md
- 50-3001-F002-US002-file-02.md
- 50-3001-F002-US003-file-01.md
- 50-3001-F002-US003-file-02.md
- 50-3001-F003-US001-file-01.md
- 50-3001-F003-US001-file-02.md
- 50-3001-F003-US001-file-03.md
- 50-3001-F003-US002-file-01.md
- 50-3001-F003-US002-file-02.md
- 50-3001-F003-US003-file-01.md
- 50-3001-F003-US003-file-02.md
- 50-3001-F003-US003-file-03.md
- 50-3001-F004-US001-file-01.md
- 50-3001-F004-US001-file-02.md
- 50-3001-F004-US002-file-01.md
- 50-3001-F004-US002-file-02.md
- 50-3001-F004-US002-file-03.md
- 50-3001-F004-US003-file-01.md
- 50-3001-F004-US003-file-02.md
- 50-3001-F005-US001-file-01.md
- 50-3001-F005-US001-file-02.md
- 50-3001-F005-US002-file-01.md
- 50-3001-F005-US002-file-02.md
- 50-3001-F005-US003-file-01.md
- 50-3001-F005-US003-file-02.md
- 50-3001-F005-US003-file-03.md
- 50-3001-F006-US001-file-01.md
- 50-3001-F006-US001-file-02.md
- 50-3001-F006-US002-file-01.md
- 50-3001-F006-US002-file-02.md
- 50-3001-F006-US003-file-01.md
- 50-3001-F006-US003-file-02.md

### Expected vs Actual Output
No expected output files defined (not running a FlowPlane step).

## Processing Results

Successfully processed 18 items


Each result contains the generated content based on your prompts and input items.
