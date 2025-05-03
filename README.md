# 🧱 block-adobe

Don’t you just ***hate*** it when you finally take a well-deserved break from designing all those masterpieces in Photoshop, fire up your favorite game… only to discover that everything lags like heck?

You open Task Manager, start digging, and surprise (not really a surprise)—it’s Photoshop, again, hogging your bandwidth all for itself.

### Put an end to that.

**`block-adobe`** is a tiny Windows utility that scans your `Program Files` for Adobe applications and automatically adds them to your Windows Defender firewall rules. That means no more surprise background uploads, updates, or "helpful" Adobe chatter with the internet when you don’t want it.

Save your bandwidth for the things *you* care about—not for Adobe.

---

## 🔧 Building

To build `block-adobe` on Windows, make sure you have **Python 3.13** installed. Then open PowerShell and run:

```powershell
> python -m venv .venv
> . .venv\Scripts\Activate.ps1
> pip install -r requirements.txt
> .\build.ps1
```
