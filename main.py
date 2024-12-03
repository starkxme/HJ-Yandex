import imaplib
import email
from email.header import decode_header
from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import re
import random
import string
from keep_alive import keep_alive

keep_alive()

# Your Yandex Mail credentials
EMAIL = "akublutut@yandex.com"
PASSWORD = "bcbgjkhninlcqxsn"  # Use Yandex app password, not the account password

# Telegram Bot Token
BOT_TOKEN = "7200824261:AAGl08ZdTLWj67OTcmujKdWtF0r-hQAgFsU"

# List to store all user IDs who have interacted with the bot
user_ids = set()

# Connect to the Yandex IMAP server
def connect_to_imap():
    try:
        mail = imaplib.IMAP4_SSL("imap.yandex.com")
        mail.login(EMAIL, PASSWORD)
        print("Connected to IMAP server successfully.")
        return mail
    except Exception as e:
        print(f"Error connecting to IMAP: {e}")
        raise

# Fetch unread emails from the inbox
def fetch_emails():
    try:
        mail = connect_to_imap()
        mail.select("inbox")  # Open the inbox folder
        status, messages = mail.search(None, "UNSEEN")  # Search for unread emails
        if status != "OK":
            print("No unread emails found.")
            return []

        emails = []
        for num in messages[0].split():
            status, msg_data = mail.fetch(num, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    sender = msg.get("From")
                    body = extract_email_body(msg)
                    print(f"Email found: Subject={subject}, From={sender}")
                    emails.append((subject, sender, body))
        mail.logout()
        return emails
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []

# Extract the plain text body from an email
def extract_email_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = msg.get_payload(decode=True).decode()

    # Optional: Clean up email body formatting
    body = clean_email_body(body)
    return body

# Clean and format the email body for Telegram
def clean_email_body(body):
    # Example cleanup: Remove extra spaces, newlines, or specific patterns
    body = re.sub(r"\n\s*\n", "\n", body)  # Remove consecutive newlines
    body = body.strip()  # Trim leading/trailing spaces
    return body

# Send email details to all users who have interacted with the bot
async def send_to_telegram(subject, sender, body):
    try:
        bot = Bot(token=BOT_TOKEN)
        message = f"New Email:{body}"

        # Send to all tracked user IDs
        for user_id in user_ids:
            await bot.send_message(chat_id=user_id, text=message)
            print(f"Email sent to user ID {user_id}: {subject}")
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

# Generate a random email alias
def generate_email_alias():
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return f"{EMAIL.split('@')[0]}+{random_string}@yandex.com"

# Handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Track the user ID
    user_ids.add(update.message.from_user.id)

    keyboard = [[
        "Get Mail", 
        "Generate Mail"
    ]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)

# Handle button clicks
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Track the user ID if they haven't interacted before
    user_ids.add(update.message.from_user.id)

    if text == "Get Mail":
        emails = fetch_emails()
        if emails:
            for subject, sender, body in emails:
                await send_to_telegram(subject, sender, body)
            await update.message.reply_text("Unread emails have been sent to Telegram.")
        else:
            await update.message.reply_text("No unread emails found.")

    elif text == "Generate Mail":
        new_email = generate_email_alias()
        await update.message.reply_text(f"Generated email: {new_email}")

# Main function to start the bot
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
