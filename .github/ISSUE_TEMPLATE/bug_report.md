---
name: Bug report
about: Create a report to help us improve
title: ''
labels: bug
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is and the expected behavior.

**Affected scrapers**
This affects the following scrapers:
- [ ] ClubElo
- [ ] ESPN
- [ ] FBref
- [ ] FiveThirtyEight
- [ ] FotMob
- [ ] Match History
- [ ] SoFIFA
- [ ] Understat
- [ ] WhoScored

**Code example**
A minimal code example that fails. Use `no_cache=True` to make sure an invalid cached file does not cause the bug and make sure you have the latest version of soccerdata installed.

```python
import soccerdata as sd
fbref = sd.FBref(leagues="ENG-Premier League", seasons="24/25", no_cache=True)
fbref.read_schedule()
```

**Error message**

```
<paste the error message here>
```

**Additional context**
Add any other context about the problem here.

**Contributor Action Plan**

- [ ] I can fix this issue and will submit a pull request.
- [ ] I’m unsure how to fix this, but I'm willing to work on it with guidance.
- [ ] I’m not able to fix this issue.
