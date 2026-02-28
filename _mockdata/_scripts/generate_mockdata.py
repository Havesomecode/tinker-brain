#!/usr/bin/env python3
from __future__ import annotations

import json
import random
import re
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Iterable

random.seed(42)


@dataclass
class NoteSpec:
    title: str
    rel_path: str
    note_type: str
    status: str
    tags: list[str]
    aliases: list[str]
    created: datetime
    summary: str
    sections: list[str]
    links: list[str]


def deterministic_uuid4() -> str:
    return str(uuid.UUID(int=random.getrandbits(128), version=4))


def iso_local(dt: datetime) -> str:
    return dt.replace(microsecond=0).astimezone().isoformat()


def random_dt_for_day(day: date, hour_start: int = 8, hour_end: int = 19) -> datetime:
    hour = random.randint(hour_start, hour_end)
    minute = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
    return datetime.combine(day, time(hour=hour, minute=minute)).astimezone()


def yaml_list(values: Iterable[str]) -> str:
    escaped = [v.replace('"', '\\"') for v in values]
    return "[" + ", ".join(f'\"{v}\"' for v in escaped) + "]"


def format_note(spec: NoteSpec, note_id: str, updated: datetime) -> str:
    frontmatter = [
        "---",
        f"id: {note_id}",
        f"created: {iso_local(spec.created)}",
        f"updated: {iso_local(updated)}",
        f"type: {spec.note_type}",
        f"status: {spec.status}",
        f"tags: {yaml_list(spec.tags)}",
        f"aliases: {yaml_list(spec.aliases)}",
        "---",
        "",
    ]
    body = [spec.summary.strip(), ""]
    body.extend([section.rstrip() + "\n" for section in spec.sections])
    body.append("## Links")
    for link in spec.links:
        body.append(f"- [[{link}]]")
    body.append("")
    return "\n".join(frontmatter + body)


def ensure_dirs(root: Path) -> None:
    required = [
        "00 Inbox",
        "10 Projects",
        "20 Areas",
        "30 Resources",
        "40 Archive",
        "Daily",
        "People",
        "MOCs",
        "Templates",
        "_meta",
        "_scripts",
        "10 Projects/OpenClaw Obsidian Second Brain/Meetings",
    ]
    for rel in required:
        (root / rel).mkdir(parents=True, exist_ok=True)


def title_from_path(rel_path: str) -> str:
    return Path(rel_path).stem


