# Feature Technical Architecture - F006: Web-Based Command Center

## 1. Architecture Overview

### 1.1 Technical Strategy
The Web-Based Command Center leverages Next.js 14+ with TypeScript for the frontend, creating a responsive, real-time interface that connects directly to the FastAPI backend and PostgreSQL database established in the P10 architecture. The interface maintains persistent connections through WebSocket technology for sub-second updates while providing comprehensive portfolio management capabilities through shadcn/ui components and Tailwind CSS styling.

### 1.2 Key Decisions
- **Decision**: Next.js 14+ with Server-Side Rendering for initial page loads
- **Rationale**: Provides optimal performance for data-heavy financial dashboards while maintaining SEO capabilities and fast initial renders
- **Trade-offs**: Increased complexity vs improved performance and user experience

- **Decision**: WebSocket connections for real-time updates via SVC-005
- **Rationale**: Financial data requires immediate updates for trading decisions, REST polling introduces unacceptable latency
- **Trade-offs**: Connection management complexity vs real-time data accuracy

- **Decision**: Zustand for client-side state management
- **Rationale**: Simpler than Redux while providing sufficient state management for financial dashboard complexity
- **Trade-offs**: Less ecosystem tooling vs reduced development overhead

- **Decision**: shadcn/ui component library with financial-specific extensions
- **Rationale**: Provides professional UI foundation with customization flexibility for financial data visualization
- **Trade-offs**: Component customization effort vs consistent design system

## 2. Shared Component Architecture

### 2.1 Real-Time Data Display Components
**Purpose**: Present live financial data with automatic updates and visual state indicators
**Used By**: F006-US001, F006-US002, F006-US003
**Behaviors**: 
- Maintains WebSocket connections through SVC-005 for sub-second data updates
- Tracks connection state and provides fallback mechanisms during network interruptions
- Enables visual differentiation between live, delayed, and stale data states
- Coordinates data refresh cycles with market hours and trading sessions
**Constraints**: Updates must complete within 30 seconds, handle 50+ concurrent strategy displays

### 2.2 Strategy Performance Visualization
**Purpose**: Display strategy metrics, performance charts, and risk indicators in scannable format
**Used By**: F006-US001, F006-US002
**Behaviors**:
- Maintains performance history visualization using Chart.js integration
- Tracks multiple performance metrics simultaneously (Sharpe ratio, drawdown, correlation)
- Enables drill-down from portfolio view to individual strategy details
- Coordinates color coding for profit/loss states using design system tokens
**Constraints**: Render 100+ strategy cards without performance degradation, support mobile responsive layouts

### 2.3 Portfolio Management Interface
**Purpose**: Enable portfolio allocation changes, rebalancing decisions, and risk management controls
**Used By**: F006-US002, F006-US003
**Behaviors**:
- Maintains current portfolio state synchronized with PostgreSQL through API calls
- Tracks pending changes and provides preview of allocation impacts
- Enables drag-drop allocation adjustments with real-time constraint validation
- Coordinates with SVC-002 for portfolio optimization calculations
**Constraints**: Allocation changes must validate within 5 seconds, support 50+ strategy portfolio

### 2.4 Alert and Notification System
**Purpose**: Display system alerts, strategy notifications, and risk warnings with appropriate urgency
**Used By**: F006-US001, F006-US003
**Behaviors**:
- Maintains notification queue with priority-based display ordering
- Tracks user acknowledgment states for critical alerts
- Enables filtering and categorization of notification types
- Coordinates with SVC-005 for real-time alert delivery
**Constraints**: Critical alerts must display within 5 seconds, support notification history

### 2.5 Interactive Data Tables
**Purpose**: Present tabular financial data with sorting, filtering, and selection capabilities
**Used By**: F006-US001, F006-US002
**Behaviors**:
- Maintains column state preferences and sorting configurations
- Tracks row selection for batch operations on strategies
- Enables real-time data updates within table cells
- Coordinates with backend APIs for server-side filtering and pagination
**Constraints**: Handle 1000+ rows with virtual scrolling, maintain 60fps scroll performance

## 3. Data Architecture

### 3.1 Real-Time Data Flow
The command center maintains bidirectional data flow between the Next.js frontend and FastAPI backend. WebSocket connections through SVC-005 provide real-time updates for portfolio performance, strategy status changes, and system alerts. Client-side state management through Zustand coordinates between WebSocket updates and user interactions, ensuring data consistency across components.

