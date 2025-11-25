git status
git add .
git commit -m "🔥 Helix infra stack: Traefik + Keycloak + FastAPI baseline"

git commit -m "🔰️ Updating On-Boarding README Docs"

git remote add origin git@github.com:akenel/helixnet.git
git push -u origin main


# Start an interactive rebase for the last 3 commits
git rebase -i HEAD~3

# In the editor that opens, you'll see your commits. 
# Change 'pick' to 'edit' for the commit that contained the secret (probably the first one listed)
# Save and close the editor

# Now you'll be at the commit that had the secret
# Remove the secret from env/helix.example.env if you haven't already
nano env/helix.example.env

# Stage the change
git add env/helix.example.env

# Amend the commit
git commit --amend

# Continue the rebase
git rebase --continue

# If there are merge conflicts with subsequent commits, resolve them and continue
# Repeat git add and git rebase --continue as needed

# Force push the cleaned history
git push -f origin main

