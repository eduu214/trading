# Batch Processing Summary

**Generation Date:** 2025-08-15T04:56:34.217Z
**Batch ID:** /Users/andywillis/dev/workspace/trading/docs/alphastrat/30-refinement
**Model:** claude-sonnet-4-20250514
**Temperature:** 0.3
**Processing Mode:** Streaming API
**Dry Run:** No (real API calls)
**Step:** Create Design System

## Processing Statistics

- **Total Items:** 1
- **Successful:** 1
- **Failed:** 0
- **Success Rate:** 100.0%
- **Processing Time:** 57.1 seconds
- **Processing Speed:** 1.1 items/minute
- **Token Throughput:** 68.574 tokens/second

## Token Usage

### Summary
- **Total Input Tokens:** 14
- **Total Output Tokens:** 3,900
- **Total Tokens:** 3,914

### Cache Performance
- **Cache Creation Tokens:** 8,555
- **Cache Read Tokens:** 0
- **Cache Hit Rate:** 100.0%
- **Tokens Saved:** 0 (90% discount on cached tokens)

### Averages Per Item
- **Average Input Tokens:** 14
- **Average Output Tokens:** 3,900

## Document Caching Breakdown

### Cache Optimization
Documents are automatically ordered from broadest to narrowest scope for optimal cache reuse:
1. **Project-wide** → Cached once, used by all items
2. **Feature-wide** → Cached per feature, shared by all stories
3. **Story-specific** → Not cached, unique per story

### Document Usage
| Document | Scope | Cacheable | Times Used | Cache Efficiency |
|----------|-------|-----------|------------|------------------|
| 20-2001-architecture.md | Project | ✅ Yes | 1 | First use |
| 30-1003-scope-overview.md | Project | ✅ Yes | 1 | First use |

### Cache Statistics
- **Documents Processed:** 2
- **Cacheable Documents:** 2 (100%)
- **Total Document Uses:** 2
- **Cached Document Uses:** 2 (100%)


## Cost Analysis

### Detailed Breakdown
- **Input Token Cost:** $0.0000
- **Output Token Cost:** $0.0585
- **Cache Write Cost:** $0.0321
- **Cache Read Cost:** $0.0000

### Total Cost
- **Total Cost:** $0.0906
- **Average Cost per Item:** $0.0906

### Cache Savings
- **Input Cost Without Caching:** $0.0257
- **Input Cost With Caching:** $0.0321
- **Cache Savings:** $-0.0064 (-25.0%)
- **Note:** Output costs ($0.0585) are the same regardless of caching

## Model Cost Comparison

Estimated costs for this same workload using different Claude models:

### Claude 3.5 Haiku (Latest)
- **Cost:** $0.0242
- **Comparison:** 0.3x current run cost
- **Per Item:** $0.0242

### Claude 4 Sonnet (Current Run)
- **Cost:** $0.0906
- **Comparison:** Baseline
- **Per Item:** $0.0906

### Claude 4 Opus
- **Cost:** $0.4529
- **Comparison:** 5.0x current run cost
- **Per Item:** $0.4529

## File Processing Details

### Input Files Used
- ./docs/alphastrat/20-scope/20-2001-architecture.md
- ./docs/alphastrat/30-refinement/30-1003-scope-overview.md

### Output Files Created
- 30-2001-design-system.yaml

### Expected vs Actual Output
**Files created as expected (1):**
- ✓ 30-2001-design-system.yaml

✅ All files were created exactly as expected.

## Processing Results

Successfully processed 1 items


Each result contains the generated content based on your prompts and input items.