### 3.2 State Management Patterns
Application state divides into three layers: server state (cached from PostgreSQL), real-time state (WebSocket updates), and UI state (user interactions). Server state uses React Query for caching and synchronization, real-time state flows through WebSocket handlers, and UI state manages through Zustand stores with persistence to localStorage for user preferences.

### 3.3 Data Persistence Requirements
User interface preferences, dashboard configurations, and alert acknowledgments persist in PostgreSQL through dedicated user settings tables. Real-time data maintains in Redis cache for immediate access, while historical performance data queries directly from TimescaleDB for chart generation and analysis.

## 4. Service Layer

### 4.1 Dashboard API Service
**Technology**: FastAPI with WebSocket support
**Responsibility**: Coordinates data aggregation from multiple backend services for dashboard display
**Performance**: Sub-second response times for dashboard data, handle 10+ concurrent WebSocket connections per user

### 4.2 User Preference Service
**Technology**: FastAPI with PostgreSQL persistence
**Responsibility**: Manages user interface configurations, alert preferences, and dashboard customizations
**Performance**: Instant preference updates, support personalization for multiple user profiles

### 4.3 Real-Time Update Coordinator
**Technology**: WebSocket server integrated with SVC-005
**Responsibility**: Manages WebSocket connections, coordinates update broadcasting, and handles connection lifecycle
**Performance**: Maintain persistent connections with <100ms latency, support graceful reconnection

### 4.4 Data Aggregation Service
**Technology**: FastAPI with Redis caching
**Responsibility**: Aggregates data from SVC-001, SVC-002, and DB-001 for dashboard consumption
**Performance**: Cache frequently accessed data, provide sub-second aggregation for portfolio views

## 5. Integration Architecture

### 5.1 Backend Service Integration
The command center integrates with SVC-005 for real-time notifications, SVC-002 for strategy execution data, and SVC-003 for validation status updates. API calls use Axios with TypeScript code generation for type safety, while WebSocket connections provide real-time updates for time-sensitive financial data.

### 5.2 External Service Boundaries
Direct integration with Alpaca WebSocket API provides real-time portfolio performance data, while Grafana dashboards embed for operational monitoring. Authentication flows through Clerk service for secure access control and session management.

### 5.3 Event-Driven Updates
Strategy status changes, portfolio rebalancing events, and system alerts flow through event-driven architecture. WebSocket events trigger React component re-renders, while background sync processes ensure data consistency during connection interruptions.

## 6. Architecture Validation

| Story | Components | Services | Requirements |
|-------|-----------|----------|--------------|
| F006-US001 | Real-Time Data Display, Strategy Performance Visualization, Interactive Data Tables, Alert System | Dashboard API, Real-Time Update Coordinator, Data Aggregation | NFR-U-001 (15min review), NFR-P-002 (<2s response) |
| F006-US002 | Portfolio Management Interface, Strategy Performance Visualization, Interactive Data Tables | Dashboard API, User Preference Service, Data Aggregation | NFR-P-004 (30s optimization), NFR-SC-002 (100+ strategies) |
| F006-US003 | Real-Time Data Display, Alert System, Portfolio Management Interface | Real-Time Update Coordinator, Dashboard API | NFR-P-002 (<500ms API), NFR-R-001 (99.5% uptime) |

### 5.4 Performance Architecture
The command center implements performance optimization through multiple strategies: React component memoization for expensive renders, virtual scrolling for large data tables, WebSocket connection pooling for efficient real-time updates, and progressive loading for dashboard initialization. Chart.js integration provides hardware-accelerated financial data visualization while maintaining 60fps performance targets.

### 5.5 Responsive Design Architecture
Mobile-first responsive design ensures core monitoring functions remain accessible across device types. Critical portfolio management features adapt to touch interfaces while maintaining full desktop functionality. Progressive Web App capabilities enable offline access to cached portfolio data during network interruptions.

### 5.6 Error Handling and Resilience
Comprehensive error boundaries prevent component failures from affecting entire dashboard functionality. WebSocket reconnection logic handles network interruptions gracefully, while fallback polling mechanisms ensure data updates continue during connection issues. User-friendly error messages provide actionable guidance for resolution.