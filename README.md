<img width="1236" height="814" alt="Screenshot 2026-06-11 at 8 51 25 PM" src="https://github.com/user-attachments/assets/0bd15fea-f93d-4e58-b36b-220ecee3e7c9" />
<img width="1376" height="809" alt="Screenshot 2026-06-11 at 8 51 10 PM" src="https://github.com/user-attachments/assets/06e16a9a-9bbd-44e8-9e9d-42f9ec6af711" />
<img width="1253" height="811" alt="Screenshot 2026-06-11 at 8 51 42 PM" src="https://github.com/user-attachments/assets/17381141-c0d7-4dc5-92e8-8a8eeb972563" />
<img width="1282" height="804" alt="Screenshot 2026-06-11 at 8 51 57 PM" src="https://github.com/user-attachments/assets/0ac27f05-b377-4aa3-a862-5ec549331961" />
# 📚 Online Bookstore - Full-Stack E-Commerce Platform

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Django](https://img.shields.io/badge/Django-Full%20Stack-darkgreen)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Razorpay](https://img.shields.io/badge/Payment-Razorpay-blueviolet)
![Twilio](https://img.shields.io/badge/SMS-Twilio-red)

## 📌 Project Overview
A comprehensive, full-stack e-commerce platform built using Python and the Django framework. [cite_start]This application provides a seamless shopping experience for users looking to purchase both eBooks and physical hardcopies, complete with secure payment processing and real-time order tracking notifications[cite: 40]. 

## 🚀 Core Features
* [cite_start]**Dual Product Support:** Seamlessly handles the sale and delivery management for both digital eBooks and physical hardcopy books[cite: 40].
* [cite_start]**Secure Payment Gateway:** Integrated with the **Razorpay API** to process secure, real-time financial transactions[cite: 41].
* [cite_start]**Automated Notifications:** Utilizes the **Twilio API** to dispatch automated SMS alerts to customers regarding their order status and payment confirmations[cite: 41].
* [cite_start]**Interactive User Experience:** Features a built-in user review system, allowing customers to rate and review their purchases[cite: 40].
* [cite_start]**Admin & Analytics:** Includes a custom-built sales dashboard for the admin to track revenue, inventory, and user engagement efficiently[cite: 41].

## 🛠️ Tech Stack
* **Backend:** Python, Django
* [cite_start]**Database:** SQLite [cite: 40]
* [cite_start]**APIs & Integrations:** Razorpay (Payments), Twilio (SMS Alerts) [cite: 41]
* **Frontend:** HTML, CSS, JavaScript (Django Templates)

## 📂 Project Structure
```text
📦 Django-Online-Bookstore
 ┣ 📂 bookstore_core        # Main Django project settings and URL routing
 ┣ 📂 shop                  # E-commerce app (models, views, templates for products)
 ┣ 📂 users                 # User authentication and profile management
 ┣ 📜 manage.py             # Django entry point
 ┗ 📜 requirements.txt      # Project dependencies
