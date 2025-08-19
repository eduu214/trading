# Batch Processing Summary

**Generation Date:** 2025-08-15T05:00:42.913Z
**Batch ID:** /Users/andywillis/dev/workspace/trading/docs/flowplane/30-refinement
**Model:** claude-3-5-haiku-20241022
**Temperature:** 0.3
**Processing Mode:** Streaming API
**Dry Run:** No (real API calls)
**Step:** Create Requirements Traceability

## Processing Statistics

- **Total Items:** 1
- **Successful:** 1
- **Failed:** 0
- **Success Rate:** 100.0%
- **Processing Time:** 29.6 seconds
- **Processing Speed:** 2.0 items/minute
- **Token Throughput:** 62.842 tokens/second

## Token Usage

### Summary
- **Total Input Tokens:** 18
- **Total Output Tokens:** 1,842
- **Total Tokens:** 1,860

### Cache Performance
- **Cache Creation Tokens:** 10,787
- **Cache Read Tokens:** 0
- **Cache Hit Rate:** 100.0%
- **Tokens Saved:** 0 (90% discount on cached tokens)

### Averages Per Item
- **Average Input Tokens:** 18
- **Average Output Tokens:** 1,842

## Document Caching Breakdown

### Cache Optimization
Documents are automatically ordered from broadest to narrowest scope for optimal cache reuse:
1. **Project-wide** → Cached once, used by all items
2. **Feature-wide** → Cached per feature, shared by all stories
3. **Story-specific** → Not cached, unique per story

### Document Usage
| Document | Scope | Cacheable | Times Used | Cache Efficiency |
|----------|-------|-----------|------------|------------------|
| 30-3001-infrastructure-registry.yaml | Project | ✅ Yes | 1 | First use |
| 30-4001-requirements-catalog.md | Project | ✅ Yes | 1 | First use |
| 30-1001-feature-registry.yaml | Project | ✅ Yes | 1 | First use |
| 30-1002-story-registry.yaml | Project | ✅ Yes | 1 | First use |

### Cache Statistics
- **Documents Processed:** 4
- **Cacheable Documents:** 4 (100%)
- **Total Document Uses:** 4
- **Cached Document Uses:** 4 (100%)


## Cost Analysis

### Detailed Breakdown
- **Input Token Cost:** $0.0000
- **Output Token Cost:** $0.0074
- **Cache Write Cost:** $0.0108
- **Cache Read Cost:** $0.0000

### Total Cost
- **Total Cost:** $0.0182
- **Average Cost per Item:** $0.0182

### Cache Savings
- **Input Cost Without Caching:** $0.0086
- **Input Cost With Caching:** $0.0108
- **Cache Savings:** $-0.0022 (-25.0%)
- **Note:** Output costs ($0.0074) are the same regardless of caching

## Model Cost Comparison

Estimated costs for this same workload using different Claude models:

### Claude 3.5 Haiku (Latest)
- **Cost:** $0.0182
- **Comparison:** 1.0x current run cost
- **Per Item:** $0.0182

### Claude 4 Sonnet
- **Cost:** $0.0681
- **Comparison:** 3.8x current run cost
- **Per Item:** $0.0681

### Claude 4 Opus
- **Cost:** $0.3404
- **Comparison:** 18.8x current run cost
- **Per Item:** $0.3404

## File Processing Details

### Input Files Used
- ./docs/flowplane/30-refinement/30-1001-feature-registry.yaml
- ./docs/flowplane/30-refinement/30-1002-story-registry.yaml
- ./docs/flowplane/30-refinement/30-3001-infrastructure-registry.yaml
- ./docs/flowplane/30-refinement/30-4001-requirements-catalog.md

### Output Files Created
- 30-5001-requirements-traceability.md

### Expected vs Actual Output
**Files created as expected (1):**
- ✓ 30-5001-requirements-traceability.md

✅ All files were created exactly as expected.

## Processing Results

Successfully processed 1 items


Each result contains the generated content based on your prompts and input items.
