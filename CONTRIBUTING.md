# Contributing to XTM-mcp

Thank you for reading this documentation and considering making your contribution to the project. Any contribution that helps us improve the repository is valuable and much appreciated. If it is also meaningful to you or your organisation it’s all for the best.

In order to help you understand the project, where we are heading and how you can contribute, below are several resources and answers.

Do not hesitate to shoot us an [email](mailto:contact@opencti.io) or join us on our [Slack channel](https://community.filigran.io).


## Why contribute?

XTM-mcp is an open source project aiming at building MCP servers for Filigran's products. If you want to know more about OpenCTI, you can read the [detailed documentation](https://docs.opencti.io/latest/) or try it on the [demonstration platform](https://demo.opencti.io/). If you want to know more about OpenBAS, you can read the [detailed documentation](https://docs.openbas.io/latest/) or try it on the [demonstration platform](https://demo.openbas.io/).

Whether you are an organisation or an individual working or studying in the field of cybersecurity and cyberdefense, or simply as an individual looking for a technical challenge, contributing to the project may represent a great opportunity for you.

* You can help grow the community and tools focused on improving the AI based automation for cyberdefense.

* You will be able to adapt the tool to your core interests and methods of work by developing features or fixing bugs you are most interested in.


## Where is the project heading?

Now that the first version of the tool has been released, our goal for the future releases is two-fold:

* Of course, fix bugs and develop features which are identify as non-critical but would really add-up to MCP capabilities.

* Ease the cross usage of Filigran's tools though MCP capabilities


## Code of Conduct

OpenCTI has adopted a Code of Conduct that we expect project participants to adhere to. Please read the [full text](https://github.com/FiligranHQ/xtm-mcp/blob/master/CODE_OF_CONDUCT.md) so that you can understand which actions will and will not be tolerated.


## How can you contribute?

Any contribution is appreciated, and many don’t imply coding. Contributions can range from a suggestion for improving documentation, requesting a new feature, reporting a bug, to developing features or fixing bugs yourself.

For general suggestions or questions about the project or the documentation, you can open an issue on the repository with the label "question". We will answer as soon as possible. If you do not wish to publish on the repository, please see the section below [**"How can you get in touch for other questions?"**](#howcanyougetintouchforotherquestions).

* Just using the tools and opening issues if everything is not working as expected will be a huge step forward. 

* You can look through opened issues and help triage them (ask for more information, suggest workarounds, suggest label, flag issues etc.)

### How can you get in touch for other questions?

If you need support or you wish to engage a discussion about the OpenCTI platform, feel free to join us on our [Slack channel](https://community.filigran.io). You can also send us an [email](mailto:contact@opencti.io).


<!-- filigran-conventions:start -->
## Commit, pull request & issue conventions

To keep the backlog consistent and searchable across all Filigran projects, this
repository follows a shared title and label convention. The full taxonomy lives
in [`.github/LABELS.md`](.github/LABELS.md). In short:

* **Titles** — All commit, pull request and issue titles follow the
  [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
  specification with a GitHub issue reference:
  `type(scope?)!?: description (#issue)` (e.g.
  `feat(api): add bulk export endpoint (#1234)`). The description starts with a
  lowercase letter and has no trailing period; preserve acronyms and proper
  nouns. Types: `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `perf`,
  `test`, `build`, `ci`, `revert`.

* **No more bracket prefixes** — The old `[backend]` / `[frontend]` /
  `[component]` prefixes are **discontinued**; use a Conventional Commits scope
  instead (e.g. `fix(backend): ...`).

* **GitHub reference** — Pull request titles **must** end with the related issue
  reference, e.g. `(#1234)` (the PR title becomes the squash-merge commit). Every
  pull request must be linked to an issue. Enforcement is preventive and applied
  at the organization level; **Renovate** pull requests are exempt.

* **Signed commits** — All commits must be signed. See the
  [GitHub documentation on signing commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits).

* **Labels** — Every **issue** carries one primary type label matching its title
  prefix (`feature` for `feat:`, `bug` for `fix:`, `documentation` for `docs:`)
  plus optional area labels, and its GitHub **Type** (Feature / Bug / Task) set
  to match. **Pull requests carry a restricted label set** — exactly one
  ownership label (`filigran team` or `community`), optionally `vibe-coded` (an
  AI-assisted change the author reviews first), and the automatic language /
  `dependencies` labels. Type, area/scope and workflow labels are issue-only. Do
  not use the deprecated `enhancement` / `feature request` labels — use
  `feature`. See [`.github/LABELS.md`](.github/LABELS.md) for the shared palette
  ([`.github/labels.yml`](.github/labels.yml)).
<!-- filigran-conventions:end -->
