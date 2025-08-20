"""Database manager for schema creation and management."""

import logging
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from sqlalchemy import text, inspect, func
from sqlalchemy.exc import SQLAlchemyError

from src.database.connection import DatabaseConnection
from src.database.models import Base, RawTransaction, Company, Charge

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database schema creation and operations."""
    
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """Initialize database manager.
        
        Args:
            db_connection: Database connection instance. If None, uses global instance.
        """
        from src.database.connection import db_connection as global_db_connection
        self.db_connection = db_connection or global_db_connection
    
    def create_schemas(self) -> bool:
        """Create database schemas if they don't exist."""
        try:
            with self.db_connection.get_session() as session:
                # Create schemas
                session.execute(text("CREATE SCHEMA IF NOT EXISTS raw_data"))
                session.execute(text("CREATE SCHEMA IF NOT EXISTS normalized_data"))
                
                # Grant permissions
                session.execute(text("""
                    GRANT ALL PRIVILEGES ON SCHEMA raw_data TO CURRENT_USER
                """))
                session.execute(text("""
                    GRANT ALL PRIVILEGES ON SCHEMA normalized_data TO CURRENT_USER
                """))
                
                logger.info("Database schemas created successfully")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create schemas: {e}")
            return False
    
    def create_tables(self) -> bool:
        """Create all database tables."""
        try:
            # First create schemas
            if not self.create_schemas():
                return False
            
            # Create all tables
            Base.metadata.create_all(bind=self.db_connection.engine)
            logger.info("Database tables created successfully")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    def drop_tables(self) -> bool:
        """Drop all database tables."""
        try:
            Base.metadata.drop_all(bind=self.db_connection.engine)
            logger.info("Database tables dropped successfully")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop tables: {e}")
            return False
    
    def create_reporting_view(self) -> bool:
        """Create the daily transaction summary view with proper aggregation."""
        drop_view_sql = """
        DROP VIEW IF EXISTS normalized_data.daily_transaction_summary CASCADE;
        """
        
        create_view_sql = """
        CREATE VIEW normalized_data.daily_transaction_summary AS
        SELECT 
            DATE(c.created_at) as transaction_date,
            comp.company_name,
            comp.company_id,
            SUM(c.amount) as total_amount,
            COUNT(*) as transaction_count,
            AVG(c.amount) as average_amount,
            MIN(c.amount) as min_amount,
            MAX(c.amount) as max_amount,
            COUNT(CASE WHEN c.status = 'paid' THEN 1 END) as paid_count,
            COUNT(CASE WHEN c.status = 'refunded' THEN 1 END) as refunded_count,
            SUM(CASE WHEN c.status = 'paid' THEN c.amount ELSE 0 END) as paid_amount,
            SUM(CASE WHEN c.status = 'refunded' THEN c.amount ELSE 0 END) as refunded_amount
        FROM normalized_data.charges c
        JOIN normalized_data.companies comp ON c.company_id = comp.company_id
        WHERE c.status IN ('paid', 'refunded')
        GROUP BY DATE(c.created_at), comp.company_id, comp.company_name
        ORDER BY transaction_date DESC, total_amount DESC;
        """
        
        try:
            with self.db_connection.get_session() as session:
                # Drop existing view first to avoid column type conflicts
                session.execute(text(drop_view_sql))
                # Create the new view
                session.execute(text(create_view_sql))
                logger.info("Daily transaction summary view created successfully")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create reporting view: {e}")
            return False
    
    def table_exists(self, table_name: str, schema: str = "public") -> bool:
        """Check if a table exists in the database."""
        try:
            inspector = inspect(self.db_connection.engine)
            tables = inspector.get_table_names(schema=schema)
            return table_name in tables
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to check table existence: {e}")
            return False
    
    def get_table_row_count(self, table_name: str, schema: str = "public") -> Optional[int]:
        """Get the number of rows in a table."""
        try:
            with self.db_connection.get_session() as session:
                result = session.execute(
                    text(f"SELECT COUNT(*) FROM {schema}.{table_name}")
                )
                count = result.scalar()
                return count
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get row count for {schema}.{table_name}: {e}")
            return None
    
    def get_database_info(self) -> dict:
        """Get database information and statistics."""
        info = {
            "connection_string": self.db_connection.connection_string.replace(
                self.db_connection.connection_string.split("@")[0].split(":")[-1], "***"
            ),
            "schemas": [],
            "tables": {},
            "views": []
        }
        
        try:
            inspector = inspect(self.db_connection.engine)
            
            # Get schemas
            with self.db_connection.get_session() as session:
                result = session.execute(text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name IN ('raw_data', 'normalized_data', 'public')
                """))
                info["schemas"] = [row[0] for row in result]
            
            # Get tables for each schema
            for schema in info["schemas"]:
                tables = inspector.get_table_names(schema=schema)
                info["tables"][schema] = {}
                
                for table in tables:
                    row_count = self.get_table_row_count(table, schema)
                    info["tables"][schema][table] = {
                        "row_count": row_count,
                        "columns": len(inspector.get_columns(table, schema=schema))
                    }
            
            # Get views
            with self.db_connection.get_session() as session:
                result = session.execute(text("""
                    SELECT table_name, table_schema
                    FROM information_schema.views 
                    WHERE table_schema IN ('raw_data', 'normalized_data', 'public')
                """))
                info["views"] = [f"{row[1]}.{row[0]}" for row in result]
            
            return info
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get database info: {e}")
            return info
    
    def distribute_data_to_normalized_tables(self) -> Dict[str, Any]:
        """Distribute data from raw tables to normalized schema.
        
        This method coordinates the data transformation and distribution process
        by using the DataTransformer to convert raw data into the normalized
        companies and charges tables.
        
        Returns:
            Dictionary with distribution results and statistics
        """
        logger.info("Starting data distribution to normalized tables")
        
        try:
            # Import here to avoid circular imports
            from src.data_processing.transformer import DataTransformer
            
            # Initialize transformer with our database connection
            transformer = DataTransformer(self.db_connection)
            
            # Perform the transformation
            report = transformer.transform_to_schema(
                source_table="raw_transactions",
                batch_size=1000,
                validate_data=True,
                apply_business_rules=True
            )
            
            # Get additional statistics
            stats = transformer.get_transformation_statistics()
            integrity = transformer.validate_transformation_integrity()
            
            result = {
                'success': True,
                'transformation_report': {
                    'total_raw_rows': report.total_raw_rows,
                    'transformed_rows': report.transformed_rows,
                    'skipped_rows': report.skipped_rows,
                    'companies_created': report.companies_created,
                    'charges_created': report.charges_created,
                    'success_rate': report.transformation_success_rate,
                    'execution_time_seconds': report.execution_time_seconds,
                    'errors_count': len(report.transformation_errors),
                    'quality_issues_count': len(report.data_quality_issues)
                },
                'statistics': stats,
                'integrity_validation': integrity
            }
            
            logger.info(f"Data distribution completed successfully: {report}")
            return result
            
        except Exception as e:
            logger.error(f"Data distribution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'transformation_report': None,
                'statistics': None,
                'integrity_validation': None
            }
    
    def create_normalized_schema(self) -> bool:
        """Create the normalized database schema with companies and charges tables.
        
        This method creates the normalized_data schema and the companies and charges
        tables with proper relationships and constraints.
        
        Returns:
            True if schema creation was successful, False otherwise
        """
        logger.info("Creating normalized database schema")
        
        try:
            with self.db_connection.get_session() as session:
                # Create normalized_data schema if it doesn't exist
                session.execute(text("CREATE SCHEMA IF NOT EXISTS normalized_data"))
                
                # Grant permissions
                session.execute(text("""
                    GRANT ALL PRIVILEGES ON SCHEMA normalized_data TO CURRENT_USER
                """))
                
                # Create tables using SQLAlchemy metadata
                # This will create companies and charges tables with proper relationships
                Base.metadata.create_all(
                    bind=self.db_connection.engine,
                    tables=[Company.__table__, Charge.__table__]
                )
                
                logger.info("Normalized schema created successfully")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create normalized schema: {e}")
            return False
    
    def validate_normalized_schema(self) -> Dict[str, Any]:
        """Validate the normalized schema structure and constraints.
        
        Returns:
            Dictionary with validation results
        """
        logger.info("Validating normalized schema")
        
        validation_result = {
            'schema_exists': False,
            'companies_table_exists': False,
            'charges_table_exists': False,
            'foreign_key_constraints': [],
            'indexes': [],
            'validation_errors': [],
            'is_valid': False
        }
        
        try:
            inspector = inspect(self.db_connection.engine)
            
            # Check if normalized_data schema exists
            with self.db_connection.get_session() as session:
                result = session.execute(text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name = 'normalized_data'
                """))
                validation_result['schema_exists'] = result.fetchone() is not None
            
            if not validation_result['schema_exists']:
                validation_result['validation_errors'].append("normalized_data schema does not exist")
                return validation_result
            
            # Check if tables exist
            tables = inspector.get_table_names(schema='normalized_data')
            validation_result['companies_table_exists'] = 'companies' in tables
            validation_result['charges_table_exists'] = 'charges' in tables
            
            if not validation_result['companies_table_exists']:
                validation_result['validation_errors'].append("companies table does not exist")
            
            if not validation_result['charges_table_exists']:
                validation_result['validation_errors'].append("charges table does not exist")
            
            # Check foreign key constraints if both tables exist
            if validation_result['companies_table_exists'] and validation_result['charges_table_exists']:
                fk_constraints = inspector.get_foreign_keys('charges', schema='normalized_data')
                validation_result['foreign_key_constraints'] = [
                    {
                        'name': fk['name'],
                        'constrained_columns': fk['constrained_columns'],
                        'referred_table': fk['referred_table'],
                        'referred_columns': fk['referred_columns']
                    }
                    for fk in fk_constraints
                ]
                
                # Validate that the expected foreign key exists
                expected_fk_found = any(
                    'company_id' in fk['constrained_columns'] and 
                    fk['referred_table'] == 'companies'
                    for fk in fk_constraints
                )
                
                if not expected_fk_found:
                    validation_result['validation_errors'].append(
                        "Expected foreign key constraint from charges.company_id to companies.company_id not found"
                    )
            
            # Check indexes
            if validation_result['companies_table_exists']:
                company_indexes = inspector.get_indexes('companies', schema='normalized_data')
                validation_result['indexes'].extend([
                    {'table': 'companies', 'name': idx['name'], 'columns': idx['column_names']}
                    for idx in company_indexes
                ])
            
            if validation_result['charges_table_exists']:
                charge_indexes = inspector.get_indexes('charges', schema='normalized_data')
                validation_result['indexes'].extend([
                    {'table': 'charges', 'name': idx['name'], 'columns': idx['column_names']}
                    for idx in charge_indexes
                ])
            
            # Overall validation
            validation_result['is_valid'] = (
                validation_result['schema_exists'] and
                validation_result['companies_table_exists'] and
                validation_result['charges_table_exists'] and
                len(validation_result['validation_errors']) == 0
            )
            
            logger.info(f"Schema validation completed: {'VALID' if validation_result['is_valid'] else 'INVALID'}")
            return validation_result
            
        except SQLAlchemyError as e:
            logger.error(f"Schema validation failed: {e}")
            validation_result['validation_errors'].append(f"Database error: {str(e)}")
            return validation_result
    
    def get_data_distribution_statistics(self) -> Dict[str, Any]:
        """Get statistics about data distribution in normalized tables.
        
        Returns:
            Dictionary with distribution statistics
        """
        logger.info("Getting data distribution statistics")
        
        try:
            with self.db_connection.get_session() as session:
                # Basic counts
                companies_count = session.query(Company).count()
                charges_count = session.query(Charge).count()
                raw_count = session.query(RawTransaction).count()
                
                # Company statistics
                company_stats = session.query(
                    func.count(Charge.id).label('charge_count'),
                    func.sum(Charge.amount).label('total_amount'),
                    Company.company_name
                ).join(Charge).group_by(Company.company_id, Company.company_name).all()
                
                # Status distribution
                status_distribution = session.query(
                    Charge.status,
                    func.count(Charge.id).label('count'),
                    func.sum(Charge.amount).label('total_amount')
                ).group_by(Charge.status).all()
                
                # Date range
                date_range = session.query(
                    func.min(Charge.created_at).label('earliest'),
                    func.max(Charge.created_at).label('latest')
                ).first()
                
                # Data integrity checks
                orphaned_charges = session.query(Charge).outerjoin(Company).filter(
                    Company.company_id.is_(None)
                ).count()
                
                companies_without_charges = session.query(Company).outerjoin(Charge).filter(
                    Charge.company_id.is_(None)
                ).count()
                
                return {
                    'record_counts': {
                        'raw_transactions': raw_count,
                        'companies': companies_count,
                        'charges': charges_count,
                        'transformation_rate': (charges_count / raw_count * 100) if raw_count > 0 else 0
                    },
                    'company_statistics': [
                        {
                            'company_name': stat.company_name,
                            'charge_count': stat.charge_count,
                            'total_amount': float(stat.total_amount) if stat.total_amount else 0
                        }
                        for stat in company_stats
                    ],
                    'status_distribution': [
                        {
                            'status': stat.status,
                            'count': stat.count,
                            'total_amount': float(stat.total_amount) if stat.total_amount else 0
                        }
                        for stat in status_distribution
                    ],
                    'date_range': {
                        'earliest': date_range.earliest.isoformat() if date_range.earliest else None,
                        'latest': date_range.latest.isoformat() if date_range.latest else None
                    },
                    'data_integrity': {
                        'orphaned_charges': orphaned_charges,
                        'companies_without_charges': companies_without_charges,
                        'integrity_score': 100 - (orphaned_charges * 10) - (companies_without_charges * 5)
                    }
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get distribution statistics: {e}")
            return {'error': str(e)}
    
    def initialize_database(self) -> bool:
        """Initialize the complete database structure."""
        logger.info("Initializing database structure...")
        
        # Test connection first
        if not self.db_connection.test_connection():
            logger.error("Database connection test failed")
            return False
        
        # Create tables
        if not self.create_tables():
            logger.error("Failed to create database tables")
            return False
        
        # Create reporting view
        if not self.create_reporting_view():
            logger.error("Failed to create reporting view")
            return False
        
        logger.info("Database initialization completed successfully")
        return True
    
    def query_daily_transaction_summary(self, 
                                      start_date: Optional[str] = None,
                                      end_date: Optional[str] = None,
                                      company_id: Optional[str] = None,
                                      limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query the daily transaction summary view with optional filters.
        
        Args:
            start_date: Start date filter (YYYY-MM-DD format)
            end_date: End date filter (YYYY-MM-DD format)
            company_id: Company ID filter
            limit: Maximum number of results to return
            
        Returns:
            List of dictionaries containing daily transaction summaries
        """
        logger.info(f"Querying daily transaction summary with filters: start_date={start_date}, end_date={end_date}, company_id={company_id}, limit={limit}")
        
        try:
            with self.db_connection.get_session() as session:
                # Build the base query
                query = """
                SELECT 
                    transaction_date,
                    company_name,
                    company_id,
                    total_amount,
                    transaction_count,
                    average_amount,
                    min_amount,
                    max_amount,
                    paid_count,
                    refunded_count,
                    paid_amount,
                    refunded_amount
                FROM normalized_data.daily_transaction_summary
                WHERE 1=1
                """
                
                params = {}
                
                # Add date filters
                if start_date:
                    query += " AND transaction_date >= :start_date"
                    params['start_date'] = start_date
                
                if end_date:
                    query += " AND transaction_date <= :end_date"
                    params['end_date'] = end_date
                
                # Add company filter
                if company_id:
                    query += " AND company_id = :company_id"
                    params['company_id'] = company_id
                
                # Add ordering and limit
                query += " ORDER BY transaction_date DESC, total_amount DESC"
                
                if limit:
                    query += " LIMIT :limit"
                    params['limit'] = limit
                
                result = session.execute(text(query), params)
                
                # Convert results to list of dictionaries
                columns = result.keys()
                rows = result.fetchall()
                
                summary_data = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    # Convert Decimal to float for JSON serialization
                    for key, value in row_dict.items():
                        if isinstance(value, Decimal):
                            row_dict[key] = float(value)
                        elif hasattr(value, 'isoformat'):  # Handle date objects
                            row_dict[key] = value.isoformat()
                    summary_data.append(row_dict)
                
                logger.info(f"Retrieved {len(summary_data)} daily transaction summary records")
                return summary_data
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to query daily transaction summary: {e}")
            return []
    
    def get_company_transaction_totals(self, 
                                     start_date: Optional[str] = None,
                                     end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get total transaction amounts grouped by company.
        
        Args:
            start_date: Start date filter (YYYY-MM-DD format)
            end_date: End date filter (YYYY-MM-DD format)
            
        Returns:
            List of dictionaries containing company transaction totals
        """
        logger.info(f"Getting company transaction totals with date range: {start_date} to {end_date}")
        
        try:
            with self.db_connection.get_session() as session:
                query = """
                SELECT 
                    company_name,
                    company_id,
                    SUM(total_amount) as total_amount,
                    SUM(transaction_count) as total_transactions,
                    AVG(average_amount) as overall_average,
                    SUM(paid_amount) as total_paid_amount,
                    SUM(refunded_amount) as total_refunded_amount,
                    COUNT(DISTINCT transaction_date) as active_days
                FROM normalized_data.daily_transaction_summary
                WHERE 1=1
                """
                
                params = {}
                
                if start_date:
                    query += " AND transaction_date >= :start_date"
                    params['start_date'] = start_date
                
                if end_date:
                    query += " AND transaction_date <= :end_date"
                    params['end_date'] = end_date
                
                query += """
                GROUP BY company_name, company_id
                ORDER BY total_amount DESC
                """
                
                result = session.execute(text(query), params)
                columns = result.keys()
                rows = result.fetchall()
                
                company_totals = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    # Convert Decimal to float for JSON serialization
                    for key, value in row_dict.items():
                        if isinstance(value, Decimal):
                            row_dict[key] = float(value)
                    company_totals.append(row_dict)
                
                logger.info(f"Retrieved transaction totals for {len(company_totals)} companies")
                return company_totals
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get company transaction totals: {e}")
            return []
    
    def get_daily_transaction_trends(self, 
                                   days: int = 30,
                                   company_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get daily transaction trends for the specified number of days.
        
        Args:
            days: Number of days to include in the trend analysis
            company_id: Optional company ID filter
            
        Returns:
            List of dictionaries containing daily transaction trends
        """
        logger.info(f"Getting daily transaction trends for {days} days, company_id={company_id}")
        
        try:
            with self.db_connection.get_session() as session:
                query = """
                SELECT 
                    transaction_date,
                    SUM(total_amount) as daily_total,
                    SUM(transaction_count) as daily_count,
                    AVG(average_amount) as daily_average,
                    COUNT(DISTINCT company_id) as active_companies
                FROM normalized_data.daily_transaction_summary
                WHERE transaction_date >= CURRENT_DATE - INTERVAL '%s days'
                """ % days
                
                params = {}
                
                if company_id:
                    query += " AND company_id = :company_id"
                    params['company_id'] = company_id
                
                query += """
                GROUP BY transaction_date
                ORDER BY transaction_date DESC
                """
                
                result = session.execute(text(query), params)
                columns = result.keys()
                rows = result.fetchall()
                
                trends = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    # Convert Decimal to float and dates to ISO format
                    for key, value in row_dict.items():
                        if isinstance(value, Decimal):
                            row_dict[key] = float(value)
                        elif hasattr(value, 'isoformat'):
                            row_dict[key] = value.isoformat()
                    trends.append(row_dict)
                
                logger.info(f"Retrieved {len(trends)} days of transaction trends")
                return trends
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get daily transaction trends: {e}")
            return []
    
    def create_reporting_indexes(self) -> bool:
        """Create optimized indexes for reporting queries.
        
        Returns:
            True if indexes were created successfully, False otherwise
        """
        logger.info("Creating reporting indexes for query optimization")
        
        indexes = [
            # Composite index for date-based queries
            """
            CREATE INDEX IF NOT EXISTS idx_charges_date_company_status 
            ON normalized_data.charges (created_at, company_id, status)
            """,
            
            # Index for amount-based queries
            """
            CREATE INDEX IF NOT EXISTS idx_charges_amount_status 
            ON normalized_data.charges (amount, status) 
            WHERE status IN ('paid', 'refunded')
            """,
            
            # Partial index for paid and refunded transactions only
            """
            CREATE INDEX IF NOT EXISTS idx_charges_paid_refunded 
            ON normalized_data.charges (created_at, company_id, amount) 
            WHERE status IN ('paid', 'refunded')
            """,
            
            # Index for company-based aggregations
            """
            CREATE INDEX IF NOT EXISTS idx_companies_name_id 
            ON normalized_data.companies (company_name, company_id)
            """
        ]
        
        try:
            with self.db_connection.get_session() as session:
                for index_sql in indexes:
                    session.execute(text(index_sql))
                    
                logger.info("Reporting indexes created successfully")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create reporting indexes: {e}")
            return False
    
    def analyze_view_performance(self) -> Dict[str, Any]:
        """Analyze the performance of the daily transaction summary view.
        
        Returns:
            Dictionary containing performance analysis results
        """
        logger.info("Analyzing daily transaction summary view performance")
        
        try:
            with self.db_connection.get_session() as session:
                # Get execution plan for the view query
                explain_query = """
                EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
                SELECT * FROM normalized_data.daily_transaction_summary
                LIMIT 100
                """
                
                result = session.execute(text(explain_query))
                execution_plan = result.fetchone()[0]
                
                # Get view statistics
                stats_query = """
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT company_id) as unique_companies,
                    COUNT(DISTINCT transaction_date) as unique_dates,
                    MIN(transaction_date) as earliest_date,
                    MAX(transaction_date) as latest_date,
                    SUM(total_amount) as grand_total,
                    AVG(total_amount) as avg_daily_total
                FROM normalized_data.daily_transaction_summary
                """
                
                stats_result = session.execute(text(stats_query))
                stats_row = stats_result.fetchone()
                
                # Get index usage information
                index_usage_query = """
                SELECT 
                    schemaname,
                    relname as tablename,
                    indexrelname as indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'normalized_data'
                AND relname IN ('charges', 'companies')
                ORDER BY idx_scan DESC
                """
                
                index_result = session.execute(text(index_usage_query))
                index_stats = [dict(zip(index_result.keys(), row)) for row in index_result.fetchall()]
                
                performance_analysis = {
                    'execution_plan': execution_plan,
                    'view_statistics': {
                        'total_rows': stats_row[0],
                        'unique_companies': stats_row[1],
                        'unique_dates': stats_row[2],
                        'earliest_date': stats_row[3].isoformat() if stats_row[3] else None,
                        'latest_date': stats_row[4].isoformat() if stats_row[4] else None,
                        'grand_total': float(stats_row[5]) if stats_row[5] else 0,
                        'avg_daily_total': float(stats_row[6]) if stats_row[6] else 0
                    },
                    'index_usage': index_stats,
                    'recommendations': self._generate_performance_recommendations(execution_plan, index_stats)
                }
                
                logger.info("View performance analysis completed")
                return performance_analysis
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to analyze view performance: {e}")
            return {'error': str(e)}
    
    def _generate_performance_recommendations(self, execution_plan: List[Dict], index_stats: List[Dict]) -> List[str]:
        """Generate performance recommendations based on execution plan and index usage.
        
        Args:
            execution_plan: Query execution plan from EXPLAIN
            index_stats: Index usage statistics
            
        Returns:
            List of performance recommendations
        """
        recommendations = []
        
        try:
            # Analyze execution plan for sequential scans
            plan_str = str(execution_plan)
            if 'Seq Scan' in plan_str:
                recommendations.append("Consider adding indexes to avoid sequential scans on large tables")
            
            # Check for unused indexes
            unused_indexes = [idx for idx in index_stats if idx['idx_scan'] == 0]
            if unused_indexes:
                recommendations.append(f"Consider dropping unused indexes: {[idx['indexname'] for idx in unused_indexes]}")
            
            # Check for high-cost operations
            if 'cost=' in plan_str:
                recommendations.append("Monitor query costs and consider query optimization if costs are high")
            
            # General recommendations
            recommendations.extend([
                "Regularly update table statistics with ANALYZE command",
                "Consider partitioning large tables by date for better performance",
                "Monitor view usage patterns and adjust indexes accordingly"
            ])
            
        except Exception as e:
            logger.warning(f"Could not generate detailed recommendations: {e}")
            recommendations.append("Enable detailed performance monitoring for better recommendations")
        
        return recommendations