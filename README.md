<div align="center">
<img src="data/icons/hicolor/128x128/apps/in.gxanshu.postcard.png" width="96" alt="WinPostcard icon">

# WinPostcard

**A Windows email client written in Python with GTK 4 and libadwaita.**

[![Tests](https://img.shields.io/github/actions/workflow/status/Johnny70/WinPostcard/tests.yml?style=flat-square&label=tests)](https://github.com/Johnny70/WinPostcard/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/license-GPL--3.0--or--later-3584e4?style=flat-square)](COPYING)

[**Providers**](#supported-providers) · [**Features**](#features) · [**Build**](#building-from-source)
</div>

WinPostcard has the classic three panel layout: folders on the left, conversations in the middle, and the reading panel. Nothing fancy, just how an email client should look. The whole codebase is small enough to read in an evening.

**There are no accounts, no telemetry, and no cloud**. Your mail is stored in a SQLite file on your machine and your passwords go into Windows Credential Manager. WinPostcard only talks to your mail server, nothing else.

<div align="center">
<img src="data/screenshots/main-window.png" alt="WinPostcard showing the three-pane layout with folders, conversations, and reader">
</div>

<table>
<tr>
<td width="50%"><img src="data/screenshots/preferences.png" alt="Preferences showing notification, remote image, avatar, background and signature settings"></td>
<td width="50%"><img src="data/screenshots/about.png" alt="The About dialog showing WinPostcard version 1.6.0"></td>
</tr>
<tr>
<td align="center"><sub><b>Preferences</b></sub></td>
<td align="center"><sub><b>About</b></sub></td>
</tr>
</table>

<div align="center">
<img src="data/screenshots/mailing-list-unsubscribe.png" width="480" alt="The reader showing a mailing list banner with an Unsubscribe button and the confirmation dialog naming the host the request goes to">

<sub><b>One click unsubscribe from a mailing list</b></sub>
</div>

<div align="center">
<img src="data/screenshots/mail-compose.png" width="340" alt="The composer at a narrow window size, with To/Cc/Bcc fields and a rich-text toolbar">

<sub><b>Composer</b></sub>
</div>

> **WinPostcard is in heavy development.** You will probably hit bugs. Please
> [report them](https://github.com/Johnny70/WinPostcard/issues), it helps a lot.

## Features

### 📬 Mail

- **Any IMAP/SMTP account**, as many as you want. Passwords are stored in Windows Credential Manager. You can choose TLS or STARTTLS for each server, so Proton Mail Bridge also works.
- **A separate username** when the server's login is not your email address, or the mailbox is reached through a preferred alias.
- **Server settings are filled in automatically** from your email address for Gmail, Yahoo, iCloud, Outlook, Fastmail, Zoho, AOL and Yandex. If you type something by hand, WinPostcard does not touch it.
- **One unified inbox.** An *All Inboxes* row at the top of the sidebar shows mail from every account in a single list, and archive, trash, star and reply all still act on the right account.
- **Threaded conversations** and nested folders shown as a tree.
- **Full-text search** across all your mail.
- **Works offline** from the local cache, and keeps syncing after you close the window (optional)

### ✍️ Composing

- **Rich text**: bold, italic, underline, strikethrough, bulleted and numbered lists, links. Mail is sent as HTML with a plain-text version included.
- **Reply, reply-all and forward**, with Cc/Bcc, a signature, and a Drafts/Outbox that does not lose your message.
- **Recipient autocomplete** from the addresses already in your mail.

### 🖥️ Desktop

- **HTML and plain-text mail.** Remote images are blocked until you allow them, and links open in your browser.
- **One click unsubscribe** from a mailing list. If the list supports it (RFC 8058), WinPostcard sends the request itself after telling you where it goes; otherwise it opens the list's page in your browser or a pre-filled email.
- **Archive, trash, move, undo**, on one conversation or a whole selection.
- **Attachments** open in their default app with one click.
- **Relative dates** ("2h ago", "Yesterday"), with the exact time shown on hover.
- **Desktop notifications** when new mail arrives.
- **Tray icon with an unread badge.**
- **Sender avatars** from Gravatar, or the icon from the sender's website if there is no Gravatar. You can turn this off.
- **Default mail client**: `mailto:` links open the composer with the fields already filled.
- **Name accounts your way**: show each account's display name in the sidebar instead of its address.

More are coming.

## Supported providers

WinPostcard speaks plain IMAP and SMTP, so anything that supports those should work. "Works" means the protocol is supported. "Tested" means I actually ran it against a real account.

| Provider | Works | Tested | Notes |
|---|:---:|:---:|---|
| **Gmail** | ✅ | ✅ | You need 2-Step Verification and an [app password](https://myaccount.google.com/apppasswords) |
| **Yahoo Mail** | ✅ | ✅ | Needs an app password from Account Security |
| **Proton Mail** | ✅ | ✅ | Through [Proton Mail Bridge](https://proton.me/mail/bridge) (paid plans). Use the Bridge's local host, port and password with STARTTLS |
| **Any IMAP/SMTP server** | ✅ | ❌ | Fastmail, Zoho, Mailbox.org, Migadu (✅), self-hosted Dovecot/Postfix. Enter host, port and TLS mode by hand |
| **Outlook / Hotmail / Microsoft 365** | ❌ | ❌ | Microsoft removed basic auth and requires OAuth 2.0. Planned |

TIP: most providers with 2FA will reject your normal account password over IMAP. Generate an app-specific password instead.

# Installation

There is no installer yet — see [Building from source](#building-from-source) below to run WinPostcard from a checkout. A packaged installer is planned.

## Starting hidden at login

Turn on **Keep running in the background** and **Start at Login** in Preferences.
WinPostcard writes a `Run` entry to your user registry hive, so there is no
file to create by hand.

WinPostcard starts with no window, checks for mail on your sync interval, and notifies you when something arrives. Click the notification to open it.

## Building from source

WinPostcard is a Windows app. GTK 4 and libadwaita come from [MSYS2](https://www.msys2.org/)'s UCRT64 packages rather than a from-source build. See [docs/windows-setup.md](docs/windows-setup.md) for the one-time prerequisites, then everything goes through [`just`](https://github.com/casey/just):

```bash
just init  # one-time: pacman-install GTK4/libadwaita/PyGObject via MSYS2
just build # compile blueprints -> gresource -> gschema
just run   # build, then launch (the normal dev loop)
```

For the curious: the UI is GTK 4 and libadwaita with Blueprint (`.blp`) files, search uses SQLite FTS5, networking is done with the Python standard library (`imaplib` and `smtplib`), and credentials go through Windows Credential Manager via `keyring`. HTML mail rendering is a fork of [webview2-gtk](https://github.com/Johnny70/webview2-gtk) (Microsoft Edge WebView2) — see `docs/windows-setup.md` for its current status.

## AI Notice

I write WinPostcard with the help of AI tools. The AI does the typing, but the architecture, the review and the responsibility are mine. I read every line before it ships.

I am not interested in spending hours typing out code that is already fully formed in my head, so I let the AI type it. But I would never recommend running it on autopilot. You have to stay in control of what it produces.

If this still feels as "AI slop" to you, that is fair, and you are welcome to use whatever client suits you. But if you do install WinPostcard, I hope you will trust it. It is built with the same care as anything written by hand.

## Contributing

Contributions are welcome, bug reports especially, because WinPostcard is young and every real inbox is different. Code should pass `just check` and `just test`. AI-assisted work is fine, as long as you understand every line you submit.

New here? [CONTRIBUTING.md](CONTRIBUTING.md) explains the dev environment — see [docs/windows-setup.md](docs/windows-setup.md) for the one-time prerequisites, then run `just init` and `just run`.

If WinPostcard is useful to you, a ⭐ helps other people find it.

## License

[GPL-3.0-or-later](COPYING).
