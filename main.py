from dotenv import load_dotenv
import imaplib
import email
import os
from bs4 import BeautifulSoup
import requests
import datetime

load_dotenv()

username = os.getenv("EMAIL")
password = os.getenv("PASSWORD")

def connect_to_mail():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, password)
    mail.select("inbox")
    return mail

def extract_links_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    links = [link["href"] for link in soup.find_all("a", href=True) if "unsubscribe" in link["href"].lower()]
    return links

def click_link(link):
    try:
        response = requests.get(link)
        if response.status_code == 200:
            print("Successfully visited", link)
        else:
            print("Failed to visit", link, "error code:", response.status_code)
    except Exception as e:
        print("Error with", link, str(e))

def search_for_email(days_back=10):
    mail = connect_to_mail()
    print("Connected to email server")


    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=days_back)
    start_date_str = start_date.strftime("%d-%b-%Y") 

    _, search_data = mail.search(None, f'(SINCE "{start_date_str}" BODY "unsubscribe")')
    print(f"Found {len(search_data[0].split())} matching emails")

    data = search_data[0].split()
    links = []

    for num in data:
        _, data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        print(f"Processing email {num}")

        email_date = email.utils.parsedate_to_datetime(msg["Date"])
        if email_date.date() < start_date:
            continue


        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    html_content = part.get_payload(decode=True).decode()
                    links.extend(extract_links_from_html(html_content))
        else:
            content_type = msg.get_content_type()
            content = msg.get_payload(decode=True).decode()
            if content_type == "text/html":
                links.extend(extract_links_from_html(content))

    mail.logout()
    return links

def save_links_to_file(links):
    with open("links.txt", "w") as f:
        f.write("\n".join(links))


links = search_for_email(days_back=10)  
for link in links:
    click_link(link)

save_links_to_file(links)
