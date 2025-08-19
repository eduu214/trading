# Batch Processing Summary

**Generation Date:** 2025-08-15T04:20:56.556Z
**Batch ID:** /Users/andywillis/dev/workspace/trading/docs/alphastrat/20-scope
**Model:** claude-sonnet-4-20250514
**Temperature:** 0.3
**Processing Mode:** Streaming API
**Dry Run:** No (real API calls)
**Step:** Alignment Check - Scope vs Architecture

## Processing Statistics

- **Total Items:** 1
- **Successful:** 1
- **Failed:** 0
- **Success Rate:** 100.0%
- **Processing Time:** 40.4 seconds
- **Processing Speed:** 1.5 items/minute
- **Token Throughput:** 360.059 tokens/second

## Token Usage

### Summary
- **Total Input Tokens:** 12,383
- **Total Output Tokens:** 2,176
- **Total Tokens:** 14,559

### Cache Performance
- **Cache Creation Tokens:** 2,904
- **Cache Read Tokens:** 0
- **Cache Hit Rate:** 100.0%
- **Tokens Saved:** 0 (90% discount on cached tokens)

### Averages Per Item
- **Average Input Tokens:** 12,383
- **Average Output Tokens:** 2,176

## Document Caching Breakdown

### Cache Optimization
Documents are automatically ordered from broadest to narrowest scope for optimal cache reuse:
1. **Project-wide** → Cached once, used by all items
2. **Feature-wide** → Cached per feature, shared by all stories
3. **Story-specific** → Not cached, unique per story

### Document Usage
| Document | Scope | Cacheable | Times Used | Cache Efficiency |
|----------|-------|-----------|------------|------------------|
| 20-1001-scope.md | Project | ❌ No | 1 | N/A |
| 20-2001-architecture.md | Project | ❌ No | 1 | N/A |
| 20-3001-alignment-analysis.md | Project | ❌ No | 1 | N/A |
| 20-3002-scope-updates.md | Project | ❌ No | 1 | N/A |
| 20-3003-architecture-updates.md | Project | ❌ No | 1 | N/A |

### Cache Statistics
- **Documents Processed:** 5
- **Cacheable Documents:** 0 (0%)
- **Total Document Uses:** 5
- **Cached Document Uses:** 0 (0%)


## Cost Analysis

### Detailed Breakdown
- **Input Token Cost:** $0.0284
- **Output Token Cost:** $0.0326
- **Cache Write Cost:** $0.0109
- **Cache Read Cost:** $0.0000

### Total Cost
- **Total Cost:** $0.0720
- **Average Cost per Item:** $0.0720

### Cache Savings
- **Input Cost Without Caching:** $0.0371
- **Input Cost With Caching:** $0.0393
- **Cache Savings:** $-0.0022 (-5.9%)
- **Note:** Output costs ($0.0326) are the same regardless of caching

## Model Cost Comparison

Estimated costs for this same workload using different Claude models:

### Claude 3.5 Haiku (Latest)
- **Cost:** $0.0192
- **Comparison:** 0.3x current run cost
- **Per Item:** $0.0192

### Claude 4 Sonnet (Current Run)
- **Cost:** $0.0720
- **Comparison:** Baseline
- **Per Item:** $0.0720

### Claude 4 Opus
- **Cost:** $0.3598
- **Comparison:** 5.0x current run cost
- **Per Item:** $0.3598

## File Processing Details

### Input Files Used
- ./docs/alphastrat/20-scope/20-1001-scope.md
- ./docs/alphastrat/20-scope/20-2001-architecture.md
- ./docs/alphastrat/20-scope/20-3001-alignment-analysis.md
- ./docs/alphastrat/20-scope/20-3002-scope-updates.md
- ./docs/alphastrat/20-scope/20-3003-architecture-updates.md

### Output Files Created
- 20-3001-alignment-analysis.md
- 20-3002-scope-updates.md
- 20-3003-architecture-updates.md

### Expected vs Actual Output
**Files created as expected (3):**
- ✓ 20-3001-alignment-analysis.md
- ✓ 20-3002-scope-updates.md
- ✓ 20-3003-architecture-updates.md

✅ All files were created exactly as expected.

## Processing Results

Successfully processed 1 items


Each result contains the generated content based on your prompts and input items.
