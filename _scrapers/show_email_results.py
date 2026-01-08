#!/usr/bin/env python3
"""
Email Scraper Results Viewer
Shows the latest email scraping results and provides quick analysis.
"""

import os
import glob
import pandas as pd
from datetime import datetime

def find_latest_results():
    """Find the most recent email scraping results"""
    results_dir = 'results'
    
    if not os.path.exists(results_dir):
        print("❌ No results directory found. Run the email scraper first.")
        return None, None
    
    # Find all email scraping result files
    csv_files = glob.glob(f"{results_dir}/scraped_emails_*.csv")
    summary_files = glob.glob(f"{results_dir}/scraped_emails_*_summary.txt")
    
    if not csv_files:
        print("❌ No email scraping results found.")
        return None, None
    
    # Sort by modification time to get latest
    latest_csv = max(csv_files, key=os.path.getmtime)
    latest_summary = latest_csv.replace('.csv', '_summary.txt')
    
    return latest_csv, latest_summary if os.path.exists(latest_summary) else None

def show_summary(summary_file):
    """Display the summary file content"""
    if summary_file and os.path.exists(summary_file):
        print("📊 SCRAPING SUMMARY")
        print("=" * 50)
        with open(summary_file, 'r', encoding='utf-8') as f:
            print(f.read())
    else:
        print("⚠️  No summary file found")

def analyze_results(csv_file):
    """Provide detailed analysis of results"""
    try:
        df = pd.read_csv(csv_file)
        
        print("\n📈 DETAILED ANALYSIS")
        print("=" * 50)
        print(f"📁 Results file: {csv_file}")
        print(f"📅 File date: {datetime.fromtimestamp(os.path.getmtime(csv_file)).strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Basic statistics
        total = len(df)
        successful = len(df[df['scraping_status'] == 'success'])
        with_priority = len(df[df['priority_emails'] != ''])
        with_general = len(df[df['general_emails'] != ''])
        total_emails = df['total_emails_found'].sum()
        
        print(f"📊 Statistics:")
        print(f"   Total entries processed: {total:,}")
        print(f"   Successfully scraped: {successful:,} ({successful/total*100:.1f}%)")
        print(f"   Entries with priority emails: {with_priority:,}")
        print(f"   Entries with general emails: {with_general:,}")
        print(f"   Total emails found: {total_emails:,}")
        print()
        
        # Status breakdown
        print("📋 Status Breakdown:")
        status_counts = df['scraping_status'].value_counts()
        for status, count in status_counts.items():
            print(f"   {status}: {count:,} ({count/total*100:.1f}%)")
        print()
        
        # Top practices with most emails
        if successful > 0:
            top_practices = df[df['total_emails_found'] > 0].nlargest(5, 'total_emails_found')[['title', 'total_emails_found', 'priority_emails']]
            if len(top_practices) > 0:
                print("🏆 Top Practices (Most Emails Found):")
                for _, row in top_practices.iterrows():
                    priority_text = f" (Priority: {row['priority_emails']})" if row['priority_emails'] else ""
                    print(f"   • {row['title']}: {row['total_emails_found']} emails{priority_text}")
                print()
        
        # Sample of successful entries
        successful_entries = df[df['scraping_status'] == 'success'].head(3)
        if len(successful_entries) > 0:
            print("✅ Sample Successful Entries:")
            for _, row in successful_entries.iterrows():
                print(f"   • {row['title']}")
                print(f"     URL: {row['url']}")
                if row['priority_emails']:
                    print(f"     Priority: {row['priority_emails']}")
                if row['emails']:
                    print(f"     All emails: {row['emails']}")
                print()
    
    except Exception as e:
        print(f"❌ Error analyzing results: {e}")

def list_all_results():
    """List all available result files"""
    results_dir = 'results'
    
    if not os.path.exists(results_dir):
        print("❌ No results directory found.")
        return
    
    csv_files = glob.glob(f"{results_dir}/scraped_emails_*.csv")
    
    if not csv_files:
        print("❌ No email scraping results found.")
        return
    
    print(f"\n📁 ALL EMAIL SCRAPING RESULTS ({len(csv_files)} files)")
    print("=" * 60)
    
    # Sort by modification time (newest first)
    csv_files.sort(key=os.path.getmtime, reverse=True)
    
    for i, file in enumerate(csv_files):
        file_date = datetime.fromtimestamp(os.path.getmtime(file))
        file_size = os.path.getsize(file)
        
        # Try to get basic stats
        try:
            df = pd.read_csv(file)
            total_entries = len(df)
            successful = len(df[df['scraping_status'] == 'success'])
            total_emails = df['total_emails_found'].sum()
            stats = f" - {total_entries} entries, {successful} successful, {total_emails} emails"
        except:
            stats = f" - {file_size} bytes"
        
        marker = "📌 [LATEST]" if i == 0 else "  "
        print(f"{marker} {os.path.basename(file)}")
        print(f"     Date: {file_date.strftime('%Y-%m-%d %H:%M:%S')}{stats}")
        print()

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        list_all_results()
        return
    
    print("🔍 Email Scraper Results Viewer")
    print("=" * 40)
    
    latest_csv, latest_summary = find_latest_results()
    
    if not latest_csv:
        return
    
    # Show summary if available
    show_summary(latest_summary)
    
    # Show detailed analysis
    analyze_results(latest_csv)
    
    print("\n💡 Usage:")
    print("   python show_email_results.py --list  # Show all result files")
    print(f"   head -10 {latest_csv}  # View raw data")
    print(f"   cp {latest_csv} ../web/scraped_emails_latest.csv  # Copy to web directory")

if __name__ == "__main__":
    main()