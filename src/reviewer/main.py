import fnmatch
import json
import os
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from github import (
    Github,
    GithubException,
)
from pydantic import (
    BaseModel,
    Field,
)
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from unidiff import PatchSet

# Read environment variables
github_token = (
    os.environ.get("INPUT_GITHUB_TOKEN") or
    os.environ.get("INPUT_GITHUB-TOKEN") or
    os.environ.get("GITHUB_TOKEN")
)
api_key = (
    os.environ.get("INPUT_API_KEY") or
    os.environ.get("INPUT_API-KEY") or
    os.environ.get("API_KEY")
)
base_url = os.environ.get("INPUT_BASE_URL") or os.environ.get("INPUT_BASE-URL")
model_name = os.environ.get("INPUT_MODEL", "gpt-4o")
language = os.environ.get("INPUT_LANGUAGE", "en")
repo_full_name = os.environ.get("GITHUB_REPOSITORY")
event_path = os.environ.get("GITHUB_EVENT_PATH")
event_name = os.environ.get("GITHUB_EVENT_NAME")


class PRDetails(BaseModel):
    """Pull Request details"""
    owner: str
    repo: str
    pull_number: int
    title: str
    description: Optional[str]


class HunkContext(BaseModel):
    """Context for a single diff hunk"""
    file_path: str
    hunk_content: str
    start_position: int  # GitHub API position where this hunk starts


class ReviewItem(BaseModel):
    """Individual review comment"""
    line_number: int = Field(
        ...,
        description="Line number relative to the hunk content (1-based)",
        ge=1
    )
    review_comment: str = Field(
        ...,
        description="GitHub Markdown formatted review comment"
    )
    severity: str = Field(
        default="suggestion",
        description="Issue severity: critical, warning, suggestion"
    )


class ReviewResult(BaseModel):
    """AI review result"""
    summary: str = Field(
        default="",
        description="Brief summary of the PR changes"
    )
    reviews: List[ReviewItem] = Field(
        default_factory=list,
        description="List of review comments. Empty if no issues found."
    )


def build_ai_agent(api_key: str, base_url: Optional[str], model_name: str) -> Agent[ReviewResult]:
    """Build pydantic-ai agent for code review"""
    provider = OpenAIProvider(api_key=api_key, base_url=base_url)
    model = OpenAIModel(model_name, provider=provider)
    return Agent(model, output_type=ReviewResult)


