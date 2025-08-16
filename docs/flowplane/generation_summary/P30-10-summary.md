# Batch Processing Summary

**Generation Date:** 2025-08-15T04:50:41.741Z
**Batch ID:** /Users/andywillis/dev/workspace/trading/docs/flowplane/30-refinement
**Model:** claude-sonnet-4-20250514
**Temperature:** 0.3
**Processing Mode:** Streaming API
**Dry Run:** No (real API calls)
**Step:** Refine Scope with Infrastructure

## Processing Statistics

- **Total Items:** 1
- **Successful:** 1
- **Failed:** 0
- **Success Rate:** 100.0%
- **Processing Time:** 82.8 seconds
- **Processing Speed:** 0.7 items/minute
- **Token Throughput:** 57.995 tokens/second

## Token Usage

### Summary
- **Total Input Tokens:** 18
- **Total Output Tokens:** 4,784
- **Total Tokens:** 4,802

### Cache Performance
- **Cache Creation Tokens:** 11,247
- **Cache Read Tokens:** 0
- **Cache Hit Rate:** 100.0%
- **Tokens Saved:** 0 (90% discount on cached tokens)

### Averages Per Item
- **Average Input Tokens:** 18
- **Average Output Tokens:** 4,784

## Document Caching Breakdown

### Cache Optimization
Documents are automatically ordered from broadest to narrowest scope for optimal cache reuse:
1. **Project-wide** → Cached once, used by all items
2. **Feature-wide** → Cached per feature, shared by all stories
3. **Story-specific** → Not cached, unique per story

### Document Usage
| Document | Scope | Cacheable | Times Used | Cache Efficiency |
|----------|-------|-----------|------------|------------------|
| 20-1001-scope.md | Project | ✅ Yes | 1 | First use |
| 20-2001-architecture.md | Project | ✅ Yes | 1 | First use |
| 00-100-ux-guidelines.md | Project | ✅ Yes | 1 | First use |

### Cache Statistics
- **Documents Processed:** 3
- **Cacheable Documents:** 3 (100%)
- **Total Document Uses:** 3
- **Cached Document Uses:** 3 (100%)


## Cost Analysis

### Detailed Breakdown
- **Input Token Cost:** $0.0000
- **Output Token Cost:** $0.0718
- **Cache Write Cost:** $0.0422
- **Cache Read Cost:** $0.0000

### Total Cost
- **Total Cost:** $0.1139
- **Average Cost per Item:** $0.1139

### Cache Savings
- **Input Cost Without Caching:** $0.0337
- **Input Cost With Caching:** $0.0422
- **Cache Savings:** $-0.0084 (-25.0%)
- **Note:** Output costs ($0.0718) are the same regardless of caching

## Model Cost Comparison

Estimated costs for this same workload using different Claude models:

### Claude 3.5 Haiku (Latest)
- **Cost:** $0.0304
- **Comparison:** 0.3x current run cost
- **Per Item:** $0.0304

### Claude 4 Sonnet (Current Run)
- **Cost:** $0.1139
- **Comparison:** Baseline
- **Per Item:** $0.1139

### Claude 4 Opus
- **Cost:** $0.5697
- **Comparison:** 5.0x current run cost
- **Per Item:** $0.5697

## File Processing Details

### Input Files Used
- ./docs/flowplane/00-misc/00-100-ux-guidelines.md
- ./docs/flowplane/20-scope/20-1001-scope.md
- ./docs/flowplane/20-scope/20-2001-architecture.md

### Output Files Created
- 30-1001-feature-registry.yaml
- 30-1002-story-registry.yaml
- 30-1003-scope-overview.md
- 30-1004-infrastructure-requirements.md

### Expected vs Actual Output
**Files created as expected (4):**
- ✓ 30-1001-feature-registry.yaml
- ✓ 30-1002-story-registry.yaml
- ✓ 30-1003-scope-overview.md
- ✓ 30-1004-infrastructure-requirements.md

✅ All files were created exactly as expected.

## Processing Results

Successfully processed 1 items


Each result contains the generated content based on your prompts and input items.
