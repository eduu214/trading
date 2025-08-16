# Feature Technical Architecture - F006: Web-Based Command Center

## 1. Architecture Overview

### 1.1 Technical Strategy
The Web-Based Command Center leverages Next.js 14+ with TypeScript for the frontend, providing server-side rendering capabilities and optimal performance. The interface connects to the FastAPI backend through RESTful APIs and maintains real-time connectivity via WebSocket connections. PostgreSQL with TimescaleDB serves as the primary data store for historical performance data, while Redis provides caching for frequently accessed dashboard metrics. The architecture emphasizes responsive design using Tailwind CSS with shadcn/ui components, ensuring consistent user experience across desktop and mobile devices.

### 1.2 Key Decisions
- **Decision**: Next.js 14+ with TypeScript for frontend framework
- **Rationale**: Server-side rendering improves initial load times for data-heavy dashboards, TypeScript ensures type safety for financial calculations
- **Trade-offs**: Gain performance and developer experience, sacrifice some bundle size optimization

- **Decision**: WebSocket + Server-Sent Events for real-time updates
- **Rationale**: Financial dashboards require immediate feedback on portfolio changes and market movements
- **Trade-offs**: Gain real-time responsiveness, sacrifice some server resource efficiency

- **Decision**: Zustand for state management over Redux
- **Rationale**: Simpler API reduces complexity for financial dashboard state management
- **Trade-offs**: Gain development speed and maintainability, sacrifice ecosystem size

## 2. Shared Component Architecture

### 2.1 Real-Time Dashboard Framework
- **Purpose**: Provides live updating dashboard infrastructure for all monitoring interfaces
- **Used By**: F006-US001, F006-US002, F006-US003
- **Behaviors**: Maintains WebSocket connections, coordinates data refresh cycles, manages connection resilience
- **Technology**: WebSocket + Server-Sent Events with automatic reconnection
- **Constraints**: Updates must reflect actual system state within 30 seconds, handle 50+ concurrent strategy displays
- **Dependencies**: SVC-005 (Real-time Notifications)

### 2.2 Financial Data Visualization Engine
- **Purpose**: Renders charts, performance metrics, and portfolio analytics with financial-specific formatting
- **Used By**: F006-US002, F006-US003
- **Behaviors**: Transforms raw financial data into interactive visualizations, handles profit/loss color coding, manages chart responsiveness
- **Technology**: Chart.js with custom financial chart types, D3.js for complex visualizations
- **Constraints**: Render 50+ strategy performance charts simultaneously, maintain 60fps interaction performance
- **Performance**: Sub-second chart rendering for portfolio overview

### 2.3 Strategy Action Interface
- **Purpose**: Enables single-click strategy approval, rejection, and deployment actions
- **Used By**: F006-US001, F006-US002
- **Behaviors**: Validates user permissions, coordinates with validation framework, provides immediate feedback on actions
- **Technology**: React Hook Form with Zod validation, optimistic UI updates
- **Constraints**: Complete strategy deployment within 15 minutes of user review, prevent unauthorized actions
- **Dependencies**: SVC-003 (Validation Framework), SVC-002 (Strategy Execution Engine)

### 2.4 Portfolio Risk Monitor
- **Purpose**: Displays real-time risk metrics and correlation analysis across strategy portfolio
- **Used By**: F006-US002, F006-US003
- **Behaviors**: Calculates portfolio VaR in real-time, monitors individual strategy drawdowns, tracks aggregate position limits
- **Technology**: Custom risk calculation engine with WebSocket updates
- **Constraints**: Risk metrics update within 30 seconds of portfolio changes, handle 100+ strategy correlation matrix
- **Performance**: Real-time correlation calculations for 50+ active strategies

## 3. Data Architecture

### 3.1 Dashboard State Management
The command center maintains hierarchical state management with strategy-level, portfolio-level, and system-level data layers. Strategy data includes performance metrics, current positions, and validation status. Portfolio data encompasses allocation percentages, correlation matrices, and aggregate risk metrics. System data tracks operational health, background task progress, and user session state. All state updates flow through Zustand stores with automatic persistence for user preferences and dashboard configurations.

### 3.2 Real-Time Data Flow
Market data and portfolio updates flow from Alpaca WebSocket feeds through the real-time notification service into the dashboard components. Strategy performance calculations occur in the backend with results pushed via Server-Sent Events. User actions trigger optimistic UI updates followed by backend validation and confirmation. Historical data queries leverage PostgreSQL with TimescaleDB for efficient time-series operations, with Redis caching for frequently accessed dashboard metrics.

