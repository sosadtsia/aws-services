import boto3, pytz, time, csv
from datetime import datetime, timedelta, timezone

# Create a session by assuming the role in the named profile
session = boto3.Session(profile_name='admin')
# Use the session to access resources via the role
code_commit = session.client('codecommit')

# Function to parse the custom date format
def parse_custom_date(date_str):
    # Split the timestamp and timezone offset
    timestamp_str, offset_str = date_str.split()
    # Convert the timestamp to an integer
    timestamp = int(timestamp_str)
    # Convert the timestamp to a datetime object
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    # Apply the timezone offset
    offset_hours = int(offset_str[:3])
    offset_minutes = int(offset_str[0] + offset_str[3:])  # Handle negative offsets
    offset = timedelta(hours=offset_hours, minutes=offset_minutes)
    dt = dt - offset
    return dt

# Function to sanitize commit messages
def sanitize_commit_message(message):
    # Replace newlines and carriage returns with spaces
    sanitized_message = message.replace('\n', ' ').replace('\r', ' ')
    # Replace multiple spaces with a single space
    sanitized_message = ' '.join(sanitized_message.split())
    # Shorten the message if it exceeds 100 characters
    if len(sanitized_message) > 100:
        sanitized_message = sanitized_message[:100] + '...'
    return sanitized_message

# Function to get commits from a repository within the past 2 years
def get_commits_for_past_years(repository_name, past_years=2, max_commits=1000, timeout=300):
    commits = []
    # Calculate the date 2 years ago from today
    two_years_ago = datetime.now(tz=timezone.utc) - timedelta(days=365 * past_years)

    # Get the default branch (usually 'main' or 'master')
    response = code_commit.get_repository(repositoryName=repository_name)
    default_branch = response['repositoryMetadata']['defaultBranch']

    # Get the latest commit ID from the default branch
    branch_info = code_commit.get_branch(repositoryName=repository_name, branchName=default_branch)
    commit_id = branch_info['branch']['commitId']

    commit_count = 0
    start_time = time.time()

    while commit_id and commit_count < max_commits:
        # Check if the timeout has been reached
        if time.time() - start_time > timeout:
            print(f"Timeout reached for repository: {repository_name}")
            break

        try:
            commit_response = code_commit.get_commit(repositoryName=repository_name, commitId=commit_id)
        except Exception as e:
            print(f"Error getting commit {commit_id} for repository {repository_name}: {e}")
            break

        commit = commit_response['commit']
        commit_date = parse_custom_date(commit['author']['date'])

        if commit_date >= two_years_ago:
            commits.append(commit)
            commit_count += 1

            # Extract required information
            short_commit_id = commit_id[:7]  # Shorten the commit ID
            author = commit['author']['name']
            date_str = commit_date.strftime('%Y-%m-%d')
            time_str = commit_date.strftime('%H:%M')
            message = sanitize_commit_message(commit['message'])

            # Print the formatted commit information
            print(f"{short_commit_id}, {author}, {message}, {date_str}, {time_str}")
        else:
            # Since commits are returned in reverse chronological order, we can break early
            break

        # Move to the parent commit
        if commit['parents']:
            commit_id = commit['parents'][0]
        else:
            break

    return commits

# List of repository names
repository_names = [
    # 'live-aws-percipio-environments'
    'live-aws-iac-admin-environments'
]

# Open a CSV file for writing
with open('codecommit_commits.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    # Write the header row
    writer.writerow(['Short Commit ID', 'Author', 'Message', 'Date', 'Time'])

    for repository_name in repository_names:
        print(f"Commits for repository: {repository_name}")
        commits = get_commits_for_past_years(repository_name)

        # Write commit information to the CSV file
        for commit in commits:
            commit_id = commit['commitId']
            author = commit['author']['name']
            commit_date = parse_custom_date(commit['author']['date'])
            date_str = commit_date.strftime('%Y-%m-%d')
            time_str = commit_date.strftime('%H:%M')
            message = sanitize_commit_message(commit['message'])

            # Write the formatted commit information to the CSV file
            writer.writerow([commit_id[:7], author, message, date_str, time_str])
        print('=' * 80)

print("Script execution completed and CSV file has been written.")
