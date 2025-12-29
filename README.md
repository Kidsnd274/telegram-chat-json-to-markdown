# Telegram Chat to Markdown Converter (AI Generated)

Convert your exported Telegram chat history (JSON format) into a beautifully formatted, readable Markdown document.

## Features

- **Chat Details Header**: Displays group/chat name, type, ID, message count, date range, and list of participants
- **Full Message History**: All messages with timestamps and sender information
- **Reply Support**: Shows the original message content when someone replies
- **Forwarded Messages**: Indicates when messages are forwarded and from whom
- **Rich Text Formatting**: Preserves bold, italic, code, links, mentions, and more
- **Media Indicators**: Shows placeholders for photos, videos, stickers, voice messages, files, etc.
- **Service Messages**: Formats group events like joins, leaves, title changes, etc.

## Requirements

- Python 3.7+
- No external dependencies (uses only standard library)

## Usage

### Basic Usage

```bash
python telegram_to_markdown.py result.json
```

This will create `result.md` in the same directory.

### Custom Output Path

```bash
python telegram_to_markdown.py result.json -o chat_history.md
```

### Help

```bash
python telegram_to_markdown.py --help
```

## How to Export Telegram Chat

1. Open Telegram Desktop
2. Go to the chat you want to export
3. Click on the three dots menu (⋮) → **Export chat history**
4. Select **JSON** as the format
5. Choose what to include (messages, photos, etc.)
6. Click **Export**
7. Use the generated `result.json` file with this script

## Output Format

The generated Markdown file includes:

### Header Section
- Chat name and type
- Total message count
- Date range (first to last message)
- List of all participants

### Messages Section
Each message includes:
- Sender name
- Timestamp
- Message ID
- Reply context (if replying to another message)
- Forward information (if forwarded)
- Message content with formatting preserved
- Media type indicators

## Example Output

```markdown
# My Group Chat

## Chat Details

| Property | Value |
|----------|-------|
| **Name** | My Group Chat |
| **Type** | Private Group |
| **ID** | 123456789 |
| **Total Messages** | 1,234 |
| **First Message** | 2023-01-15 10:30:00 |
| **Last Message** | 2024-12-29 15:45:00 |
| **Participants** | 5 |

### Participants

- Alice
- Bob
- Charlie

---

## Messages

### Alice
*2023-01-15 10:30:00* | Message #1

Hello everyone! 👋

---

### Bob
*2023-01-15 10:31:00* | Message #2

> **↩ Reply to Alice:** Hello everyone! 👋

Hey Alice! Welcome!

---
```