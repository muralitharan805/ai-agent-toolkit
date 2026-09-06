# Workflows

Upcoming Migration to Skills

Workflows are being deprecated in favor of **[Agent Skills](/docs/ide/skills)** by November 1, 2026. Please refer to our **[Workflows to Skills Migration Guide](/docs/migration/workflows-to-skills)** or use the `/migrate-workflows` slash command in chat to automatically migrate your existing workflows to skills.

Workflows enable you to define a series of steps to guide the Agent through a repetitive set of tasks, such as deploying a service or responding to PR comments. These Workflows are saved as markdown files, allowing you to have an easy repeatable way to run key processes. Once saved, Workflows can be invoked in Agent via a slash command with the format /workflow-name.

While Rules provide models with guidance by providing persistent, reusable context at the prompt level, Workflows provide a structured sequence of steps or prompts at the trajectory level, guiding the model through a series of interconnected tasks or actions.

To create a workflow:

1.  Open the Customizations panel via the ”…” dropdown at the top of the editor’s agent panel.
2.  Navigate to the Workflows panel.
3.  Click the **\+ Global** button to create a new global workflow that can be accessed across all your workspaces, or click the **\+ Workspace** button to create a workflow specific to your current workspace.

To execute a workflow, simply invoke it in Agent using the /workflow-name command. You can call other Workflows from within a workflow! For example, /workflow-1 can include instructions like “Call /workflow-2” and “Call /workflow-3”. Upon invocation, Agent sequentially processes each step defined in the workflow, performing actions or generating responses as specified.

Workflows are saved as markdown files and contain a title, a description and a series of steps with specific instructions for Agent to follow. Workflow files are limited to 12,000 characters each.

## Agent-Generated Workflows

You can also ask Agent to generate Workflows for you! This works particularly well after manually working with Agent through a series of steps since it can use the conversation history to create the Workflow.