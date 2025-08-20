#!/usr/bin/env python3
"""
Demo script for reporting views and SQL queries functionality.

This script demonstrates the reporting capabilities of the database manager,
including daily transaction summaries, company totals, and performance analysis.
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.connection import DatabaseConnection
from src.database.manager import DatabaseManager
from src.config import db_config


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_json(data, title: str = None):
    """Print data as formatted JSON."""
    if title:
        print(f"\n{title}:")
    print(json.dumps(data, indent=2, default=str))


def demo_reporting_views():
    """Demonstrate reporting views and SQL queries functionality."""
    print("🔍 Database Reporting Views Demo")
    print("This demo showcases the reporting capabilities of the database manager.")
    
    try:
        # Initialize database connection
        db_connection = DatabaseConnection()
        
        # Test connection
        if not db_connection.test_connection():
            print("❌ Database connection failed!")
            return False
        
        print("✅ Database connection successful!")
        
        # Initialize database manager
        manager = DatabaseManager(db_connection)
        
        # 1. Create/Update reporting view
        print_section("1. Creating Enhanced Reporting View")
        if manager.create_reporting_view():
            print("✅ Daily transaction summary view created successfully!")
        else:
            print("❌ Failed to create reporting view")
            return False
        
        # 2. Create reporting indexes for optimization
        print_section("2. Creating Reporting Indexes")
        if manager.create_reporting_indexes():
            print("✅ Reporting indexes created successfully!")
        else:
            print("⚠️  Warning: Some indexes may already exist or creation failed")
        
        # 3. Query daily transaction summary
        print_section("3. Daily Transaction Summary")
        
        # Query without filters
        print("\n📊 All Daily Transaction Summaries (Last 10 records):")
        daily_summaries = manager.query_daily_transaction_summary(limit=10)
        if daily_summaries:
            print_json(daily_summaries[:3], "Sample Records")  # Show first 3 for brevity
            print(f"Total records retrieved: {len(daily_summaries)}")
        else:
            print("No daily transaction summaries found.")
        
        # Query with date filter
        print("\n📊 Recent Daily Transaction Summaries (Last 7 days):")
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        recent_summaries = manager.query_daily_transaction_summary(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            limit=5
        )
        if recent_summaries:
            print_json(recent_summaries, "Recent Summaries")
        else:
            print("No recent transaction summaries found.")
        
        # 4. Company transaction totals
        print_section("4. Company Transaction Totals")
        company_totals = manager.get_company_transaction_totals()
        if company_totals:
            print_json(company_totals, "Company Totals")
        else:
            print("No company transaction totals found.")
        
        # 5. Daily transaction trends
        print_section("5. Daily Transaction Trends")
        trends = manager.get_daily_transaction_trends(days=30)
        if trends:
            print_json(trends[:5], "Transaction Trends (Last 30 days - Sample)")
            print(f"Total trend records: {len(trends)}")
        else:
            print("No transaction trends found.")
        
        # 6. Performance analysis
        print_section("6. View Performance Analysis")
        performance = manager.analyze_view_performance()
        if 'error' not in performance:
            print("✅ Performance analysis completed!")
            
            # Show view statistics
            if 'view_statistics' in performance:
                print_json(performance['view_statistics'], "View Statistics")
            
            # Show recommendations
            if 'recommendations' in performance:
                print("\n🔧 Performance Recommendations:")
                for i, rec in enumerate(performance['recommendations'], 1):
                    print(f"  {i}. {rec}")
            
            # Show index usage (if available)
            if 'index_usage' in performance and performance['index_usage']:
                print_json(performance['index_usage'][:3], "Index Usage (Sample)")
        else:
            print(f"⚠️  Performance analysis failed: {performance['error']}")
        
        # 7. Database information
        print_section("7. Database Information")
        db_info = manager.get_database_info()
        print_json(db_info, "Database Information")
        
        # 8. Data distribution statistics
        print_section("8. Data Distribution Statistics")
        dist_stats = manager.get_data_distribution_statistics()
        if 'error' not in dist_stats:
            print_json(dist_stats, "Distribution Statistics")
        else:
            print(f"⚠️  Could not retrieve distribution statistics: {dist_stats['error']}")
        
        print_section("Demo Completed Successfully!")
        print("✅ All reporting functionality demonstrated successfully!")
        print("\n📝 Summary of demonstrated features:")
        print("  • Enhanced daily transaction summary view")
        print("  • Optimized reporting indexes")
        print("  • Flexible query filtering (date, company, limit)")
        print("  • Company transaction totals and aggregations")
        print("  • Daily transaction trends analysis")
        print("  • Performance analysis and recommendations")
        print("  • Database statistics and monitoring")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up connection
        try:
            db_connection.close()
            print("\n🔌 Database connection closed.")
        except:
            pass


def demo_specific_queries():
    """Demonstrate specific SQL queries for business requirements."""
    print_section("Specific Business Query Examples")
    
    try:
        db_connection = DatabaseConnection()
        
        manager = DatabaseManager(db_connection)
        
        # Example 1: Top performing companies by total amount
        print("\n💰 Top Performing Companies:")
        company_totals = manager.get_company_transaction_totals()
        if company_totals:
            top_companies = sorted(company_totals, key=lambda x: x['total_amount'], reverse=True)[:3]
            for i, company in enumerate(top_companies, 1):
                print(f"  {i}. {company['company_name']}: ${company['total_amount']:,.2f} "
                      f"({company['total_transactions']} transactions)")
        
        # Example 2: Recent activity analysis
        print("\n📈 Recent Activity Analysis (Last 7 days):")
        recent_trends = manager.get_daily_transaction_trends(days=7)
        if recent_trends:
            total_recent = sum(day['daily_total'] for day in recent_trends)
            avg_daily = total_recent / len(recent_trends) if recent_trends else 0
            print(f"  • Total volume: ${total_recent:,.2f}")
            print(f"  • Average daily volume: ${avg_daily:,.2f}")
            print(f"  • Active days: {len(recent_trends)}")
        
        # Example 3: Company-specific analysis
        if company_totals:
            sample_company_id = company_totals[0]['company_id']
            print(f"\n🏢 Company-Specific Analysis ({company_totals[0]['company_name']}):")
            
            company_trends = manager.get_daily_transaction_trends(days=30, company_id=sample_company_id)
            if company_trends:
                company_total = sum(day['daily_total'] for day in company_trends)
                print(f"  • 30-day total: ${company_total:,.2f}")
                print(f"  • Active days: {len(company_trends)}")
            
            company_daily = manager.query_daily_transaction_summary(
                company_id=sample_company_id,
                limit=5
            )
            if company_daily:
                print(f"  • Recent daily summaries: {len(company_daily)} records")
        
        db_connection.close()
        
    except Exception as e:
        print(f"❌ Specific queries demo failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Database Reporting Views Demo\n")
    
    # Run main demo
    success = demo_reporting_views()
    
    if success:
        # Run specific queries demo
        demo_specific_queries()
        
        print("\n🎉 All demos completed successfully!")
        print("\nNext steps:")
        print("  • Review the generated reports and statistics")
        print("  • Monitor query performance using the analysis tools")
        print("  • Customize queries based on specific business needs")
        print("  • Set up regular reporting schedules")
    else:
        print("\n❌ Demo failed. Please check the error messages above.")
        sys.exit(1)