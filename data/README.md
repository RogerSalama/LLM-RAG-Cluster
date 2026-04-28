# Skills Library

This folder contains **24 modular AI agent skills**. Each skill is a self-contained folder with a `SKILL.md` file that uses **Progressive Disclosure** — only the YAML frontmatter (name + description) is loaded initially; the full instructions are read only when the skill is activated.

## Available Skills

| Skill | Description |
|-------|-------------|
| [analytics-metrics](analytics-metrics/SKILL.md) | Build data visualization and analytics dashboards |
| [aws-account-management](aws-account-management/SKILL.md) | Manage AWS accounts, organizations, IAM, and billing |
| [aws-agentcore](aws-agentcore/SKILL.md) | Build AI agents with AWS Bedrock AgentCore |
| [aws-strands](aws-strands/SKILL.md) | Build AI agents with Strands Agents SDK |
| [bun](bun/SKILL.md) | Build fast applications with Bun JavaScript runtime |
| [cloudflare](cloudflare/SKILL.md) | Build and deploy on Cloudflare's edge platform |
| [copilot-docs](copilot-docs/SKILL.md) | Configure GitHub Copilot with custom instructions |
| [copilot-sdk](copilot-sdk/SKILL.md) | Build agentic applications with GitHub Copilot SDK |
| [fal-ai](fal-ai/SKILL.md) | Generate images, videos, and audio with fal |
| [figma](figma/SKILL.md) | Integrate with Figma API for design automation and code generation |
| [github-trending](github-trending/SKILL.md) | Fetch and display GitHub trending repositories and developers |
| [google-workspace-cli](google-workspace-cli/SKILL.md) | Interact with all Google Workspace APIs via the gws CLI |
| [honest-agent](honest-agent/SKILL.md) | Configure AI coding agents to be honest, objective, and non-sycophantic |
| [langchain](langchain/SKILL.md) | Build LLM applications with LangChain and LangGraph |
| [local-llm-router](local-llm-router/SKILL.md) | Route AI coding queries to local LLMs in air-gapped networks |
| [mermaid-diagrams](mermaid-diagrams/SKILL.md) | Create diagrams and visualizations using Mermaid syntax |
| [mobile-responsiveness](mobile-responsiveness/SKILL.md) | Build responsive, mobile-first web applications |
| [mongodb](mongodb/SKILL.md) | Work with MongoDB databases using best practices |
| [nano-banana-pro](nano-banana-pro/SKILL.md) | Generate images with Google's Nano Banana Pro (Gemini 3 Pro Image) |
| [owasp-security](owasp-security/SKILL.md) | Implement secure coding practices following OWASP Top 10 |
| [railway](railway/SKILL.md) | Deploy applications on Railway platform |
| [ux-design-systems](ux-design-systems/SKILL.md) | Build consistent design systems with tokens, components, and theming |
| [vercel](vercel/SKILL.md) | Deploy and configure applications on Vercel |
| [web-accessibility](web-accessibility/SKILL.md) | Build accessible web applications following WCAG guidelines |

## Adding a New Skill

1. Copy `../templates/skill-template/` into this folder
2. Rename the folder to your skill name (lowercase, hyphenated)
3. Edit the `SKILL.md`:
   - Set `name` and `description` in the YAML frontmatter
   - Include trigger keywords in the description so agents know when to activate it
   - Fill in Quick Start, Core Patterns, Common Use Cases, and Resources sections
4. Optional: add a `references/` subfolder for supplementary docs

## Folder Rules

- **One skill = one folder** with a `SKILL.md` at its root
- **Frontmatter is mandatory** — both `name` and `description` fields
- **Description must include trigger keywords** — these are how agents decide to load the skill
- **Keep skills self-contained** — don't reference other skills' internal files
