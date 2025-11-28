<div align="center">

# 🌌 SkyLyne Multi-Server VPN Manager

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Aiogram](https://img.shields.io/badge/Aiogram-v3.x-blueviolet?style=for-the-badge&logo=telegram)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

<p align="center">
  <b>Manage unlimited VPS servers, automate OpenVPN installations, and handle users with professional traffic & time limits directly from Telegram.</b>
</p>

<p align="center">
  <a href="https://t.me/storm_inc">
    <img src="https://img.shields.io/badge/Contact-Developer-blue?style=for-the-badge&logo=telegram" alt="Developer">
  </a>
  <a href="https://t.me/DevolpersLab">
    <img src="https://img.shields.io/badge/Join-Channel-blueviolet?style=for-the-badge&logo=telegram" alt="Channel">
  </a>
</p>

</div>

---

## 🚀 Features

SkyLyne is not just a simple bot; it is a fully functional **SaaS (Software as a Service)** management panel.

- **☁️ Multi-Server Architecture:** Manage unlimited VPS servers from a single bot interface.
- **⚡ One-Click Installation:** Automatically installs OpenVPN and monitoring agents on fresh servers via SSH.
- **👤 Advanced User Management:**
  - Create users instantly (auto-generates .ovpn files).
  - Set **Traffic Limits** (e.g., 10GB).
  - Set **Time Limits** (e.g., 30 Days).
- **🛡️ Auto-Revoke System:** Automatically deletes users and revokes access when their time or data limit expires.
- **👀 Real-Time Monitoring:** View online users connected to your servers instantly.
- **📱 Modern UI:** Persistent Keyboard buttons for navigation and HTML-styled messages.
- **💾 Secure Database:** Uses SQLite for reliable data storage.

---

## 🛠️ Requirements

To run this bot, you need:

- **Python 3.10** or higher.
- **Target VPS OS:** Ubuntu 20.04/22.04 or Debian 10/11.

---

## 📥 Installation Guide

Follow these steps to deploy the bot on your local machine or server.

### 1. Clone the Repository
Open your terminal and clone the project:

```bash
git clone [https://github.com/HyperCreatorTM/OpenVPN_Menager.git](https://github.com/HyperCreatorTM/OpenVPN_Menager.git)
cd OpenVPN_Menager

2. Install Dependencies

Install the required Python libraries:
Bash

pip install -r requirements.txt

3. Configuration

Create a file named config.py in the main directory and add your credentials:
Python

# config.py
TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = 12345678  # Your Telegram ID
DB_NAME = "vps_data.db"

4. Run the Bot

Start the application:
Bash

python main.py

📖 Usage

Once the bot is running, send the /start command.

Adding a VPS

    Click ☁️ VPS GOŞ / AÝYR on the main keyboard.

    Click ➕ Taze VPS Goş.

    Enter your IP, Port (default 22), Username (root), and Password.

    The bot will automatically connect and install the necessary scripts (approx. 2-3 mins).

Managing Users

    Click ⚙️ Panel on the main keyboard.

    Select the server you want to manage.

    Use the menu to:

        Create User: Set limits and duration.

        Online Users: See who is connected.

        Delete User: Revoke access immediately.

⚠️ Disclaimer

This software is developed for educational and server management purposes. The developer is not responsible for any misuse.

<div align="center">

Developed by @storm_inc

Channel: @DevolpersLab

Made with ❤️ in Python

</div>
