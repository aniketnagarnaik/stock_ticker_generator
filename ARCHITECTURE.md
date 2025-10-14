# Clean Architecture Documentation

## Overview

The stock ticker application has been refactored to follow clean architecture principles, separating concerns into distinct layers for better maintainability, testability, and extensibility.

## Architecture Layers

### 1. Data Providers Layer (`data_providers/`)

**Purpose**: Fetch raw data from external sources only

**Components**:
- `base_provider.py` - Abstract base class defining provider interface
- `defeatbeta_provider.py` - Fetches stock data from defeatbeta-api (Hugging Face)
- `polygon_provider.py` - Fetches benchmark data from Polygon.io
- `yahoo_provider.py` - Fetches data from Yahoo Finance (fallback)
- `provider_manager.py` - Manages provider selection and fallback logic

**Responsibilities**:
- Fetch raw data from external APIs
- Handle API-specific formatting and error handling
- Rate limiting and caching (where appropriate)
- **NO business logic or calculations**

### 2. Data Access Object (DAO) Layer (`dao/`)

**Purpose**: Handle all database operations

**Components**:
- `base_dao.py` - Base class with common CRUD operations
- `stock_dao.py` - Operations for `stocks` table
- `stock_metrics_dao.py` - Operations for `stock_metrics` table  
- `index_dao.py` - Operations for `indices` table

**Responsibilities**:
- Database CRUD operations
- Data persistence and retrieval
- Transaction management
- **NO business logic**

### 3. Business Logic Layer (`business/`)

**Purpose**: Handle all business rules, calculations, and data orchestration

**Components**:
- `calculations.py` - Financial calculations (EMA, RS, EPS growth)
- `sector_mapper.py` - Sector-to-ETF mapping for RS calculations
- `data_orchestrator.py` - Coordinates data flow between layers

**Responsibilities**:
- Financial calculations (EMA, relative strength, EPS growth)
- Data validation and transformation
- Business rule enforcement
- Orchestrating data flow between providers, DAOs, and calculations

### 4. Publisher Layer (`publisher/`)

**Purpose**: High-level data publishing and refresh orchestration

**Components**:
- `data_publisher.py` - Main publishing interface
- `yahoo_client.py` - Legacy Yahoo Finance client (deprecated)

**Responsibilities**:
- High-level data refresh orchestration
- Refresh logging and status tracking
- Public API for data operations

### 5. Application Layer (`app.py`)

**Purpose**: Flask web application and API endpoints

**Responsibilities**:
- HTTP request/response handling
- Template rendering
- API endpoint definitions
- **Minimal business logic - delegates to business layer**

## Data Flow

```
External APIs → Data Providers → Business Logic → DAOs → Database
                     ↓              ↓
              Data Orchestrator ← Calculations
                     ↓
              Data Publisher ← App Layer
```

### Detailed Flow:

1. **Data Refresh Triggered**:
   - `app.py` receives refresh request
   - `DataPublisher.publish_all_stocks()` called
   - `DataOrchestrator.refresh_benchmark_data()` called first

2. **Benchmark Data Refresh**:
   - `PolygonProvider.get_benchmark_data()` fetches SPY/QQQ data
   - `IndexDAO.upsert_index()` stores data in `indices` table

3. **Stock Data Processing**:
   - `DataOrchestrator.process_stock_data()` processes each stock
   - `DefeatBetaProvider.get_stock_info()` fetches raw stock data
   - `FinancialCalculations.calculate_all_emas()` calculates EMAs
   - `FinancialCalculations.calculate_eps_growth()` calculates EPS metrics
   - `FinancialCalculations.calculate_relative_strength()` calculates RS
   - `StockDAO.upsert_stock()` and `StockMetricsDAO.upsert_metrics()` store data

4. **Data Retrieval**:
   - `app.py` calls `DataOrchestrator.get_all_stocks_data()`
   - `StockMetricsDAO.get_combined_stock_data()` joins stocks and metrics
   - Data returned to UI

## Key Benefits

### 1. Separation of Concerns
- Each layer has a single responsibility
- Easy to modify one layer without affecting others
- Clear boundaries between external data, business logic, and persistence

### 2. Testability
- Business logic can be tested independently of data sources
- Mock data providers for unit testing
- Isolated database operations

### 3. Extensibility
- Easy to add new data providers (implement `BaseDataProvider`)
- New calculations can be added to `calculations.py`
- Database schema changes isolated to DAO layer

### 4. Maintainability
- Clear code organization
- Reduced coupling between components
- Easier debugging and troubleshooting

## Database Schema

### Tables:
1. **`stocks`** - Basic stock information
   - `id`, `symbol`, `company_name`, `sector`, `industry`
   - `market_cap`, `current_price`, `last_updated`, `created_at`

2. **`stock_metrics`** - Calculated metrics
   - `id`, `symbol`, `stock_id`, `eps_growth_qoq`, `eps_growth_yoy`
   - `latest_quarterly_eps`, `rs_spy`, `rs_sector`
   - `ema_data` (JSON), `eps_history` (JSON), `last_updated`

3. **`indices`** - Benchmark data
   - `id`, `symbol`, `name`, `price_data` (JSON)
   - `last_updated`, `created_at`

4. **`refresh_logs`** - Refresh tracking
   - `id`, `status`, `successful_count`, `failed_count`
   - `error_message`, `started_at`, `completed_at`

## Configuration

### Environment Variables:
- `DATABASE_URL` - PostgreSQL connection string
- `POLYGON_API_KEY` - Polygon.io API key for benchmark data

### Provider Configuration:
- Provider priority defined in `ProviderManager`
- Fallback logic handled automatically
- Rate limiting configured per provider

## Migration Guide

### From Old Architecture:
1. **Data Providers**: Moved from `yahoo_client.py` to dedicated provider classes
2. **Calculations**: Moved from provider classes to `business/calculations.py`
3. **Database Operations**: Moved from `data_publisher.py` to DAO classes
4. **Orchestration**: New `DataOrchestrator` coordinates all operations

### Backward Compatibility:
- Public APIs remain the same (`app.py` routes)
- Database schema unchanged
- External interfaces preserved

## Future Enhancements

### Potential Additions:
1. **New Data Providers**: Alpha Vantage, IEX Cloud, etc.
2. **Additional Calculations**: Technical indicators, fundamental ratios
3. **Caching Layer**: Redis for improved performance
4. **Background Jobs**: Celery for async processing
5. **API Versioning**: RESTful API versioning
6. **Monitoring**: Health checks and metrics

### Testing Strategy:
1. **Unit Tests**: Test each layer independently
2. **Integration Tests**: Test layer interactions
3. **End-to-End Tests**: Test complete data flows
4. **Performance Tests**: Test with large datasets

## Troubleshooting

### Common Issues:
1. **Provider Failures**: Check API keys and network connectivity
2. **Calculation Errors**: Verify data format and business logic
3. **Database Issues**: Check connection strings and schema
4. **Performance**: Monitor database queries and API rate limits

### Debugging:
- Enable debug logging in each layer
- Use database query logging
- Monitor API response times
- Check refresh logs for errors