### 3.3 Data Persistence Strategy
User dashboard configurations, preferred layouts, and alert settings persist in PostgreSQL user preference tables. Session state maintains temporary data like selected time ranges, active filters, and expanded strategy details. Performance data caching in Redis reduces database load for real-time dashboard updates while ensuring data consistency through cache invalidation on portfolio changes.

## 4. Service Layer

### 4.1 Dashboard Orchestration Service
- **Technology**: FastAPI with WebSocket support
- **Responsibility**: Coordinates data aggregation from multiple backend services for unified dashboard views
- **Performance**: Aggregate data from 5+ services within 500ms for dashboard refresh
- **Behaviors**: Manages concurrent data requests, handles service failures gracefully, provides fallback data when services unavailable

### 4.2 Real-Time Update Coordinator
- **Technology**: WebSocket + Server-Sent Events with Redis pub/sub
- **Responsibility**: Manages real-time data distribution to connected dashboard clients
- **Performance**: Distribute updates to 100+ concurrent users within 1 second
- **Behaviors**: Maintains client connection health, batches updates for efficiency, handles client reconnection seamlessly

### 4.3 User Interface State Service
- **Technology**: Next.js API routes with session management
- **Responsibility**: Manages user preferences, dashboard layouts, and personalization settings
- **Performance**: Load user preferences within 200ms of dashboard initialization
- **Behaviors**: Persists layout changes automatically, synchronizes preferences across browser sessions, provides default configurations for new users

### 4.4 Financial Calculation Engine
- **Technology**: Custom TypeScript modules with financial math libraries
- **Responsibility**: Performs client-side financial calculations for immediate UI feedback
- **Performance**: Calculate portfolio metrics for 50+ strategies within 100ms
- **Behaviors**: Validates calculation inputs, handles edge cases in financial formulas, provides calculation audit trails

## 5. Integration Architecture

### 5.1 Backend Service Integration
The command center integrates with all shared services through RESTful APIs and WebSocket connections. Strategy data flows from the validation framework and execution engine, portfolio calculations leverage the async task processor, and real-time updates utilize the notification service. Each integration includes circuit breaker patterns for resilience and fallback mechanisms for service unavailability.

### 5.2 External API Integration
Direct integration with Alpaca WebSocket API provides real-time portfolio positions and trade confirmations. Polygon.io market data feeds support real-time price displays and market status indicators. All external integrations include rate limit management and error handling with graceful degradation when services are unavailable.

### 5.3 Authentication Integration
Clerk authentication service provides secure user sessions with role-based access control. Dashboard components respect user permissions for strategy deployment actions and sensitive financial data access. Session management includes automatic renewal and secure logout procedures.

## 6. Architecture Validation

| Story | Components | Services | Requirements |
|-------|-----------|----------|--------------|
| F006-US001 | Real-Time Dashboard Framework, Strategy Action Interface, Financial Data Visualization Engine | Dashboard Orchestration Service, Real-Time Update Coordinator | NFR-U-001 (15-minute daily review), NFR-P-002 (<2s response time) |
| F006-US002 | Financial Data Visualization Engine, Portfolio Risk Monitor, Real-Time Dashboard Framework | Dashboard Orchestration Service, Financial Calculation Engine, User Interface State Service | NFR-P-004 (30s portfolio optimization), NFR-SC-002 (100+ strategy scaling) |
| F006-US003 | Real-Time Dashboard Framework, Portfolio Risk Monitor, Strategy Action Interface | Real-Time Update Coordinator, Dashboard Orchestration Service | NFR-P-002 (<2s response time), NFR-R-001 (99.5% uptime) |

### 6.1 Performance Architecture Validation
The architecture supports the target of 50+ concurrent strategies through efficient data aggregation and caching strategies. WebSocket connections with Redis pub/sub enable real-time updates for 100+ concurrent users. Client-side financial calculations reduce server load while maintaining calculation accuracy. Progressive loading and virtualization handle large strategy portfolios without performance degradation.

### 6.2 Usability Architecture Validation
Single-click deployment actions integrate with the validation framework to ensure safe strategy deployment. Dashboard layouts adapt to different screen sizes using responsive design principles. Progressive disclosure patterns prevent information overload while maintaining access to detailed strategy information. Real-time feedback provides immediate confirmation of user actions.

### 6.3 Reliability Architecture Validation
Circuit breaker patterns prevent cascade failures when backend services experience issues. Optimistic UI updates provide immediate feedback while backend validation ensures data consistency. Automatic reconnection logic maintains real-time connectivity during network interruptions. Fallback data sources ensure dashboard functionality during service outages.