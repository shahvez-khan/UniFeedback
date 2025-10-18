# 🎓 UniFeedback: The Secure Faculty Feedback Platform

**Your confidential voice for academic improvement.** Provide constructive feedback on faculty, course material, and teaching quality to help build a better learning environment.

## 🔗 Live Application

The UniFeedback platform is currently deployed and accessible at:
**[https://unifeedback.onrender.com/](https://unifeedback.onrender.com/)**

-----

## ✨ Features

UniFeedback is designed to make the feedback process easy, secure, and impactful.

  * **🔒 Complete Anonymity:** All submissions are completely anonymous. We prioritize your privacy to ensure **honest and candid responses**, free from any fear of reprisal.
  * **🚀 Driving Quality Education:** Your input is directly used by administration and faculty to implement targeted improvements in **curriculum and teaching methodologies**.
  * **💻 Intuitive User Experience:** The system is designed for quick and easy navigation. Complete a comprehensive feedback form in minutes using any device.
  * **📊 Comprehensive Results Dashboard:** Faculty and administrators can view professional PDF reports to instantly identify areas of **strength and opportunities for development** based on aggregated student ratings and comments.
  * **📈 Data-Driven Decisions:** The aggregated data leads to **Improved Course Content**, **Enhanced Student Success**, and **Better Faculty Engagement**.

-----

## 3-Step Feedback Process

The platform simplifies the entire process into three clear steps:

1.  **Submit Your Review:** Fill out the confidential form, providing ratings (1=Poor, 5=Excellent) on key categories like **"Knowledge," "Clarity," "Engagement,"** and **"Punctuality,"** and include detailed comments.
2.  **Data Aggregation:** The system automatically calculates **average ratings** and aggregates anonymous comments for each faculty member across all criteria, ensuring anonymity is maintained throughout the process.
3.  **Review & Act:** Faculty and administrators access professional PDF reports to identify areas of strength and opportunities for development, enabling them to make **Data-Driven Decisions**.

-----

## 🛠️ Technology Stack

This platform is built using a modern, efficient, and scalable technology stack:

| Component | Technology |
| :--- | :--- |
| **Frontend** | **HTML5, CSS3** |
| **Backend** | **Python** with **Flask** (Micro-framework) |
| **Database** | **MySQL** |
| **Deployment**| **Render** |

-----

## 🚀 Getting Started

### Prerequisites

  * Python 3.x
  * pip (Python package installer)
  * A running MySQL instance

### Installation (For Developers)

1.  **Clone the repository:**
    ```bash
    git clone [Your Repository URL]
    cd UniFeedback
    ```
2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure environment variables:**
    Create a `.env` file (or set environment variables directly) to store sensitive information, including your database connection details.
    ```
    # Example .env content
    MYSQL_HOST=localhost
    MYSQL_USER=user
    MYSQL_PASSWORD=password
    MYSQL_DB=unifeedback_db
    FLASK_SECRET_KEY=your_secret_key
    ```
5.  **Initialize the database (if necessary):**
    Run any setup scripts or migration commands to create the necessary tables in your MySQL database.
    ```bash
    # Example command, depending on your setup
    python db_setup.py 
    ```
6.  **Run the Flask application:**
    ```bash
    flask run
    ```

The application should now be running locally, typically accessible at `http://127.0.0.1:5000/`.

-----
