# Batch Processing Summary

**Generation Date:** 2025-08-18T20:37:48.738Z
**Output Path:** /Users/andywillis/dev/workspace/jack-trading/docs/flowplane/40-design
**Model:** claude-sonnet-4-20250514
**Temperature:** 0.3
**Processing Mode:** Streaming API
**API Calls:** Real API calls
**Step:** Custom batch processing

## Processing Statistics

- **Total Items:** 6
- **Successful:** 6
- **Failed:** 0
- **Success Rate:** 100.0%
- **Processing Time:** 86.2 seconds
- **Processing Speed:** 4.2 items/minute
- **Token Throughput:** 143.22 tokens/second

## Token Usage

### Summary
- **Total Input Tokens:** 126
- **Total Output Tokens:** 12,218
- **Total Tokens:** 12,344

### Cache Performance
- **Cache Creation Tokens:** 102,711
- **Cache Read Tokens:** 6,615
- **Cache Hit Rate:** 100.0%
- **Tokens Saved:** 5,953.5 (90% discount on cached tokens)

### Averages Per Item
- **Average Input Tokens:** 21
- **Average Output Tokens:** 2,036

## Document Caching Breakdown

### Cache Optimization
Documents are automatically ordered from broadest to narrowest scope for optimal cache reuse:
1. **Project-wide** → Cached once, used by all items
2. **Feature-wide** → Cached per feature, shared by all stories
3. **Story-specific** → Not cached, unique per story

### Document Usage
| Document | Scope | Cacheable | Times Used | Cache Efficiency |
|----------|-------|-----------|------------|------------------|
| 20-2001-architecture.md | Project | ✅ Yes | 6 | 83% reuse |
| 30-2001-design-system.yaml | Project | ✅ Yes | 6 | 83% reuse |
| 30-3001-infrastructure-registry.yaml | Project | ✅ Yes | 6 | 83% reuse |
| 30-4001-requirements-catalog.md | Project | ✅ Yes | 6 | 83% reuse |
| 30-1001-feature-registry.yaml | Project | ✅ Yes | 6 | 83% reuse |

### Cache Statistics
- **Documents Processed:** 5
- **Cacheable Documents:** 5 (100%)
- **Total Document Uses:** 30
- **Cached Document Uses:** 30 (100%)


## Cost Analysis

### Detailed Breakdown
- **Input Token Cost:** $0.0000
- **Output Token Cost:** $0.1833
- **Cache Write Cost:** $0.3852
- **Cache Read Cost:** $0.0020

### Total Cost
- **Total Cost:** $0.5704
- **Average Cost per Item:** $0.0951

### Cache Savings
- **Input Cost Without Caching:** $1.8488
- **Input Cost With Caching:** $0.3872
- **Cache Savings:** $1.4616 (79.1%)
- **Note:** Output costs ($0.1833) are the same regardless of caching

## Model Cost Comparison

Estimated costs for this same workload using different Claude models:

### Claude 3.5 Haiku (Latest)
- **Cost:** $0.1521
- **Comparison:** 0.3x current run cost
- **Per Item:** $0.0254

### Claude 4 Sonnet (Current Run)
- **Cost:** $0.5704
- **Comparison:** Baseline
- **Per Item:** $0.0951

### Claude 4 Opus
- **Cost:** $2.8521
- **Comparison:** 5.0x current run cost
- **Per Item:** $0.4754

## File Processing Details

### Input Files Used
- ./docs/flowplane/20-scope/20-2001-architecture.md
- ./docs/flowplane/30-refinement/30-1001-feature-registry.yaml
- ./docs/flowplane/30-refinement/30-2001-design-system.yaml
- ./docs/flowplane/30-refinement/30-3001-infrastructure-registry.yaml
- ./docs/flowplane/30-refinement/30-4001-requirements-catalog.md

### Output Files Created
- 40-3001-F001-technical.md
- 40-3001-F002-technical.md
- 40-3001-F003-technical.md
- 40-3001-F004-technical.md
- 40-3001-F005-technical.md
- 40-3001-F006-technical.md

### Expected vs Actual Output
No expected output files defined (not running a FlowPlane step).

## Processing Results

Successfully processed 6 items


Each result contains the generated content based on your prompts and input items.
