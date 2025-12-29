#!/usr/bin/env python3
"""
Telegram Chat JSON to Markdown Converter

Converts exported Telegram chat history (JSON format) into a readable Markdown document.
Supports group chats and private chats, including replies and various message types.
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any


def load_chat_data(json_path: str) -> dict:
    """Load and parse the Telegram JSON export file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_timestamp(date_str: str) -> str:
    """Format the date string into a readable timestamp."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, AttributeError):
        return date_str


def extract_text_content(text_field: Any) -> str:
    """
    Extract text content from Telegram's text field.
    The text field can be a string or a list of mixed strings and objects.
    """
    if isinstance(text_field, str):
        return text_field
    
    if isinstance(text_field, list):
        result = []
        for item in text_field:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                # Handle formatted text (bold, italic, links, mentions, etc.)
                text = item.get('text', '')
                item_type = item.get('type', '')
                
                if item_type == 'bold':
                    result.append(f'**{text}**')
                elif item_type == 'italic':
                    result.append(f'*{text}*')
                elif item_type == 'code':
                    result.append(f'`{text}`')
                elif item_type == 'pre':
                    result.append(f'\n```\n{text}\n```\n')
                elif item_type == 'text_link':
                    href = item.get('href', '')
                    result.append(f'[{text}]({href})')
                elif item_type == 'link':
                    result.append(text)
                elif item_type in ('mention', 'mention_name'):
                    result.append(f'@{text}' if not text.startswith('@') else text)
                elif item_type == 'hashtag':
                    result.append(text)
                elif item_type == 'email':
                    result.append(text)
                elif item_type == 'phone':
                    result.append(text)
                elif item_type == 'strikethrough':
                    result.append(f'~~{text}~~')
                elif item_type == 'underline':
                    result.append(f'<u>{text}</u>')
                elif item_type == 'spoiler':
                    result.append(f'||{text}||')
                elif item_type == 'custom_emoji':
                    result.append(text)
                else:
                    result.append(text)
        return ''.join(result)
    
    return str(text_field) if text_field else ''


def get_message_type_info(message: dict) -> str:
    """Get additional info about special message types."""
    media_type = message.get('media_type')
    
    if media_type == 'sticker':
        emoji = message.get('sticker_emoji', '')
        return f'[Sticker {emoji}]'
    elif media_type == 'voice_message':
        duration = message.get('duration_seconds', 0)
        return f'[Voice message - {duration}s]'
    elif media_type == 'video_message':
        duration = message.get('duration_seconds', 0)
        return f'[Video message - {duration}s]'
    elif media_type == 'animation':
        return '[GIF]'
    elif media_type == 'video_file':
        return '[Video]'
    elif media_type == 'audio_file':
        title = message.get('title', 'Audio')
        performer = message.get('performer', '')
        if performer:
            return f'[Audio: {performer} - {title}]'
        return f'[Audio: {title}]'
    
    # Check for photo
    if 'photo' in message:
        return '[Photo]'
    
    # Check for file
    if 'file' in message:
        file_name = message.get('file_name', message.get('file', 'File'))
        return f'[File: {file_name}]'
    
    # Check for location
    if 'location_information' in message:
        loc = message.get('location_information', {})
        lat = loc.get('latitude', '')
        lon = loc.get('longitude', '')
        return f'[Location: {lat}, {lon}]'
    
    # Check for contact
    if 'contact_information' in message:
        contact = message.get('contact_information', {})
        name = contact.get('first_name', '') + ' ' + contact.get('last_name', '')
        phone = contact.get('phone_number', '')
        return f'[Contact: {name.strip()} - {phone}]'
    
    # Check for poll
    if 'poll' in message:
        poll = message.get('poll', {})
        question = poll.get('question', 'Poll')
        return f'[Poll: {question}]'
    
    return ''


def format_service_message(message: dict) -> str:
    """Format service messages (joins, leaves, title changes, etc.)."""
    action = message.get('action', '')
    actor = message.get('actor', message.get('from', 'Someone'))
    
    action_messages = {
        'create_group': f'*{actor} created the group*',
        'invite_members': f'*{actor} invited members to the group*',
        'remove_members': f'*{actor} removed members from the group*',
        'join_group_by_link': f'*{actor} joined the group via invite link*',
        'leave_group': f'*{actor} left the group*',
        'pin_message': f'*{actor} pinned a message*',
        'edit_group_title': f'*{actor} changed the group title to "{message.get("title", "")}"*',
        'edit_group_photo': f'*{actor} changed the group photo*',
        'delete_group_photo': f'*{actor} deleted the group photo*',
        'migrate_from_group': '*Group upgraded to supergroup*',
        'migrate_to_supergroup': '*Group upgraded to supergroup*',
        'phone_call': f'*Phone call with {actor}*',
        'score_in_game': f'*{actor} scored in a game*',
        'bot_allowed': f'*Bot allowed by {actor}*',
    }
    
    return action_messages.get(action, f'*[{action}]*')


def build_message_index(messages: list) -> dict:
    """Build an index of messages by ID for quick reply lookups."""
    return {msg.get('id'): msg for msg in messages if 'id' in msg}


def format_message(message: dict, message_index: dict) -> str:
    """Format a single message into Markdown."""
    lines = []
    
    # Check if it's a service message
    if message.get('type') == 'service':
        timestamp = format_timestamp(message.get('date', ''))
        service_text = format_service_message(message)
        lines.append(f'> {service_text}')
        lines.append(f'> *{timestamp}*')
        lines.append('')
        return '\n'.join(lines)
    
    # Regular message
    msg_id = message.get('id', '')
    sender = message.get('from', message.get('actor', 'Unknown'))
    timestamp = format_timestamp(message.get('date', ''))
    
    # Handle forwarded messages
    forwarded_from = message.get('forwarded_from')
    
    # Start message block
    lines.append(f'### {sender}')
    lines.append(f'*{timestamp}* | Message #{msg_id}')
    lines.append('')
    
    # Handle replies
    reply_to_id = message.get('reply_to_message_id')
    if reply_to_id and reply_to_id in message_index:
        original = message_index[reply_to_id]
        original_sender = original.get('from', original.get('actor', 'Unknown'))
        original_text = extract_text_content(original.get('text', ''))
        
        # Truncate long replies
        if len(original_text) > 100:
            original_text = original_text[:100] + '...'
        
        original_text = original_text.replace('\n', ' ')
        lines.append(f'> **↩ Reply to {original_sender}:** {original_text}')
        lines.append('')
    
    # Handle forwarded
    if forwarded_from:
        lines.append(f'> **↪ Forwarded from {forwarded_from}**')
        lines.append('')
    
    # Message content
    text = extract_text_content(message.get('text', ''))
    media_info = get_message_type_info(message)
    
    if media_info:
        lines.append(f'📎 {media_info}')
        if text:
            lines.append('')
    
    if text:
        lines.append(text)
    
    # Handle empty messages (shouldn't happen but just in case)
    if not text and not media_info:
        lines.append('*[Empty message]*')
    
    lines.append('')
    lines.append('---')
    lines.append('')
    
    return '\n'.join(lines)


def generate_chat_header(chat_data: dict) -> str:
    """Generate the Markdown header with chat details."""
    lines = []
    
    chat_name = chat_data.get('name', 'Telegram Chat')
    chat_type = chat_data.get('type', 'unknown')
    chat_id = chat_data.get('id', '')
    
    lines.append(f'# {chat_name}')
    lines.append('')
    lines.append('## Chat Details')
    lines.append('')
    lines.append('| Property | Value |')
    lines.append('|----------|-------|')
    lines.append(f'| **Name** | {chat_name} |')
    lines.append(f'| **Type** | {chat_type.replace("_", " ").title()} |')
    lines.append(f'| **ID** | {chat_id} |')
    
    # Count messages
    messages = chat_data.get('messages', [])
    lines.append(f'| **Total Messages** | {len(messages)} |')
    
    # Get date range
    if messages:
        dates = [m.get('date') for m in messages if m.get('date')]
        if dates:
            first_date = format_timestamp(min(dates))
            last_date = format_timestamp(max(dates))
            lines.append(f'| **First Message** | {first_date} |')
            lines.append(f'| **Last Message** | {last_date} |')
    
    # Get unique participants
    participants = set()
    for msg in messages:
        sender = msg.get('from') or msg.get('actor')
        if sender:
            participants.add(sender)
    
    if participants:
        lines.append(f'| **Participants** | {len(participants)} |')
    
    lines.append('')
    
    # List participants
    if participants:
        lines.append('### Participants')
        lines.append('')
        for p in sorted(participants):
            lines.append(f'- {p}')
        lines.append('')
    
    lines.append('---')
    lines.append('')
    lines.append('## Messages')
    lines.append('')
    
    return '\n'.join(lines)


def convert_to_markdown(chat_data: dict) -> str:
    """Convert the entire chat data to Markdown format."""
    output_parts = []
    
    # Generate header
    output_parts.append(generate_chat_header(chat_data))
    
    # Process messages
    messages = chat_data.get('messages', [])
    message_index = build_message_index(messages)
    
    for message in messages:
        formatted = format_message(message, message_index)
        output_parts.append(formatted)
    
    return '\n'.join(output_parts)


def main():
    parser = argparse.ArgumentParser(
        description='Convert Telegram chat export (JSON) to Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python telegram_to_markdown.py result.json
  python telegram_to_markdown.py result.json -o chat_history.md
  python telegram_to_markdown.py export/result.json --output ./output/chat.md
        '''
    )
    parser.add_argument(
        'input_file',
        help='Path to the Telegram JSON export file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output Markdown file path (default: same name as input with .md extension)'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    
    if not input_path.exists():
        print(f'Error: Input file "{input_path}" not found.')
        return 1
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix('.md')
    
    # Load and convert
    print(f'Loading chat data from: {input_path}')
    chat_data = load_chat_data(str(input_path))
    
    print(f'Converting {len(chat_data.get("messages", []))} messages...')
    markdown_content = convert_to_markdown(chat_data)
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f'Markdown saved to: {output_path}')
    return 0


if __name__ == '__main__':
    exit(main())