def load_event(path: str) -> Dict[str, Any]:
    """Load GitHub event data from file"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_pr_details(gh: Github, repo_full_name: str, event: Dict[str, Any]) -> PRDetails:
    """Extract PR details from GitHub event"""
    repo = gh.get_repo(repo_full_name)

    # Support both pull_request events and issue_comment events on PRs
    if "pull_request" in event:
        pr_number = event.get("number") or event["pull_request"]["number"]
    elif event.get("issue", {}).get("pull_request"):
        pr_number = event["issue"]["number"]
    else:
        raise RuntimeError("This event is not for a pull request.")

    pr = repo.get_pull(pr_number)
    owner, repo_name = repo_full_name.split("/")

    return PRDetails(
        owner=owner,
        repo=repo_name,
        pull_number=pr_number,
        title=pr.title,
        description=pr.body
    )


def get_pr_diff(gh: Github, pr_details: PRDetails) -> str:
    """Fetch PR diff using GitHub API"""
    import requests

    api_url = f"https://api.github.com/repos/{pr_details.owner}/{pr_details.repo}/pulls/{pr_details.pull_number}"
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3.diff'
    }

    response = requests.get(f"{api_url}.diff", headers=headers)

    if response.status_code == 200:
        return response.text
    else:
        raise RuntimeError(f"Failed to get diff. Status: {response.status_code}, Response: {response.text}")


def parse_diff_with_positions(diff_text: str) -> List[HunkContext]:
    """Parse diff using unidiff and calculate GitHub positions"""
    hunks_with_context = []

    try:
        patch_set = PatchSet(diff_text)
    except Exception as e:
        print(f"Error parsing diff with unidiff: {e}")
        # Fallback to manual parsing if unidiff fails
        return parse_diff_manual(diff_text)

    for patched_file in patch_set:
        if patched_file.path == "/dev/null" or not patched_file.path:
            continue

        # Track position in the entire file's diff
        position = 1

        for hunk in patched_file:
            # Skip the @@ header line
            hunk_start_position = position + 1

            # Build hunk content
            hunk_lines = []
            for line in hunk:
                hunk_lines.append(f"{line.line_type}{line.value}")

            if hunk_lines:
                hunks_with_context.append(
                    HunkContext(
                        file_path=patched_file.path,
                        hunk_content="\n".join(hunk_lines),
                        start_position=hunk_start_position
                    ))

            # Update position: header + content lines
            position += 1 + len(hunk_lines)

    return hunks_with_context


def parse_diff_manual(diff_text: str) -> List[HunkContext]:
    """Manual diff parsing as fallback"""
    hunks_with_context = []
    lines = diff_text.splitlines()
    current_file = None
    position = 1
    i = 0

    while i < len(lines):
        line = lines[i]

        # New file
        if line.startswith('diff --git'):
            current_file = None
            position = 1
        elif line.startswith('+++ b/'):
            current_file = line[6:]
        elif line.startswith('@@') and current_file:
            # Found hunk header
            hunk_start_position = position + 1
            hunk_lines = []
            i += 1
            position += 1

            # Collect hunk content
            while i < len(lines) and not lines[i].startswith('@@') and not lines[i].startswith('diff --git'):
                hunk_lines.append(lines[i])
                i += 1
                position += 1

            if hunk_lines:
                hunks_with_context.append(
                    HunkContext(
                        file_path=current_file,
                        hunk_content="\n".join(hunk_lines),
                        start_position=hunk_start_position
                    ))
            continue

        i += 1
        if current_file:  # Only increment position when we're in a file
            position += 1

    return hunks_with_context


def build_prompt(pr_details: PRDetails, hunk_context: HunkContext, language: str) -> str:
    """Build review prompt using template from prompts.py"""
    from .prompts import (
        reviewer_prompt,
        user_inputs_template,
    )

    # Format the prompt with context
    prompt = reviewer_prompt + user_inputs_template.format(
        pr_title=pr_details.title,
        pr_body=pr_details.description or "No description provided",
        git_diff=hunk_context.hunk_content
    )

    # Add language instruction
    prompt += f"\n\n# OUTPUT FORMAT\n"
    prompt += f"Return your analysis as a structured JSON matching the ReviewResult schema.\n"
    prompt += f"Always respond in {language} language for the review comments.\n"
    prompt += f"File being reviewed: {hunk_context.file_path}\n"

    return prompt


def should_exclude_file(file_path: str, exclude_patterns: List[str]) -> bool:
    """Check if file should be excluded based on patterns"""
    return any(fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns)


def filter_hunks_by_file(hunks: List[HunkContext], exclude_patterns: List[str]) -> List[HunkContext]:
    """Filter out hunks from excluded files"""
    filtered = []
    excluded_files = set()

    for hunk in hunks:
        if should_exclude_file(hunk.file_path, exclude_patterns):
            excluded_files.add(hunk.file_path)
        else:
            filtered.append(hunk)

    for file in excluded_files:
        print(f"Excluded file: {file}")

    return filtered


def analyze_hunks(
    agent: Agent[ReviewResult],
    hunks: List[HunkContext],
    pr_details: PRDetails,
    language: str
) -> List[Dict[str, Any]]:
    """Analyze code hunks and generate review comments"""
    review_comments = []

    for hunk in hunks:
        prompt = build_prompt(pr_details, hunk, language)

        try:
            print(f"Analyzing {hunk.file_path} (position {hunk.start_position})...")
            result = agent.run_sync(prompt)
            review_result: ReviewResult = result.output

            # Log summary if provided
            if review_result.summary:
                print(f"Summary: {review_result.summary}")

            # Process review items
            for item in review_result.reviews:
                # Calculate actual GitHub position
                hunk_lines = hunk.hunk_content.splitlines()

                if item.line_number < 1 or item.line_number > len(hunk_lines):
                    print(f"Warning: line_number {item.line_number} out of range for hunk with {len(hunk_lines)} lines")
                    continue

                position = hunk.start_position + (item.line_number - 1)

                review_comments.append(
                    {
                        "path": hunk.file_path,
                        "position": position,
                        "body": f"**[{item.severity.upper()}]** {item.review_comment}"
                    })

        except Exception as e:
            print(f"Error analyzing {hunk.file_path}: {e}")
            continue

    return review_comments


def submit_review(
    gh: Github,
    pr_details: PRDetails,
    comments: List[Dict[str, Any]]
) -> bool:
    """Submit review comments to GitHub"""
    if not comments:
        print("No review comments to submit.")
        return True

    try:
        repo = gh.get_repo(f"{pr_details.owner}/{pr_details.repo}")
        pr = repo.get_pull(pr_details.pull_number)

        # Group comments by severity for summary
        severity_counts = {"critical": 0, "warning": 0, "suggestion": 0}
        for comment in comments:
            body = comment.get("body", "")
            for severity in severity_counts:
                if f"[{severity.upper()}]" in body:
                    severity_counts[severity] += 1
                    break

        # Build review summary
        summary_parts = []
        if severity_counts["critical"] > 0:
            summary_parts.append(f"🚨 {severity_counts['critical']} critical issue(s)")
        if severity_counts["warning"] > 0:
            summary_parts.append(f"⚠️ {severity_counts['warning']} warning(s)")
        if severity_counts["suggestion"] > 0:
            summary_parts.append(f"💡 {severity_counts['suggestion']} suggestion(s)")

        review_body = f"## AI Code Review\n\n"
        if summary_parts:
            review_body += "Found: " + ", ".join(summary_parts) + "\n\n"
        review_body += f"Reviewed {len(set(c['path'] for c in comments))} file(s) with {len(comments)} comment(s)."

        # Submit review
        pr.create_review(
            body=review_body,
            comments=comments,
            event="COMMENT"
        )

        print(f"✅ Submitted review with {len(comments)} comment(s)")
        return True

    except GithubException as e:
        print(f"❌ Failed to submit review: {e}")

        # Fallback: post as issue comment
        try:
            repo = gh.get_repo(f"{pr_details.owner}/{pr_details.repo}")
            pr = repo.get_pull(pr_details.pull_number)

            fallback_body = "## AI Code Review (Fallback)\n\n"
            fallback_body += "Unable to create inline comments. Summary:\n\n"

            # Group by file
            by_file = {}
            for comment in comments:
                by_file.setdefault(comment['path'], []).append(comment)

            for file_path, file_comments in by_file.items():
                fallback_body += f"### `{file_path}`\n"
                for comment in file_comments:
                    fallback_body += f"- Line ~{comment['position']}: {comment['body']}\n"
                fallback_body += "\n"

            pr.create_issue_comment(fallback_body)
            print("✅ Posted fallback comment")
            return True

        except Exception as e2:
            print(f"❌ Fallback also failed: {e2}")
            return False


def main():
    """Main entry point for the reviewer"""
    # Validate required inputs
    if not github_token:
        print("❌ Missing GitHub token (GITHUB_TOKEN)")
        return 1
    if not api_key:
        print("❌ Missing AI API key (INPUT_API_KEY)")
        return 1
    if not repo_full_name or not event_path:
        print("❌ Missing GitHub context")
        return 1

    # Parse exclude patterns
    exclude_raw = os.environ.get("INPUT_EXCLUDE", "").strip()
    exclude_patterns = [p.strip() for p in exclude_raw.split(",") if p.strip()] if exclude_raw else []

    print(f"🚀 AI Code Reviewer starting...")
    print(f"📦 Repository: {repo_full_name}")
    print(f"🤖 Model: {model_name}")
    print(f"🌍 Language: {language}")
    if exclude_patterns:
        print(f"🚫 Exclude patterns: {exclude_patterns}")

    try:
        # Initialize GitHub client
        gh = Github(github_token)

        # Load event and get PR details
        event = load_event(event_path)
        pr_details = get_pr_details(gh, repo_full_name, event)

        print(f"🔍 Reviewing PR #{pr_details.pull_number}: {pr_details.title}")

        # Get diff
        diff_text = get_pr_diff(gh, pr_details)
        if not diff_text:
            print("⚠️ No diff found")
            return 0

        # Parse diff into hunks
        all_hunks = parse_diff_with_positions(diff_text)
        print(f"📄 Found {len(all_hunks)} hunk(s) to review")

        # Filter excluded files
        hunks_to_review = filter_hunks_by_file(all_hunks, exclude_patterns)
        print(f"📝 Reviewing {len(hunks_to_review)} hunk(s) after filtering")

        if not hunks_to_review:
            print("✅ No hunks to review after filtering")
            return 0

        # Build AI agent
        agent = build_ai_agent(api_key, base_url, model_name)

        # Analyze code
        comments = analyze_hunks(agent, hunks_to_review, pr_details, language)

        # Submit review
        if submit_review(gh, pr_details, comments):
            return 0
        else:
            return 1

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
