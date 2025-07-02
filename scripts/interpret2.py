import pandas as pd
import sys
from typing import List, Dict, Set

def analyze_flaky_tests(csv_file_path: str) -> pd.DataFrame:
    """
    Analyzes a CSV file containing test results to identify flaky tests.
    
    A flaky test is defined as a test that fails on some operating systems
    but not on others (i.e., appears in some environments but not all).
    
    Args:
        csv_file_path (str): Path to the CSV file containing test results
        
    Returns:
        pd.DataFrame: DataFrame containing flaky tests with their environment details
    """
    
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Strip whitespace from headers (common CSV issue)
        df.columns = df.columns.str.strip()
        
        print(f"Loaded {len(df)} test failure records from {csv_file_path}")
        print(f"Columns found: {list(df.columns)}")
        print(f"Unique environments: {sorted(df['environment'].unique())}")
        print(f"Unique projects: {len(df['project'].unique())}")
        print()
        
    except FileNotFoundError:
        print(f"Error: File '{csv_file_path}' not found.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return pd.DataFrame()
    
    # Create a unique identifier for each test (project + test_name)
    df['test_id'] = df['project'] + '::' + df['test_name']
    
    # Get all unique environments and test IDs
    all_environments = set(df['environment'].unique())
    all_test_ids = set(df['test_id'].unique())
    
    print(f"Total unique tests analyzed: {len(all_test_ids)}")
    print(f"Environments found: {all_environments}")
    print()
    
    # Group by test_id to see which environments each test fails in
    test_environments = df.groupby('test_id')['environment'].apply(set).reset_index()
    test_environments.columns = ['test_id', 'failing_environments']
    
    # Identify flaky tests: tests that don't fail in ALL environments
    # Since the CSV only contains failing tests, a flaky test is one that 
    # appears in some environments but not others
    flaky_tests = []
    
    for _, row in test_environments.iterrows():
        test_id = row['test_id']
        failing_envs = row['failing_environments']
        
        # If the test doesn't fail in ALL environments, it's flaky
        if failing_envs != all_environments:
            missing_envs = all_environments - failing_envs
            
            flaky_tests.append({
                'test_id': test_id,
                'failing_environments': sorted(list(failing_envs)),
                'passing_environments': sorted(list(missing_envs)),
                'num_failing_envs': len(failing_envs),
                'num_passing_envs': len(missing_envs)
            })
    
    if not flaky_tests:
        print("No flaky tests found. All tests either:")
        print("- Fail consistently across all environments, or")
        print("- Only one environment was tested")
        return pd.DataFrame()
    
    # Convert to DataFrame for better presentation
    flaky_df = pd.DataFrame(flaky_tests)
    
    # Add original test details
    test_details = df[['test_id', 'project', 'test_name', 'outcome']].drop_duplicates()
    flaky_result = flaky_df.merge(test_details, on='test_id', how='left')
    
    # Reorder columns for better readability
    column_order = ['project', 'test_name', 'outcome', 'failing_environments', 
                   'passing_environments', 'num_failing_envs', 'num_passing_envs']
    flaky_result = flaky_result[column_order]
    
    return flaky_result

def print_flaky_analysis(flaky_tests: pd.DataFrame) -> None:
    """
    Prints a detailed analysis of flaky tests.
    
    Args:
        flaky_tests (pd.DataFrame): DataFrame containing flaky test results
    """
    
    if flaky_tests.empty:
        print("No flaky tests detected.")
        return
    
    print("=" * 80)
    print("FLAKY TESTS ANALYSIS")
    print("=" * 80)
    print()
    
    print(f"Found {len(flaky_tests)} flaky tests")
    print()
    
    # Group by project for better organization
    for project in sorted(flaky_tests['project'].unique()):
        project_tests = flaky_tests[flaky_tests['project'] == project]
        
        print(f"PROJECT: {project}")
        print("-" * (len(project) + 9))
        
        for _, test in project_tests.iterrows():
            print(f"  Test: {test['test_name']}")
            print(f"  Outcome: {test['outcome']}")
            print(f"  Fails in: {', '.join(test['failing_environments'])}")
            print(f"  Passes in: {', '.join(test['passing_environments'])}")
            print()
    
    # Summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    env_stats = flaky_tests.groupby('num_failing_envs').size()
    print("Distribution of flaky tests by number of failing environments:")
    for num_envs, count in env_stats.items():
        print(f"  Tests failing in {num_envs} environment(s): {count}")
    
    outcome_stats = flaky_tests['outcome'].value_counts()
    print(f"\nDistribution by outcome type:")
    for outcome, count in outcome_stats.items():
        print(f"  {outcome}: {count}")

def save_flaky_tests(flaky_tests: pd.DataFrame, output_file: str = "flaky_tests_report.csv") -> None:
    """
    Saves flaky tests to a CSV file.
    
    Args:
        flaky_tests (pd.DataFrame): DataFrame containing flaky test results
        output_file (str): Output file path
    """
    
    if not flaky_tests.empty:
        flaky_tests.to_csv(output_file, index=False)
        print(f"\nFlaky tests report saved to: {output_file}")

def main():
    """
    Main function to run the flaky test analysis.
    """
    
    # You can modify this path to point to your CSV file
    csv_file_path = "final.csv"
    
    # If a command line argument is provided, use it as the file path
    if len(sys.argv) > 1:
        csv_file_path = sys.argv[1]
    
    print("Flaky Test Analyzer")
    print("=" * 50)
    print(f"Analyzing file: {csv_file_path}")
    print()
    
    # Analyze flaky tests
    flaky_tests = analyze_flaky_tests(csv_file_path)
    
    # Print detailed analysis
    print_flaky_analysis(flaky_tests)
    
    # Save results to file
    save_flaky_tests(flaky_tests)

if __name__ == "__main__":
    main()