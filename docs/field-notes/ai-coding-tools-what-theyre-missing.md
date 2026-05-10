# Are You Building Software, or Are You Arguing With an LLM?

I ship production code with an AI co-pilot every day. Not tutorials. Not TODO apps. A platform with 44 database models, Keycloak RBAC, Traefik reverse proxy, Docker Compose, deployed to real servers, used by real people.

Today I watched someone spend four hours arguing with an AI about whether to use Redux or Context API. Meanwhile their app doesn't have auth, doesn't deploy anywhere, and crashes when you refresh the page.

This post is for you if you're using AI coding tools and wondering why your project isn't going anywhere. I'm not here to flex. I'm here to ask you the questions you should be asking yourself -- because if you can't answer them, no AI tool will save you.

---

## Are you reading the codebase before you generate code?

Be honest. When you ask the AI to "add a new feature," does it read your existing code first? Or does it just start generating?

We built a complete Kanban board module today. Before a single line was written, the AI read our existing QA module -- same codebase, same patterns. The new module matches the old one exactly. Same model structure. Same schema conventions. Same router pattern. Same template style.

If your AI is generating code that looks different from file to file, you don't have a codebase. You have a folder of experiments. And six months from now, you won't be able to maintain any of it.

**Question you should be asking:** "Does my new code look like it was written by the same team that wrote everything else?"

## Has your app ever left localhost?

This is the one that separates real software from demos.

Today, after building the module, we deployed to a Hetzner server. Immediately hit four problems:

- Keycloak login URL was routing wrong because Traefik uses hostname-based routing locally but path-based on the remote server
- An environment variable was stuck on the wrong server IP from a previous session
- The remote server's IP wasn't in Keycloak's allowed redirect URIs
- A team member was missing a role assignment in the running auth server

None of these are code problems. None of them show up on localhost. None of them appear in any benchmark. But they are 80% of the actual work of shipping software.

If your AI coding tool has never helped you debug a failed OAuth2 token exchange caused by an untrusted forwarded header behind a reverse proxy -- you haven't tested it. You've demoed it.

**Question you should be asking:** "What happens when I deploy this to a real server with real auth and real DNS?"

## Do you know why your config is the way it is?

A Keycloak hostname variable was set to a DigitalOcean IP. It was left over from a remote testing session two weeks ago. The comment in the config file literally said "revert after session."

The AI caught it -- but only because it had persistent context from previous sessions. It knew the history. It knew that IP belonged to a different server. Without that context, it would have looked like a valid configuration.

If you start a fresh AI session every time you code, you're hiring a new contractor every morning who's never seen your project. They'll write plausible-looking code that breaks things you fixed last week.

**Question you should be asking:** "Does my AI know why things are configured the way they are, or is it just guessing?"

## Are you the navigator, or are you a passenger?

During deployment, the AI tried to use the wrong server IP. I caught it in one sentence: "That's the DigitalOcean box, not Hetzner." Three seconds. Saved an hour.

That's not the AI failing. That's the workflow working. I know my infrastructure. I know which server is which. I know the deployment pipeline. The AI does the heavy lifting on code generation, but I'm navigating.

If you're copying and pasting AI output without understanding what it does, you're not coding with AI. You're hoping. And hope is not a deployment strategy.

The people spending hours arguing with the LLM about code style, framework choices, and TypeScript generics -- while their app has no auth, no deployment pipeline, no tests against a real database -- are solving the wrong problems. You're debating paint colors for a house with no foundation.

**Question you should be asking:** "If the AI disappeared tomorrow, could I debug this system myself?"

## Can you trace a request from browser to database and back?

When the login page broke, here's what the debugging looked like:

Browser sends request to `helix.local/realms/...` -- Traefik routes by hostname, sends it to the app server, not Keycloak -- 404. Fixed by routing to `keycloak.helix.local`. But on the remote server, there's no DNS for that hostname -- Caddy routes by path instead. So the template needs to detect which environment it's in and use the right URL pattern.

That's one bug. It touches the browser, the reverse proxy, the auth server, the template engine, and the deployment environment. It requires understanding how HTTP headers, OAuth2 flows, reverse proxy routing, and DNS resolution actually work.

No amount of AI code generation helps you here if you don't understand the request lifecycle. The AI can help you fix it -- but only if you can describe the problem. And you can only describe the problem if you understand the system.

**Question you should be asking:** "Can I draw the request flow from the user's browser to the database on a whiteboard?"

## Are you building the simplest thing that works?

We built the backlog with 4 enums and 2 tables. No epics. No sprints. No velocity charts. No drag-and-drop. No WebSocket real-time updates. Tags handle grouping. A click changes status. One page does everything.

It took one session. It's deployed. It works. People are using it.

The temptation with AI is to ask for everything. "Give me a full project management suite with Gantt charts and resource allocation." The AI will happily generate 3,000 lines of code that looks impressive and does nothing you actually need.

The developers who ship are the ones who build the minimum that solves today's problem. The developers who don't ship are the ones still configuring their sprint velocity dashboard for a team of three.

**Question you should be asking:** "What is the least I can build that solves the actual problem?"

---

## The real question

Here's what it comes down to.

AI coding tools are incredible. I use one every day and it makes me significantly faster. But faster at what? Faster at the things I already know how to do. The AI doesn't replace the experience of knowing how OAuth2 works, how reverse proxies route traffic, how database migrations run, how Docker networking connects services, how to debug a 502 in production.

If you have that experience, AI is a force multiplier. You think, it types. You navigate, it builds. You catch the wrong IP in three seconds because you know your infrastructure.

If you don't have that experience, AI is a trap. It generates code you can't debug, for systems you can't operate, deployed to infrastructure you don't understand. And when it breaks -- not if, when -- you'll be back on Stack Overflow or Reddit asking "why does my Keycloak redirect give me a 502" and nobody can help you because your setup is a maze of AI-generated configs that you can't explain.

The wannabes are building better hammers. The actual work is knowing where to swing.

No tool fixes that. Only experience does.

---

*Angelo Kenel -- HelixNet*
