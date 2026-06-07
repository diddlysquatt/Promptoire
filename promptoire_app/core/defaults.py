"""A small, curated starter library for fresh installs.

Showcases both prompt types, placeholders, tags, and image-model fields — so a
brand-new user immediately sees what Promptoire is for. Existing users keep
their own prompts.json and never see this.
"""

from __future__ import annotations

from . import schema


def _p(title, body, type="text", tags=None, **img):
    return schema.new_prompt(title=title, body=body, type=type, tags=tags or [], **img)


def _c(name, color, prompts):
    cat = schema.new_category(name, color=color)
    cat["prompts"] = prompts
    return cat


def default_library() -> dict:
    return {
        "version": schema.SCHEMA_VERSION,
        "categories": [
            _c("Writing", "#7c5cff", [
                _p("Improve this writing",
                   "Improve the following text. Make it clearer, tighter, and more engaging while keeping my voice. "
                   "Return only the rewrite.\n\n{text}",
                   tags=["editing", "rewrite"]),
                _p("Explain like I'm {age}",
                   "Explain {topic} clearly to a {age}-year-old. Use a simple analogy and avoid jargon.",
                   tags=["explain"]),
                _p("Summarize to bullet points",
                   "Summarize the text below into 5-7 crisp bullet points capturing the key ideas.\n\n{text}",
                   tags=["summary"]),
            ]),
            _c("Coding", "#22d3ee", [
                _p("New-chat handoff brief",
                   "Create a NEW CHAT HANDOFF that summarizes everything needed to continue this work immediately: "
                   "objective, current state, constraints, decisions made, key files/paths, commands to run, known "
                   "bugs, and the next steps in priority order.",
                   tags=["workflow", "context"]),
                _p("Pragmatic code review",
                   "Review the code below for correctness bugs and clear, low-risk improvements. Prioritize real "
                   "issues over style. For each finding: what, why it matters, and the minimal fix.\n\n{code}",
                   tags=["review"]),
                _p("Explain this error",
                   "Here is an error and the relevant code. Explain the root cause in plain terms and give the "
                   "smallest correct fix.\n\nError:\n{error}\n\nCode:\n{code}",
                   tags=["debug"]),
            ]),
            _c("Productivity", "#34d399", [
                _p("Turn this into a plan",
                   "Turn the following goal into a concrete, ordered plan with milestones and a realistic first "
                   "step I can do today.\n\nGoal: {goal}",
                   tags=["planning"]),
                _p("Draft a reply",
                   "Draft a {tone} reply to the message below. Keep it concise and clear.\n\n{message}",
                   tags=["email"]),
            ]),
            _c("AI Art", "#f472b6", [
                _p("Cinematic portrait",
                   "cinematic portrait of {subject}, dramatic rim lighting, 85mm, shallow depth of field, "
                   "film grain, moody color grade, highly detailed",
                   type="image", tags=["portrait", "cinematic"],
                   negative="blurry, lowres, extra fingers, watermark, text",
                   model="Midjourney v6", params="--ar 4:5 --stylize 250"),
                _p("Isometric asset",
                   "isometric {object}, clean vector style, soft studio lighting, pastel palette, centered, "
                   "game asset, white background",
                   type="image", tags=["isometric", "asset"],
                   negative="text, busy background, noise",
                   model="SDXL", params="Steps: 30, CFG: 6"),
                _p("Dreamy landscape",
                   "vast {place} at golden hour, volumetric light, atmospheric haze, ultra-detailed, "
                   "epic scale, painterly",
                   type="image", tags=["landscape"],
                   negative="people, text, watermark",
                   model="Flux.1", params="--ar 16:9"),
            ]),
        ],
    }