def render_tree(root: Path, max_depth: int = 2) -> str:
    lines: list[str] = [f"{root.name}/"]

    def walk(path: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for item in items:
            marker = "/" if item.is_dir() else ""
            lines.append(f"{prefix}{item.name}{marker}")
            if item.is_dir() and depth < max_depth:
                walk(item, prefix + "  ", depth + 1)

    walk(root, "  ", 1)
    return "\n".join(lines)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    ensure_dirs(root)

    today = datetime.now().astimezone().date()

    projects = [
        "OpenClaw Obsidian Second Brain",
        "Hackathon Demo Pipeline",
        "Personal Knowledge Capture",
    ]

    areas = ["Health", "Career", "Learning"]

    resources = [
        "Article - PARA Method for Digital Notes",
        "Book - Building a Second Brain",
        "Book - How to Take Smart Notes",
        "Tool - Obsidian",
        "Tool - Readwise",
        "Article - Zettelkasten for Teams",
        "Guide - LLM Prompting Patterns",
        "Course - Effective Note-Taking",
        "Podcast - Knowledge Work Weekly Ep 84",
        "Checklist - Weekly Review for PKM",
    ]

    people = [
        "Alex Rivera",
        "Maya Chen",
        "Jordan Patel",
        "Samir Thompson",
        "Priya Nandakumar",
        "Elena Garcia",
        "Noah Kim",
        "Rina Sato",
        "Marcus Bell",
        "Leah Brooks",
    ]

    meeting_dates = [today - timedelta(days=d) for d in [13, 11, 10, 8, 6, 4, 2, 1]]
    meeting_topics = [
        "Kickoff and Scope Alignment",
        "Vault Taxonomy Review",
        "Ingestion Pipeline Sync",
        "Weekly Retro 1",
        "Demo Narrative Planning",
        "Metadata QA",
        "Weekly Retro 2",
        "Launch Readiness",
    ]
    meeting_titles = [
        f"Meeting - OpenClaw {day.isoformat()} - {topic}"
        for day, topic in zip(meeting_dates, meeting_topics)
    ]

    daily_dates = [today - timedelta(days=d) for d in range(13, -1, -1)]
    daily_titles = [d.isoformat() for d in daily_dates]

    inbox_titles = [
        "Capture quick tour script",
        "Question about PARA tags",
        "Voice memo about search UX",
        "Screenshot request for README",
        "Idea for meeting digest",
        "Bug note on broken wikilink",
        "Follow-up with mentor",
        "Prompt pattern for triage",
        "Add people MOC shortcuts",
        "Draft launch checklist",
        "Refactor template frontmatter",
        "Collect demo feedback snippets",
    ]

    ideas = [
        "Idea - Daily Voice Memo Digest",
        "Idea - Demo Storyboard for Stakeholders",
        "Idea - Habit Heatmap for Learning",
    ]

    decisions = [
        "Decision - Use PARA as Top-Level Structure",
        "Decision - Keep Meetings Inside OpenClaw Project",
        "Decision - Ship Hackathon Demo as Static Vault Snapshot",
    ]

    mocs = [
        "MOC - Projects",
        "MOC - Areas",
        "MOC - Resources",
        "MOC - People",
    ]

    templates = [
        "Template - Capture",
        "Template - Project",
        "Template - Meeting",
        "Template - Daily",
    ]

    all_core_titles = set(
        projects
        + areas
        + resources
        + people
        + meeting_titles
        + daily_titles
        + ideas
        + decisions
        + mocs
        + templates
        + ["Index", "Start Here"]
    )

    specs: list[NoteSpec] = []

    def add(
        title: str,
        rel_path: str,
        note_type: str,
        status: str,
        tags: list[str],
        aliases: list[str],
        created: datetime,
        summary: str,
        sections: list[str],
        links: list[str],
    ) -> None:
        unique_links: list[str] = []
        for link in links:
            if link != title and link not in unique_links:
                unique_links.append(link)
        # keep links in bounds
        if len(unique_links) < 3:
            fillers = [t for t in sorted(all_core_titles) if t != title and t not in unique_links]
            random.shuffle(fillers)
            unique_links.extend(fillers[: 3 - len(unique_links)])
        if len(unique_links) > 8:
            unique_links = unique_links[:8]

        specs.append(
            NoteSpec(
                title=title,
                rel_path=rel_path,
                note_type=note_type,
                status=status,
                tags=tags,
                aliases=aliases,
                created=created,
                summary=summary,
                sections=sections,
                links=unique_links,
            )
        )

    # Projects
    add(
        projects[0],
        f"10 Projects/{projects[0]}.md",
        "project",
        "active",
        ["project", "openclaw", "obsidian", "hackathon"],
        ["OpenClaw SB"],
        random_dt_for_day(today - timedelta(days=13)),
        "This project builds a realistic Obsidian second-brain demo dataset for the OpenClaw narrative, with strong linking between people, meetings, and decisions.",
        [
            "## Goal\nDeliver a clean, believable vault demo that shows capture, triage, and recall in under five minutes.",
            "## Next actions\n- [ ] Finalize meeting-to-decision backlinks\n- [ ] Polish daily-note highlights for demo day\n- [ ] Run link validation before handoff",
            "## Decisions\n- [[Decision - Use PARA as Top-Level Structure]]\n- [[Decision - Keep Meetings Inside OpenClaw Project]]",
        ],
        [
            "Hackathon Demo Pipeline",
            "Personal Knowledge Capture",
            "MOC - Projects",
            meeting_titles[0],
            meeting_titles[-1],
            decisions[0],
            decisions[1],
            "Tool - Obsidian",
        ],
    )

    add(
        projects[1],
        f"10 Projects/{projects[1]}.md",
        "project",
        "active",
        ["project", "hackathon", "obsidian"],
        [],
        random_dt_for_day(today - timedelta(days=12)),
        "This project packages the second-brain content into a deterministic demo pipeline that can be regenerated quickly before presentations.",
        [
            "## Goal\nCreate a repeatable pipeline that generates, validates, and showcases the mock vault in one command.",
            "## Next actions\n- [ ] Lock final seed values\n- [ ] Capture before/after screenshots\n- [ ] Add a smoke-test checklist for presenters",
            "## Decisions\n- [[Decision - Ship Hackathon Demo as Static Vault Snapshot]]",
        ],
        [
            "OpenClaw Obsidian Second Brain",
            "Personal Knowledge Capture",
            "MOC - Projects",
            "Decision - Ship Hackathon Demo as Static Vault Snapshot",
            "Guide - LLM Prompting Patterns",
            meeting_titles[4],
        ],
    )

    add(
        projects[2],
        f"10 Projects/{projects[2]}.md",
        "project",
        "active",
        ["project", "obsidian", "learning"],
        ["PKC"],
        random_dt_for_day(today - timedelta(days=10)),
        "This project improves daily capture habits so personal notes stay useful, searchable, and connected to longer-term goals.",
        [
            "## Goal\nMaintain a sustainable capture-and-review routine that supports work and learning without adding friction.",
            "## Next actions\n- [ ] Keep daily notes under ten minutes to update\n- [ ] Turn two inbox captures into evergreen notes\n- [ ] Schedule weekly review on Fridays",
            "## Decisions\n- [[Decision - Use PARA as Top-Level Structure]]",
        ],
        [
            "OpenClaw Obsidian Second Brain",
            "Hackathon Demo Pipeline",
            "Learning",
            "Checklist - Weekly Review for PKM",
            "Book - Building a Second Brain",
            daily_titles[-1],
        ],
    )

    # Areas
    add(
        "Health",
        "20 Areas/Health.md",
        "area",
        "active",
        ["area", "health"],
        [],
        random_dt_for_day(today - timedelta(days=9)),
        "Health is tracked as an ongoing area with lightweight routines, recovery notes, and practical experiments that fit around project work.",
        [
            "## Focus\n- Improve energy consistency during demo week\n- Keep a short walking block after lunch",
            "## Cadence\nWeekly check-ins are captured in daily notes and rolled up each Sunday.",
        ],
        ["Learning", "Career", "MOC - Areas", daily_titles[-2]],
    )

    add(
        "Career",
        "20 Areas/Career.md",
        "area",
        "active",
        ["area", "career"],
        [],
        random_dt_for_day(today - timedelta(days=11)),
        "Career notes capture collaboration patterns, mentorship conversations, and concrete execution habits that improve delivery quality.",
        [
            "## Focus\n- Strengthen project communication in meetings\n- Document tradeoffs when making tooling choices",
            "## Cadence\nReview at the end of each sprint retro.",
        ],
        ["Learning", "Health", "MOC - Areas", "Alex Rivera", "Leah Brooks"],
    )

    add(
        "Learning",
        "20 Areas/Learning.md",
        "area",
        "active",
        ["area", "learning"],
        [],
        random_dt_for_day(today - timedelta(days=8)),
        "Learning tracks reading, experiments, and prompt techniques that improve both note quality and team execution speed.",
        [
            "## Focus\n- Practice concise synthesis from long notes\n- Run one prompting experiment each week",
            "## Cadence\nCapture insights in resources and promote ideas into projects when proven.",
        ],
        ["Career", "Health", "MOC - Areas", "Guide - LLM Prompting Patterns", "Book - How to Take Smart Notes"],
    )

    # Resources
    resource_summaries = {
        "Article - PARA Method for Digital Notes": "A practical walkthrough of PARA that informed the top-level vault structure and reduced navigation friction.",
        "Book - Building a Second Brain": "Core concepts on capture and distillation, used to shape weekly review and retrieval habits.",
        "Book - How to Take Smart Notes": "Reference for evergreen note principles and durable linking decisions.",
        "Tool - Obsidian": "Primary workspace for markdown notes, wikilinks, and graph-style navigation in the demo.",
        "Tool - Readwise": "Used as an example ingestion source for highlights and external reading notes.",
        "Article - Zettelkasten for Teams": "Explores how atomic notes can scale beyond solo workflows in collaborative settings.",
        "Guide - LLM Prompting Patterns": "Prompt patterns that help turn rough captures into structured notes with less manual cleanup.",
        "Course - Effective Note-Taking": "A concise course used as baseline training material for new teammates.",
        "Podcast - Knowledge Work Weekly Ep 84": "Episode summary covering practical retrieval habits and meeting-note hygiene.",
        "Checklist - Weekly Review for PKM": "Operational checklist for converting inbox captures into useful, linked notes each week.",
    }

    for idx, title in enumerate(resources):
        created_day = today - timedelta(days=13 - (idx % 10))
        add(
            title,
            f"30 Resources/{title}.md",
            "resource",
            "active" if idx % 3 else "draft",
            ["resource", "obsidian", "learning"],
            [],
            random_dt_for_day(created_day),
            resource_summaries[title],
            [
                "## Key takeaways\n- Capture should be frictionless\n- Triage should be scheduled, not ad hoc\n- Retrieval improves with consistent naming",
                "## Why it matters\nThis note supports current project execution and links directly into repeatable workflows.",
            ],
            [
                "OpenClaw Obsidian Second Brain",
                "Personal Knowledge Capture",
                "MOC - Resources",
                "MOC - Projects",
                "Learning",
            ],
        )

    # Ideas
    idea_summaries = {
        ideas[0]: "Convert scattered voice memos into a daily digest note so quick thoughts become searchable project knowledge.",
        ideas[1]: "Use a narrative storyboard note to map demo scenes from raw capture to polished recall.",
        ideas[2]: "Track learning habits with a lightweight heatmap linked from daily notes and weekly review.",
    }
    for idx, title in enumerate(ideas):
        add(
            title,
            f"30 Resources/{title}.md",
            "idea",
            "draft",
            ["idea", "resource", "obsidian"],
            [],
            random_dt_for_day(today - timedelta(days=7 - idx)),
            idea_summaries[title],
            [
                "## Context\nThis idea emerged from daily capture and is pending a small trial before promotion.",
                "## Experiment\n- Define success metric\n- Run for one week\n- Decide whether to operationalize",
            ],
            [
                "OpenClaw Obsidian Second Brain",
                "Hackathon Demo Pipeline",
                "Checklist - Weekly Review for PKM",
                "MOC - Resources",
            ],
        )

    # Decisions
    decision_summaries = {
        decisions[0]: "We standardized on PARA for top-level folders to keep onboarding simple and retrieval predictable.",
        decisions[1]: "Meeting notes stay inside the OpenClaw project folder to preserve project context and speed review.",
        decisions[2]: "The hackathon demo ships as a static vault snapshot so the walkthrough is stable under time pressure.",
    }

    decision_paths = [
        f"10 Projects/OpenClaw Obsidian Second Brain/{decisions[0]}.md",
        f"10 Projects/OpenClaw Obsidian Second Brain/{decisions[1]}.md",
        f"10 Projects/{decisions[2]}.md",
    ]

    for idx, (title, rel_path) in enumerate(zip(decisions, decision_paths)):
        add(
            title,
            rel_path,
            "decision",
            "done",
            ["decision", "project", "openclaw" if idx < 2 else "hackathon"],
            [],
            random_dt_for_day(today - timedelta(days=12 - idx)),
            decision_summaries[title],
            [
                "## Rationale\nThe team prioritized a structure that demo audiences can understand immediately.",
                "## Consequences\n- Better consistency across notes\n- Slightly less flexibility for edge cases",
            ],
            [
                "OpenClaw Obsidian Second Brain",
                "Hackathon Demo Pipeline",
                "MOC - Projects",
                meeting_titles[idx + 1],
            ],
        )

    # Meetings
    meeting_people_map = [
        ["Alex Rivera", "Maya Chen", "Jordan Patel"],
        ["Samir Thompson", "Priya Nandakumar", "Leah Brooks"],
        ["Elena Garcia", "Noah Kim", "Rina Sato"],
        ["Alex Rivera", "Marcus Bell", "Leah Brooks"],
        ["Maya Chen", "Jordan Patel", "Priya Nandakumar"],
        ["Elena Garcia", "Rina Sato", "Noah Kim"],
        ["Marcus Bell", "Leah Brooks", "Alex Rivera"],
        ["Maya Chen", "Samir Thompson", "Jordan Patel"],
    ]

    for idx, (title, meeting_day, participants) in enumerate(zip(meeting_titles, meeting_dates, meeting_people_map)):
        rel = f"10 Projects/OpenClaw Obsidian Second Brain/Meetings/{title}.md"
        agenda = (
            "## Agenda\n"
            "- Review current note graph quality\n"
            "- Resolve blockers in capture and triage flow\n"
            "- Assign demo prep actions"
        )
        notes = (
            "## Notes\n"
            f"Team aligned on sprint checkpoint {idx + 1} and tightened the OpenClaw story around realistic daily workflows."
        )
        actions = (
            "## Action items\n"
            "- [ ] Update one MOC section before next sync\n"
            "- [ ] Close at least one open inbox capture\n"
            "- [ ] Confirm decision links in project notes"
        )
        links = [
            "OpenClaw Obsidian Second Brain",
            "Hackathon Demo Pipeline",
            daily_titles[min(idx + 5, len(daily_titles) - 1)],
            decisions[min(idx // 3, len(decisions) - 1)],
            *participants,
        ]
        add(
            title,
            rel,
            "meeting",
            "done" if idx < 6 else "active",
            ["meeting", "project", "openclaw", "obsidian"],
            [],
            random_dt_for_day(meeting_day),
            "Working session to coordinate scope, note quality, and next actions for the OpenClaw second-brain demo.",
            [agenda, notes, actions],
            links,
        )

    # Daily notes
    for idx, day in enumerate(daily_dates):
        title = day.isoformat()
        rel = f"Daily/{title}.md"
        project_focus = projects[idx % len(projects)]
        person_focus = people[(idx * 2) % len(people)]
        meeting_link = meeting_titles[idx % len(meeting_titles)]
        inbox_seed = inbox_titles[idx % len(inbox_titles)]
        sections = [
            (
                "## Highlights\n"
                f"- Progressed [[{project_focus}]] with concrete next steps\n"
                f"- Clarified handoff details with [[{person_focus}]]"
            ),
            (
                "## Log\n"
                "- 09:15 Reviewed open captures and sorted priorities\n"
                "- 11:40 Drafted updates for project MOC\n"
                "- 16:20 Closed one lingering task from the previous meeting"
            ),
            (
                "## Tasks\n"
                "- [ ] Resolve one broken backlink\n"
                "- [ ] Move one inbox note to project or resource\n"
                "- [x] Summarize the day in three lines"
            ),
            (
                "## Inbox triage\n"
                f"- Promoted \"{inbox_seed}\" into an actionable note\n"
                "- Deferred low-signal captures to weekly review"
            ),
        ]
        add(
            title,
            rel,
            "daily",
            "done" if day < today else "active",
            ["daily", "obsidian", "openclaw"],
            [],
            random_dt_for_day(day, 18, 21),
            "Daily snapshot of work, context, and triage outcomes to keep momentum across projects and areas.",
            sections,
            [
                project_focus,
                person_focus,
                meeting_link,
                "Checklist - Weekly Review for PKM",
                "MOC - Projects",
            ],
        )

    # Inbox captures
    inbox_days = [today - timedelta(days=d) for d in [13, 12, 11, 10, 9, 8, 7, 5, 4, 3, 2, 1]]
    inbox_times = ["0840", "1015", "1110", "1335", "0915", "1745", "1220", "1630", "0955", "1410", "1525", "1820"]

    for day, hhmm, short in zip(inbox_days, inbox_times, inbox_titles):
        filename = f"{day.strftime('%Y%m%d')}-{hhmm} - {short}.md"
        title = Path(filename).stem
        rel = f"00 Inbox/{filename}"
        add(
            title,
            rel,
            "inbox",
            "draft",
            ["inbox", "capture", "obsidian"],
            [],
            datetime.combine(day, time(hour=int(hhmm[:2]), minute=int(hhmm[2:]))).astimezone(),
            "Quick capture collected during focused work so the thought is preserved before triage.",
            [
                "## Capture\nRaw thought captured in under sixty seconds with enough detail to process later.",
                "## Why it matters\nThis item likely maps to an active project or recurring area responsibility.",
            ],
            [
                projects[random.randint(0, 2)],
                daily_titles[min((today - day).days, len(daily_titles) - 1)],
                "Template - Capture",
                "MOC - Projects",
            ],
        )

    # People
    person_roles = {
        "Alex Rivera": "Engineering lead",
        "Maya Chen": "Product manager",
        "Jordan Patel": "Design partner",
        "Samir Thompson": "Developer advocate",
        "Priya Nandakumar": "Research lead",
        "Elena Garcia": "QA specialist",
        "Noah Kim": "Data engineer",
        "Rina Sato": "Technical writer",
        "Marcus Bell": "Mentor",
        "Leah Brooks": "Operations manager",
    }

    for idx, person in enumerate(people):
        meeting_a = meeting_titles[idx % len(meeting_titles)]
        meeting_b = meeting_titles[(idx + 3) % len(meeting_titles)]
        project_a = projects[idx % len(projects)]
        project_b = projects[(idx + 1) % len(projects)]
        add(
            person,
            f"People/{person}.md",
            "person",
            "active",
            ["person", "team", "openclaw"],
            [],
            random_dt_for_day(today - timedelta(days=13 - (idx % 8))),
            f"{person} is a key collaborator on the OpenClaw demo effort, with clear ownership and regular meeting cadence.",
            [
                f"## Role\n{person_roles[person]} responsible for high-quality handoffs and decision follow-through.",
                "## Working style\nPrefers concise updates, explicit owners, and end-of-day summaries tied to project outcomes.",
            ],
            [project_a, project_b, meeting_a, meeting_b, "MOC - People"],
        )

    # MOCs
    add(
        "MOC - Projects",
        "MOCs/MOC - Projects.md",
        "moc",
        "active",
        ["moc", "project", "openclaw"],
        [],
        random_dt_for_day(today - timedelta(days=13)),
        "Central map for active and supporting projects in the demo vault.",
        [
            "## How to use this\n- Start here before opening project notes\n- Follow links to decisions and meetings\n- Use this as a checkpoint during triage",
            "## Notes\n- [[OpenClaw Obsidian Second Brain]]\n- [[Hackathon Demo Pipeline]]\n- [[Personal Knowledge Capture]]",
        ],
        ["MOC - Areas", "MOC - Resources", "Index", *projects],
    )

    add(
        "MOC - Areas",
        "MOCs/MOC - Areas.md",
        "moc",
        "active",
        ["moc", "area"],
        [],
        random_dt_for_day(today - timedelta(days=12)),
        "Map of ongoing responsibilities that outlive individual projects.",
        [
            "## How to use this\n- Review weekly to rebalance effort\n- Link project tasks back to stable areas\n- Keep area notes concise and actionable",
            "## Notes\n- [[Health]]\n- [[Career]]\n- [[Learning]]",
        ],
        ["MOC - Projects", "MOC - Resources", "Index", *areas],
    )

    add(
        "MOC - Resources",
        "MOCs/MOC - Resources.md",
        "moc",
        "active",
        ["moc", "resource", "learning"],
        [],
        random_dt_for_day(today - timedelta(days=11)),
        "Map of references used to guide structure, workflows, and writing quality.",
        [
            "## How to use this\n- Open one resource before planning\n- Capture takeaways in your own words\n- Link resources to active projects",
            "## Notes\n- [[Article - PARA Method for Digital Notes]]\n- [[Book - Building a Second Brain]]\n- [[Book - How to Take Smart Notes]]\n- [[Tool - Obsidian]]\n- [[Tool - Readwise]]\n- [[Article - Zettelkasten for Teams]]\n- [[Guide - LLM Prompting Patterns]]\n- [[Course - Effective Note-Taking]]\n- [[Podcast - Knowledge Work Weekly Ep 84]]\n- [[Checklist - Weekly Review for PKM]]\n- [[Idea - Daily Voice Memo Digest]]\n- [[Idea - Demo Storyboard for Stakeholders]]\n- [[Idea - Habit Heatmap for Learning]]",
        ],
        ["MOC - Projects", "MOC - Areas", "Index", resources[0], resources[3], ideas[0]],
    )

    add(
        "MOC - People",
        "MOCs/MOC - People.md",
        "moc",
        "active",
        ["moc", "person", "openclaw"],
        [],
        random_dt_for_day(today - timedelta(days=10)),
        "Map of collaborators, mentors, and stakeholders involved in the demo storyline.",
        [
            "## How to use this\n- Open before meetings to refresh context\n- Check ownership and follow-ups\n- Keep person notes connected to outcomes",
            "## Notes\n"
            + "\n".join(f"- [[{person}]]" for person in people),
        ],
        ["MOC - Projects", "Index", people[0], people[1], people[2]],
    )

    # Templates
    template_skeleton = {
        "Template - Capture": "```yaml\nid: <uuid4>\ncreated: <iso8601>\nupdated: <iso8601>\ntype: inbox\nstatus: draft\ntags: [\"inbox\", \"capture\"]\naliases: []\n```\n\n## Summary\n\n## Capture\n\n## Why it matters\n\n## Links",
        "Template - Project": "```yaml\nid: <uuid4>\ncreated: <iso8601>\nupdated: <iso8601>\ntype: project\nstatus: active\ntags: [\"project\"]\naliases: []\n```\n\n## Summary\n\n## Goal\n\n## Next actions\n- [ ]\n\n## Decisions\n\n## Links",
        "Template - Meeting": "```yaml\nid: <uuid4>\ncreated: <iso8601>\nupdated: <iso8601>\ntype: meeting\nstatus: active\ntags: [\"meeting\"]\naliases: []\n```\n\n## Summary\n\n## Agenda\n\n## Notes\n\n## Action items\n- [ ]\n\n## Links",
        "Template - Daily": "```yaml\nid: <uuid4>\ncreated: <iso8601>\nupdated: <iso8601>\ntype: daily\nstatus: active\ntags: [\"daily\"]\naliases: []\n```\n\n## Summary\n\n## Highlights\n\n## Log\n\n## Tasks\n- [ ]\n\n## Inbox triage\n\n## Links",
    }

    for idx, title in enumerate(templates):
        add(
            title,
            f"Templates/{title}.md",
            "resource",
            "draft",
            ["resource", "template", "obsidian"],
            [],
            random_dt_for_day(today - timedelta(days=9 - idx)),
            "Reusable note template used to keep metadata and section structure consistent across the vault.",
            ["## Frontmatter skeleton\n" + template_skeleton[title]],
            ["Index", "Start Here", "MOC - Projects", "MOC - Resources"],
        )

    # Index and Start Here
    add(
        "Index",
        "Index.md",
        "moc",
        "active",
        ["moc", "index", "openclaw", "obsidian"],
        ["Home"],
        random_dt_for_day(today),
        "Entry point for the mock second-brain dataset with fast links to projects, maps of content, and today's context.",
        [
            "## Quick navigation\n- [[MOC - Projects]]\n- [[MOC - Areas]]\n- [[MOC - Resources]]\n- [[MOC - People]]\n- [[Start Here]]",
            f"## Today\n- [[{today.isoformat()}]]",
            "## Active projects\n- [[OpenClaw Obsidian Second Brain]]\n- [[Hackathon Demo Pipeline]]\n- [[Personal Knowledge Capture]]",
        ],
        [
            "Start Here",
            "MOC - Projects",
            "MOC - Areas",
            "MOC - Resources",
            "MOC - People",
            today.isoformat(),
            *projects,
        ],
    )

    add(
        "Start Here",
        "Start Here.md",
        "moc",
        "active",
        ["moc", "guide", "obsidian", "openclaw"],
        [],
        random_dt_for_day(today),
        "This vault demonstrates a practical second-brain workflow for a small team over two weeks of project work.",
        [
            "## Structure\n- `00 Inbox` for quick captures\n- `10 Projects` for active outcomes\n- `20 Areas` for ongoing responsibilities\n- `30 Resources` for references\n- `40 Archive` for old or stub content",
            "## 3-step demo flow\n1. capture: open an inbox note and record context quickly\n2. triage: move and refine the note into project/resource context\n3. recall: use MOCs and links to retrieve what matters",
        ],
        ["Index", "MOC - Projects", "MOC - Areas", "MOC - Resources", "MOC - People", projects[0]],
    )

    # Validate links; create stubs if needed
    title_to_spec = {spec.title: spec for spec in specs}
    missing = sorted({link for spec in specs for link in spec.links if link not in title_to_spec})
    for missing_title in missing:
        stub_rel = f"40 Archive/Stubs/{missing_title}.md"
        add(
            missing_title,
            stub_rel,
            "resource",
            "archived",
            ["resource", "archive", "stub"],
            [],
            random_dt_for_day(today - timedelta(days=1)),
            "Stub note auto-created to keep every wikilink resolvable in the demo dataset.",
            ["## Context\nOriginal link target was not present at generation time.", "## Follow-up\nCreate a full note if this concept becomes active."],
            ["Index", "MOC - Resources", "40 Archive"],
        )

    # Write notes
    title_to_id: dict[str, str] = {}
    note_paths: list[Path] = []
    for spec in specs:
        abs_path = root / spec.rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        note_id = deterministic_uuid4()
        title_to_id[spec.title] = note_id
        content = format_note(spec, note_id=note_id, updated=spec.created)
        abs_path.write_text(content, encoding="utf-8")
        note_paths.append(abs_path)

    # Note parser used for manifest generation
    link_re = re.compile(r"\[\[([^\]]+)\]\]")
    fm_type_re = re.compile(r"^type:\s*(.+)$", re.MULTILINE)
    fm_created_re = re.compile(r"^created:\s*(.+)$", re.MULTILINE)
    fm_id_re = re.compile(r"^id:\s*(.+)$", re.MULTILINE)
    fm_tags_re = re.compile(r"^tags:\s*(.+)$", re.MULTILINE)

    def parse_note(path: Path) -> dict:
        text = path.read_text(encoding="utf-8")
        links = sorted(set(link_re.findall(text)))
        note_type = fm_type_re.search(text).group(1).strip() if fm_type_re.search(text) else "resource"
        created = fm_created_re.search(text).group(1).strip() if fm_created_re.search(text) else ""
        note_id = fm_id_re.search(text).group(1).strip() if fm_id_re.search(text) else ""
        tags_raw = fm_tags_re.search(text).group(1).strip() if fm_tags_re.search(text) else "[]"
        try:
            tags = json.loads(tags_raw.replace("'", '"'))
        except json.JSONDecodeError:
            tags = []

        return {
            "path": str(path.relative_to(root).as_posix()),
            "title": path.stem,
            "id": note_id,
            "type": note_type,
            "created": created,
            "tags": tags,
            "links": links,
        }

    # Stats markdown
    manifest_for_stats = [parse_note(path) for path in sorted(note_paths)]
    by_type = Counter(item["type"] for item in manifest_for_stats)
    by_tag = Counter(tag for item in manifest_for_stats for tag in item["tags"])
    stats_created = datetime.now().astimezone()
    stats_id = deterministic_uuid4()

    stats_lines = [
        "---",
        f"id: {stats_id}",
        f"created: {iso_local(stats_created)}",
        f"updated: {iso_local(stats_created)}",
        "type: resource",
        "status: active",
        'tags: ["meta", "stats", "resource"]',
        "aliases: []",
        "---",
        "",
        "Generated summary of note counts and tag distribution for the mock dataset.",
        "",
        "## Counts by type",
    ]
    for key, value in sorted(by_type.items()):
        stats_lines.append(f"- {key}: {value}")

    stats_lines.extend(["", "## Counts by tag"])
    for key, value in sorted(by_tag.items()):
        stats_lines.append(f"- {key}: {value}")

    stats_lines.extend(
        [
            "",
            "## Links",
            "- [[Index]]",
            "- [[MOC - Projects]]",
            "- [[MOC - Resources]]",
        ]
    )
    (root / "_meta" / "stats.md").write_text("\n".join(stats_lines) + "\n", encoding="utf-8")

    # Build manifest from all markdown notes, including _meta/stats.md
    markdown_paths = sorted(root.rglob("*.md"))
    manifest = [parse_note(path) for path in markdown_paths]
    manifest_path = root / "_meta" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    total_notes = len(manifest)
    index_path = root / "Index.md"
    today_daily_path = root / "Daily" / f"{today.isoformat()}.md"

    print(root.name)
    print(total_notes)
    print(index_path.as_posix())
    print(today_daily_path.as_posix())
    print(render_tree(root, max_depth=2))


if __name__ == "__main__":
    main()
