# Batch Processing Summary

**Generation Date:** 2025-08-15T04:59:42.716Z
**Batch ID:** /Users/andywillis/dev/workspace/trading/docs/flowplane/30-refinement
**Model:** claude-sonnet-4-20250514
**Temperature:** 0.3
**Processing Mode:** Streaming API
**Dry Run:** No (real API calls)
**Step:** Extract Requirements Catalog

## Processing Statistics

- **Total Items:** 1
- **Successful:** 1
- **Failed:** 0
- **Success Rate:** 100.0%
- **Processing Time:** 83.0 seconds
- **Processing Speed:** 0.7 items/minute
- **Token Throughput:** 61.615 tokens/second

## Token Usage

### Summary
- **Total Input Tokens:** 15
- **Total Output Tokens:** 5,101
- **Total Tokens:** 5,116

### Cache Performance
- **Cache Creation Tokens:** 4,832
- **Cache Read Tokens:** 0
- **Cache Hit Rate:** 100.0%
- **Tokens Saved:** 0 (90% discount on cached tokens)

### Averages Per Item
- **Average Input Tokens:** 15
- **Average Output Tokens:** 5,101

## Document Caching Breakdown

### Cache Optimization
Documents are automatically ordered from broadest to narrowest scope for optimal cache reuse:
1. **Project-wide** → Cached once, used by all items
2. **Feature-wide** → Cached per feature, shared by all stories
3. **Story-specific** → Not cached, unique per story

### Document Usage
| Document | Scope | Cacheable | Times Used | Cache Efficiency |
|----------|-------|-----------|------------|------------------|
| 30-1003-scope-overview.md | Project | ✅ Yes | 1 | First use |
| 30-1001-feature-registry.yaml | Project | ✅ Yes | 1 | First use |
| 30-3001-infrastructure-registry.yaml | Project | ✅ Yes | 1 | First use |

### Cache Statistics
- **Documents Processed:** 3
- **Cacheable Documents:** 3 (100%)
- **Total Document Uses:** 3
- **Cached Document Uses:** 3 (100%)


## Cost Analysis

### Detailed Breakdown
- **Input Token Cost:** $0.0000
- **Output Token Cost:** $0.0765
- **Cache Write Cost:** $0.0181
- **Cache Read Cost:** $0.0000

### Total Cost
- **Total Cost:** $0.0946
- **Average Cost per Item:** $0.0946

### Cache Savings
- **Input Cost Without Caching:** $0.0145
- **Input Cost With Caching:** $0.0181
- **Cache Savings:** $-0.0036 (-25.0%)
- **Note:** Output costs ($0.0765) are the same regardless of caching

## Model Cost Comparison

Estimated costs for this same workload using different Claude models:

### Claude 3.5 Haiku (Latest)
- **Cost:** $0.0252
- **Comparison:** 0.3x current run cost
- **Per Item:** $0.0252

### Claude 4 Sonnet (Current Run)
- **Cost:** $0.0946
- **Comparison:** Baseline
- **Per Item:** $0.0946

### Claude 4 Opus
- **Cost:** $0.4732
- **Comparison:** 5.0x current run cost
- **Per Item:** $0.4732

## File Processing Details

### Input Files Used
- ./docs/flowplane/30-refinement/30-1001-feature-registry.yaml
- ./docs/flowplane/30-refinement/30-1003-scope-overview.md
- ./docs/flowplane/30-refinement/30-3001-infrastructure-registry.yaml

### Output Files Created
- 30-4001-requirements-catalog.md

### Expected vs Actual Output
**Files created as expected (1):**
- ✓ 30-4001-requirements-catalog.md

✅ All files were created exactly as expected.

## Processing Results

Successfully processed 1 items


Each result contains the generated content based on your prompts and input items.
