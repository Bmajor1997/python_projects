export type IssueDraft = { title: string; body: string; labels?: string[]; assignees?: string[]; fingerprint: string };
export type PublishResult = { url: string; number: number; existing: boolean };
export interface IssuePublisher { publish(draft: IssueDraft, dryRun?: boolean): Promise<PublishResult | null>; }

export class GitHubIssuePublisher implements IssuePublisher {
  constructor(private readonly owner: string, private readonly repo: string, private readonly token: string) {}
  private async request(path: string, init?: RequestInit): Promise<Response> {
    const response = await fetch(`https://api.github.com/repos/${this.owner}/${this.repo}${path}`, { ...init, headers: { Accept: "application/vnd.github+json", Authorization: `Bearer ${this.token}`, "X-GitHub-Api-Version": "2022-11-28", ...init?.headers } });
    if (!response.ok) throw new Error(`GitHub issue publishing failed (${response.status})`); return response;
  }
  async publish(draft: IssueDraft, dryRun = false): Promise<PublishResult | null> {
    if (dryRun) return null;
    const marker = `<!-- bug-report-fingerprint:${draft.fingerprint} -->`;
    const query = encodeURIComponent(`${draft.fingerprint} in:body repo:${this.owner}/${this.repo} is:issue`);
    const search = await fetch(`https://api.github.com/search/issues?q=${query}`, { headers: { Authorization: `Bearer ${this.token}`, Accept: "application/vnd.github+json" } });
    if (search.ok) { const json = await search.json() as { items?: Array<{ html_url: string; number: number }> }; const match = json.items?.[0]; if (match) return { url: match.html_url, number: match.number, existing: true }; }
    const response = await this.request("/issues", { method: "POST", body: JSON.stringify({ title: draft.title, body: `${draft.body}\n\n${marker}`, labels: draft.labels, assignees: draft.assignees }) });
    const issue = await response.json() as { html_url: string; number: number }; return { url: issue.html_url, number: issue.number, existing: false };
  }
}
