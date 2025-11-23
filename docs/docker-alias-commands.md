
## 🐳 Docker Alias Quick Reference (dh)

| Alias | Purpose | Equivalent Full Command |
| :---- | :--- | :--- |
| **dps** | Running Containers (Essential columns) | `docker ps --format "table..."` |
| **dpsa**| All Containers (Running/Stopped/Exit) | `docker ps -a --format "table..."` |
| **dl** | Logs (Last 100 lines) | `docker logs --tail 100 <name>` |
| **dll** | Logs (Follow/Stream) | `docker logs -f <name>` |
| **dil** | Image List | `docker image ls` |
| **dir** | Image Remove | `docker rmi <id/name>` |
| **dip** | Image Prune (Remove unused) | `docker image prune` |
| **dvl** | Volume List | `docker volume ls` |
| **dvr** | Volume Remove | `docker volume rm <name>` |
| **dvp** | Volume Prune (Remove unused) | `docker volume prune` |

